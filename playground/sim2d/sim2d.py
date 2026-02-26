

import pygame
import numpy as np
import math
import sys
from dataclasses import dataclass, field
from typing import List, Optional

# ── Main ──────────────────────────────────────────────────────────────────────

"""
2D Rigid Body Physics Simulator
================================
Bodies: convex polygons with mass/inertia
Joints: revolute (pin) joints with optional motor torque
Collisions: ground plane, impulse-based resolution
Integration: symplectic Euler

Controls:
  Q/W  - hip joint torque (CCW/CW)
  A/S  - knee joint torque (CCW/CW)
  Z/X  - ankle joint torque (CCW/CW)
  R    - reset
  SPACE- pause/unpause
"""

def main():
    pygame.init()
    W, H = 2736, 1824
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("2D Rigid Body Robotics Simulator")
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont("monospace", 14)

    def make_world():
        world = World(gravity=(0, -9.81))
        world.ground_y = 0.0
        parts = build_bipedal_robot(world)
        return world, parts

    world, (torso, thigh, shin, foot, hip, knee, ankle) = make_world()
    cam = Camera(W, H, ppm=120, offset=(0, 1.5))

    MOTOR_TORQUE = 30.0   # Nm
    paused = False
    dt = 1/60.0

    hip_cmd   = 0.0
    knee_cmd  = 0.0
    ankle_cmd = 0.0

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    paused = not paused
                if ev.key == pygame.K_r:
                    world, (torso, thigh, shin, foot, hip, knee, ankle) = make_world()

        keys = pygame.key.get_pressed()
        hip_cmd   = (keys[pygame.K_w] - keys[pygame.K_q]) * MOTOR_TORQUE
        knee_cmd  = (keys[pygame.K_s] - keys[pygame.K_a]) * MOTOR_TORQUE
        ankle_cmd = (keys[pygame.K_x] - keys[pygame.K_z]) * MOTOR_TORQUE

        hip.motor_torque   = hip_cmd
        knee.motor_torque  = knee_cmd
        ankle.motor_torque = ankle_cmd

        if not paused:
            world.step(dt, substeps=8)
            # follow torso horizontally
            cam.set_offset(float(torso.pos[0]), cam.oy)

        # ── Draw ──────────────────────────────────────────────────────────
        screen.fill((18, 22, 30))
        draw_ground(screen, cam, world.ground_y)

        for b in world.bodies:
            draw_body(screen, cam, b)
        for j in world.joints:
            draw_joint(screen, cam, j)

        # HUD
        def hud(row, text, color=(180,220,255)):
            surf = font.render(text, True, color)
            screen.blit(surf, (12, 12 + row*18))

        hud(0, "2D RIGID BODY SIMULATOR", (255,230,80))
        hud(1, f"t = {world.time:.2f}s   {'PAUSED' if paused else 'RUNNING'}")
        hud(2, "─────────────────────────────")
        hud(3, "Q/W  → hip torque CCW/CW")
        hud(4, "A/S  → knee torque CCW/CW")
        hud(5, "Z/X  → ankle torque CCW/CW")
        hud(6, "R    → reset    SPACE → pause")
        hud(7, "─────────────────────────────")
        hud(8, f"hip   torque: {hip_cmd:+6.1f} Nm   angle: {hip.relative_angle():+.2f} rad")
        hud(9, f"knee  torque: {knee_cmd:+6.1f} Nm   angle: {knee.relative_angle():+.2f} rad")
        hud(10,f"ankle torque: {ankle_cmd:+6.1f} Nm   angle: {ankle.relative_angle():+.2f} rad")
        hud(11,f"torso vel: ({torso.vel[0]:+.2f}, {torso.vel[1]:+.2f}) m/s")

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()