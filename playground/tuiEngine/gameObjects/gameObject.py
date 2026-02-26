from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

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