from __future__ import annotations

import random
import curses
import time
from dataclasses import dataclass, field
from typing      import Callable, Optional

from playground.tuiEngine.gameObjects.gameMatrix import Matrix
from playground.tuiEngine.gameObjects.gameObject import GameObject

# ── Terrain generation ────────────────────────────────────────────────────────

def _smooth_noise(x: float, y: float, seed: int = 0) -> float:
    """@brief Smooth lattice noise in [0,1]."""
    def _hash(ix, iy):
        h = (ix*1619 + iy*31337 + seed*6971) & 0xffffffff
        h = ((h >> 16) ^ h) * 0x45d9f3b & 0xffffffff
        return ((h >> 16) ^ h) / 0xffffffff
    ix, iy = int(x), int(y)
    fx, fy = x-ix, y-iy
    ux, uy = fx*fx*(3-2*fx), fy*fy*(3-2*fy)
    return (_hash(ix,  iy  )*(1-ux)*(1-uy) + _hash(ix+1,iy  )*ux*(1-uy) +
            _hash(ix,  iy+1)*(1-ux)*uy     + _hash(ix+1,iy+1)*ux*uy)

def _fbm(x: float, y: float, seed: int = 0, octaves: int = 4) -> float:
    """@brief Fractional Brownian motion over _smooth_noise."""
    v, amp, freq, total = 0.0, 0.5, 1.0, 0.0
    for _ in range(octaves):
        v += _smooth_noise(x*freq, y*freq, seed)*amp; total += amp
        amp *= 0.5; freq *= 2.0
    return v / total

def generate_terrain(matrix: Matrix, scale: float = 0.15, seed: int = 0) -> None:
    """@brief Fill matrix with bg-layer terrain tiles.
    Tiles use layer='bg' so they set the cell background color.
    @param scale  Noise zoom — smaller = broader landmasses.
    @param seed   Map seed.
    """
    TILES = [
        # (max_noise, ch,  fg,        bg,        collision, description)

        # ── Water ────────────────────────────────────────────────────────
        (0.18, '淵', '#0a4a7a', '#050f1a', True,  '淵 (fuchi) — abyss, deep pool'),
        (0.26, '海', '#1a6090', '#0a2040', True, '海 (umi) — sea, ocean'),
        (0.33, '波', '#2a7ab5', '#0f3060', True, '波 (nami) — wave'),
        (0.38, '川', '#3a8acc', '#1a4070', True, '川 (kawa) — river'),
        (0.42, '浅', '#4a9fd4', '#1a5080', False, '浅 (asa) — shallow'),
        (0.46, '潮', '#5aaad8', '#2a5a80', False, '潮 (shio) — tide'),

        # ── Shore & wetland ──────────────────────────────────────────────
        (0.49, '砂', '#d4b483', '#8a6a2a', False, '砂 (suna) — sand'),
        (0.52, '浜', '#c8a86a', '#7a5a20', False, '浜 (hama) — beach'),
        (0.54, '湿', '#7a9a5a', '#3a5a2a', False, '湿 (shitsu) — damp, wetland'),
        (0.56, '沼', '#5a8a4a', '#2a4a1a', False, '沼 (numa) — swamp, marsh'),

        # ── Grassland ────────────────────────────────────────────────────
        (0.59, '野', '#7ab550', '#3a5a20', False, '野 (no) — field, plain'),
        (0.62, '原', '#6aa040', '#2a4a15', False, '原 (hara) — meadow, plain'),
        (0.65, '草', '#5a9030', '#1a3a0a', False, '草 (kusa) — grass'),
        (0.67, '丘', '#8aaa50', '#3a5a1a', False, '丘 (oka) — hill, knoll'),

        # ── Shrub & bush ─────────────────────────────────────────────────
        (0.69, '茂', '#4a8028', '#1a3008', False, '茂 (mo) — overgrown, thick'),
        (0.71, '藪', '#3a7020', '#152808', True,  '藪 (yabu) — thicket, bush'),

        # ── Forest ───────────────────────────────────────────────────────
        (0.73, '林', '#3a7a2a', '#152010', True,  '林 (hayashi) — grove, small forest'),
        (0.75, '森', '#2a6a1a', '#0f1a08', True,  '森 (mori) — forest'),
        (0.77, '木', '#1a5a10', '#0a1205', True,  '木 (ki) — tree'),
        (0.79, '樹', '#155010', '#081005', True,  '樹 (ju) — large tree'),

        # ── Highland transition ──────────────────────────────────────────
        (0.81, '坂', '#9a8a6a', '#4a3a2a', True, '坂 (saka) — slope'),
        (0.83, '崖', '#8a7a5a', '#3a2a1a', True,  '崖 (gake) — cliff'),
        (0.85, '岩', '#7a6a50', '#3a2a18', True,  '岩 (iwa) — boulder, rock'),

        # ── Mountain ─────────────────────────────────────────────────────
        (0.87, '峠', '#9a8878', '#504030', True,  '峠 (toge) — mountain pass'),
        (0.90, '山', '#b0a090', '#604840', True,  '山 (yama) — mountain'),
        (0.93, '嶺', '#c8b8a8', '#706050', True,  '嶺 (mine) — summit, peak'),
        (0.96, '雪', '#e8e8f0', '#9090a8', True,  '雪 (yuki) — snow'),
        (1.01, '氷', '#d0e8f8', '#a0c0e0', True,  '氷 (koori) — ice'),
    ]

    for y in range(matrix.rows):
        for x in range(matrix.cols):
            n  = _fbm(x*scale, y*scale, seed=seed)
            n2 = _fbm(x*scale*2.1, y*scale*2.1, seed=seed+99)
            # Blend second octave into rock band
            n_eff = n if n < 0.78 else n * (1 + (n2 - 0.5) * 0.3)

            for max_n, ch, fg, bg, col, desc in TILES:
                if n_eff < max_n:
                    matrix.add(GameObject(
                        x=x, y=y, character=ch,
                        color=fg, bg_color=bg,
                        collision=col, layer='bg',
                        description=desc,
                    ))
                    break

    generate_characters('犬','Dog',matrix)
    generate_characters('猫','Cat',matrix)
    generate_characters('匪','Bandit',matrix)



def generate_characters(
    character: str,
    description: str,
    matrix: Matrix,
    howMany: int = 5, 
    spread: int = 3,
    min_x: int = 1,
    max_x: int = 66,
    min_y: int = 1,
    max_y: int = 41,
    collision: bool = True,
    layer: str = 'fg',
    color: str = 'white',
    bg_color: str = 'black',
    scale: float = 5, 
    seed: int = 69
) -> None:

    x = random.randint(min_x, max_x)
    y = random.randint(min_y, max_y)

    for i in range(howMany):

        dx = random.randint(-spread, spread)
        dy = random.randint(-spread, spread)

        if bg_color == 'black':
            bg_color = '#000000'

        if color == 'white':
            color = '#FFFFFF'

        matrix.add(GameObject(
            x=x+dx, y=y+dy, character=character,
            color=color, bg_color=bg_color,
            collision=collision, layer=layer,
            description=description,
        ))


