import pygame
import numpy as np
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# ── Ground Plane Collision ────────────────────────────────────────────────────
def resolve_ground(body: RigidBody, ground_y: float):
    """Per-vertex ground collision with impulse response"""
    verts = body.world_vertices()
    for v in verts:
        pen = ground_y - v[1]
        if pen <= 0:
            continue
        n = np.array([0.0, 1.0])
        r = v - body.pos
        vp = body.velocity_at(v)
        vn = float(np.dot(vp, n))
        if vn > 0:   # separating
            # just push out
            body.pos[1] += pen * 0.8
            continue

        # effective mass
        rn = cross2(r, n)
        eff_mass = body.inv_mass + body.inv_inertia * rn * rn
        if eff_mass < 1e-10:
            continue

        # normal impulse
        j_n = -(1 + body.restitution) * vn / eff_mass
        j_n = max(j_n, 0.0)
        imp_n = j_n * n

        # friction impulse
        t_vec = vp - vn * n
        t_len = np.linalg.norm(t_vec)
        if t_len > 1e-6:
            t_hat = t_vec / t_len
            vt = float(np.dot(vp, t_hat))
            rt = cross2(r, t_hat)
            eff_mass_t = body.inv_mass + body.inv_inertia * rt * rt
            j_t = -vt / eff_mass_t
            j_t = np.clip(j_t, -body.friction * j_n, body.friction * j_n)
            imp_n += j_t * t_hat

        body.vel   += imp_n * body.inv_mass
        body.omega += cross2(r, imp_n) * body.inv_inertia
        body.pos[1] += pen * 0.5

# ── World ─────────────────────────────────────────────────────────────────────
class World:
    def __init__(self, gravity=(0, -9.81)):
        self.gravity = np.array(gravity, dtype=float)
        self.bodies: List[RigidBody] = []
        self.joints: List[RevoluteJoint] = []
        self.ground_y = 0.0
        self.time = 0.0

    def add_body(self, body: RigidBody) -> RigidBody:
        self.bodies.append(body)
        return body

    def add_joint(self, joint: RevoluteJoint) -> RevoluteJoint:
        self.joints.append(joint)
        return joint

    def step(self, dt: float, substeps: int = 4):
        sub_dt = dt / substeps
        for _ in range(substeps):
            # motors
            for j in self.joints:
                j.apply_motor()
            # integrate
            for b in self.bodies:
                b.integrate(sub_dt, self.gravity)
            # joint constraints
            for j in self.joints:
                j.solve_position(sub_dt)
            # ground collisions
            for b in self.bodies:
                if b.inv_mass > 0:
                    resolve_ground(b, self.ground_y)
        self.time += dt