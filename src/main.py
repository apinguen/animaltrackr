"""Application entry point preserving the original state-machine structure."""

from __future__ import annotations

import logging
import signal

import constants as const
from camera import Camera
from hardware import Hardware
from inference import InferenceEngine

logging.basicConfig(level=getattr(logging, const.DEFAULT_LOG_LEVEL, logging.INFO))


class Application:
    """Coordinates hardware, camera, and inference via a match-based state machine."""

    def __init__(self) -> None:
        self.hw = Hardware()
        self.camera = Camera()
        self.engine = InferenceEngine(const.MODEL_PATH)
        self.mode = const.MODE
        self.state = const.State.IDLE
        self._running = True
        self.hw.when_motion(self._on_motion)

    def run(self) -> None:
        self._setup()
        signal.signal(signal.SIGTERM, lambda *_: self.stop())

        try:
            while self._running:
                self._tick()
        except KeyboardInterrupt:
            logging.info("Interrupted; shutting down")
        finally:
            self._shutdown()

    # ------------------------------------------------------------------
    def _setup(self) -> None:
        self.hw.setup()
        self.camera.start()

    def _tick(self) -> None:
        match self.mode:
            case const.Mode.TUNING:
                self._tick_tuning()
            case const.Mode.DEFAULT:
                self._tick_default()
            case const.Mode.PICTURE:
                self._tick_picture()
            case const.Mode.TURRET:
                self._tick_turret()
            case const.Mode.PICTURE_FIRE:
                self._tick_picture_fire()

    def _tick_tuning(self) -> None:
        logging.debug("TUNING mode tick")

    def _tick_default(self) -> None:
        logging.debug("DEFAULT mode tick")

    def _tick_picture(self) -> None:
        logging.debug("PICTURE mode tick")

    def _tick_turret(self) -> None:
        logging.debug("TURRET mode tick")

    def _tick_picture_fire(self) -> None:
        logging.debug("PICTURE_FIRE mode tick")

    def _on_motion(self) -> None:
        logging.info("Motion detected via PIR")

    def stop(self) -> None:
        self._running = False

    def _shutdown(self) -> None:
        self.camera.stop()
        self.engine.close()
        self.hw.cleanup()


def main() -> None:
    Application().run()


if __name__ == "__main__":
    main()

