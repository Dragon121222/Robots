#!/usr/bin/env python3
"""@file game_tui.py  Matrix-based TUI game engine with fg/bg layer rendering."""

from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional


# ── Color ─────────────────────────────────────────────────────────────────────

def _hex_to_256(h: str) -> int:
    """@brief '#rrggbb' → nearest xterm-256 index."""
    h = h.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    if r == g == b:
        if r < 8:   return 16
        if r > 248: return 231
        return round((r - 8) / 247 * 24) + 232
    return 16 + 36*round(r/255*5) + 6*round(g/255*5) + round(b/255*5)

_color_cache: dict[tuple, int] = {}  # (fg_idx, bg_idx) → pair id
_next_pair = [1]

def _get_pair(fg: str, bg: str = '') -> int:
    """@brief Return curses pair id for (fg, bg) hex strings.
    bg='' means default terminal background (-1).
    """
    fi = _hex_to_256(fg) if fg else -1
    bi = _hex_to_256(bg) if bg else -1
    key = (fi, bi)
    if key not in _color_cache:
        pid = _next_pair[0]; _next_pair[0] += 1
        curses.init_pair(pid, fi, bi)
        _color_cache[key] = pid
    return _color_cache[key]


# ── GameObject ────────────────────────────────────────────────────────────────
class GameObject:
    """@brief A single character occupying a cell in the matrix.

    @param x          Column (uint).
    @param y          Row (uint).
    @param character  Glyph to draw.
    @param color      Hex foreground color '#rrggbb'.
    @param collision  If True, blocks other objects from entering this cell.
    @param layer      'bg' or 'fg'.
                      bg objects set the terminal background color for their cell.
                      fg objects draw their character+color over the bg; they do
                      not affect the background color.
    @param bg_color   Background fill color (hex). Only meaningful when layer='bg'.
    @param description  Optional text shown in the info panel.
    """

    def __init__(self, x: int, y: int, character: str,
                 color:       str  = '#ffffff',
                 collision:   bool = False,
                 layer:       str  = 'fg',
                 bg_color:    str  = '',
                 description: str  = ''):
        self.x           = int(x)
        self.y           = int(y)
        self.character   = character
        self.color       = color        # foreground hex
        self.bg_color    = bg_color     # background hex (bg layer only)
        self.collision   = collision
        self.layer       = layer        # 'bg' or 'fg'
        self.description = description
        self.i           = 0
        self._matrix: Optional['Matrix'] = None

    def move(self, dx: int, dy: int) -> bool:
        """@brief Move to (x+dx, y+dy) if the destination allows it."""
        if self._matrix is None: return False
        return self._matrix.move_object(self, self.x + dx, self.y + dy)

    def update(self, dt: float): pass
    def on_key(self, key: int) -> bool: return False


