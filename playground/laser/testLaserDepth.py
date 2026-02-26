#!/usr/bin/env python3
# test_laser_depth.py
# ================================================================
# Live Laser Triangulation Tester
#
# Loads calibration, continuously measures depth at the laser dot.
# Two modes:
#   --fast    Single-frame detection (~10 Hz, less robust)
#   default   Multi-frame consensus (~2 Hz, robust)
#
# Usage:
#   python test_laser_depth.py
#   python test_laser_depth.py --cal laser_calibration.json
#   python test_laser_depth.py --fast
#   python test_laser_depth.py --save
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


def run(args):
    if not os.path.exists(args.cal):
        print(f"ERROR: Calibration not found: {args.cal}")
        print("Run calibrate_laser.py first.")
        sys.exit(1)

    tri = LaserTriangulation(args.cal)
    cap = open_camera(args.device)

    mode = "single-frame" if args.fast else f"multi-frame ({args.frames}f)"

    print("=" * 60)
    print("Live Laser Depth Tester")
    print("=" * 60)
    print(f"  Camera:      {args.device}")
    print(f"  Calibration: {args.cal}")
    print(f"  Detection:   {mode}")
    print(f"  Save frames: {'ON' if args.save else 'OFF'}")
    print("=" * 60)
    print()
    print(f"{'TIME':>8s}  {'DEPTH':>8s}  {'RAW':>8s}  {'PIXEL':>12s}  {'STATUS'}")
    print(f"{'─' * 8}  {'─' * 8}  {'─' * 8}  {'─' * 12}  {'─' * 20}")

    if args.save:
        save_dir = "/tmp/laser_test"
        os.makedirs(save_dir, exist_ok=True)

    tri._num_detect_frames = args.frames
    frame_count = 0
    detect_count = 0
    t_start = time.monotonic()

    try:
        while True:
            t_loop = time.monotonic()
            frame_count += 1

            if args.fast:
                # Single-frame: grab fresh frame
                for _ in range(2):
                    cap.grab()
                ok, frame = cap.read()
                if not ok:
                    print("  Camera read failed")
                    time.sleep(0.1)
                    continue
                result = tri.estimate_depth(frame)
            else:
                # Multi-frame consensus
                result = tri.estimate_depth_multiframe(cap)

            elapsed = time.monotonic() - t_start
            dt = time.monotonic() - t_loop

            if result.get('valid'):
                detect_count += 1
                z = result['depth_m']
                raw_z = result.get('raw_depth_m', z)
                u, v = result['pixel']

                print(f"\r{elapsed:7.1f}s  {z:7.3f}m  {raw_z:7.3f}m  "
                      f"({u:4d}, {v:4d})  ● {dt:.2f}s     ",
                      end="", flush=True)

                if args.save and frame_count % 5 == 0:
                    # Grab a frame to annotate
                    cap.grab()
                    ok, frame = cap.read()
                    if ok:
                        annotated = tri.annotate_frame(frame, result)
                        path = os.path.join(save_dir, f"test_{frame_count:06d}.jpg")
                        cv2.imwrite(path, annotated)
            else:
                reason = result.get('reason', 'no dot')
                print(f"\r{elapsed:7.1f}s  {'---':>8s}  {'---':>8s}  "
                      f"{'---':>12s}  ○ {reason:<20s}",
                      end="", flush=True)

                if args.save and frame_count % 10 == 0:
                    cap.grab()
                    ok, frame = cap.read()
                    if ok:
                        tri.save_debug_frame(frame,
                            os.path.join(save_dir, f"miss_{frame_count:06d}.jpg"))

    except KeyboardInterrupt:
        total_time = time.monotonic() - t_start
        rate = detect_count / total_time if total_time > 0 else 0
        pct = detect_count / frame_count * 100 if frame_count else 0

        print("\n")
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"  Duration:    {total_time:.1f}s")
        print(f"  Attempts:    {frame_count}")
        print(f"  Detections:  {detect_count} ({pct:.1f}%)")
        print(f"  Rate:        {rate:.1f} measurements/s")
        print("=" * 60)

    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description="Live Laser Depth Tester")
    parser.add_argument("--device", default="/dev/video1")
    parser.add_argument("--cal", default="laser_calibration.json")
    parser.add_argument("--fast", action="store_true",
                        help="Single-frame detection (faster, less robust)")
    parser.add_argument("--frames", type=int, default=6,
                        help="Frames for multi-frame detection (default: 6)")
    parser.add_argument("--save", action="store_true",
                        help="Save frames to /tmp/laser_test/")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()