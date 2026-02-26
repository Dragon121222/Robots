from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameObject import GameObject

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