# ── Matrix ────────────────────────────────────────────────────────────────────
class Matrix:
    """@brief 2-D grid of per-cell queues split into bg and fg sublists.

    Each cell holds objects in insertion order.
    Rendering rule per cell:
      - background color  = top bg object's bg_color   (or '' if none)
      - foreground char   = top fg object's character  (or top bg object's character)
      - foreground color  = top fg object's color      (or top bg object's color)
    """

    def __init__(self, cols: int, rows: int):
        self.cols, self.rows = cols, rows
        self._cells:   dict[tuple, list[GameObject]] = {}
        self._objects: list[GameObject]              = []

    def add(self, obj: GameObject) -> 'Matrix':
        obj._matrix = self
        self._objects.append(obj)
        q = self._cells.setdefault((obj.x, obj.y), [])
        q.append(obj)
        obj.i = len(q) - 1
        return self

    def remove(self, obj: GameObject) -> 'Matrix':
        self._dequeue(obj)
        try: self._objects.remove(obj)
        except ValueError: pass
        obj._matrix = None
        return self

    def move_object(self, obj: GameObject, nx: int, ny: int) -> bool:
        if not (0 <= nx < self.cols and 0 <= ny < self.rows): return False
        dest = self._cells.get((nx, ny), [])
        # Collision: blocked if any object in dest has collision=True
        if any(o.collision for o in dest): return False
        self._dequeue(obj)
        obj.x, obj.y = nx, ny
        q = self._cells.setdefault((nx, ny), [])
        q.append(obj)
        obj.i = len(q) - 1
        return True

    def _dequeue(self, obj: GameObject):
        key = (obj.x, obj.y)
        q   = self._cells.get(key, [])
        if obj in q:
            idx = q.index(obj)
            q.pop(idx)
            for k in range(idx, len(q)): q[k].i = k
        if not q: self._cells.pop(key, None)

    def resolve(self, x: int, y: int) -> tuple[str, str, str, Optional[GameObject]]:
        """@brief Compute (character, fg_hex, bg_hex, top_obj) for cell (x,y).
        Returns ('', '', '', None) for empty cells.
        """
        q = self._cells.get((x, y))
        if not q: return '', '', '', None
        bgs = [o for o in q if o.layer == 'bg']
        fgs = [o for o in q if o.layer == 'fg']
        top_bg = bgs[-1] if bgs else None
        top_fg = fgs[-1] if fgs else None
        bg_hex = top_bg.bg_color if top_bg else ''
        if top_fg:
            return top_fg.character, top_fg.color, bg_hex, top_fg
        elif top_bg:
            return top_bg.character, top_bg.color, bg_hex, top_bg
        return '', '', '', None

    def top(self, x: int, y: int) -> Optional[GameObject]:
        q = self._cells.get((x, y))
        return q[-1] if q else None

    def queue_at(self, x: int, y: int) -> list[GameObject]:
        return list(self._cells.get((x, y), []))

    def by_type(self, cls) -> list:
        return [o for o in self._objects if isinstance(o, cls)]

    def by_tag(self, tag: str) -> list:
        return [o for o in self._objects if hasattr(o, 'tags') and tag in o.tags]

    def update(self, dt: float):
        for obj in list(self._objects): obj.update(dt)

    def on_key(self, key: int) -> bool:
        for obj in reversed(self._objects):
            if obj.on_key(key): return True
        return False


# ── Renderer ──────────────────────────────────────────────────────────────────

@dataclass
class _Committed:
    ch: str; fg: str; bg: str

class Renderer:
    """@brief Diffs matrix.resolve() against last frame; writes only changed cells."""

    def __init__(self):
        self._committed: dict[tuple, _Committed] = {}

    def flush(self, scr, matrix: Matrix, row0: int, col0: int, h: int, w: int):
        H, W  = scr.getmaxyx()
        drawn: set[tuple] = set()

        for (x, y) in list(matrix._cells.keys()):
            if not (0 <= x*2+1 < w and 0 <= y < h): continue
            ch, fg, bg, _ = matrix.resolve(x, y)
            if not ch: continue
            key    = (x, y)
            ar, ac = row0 + y, col0 + x*2
            if ar >= H or ac >= W: continue
            drawn.add(key)
            prev = self._committed.get(key)
            if prev and prev.ch == ch and prev.fg == fg and prev.bg == bg: continue
            pair = _get_pair(fg, bg)
            try:
                scr.addstr(ar, ac, ch, curses.color_pair(pair))
                self._committed[key] = _Committed(ch=ch, fg=fg, bg=bg)
            except curses.error:
                pass

        for key in list(self._committed):
            if key in drawn: continue
            x, y   = key
            ar, ac = row0 + y, col0 + x*2
            if 0 <= ar < H and 0 <= ac < W:
                try: scr.addstr(ar, ac, '  ', 0)
                except curses.error: pass
            del self._committed[key]

    def invalidate(self): self._committed.clear()


# ── Info panel state ──────────────────────────────────────────────────────────

@dataclass
class InfoState:
    """@brief Shared state for the info panel."""
    selected: Optional[GameObject] = None
    log:      list[str]            = field(default_factory=list)

    def select(self, obj: Optional[GameObject]):
        self.selected = obj

    def log_append(self, msg: str):
        self.log.append(msg)
        if len(self.log) > 100: self.log.pop(0)


# ── Panel ─────────────────────────────────────────────────────────────────────

@dataclass
class PanelDef:
    fn:           Callable
    x: float;    y: float
    w: float;    h: float
    title:        str              = ''
    border:       bool             = True
    border_color: str              = '#444444'
    title_color:  str              = '#00ffff'
    matrix:       Optional[Matrix] = None
    _renderer:    Renderer         = field(default_factory=Renderer)


# ── GameTUI ───────────────────────────────────────────────────────────────────

