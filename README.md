# animaltrackr
Code/CAD repository for a primarily 3d-printed turret capable of tracking and identifying passing wildlife. Also has a watergun feature for anti bird/cat poop feature.

## Configuration

`src/constants.py` exposes sane defaults for Raspberry Pi Zero builds, but every value can be overridden using environment variables at launch time. Set the variables before starting the service or include them in your systemd unit.

Common overrides:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PIR_PIN` | 7 | GPIO.BOARD pin wired to the PIR sensor |
| `LED_R_PIN`, `LED_G_PIN`, `LED_B_PIN` | 15/16/18 | RGB LED channels |
| `YAW_SERVO_PIN`, `PITCH_SERVO_PIN` | 11/13 | Pan/tilt servo channels |
| `SERVO_WAIT_TIME` | 0.5 | Seconds to wait after commanding a servo |
| `DATA_DIR` | `<repo>/data` | Directory used for captured media |
| `MODEL_PATH` | `<repo>/models/model.tflite` | TensorFlow Lite model used by the inference engine |
| `DEFAULT_LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, etc.) |

Example (Bash):

```bash
export PIR_PIN=18
export DEFAULT_LOG_LEVEL=DEBUG
python -m animaltrackr.src.main
```

In `systemd/animaltrackr.service` you can add `Environment=KEY=value` lines or point to an environment file via `EnvironmentFile=/etc/animaltrackr.env` to keep overrides in one place.

## Raspberry Pi Zero Setup

These steps assume Raspberry Pi OS (Bookworm or Bullseye) with camera and I2C interfaces enabled via `raspi-config`.

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip libatlas-base-dev git python3-picamera2 i2c-tools

cd /home/pi
git clone https://github.com/apinguen/animaltrackr.git
cd animaltrackr
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install opencv-python-headless tflite-runtime gpiozero adafruit-circuitpython-servokit picamera2

# sanity check (optional)
python src/main.py --help 2>/dev/null || true
```

- Use `i2cdetect -y 1` to ensure the PCA9685 / I2C peripherals are visible.
- Run `libcamera-still -n -o test.jpg` (or `picamera2` demo) once to confirm camera access.
- For faster inference consider swapping in a Coral USB Accelerator and the Edge TPU runtime.

## Systemd Service

1. Copy the provided unit file to `/etc/systemd/system/`:
	```bash
	sudo cp systemd/animaltrackr.service /etc/systemd/system/
	```
2. (Optional) create `/etc/animaltrackr.env` with overrides such as `DEFAULT_LOG_LEVEL=DEBUG`.
3. Reload systemd and enable auto-start:
	```bash
	sudo systemctl daemon-reload
	sudo systemctl enable animaltrackr
	sudo systemctl start animaltrackr
	```
4. Tail logs with `journalctl -u animaltrackr -f`.

Edit the `WorkingDirectory`, `ExecStart`, and `User` fields inside `systemd/animaltrackr.service` if your install path differs from `/home/pi/animaltrackr`.

## Diagnostics / Test Modes

Use the LCD + joystick/buttons to navigate to **Calibration → Diagnostics**. Each entry maps to a runtime mode that exercises hardware:

- **LED Test** cycles RGB combinations so you can confirm wiring.
- **Servo Test** sweeps yaw and pitch continuously.
- **Pump Test** fires the pump/valve every 10 seconds (have water ready!).
- **Sensor Test** lights the LED based on PIR/back/confirm inputs and logs joystick readings.
- **Camera Test** captures periodic stills into `data/` and logs the file path.

Switch back to any other mode via the menu once you are done validating a component.
