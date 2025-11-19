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

# Hardware pins (GPIO numbering)
PIR_PIN: int = 
LED_R_PIN: int = 
LED_G_PIN: int =
LED_B_PIN: int =

SWITCH_ONE_PIN: int = 
SWITCH_TWO_PIN: int = 

BUTTON_ONE_PIN: int = 
BUTTON_TWO_PIN: int = 

JOYSTICK_VRX_PIN: int = 
JOYSTICK_VRY_PIN: int = 
JOYSTICK_SW_PIN: int = 

LCD_D4_PIN: int = 
LCD_D5_PIN: int = 
LCD_D6_PIN: int = 
LCD_D7_PIN: int = 
LCD_E_PIN: int = 
LCD_RS_PIN: int = 

GUN_PUMP_PIN: int = 
GUN_SHOOT_PIN: int = 

# Reminder for me brain: Side to side
YAW_SERVO_PIN: int =
# Reminder for me brain: Up and down
PITCH_SERVO_PIN: int =

# Timing
servoWaitTime: float = 0.5  # seconds to wait for servo to reach position

# Camera defaults
DEFAULT_CAMERA_RESOLUTION: Tuple[int, int] = (1280, 720)

# Paths (derived from repository layout)
PROJECT_ROOT: str = os.path.dirname(os.path.dirname(__file__))
DATA_DIR: str = os.path.join(PROJECT_ROOT, "data")
MODEL_PATH: str = os.path.join(PROJECT_ROOT, "models", "model.tflite")

# Logging / operation
DEFAULT_LOG_LEVEL: str = "INFO"

__all__ = [

]
