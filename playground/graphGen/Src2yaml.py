#!/usr/bin/env python3
"""
src2yaml — Convert C++/Python source code to a graph YAML representation.

Graph schema:
  nodes:
    - id: str          # unique identifier
      type: str        # module | class | function | method | variable | import | namespace | lambda
      name: str        # unqualified name
      qualified_name: str
      language: str    # python | cpp
      loc: {file, line_start, line_end, col_start}
      metadata: {}     # type-specific extras (return_type, params, bases, etc.)

  edges:
    - id: str
      source: str      # node id
      target: str      # node id
      type: str        # contains | calls | inherits | imports | references | instantiates | overrides | uses_type
      metadata: {}
"""

import ast
import sys
import os
import hashlib
import argparse
from pathlib import Path
from typing import Any

import yaml

try:
    from tree_sitter_languages import get_parser as ts_get_parser
    HAS_TS = True
except ImportError:
    HAS_TS = False


# ─────────────────────────────────────────────────────────────
# Shared utilities
# ─────────────────────────────────────────────────────────────

def make_id(prefix: str, name: str, extra: str = "") -> str:
    h = hashlib.md5(f"{prefix}:{name}:{extra}".encode()).hexdigest()[:6]
    safe = name.replace("::", "__").replace(".", "_").replace("<", "").replace(">", "")[:40]
    return f"{safe}_{h}"


def edge_id(src: str, tgt: str, etype: str) -> str:
    return f"e_{src[:8]}_{tgt[:8]}_{etype}"


class GraphBuilder:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = {}
        self._edge_set: set[tuple] = set()

    def add_node(self, nid: str, ntype: str, name: str, qualified: str,
                 language: str, loc: dict, metadata: dict | None = None) -> str:
        if nid not in self.nodes:
            self.nodes[nid] = {
                "id": nid,
                "type": ntype,
                "name": name,
                "qualified_name": qualified,
                "language": language,
                "loc": loc,
                "metadata": metadata or {},
            }
        return nid

    def add_edge(self, src: str, tgt: str, etype: str, metadata: dict | None = None):
        key = (src, tgt, etype)
        if key in self._edge_set:
            return
        if src not in self.nodes or tgt not in self.nodes:
            return
        self._edge_set.add(key)
        if not hasattr(self, '_edges_list'):
            self._edges_list = []
        self._edges_list.append({
            "id": edge_id(src, tgt, etype),
            "source": src,
            "target": tgt,
            "type": etype,
            "metadata": metadata or {},
        })

    def to_dict(self) -> dict:
        return {
            "graph": {
                "source_file": self.filepath,
                "nodes": list(self.nodes.values()),
                "edges": getattr(self, '_edges_list', []),
            }
        }


# ─────────────────────────────────────────────────────────────
# Python parser (stdlib ast)
# ─────────────────────────────────────────────────────────────

