"""Application entry point preserving the original state-machine structure."""

from __future__ import annotations

import logging
import signal
import time
from typing import Any, Dict, Tuple

import constants as const
from camera import Camera
from hardware import Hardware
from inference import InferenceEngine
from menu import InputActions, Menu

logging.basicConfig(level=getattr(logging, const.DEFAULT_LOG_LEVEL, logging.INFO))


class Application:
    """Coordinates hardware, camera, and inference via a match-based state machine."""

    def __init__(self) -> None:
        self.hw = Hardware()
        self.camera = Camera()
        self.engine = InferenceEngine(const.MODEL_PATH)
        self.menu = Menu()
        self.menu.mode = const.MODE
        self.mode = self.menu.getMode()
        lines = self.menu.getMessage()
        if len(lines) < 2:
            lines = lines + [""] * (2 - len(lines))
        self._menu_lines: Tuple[str, str] = (lines[0], lines[1])
        self.state = const.State.IDLE
        self._running = True
        self._motion_detected = False
        self._current_yaw = 90.0
        self._current_pitch = 90.0
        self._sweep_direction = 1
        self._next_sweep_time = 0.0
        self._led_cycle = [
            ((True, False, False), "RED"),
            ((False, True, False), "GREEN"),
            ((False, False, True), "BLUE"),
            ((True, True, True), "WHITE"),
            ((False, False, False), "OFF"),
        ]
        self._led_cycle_index = 0
        self._next_led_cycle = 0.0
        self._pitch_direction = 1
        self._next_pitch_step = 0.0
        self._next_pump_test = 0.0
        self._next_sensor_report = 0.0
        self._last_sensor_snapshot: Dict[str, float | bool] | None = None
        self._next_camera_test = 0.0
        self._status_led: str | None = None
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
        try:
            self.hw.setup()
            self.camera.start()
            self.hw.set_servo_angle("yaw", self._current_yaw)
            self.hw.set_servo_angle("pitch", self._current_pitch)
        except Exception:
            self._set_status_led("error")
            raise
        self._set_status_led("idle" if self.hw.has_real_gpio else "error")

    def _tick(self) -> None:
        self._update_menu()
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
            case const.Mode.LED_TEST:
                self._tick_led_test()
            case const.Mode.SERVO_TEST:
                self._tick_servo_test()
            case const.Mode.PUMP_TEST:
                self._tick_pump_test()
            case const.Mode.SENSOR_TEST:
                self._tick_sensor_test()
            case const.Mode.CAMERA_TEST:
                self._tick_camera_test()

    def _tick_tuning(self) -> None:
        logging.debug("TUNING mode idle tick")
        self._idle_wait(0.1)

    def _tick_default(self) -> None:
        logging.debug("DEFAULT mode idle tick")
        self._idle_wait(0.1)

    def _tick_picture(self) -> None:
        if not self._motion_detected:
            self._idle_wait(0.25)
            return
        self._motion_detected = False
        logging.info("PICTURE mode: motion detected, capturing photo")
        self._engage_target(shoot=False, capture=True)
        self._idle_wait(0.25)

    def _tick_turret(self) -> None:
        self._sweep_yaw()
        if not self._motion_detected:
            self._idle_wait(0.05)
            return
        self._motion_detected = False
        logging.info("TURRET mode: engaging motion target")
        self._engage_target(shoot=True, capture=False)

    def _tick_picture_fire(self) -> None:
        self._sweep_yaw()
        if not self._motion_detected:
            self._idle_wait(0.05)
            return
        self._motion_detected = False
        logging.info("PICTURE_FIRE mode: engaging target with photo + water")
        self._engage_target(shoot=True, capture=True)

    def _on_motion(self) -> None:
        logging.info("Motion detected via PIR")
        self._motion_detected = True

    def _update_menu(self) -> None:
        action = self.hw.getInput()
        if action is InputActions.NONE:
            return
        previous_mode = self.menu.getMode()
        self.menu.update(action)
        lines = self.menu.getMessage()
        if len(lines) < 2:
            lines = lines + [""] * (2 - len(lines))
        new_lines = (lines[0], lines[1])
        if new_lines != self._menu_lines:
            self._menu_lines = new_lines
            logging.debug("Menu: %s | %s", new_lines[0], new_lines[1])
            self.hw.display_message(list(new_lines))
        if self.menu.getMode() != previous_mode:
            self.mode = self.menu.getMode()
            logging.info("Mode switched to %s", self.mode.name)

    def _idle_wait(self, duration: float) -> None:
        time.sleep(duration)

    def _sweep_yaw(self) -> None:
        now = time.time()
        if now < self._next_sweep_time:
            return
        self._current_yaw += self._sweep_direction * 2
        if self._current_yaw >= 170:
            self._current_yaw = 170
            self._sweep_direction = -1
        elif self._current_yaw <= 10:
            self._current_yaw = 10
            self._sweep_direction = 1
        self.hw.set_servo_angle("yaw", self._current_yaw)
        self._next_sweep_time = now + 0.2

    def _engage_target(self, *, shoot: bool, capture: bool) -> None:
        frame = self._capture_frame_for_analysis()
        yaw, pitch = self._resolve_target_angles(frame)
        self._set_turret_angles(yaw=yaw, pitch=pitch)

        shooting_error = False
        if shoot:
            self._set_status_led("shooting")
            try:
                self.hw.trigger_gun()
            except Exception:
                shooting_error = True
                self._set_status_led("error")
                logging.exception("Failed to fire water gun")

        if capture and not shooting_error:
            self._capture_photo_with_feedback()
        elif not shoot and not capture and self._status_led != "error":
            self._set_status_led("idle")

    def _capture_photo_with_feedback(self, filename: str | None = None) -> None:
        self._set_status_led("capture")
        self.hw.set_ir_led(True)
        try:
            path = self.camera.capture_photo(filename)
            logging.info("Captured image %s", path)
        except Exception:
            self._set_status_led("error")
            logging.exception("Failed to capture photo")
        finally:
            self.hw.set_ir_led(False)
            if self._status_led != "error":
                self._set_status_led("idle")

    def _capture_frame_for_analysis(self) -> Any | None:
        try:
            for frame in self.camera.frames(frame_limit=1):
                return frame
        except Exception:
            logging.exception("Unable to pull analysis frame")
        return None

    def _resolve_target_angles(self, frame: Any | None) -> Tuple[float, float]:
        target_x, target_y = self._estimate_motion_vector(frame)
        dx = (target_x - const.CAMERA_CENTER[0]) / max(1, const.CAMERA_CENTER[0])
        dy = (target_y - const.CAMERA_CENTER[1]) / max(1, const.CAMERA_CENTER[1])
        yaw = max(0.0, min(180.0, self._current_yaw - dx * 30))
        pitch = max(0.0, min(180.0, self._current_pitch + dy * 20))
        return yaw, pitch

    def _estimate_motion_vector(self, frame: Any | None) -> Tuple[float, float]:
        if frame is None:
            return const.CAMERA_CENTER
        try:
            height, width = frame.shape[:2]
            return (width / 2, height / 2)
        except AttributeError:
            return const.CAMERA_CENTER

    def _set_turret_angles(self, yaw: float | None = None, pitch: float | None = None) -> None:
        if yaw is not None:
            self._current_yaw = yaw
            self.hw.set_servo_angle("yaw", self._current_yaw)
        if pitch is not None:
            self._current_pitch = pitch
            self.hw.set_servo_angle("pitch", self._current_pitch)
        self._idle_wait(const.SERVO_WAIT_TIME)

    def _set_status_led(self, status: str) -> None:
        if status == self._status_led:
            return
        if status == "idle" and not self.hw.has_real_gpio:
            status = "error"
        self._status_led = status
        match status:
            case "error":
                self.hw.set_led(r=True)
            case "shooting":
                self.hw.set_led(r=True, g=True)     # yellow
            case "capture":
                self.hw.set_led(g=True)
            case "idle":
                self.hw.set_led(b=True)
            case _:
                self.hw.set_led()

    # ------------------------------------------------------------------
    # Diagnostic / calibration helpers
    def _tick_led_test(self) -> None:
        now = time.time()
        if now >= self._next_led_cycle:
            color, label = self._led_cycle[self._led_cycle_index]
            self.hw.set_led(*color)
            logging.info("LED test: %s", label)
            self._led_cycle_index = (self._led_cycle_index + 1) % len(self._led_cycle)
            self._next_led_cycle = now + 0.75
        self._idle_wait(0.05)

    def _tick_servo_test(self) -> None:
        self._sweep_yaw()
        now = time.time()
        if now >= self._next_pitch_step:
            self._current_pitch += self._pitch_direction * 4
            if self._current_pitch >= 150:
                self._current_pitch = 150
                self._pitch_direction = -1
            elif self._current_pitch <= 30:
                self._current_pitch = 30
                self._pitch_direction = 1
            self.hw.set_servo_angle("pitch", self._current_pitch)
            logging.info("Servo test: yaw=%.1f pitch=%.1f", self._current_yaw, self._current_pitch)
            self._next_pitch_step = now + 0.25
        self._idle_wait(0.05)

    def _tick_pump_test(self) -> None:
        self.hw.set_led(r=True, b=True)
        now = time.time()
        if now >= self._next_pump_test:
            logging.info("Pump test: firing water gun")
            self.hw.trigger_gun()
            self._next_pump_test = now + 10
        self._idle_wait(0.25)

    def _tick_sensor_test(self) -> None:
        snapshot = self.hw.snapshot_inputs()
        now = time.time()
        if self._last_sensor_snapshot != snapshot and now >= self._next_sensor_report:
            logging.info("Sensor test snapshot: %s", snapshot)
            self._last_sensor_snapshot = snapshot
            self._next_sensor_report = now + 0.5

        if snapshot.get("pir"):
            self.hw.set_led(r=True)
        elif snapshot.get("confirm"):
            self.hw.set_led(g=True)
        elif snapshot.get("back"):
            self.hw.set_led(b=True)
        else:
            self.hw.set_led()
        self._idle_wait(0.1)

    def _tick_camera_test(self) -> None:
        now = time.time()
        if now >= self._next_camera_test:
            try:
                path = self.camera.capture_photo(f"camera-test-{int(now)}.jpg")
                logging.info("Camera test captured %s", path)
            except Exception:
                logging.exception("Camera test capture failed")
            self._next_camera_test = now + 10
        self._idle_wait(0.25)

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

