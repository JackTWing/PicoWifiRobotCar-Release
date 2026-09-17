"""FS90R robot controls for Pico 2 W and YD ESP32-S3-N16R8.

Edit hardware, calibration, and actions here. WiFi and dashboard code lives in lib/.
See START_HERE.md for setup and readme.md for calibration and API details.
"""
import analogio
import board
import pwmio
from adafruit_motor import servo

from wifi_command_server import WifiCommandServer


# Hardware and calibration
def _board_pin(*names):
    """Return the first pin name exposed by the current board definition."""
    for name in names:
        pin = getattr(board, name, None)
        if pin is not None:
            return pin
    raise RuntimeError("Board does not provide any of these pins: " + ", ".join(names))


# GPIO names, not physical header positions. Pin aliases differ by board.
left_motor_pin = _board_pin("GP13", "GPIO13")
right_motor_pin = _board_pin("GP12", "GPIO12")

# PWM starts with no pulses. Stop below sends a calibrated neutral pulse instead.
pwm_left = pwmio.PWMOut(left_motor_pin, frequency=50)
pwm_right = pwmio.PWMOut(right_motor_pin, frequency=50)
left_servo = servo.ContinuousServo(pwm_left)
right_servo = servo.ContinuousServo(pwm_right)

# Pico VSYS is the active supply, not necessarily the battery when USB is attached.
# The YD ESP32-S3 has no equivalent onboard monitor.
voltage_monitor_pin = getattr(board, "VOLTAGE_MONITOR", None)

# Tune each wheel while Stop is commanded; these values are specific to this rig.
left_neutral = 0.0
right_neutral = 0.01  # Stops the tested right FS90R's idle creep.
# Movement-only offsets; changing these will not fix drift at Stop.
left_trim = 0
right_trim = 0
neutral_deadband = 0.05  # Requests below this magnitude use the neutral setting.
# Reverse both movement and neutral offsets to match each wheel's orientation.
right_reverse = -1.0
left_reverse = 1.0

speed_percent = 50
ROBOT_DEBUG = True


def robot_log(*parts):
    if ROBOT_DEBUG:
        print("[Robot]", *parts)


def _scale(value):
    return max(-1.0, min(1.0, value * (speed_percent / 100.0)))


def _wheel_output(requested, neutral, trim, reverse):
    """Apply neutral or movement trim, then reversal and output limits."""
    if abs(requested) < neutral_deadband:
        return max(-1.0, min(1.0, neutral * reverse))
    return max(-1.0, min(1.0, (requested + trim) * reverse))


def set_wheels(left, right):
    left_servo_throttle = _wheel_output(left, left_neutral, left_trim, left_reverse)
    right_servo_throttle = _wheel_output(right, right_neutral, right_trim, right_reverse)
    robot_log(
        "WHEEL OUTPUT",
        "requested=({:.3f},{:.3f})".format(left, right),
        "final=({:.3f},{:.3f})".format(left_servo_throttle, right_servo_throttle),
    )
    left_servo.throttle = left_servo_throttle
    right_servo.throttle = right_servo_throttle


def stop_motion():
    """Shared stop action for release, Stop, Emergency Stop, and the watchdog."""
    robot_log(
        "STOP -> NEUTRAL",
        "left={:.3f}".format(max(-1.0, min(1.0, left_neutral * left_reverse))),
        "right={:.3f}".format(max(-1.0, min(1.0, right_neutral * right_reverse))),
    )
    set_wheels(0.0, 0.0)


def forward():
    robot_log("COMMAND forward")
    set_wheels(_scale(-1.0), _scale(-1.0))


def reverse():
    robot_log("COMMAND reverse")
    set_wheels(_scale(1.0), _scale(1.0))


def left():
    robot_log("COMMAND left")
    set_wheels(_scale(-0.5), _scale(0.5))


def right():
    robot_log("COMMAND right")
    set_wheels(_scale(0.5), _scale(-0.5))


def set_speed(percent):
    global speed_percent
    speed_percent = int(max(0, min(100, percent)))
    robot_log("SPEED", speed_percent, "percent")


def read_sys_voltage():
    if voltage_monitor_pin is None:
        return None

    # Pico W voltage sensing shares hardware with WiFi; release the ADC promptly.
    vsys_input = analogio.AnalogIn(voltage_monitor_pin)
    try:
        adc_reading = vsys_input.value
        adc_voltage = (adc_reading * vsys_input.reference_voltage) / 65535
    finally:
        vsys_input.deinit()

    # Undo Pico's 1/3 voltage divider.
    vsys_voltage = adc_voltage * 3
    return round(vsys_voltage, 1)


# Dashboard settings and actions (register before server.run())
server = WifiCommandServer(
    ssid="RobotCar",
    password="12345678",
    title="WiFi Robot Car",
    # Avoid port 80, which CircuitPython Web Workflow may use.
    port=8080,
    command_timeout_ms=1200,
    # Add a board-specific suffix, e.g. RobotCar-A1B2C3.
    unique_ssid=True,
    # Try 1 or 11 if congested. Fully power-cycle after changing AP settings.
    ap_channel=6,
)


@server.command("forward", label="Forward", motion=True, on_release=stop_motion)
def _cmd_forward():
    forward()


@server.command("reverse", label="Reverse", motion=True, on_release=stop_motion)
def _cmd_reverse():
    reverse()


@server.command("left", label="Left", motion=True, on_release=stop_motion)
def _cmd_left():
    left()


@server.command("right", label="Right", motion=True, on_release=stop_motion)
def _cmd_right():
    right()


@server.command("stop", label="Stop")
def _cmd_stop():
    stop_motion()


@server.slider("speed", min=0, max=100, default=50, label="Speed", step=1)
def _slider_speed(value):
    set_speed(value)


if voltage_monitor_pin is not None:
    server.register_telemetry(
        "battery",
        read_sys_voltage,
        label="System Voltage (V)",
    )


@server.telemetry("speed", label="Speed (%)")
def _tm_speed():
    return speed_percent


server.set_emergency_stop(stop_motion)

robot_log("=== WIFI ROBOT CAR DEBUG ENABLED ===")
robot_log("Board:", board.board_id)
robot_log("Motor commands are sent on pin 13/pin 12.")
robot_log(
    "LEFT calibration",
    "neutral=", left_neutral,
    "trim=", left_trim,
    "reverse=", left_reverse,
)
robot_log(
    "RIGHT calibration",
    "neutral=", right_neutral,
    "trim=", right_trim,
    "reverse=", right_reverse,
)
robot_log("Neutral deadband=", neutral_deadband, "initial speed=", speed_percent)
robot_log("Starting WiFi dashboard server...")
server.run()