class PythonParser:
    def __init__(self, source: str, filepath: str):
        self.source = source
        self.filepath = filepath
        self.graph = GraphBuilder(filepath)
        self._scope_stack: list[str] = []  # stack of node ids

    def _loc(self, node: ast.AST) -> dict:
        return {
            "file": self.filepath,
            "line_start": getattr(node, 'lineno', 0),
            "line_end": getattr(node, 'end_lineno', 0),
            "col_start": getattr(node, 'col_offset', 0),
        }

    def _qualified(self, name: str) -> str:
        parts = [self.graph.nodes[nid]['name'] for nid in self._scope_stack
                 if nid in self.graph.nodes]
        return ".".join(parts + [name]) if parts else name

    def parse(self) -> GraphBuilder:
        tree = ast.parse(self.source, filename=self.filepath)
        mod_id = make_id("module", self.filepath)
        self.graph.add_node(
            mod_id, "module", Path(self.filepath).stem,
            Path(self.filepath).stem, "python",
            {"file": self.filepath, "line_start": 1, "line_end": 0, "col_start": 0},
        )
        self._scope_stack.append(mod_id)
        self._visit_body(tree.body)
        self._scope_stack.pop()
        return self.graph

    def _visit_body(self, stmts: list):
        for node in stmts:
            self._visit(node)

    def _visit(self, node: ast.AST):
        if isinstance(node, ast.Import):
            self._visit_import(node)
        elif isinstance(node, ast.ImportFrom):
            self._visit_importfrom(node)
        elif isinstance(node, ast.ClassDef):
            self._visit_class(node)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            self._visit_function(node)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            self._visit_assign(node)

    def _visit_import(self, node: ast.Import):
        parent = self._scope_stack[-1]
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            nid = make_id("import", alias.name, self.filepath)
            self.graph.add_node(nid, "import", name, alias.name, "python",
                                self._loc(node), {"module": alias.name})
            self.graph.add_edge(parent, nid, "imports")

    def _visit_importfrom(self, node: ast.ImportFrom):
        parent = self._scope_stack[-1]
        module = node.module or ""
        for alias in node.names:
            fullname = f"{module}.{alias.name}"
            name = alias.asname or alias.name
            nid = make_id("import", fullname, self.filepath)
            self.graph.add_node(nid, "import", name, fullname, "python",
                                self._loc(node), {"module": module, "symbol": alias.name})
            self.graph.add_edge(parent, nid, "imports")

    def _visit_class(self, node: ast.ClassDef):
        parent = self._scope_stack[-1]
        qname = self._qualified(node.name)
        nid = make_id("class", qname, self.filepath)
        bases = [ast.unparse(b) for b in node.bases]
        self.graph.add_node(nid, "class", node.name, qname, "python",
                            self._loc(node), {"bases": bases, "decorators": [ast.unparse(d) for d in node.decorator_list]})
        self.graph.add_edge(parent, nid, "contains")

        # inheritance edges (symbolic — resolved by name)
        for base in node.bases:
            base_name = ast.unparse(base)
            base_id = make_id("class", base_name, "")
            # Create placeholder node if needed for the edge
            if base_id not in self.graph.nodes:
                self.graph.add_node(base_id, "class", base_name, base_name, "python",
                                    {"file": "", "line_start": 0, "line_end": 0, "col_start": 0},
                                    {"external": True})
            self.graph.add_edge(nid, base_id, "inherits")

        self._scope_stack.append(nid)
        self._visit_body(node.body)
        self._scope_stack.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        parent = self._scope_stack[-1]
        parent_type = self.graph.nodes.get(parent, {}).get("type", "")
        ntype = "method" if parent_type == "class" else "function"
        qname = self._qualified(node.name)
        nid = make_id(ntype, qname, self.filepath)

        params = []
        for arg in node.args.args:
            p = {"name": arg.arg}
            if arg.annotation:
                p["type"] = ast.unparse(arg.annotation)
            params.append(p)

        ret = ast.unparse(node.returns) if node.returns else None
        self.graph.add_node(nid, ntype, node.name, qname, "python",
                            self._loc(node),
                            {"params": params, "return_type": ret,
                             "async": isinstance(node, ast.AsyncFunctionDef),
                             "decorators": [ast.unparse(d) for d in node.decorator_list]})
        self.graph.add_edge(parent, nid, "contains")

        self._scope_stack.append(nid)
        # Scan calls within function body
        for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
            if isinstance(child, ast.Call):
                self._visit_call(child, nid)
        self._scope_stack.pop()

    def _visit_call(self, node: ast.Call, caller_id: str):
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
        else:
            return
        callee_id = make_id("function", callee_name, "")
        if callee_id not in self.graph.nodes:
            self.graph.add_node(callee_id, "function", callee_name, callee_name, "python",
                                {"file": "", "line_start": 0, "line_end": 0, "col_start": 0},
                                {"external": True})
        self.graph.add_edge(caller_id, callee_id, "calls")

    def _visit_assign(self, node: ast.Assign | ast.AnnAssign):
        parent = self._scope_stack[-1]
        targets = []
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append((t.id, None))
        else:
            if isinstance(node.target, ast.Name):
                ann = ast.unparse(node.annotation) if node.annotation else None
                targets.append((node.target.id, ann))

        for name, ann in targets:
            qname = self._qualified(name)
            nid = make_id("variable", qname, self.filepath)
            self.graph.add_node(nid, "variable", name, qname, "python",
                                self._loc(node), {"type_annotation": ann})
            self.graph.add_edge(parent, nid, "contains")


