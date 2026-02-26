#!/usr/bin/env python3
# calibrate_laser.py
# ================================================================
# Laser-Camera Triangulation Calibration
#
# Multi-frame consensus detection + interactive review.
# After each point, shows all points and warns about outliers.
#
# Commands during calibration:
#   <distance>   e.g. 0.3, 12in, 30cm — capture and add point
#   redo         recapture the last distance
#   drop         remove last point
#   list         show all points + monotonicity check
#   debug        save debug frame with all candidates marked
#   done         calibrate and save
#   quit         abort
# ================================================================
import cv2
import numpy as np
import sys
import os
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from laserTriangulation import LaserTriangulation


def open_camera(device):
    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera {device}")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    for _ in range(10):
        cap.read()
    return cap


def parse_distance(text):
    """Parse distance string. Returns meters or None."""
    text = text.strip()
    try:
        if text.lower().endswith('in'):
            inches = float(text[:-2].strip())
            m = inches * 0.0254
            print(f"  → {inches:.1f} in = {m:.4f} m")
            return m
        elif text.lower().endswith('cm'):
            cm = float(text[:-2].strip())
            m = cm / 100.0
            print(f"  → {cm:.1f} cm = {m:.4f} m")
            return m
        else:
            return float(text)
    except ValueError:
        return None


def capture_point(cap, tri, distance_m, point_num):
    """Capture frames and try to detect laser. Returns (u,v) or None."""
    print(f"  Capturing {tri._num_detect_frames} frames...")
    dot = tri.add_calibration_point_from_cap(cap, distance_m)

    if dot is None:
        cap.grab()
        ok, frame = cap.read()
        if ok:
            tri.save_debug_frame(frame, f"/tmp/laser_cal_debug_{point_num}.jpg")
        print("  Use 'debug' to inspect, or 'redo' to try again.")
        return None

    u, v = dot

    # Save annotated snapshot
    cap.grab()
    ok, frame = cap.read()
    if ok:
        annotated = frame.copy()
        cv2.drawMarker(annotated, (u, v), (0, 255, 0),
                        cv2.MARKER_CROSS, 20, 2)
        cv2.putText(annotated, f"{distance_m:.3f}m @ ({u},{v})",
                    (u + 15, v - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)
        cv2.imwrite(f"/tmp/laser_cal_point_{point_num}.jpg", annotated)

    # Show all points after each addition
    print()
    tri.print_points()
    print()

    return dot


def run(args):
    print("=" * 60)
    print("Laser Triangulation Calibration")
    print("=" * 60)
    print(f"  Device:    {args.device}")
    print(f"  Output:    {args.output}")
    print(f"  Frames:    {args.frames} per point")
    print("=" * 60)

    cap = open_camera(args.device)
    tri = LaserTriangulation()
    tri._num_detect_frames = args.frames

    print("\nCommands:")
    print("  <distance>  Capture point (e.g. 0.3, 12in, 30cm)")
    print("  redo        Recapture at the last distance")
    print("  drop        Remove last point")
    print("  list        Show all points")
    print("  debug       Save debug frame")
    print("  done        Calibrate and save")
    print("  quit        Abort")
    print()

    point_num = 0
    last_distance = None

    while True:
        n_pts = len(tri._cal_points)
        prompt = f"[{n_pts} pts] Enter distance (or command): "
        cmd = input(prompt).strip()

        if not cmd:
            continue

        lc = cmd.lower()

        if lc == 'done':
            break

        if lc in ('quit', 'q'):
            print("Aborted.")
            cap.release()
            sys.exit(0)

        if lc == 'debug':
            cap.grab()
            ok, frame = cap.read()
            if ok:
                tri.save_debug_frame(frame, f"/tmp/laser_debug_{point_num}.jpg")
            continue

        if lc == 'list':
            tri.print_points()
            continue

        if lc == 'drop':
            tri.drop_last_point()
            tri.print_points()
            continue

        if lc == 'redo':
            if last_distance is None:
                print("  Nothing to redo.")
                continue
            # Drop last point and recapture
            if tri._cal_points:
                tri.drop_last_point()
            distance_m = last_distance
            print(f"  Redoing at {distance_m:.4f}m")
        else:
            distance_m = parse_distance(cmd)
            if distance_m is None:
                print(f"  Invalid: '{cmd}'  (try: 0.3, 12in, 30cm, "
                      f"or commands: done/drop/redo/list/debug/quit)")
                continue
            if distance_m <= 0:
                print("  Distance must be positive.")
                continue

        last_distance = distance_m
        dot = capture_point(cap, tri, distance_m, point_num)
        if dot is not None:
            point_num += 1

    cap.release()

    n_pts = len(tri._cal_points)
    if n_pts < 2:
        print(f"\nNeed at least 2 points, got {n_pts}.")
        sys.exit(1)

    # Final review
    print(f"\nFinal points ({n_pts}):")
    tri.print_points()

    print(f"\nCalibrating...")
    if tri.calibrate():
        tri.save_calibration(args.output)
        print(f"\n✓ Saved: {args.output}")
    else:
        print("\nCalibration failed.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Laser-Camera Triangulation Calibration")
    parser.add_argument("--device", default="/dev/video1")
    parser.add_argument("--output", default="laser_calibration.json")
    parser.add_argument("--frames", type=int, default=8,
                        help="Frames per detection (default: 8)")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()