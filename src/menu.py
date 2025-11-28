from tokenize import String
import constants as const
from enum import Enum, auto
from constants import Mode 

class MenuStates(Enum):
    MAIN = auto()
    MODE = auto()
    SETTINGS = auto()
    CALIBRATION = auto()

class InputActions(Enum):
    NONE = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    CONFIRM = auto()
    BACK = auto()

'''
">" = hovered selection

Menu layout

Main Menu:
1/3 Mode
2/3 Settings
3/3 Calibration

Modes:
Tuning
Default
Picture
Turret
Picture & Fire

Settings:

'''
class mainMenuOptions(Enum):
    MODE = 0
    SETTINGS = 1
    CALIBRATION = 2

class modeMenuOptions(Enum):
    TUNING = 0
    DEFAULT = 1
    PICTURE = 2
    TURRET = 3
    PICTURE_FIRE = 4


class Menu():
    def __init__(self):
        self.state = MenuStates.MAIN
        self.line = 0
        self.message = ["",""]
        self.prevMenu = None
        self.mode = const.Mode.DEFAULT
    
    def update(self, action: InputActions):
        match self.state:
            case MenuStates.MAIN:
                if action == InputActions.CONFIRM:
                    self.prevMenu = MenuStates.MAIN
                    self.line = 0
                    if self.line == 0:
                        self.state = MenuStates.MODE
                    elif self.line == 1:
                        self.state = MenuStates.SETTINGS
                    elif self.line == 2:
                        self.state = MenuStates.CALIBRATION
                elif action == InputActions.BACK and self.prevMenu != None:
                    self.state = self.prevMenu
                elif action == InputActions.UP and self.line > 0:
                    self.line -= 1
                elif action == InputActions.DOWN and self.line < len(mainMenuOptions) - 1:
                    self.line += 1
                if self.line == 0:
                    self.message[0] = "Main Menu"
                    self.message[1] = "> 1/3  Mode"
                elif self.line == 1:
                    self.message[0] = "Main Menu"
                    self.message[1] = "> 2/3 Settings"
                elif self.line == 2:
                    self.message[0] = "Main Menu"
                    self.message[1] = "> 3/3  Calibration"
            case MenuStates.MODE:
                if action == InputActions.CONFIRM:
                    if self.line == 0:
                        self.mode = const.Mode.TUNING
                    elif self.line == 1:
                        self.mode = const.Mode.DEFAULT
                    elif self.line == 2:
                        self.mode = const.Mode.PICTURE
                    elif self.line == 3:
                        self.mode = const.Mode.TURRET
                    elif self.line == 4:
                        self.mode = const.Mode.PICTURE_FIRE
                elif action == InputActions.BACK:
                    self.state = MenuStates.MAIN
                    self.line = 0
                elif action == InputActions.UP and self.line > 0:
                    self.line -= 1
                elif action == InputActions.DOWN and self.line < len(modeMenuOptions) - 1:
                    self.line += 1
                if self.line == 0:
                    self.message[0] = "Select Mode"
                    self.message[1] = "> Tuning"
                elif self.line == 1:
                    self.message[0] = "Select Mode"
                    self.message[1] = "> Default"
                elif self.line == 2:
                    self.message[0] = "Select Mode"
                    self.message[1] = "> Picture"
                elif self.line == 3:
                    self.message[0] = "Select Mode"
                    self.message[1] = "> Turret"
                elif self.line == 4:
                    self.message[0] = "Select Mode"
                    self.message[1] = "> Picture & Fire"
            case MenuStates.SETTINGS:
                # To be implemented
                self.message[0] = "Settings"
                self.message[1] = "To be implemented"
                if action == InputActions.BACK:
                    self.state = MenuStates.MAIN
                    self.line = 0
            case MenuStates.CALIBRATION:
                # To be implemented
                self.message[0] = "Calibration"
                self.message[1] = "To be implemented"
                if action == InputActions.BACK:
                    self.state = MenuStates.MAIN
                    self.line = 0
    def getMessage(self) -> list[str]:
        return self.message
    
    def getMode(self) -> Mode:
        return self.mode