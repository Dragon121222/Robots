#!/usr/bin/env python3
"""
yaml2graph — Render a code graph YAML (from src2yaml) as a CG-style image.

Uses Pillow for rendering. Force-directed layout with Barnes-Hut approximation.
Visual style: dark background, neon node glows by type, curved/tapered edges,
directional arrows, type-specific icons encoded as colored rings.

Usage:
  python3 yaml2graph.py graph.yaml [-o output.png] [--width W] [--height H]
               [--iterations N] [--no-externals] [--labels]
"""

import argparse
import math
import random
import sys
from pathlib import Path
from typing import NamedTuple

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ─────────────────────────────────────────────────────────────
# Colour palette (r,g,b as 0-255)
# ─────────────────────────────────────────────────────────────

BG        = (8, 8, 16)

NODE_COLORS = {
    "module":    (0,   200, 255),   # cyan
    "namespace": (80,  255, 200),   # teal
    "class":     (255, 80,  220),   # magenta
    "struct":    (255, 140, 60),    # orange
    "function":  (80,  200, 80),    # green
    "method":    (140, 255, 80),    # lime
    "variable":  (200, 160, 255),   # lavender
    "import":    (255, 220, 40),    # amber
    "lambda":    (255, 100, 100),   # red
}
DEFAULT_COLOR = (160, 160, 160)

EDGE_COLORS = {
    "contains":    (60,  60,  120, 180),
    "calls":       (80,  255, 80,  200),
    "inherits":    (255, 80,  220, 220),
    "imports":     (255, 220, 40,  180),
    "references":  (100, 180, 255, 160),
    "instantiates":(255, 140, 60,  200),
    "overrides":   (255, 80,  80,  200),
    "uses_type":   (180, 100, 255, 180),
}
DEFAULT_EDGE = (120, 120, 200, 160)

# ─────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────

class Vec2(NamedTuple):
    x: float
    y: float

    def __add__(self, o): return Vec2(self.x+o.x, self.y+o.y)
    def __sub__(self, o): return Vec2(self.x-o.x, self.y-o.y)
    def __mul__(self, s): return Vec2(self.x*s, self.y*s)
    def __rmul__(self, s): return self.__mul__(s)
    def length(self): return math.sqrt(self.x**2 + self.y**2)
    def norm(self):
        l = self.length()
        return Vec2(self.x/l, self.y/l) if l > 1e-9 else Vec2(0, 0)
    def clamp(self, maxlen):
        l = self.length()
        return Vec2(self.x/l*maxlen, self.y/l*maxlen) if l > maxlen else self


def force_directed(nodes: list[dict], edges: list[dict],
                   width: int, height: int, iterations: int = 200,
                   seed: int = 42) -> dict[str, Vec2]:
    rng = random.Random(seed)
    ids = [n['id'] for n in nodes]
    pos = {nid: Vec2(rng.uniform(0.1, 0.9)*width, rng.uniform(0.1, 0.9)*height)
           for nid in ids}
    vel = {nid: Vec2(0, 0) for nid in ids}

    # node sizing for repulsion radius
    radii = {n['id']: node_radius(n) for n in nodes}

    k = math.sqrt(width * height / max(len(nodes), 1)) * 1.2
    edge_len_ideal = k * 1.5

    for it in range(iterations):
        t = 1.0 - it / iterations          # temperature schedule
        forces = {nid: Vec2(0, 0) for nid in ids}

        # Repulsion O(N²) — fine for <2000 nodes
        for i, a in enumerate(ids):
            pa = pos[a]
            for b in ids[i+1:]:
                pb = pos[b]
                d = pa - pb
                dist = max(d.length(), 1.0)
                rep_dist = radii[a] + radii[b] + 20
                force_mag = (k**2) / dist + max(0, rep_dist - dist) * 3.0
                fv = d.norm() * force_mag
                forces[a] = forces[a] + fv
                forces[b] = forces[b] + (fv * -1)

        # Attraction along edges
        edge_index: dict[str, set[str]] = {nid: set() for nid in ids}
        for e in edges:
            s, tgt = e.get('source'), e.get('target')
            if s in pos and tgt in pos:
                edge_index[s].add(tgt)
                edge_index[tgt].add(s)

        for e in edges:
            s, tgt = e.get('source'), e.get('target')
            if s not in pos or tgt not in pos:
                continue
            etype = e.get('type', '')
            # contains edges shorter, call edges longer
            if etype == 'contains':
                ideal = edge_len_ideal * 0.6
            elif etype == 'calls':
                ideal = edge_len_ideal * 1.2
            else:
                ideal = edge_len_ideal
            d = pos[tgt] - pos[s]
            dist = max(d.length(), 1.0)
            fmag = (dist - ideal) * 0.04
            fv = d.norm() * fmag
            forces[s] = forces[s] + fv
            forces[tgt] = forces[tgt] + (fv * -1)

        # Center gravity
        cx, cy = width/2, height/2
        for nid in ids:
            grav = Vec2(cx - pos[nid].x, cy - pos[nid].y) * 0.005
            forces[nid] = forces[nid] + grav

        # Integrate
        max_disp = max(5.0, 100 * t)
        for nid in ids:
            vel[nid] = (vel[nid] + forces[nid] * 0.1) * 0.85
            vel[nid] = vel[nid].clamp(max_disp)
            nx = pos[nid].x + vel[nid].x
            ny = pos[nid].y + vel[nid].y
            margin = 60
            nx = max(margin, min(width - margin, nx))
            ny = max(margin, min(height - margin, ny))
            pos[nid] = Vec2(nx, ny)

    return pos


