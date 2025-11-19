import time, cv2, os, atexit
import RPi.GPIO as GPIO
import constants as const
from time import sleep

class Hardware:
    
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        self._setup_outputs()
        self._start_pwm()
        atexit.register(self.cleanup)

    # Helpers
    def _setup_outputs(self):
        GPIO.setup(const.YAW_SERVO_PIN, GPIO.OUT)
        GPIO.setup(const.PITCH_SERVO_PIN, GPIO.OUT)
        GPIO.setup(const.LED_R_PIN, GPIO.OUT)
        GPIO.setup(const.LED_G_PIN, GPIO.OUT)
        GPIO.setup(const.LED_B_PIN, GPIO.OUT)
    
    def _start_pwm(self):
        self.pwmYaw = GPIO.PWM(const.YAW_SERVO_PIN,50)
        self.pwmPitch = GPIO.PWM(const.PITCH_SERVO_PIN,50)
        self.pwmYaw.start(0)
        self.pwmPitch.start(0)


    # public methods

    def setYaw(self,angle):
        duty = angle / 18 + 2
        GPIO.output(const.YAW_SERVO_PIN, True)
        self.pwmYaw.ChangeDutyCycle(duty)
        sleep(const.servoWaitTime)
        GPIO.output(const.YAW_SERVO_PIN, False)
        self.pwmYaw.ChangeDutyCycle(duty)

    def setPitch(self,angle):
        duty = angle / 18 + 2
        GPIO.output(const.PITCH_SERVO_PIN, True)
        self.pwmPitch.ChangeDutyCycle(duty)
        sleep(const.servoWaitTime)
        GPIO.output(const.PITCH_SERVO_PIN, False)
        self.pwmPitch.ChangeDutyCycle(duty)

    def setLEDColor(self,r, g, b):
        GPIO.output(const.LED_R_PIN, r)
        GPIO.output(const.LED_G_PIN, g)
        GPIO.output(const.LED_B_PIN, b)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def cleanup(self):
        self.pwmYaw.stop()
        self.pwmPitch.stop()
        GPIO.cleanup()