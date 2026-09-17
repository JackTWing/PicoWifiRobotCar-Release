# PicoWifiRobotCar

PicoWifiRobotCar lets you drive a CircuitPython robot from a phone browser.
The board creates a WiFi network and serves the dashboard itself. Driving needs
no internet, app, cloud service, or computer.

Robot actions and sensor readings live in `code.py`. Register a Python function
as a command, slider, or telemetry getter, and the dashboard builds its controls
from those registrations. The same server can be used with other hardware.

**First time using a kit? Read [Start Here](START_HERE.md).** This README covers
installation, calibration, the API, and maintenance. Open work and test results
are in [TODO.md](TODO.md); hardware validation is still in progress.

[Calibration](#wheel-calibration) | [Python API](#commands-settings-and-readings) |
[Troubleshooting](#troubleshooting) | [Extending](#extending-the-project)

## Project layout

| File | Responsibility |
| --- | --- |
| [`code.py`](code.py) | Board pins, wheel calibration, robot actions, sensor readings |
| [`lib/wifi_command_server.py`](lib/wifi_command_server.py) | WiFi access point (AP), HTTP, registrations, schema, motion watchdog |
| [`lib/wifi_dashboard_assets.py`](lib/wifi_dashboard_assets.py) | Embedded HTML, CSS, and JavaScript; no frontend build step |
| [`examples/code_minimal.py`](examples/code_minimal.py) | Print-only example; does not control motors |
| [`tests/`](tests/) | Desktop tests with hardware stubs |

The path from a button to a wheel is: browser request -> server route ->
registered handler in `code.py` -> servo output. Telemetry flows back through
`/api/state`. The server knows nothing about the robot's motor pins.

## Installation

Supported boards and signal pins in the supplied `code.py`:

| Board | Left / right signal | System Voltage reading |
| --- | --- | --- |
| [Raspberry Pi Pico 2 W](https://circuitpython.org/board/raspberry_pi_pico2_w/) | `GP13` / `GP12` | VSYS |
| [YD ESP32-S3-N16R8](https://circuitpython.org/board/yd_esp32_s3_n16r8/) | `GPIO13` / `GPIO12` | Not provided |

These are GPIO names, not physical header positions. The current robot uses
FEETECH/Fitec FS90R continuous-rotation servos. Follow the kit's power wiring;
servo power must not come from a GPIO, and servo and board grounds must be common.
See [Adafruit's servo wiring guide](https://learn.adafruit.com/circuitpython-essentials/circuitpython-servo).

1. Back up the board's existing files. Keep motors disconnected during setup.
2. Install CircuitPython using the instructions for the exact board linked above.
   This project does not run on MicroPython or ordinary desktop Python.
3. From the [Adafruit library bundle](https://circuitpython.org/libraries), choose
   the bundle matching your CircuitPython major version and copy `adafruit_motor`
   into the board's `lib` folder.
4. Copy the three project runtime files. The result on `CIRCUITPY` should be:

   ```text
   CIRCUITPY/
     code.py
     lib/
       wifi_command_server.py
       wifi_dashboard_assets.py
       adafruit_motor/            from the library bundle, not this repo
   ```

5. Reconnect hardware with power off, raise the wheels, then fully power-cycle.
   The USB serial terminal prints the network name and dashboard URL.
6. Join `RobotCar-XXXXXX` with password `12345678`, then open
   `http://192.168.4.1:8080/`. Stay on the network if the phone warns of no internet.
   If the printed address differs, use that address.
7. Calibrate Stop before driving. Follow the [first-drive checks](START_HERE.md#3-check-stop-then-drive).

Record the CircuitPython version, bundle version/date, and Git commit for any
test or deployment. A tested release/bundle pair has not yet been pinned; a new
upstream release is not automatically a validated robot build.

## Network settings

Configure the `WifiCommandServer(...)` call in `code.py`. Its choices differ
from the reusable class defaults:

| Option | Class default | Supplied robot | Meaning |
| --- | --- | --- | --- |
| `ssid` | `"RobotCar"` | Same | Network name or prefix; use ASCII |
| `password` | `"12345678"` | Same | WiFi password; use 8-63 ASCII characters |
| `title` | `"WiFi Robot Dashboard"` | `"WiFi Robot Car"` | Page and browser-tab title |
| `port` | `80` | `8080` | HTTP port; avoids a conflict with Web Workflow on port 80 |
| `unique_ssid` | `False` | `True` | Append six hex digits from the AP MAC address |
| `ap_channel` | `1` | `6` | WiFi channel; accepted range 1-11 |
| `command_timeout_ms` | `1200` | Same | Motion inactivity timeout, not a guaranteed stop deadline |
| `poll_timeout_s` | `0.1` | Same | Wait for a client before checking idle work and safety |

Fully power-cycle after changing the network name, password, or channel. On
Pico W-family boards, a soft reload may retain the AP; the server reuses it.
If channel 6 is crowded, try 1 or 11. A connected station-mode network can force
the AP to share its channel; check the startup log and Web Workflow settings.

For classes, label robots with their network names and assign one controlling
phone per robot. Unique names reduce confusion; they are not access control.
The password is public by default. Anyone able to join can send commands:
there is no per-user authentication, HTTPS, or controller ownership. Assign kit
passwords before distribution and do not expose this server to the internet.

## Wheel calibration

Calibrate with wheels raised and power within reach. The current test rig uses
`left_neutral = 0.0`, `right_neutral = 0.01`, and zero movement trim. These are
per-robot settings, not universal FS90R values.

1. Power on, then press **Stop before driving**. Startup has no PWM pulses;
   Stop sends a neutral pulse. Still wheels at startup alone do not confirm
   neutral calibration.
2. If a wheel creeps, change only its `left_neutral` or `right_neutral`. Try small
   steps such as `0.005`; if creep worsens, try the other direction. After each
   save/reload, press Stop again.
3. Check Forward -> Stop, Reverse -> Stop, release, and Emergency Stop. Confirm
   the wheels remain still, then repeat after a power cycle.

The FS90R also has a physical neutral adjustment. Use either that or the code
setting, one at a time. [FS90R adjustment details](https://www.pololu.com/product/2820).

In `_wheel_output`, requests with magnitude below `neutral_deadband` use
`neutral * reverse`. Other requests use `(requested + trim) * reverse`; both
are clamped to `[-1, 1]`. Thus movement trim cannot correct idle drift, and the
right wheel's `reverse = -1.0` also reverses its neutral offset. Nonzero additive
trim affects forward and reverse differently.

Speed scales drive requests and takes effect on the next press; changing the
slider does not re-run a held drive handler.

On Pico 2 W, System Voltage is VSYS, not a battery percentage. It reflects the
active supply, including USB-derived power when connected. The ADC is released
after each reading. The ESP32-S3 example omits this reading.

## Commands, settings, and readings

Add registrations before `server.run()`, which starts the blocking server loop.
For example, these additions to `code.py` need no extra hardware:

```python
@server.command("horn", label="Horn")
def horn():
    print("Beep!")  # Replace with your buzzer action.


@server.telemetry("mode", label="Mode")
def read_mode():
    return "Manual"
```

See [the print-only example](examples/code_minimal.py) for a complete program.
Its stop function only prints; replace it before adding motor control.

| Registration | Callback and options |
| --- | --- |
| `@server.command(id, ...)` | No-argument handler; `label=None`, `motion=False`, `on_release=None` |
| `@server.slider(id, ...)` | Handler receives one numeric value; `min=0`, `max=100`, `default=0`, `step=1`, `label=None`, `motion=False` |
| `@server.telemetry(id, ...)` | No-argument getter; `label=None`; return a JSON-compatible value |
| `server.set_emergency_stop(handler)` | No-argument stop action; use the same action as drive release |
| `server.set_idle_callback(callback)` | Runs when no connection is accepted; not a fixed-rate timer |

Without decorators, use `register_command(id, handler, ...)`,
`register_slider(id, handler, ...)`, or `register_telemetry(id, getter, ...)`
with the same options. `server.stop()` stops active motion before exiting the
loop; it returns `False` if that stop handler fails.

For held driving, register both `motion=True` and `on_release=stop_motion`, then
call `server.set_emergency_stop(stop_motion)`. Startup requires a positive
timeout and either an Emergency Stop handler or a registered `stop` command.

Keep callbacks short. There are no worker threads: a long loop, sleep, sensor
read, or idle callback can delay commands and the watchdog. Return a number,
string, boolean, or `None` for a simple status field. Getter exceptions yield
`None` (`--` on the dashboard); blocking getters and non-serializable values
are not isolated.

Use distinct ASCII IDs within each registry. Duplicate IDs are not rejected
and can produce duplicate controls. Telemetry overwrites a same-named slider
value in `/api/state`; the robot intentionally uses this for `speed`.
Slider values are clamped to min/max, but `step` is only a browser hint.
Registration sets the stored default without calling the handler, so initialize
your robot's setting to the same default.

### Custom Buttons

The dashboard's Add Button creates a temporary shortcut to an existing command
ID, such as `horn`, not a URL such as `/cmd/horn`. It sends a single press, with
no release or keepalives: use it only for non-motion actions. The prompt does
not enforce this restriction. Buttons disappear on reload.

All registered commands already get a default dashboard button. Hidden commands
(`show_control=False`) and persistent custom buttons are not implemented.

## Motion safety

1. A press runs the drive handler once and arms the watchdog.
2. While held, the browser sends keepalives about every 320 ms. Accepted
   keepalives refresh the timeout without re-running the handler.
3. Release calls the release handler and clears active motion. Pointer cancel,
   keyboard focus loss, and page exit/backgrounding also request stops.
4. After 1200 ms without a motion refresh, the server requests Emergency Stop
   at its next watchdog check. Socket waits and callbacks can extend this delay.

Emergency Stop clears active motion, so later keepalives cannot restart it.
It is **not latched**: a new press can drive again. Motion-handler exceptions,
or other command/slider failures during active motion, attempt the same stop.
A failed stop is logged; active motion stays armed for watchdog retries.

This is a software watchdog, not a hardware power cut. It cannot protect against
a blocked interpreter, faulty stop handler, bad wiring, or uncalibrated servo.
Test with raised wheels, provide a reachable power switch, and supervise use.

## Schema and HTTP API

`/api/schema` returns `title`, `controls`, and `telemetry` metadata. Each control
has `type`, `id`, `label`, and type-specific options. Currently supported types
are `button` and `slider`. Only `forward`, `left`, `stop`, `right`, and `reverse`
get special gamepad positions; transport uses the registered IDs generically.

| Method | Endpoint | Result or action |
| --- | --- | --- |
| GET | `/`, `/app.css`, `/app.js` | Embedded dashboard assets |
| GET | `/api/schema` | Registrations and labels |
| GET | `/api/state` | Stored slider values plus telemetry readings |
| GET | `/api/ping` | `ok` and AP `ip` |
| GET | `/api/command?id=forward&event=press` | Command event: `press`, `keepalive`, or `release` |
| GET | `/api/set?id=speed&value=50` | Set a slider |
| GET or POST | `/api/emergency_stop` | Invoke the stop handler |
| POST | `/api/command` | JSON body: `{"id":"forward","event":"press"}` |
| POST | `/api/set` | JSON body: `{"id":"speed","value":50}` |

The dashboard uses GET for controls and POST when leaving the page. Command
events default to `press` if omitted. Failures return `ok: false` and `error`:
400 for malformed input, 404 for unknown IDs/routes, 409 for inactive or mismatched
keepalives, and 500 for handler failures. Successful commands return `ok: true`;
slider responses also include the clamped `value`.

## Troubleshooting

| Symptom | First checks |
| --- | --- |
| No `CIRCUITPY` drive | Use a data cable and the correct board firmware/USB port. On the YD ESP32-S3, use native USB, not the USB-to-serial connector. |
| Missing `adafruit_motor` or incompatible `.mpy` | Check `CIRCUITPY/lib` and that the bundle matches CircuitPython's major version. |
| Network visible, phone won't join | Confirm suffix/password; forget the saved network, fully power-cycle, and rejoin. If persistent, test a different AP channel. |
| WiFi joined, dashboard won't load | Include `http://` and `:8080`. Check the serial log for the printed address or traceback. |
| A wheel creeps after Stop | Follow [neutral calibration](#wheel-calibration); movement trim does not apply at Stop. |
| Custom command returns 404 | Use the exact registered ID. Add Button does not register Python code. |
| Status shows `--` | Check for a `[TELEMETRY]` error or a getter returning `None`. |
| Voltage seems high on USB | VSYS reports the active supply, not an isolated battery measurement. |

For a bug report, include board model, CircuitPython/bundle versions, Git branch
and commit, power source, browser, and steps to reproduce. Capture the startup
log plus the press/stop or failure sequence; omit passwords. `ROBOT_DEBUG` in
`code.py` controls wheel logs; `DEBUG_LOG` in the server module controls HTTP and
safety logs. Both are currently enabled.

## Extending the project

- **New action or reading:** register it in `code.py`; leave server routes alone.
- **Different robot hardware:** change pin selection, motor functions, calibration,
  and sensor getters in `code.py`. Start with the print-only example if needed.
- **New control type:** add its registration/schema in `wifi_command_server.py`
  and renderer in `wifi_dashboard_assets.py`'s `controlRenderers`. Reuse transport
  only if its semantics fit. The current frontend has no held-slider keepalive;
  don't assume a joystick or other motion input is safe just because it renders.
- **Transport fix:** keep board-specific WiFi/socket workarounds in the server.
  Do not reintroduce `stations_ap` polling without Pico hardware tests; it caused
  radio timeouts in earlier testing.

Keep the three-file deployment and decorator API small. Add tests with each
behavior change; avoid a new module or framework unless it solves a concrete need.

## Tests

From the repository root, using desktop Python and no extra test packages:

```shell
python -m unittest discover -s tests -v
```

Tests cover registration, schema, routing, parsing, slider clamping, telemetry
exceptions, motion state, and selected socket cases. Dashboard checks inspect
asset text; they do not simulate a browser. Neither suite measures servo pulses
or proves hardware safety.

Before a release, repeat held-drive, release, Emergency Stop during motion,
disconnect/watchdog, page-hide, neutral, and WiFi recovery checks on both boards.
Record physical results separately from desktop tests in [TODO.md](TODO.md).

## License

See [`LICENSE`](LICENSE).