# ─────────────────────────────────────────────────────────────
# C++ parser (tree-sitter)
# ─────────────────────────────────────────────────────────────

class CppParser:
    NODE_TEXT_LIMIT = 256

    def __init__(self, source: str, filepath: str):
        self.source = source
        self.source_bytes = source.encode()
        self.filepath = filepath
        self.graph = GraphBuilder(filepath)
        self._scope_stack: list[str] = []

    def _text(self, node) -> str:
        return self.source_bytes[node.start_byte:node.end_byte].decode(errors='replace')[:self.NODE_TEXT_LIMIT]

    def _loc(self, node) -> dict:
        return {
            "file": self.filepath,
            "line_start": node.start_point[0] + 1,
            "line_end": node.end_point[0] + 1,
            "col_start": node.start_point[1],
        }

    def _qualified(self, name: str) -> str:
        parts = [self.graph.nodes[nid]['name'] for nid in self._scope_stack
                 if nid in self.graph.nodes]
        return "::".join(parts + [name]) if parts else name

    def parse(self) -> GraphBuilder:
        if not HAS_TS:
            raise RuntimeError("tree-sitter-languages not available; cannot parse C++")
        parser = ts_get_parser('cpp')
        tree = parser.parse(self.source_bytes)

        mod_id = make_id("module", self.filepath)
        self.graph.add_node(mod_id, "module", Path(self.filepath).stem,
                            Path(self.filepath).stem, "cpp",
                            {"file": self.filepath, "line_start": 1, "line_end": 0, "col_start": 0})
        self._scope_stack.append(mod_id)
        self._walk(tree.root_node)
        self._scope_stack.pop()
        return self.graph

    def _walk(self, node):
        t = node.type
        if t == 'namespace_definition':
            self._handle_namespace(node)
        elif t in ('class_specifier', 'struct_specifier'):
            self._handle_class(node)
        elif t == 'function_definition':
            self._handle_function(node)
        elif t == 'declaration':
            self._handle_declaration(node)
        elif t == 'preproc_include':
            self._handle_include(node)
        elif t == 'using_declaration':
            self._handle_using(node)
        else:
            for child in node.children:
                self._walk(child)

    def _child_by_type(self, node, *types):
        for c in node.children:
            if c.type in types:
                return c
        return None

    def _child_text_by_type(self, node, *types) -> str:
        c = self._child_by_type(node, *types)
        return self._text(c) if c else ""

    def _handle_namespace(self, node):
        parent = self._scope_stack[-1]
        name = self._child_text_by_type(node, 'identifier', 'namespace_identifier') or "<anonymous>"
        qname = self._qualified(name)
        nid = make_id("namespace", qname, self.filepath)
        self.graph.add_node(nid, "namespace", name, qname, "cpp", self._loc(node))
        self.graph.add_edge(parent, nid, "contains")
        body = self._child_by_type(node, 'declaration_list')
        if body:
            self._scope_stack.append(nid)
            for c in body.children:
                self._walk(c)
            self._scope_stack.pop()

    def _handle_class(self, node):
        parent = self._scope_stack[-1]
        name_node = self._child_by_type(node, 'type_identifier', 'identifier')
        name = self._text(name_node) if name_node else "<anon>"
        qname = self._qualified(name)
        nid = make_id("class", qname, self.filepath)

        bases = []
        base_clause = self._child_by_type(node, 'base_class_clause')
        if base_clause:
            for c in base_clause.children:
                if c.type in ('type_identifier', 'qualified_identifier'):
                    bases.append(self._text(c))

        self.graph.add_node(nid, "class", name, qname, "cpp", self._loc(node),
                            {"bases": bases, "kind": node.type.split('_')[0]})
        self.graph.add_edge(parent, nid, "contains")

        for b in bases:
            bid = make_id("class", b, "")
            if bid not in self.graph.nodes:
                self.graph.add_node(bid, "class", b, b, "cpp",
                                    {"file": "", "line_start": 0, "line_end": 0, "col_start": 0},
                                    {"external": True})
            self.graph.add_edge(nid, bid, "inherits")

        body = self._child_by_type(node, 'field_declaration_list')
        if body:
            self._scope_stack.append(nid)
            for c in body.children:
                self._walk(c)
            self._scope_stack.pop()

    def _handle_function(self, node):
        parent = self._scope_stack[-1]
        parent_type = self.graph.nodes.get(parent, {}).get("type", "")

        # Declarator chain → name
        decl = self._child_by_type(node, 'function_declarator', 'pointer_declarator',
                                   'reference_declarator')
        name = self._extract_function_name(decl) if decl else "<unknown>"
        qname = self._qualified(name)
        ntype = "method" if parent_type == "class" else "function"
        nid = make_id(ntype, qname, self.filepath)

        ret_type = self._extract_return_type(node)
        params = self._extract_params(decl) if decl else []

        self.graph.add_node(nid, ntype, name, qname, "cpp", self._loc(node),
                            {"return_type": ret_type, "params": params})
        self.graph.add_edge(parent, nid, "contains")

        # Walk body for calls
        body = self._child_by_type(node, 'compound_statement')
        if body:
            self._scope_stack.append(nid)
            self._collect_calls(body, nid)
            self._scope_stack.pop()

    def _extract_function_name(self, node) -> str:
        if node is None:
            return "<unknown>"
        for c in node.children:
            if c.type in ('identifier', 'field_identifier', 'qualified_identifier',
                          'destructor_name', 'operator_name'):
                return self._text(c)
            if c.type in ('function_declarator', 'pointer_declarator'):
                return self._extract_function_name(c)
        return "<unknown>"

    def _extract_return_type(self, node) -> str:
        parts = []
        for c in node.children:
            if c.type in ('type_specifier', 'primitive_type', 'type_identifier',
                          'qualified_identifier', 'template_type', 'auto'):
                parts.append(self._text(c))
            elif c.type in ('function_declarator', 'pointer_declarator',
                            'reference_declarator', 'compound_statement'):
                break
        return " ".join(parts) or "auto"

    def _extract_params(self, decl) -> list:
        if decl is None:
            return []
        plist = self._child_by_type(decl, 'parameter_list')
        if not plist:
            return []
        params = []
        for p in plist.children:
            if p.type == 'parameter_declaration':
                ptype = ""
                pname = ""
                for c in p.children:
                    if c.type in ('primitive_type', 'type_identifier', 'qualified_identifier',
                                  'template_type', 'type_specifier'):
                        ptype = self._text(c)
                    elif c.type in ('identifier', 'pointer_declarator', 'reference_declarator'):
                        pname = self._text(c)
                params.append({"name": pname or "_", "type": ptype})
        return params

    def _collect_calls(self, node, caller_id: str):
        if node.type == 'call_expression':
            fn = node.children[0] if node.children else None
            if fn:
                raw = self._text(fn)
                # strip namespace prefix for display
                callee_name = raw.split("::")[-1].split("->")[-1].split(".")[-1][:40]
                callee_id = make_id("function", callee_name, "")
                if callee_id not in self.graph.nodes:
                    self.graph.add_node(callee_id, "function", callee_name, raw, "cpp",
                                        {"file": "", "line_start": 0, "line_end": 0, "col_start": 0},
                                        {"external": True})
                self.graph.add_edge(caller_id, callee_id, "calls")
        for c in node.children:
            self._collect_calls(c, caller_id)

    def _handle_declaration(self, node):
        parent = self._scope_stack[-1]
        # simple variable/field declarations
        type_parts = []
        names = []
        for c in node.children:
            if c.type in ('primitive_type', 'type_identifier', 'qualified_identifier',
                          'template_type', 'type_specifier'):
                type_parts.append(self._text(c))
            elif c.type in ('identifier', 'init_declarator'):
                raw = self._text(c)
                # strip initializer
                name = raw.split("=")[0].strip().split("(")[0].strip()
                if name:
                    names.append(name)
        if not names:
            return
        vtype = " ".join(type_parts)
        for name in names:
            qname = self._qualified(name)
            nid = make_id("variable", qname, self.filepath)
            self.graph.add_node(nid, "variable", name, qname, "cpp", self._loc(node),
                                {"type": vtype})
            self.graph.add_edge(parent, nid, "contains")

    def _handle_include(self, node):
        parent = self._scope_stack[-1]
        path_node = self._child_by_type(node, 'string_literal', 'system_lib_string')
        path = self._text(path_node).strip('<>"') if path_node else ""
        nid = make_id("import", path, self.filepath)
        self.graph.add_node(nid, "import", path, path, "cpp", self._loc(node),
                            {"system": self._text(node).startswith("#include <")})
        self.graph.add_edge(parent, nid, "imports")

    def _handle_using(self, node):
        parent = self._scope_stack[-1]
        for c in node.children:
            if c.type in ('qualified_identifier', 'identifier', 'namespace_identifier'):
                name = self._text(c)
                nid = make_id("import", name, self.filepath)
                self.graph.add_node(nid, "import", name, name, "cpp", self._loc(node),
                                    {"using": True})
                self.graph.add_edge(parent, nid, "imports")
                break


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def detect_language(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    if ext in ('.py',):
        return 'python'
    if ext in ('.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx'):
        return 'cpp'
    raise ValueError(f"Unsupported extension: {ext}")


def parse_file(filepath: str) -> dict:
    source = Path(filepath).read_text(errors='replace')
    lang = detect_language(filepath)
    if lang == 'python':
        graph = PythonParser(source, filepath).parse()
    else:
        graph = CppParser(source, filepath).parse()
    return graph.to_dict()


def main():
    ap = argparse.ArgumentParser(description="Convert C++/Python source to graph YAML.")
    ap.add_argument("sources", nargs="+", help="Source files to parse")
    ap.add_argument("-o", "--output", default=None,
                    help="Output YAML file (default: <source>.graph.yaml)")
    ap.add_argument("--merge", action="store_true",
                    help="Merge multiple source files into a single graph")
    args = ap.parse_args()

    if args.merge and len(args.sources) > 1:
        # Merge all graphs into one
        all_nodes = {}
        all_edges = []
        edge_set = set()
        sources_str = ", ".join(args.sources)
        for src in args.sources:
            g = parse_file(src)['graph']
            for n in g['nodes']:
                all_nodes[n['id']] = n
            for e in g['edges']:
                k = (e['source'], e['target'], e['type'])
                if k not in edge_set:
                    edge_set.add(k)
                    all_edges.append(e)
        result = {"graph": {
            "source_file": sources_str,
            "nodes": list(all_nodes.values()),
            "edges": all_edges,
        }}
        out = args.output or "merged.graph.yaml"
        Path(out).write_text(yaml.dump(result, sort_keys=False, allow_unicode=True))
        print(f"[src2yaml] Merged {len(args.sources)} files → {out}")
        print(f"           {len(all_nodes)} nodes, {len(all_edges)} edges")
    else:
        for src in args.sources:
            result = parse_file(src)
            n = len(result['graph']['nodes'])
            e = len(result['graph']['edges'])
            if args.output and len(args.sources) == 1:
                out = args.output
            else:
                out = src + ".graph.yaml"
            Path(out).write_text(yaml.dump(result, sort_keys=False, allow_unicode=True))
            print(f"[src2yaml] {src} → {out}  ({n} nodes, {e} edges)")


if __name__ == "__main__":
    main()
