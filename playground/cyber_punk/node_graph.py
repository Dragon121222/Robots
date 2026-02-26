#!/usr/bin/env python3
"""
node_graph.py — text-mode node graph example for cyber_tui

Nodes are boxes with a title and ports.
Edges connect output ports to input ports via ASCII routing.

Controls:
  [↑↓←→]  move selected node
  [Tab]    cycle selected node
  [q]      quit
  Two-finger swipe to pan the graph view
"""

import curses
import random
from dataclasses import dataclass, field
from cyber_punk.cyber_tui import CyberTUI, C_CYAN, C_MAGENTA, C_GREEN, C_YELLOW, C_DIM, C_WHITE, C_RED

# ── Graph data structures ──────────────────────────────────────────────────────

@dataclass
class Port:
    name:  str
    kind:  str   # 'in' | 'out'

@dataclass
class Node:
    id:      str
    title:   str
    x:       int          # position in graph-space (cols)
    y:       int          # position in graph-space (rows)
    inputs:  list[Port]   = field(default_factory=list)
    outputs: list[Port]   = field(default_factory=list)
    value:   str          = ''   # optional status/value line

    def width(self):
        max_label = max(
            (len(p.name) for p in self.inputs + self.outputs),
            default=0
        )
        return max(len(self.title) + 4, max_label + 6, 14)

    def height(self):
        # title row + separator + max(inputs, outputs) rows + bottom border
        return max(len(self.inputs), len(self.outputs)) + 3 + (1 if self.value else 0)

    def port_row(self, port_index: int) -> int:
        """Graph-space row of a port (relative to node y)."""
        return self.y + 2 + port_index   # +2 = title + separator

    def in_port_col(self) -> int:
        return self.x                    # left edge

    def out_port_col(self) -> int:
        return self.x + self.width() - 1 # right edge


@dataclass
class Edge:
    src_id:   str
    src_port: int   # output port index
    dst_id:   str
    dst_port: int   # input port index


class Graph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge]      = []

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        return node

    def add_edge(self, src_id, src_port, dst_id, dst_port):
        self.edges.append(Edge(src_id, src_port, dst_id, dst_port))


# ── Renderer ───────────────────────────────────────────────────────────────────

