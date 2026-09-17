# Start Here: Your First Drive

PicoWifiRobotCar turns any smartphone, tablet, or computer into a robot remote controller. The robot makes its own WiFi
network - just join it and open the controls in a browser. No app, account, or
internet connection is needed to drive.

This guide is for an assembled robot with a Raspberry Pi Pico 2 W or
YD ESP32-S3-N16R8. Always follow your kit's wiring and power instructions first.

## 1. Get the robot ready

If your kit already has the software installed, skip to step 2.

Otherwise, use a computer and a USB data cable for this one-time setup:

1. Install CircuitPython on the board:
   [Pico 2 W](https://circuitpython.org/board/raspberry_pi_pico2_w/) or
   [YD ESP32-S3-N16R8](https://circuitpython.org/board/yd_esp32_s3_n16r8/).
   Follow the instructions on that board's download page.
2. Open the board's `CIRCUITPY` drive. Back up any existing program before
   replacing it.
3. Copy this project's `code.py` onto the drive. Copy `wifi_command_server.py`
   and `wifi_dashboard_assets.py` from the project's `lib` folder into the
   drive's `lib` folder.
4. Download the [Adafruit library bundle](https://circuitpython.org/libraries)
   matching your CircuitPython version (for example, 10.x with 10.x). Copy its
   `adafruit_motor` folder into `CIRCUITPY/lib` too.

The [README setup section](readme.md#installation) shows the finished file layout.

## 2. Connect your phone

Keep the wheels raised for the first test, with power easy to disconnect.

1. Power on the robot.
2. In your phone's WiFi settings, join `RobotCar-XXXXXX`. Each board has its own
   suffix. Your kit may use a different name or password.
3. Enter the default password: `12345678`.
4. If your phone warns that this network has **no internet**, stay connected - this is OK!
5. Open **[http://192.168.4.1:8080/](http://192.168.4.1:8080/)** in your browser.
   Include `http://` and `:8080`; don't enter it as a web search.

For multi-robot activities, label each robot with its network name and use one controlling
phone per robot. The network name and dashboard address also appear in the
board's USB serial terminal.

## 3. Check Stop, then drive

Press **Stop** before any directional key. Both wheels should stay still. If one
creeps, pause here and follow [wheel calibration](readme.md#wheel-calibration).

Set Speed low (50%), then hold **Forward** briefly. Release it: both wheels should
stop. Try Reverse, Left, and Right. Speed changes apply to the next drive press.
With the wheels still raised, check **Emergency Stop** during a held direction.

Once these checks pass, put the robot on a clear floor and try short movements.
Keep it away from table edges, stairs, fingers, and pets. Supervise young drivers.

Emergency Stop is a software control, not a power switch. It does not lock out
later drive commands. If the robot does not stop, disconnect its power.

## If something isn't right

- **Can't join WiFi:** confirm the robot's network name, forget that saved
  network on the phone, fully power-cycle the robot, and rejoin.
- **Connected, but no controls:** check the full address above and reload.
- **A wheel creeps after Stop:** adjust neutral (resting) trim.
- **System Voltage is missing on ESP32-S3:** expected - the ESP32 has no onboard
  voltage sensor for the software to read.

More help: [troubleshooting](readme.md#troubleshooting).

## Make it yours

Robot actions can be written or modified in `code.py`. Start by changing a button label, then try a
new action or sensor reading. [Adding controls](readme.md#commands-settings-and-readings)
shows how! Custom Buttons on the phone are shortcuts to actions created in the
robot's code - they do not create new Python functions by themselves.
