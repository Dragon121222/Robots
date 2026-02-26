from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameMatrix import Matrix
from playground.tuiEngine.gameObjects.gameColor import _get_pair

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