from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameObject import GameObject

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