# ─────────────────────────────────────────────────────────────
# Rendering helpers
# ─────────────────────────────────────────────────────────────

def node_radius(node: dict) -> float:
    t = node.get('type', '')
    return {
        "module": 22, "namespace": 18, "class": 16, "struct": 16,
        "function": 12, "method": 11, "variable": 7, "import": 8, "lambda": 9,
    }.get(t, 10)


def rgba_tuple(rgb: tuple, a: int = 255) -> tuple:
    return (*rgb[:3], a)


def blend_color(c: tuple, alpha: float) -> tuple:
    """Apply brightness reduction for glow layers."""
    return tuple(int(v * alpha) for v in c[:3])


def draw_glow_circle(draw_layers: list, cx: float, cy: float, r: float,
                     color: tuple, glow_radius: int = 3):
    """Draw a glowing circle using multiple alpha layers."""
    for layer_img, layer_draw in draw_layers:
        pass  # handled below

def alpha_circle(img: Image.Image, cx: int, cy: int, r: int,
                 color: tuple, alpha: int = 255):
    """Draw a filled circle on an RGBA image."""
    mask = Image.new('L', img.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx-r, cy-r, cx+r, cy+r], fill=alpha)
    colored = Image.new('RGBA', img.size, (*color[:3], 0))
    colored.putalpha(mask)
    img.alpha_composite(colored)


