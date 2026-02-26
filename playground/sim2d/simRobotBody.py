import pygame
import numpy as np
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

def _ipt(p) -> tuple:
    """Guarantee plain Python (int, int) clamped to screen-safe range."""
    def toint(v):
        try:
            f = float(v.item())
        except AttributeError:
            f = float(v)
        f = max(-32768.0, min(32767.0, f))
        return int(round(f))
    return (toint(p[0]), toint(p[1]))

def draw_body(surf, cam: Camera, body: RigidBody):
    verts = body.world_vertices()          # (N,2) numpy array
    pts = [_ipt(cam.w2s([float(v[0]), float(v[1])])) for v in verts]
    if len(pts) >= 3:
        pygame.draw.polygon(surf, tuple(body.color), pts)
        pygame.draw.polygon(surf, (255, 255, 255), pts, 1)
    pos = body.pos
    cx, cy = _ipt(cam.w2s([float(pos[0]), float(pos[1])]))
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 3)

def draw_joint(surf, cam: Camera, joint: RevoluteJoint):
    wa = joint.world_anchor_a()
    cx, cy = _ipt(cam.w2s([float(wa[0]), float(wa[1])]))
    pygame.draw.circle(surf, (255, 220, 60), (cx, cy), 6)
    pygame.draw.circle(surf, (0, 0, 0), (cx, cy), 6, 2)

def draw_ground(surf, cam: Camera, ground_y: float, color=(80, 160, 80)):
    _, gy = _ipt(cam.w2s([0.0, ground_y]))
    pygame.draw.line(surf, color, (0, gy), (surf.get_width(), gy), 2)
    for gx in range(0, surf.get_width(), 20):
        pygame.draw.line(surf, (50, 120, 50), (gx, gy), (gx + 12, gy + 12), 1)

# ── Robot Builder ─────────────────────────────────────────────────────────────
def make_box(w, h, mass, pos, angle=0.0, color=(160,200,240)) -> RigidBody:
    hw, hh = w/2, h/2
    verts = [[-hw,-hh],[hw,-hh],[hw,hh],[-hw,hh]]
    return RigidBody(verts, mass, pos, angle, color)

def build_bipedal_robot(world: World):
    """
    Torso → hip joint → thigh → knee joint → shin → ankle joint → foot
    Symmetric, starting above ground.
    """
    ground = world.ground_y
    start_y = 2.5   # meters above ground

    # Segment dimensions (meters)
    torso_w, torso_h   = 0.4, 0.5
    thigh_w, thigh_h   = 0.12, 0.4
    shin_w,  shin_h    = 0.10, 0.38
    foot_w,  foot_h    = 0.25, 0.07

    # Colors
    c_torso = (100, 160, 220)
    c_thigh = (80,  200, 160)
    c_shin  = (60,  170, 230)
    c_foot  = (220, 180, 80)

    torso = make_box(torso_w, torso_h, 10.0,
                     [0, start_y + thigh_h + shin_h + foot_h + torso_h/2],
                     color=c_torso)

    thigh = make_box(thigh_w, thigh_h, 2.5,
                     [0, start_y + shin_h + foot_h + thigh_h/2],
                     color=c_thigh)

    shin  = make_box(shin_w,  shin_h,  1.5,
                     [0, start_y + foot_h + shin_h/2],
                     color=c_shin)

    foot  = make_box(foot_w,  foot_h,  0.8,
                     [0, start_y + foot_h/2],
                     color=c_foot)

    for b in [torso, thigh, shin, foot]:
        world.add_body(b)

    # Hip joint: bottom of torso ↔ top of thigh
    hip = RevoluteJoint(
        torso, thigh,
        anchor_a=[0, -torso_h/2],
        anchor_b=[0,  thigh_h/2],
        angle_limits=(-1.2, 1.2)
    )

    # Knee joint: bottom of thigh ↔ top of shin
    knee = RevoluteJoint(
        thigh, shin,
        anchor_a=[0, -thigh_h/2],
        anchor_b=[0,  shin_h/2],
        angle_limits=(-0.1, 2.0)
    )

    # Ankle joint: bottom of shin ↔ center-back of foot
    ankle = RevoluteJoint(
        shin, foot,
        anchor_a=[0,        -shin_h/2],
        anchor_b=[-foot_w/4, foot_h/2],
        angle_limits=(-0.8, 0.8)
    )

    for j in [hip, knee, ankle]:
        world.add_joint(j)

    return torso, thigh, shin, foot, hip, knee, ankle