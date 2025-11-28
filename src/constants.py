"""Project-wide constants and defaults.

Put non-secret configuration values here. Values are typed where practical and
can be overridden via environment variables for simple runtime configuration.

Guidelines:
- Keep secrets out of this file (use environment variables or a secrets manager).
- Keep hardware pin numbers, default paths, and feature flags here.
"""
from __future__ import annotations

import os
from typing import Tuple
from enum import Enum, auto

def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val is not None else default

class Mode(Enum):
    TUNING = auto()
    DEFAULT = auto()
    PICTURE = auto()
    TURRET = auto()
    PICTURE_FIRE = auto()
    LED_TEST = auto()
    SERVO_TEST = auto()
    PUMP_TEST = auto()
    SENSOR_TEST = auto()
    CAMERA_TEST = auto()

class State(Enum):
    IDLE = auto()
    TRACKING = auto()
    FIRING = auto()

MODE = Mode.TUNING

# GPIO.BOARD numbering (matches Hardware._setup_outputs)
PIR_PIN: int = _env_int("PIR_PIN", 7)
LED_R_PIN: int = _env_int("LED_R_PIN", 15)
LED_G_PIN: int = _env_int("LED_G_PIN", 16)
LED_B_PIN: int = _env_int("LED_B_PIN", 18)

SWITCH_ONE_PIN: int = _env_int("SWITCH_ONE_PIN", 29)
SWITCH_TWO_PIN: int = _env_int("SWITCH_TWO_PIN", 31)

CONFIRM_BUTTON_PIN: int = _env_int("CONFIRM_BUTTON_PIN", 32)
BACK_BUTTON_PIN: int = _env_int("BACK_BUTTON_PIN", 33)

JOYSTICK_VRX_PIN: int = _env_int("JOYSTICK_VRX_PIN", 36)
JOYSTICK_VRY_PIN: int = _env_int("JOYSTICK_VRY_PIN", 37)
JOYSTICK_SW_PIN: int = _env_int("JOYSTICK_SW_PIN", 38)

LCD_SDA_PIN: int = _env_int("LCD_SDA_PIN", 3)
LCD_SCL_PIN: int = _env_int("LCD_SCL_PIN", 5)

GUN_PUMP_PIN: int = _env_int("GUN_PUMP_PIN", 35)
GUN_SHOOT_PIN: int = _env_int("GUN_SHOOT_PIN", 40)

YAW_SERVO_PIN: int = _env_int("YAW_SERVO_PIN", 11)
PITCH_SERVO_PIN: int = _env_int("PITCH_SERVO_PIN", 13)

SERVO_WAIT_TIME: float = float(os.getenv("SERVO_WAIT_TIME", "0.5"))
GUN_PUMP_TIME: float = float(os.getenv("GUN_PUMP_TIME", "0.5"))
GUN_SHOOT_TIME: float = float(os.getenv("GUN_SHOOT_TIME", "0.1"))

CAMERA_RESOLUTION: Tuple[int, int] = (640, 480)
CAMERA_FOV_H = 62
CAMERA_FOV_V = 48
CAMERA_CENTER: Tuple[float, float] = (CAMERA_RESOLUTION[0] // 2, CAMERA_RESOLUTION[1] // 2)

PROJECT_ROOT: str = os.path.dirname(os.path.dirname(__file__))
DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
MODEL_PATH: str = os.path.join(PROJECT_ROOT, "models", "model.tflite")

DEFAULT_LOG_LEVEL: str = os.getenv("DEFAULT_LOG_LEVEL", "INFO")

__all__ = [
    "Mode",
    "State",
    "MODE",
    "PIR_PIN",
    "LED_R_PIN",
    "LED_G_PIN",
    "LED_B_PIN",
    "SWITCH_ONE_PIN",
    "SWITCH_TWO_PIN",
    "CONFIRM_BUTTON_PIN",
    "BACK_BUTTON_PIN",
    "JOYSTICK_VRX_PIN",
    "JOYSTICK_VRY_PIN",
    "JOYSTICK_SW_PIN",
    "GUN_PUMP_PIN",
    "GUN_SHOOT_PIN",
    "YAW_SERVO_PIN",
    "PITCH_SERVO_PIN",
    "SERVO_WAIT_TIME",
    "GUN_PUMP_TIME",
    "GUN_SHOOT_TIME",
    "CAMERA_RESOLUTION",
    "CAMERA_FOV_H",
    "CAMERA_FOV_V",
    "CAMERA_CENTER",
    "PROJECT_ROOT",
    "DATA_DIR",
    "MODEL_PATH",
    "DEFAULT_LOG_LEVEL",
]
