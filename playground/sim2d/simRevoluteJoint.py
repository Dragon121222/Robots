import pygame
import numpy as np
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# ── Revolute Joint ───────────────────────────────────────────────────────────
class RevoluteJoint:
    """
    Pin joint between body_a (anchor_a in local-a) and body_b (anchor_b in local-b).
    Optional motor with target torque.
    """
    def __init__(self,
                 body_a: RigidBody,
                 body_b: RigidBody,
                 anchor_a: np.ndarray,   # local space of a
                 anchor_b: np.ndarray,   # local space of b
                 motor_torque: float = 0.0,
                 angle_limits: Optional[tuple] = None):
        self.body_a = body_a
        self.body_b = body_b
        self.anchor_a = np.array(anchor_a, dtype=float)
        self.anchor_b = np.array(anchor_b, dtype=float)
        self.motor_torque = motor_torque     # positive = CCW on b
        self.angle_limits = angle_limits     # (min_rel, max_rel) radians
        self._lambda = np.zeros(2)           # accumulated impulse

    def world_anchor_a(self) -> np.ndarray:
        return self.body_a.pos + rot2(self.body_a.angle) @ self.anchor_a

    def world_anchor_b(self) -> np.ndarray:
        return self.body_b.pos + rot2(self.body_b.angle) @ self.anchor_b

    def relative_angle(self) -> float:
        return self.body_b.angle - self.body_a.angle

    def apply_motor(self):
        if self.motor_torque == 0:
            return
        t = self.motor_torque
        # clamp by limits
        if self.angle_limits:
            rel = self.relative_angle()
            lo, hi = self.angle_limits
            if rel <= lo and t < 0:
                t = 0
            if rel >= hi and t > 0:
                t = 0
        self.body_a.apply_torque(-t)
        self.body_b.apply_torque(t)

    def solve_position(self, dt: float):
        """Velocity-level constraint with Baumgarte stabilization."""
        a, b = self.body_a, self.body_b
        Ra = rot2(a.angle) @ self.anchor_a
        Rb = rot2(b.angle) @ self.anchor_b
        wa = a.pos + Ra
        wb = b.pos + Rb
        C = wb - wa           # positional error (meters)

        # Baumgarte: bias velocity to correct position error
        # beta is a fraction per second — keep it small (0.1–0.3)
        beta = 0.2
        bias = (beta / dt) * C   # now beta/dt ~ 12/s, not 3840/s

        # Clamp bias to prevent impulse explosion on large errors
        bias_mag = np.linalg.norm(bias)
        if bias_mag > 20.0:
            bias = bias * (20.0 / bias_mag)

        # Relative velocity at constraint point
        va = a.vel + cross2_sv(a.omega, Ra)
        vb = b.vel + cross2_sv(b.omega, Rb)
        dv = vb - va

        # Effective mass matrix
        def K_contrib(body, r):
            if body.inv_mass == 0:
                return np.zeros((2, 2))
            rx, ry = float(r[0]), float(r[1])
            return (body.inv_mass * np.eye(2) +
                    body.inv_inertia * np.array([[ry*ry, -rx*ry],
                                                 [-rx*ry, rx*rx]]))

        K = K_contrib(a, Ra) + K_contrib(b, Rb)
        try:
            lam = np.linalg.solve(K, -(dv + bias))
        except np.linalg.LinAlgError:
            return

        # Clamp impulse magnitude
        max_imp = 1000.0
        lam_mag = np.linalg.norm(lam)
        if lam_mag > max_imp:
            lam = lam * (max_imp / lam_mag)

        def apply_impulse(body, r, imp):
            body.vel   += imp * body.inv_mass
            body.omega += cross2(r, imp) * body.inv_inertia

        apply_impulse(a, Ra, -lam)
        apply_impulse(b, Rb,  lam)