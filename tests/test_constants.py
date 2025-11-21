"""Unit tests for the constants module."""
from __future__ import annotations

import importlib
import os
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

const = importlib.import_module("constants")


class ConstantsTestCase(unittest.TestCase):
    """Validate basic assumptions about constants."""

    def test_enum_defaults(self) -> None:
        self.assertEqual(const.MODE, const.Mode.TUNING)
        self.assertTrue(hasattr(const.State, "IDLE"))
        self.assertTrue(hasattr(const.State, "TRACKING"))

    def test_pin_types_are_int(self) -> None:
        pin_names = [
            "PIR_PIN",
            "LED_R_PIN",
            "LED_G_PIN",
            "LED_B_PIN",
            "SWITCH_ONE_PIN",
            "SWITCH_TWO_PIN",
            "BUTTON_ONE_PIN",
            "BUTTON_TWO_PIN",
            "JOYSTICK_VRX_PIN",
            "JOYSTICK_VRY_PIN",
            "JOYSTICK_SW_PIN",
            "GUN_PUMP_PIN",
            "GUN_SHOOT_PIN",
            "YAW_SERVO_PIN",
            "PITCH_SERVO_PIN",
        ]
        for name in pin_names:
            with self.subTest(pin=name):
                value = getattr(const, name)
                self.assertIsInstance(value, int)
                self.assertGreaterEqual(value, 0)

    def test_camera_defaults(self) -> None:
        self.assertIsInstance(const.CAMERA_RESOLUTION, tuple)
        self.assertEqual(len(const.CAMERA_RESOLUTION), 2)
        self.assertTrue(all(isinstance(v, int) for v in const.CAMERA_RESOLUTION))
        self.assertIsInstance(const.DATA_DIR, str)
        self.assertIsInstance(const.MODEL_PATH, str)

    def test_env_override_applies_on_reload(self) -> None:
        original = os.environ.get("PIR_PIN")
        try:
            os.environ["PIR_PIN"] = "21"
            reload_constants()
            self.assertEqual(const.PIR_PIN, 21)
        finally:
            if original is None:
                os.environ.pop("PIR_PIN", None)
            else:
                os.environ["PIR_PIN"] = original
            reload_constants()


def reload_constants() -> None:
    """Reload the constants module so env var overrides take effect."""

    global const  # pylint: disable=global-statement
    const = importlib.reload(const)


if __name__ == "__main__":
    unittest.main()
