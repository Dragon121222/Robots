import cv2
import numpy as np

# --- Synthetic setup: create a simple image with dots ---
h, w = 240, 320
img0 = np.zeros((h, w), dtype=np.uint8)

# Draw some points
np.random.seed(42)
num_points = 50
points = np.random.randint(20, min(h,w)-20, (num_points, 2))
for x, y in points:
    cv2.circle(img0, (x, y), 2, 255, -1)

# --- Simulate camera motion (move up 5 pixels) ---
translation_pixels = np.array([0, -5])  # camera moves up
img1 = np.zeros_like(img0)
for x, y in points:
    new_pos = (x + translation_pixels[0], y + translation_pixels[1])
    if 0 <= new_pos[0] < w and 0 <= new_pos[1] < h:
        cv2.circle(img1, new_pos, 2, 255, -1)

# --- Step 1: Detect features ---
orb = cv2.ORB_create(100)
kp0, des0 = orb.detectAndCompute(img0, None)
kp1, des1 = orb.detectAndCompute(img1, None)

# --- Step 2: Match features ---
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = bf.match(des0, des1)

# --- Step 3: Build projection matrices (simple 2D simulation) ---
# Identity for frame 0, translation for frame 1
P0 = np.array([[1, 0, 0],
               [0, 1, 0]], dtype=float)
P1 = np.array([[1, 0, translation_pixels[0]],
               [0, 1, translation_pixels[1]]], dtype=float)

# --- Step 4: Triangulate (2D simulation: disparity → depth) ---
depth = np.zeros_like(img0, dtype=np.float32)
for m in matches:
    u0, v0 = map(int, kp0[m.queryIdx].pt)
    u1, v1 = map(int, kp1[m.trainIdx].pt)
    disparity = abs(v1 - v0)  # vertical displacement
    if disparity > 0:
        depth_val = 1.0 / disparity  # inverse disparity = depth
        depth[v0, u0] = depth_val

# Normalize for visualization
depth_vis = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# Show images
cv2.imshow("Frame 0", img0)
cv2.imshow("Frame 1", img1)
cv2.imshow("Depth (simulated temporal stereo)", depth_vis)
cv2.waitKey(0)
cv2.destroyAllWindows()

