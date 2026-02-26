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