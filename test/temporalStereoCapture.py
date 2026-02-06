import cv2
import numpy as np
import time

def temporal_stereo_capture(cam_index=1, wait_time=1.0):
    """
    Capture two frames from camera, compute sparse temporal stereo depth map.
    Headless version: saves images to disk, no GUI required.
    """
    # --- Open camera ---
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {cam_index}")

    print("Capture first frame")

    # --- Capture first frame ---
    ret, frame0 = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError("Failed to capture first frame")
    gray0 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY)

    # --- Wait ---
    time.sleep(wait_time)

    # --- Capture second frame ---
    ret, frame1 = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError("Failed to capture second frame")
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

    cap.release()

    # --- Detect ORB features ---
    orb = cv2.ORB_create(500)
    kp0, des0 = orb.detectAndCompute(gray0, None)
    kp1, des1 = orb.detectAndCompute(gray1, None)

    # --- Match features ---
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des0, des1)

    if len(matches) == 0:
        raise RuntimeError("No matches found between frames")

    # --- Compute sparse depth (assume vertical motion) ---
    translation_pixels = np.array([0, -5])  # adjust if needed
    depth = np.zeros_like(gray0, dtype=np.float32)
    for m in matches:
        u0, v0 = map(int, kp0[m.queryIdx].pt)
        u1, v1 = map(int, kp1[m.trainIdx].pt)
        disparity = abs(v1 - v0)
        if disparity > 0:
            depth[v0, u0] = 1.0 / disparity  # inverse disparity

    # Normalize for visualization
    depth_vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # --- Save images ---
    cv2.imwrite("frame0.png", gray0)
    cv2.imwrite("frame1.png", gray1)
    cv2.imwrite("depth.png", depth_vis)

    print(f"Saved frame0.png, frame1.png, depth.png (camera index {cam_index})")
    return gray0, gray1, depth_vis

# --- Example usage ---
if __name__ == "__main__":
    f0, f1, depth = temporal_stereo_capture(cam_index=1, wait_time=1.0)

