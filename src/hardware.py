"""Hardware abstraction for Raspberry Pi Zero.

This module centralises all direct GPIO / actuator access so the rest of the
application can be unit-tested on non-Pi hosts. When the Pi-specific libraries
are not available, the class transparently falls back to a dry-run mode that
only logs actions.
"""
from __future__ import annotations

import atexit
import logging
import time
from typing import Callable, Dict, List, Tuple
from menu import InputActions

try:
    from LCD import LCD
except ImportError:  # pragma: no cover - optional dependency
    LCD = None  # type: ignore

import constants as const


try:
    import RPi.GPIO as GPIO  # type: ignore
except (ImportError, RuntimeError):
    GPIO = None  # type: ignore

try:
    from adafruit_servokit import ServoKit  # type: ignore
except (ImportError, RuntimeError):
    ServoKit = None  # type: ignore


class Hardware:
    """High-level hardware facade for PIR, LEDs, servos, and the squirt gun."""

    def __init__(self) -> None:
        self._gpio = GPIO
        self._kit = None
        self._pir_callbacks: List[Callable[[], None]] = []
        self._configured = False
        self.backButtonPressed = False
        self.confirmButtonPressed = False
        if LCD is not None:
            try:
                self.lcd = LCD(2, 0x27, True)
            except Exception:  # pragma: no cover - hardware specific init
                logging.exception("Unable to initialise LCD; continuing without display")
                self.lcd = None
        else:
            self.lcd = None
        self.lastMessage = ["", ""]
        atexit.register(self.cleanup)

    # ---------------------------------------------------------------------
    # Setup / teardown
    def setup(self) -> None:
        """Initialise GPIO pins and optional servo driver."""

        if self._configured:
            return

        if self._gpio is None:
            logging.warning("GPIO library not available; running hardware in dry-run mode.")
            self._configured = True
            return

        logging.info("Setting up GPIO pins using BOARD numbering")
        self._gpio.setmode(self._gpio.BOARD)

        for pin in (const.LED_R_PIN, const.LED_G_PIN, const.LED_B_PIN):
            self._gpio.setup(pin, self._gpio.OUT, initial=self._gpio.LOW)

        for pin in (const.GUN_PUMP_PIN, const.GUN_SHOOT_PIN):
            self._gpio.setup(pin, self._gpio.OUT, initial=self._gpio.LOW)

        self._gpio.setup(const.PIR_PIN, self._gpio.IN)

        self._gpio.setup(const.YAW_SERVO_PIN, self._gpio.OUT)
        self._gpio.setup(const.PITCH_SERVO_PIN, self._gpio.OUT)

        self._gpio.add_event_detect(
            const.PIR_PIN,
            self._gpio.RISING,
            callback=lambda channel: self._handle_pir_trigger(),
            bouncetime=200,
        )

        if ServoKit is not None:
            try:
                self._kit = ServoKit(channels=16)
            except Exception as exc:  # pragma: no cover - hardware specific
                logging.warning("Unable to initialise ServoKit: %s", exc)
                self._kit = None
        else:
            logging.info("ServoKit not installed; defaulting to GPIO PWM for servos")
        
        self._gpio.setup(const.BACK_BUTTON_PIN, self._gpio.IN, pull_up_down=self._gpio.PUD_DOWN)
        self._gpio.setup(const.CONFIRM_BUTTON_PIN, self._gpio.IN, pull_up_down=self._gpio.PUD_DOWN)

        self._gpio.add_event_detect(
            const.BACK_BUTTON_PIN,
            self._gpio.RISING,
            callback=lambda channel: self.backButtonCallback(channel),
            bouncetime=200,
        )

        self._gpio.add_event_detect(
            const.CONFIRM_BUTTON_PIN,
            self._gpio.RISING,
            callback=lambda channel: self.confirmButtonCallback(channel),
            bouncetime=200,
        )

        self._gpio.setup(const.IR_LED_PIN, self._gpio.OUT, initial=self._gpio.LOW)

        self._configured = True

    @property
    def has_real_gpio(self) -> bool:
        return self._gpio is not None

    def cleanup(self) -> None:
        """Release hardware resources."""

        if self._gpio is not None:
            try:
                self._gpio.cleanup()
            except Exception:
                logging.exception("Failed to clean up GPIO")
        self._configured = False

    # ------------------------------------------------------------------
    # PIR events
    def when_motion(self, callback: Callable[[], None]) -> None:
        """Register a callback invoked whenever the PIR sensor fires."""

        self._pir_callbacks.append(callback)

    def _handle_pir_trigger(self) -> None:
        logging.debug("PIR trigger received; notifying %d callbacks", len(self._pir_callbacks))
        for callback in self._pir_callbacks:
            try:
                callback()
            except Exception:  # pragma: no cover - defensive programming
                logging.exception("PIR callback raised an exception")
    
    # ------------------------------------------------------------------
    # Button events
    def backButtonCallback(self, channel: int) -> None:
        self.backButtonPressed = True

    def confirmButtonCallback(self, channel: int) -> None:
        self.confirmButtonPressed = True

    def getJoystickDirection(self, tolerance: float) -> Tuple[float, float]:
        """Check the state of the joystick and return its (x, y) direction."""

        if self._gpio is None:
            logging.info("Joystick read (dry-run); returning (0.0, 0.0)")
            return (0.0, 0.0)

        x_val = self._gpio.input(const.JOYSTICK_VRX_PIN)
        y_val = self._gpio.input(const.JOYSTICK_VRY_PIN)

        x_dir = 0.0
        y_dir = 0.0

        if x_val > tolerance:
            x_dir = 1.0
        elif x_val < -tolerance:
            x_dir = -1.0

        if y_val > tolerance:
            y_dir = 1.0
        elif y_val < -tolerance:
            y_dir = -1.0

        return (x_dir, y_dir)

    # ------------------------------------------------------------------
    def set_led(self, r: bool = False, g: bool = False, b: bool = False) -> None:
        """Control the RGB LED."""

        if self._gpio is None:
            logging.info("LED set to R=%s G=%s B=%s (dry-run)", r, g, b)
            return

        self._gpio.output(const.LED_R_PIN, self._gpio.HIGH if r else self._gpio.LOW)
        self._gpio.output(const.LED_G_PIN, self._gpio.HIGH if g else self._gpio.LOW)
        self._gpio.output(const.LED_B_PIN, self._gpio.HIGH if b else self._gpio.LOW)
    
    def display_message(self, lines: List[str] | Tuple[str, str]) -> None:
        """Display a message on the LCD screen."""

        display_lines = list(lines)
        if len(display_lines) < 2:
            display_lines += [""] * (2 - len(display_lines))

        if self.lcd is None:
            logging.info("LCD display (dry-run): %s | %s", display_lines[0], display_lines[1])
            return

        if display_lines == self.lastMessage:
            return  # No change

        self.lastMessage = display_lines
        self.lcd.clear()
        self.lcd.message(display_lines[0], 1)
        self.lcd.message(display_lines[1], 2)
    
    def getInput(self) -> InputActions:
        """Check the state of the buttons and return an InputActions value."""
        actions = InputActions.NONE
        if self.backButtonPressed:
            actions = InputActions.BACK
            self.backButtonPressed = False
        elif self.confirmButtonPressed:
            actions = InputActions.CONFIRM
            self.confirmButtonPressed = False
        elif self._gpio is not None:
            x_dir, y_dir = self.getJoystickDirection(tolerance=0.5)
            if y_dir > 0:
                actions = InputActions.UP
            elif y_dir < 0:
                actions = InputActions.DOWN
            elif x_dir < 0:
                actions = InputActions.LEFT
            elif x_dir > 0:
                actions = InputActions.RIGHT
        
        return actions

    def snapshot_inputs(self) -> Dict[str, float | bool]:
        """Return a snapshot of key input states for diagnostics."""

        if self._gpio is None:
            return {
                "pir": False,
                "back": self.backButtonPressed,
                "confirm": self.confirmButtonPressed,
                "joystick_x": 0.0,
                "joystick_y": 0.0,
            }

        snapshot: Dict[str, float | bool] = {
            "pir": bool(self._gpio.input(const.PIR_PIN)),
            "back": bool(self._gpio.input(const.BACK_BUTTON_PIN)),
            "confirm": bool(self._gpio.input(const.CONFIRM_BUTTON_PIN)),
        }
        x_dir, y_dir = self.getJoystickDirection(tolerance=0.5)
        snapshot["joystick_x"] = x_dir
        snapshot["joystick_y"] = y_dir
        return snapshot
    # Actuators
    

    def set_servo_angle(self, channel: str, angle: float) -> None:
        """Move the yaw or pitch servo to the requested angle."""

        angle = max(0, min(180, angle))
        if channel not in {"yaw", "pitch"}:
            raise ValueError("channel must be 'yaw' or 'pitch'")

        if self._kit is not None:
            idx = 0 if channel == "yaw" else 1
            try:
                self._kit.servo[idx].angle = angle
            except Exception:  # pragma: no cover - hardware specific
                logging.exception("Failed to move servo via ServoKit")
            return

        if self._gpio is None:
            logging.info("Servo %s -> %.1f (dry-run)", channel, angle)
            return

        pin = const.YAW_SERVO_PIN if channel == "yaw" else const.PITCH_SERVO_PIN
        pwm = self._gpio.PWM(pin, 50)
        pwm.start(0)
        duty = angle / 18 + 2
        pwm.ChangeDutyCycle(duty)
        logging.debug("Servo %s duty %.2f", channel, duty)
        pwm.stop()

    def trigger_gun(self, pump_time: float | None = None, shoot_time: float | None = None) -> None:
        """Fire the water gun for the configured duration."""

        pump_time = pump_time or const.GUN_PUMP_TIME
        shoot_time = shoot_time or const.GUN_SHOOT_TIME

        if self._gpio is None:
            logging.info("Gun fired (dry-run) pump=%.2fs shoot=%.2fs", pump_time, shoot_time)
            return

        self._gpio.output(const.GUN_PUMP_PIN, self._gpio.HIGH)
        self._gpio.output(const.GUN_SHOOT_PIN, self._gpio.LOW)
        time.sleep(pump_time)
        self._gpio.output(const.GUN_SHOOT_PIN, self._gpio.HIGH)
        time.sleep(shoot_time)
        self._gpio.output(const.GUN_SHOOT_PIN, self._gpio.LOW)
        self._gpio.output(const.GUN_PUMP_PIN, self._gpio.LOW)

    def set_ir_led(self, enabled: bool) -> None:
        if self._ir_led_state == enabled:
            return
        self._ir_led_state = enabled
        if self._gpio is None:
            logging.info("IR LED %s (dry-run)", "ON" if enabled else "OFF")
            return
        level = self._gpio.HIGH if enabled else self._gpio.LOW
        self._gpio.output(const.IR_LED_PIN, level)
        logging.debug("IR LED -> %s", "ON" if enabled else "OFF")


__all__ = ["Hardware"]