class GameTUI:
    """@brief Curses game loop with matrix rendering and info panel support.
    @param fps Target frames per second.
    """

    def __init__(self, fps: int = 30):
        self.fps     = fps
        self.state   = {}
        self.info    = InfoState()
        self._panels:   list[PanelDef]      = []
        self._keys:     dict[int, Callable] = {}
        self._updaters: list[Callable]      = []
        self._running    = False
        self._scr        = None
        self._prev_size  = (0, 0)
        self.active_matrix: Optional[Matrix] = None
        # Track which panel+matrix the mouse is over for click→cell mapping
        self._matrix_panels: list[tuple[PanelDef, Matrix]] = []

    def panel(self, x=0.0, y=0.0, w=1.0, h=1.0,
              title='', border=True,
              border_color='#444444', title_color='#00ffff',
              matrix: Matrix = None, name=''):
        """@brief Register a panel. fn signature: fn(scr, inner, ctx, dt).
        inner = (row0, col0, h, w).  ctx = matrix or app.state.
        """
        def decorator(fn):
            self._panels.append(PanelDef(
                fn=fn, x=x, y=y, w=w, h=h,
                title=title, border=border,
                border_color=border_color, title_color=title_color,
                matrix=matrix,
            ))
            return fn
        return decorator

    def on_key(self, key):
        """@brief Register a global keypress handler: fn(state, dt)."""
        def decorator(fn):
            keys = key if isinstance(key, list) else [key]
            for k in keys:
                self._keys[ord(k) if isinstance(k, str) else k] = fn
            return fn
        return decorator

    @property
    def updater(self):
        """@brief Register a per-frame updater: fn(state, dt)."""
        def decorator(fn):
            self._updaters.append(fn); return fn
        return decorator

    def quit(self): self._running = False

    def _res(self, v, total) -> int:
        return int(v * total) if isinstance(v, float) else int(v)

    def _inner(self, p: PanelDef, H: int, W: int) -> tuple[int,int,int,int]:
        x1 = self._res(p.x, W); y1 = self._res(p.y, H)
        pw = self._res(p.w, W); ph = self._res(p.h, H)
        if p.border: return y1+1, x1+1, max(0,ph-2), max(0,pw-2)
        return y1, x1, ph, pw

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()

    def _draw_border(self, scr, p: PanelDef, H: int, W: int):
        x1 = self._res(p.x, W); y1 = self._res(p.y, H)
        pw = self._res(p.w, W); ph = self._res(p.h, H)
        ba = curses.color_pair(_get_pair(p.border_color))
        ta = curses.color_pair(_get_pair(p.title_color)) | curses.A_BOLD
        def _p(r, c, ch, a):
            if 0 <= r < H and 0 <= c < W:
                try: scr.addstr(r, c, ch, a)
                except curses.error: pass
        _p(y1,      x1,       '╔', ba); _p(y1,      x1+pw-1, '╗', ba)
        _p(y1+ph-1, x1,       '╚', ba); _p(y1+ph-1, x1+pw-1, '╝', ba)
        for i in range(1, pw-1): _p(y1,      x1+i,    '═', ba)
        for i in range(1, pw-1): _p(y1+ph-1, x1+i,    '═', ba)
        for i in range(1, ph-1): _p(y1+i,    x1,      '║', ba)
        for i in range(1, ph-1): _p(y1+i,    x1+pw-1, '║', ba)
        if p.title:
            t  = f' {p.title} '
            tc = x1 + max(1, (pw - len(t)) // 2)
            _p(y1, tc, t, ta)

    def _render(self, scr, dt: float):
        H, W = scr.getmaxyx()
        if (H, W) != self._prev_size:
            self._prev_size = (H, W)
            scr.erase(); scr.refresh()
            for p in self._panels: p._renderer.invalidate()

        for p in self._panels:
            if p.border: self._draw_border(scr, p, H, W)
            row0, col0, ih, iw = self._inner(p, H, W)
            ctx = p.matrix if p.matrix is not None else self.state
            p.fn(scr, (row0, col0, ih, iw), ctx, dt)
            if p.matrix is not None:
                p._renderer.flush(scr, p.matrix, row0, col0, ih, iw)

        scr.refresh()

    def _handle_mouse(self, scr):
        try:
            _, mx, my, _, bstate = curses.getmouse()
            if not (bstate & curses.BUTTON1_CLICKED): return
            H, W = scr.getmaxyx()
            for p in self._panels:
                if p.matrix is None: continue
                row0, col0, ih, iw = self._inner(p, H, W)
                # Convert terminal col → logical matrix col (divide by 2)
                lx = (mx - col0) // 2
                ly = my - row0
                if 0 <= lx < p.matrix.cols and 0 <= ly < p.matrix.rows:
                    _, _, _, obj = p.matrix.resolve(lx, ly)
                    self.info.select(obj)
                    return
        except curses.error:
            pass

    def _handle_input(self, scr, dt: float) -> bool:
        scr.timeout(max(1, int(1000 / self.fps)))
        key = scr.getch()
        if key == -1: return True
        if key == curses.KEY_MOUSE:
            self._handle_mouse(scr); return True
        handler = self._keys.get(key)
        if handler: handler(self.state, dt); return self._running
        if self.active_matrix and self.active_matrix.on_key(key): return self._running
        for p in self._panels:
            if p.matrix and p.matrix.on_key(key): break
        return self._running

    def _main(self, scr):
        self._scr = scr; self._running = True
        self._init_colors()
        curses.curs_set(0)
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        prev = time.perf_counter()
        while self._running:
            now = time.perf_counter(); dt = now - prev; prev = now
            for fn in self._updaters: fn(self.state, dt)
            for p  in self._panels:
                if p.matrix: p.matrix.update(dt)
            self._render(scr, dt)
            self._handle_input(scr, dt)

    def run(self):
        try:    curses.wrapper(self._main)
        except KeyboardInterrupt: pass
        finally: self._running = False
        print('\033[0m')


# ── Info panel helper ─────────────────────────────────────────────────────────

def draw_info_panel(scr, inner: tuple, info: InfoState, title_color: str = '#00ffff'):
    """@brief Standard info panel draw function.
    Pass as the fn argument to app.panel() for the info panel.
    Displays selected object's character, colors, position, description, and log.

    Usage:
        @app.panel(x=0.75, y=0, w=0.25, h=1.0, title='INFO')
        def info_panel(scr, inner, ctx, dt):
            draw_info_panel(scr, inner, app.info)
    """
    row0, col0, h, w = inner
    # Clear panel before redraw
    blank = " " * w
    for r in range(h):
        try: scr.addstr(row0+r, col0, blank)
        except curses.error: pass
    dim  = curses.color_pair(_get_pair('#555555'))
    hi   = curses.color_pair(_get_pair(title_color)) | curses.A_BOLD
    norm = curses.color_pair(_get_pair('#cccccc'))

    def _p(r, text, a=0):
        if r >= h: return
        try: scr.addstr(row0+r, col0, str(text)[:w], a)
        except curses.error: pass

    def _hline(r):
        if r >= h: return
        try: scr.addstr(row0+r, col0, '─' * w, dim)
        except curses.error: pass

    r = 0
    obj = info.selected
    if obj:
        # Glyph preview with its actual colors
        pair = _get_pair(obj.color, obj.bg_color if obj.layer == 'bg' else '')
        _p(r, ' char  ', dim)
        try: scr.addstr(row0+r, col0+7, obj.character, curses.color_pair(pair) | curses.A_BOLD)
        except curses.error: pass
        r += 1
        _p(r, f' pos   {obj.x},{obj.y}', norm);   r += 1
        _p(r, f' layer {obj.layer}',      norm);   r += 1
        _p(r, f' fg    {obj.color}',      norm);   r += 1
        if obj.layer == 'bg':
            _p(r, f' bg    {obj.bg_color or "term"}', norm); r += 1
        _p(r, f' coll  {obj.collision}',  norm);   r += 1
        if obj.description:
            _hline(r); r += 1
            _p(r, ' desc', dim); r += 1
            # Word-wrap description
            words = obj.description.split()
            line  = ''
            for w_ in words:
                if len(line) + len(w_) + 1 > w - 2:
                    _p(r, ' ' + line, norm); r += 1; line = w_
                else:
                    line = (line + ' ' + w_).strip()
            if line: _p(r, ' ' + line, norm); r += 1
    else:
        _p(r, ' click a cell', dim); r += 1

    # Log section
    _hline(r); r += 1
    _p(r, ' log', dim); r += 1
    log_rows = h - r
    for line in info.log[-log_rows:]:
        _p(r, ' ' + line[:w-1], dim); r += 1


# ── Terrain generation ────────────────────────────────────────────────────────

def _smooth_noise(x: float, y: float, seed: int = 0) -> float:
    """@brief Smooth lattice noise in [0,1]."""
    def _hash(ix, iy):
        h = (ix*1619 + iy*31337 + seed*6971) & 0xffffffff
        h = ((h >> 16) ^ h) * 0x45d9f3b & 0xffffffff
        return ((h >> 16) ^ h) / 0xffffffff
    ix, iy = int(x), int(y)
    fx, fy = x-ix, y-iy
    ux, uy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
    return (_hash(ix,  iy  )*(1-ux)*(1-uy) + _hash(ix+1,iy  )*ux*(1-uy) +
            _hash(ix,  iy+1)*(1-ux)*uy     + _hash(ix+1,iy+1)*ux*uy)

def _fbm(x: float, y: float, seed: int = 0, octaves: int = 4) -> float:
    """@brief Fractional Brownian motion over _smooth_noise."""
    v, amp, freq, total = 0.0, 0.5, 1.0, 0.0
    for _ in range(octaves):
        v += _smooth_noise(x*freq, y*freq, seed)*amp; total += amp
        amp *= 0.5; freq *= 2.0
    return v / total

def generate_terrain(matrix: Matrix, scale: float = 0.15, seed: int = 0) -> None:
    """@brief Fill matrix with bg-layer terrain tiles.
    Tiles use layer='bg' so they set the cell background color.
    @param scale  Noise zoom — smaller = broader landmasses.
    @param seed   Map seed.
    """
    TILES = [
    #   (nois,  ch,   fg,       bg,       collision, description)
        (0.08, '〜', '#3a6ea5', '#1a3a6a', True, 'Deep water'),
        (0.18, '〜', '#4a8ab5', '#2a4a8a', False, 'Shallow water'),
        (0.55, '土', '#c2a35a', '#8a6a2a', False, 'Sandy shore'),
        (0.78, '艸', '#4a7c3f', '#2a4a1f', False, 'Grassland'),
        (0.85, '木', '#6aC4f', '#3a4a2f', True,  'Dense forest'),
        (1.01, '山', '#7a6652', '#4a3a2a', True,  'Rocky mountain'),
    ]

    for y in range(matrix.rows):
        for x in range(matrix.cols):
            n  = _fbm(x*scale, y*scale, seed=seed)
            n2 = _fbm(x*scale*2.1, y*scale*2.1, seed=seed+99)
            # Blend second octave into rock band
            n_eff = n if n < 0.78 else n * (1 + (n2 - 0.5) * 0.3)

            for max_n, ch, fg, bg, col, desc in TILES:
                if n_eff < max_n:
                    matrix.add(GameObject(
                        x=x, y=y, character=ch,
                        color=fg, bg_color=bg,
                        collision=col, layer='bg',
                        description=desc,
                    ))
                    break


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import curses as _c

    app    = GameTUI(fps=30)

    matrix = Matrix(cols=66, rows=41)
    generate_terrain(matrix, scale=0.07, seed=42)

    class Player(GameObject):
        """@brief Player character 人."""
        def __init__(self, x, y):
            super().__init__(x, y, character='人', color='#ffffff',
                             collision=False, layer='fg',
                             description='The player character.')
        def on_key(self, key: int) -> bool:
            if   key == _c.KEY_UP:    return self.move( 0,-1)
            elif key == _c.KEY_DOWN:  return self.move( 0, 1)
            elif key == _c.KEY_LEFT:  return self.move(-1, 0)
            elif key == _c.KEY_RIGHT: return self.move( 1, 0)
            return False

    matrix.add(Player(x=5, y=10))
    app.active_matrix = matrix

    @app.panel(x=0, y=0, w=0.75, h=1.0, title='[ WORLD ]',
               border_color='#336633', title_color='#00ff88',
               matrix=matrix)
    def world(scr, inner, ctx, dt): pass

    @app.panel(x=0.75, y=0, w=0.25, h=1.0, title='[ INFO ]',
               border_color='#444466', title_color='#8888ff')
    def info_panel(scr, inner, ctx, dt):
        draw_info_panel(scr, inner, app.info)

    @app.on_key('q')
    def quit(state, dt): app.quit()

    app.run()