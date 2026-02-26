# laserTriangulation.py
# ================================================================
# Structured Light Depth via Laser-Camera Triangulation
#
# Detection: multi-frame temporal consensus — the laser dot is the
# bright blob that appears at the same pixel across N frames.
#
# Calibration: z = A/(v - v0) + B with RANSAC outlier rejection.
# ================================================================
import cv2
import numpy as np
import json
import os
import time


class LaserTriangulation:

    def __init__(self, calibration_file=None):
        self._A = None
        self._v0 = None
        self._B = None
        self._calibrated = False

        # Detection config
        self._min_area = 2
        self._max_area = 800
        self._num_detect_frames = 8
        self._stability_radius = 15.0
        self._min_appearance_ratio = 0.7  # Must appear in 70% of frames
        self._brightness_percentile = 97

        # Runtime smoothing
        self._depth_ema = None
        self._ema_alpha = 0.4

        # Calibration data
        self._cal_points = []  # list of (v_pixel, z_meters)

        if calibration_file and os.path.exists(calibration_file):
            self.load_calibration(calibration_file)

    # ─── Candidate Finding ────────────────────────────────

    def _find_bright_candidates(self, frame):
        """
        Find all bright, small blobs where red channel is dominant
        or at least maximal. Returns list of (cx, cy, score).
        """
        b_ch, g_ch, r_ch = [ch.astype(np.float32) for ch in cv2.split(frame)]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)

        other_max = np.maximum(g_ch, b_ch)
        red_excess = np.clip(r_ch - other_max, 0, 255)

        # Score = red excess + brightness bonus where R is max channel
        score_map = red_excess + gray * 0.3
        bright_mask = (gray > 180) & (r_ch >= other_max - 10)
        score_map = np.where(bright_mask, score_map + gray * 0.5, score_map)

        # Threshold top percentile
        nonzero = score_map[score_map > 0]
        if len(nonzero) < 100:
            return []
        thresh = max(np.percentile(nonzero, self._brightness_percentile), 15.0)

        mask = (score_map >= thresh).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        candidates = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self._min_area or area > self._max_area:
                continue
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            sc = float(score_map[cy, cx])
            candidates.append((cx, cy, sc))

        return candidates

    # ─── Multi-Frame Detection ────────────────────────────

    def detect_laser_multiframe(self, cap, num_frames=None):
        """
        Capture N frames, find bright candidates in each, return the
        spatially stable one (the laser dot).
        """
        n = num_frames or self._num_detect_frames
        min_appearances = max(2, int(n * self._min_appearance_ratio))

        all_candidates = []
        for i in range(n):
            cap.grab()
            ok, frame = cap.read()
            if not ok:
                continue
            candidates = self._find_bright_candidates(frame)
            all_candidates.append(candidates)
            time.sleep(0.05)

        if not all_candidates:
            return None

        # Flatten with frame index
        all_points = []
        for fi, cands in enumerate(all_candidates):
            for cx, cy, sc in cands:
                all_points.append((cx, cy, sc, fi))

        if not all_points:
            return None

        # Cluster by spatial proximity
        clusters = []
        for pt in all_points:
            cx, cy = pt[0], pt[1]
            assigned = False
            for cluster in clusters:
                mean_x = np.mean([p[0] for p in cluster])
                mean_y = np.mean([p[1] for p in cluster])
                dist = np.sqrt((cx - mean_x)**2 + (cy - mean_y)**2)
                if dist < self._stability_radius:
                    cluster.append(pt)
                    assigned = True
                    break
            if not assigned:
                clusters.append([pt])

        # Score clusters: frame coverage, stability, brightness
        best_cluster = None
        best_score = -1

        for cluster in clusters:
            frames_present = len(set(p[3] for p in cluster))
            if frames_present < min_appearances:
                continue

            xs = [p[0] for p in cluster]
            ys = [p[1] for p in cluster]
            variance = np.var(xs) + np.var(ys)
            mean_score = np.mean([p[2] for p in cluster])
            stability = 1.0 / (1.0 + variance)

            combined = frames_present * 100 + stability * 50 + mean_score
            if combined > best_score:
                best_score = combined
                best_cluster = cluster

        if best_cluster is None:
            return None

        cx = int(np.mean([p[0] for p in best_cluster]))
        cy = int(np.mean([p[1] for p in best_cluster]))
        n_frames = len(set(p[3] for p in best_cluster))
        variance = np.var([p[0] for p in best_cluster]) + np.var([p[1] for p in best_cluster])
        print(f"  Consensus: ({cx}, {cy}) in {n_frames}/{n} frames, variance={variance:.1f}")
        return (cx, cy)

    def detect_laser(self, frame):
        """Single-frame fallback — picks highest-scoring candidate."""
        candidates = self._find_bright_candidates(frame)
        if not candidates:
            return None
        best = max(candidates, key=lambda c: c[2])
        return (best[0], best[1])

    # ─── Calibration ──────────────────────────────────────

    def add_calibration_point_from_cap(self, cap, known_distance_m):
        """Multi-frame detection → calibration point."""
        dot = self.detect_laser_multiframe(cap)
        if dot is None:
            print(f"Calibration: not detected across {self._num_detect_frames} frames")
            return None

        u, v = dot
        self._cal_points.append((float(v), float(known_distance_m)))
        print(f"Calibration: added — pixel=({u}, {v}), z={known_distance_m:.3f}m "
              f"[{len(self._cal_points)} total]")
        return dot

    def add_calibration_point_manual(self, v_pixel, known_distance_m):
        self._cal_points.append((float(v_pixel), float(known_distance_m)))

    def drop_last_point(self):
        """Remove the most recently added calibration point."""
        if self._cal_points:
            removed = self._cal_points.pop()
            print(f"Calibration: dropped point v={removed[0]:.0f}, z={removed[1]:.3f}m "
                  f"[{len(self._cal_points)} remaining]")
            return removed
        return None

    def check_monotonicity(self):
        """
        Check if calibration points are monotonic in v vs z.
        Returns list of (index, issue_description) for bad points.
        """
        if len(self._cal_points) < 2:
            return []

        # Sort by distance
        sorted_pts = sorted(self._cal_points, key=lambda p: p[1])
        vs_sorted = [p[0] for p in sorted_pts]
        zs_sorted = [p[1] for p in sorted_pts]

        # Check if v is monotonically increasing or decreasing
        diffs = [vs_sorted[i+1] - vs_sorted[i] for i in range(len(vs_sorted)-1)]
        n_pos = sum(1 for d in diffs if d > 0)
        n_neg = sum(1 for d in diffs if d < 0)

        # Determine expected direction (majority vote)
        expect_increasing = n_pos >= n_neg

        issues = []
        for i in range(len(diffs)):
            if expect_increasing and diffs[i] < -20:
                # v should increase but dropped significantly
                issues.append((i+1, sorted_pts[i+1],
                    f"v={vs_sorted[i+1]:.0f} breaks trend "
                    f"(expected > {vs_sorted[i]:.0f} at z={zs_sorted[i+1]:.3f}m)"))
            elif not expect_increasing and diffs[i] > 20:
                issues.append((i+1, sorted_pts[i+1],
                    f"v={vs_sorted[i+1]:.0f} breaks trend "
                    f"(expected < {vs_sorted[i]:.0f} at z={zs_sorted[i+1]:.3f}m)"))

        return issues

    def print_points(self):
        """Print all calibration points in a readable table."""
        if not self._cal_points:
            print("  No calibration points.")
            return

        print(f"  {'#':>3s}  {'v (row)':>8s}  {'z (m)':>8s}")
        print(f"  {'─'*3}  {'─'*8}  {'─'*8}")
        sorted_by_z = sorted(enumerate(self._cal_points), key=lambda x: x[1][1])
        for orig_idx, (v, z) in sorted_by_z:
            print(f"  {orig_idx:>3d}  {v:>8.0f}  {z:>8.3f}")

        issues = self.check_monotonicity()
        if issues:
            print()
            print("  ⚠ MONOTONICITY WARNINGS:")
            for _, pt, desc in issues:
                print(f"    {desc}")
            print("  Use 'drop' to remove bad points, or 'redo' to recapture.")

    def calibrate(self):
        """
        Fit z = A/(v - v0) + B with RANSAC-style outlier rejection.
        """
        n = len(self._cal_points)
        if n < 2:
            print(f"Calibration: need at least 2 points, have {n}")
            return False

        vs = np.array([p[0] for p in self._cal_points])
        zs = np.array([p[1] for p in self._cal_points])

        if n == 2:
            return self._fit_2point(vs, zs)

        # With 3+ points, use RANSAC: try all 2-point pairs, pick the
        # model that has the most inliers, then refit on inliers only.
        best_inlier_mask = None
        best_inlier_count = 0
        best_params = None
        inlier_threshold = 0.05  # 5cm tolerance

        from itertools import combinations
        for i, j in combinations(range(n), 2):
            v_pair = vs[[i, j]]
            z_pair = zs[[i, j]]

            if abs(z_pair[1] - z_pair[0]) < 1e-9:
                continue

            # Fit 2-point model
            v0 = (z_pair[1]*v_pair[1] - z_pair[0]*v_pair[0]) / (z_pair[1] - z_pair[0])
            A = z_pair[0] * (v_pair[0] - v0)

            # Check all points against this model
            denom = vs - v0
            denom = np.where(np.abs(denom) < 0.1, 0.1, denom)
            predicted = A / denom
            errors = np.abs(predicted - zs)
            inliers = errors < inlier_threshold
            count = np.sum(inliers)

            if count > best_inlier_count:
                best_inlier_count = count
                best_inlier_mask = inliers
                best_params = (A, v0)

        if best_params is None or best_inlier_count < 2:
            print("Calibration: RANSAC found no consistent model.")
            print("  This usually means detection errors. Check debug frames.")
            return False

        # Report outliers
        outlier_indices = np.where(~best_inlier_mask)[0]
        if len(outlier_indices) > 0:
            print(f"Calibration: rejecting {len(outlier_indices)} outlier(s):")
            for idx in outlier_indices:
                print(f"  Point {idx}: v={vs[idx]:.0f}, z={zs[idx]:.3f}m")

        # Refit on inliers using least squares if enough points
        inlier_vs = vs[best_inlier_mask]
        inlier_zs = zs[best_inlier_mask]
        n_in = len(inlier_vs)

        if n_in == 2:
            return self._fit_2point(inlier_vs, inlier_zs)

        # Nonlinear LS on inliers
        from scipy.optimize import least_squares as scipy_ls

        A_init, v0_init = best_params

        def residuals(params):
            A, v0, B = params
            denom = inlier_vs - v0
            denom = np.where(np.abs(denom) < 0.1, 0.1, denom)
            return A / denom + B - inlier_zs

        result = scipy_ls(residuals, [A_init, v0_init, 0.0],
                          method='lm', max_nfev=5000)

        self._A, self._v0, self._B = result.x
        self._calibrated = True

        rms = np.sqrt(np.mean(result.fun ** 2))
        print(f"Calibration ({n_in} inliers of {n}): "
              f"A={self._A:.2f}, v0={self._v0:.2f}, B={self._B:.4f}")
        print(f"  RMS residual: {rms:.4f}m")

        for i, (v, z) in enumerate(zip(inlier_vs, inlier_zs)):
            z_pred = self._A / (v - self._v0) + self._B
            err = abs(z_pred - z)
            print(f"  Inlier: v={v:.0f}, actual={z:.3f}m, "
                  f"predicted={z_pred:.3f}m, err={err:.3f}m")

        return True

    def _fit_2point(self, vs, zs):
        v1, z1 = vs[0], zs[0]
        v2, z2 = vs[1], zs[1]

        if abs(z2 - z1) < 1e-9:
            print("Calibration: distances too similar")
            return False

        self._v0 = (z2*v2 - z1*v1) / (z2 - z1)
        self._A = z1 * (v1 - self._v0)
        self._B = 0.0
        self._calibrated = True
        print(f"Calibration (2-point): A={self._A:.2f}, v0={self._v0:.2f}")
        return True

    # ─── Depth Estimation ─────────────────────────────────

    def pixel_to_depth(self, v_pixel):
        if not self._calibrated:
            raise RuntimeError("Not calibrated")
        denom = v_pixel - self._v0
        if abs(denom) < 0.5:
            return float('inf')
        return self._A / denom + self._B

    def estimate_depth(self, frame):
        """Single-frame depth estimate."""
        dot = self.detect_laser(frame)
        if dot is None:
            return {'valid': False, 'depth_m': None, 'pixel': None}

        u, v = dot
        raw_z = self.pixel_to_depth(float(v))

        if raw_z < 0.01 or raw_z > 20.0:
            return {'valid': False, 'depth_m': None, 'pixel': dot,
                    'reason': f'z={raw_z:.2f}m OOB'}

        if self._depth_ema is None:
            self._depth_ema = raw_z
        else:
            self._depth_ema = (self._ema_alpha * raw_z +
                               (1 - self._ema_alpha) * self._depth_ema)

        return {'valid': True, 'depth_m': self._depth_ema,
                'raw_depth_m': raw_z, 'pixel': dot}

    def estimate_depth_multiframe(self, cap):
        """Multi-frame depth estimate."""
        dot = self.detect_laser_multiframe(cap)
        if dot is None:
            return {'valid': False, 'depth_m': None, 'pixel': None}

        u, v = dot
        raw_z = self.pixel_to_depth(float(v))

        if raw_z < 0.01 or raw_z > 20.0:
            return {'valid': False, 'depth_m': None, 'pixel': dot,
                    'reason': f'z={raw_z:.2f}m OOB'}

        if self._depth_ema is None:
            self._depth_ema = raw_z
        else:
            self._depth_ema = (self._ema_alpha * raw_z +
                               (1 - self._ema_alpha) * self._depth_ema)

        return {'valid': True, 'depth_m': self._depth_ema,
                'raw_depth_m': raw_z, 'pixel': dot}

    # ─── Save / Load ─────────────────────────────────────

    def save_calibration(self, path):
        data = {'A': self._A, 'v0': self._v0, 'B': self._B,
                'calibrated': self._calibrated, 'points': self._cal_points}
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Calibration saved: {path}")

    def load_calibration(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        self._A = data['A']
        self._v0 = data['v0']
        self._B = data['B']
        self._calibrated = data['calibrated']
        self._cal_points = data.get('points', [])
        print(f"Calibration loaded: {path}")
        print(f"  A={self._A:.2f}, v0={self._v0:.2f}, B={self._B:.4f}")

    # ─── Debug ────────────────────────────────────────────

    def annotate_frame(self, frame, result):
        out = frame.copy()
        if result.get('pixel'):
            u, v = result['pixel']
            cv2.drawMarker(out, (u, v), (0, 255, 0),
                           cv2.MARKER_CROSS, 20, 2)
            if result.get('valid') and result.get('depth_m'):
                cv2.putText(out, f"{result['depth_m']:.2f}m",
                            (u + 15, v - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)
        return out

    def save_debug_frame(self, frame, path):
        """Save frame with all candidates circled + scored."""
        out = frame.copy()
        candidates = self._find_bright_candidates(frame)
        for cx, cy, score in candidates:
            cv2.circle(out, (cx, cy), 8, (0, 0, 255), 1)
            cv2.putText(out, f"{score:.0f}", (cx + 10, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        cv2.imwrite(path, out)
        print(f"  Debug: {path} ({len(candidates)} candidates)")