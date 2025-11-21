import constants as const
from enum import Enum, auto

class MenuStates(Enum):
    MAIN = auto()
    SETTINGS = auto()
    CALIBRATION = auto()

class Menu():
    def __init__(self):
        self.