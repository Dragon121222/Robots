import pygame
import numpy as np
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# ── Renderer ──────────────────────────────────────────────────────────────────
class Camera:
    """World→screen with Y-flip"""
    def __init__(self, screen_w, screen_h, ppm=100.0, offset=(0, 0)):
        self.W = int(screen_w)
        self.H = int(screen_h)
        self.ppm = float(ppm)
        self.ox = float(offset[0])
        self.oy = float(offset[1])

    def w2s(self, p) -> tuple:
        """world → screen: guaranteed plain Python (int, int)"""
        try:
            px = float(p[0])
            py = float(p[1])
        except Exception:
            return (self.W // 2, self.H // 2)
        sx = (px - self.ox) * self.ppm + self.W / 2.0
        sy = self.H / 2.0 - (py - self.oy) * self.ppm
        if not (math.isfinite(sx) and math.isfinite(sy)):
            return (self.W // 2, self.H // 2)
        return (int(round(sx)), int(round(sy)))

    def set_offset(self, ox: float, oy: float):
        self.ox = float(ox)
        self.oy = float(oy)

    def scale(self, v: float) -> int:
        return int(round(float(v) * self.ppm))