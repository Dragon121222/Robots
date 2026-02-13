# import cv2
# import time
# from datetime import datetime
# from pathlib import Path


# class simpleCam:
#     def __init__(
#         self,
#         device="/dev/video1",
#         width=640,
#         height=480,
#         fps=30,
#         fourcc="MJPG",
#     ):

#         self._last_seen = {}  # class_name -> timestamp
#         self._timeout_fired = {}  # class_name -> bool (avoid repeated triggers)
#         self.LOST_TIMEOUT = 5.0

#         print("CTOR Simple Camera")
#         self.device = device
#         self.width = width
#         self.height = height
#         self.fps = fps
#         self.fourcc = fourcc

#         self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
#         if not self.cap.isOpened():
#             raise RuntimeError(f"Failed to open camera {device}")

#         self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
#         self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
#         self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
#         self.cap.set(cv2.CAP_PROP_FPS, fps)
#         self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

#         # Warm-up
#         for _ in range(5):
#             self.cap.read()

#         self._print_actual_format()

#     def _print_actual_format(self):
#         w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         fps = self.cap.get(cv2.CAP_PROP_FPS)
#         print(f"Camera: {w}x{h} @ {fps:.1f} FPS")

#     def snap(self):
#         """Capture one frame (raw BGR image)."""
#         ok, frame = self.cap.read()
#         if not ok:
#             raise RuntimeError("Camera read failed")
#         return frame

#     def snap_jpeg(self, quality=90):
#         """Capture one frame, return JPEG bytes."""
#         frame = self.snap()
#         ok, buf = cv2.imencode(
#             ".jpg",
#             frame,
#             [cv2.IMWRITE_JPEG_QUALITY, quality],
#         )
#         if not ok:
#             raise RuntimeError("JPEG encode failed")
#         return buf.tobytes()

#     def save(self, directory="/tmp/camera_snaps"):
#         """Capture and save to disk."""
#         Path(directory).mkdir(parents=True, exist_ok=True)
#         frame = self.snap()
#         ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#         path = Path(directory) / f"snap_{ts}.jpg"
#         cv2.imwrite(str(path), frame)
#         return path

#     def close(self):
#         self.cap.release()

import cv2
import time
import threading
from datetime import datetime
from pathlib import Path


class simpleCam:
    def __init__(
        self,
        device="/dev/video1",
        width=640,
        height=480,
        fps=30,
        fourcc="MJPG",
        stale_after=2.0,
    ):
        self._last_seen = {}
        self._timeout_fired = {}
        self.LOST_TIMEOUT = 5.0

        print("CTOR Simple Camera")
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.fourcc = fourcc

        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {device}")

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Warm-up
        for _ in range(5):
            self.cap.read()
        self._print_actual_format()

        # --- Warm-frame buffer ---
        self._stale_after = stale_after
        self._frame_lock = threading.Lock()
        self._last_snap_time = time.monotonic()
        self._warm_frame = None
        self._stop = threading.Event()
        self._refresher = threading.Thread(target=self._keep_warm, daemon=True)
        self._refresher.start()

    def _print_actual_format(self):
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Camera: {w}x{h} @ {fps:.1f} FPS")

    def _keep_warm(self):
        """Background thread: grab fresh frames when snap() goes stale."""
        poll_interval = self._stale_after / 4
        while not self._stop.wait(timeout=poll_interval):
            with self._frame_lock:
                elapsed = time.monotonic() - self._last_snap_time
                if elapsed >= self._stale_after:
                    ok, frame = self.cap.read()
                    if ok:
                        self._warm_frame = frame
                        self._last_snap_time = time.monotonic()

    def snap(self):
        """Capture one frame (raw BGR image)."""
        with self._frame_lock:
            self._last_snap_time = time.monotonic()
            if self._warm_frame is not None:
                frame = self._warm_frame
                self._warm_frame = None
                return frame
            ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Camera read failed")
        return frame

    def snap_jpeg(self, quality=90):
        """Capture one frame, return JPEG bytes."""
        frame = self.snap()
        ok, buf = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality],
        )
        if not ok:
            raise RuntimeError("JPEG encode failed")
        return buf.tobytes()

    def save(self, directory="/tmp/camera_snaps"):
        """Capture and save to disk."""
        Path(directory).mkdir(parents=True, exist_ok=True)
        frame = self.snap()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = Path(directory) / f"snap_{ts}.jpg"
        cv2.imwrite(str(path), frame)
        return path

    def close(self):
        self._stop.set()
        self._refresher.join(timeout=2.0)
        self.cap.release()