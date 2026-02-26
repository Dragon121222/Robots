from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameInfoState import InfoState
from playground.tuiEngine.gameObjects.gameColor import _get_pair

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