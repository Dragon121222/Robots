from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameInfoState import InfoState
from playground.tuiEngine.gameObjects.gamePanel import PanelDef
from playground.tuiEngine.gameObjects.gameColor import _get_pair

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