def draw_arrow(draw: ImageDraw.ImageDraw, x1, y1, x2, y2,
               color: tuple, width: int = 2, head_size: int = 10):
    """Draw a line with an arrowhead at (x2,y2)."""
    draw.line([(x1, y1), (x2, y2)], fill=color[:3], width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    for da in [2.5, -2.5]:
        ax = x2 - head_size * math.cos(angle + da * 0.4)
        ay = y2 - head_size * math.sin(angle + da * 0.4)
        draw.line([(x2, y2), (ax, ay)], fill=color[:3], width=max(1, width-1))


def quadratic_bezier(p0, p1, p2, steps=30):
    """Return points along a quadratic bezier curve."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        pts.append((x, y))
    return pts


def draw_curved_edge(layer: Image.Image, draw: ImageDraw.ImageDraw,
                     x1, y1, x2, y2, color_rgba: tuple, width: int = 2,
                     curve_offset: float = 0.15):
    """Draw a curved edge with glow using bezier path."""
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    perp_x = -dy * curve_offset
    perp_y = dx * curve_offset
    ctrl = (mx + perp_x, my + perp_y)

    pts = quadratic_bezier((x1, y1), ctrl, (x2, y2), steps=40)
    ipts = [(int(p[0]), int(p[1])) for p in pts]

    # glow pass
    glow_color = (*color_rgba[:3], color_rgba[3] // 4)
    for w in [width + 4, width + 2]:
        draw.line(ipts, fill=glow_color, width=w)
    draw.line(ipts, fill=color_rgba, width=width)

    # Arrow near target
    if len(pts) >= 2:
        last = pts[-1]
        prev = pts[-3]
        draw_arrow(draw, prev[0], prev[1], last[0], last[1],
                   color_rgba, width=width, head_size=8 + width)


def load_font(size: int):
    for name in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
                 "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
                 "/usr/share/fonts/dejavu/DejaVuSansMono.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────
# Main renderer
# ─────────────────────────────────────────────────────────────

def render_graph(graph_data: dict, width: int, height: int,
                 iterations: int, show_labels: bool,
                 show_externals: bool) -> Image.Image:

    nodes = graph_data['graph']['nodes']
    edges = graph_data['graph']['edges']

    # Filter externals
    if not show_externals:
        external_ids = {n['id'] for n in nodes
                        if n.get('metadata', {}).get('external', False)}
        nodes = [n for n in nodes if n['id'] not in external_ids]
        edges = [e for e in edges
                 if e['source'] not in external_ids and e['target'] not in external_ids]

    if not nodes:
        print("[yaml2graph] Warning: no nodes to render after filtering.")
        nodes = graph_data['graph']['nodes']
        edges = graph_data['graph']['edges']

    node_ids = {n['id'] for n in nodes}

    # Layout
    print(f"[yaml2graph] Running force-directed layout on {len(nodes)} nodes, "
          f"{len(edges)} edges …")
    pos = force_directed(nodes, edges, width, height, iterations)

    # Base canvas
    img = Image.new('RGBA', (width, height), (*BG, 255))

    # ── Background grid ──────────────────────────────────────
    grid_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid_layer)
    grid_spacing = 60
    grid_color = (30, 30, 60, 80)
    for x in range(0, width, grid_spacing):
        gd.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, grid_spacing):
        gd.line([(0, y), (width, y)], fill=grid_color, width=1)
    img.alpha_composite(grid_layer)

    # ── Edges ────────────────────────────────────────────────
    edge_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge_layer)

    # Group parallel edges to apply different curve offsets
    edge_pair_count: dict[tuple, int] = {}
    for e in edges:
        s, t = e.get('source', ''), e.get('target', '')
        if s in pos and t in pos:
            key = (min(s,t), max(s,t))
            edge_pair_count[key] = edge_pair_count.get(key, 0) + 1
    edge_pair_idx: dict[tuple, int] = {}

    for e in edges:
        s, t = e.get('source', ''), e.get('target', '')
        if s not in pos or t not in pos:
            continue
        etype = e.get('type', '')
        color_rgba = EDGE_COLORS.get(etype, DEFAULT_EDGE)

        ps, pt = pos[s], pos[t]
        rs, rt = node_radius(next((n for n in nodes if n['id']==s), {})), \
                 node_radius(next((n for n in nodes if n['id']==t), {}))

        # Shorten to node boundary
        d = Vec2(pt.x - ps.x, pt.y - ps.y)
        dist = max(d.length(), 1.0)
        norm = d.norm()
        sx = ps.x + norm.x * rs
        sy = ps.y + norm.y * rs
        ex = pt.x - norm.x * rt
        ey = pt.y - norm.y * rt

        key = (min(s,t), max(s,t))
        idx = edge_pair_idx.get(key, 0)
        edge_pair_idx[key] = idx + 1
        total = edge_pair_count.get(key, 1)
        offset = (idx - total/2 + 0.5) * 0.2 if total > 1 else 0.12

        width_px = {"contains": 1, "calls": 2, "inherits": 3,
                    "imports": 1, "references": 1}.get(etype, 2)

        draw_curved_edge(edge_layer, ed, sx, sy, ex, ey,
                         color_rgba, width=width_px, curve_offset=offset)

    img.alpha_composite(edge_layer)

    # ── Nodes ────────────────────────────────────────────────
    node_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    nd = ImageDraw.Draw(node_layer)

    node_map = {n['id']: n for n in nodes}

    for n in nodes:
        nid = n['id']
        if nid not in pos:
            continue
        p = pos[nid]
        cx, cy = int(p.x), int(p.y)
        r = int(node_radius(n))
        color = NODE_COLORS.get(n.get('type', ''), DEFAULT_COLOR)
        is_external = n.get('metadata', {}).get('external', False)

        if is_external:
            color = tuple(v // 3 for v in color)

        # Glow rings (multiple dilated circles)
        for gr, ga in [(r+10, 30), (r+6, 60), (r+3, 100)]:
            alpha_circle(node_layer, cx, cy, gr, color, ga)

        # Core fill (dark center with colored ring)
        alpha_circle(node_layer, cx, cy, r, color, 255)
        alpha_circle(node_layer, cx, cy, max(1, r-3), (20, 20, 35), 220)

        # Type indicator inner dot
        inner_color = tuple(min(255, v + 80) for v in color)
        alpha_circle(node_layer, cx, cy, max(1, r//3), inner_color, 200)

    img.alpha_composite(node_layer)

    # ── Labels ───────────────────────────────────────────────
    label_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    ld = ImageDraw.Draw(label_layer)
    font_sm = load_font(10)
    font_md = load_font(12)

    for n in nodes:
        nid = n['id']
        if nid not in pos:
            continue
        p = pos[nid]
        cx, cy = int(p.x), int(p.y)
        r = int(node_radius(n))
        color = NODE_COLORS.get(n.get('type', ''), DEFAULT_COLOR)
        is_external = n.get('metadata', {}).get('external', False)
        if is_external:
            color = tuple(v // 2 for v in color)

        ntype = n.get('type', '')
        name = n.get('name', '')[:20]

        if show_labels or ntype in ('module', 'class', 'namespace'):
            font = font_md if ntype in ('module', 'class') else font_sm
            try:
                bbox = ld.textbbox((0, 0), name, font=font)
                tw = bbox[2] - bbox[0]
            except Exception:
                tw = len(name) * 6
            tx = cx - tw // 2
            ty = cy + r + 4

            # shadow
            ld.text((tx+1, ty+1), name, fill=(0, 0, 0, 200), font=font)
            ld.text((tx, ty), name, fill=(*color, 220), font=font)

            # type badge above node
            badge = ntype[:3].upper()
            try:
                bbadge = ld.textbbox((0,0), badge, font=font_sm)
                bw = bbadge[2] - bbadge[0]
            except Exception:
                bw = len(badge) * 5
            ld.text((cx - bw//2, cy - r - 14), badge,
                    fill=(*color, 160), font=font_sm)

    img.alpha_composite(label_layer)

    # ── Legend ───────────────────────────────────────────────
    legend_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    lgd = ImageDraw.Draw(legend_layer)
    font_lg = load_font(11)

    lx, ly = 16, 16
    lgd.rectangle([lx-6, ly-6, lx+140, ly + len(NODE_COLORS)*16 + 8],
                  fill=(15, 15, 30, 200))
    lgd.text((lx, ly), "NODE TYPES", fill=(200, 200, 255, 200), font=font_lg)
    ly += 16
    for ntype, col in NODE_COLORS.items():
        alpha_circle(legend_layer, lx+5, ly+5, 5, col, 220)
        lgd.text((lx+14, ly), ntype, fill=(*col, 200), font=font_lg)
        ly += 14

    ly += 10
    lgd.rectangle([lx-6, ly-6, lx+140, ly + len(EDGE_COLORS)*14 + 8],
                  fill=(15, 15, 30, 200))
    lgd.text((lx, ly), "EDGE TYPES", fill=(200, 200, 255, 200), font=font_lg)
    ly += 16
    for etype, col in EDGE_COLORS.items():
        lgd.line([(lx, ly+6), (lx+12, ly+6)], fill=col[:3], width=2)
        lgd.text((lx+16, ly), etype, fill=(*col[:3], 200), font=font_lg)
        ly += 14

    img.alpha_composite(legend_layer)

    # ── Stats ────────────────────────────────────────────────
    stats_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stats_layer)
    font_stats = load_font(10)
    src = graph_data['graph'].get('source_file', '')
    stats = [
        Path(src).name if src else '',
        f"{len(nodes)} nodes  {len(edges)} edges",
    ]
    sy = height - 28
    for s in stats:
        sd.text((width - 200, sy), s, fill=(100, 100, 160, 200), font=font_stats)
        sy += 12
    img.alpha_composite(stats_layer)

    # Final blur pass for ambient glow
    glow_pass = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    img = Image.blend(img, glow_pass, alpha=0.25)

    return img.convert('RGB')


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Render a code graph YAML as a CG-style image.")
    ap.add_argument("yaml_file", help="Input graph YAML from src2yaml")
    ap.add_argument("-o", "--output", default=None,
                    help="Output image (default: <yaml>.png)")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--iterations", type=int, default=300,
                    help="Force-directed layout iterations (default: 300)")
    ap.add_argument("--labels", action="store_true",
                    help="Show labels on all nodes (default: modules/classes/namespaces only)")
    ap.add_argument("--no-externals", dest="no_externals", action="store_true",
                    help="Hide external/library nodes")
    args = ap.parse_args()

    data = yaml.safe_load(Path(args.yaml_file).read_text())
    if 'graph' not in data:
        print("Error: YAML does not contain a 'graph' key.", file=sys.stderr)
        sys.exit(1)

    img = render_graph(
        data,
        width=args.width,
        height=args.height,
        iterations=args.iterations,
        show_labels=args.labels,
        show_externals=not args.no_externals,
    )

    out = args.output or (args.yaml_file + ".png")
    img.save(out)
    print(f"[yaml2graph] → {out}  ({args.width}×{args.height})")


if __name__ == "__main__":
    main()
