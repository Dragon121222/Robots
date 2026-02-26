from __future__ import annotations

import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameMatrix import Matrix
from playground.tuiEngine.gameObjects.gameRenderer import Renderer

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