class GraphRenderer:
    """Renders a Graph into a curses panel box with panning and selection."""

    NODE_BORDER   = C_CYAN
    NODE_SEL      = C_MAGENTA
    PORT_IN       = C_GREEN
    PORT_OUT      = C_YELLOW
    EDGE_COLOR    = C_DIM
    TITLE_COLOR   = C_WHITE
    VALUE_COLOR   = C_GREEN

    def __init__(self, app: CyberTUI, graph: Graph):
        self.app   = app
        self.graph = graph
        self.pan_x = 0
        self.pan_y = 0
        self.selected_id: str | None = None

    def _node_ids(self):
        return list(self.graph.nodes.keys())

    def select_next(self):
        ids = self._node_ids()
        if not ids: return
        if self.selected_id not in ids:
            self.selected_id = ids[0]
        else:
            i = ids.index(self.selected_id)
            self.selected_id = ids[(i + 1) % len(ids)]

    def move_selected(self, dx, dy):
        if self.selected_id and self.selected_id in self.graph.nodes:
            n = self.graph.nodes[self.selected_id]
            n.x = max(0, n.x + dx)
            n.y = max(0, n.y + dy)

    def pan(self, dx, dy):
        self.pan_x += dx
        self.pan_y += dy

    # graph-space → screen-space (relative to box inner origin)
    def _sx(self, gx, origin_x): return gx - self.pan_x + origin_x
    def _sy(self, gy, origin_y): return gy - self.pan_y + origin_y

    def draw(self, scr, box):
        inner  = box.inner()
        ox, oy = inner.x1, inner.y1
        iw, ih = inner.w, inner.h

        # Draw edges first (behind nodes)
        self._draw_edges(scr, ox, oy, iw, ih)

        # Draw nodes
        for node in self.graph.nodes.values():
            self._draw_node(scr, node, ox, oy, iw, ih)

    def _clip(self, scr, sy, sx, text, attr, box_w, box_h, ox, oy):
        """putch only if within inner bounds."""
        if oy <= sy < oy + box_h and ox <= sx < ox + box_w:
            self.app.putch(scr, sy, sx, text, attr)

    def _draw_node(self, scr, node: Node, ox, oy, iw, ih):
        app = self.app
        sx  = self._sx(node.x, ox)
        sy  = self._sy(node.y, oy)
        w   = node.width()
        h   = node.height()
        sel = (node.id == self.selected_id)

        bc  = app.attr(self.NODE_SEL, bold=True) if sel else app.attr(self.NODE_BORDER)
        tc  = app.attr(self.TITLE_COLOR, bold=True)

        def put(dy, dx, ch, attr):
            self._clip(scr, sy+dy, sx+dx, ch, attr, iw, ih, ox, oy)

        # Border
        put(0,   0,   '╔', bc);  put(0,   w-1, '╗', bc)
        put(h-1, 0,   '╚', bc);  put(h-1, w-1, '╝', bc)
        for c in range(1, w-1):
            put(0,   c, '═', bc)
            put(h-1, c, '═', bc)
            put(2,   c, '─', app.attr(C_DIM))
        for r in range(1, h-1):
            put(r, 0,   '║', bc)
            put(r, w-1, '║', bc)

        # Title (centered)
        title = node.title[:w-2]
        tx = (w - len(title)) // 2
        put(1, tx, title, tc)

        # Value line (bottom, if present)
        if node.value:
            val = node.value[:w-4]
            put(h-2, 2, val, app.attr(self.VALUE_COLOR))

        # Input ports (left side)
        for i, port in enumerate(node.inputs):
            pr = 3 + i
            put(pr, 0,   '├', app.attr(self.PORT_IN, bold=True))
            put(pr, 1,   f'{port.name[:w//2-1]}', app.attr(self.PORT_IN))

        # Output ports (right side)
        for i, port in enumerate(node.outputs):
            pr  = 3 + i
            lbl = port.name[:w//2-1]
            px  = w - 1 - len(lbl) - 1
            put(pr, px,  lbl,  app.attr(self.PORT_OUT))
            put(pr, w-1, '┤',  app.attr(self.PORT_OUT, bold=True))

    def _draw_edges(self, scr, ox, oy, iw, ih):
        """Simple L-shaped edge routing: horizontal then vertical then horizontal."""
        app = self.app
        g   = self.graph
        ec  = app.attr(self.EDGE_COLOR)

        for edge in g.edges:
            src = g.nodes.get(edge.src_id)
            dst = g.nodes.get(edge.dst_id)
            if not src or not dst: continue

            # Anchor points in graph-space
            gx0 = src.out_port_col()
            gy0 = src.port_row(edge.src_port)
            gx1 = dst.in_port_col()
            gy1 = dst.port_row(edge.dst_port)

            # Convert to screen
            x0 = self._sx(gx0, ox);  y0 = self._sy(gy0, oy)
            x1 = self._sx(gx1, ox);  y1 = self._sy(gy1, oy)

            mid_x = (x0 + x1) // 2

            def put(sy, sx, ch):
                self._clip(scr, sy, sx, ch, ec, iw, ih, ox, oy)

            # Horizontal leg from source
            step = 1 if mid_x > x0 else -1
            for cx in range(x0, mid_x, step):
                put(y0, cx, '─')

            # Vertical leg
            step = 1 if y1 > y0 else -1
            for cy in range(y0, y1, step):
                put(cy, mid_x, '│')

            # Horizontal leg to dest
            step = 1 if x1 > mid_x else -1
            for cx in range(mid_x, x1, step):
                put(y1, cx, '─')

            # Arrow tip
            put(y1, x1, '►')


# ── Demo app ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app = CyberTUI(tick_ms=100)

    # Build a sample graph
    g = Graph()

    g.add_node(Node(
        id='cam', title='CAMERA',  x=2,  y=2,
        inputs=[],
        outputs=[Port('frame', 'out'), Port('meta', 'out')],
        value='1920×1080 @ 30fps',
    ))
    g.add_node(Node(
        id='yolo', title='YOLO v8',  x=26, y=1,
        inputs=[Port('frame', 'in')],
        outputs=[Port('detections', 'out'), Port('mask', 'out')],
        value='NPU 87% util',
    ))
    g.add_node(Node(
        id='track', title='TRACKER', x=26, y=12,
        inputs=[Port('meta', 'in')],
        outputs=[Port('tracks', 'out')],
        value='12 active',
    ))
    g.add_node(Node(
        id='fuse', title='FUSION',  x=50, y=5,
        inputs=[Port('detections', 'in'), Port('tracks', 'in'), Port('mask', 'in')],
        outputs=[Port('objects', 'out')],
        value='',
    ))
    g.add_node(Node(
        id='ctrl', title='CONTROL', x=74, y=5,
        inputs=[Port('objects', 'in')],
        outputs=[Port('cmd', 'out')],
        value='state: TRACK',
    ))

    g.add_edge('cam',   0, 'yolo',  0)   # frame  → yolo
    g.add_edge('cam',   1, 'track', 0)   # meta   → tracker
    g.add_edge('yolo',  0, 'fuse',  0)   # detections → fusion
    g.add_edge('track', 0, 'fuse',  1)   # tracks → fusion
    g.add_edge('yolo',  1, 'fuse',  2)   # mask   → fusion
    g.add_edge('fuse',  0, 'ctrl',  0)   # objects → control

    renderer = GraphRenderer(app, g)
    renderer.selected_id = 'cam'

    app.state['tick'] = 0

    # ── Panel ──────────────────────────────────────────────────────────────────

    @app.panel(x=0, y=0, w=1.0, h=0.9, title='NODE GRAPH',
               border_color=C_DIM, title_color=C_MAGENTA)
    def panel_graph(scr, box, state):
        renderer.draw(scr, box)

    @app.panel(x=0, y=0.9, w=1.0, h=0.1, border=False)
    def panel_hint(scr, box, state):
        sel = renderer.selected_id or '—'
        node = g.nodes.get(sel)
        val  = f'  {node.value}' if node and node.value else ''
        app.putch(scr, box.y1, box.x1,
                  f'  selected: [{sel}]{val}',
                  app.attr(C_CYAN))
        app.putch(scr, box.y1+1, box.x1,
                  '  [Tab]select  [↑↓←→]move node  [WASD]pan  [q]quit',
                  app.attr(C_DIM))

    # ── Updater ────────────────────────────────────────────────────────────────

    @app.updater
    def tick(state):
        state['tick'] += 1
        # Animate node values to feel live
        if state['tick'] % 10 == 0:
            yolo = g.nodes['yolo']
            yolo.value = f'NPU {random.randint(70,99)}% util'
            track = g.nodes['track']
            track.value = f'{random.randint(8,20)} active'

    # ── Keybinds ───────────────────────────────────────────────────────────────

    @app.on_key('\t')
    def cycle(state): renderer.select_next()

    @app.on_key(curses.KEY_UP)
    def mv_up(state):    renderer.move_selected(0, -1)

    @app.on_key(curses.KEY_DOWN)
    def mv_dn(state):    renderer.move_selected(0,  1)

    @app.on_key(curses.KEY_LEFT)
    def mv_lt(state):    renderer.move_selected(-2, 0)

    @app.on_key(curses.KEY_RIGHT)
    def mv_rt(state):    renderer.move_selected( 2, 0)

    # WASD to pan
    @app.on_key('w')
    def pan_up(state):   renderer.pan( 0, -1)

    @app.on_key('s')
    def pan_dn(state):   renderer.pan( 0,  1)

    @app.on_key('a')
    def pan_lt(state):   renderer.pan(-2,  0)

    @app.on_key('d')
    def pan_rt(state):   renderer.pan( 2,  0)

    app.run()
