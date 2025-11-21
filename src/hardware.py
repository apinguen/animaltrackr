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
from typing import Callable, List

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
        atexit.register(self.cleanup)

    # ---------------------------------------------------------------------
    # Setup / teardown
    def setup(self) -> None:
        """Initialise GPIO pins and optional servo driver."""

        if self._configured:
            return

        if self._gpio is None:
            logging.warning("GPIO library not available; running hardware in dry-run mode.")
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

        self._configured = True

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
    # Actuators
    def set_led(self, r: bool = False, g: bool = False, b: bool = False) -> None:
        """Control the RGB LED."""

        if self._gpio is None:
            logging.info("LED set to R=%s G=%s B=%s (dry-run)", r, g, b)
            return

        self._gpio.output(const.LED_R_PIN, self._gpio.HIGH if r else self._gpio.LOW)
        self._gpio.output(const.LED_G_PIN, self._gpio.HIGH if g else self._gpio.LOW)
        self._gpio.output(const.LED_B_PIN, self._gpio.HIGH if b else self._gpio.LOW)

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


__all__ = ["Hardware"]