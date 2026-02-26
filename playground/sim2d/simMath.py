import pygame
import numpy as np
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# ── Math helpers ────────────────────────────────────────────────────────────
def rot2(angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s], [s, c]])

def cross2(a: np.ndarray, b: np.ndarray) -> float:
    """2D cross product → scalar"""
    return float(a[0]*b[1] - a[1]*b[0])

def cross2_sv(s: float, v: np.ndarray) -> np.ndarray:
    """scalar × vector cross"""
    return np.array([-s*v[1], s*v[0]])