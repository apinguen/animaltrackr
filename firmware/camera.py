"""Camera control helpers for Pi Zero builds."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Generator, Optional, Tuple

import constants as const

try:
    from picamera2 import Picamera2  # type: ignore
except (ImportError, RuntimeError):
    Picamera2 = None  # type: ignore


class Camera:
    """Thin wrapper around Picamera2 with friendly defaults."""

    def __init__(
        self,
        resolution: Tuple[int, int] = const.CAMERA_RESOLUTION,
        framerate: int = 10,
        output_dir: str | Path | None = None,
    ) -> None:
        self._resolution = resolution
        self._framerate = framerate
        self._output_dir = Path(output_dir or const.DATA_DIR)
        self._picam: Optional[Any] = None

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the camera stream."""

        picam = self._picam
        if picam is None:
            if Picamera2 is None:
                logging.warning("Picamera2 not installed; camera start is a no-op")
                return

            self._picam = Picamera2()
            picam = self._picam
            config = picam.create_video_configuration(
                main={"size": self._resolution, "format": "RGB888"},
            )
            picam.configure(config)

        assert picam is not None
        picam.start()
        logging.info("Camera started at %s @ %sfps", self._resolution, self._framerate)

    def stop(self) -> None:
        """Stop the camera stream."""

        if self._picam is not None:
            self._picam.stop()
            logging.info("Camera stopped")

    # ------------------------------------------------------------------
    def frames(self, frame_limit: int | None = None) -> Generator:
        """Yield frames from the camera. Blocks until stop is called."""

        picam = self._picam
        if picam is None:
            raise RuntimeError("Camera not started or Picamera2 unavailable")

        produced = 0
        delay = 1 / max(1, self._framerate)
        while frame_limit is None or produced < frame_limit:
            frame = picam.capture_array()
            produced += 1
            yield frame
            time.sleep(delay)

    def capture_photo(self, filename: str | None = None) -> Path:
        """Capture a single still image and return the file path."""

        picam = self._picam
        if picam is None:
            raise RuntimeError("Camera not started")

        self._output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        path = self._output_dir / (filename or f"capture-{timestamp}.jpg")
        picam.capture_file(str(path))
        return path


__all__ = ["Camera"]