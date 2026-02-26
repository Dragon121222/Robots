import pygame
import numpy as np
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# ── Rigid Body ───────────────────────────────────────────────────────────────
class RigidBody:
    def __init__(self,
                 vertices: np.ndarray,   # local-space convex polygon
                 mass: float,
                 pos: np.ndarray,
                 angle: float = 0.0,
                 color=(160, 200, 240)):
        self.vertices = np.array(vertices, dtype=float)  # (N,2) local
        self.mass = mass
        self.inv_mass = 1.0 / mass if mass > 0 else 0.0

        # Moment of inertia: polygon formula
        self.inertia = self._compute_inertia()
        self.inv_inertia = 1.0 / self.inertia if self.inertia > 0 else 0.0

        self.pos = np.array(pos, dtype=float)
        self.angle = float(angle)
        self.vel = np.zeros(2)
        self.omega = 0.0            # angular velocity rad/s

        self.force = np.zeros(2)
        self.torque = 0.0

        self.color = color
        self.restitution = 0.3
        self.friction = 0.6

    def _compute_inertia(self) -> float:
        verts = self.vertices
        n = len(verts)
        num = denom = 0.0
        for i in range(n):
            j = (i+1) % n
            p0, p1 = verts[i], verts[j]
            c = abs(cross2(p0, p1))
            num   += c * (np.dot(p0, p0) + np.dot(p0, p1) + np.dot(p1, p1))
            denom += c
        return (self.mass / 6.0) * (num / denom) if denom != 0 else 1.0

    def world_vertices(self) -> np.ndarray:
        R = rot2(self.angle)
        return (self.vertices @ R.T) + self.pos

    def apply_force(self, f: np.ndarray, point_world: Optional[np.ndarray] = None):
        self.force += f
        if point_world is not None:
            r = point_world - self.pos
            self.torque += cross2(r, f)

    def apply_torque(self, t: float):
        self.torque += t

    def integrate(self, dt: float, gravity: np.ndarray):
        if self.inv_mass == 0:
            return
        self.vel   += dt * (gravity + self.force * self.inv_mass)
        self.omega += dt * self.torque * self.inv_inertia

        # Linear and angular damping
        self.vel   *= 0.999
        self.omega *= 0.995

        # Safety clamp — prevents NaN cascade
        spd = np.linalg.norm(self.vel)
        if spd > 200.0:
            self.vel *= 200.0 / spd
        if abs(self.omega) > 50.0:
            self.omega = math.copysign(50.0, self.omega)

        self.pos   += dt * self.vel
        self.angle += dt * self.omega
        self.force[:] = 0
        self.torque = 0.0

    def velocity_at(self, point_world: np.ndarray) -> np.ndarray:
        r = point_world - self.pos
        return self.vel + cross2_sv(self.omega, r)