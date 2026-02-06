import cv2
import time
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
    ):
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

    def _print_actual_format(self):
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Camera: {w}x{h} @ {fps:.1f} FPS")

    def snap(self):
        """Capture one frame (raw BGR image)."""
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
        self.cap.release()
