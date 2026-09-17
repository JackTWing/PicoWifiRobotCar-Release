"""CircuitPython WiFi AP, HTTP routes, and a dashboard built from registrations."""

import json
import time
import wifi
import socketpool

from wifi_dashboard_assets import HTML, CSS, JS

DEBUG_LOG = True  # Includes routine HTTP traffic; disable for quieter serial output.
SEND_CHUNK_BYTES = 1024
SEND_RETRY_DELAY_S = 0.01
SEND_STALL_TIMEOUT_S = 2.0
WOULD_BLOCK_ERRNOS = (11, 35, 10035)


class WifiCommandServer:
    """Register actions and readings, then serve them with run()."""

    def __init__(
        self,
        ssid="RobotCar",
        password="12345678",
        title="WiFi Robot Dashboard",
        port=80,
        command_timeout_ms=1200,
        poll_timeout_s=0.1,
        unique_ssid=False,
        ap_channel=1,
    ):
        self.ssid = ssid
        self.password = password
        self.title = title
        self.port = int(port)
        self.command_timeout_ms = command_timeout_ms
        self.poll_timeout_s = poll_timeout_s
        self.unique_ssid = bool(unique_ssid)
        self.ap_channel = int(ap_channel)
        if self.ap_channel < 1 or self.ap_channel > 11:
            raise ValueError("ap_channel must be between 1 and 11")

        self._commands = {}
        self._sliders = {}
        self._telemetry = {}
        self._controls = []
        self._telemetry_meta = []
        self._state = {}

        self._running = True
        self._ap_ip = None
        self._ap_ssid = None
        self._last_motion_ms = self._now_ms()
        self._movement_active = False
        self._active_motion_command = None
        self._emergency_handler = None
        self._idle_callback = None

    def _now_ms(self):
        return int(time.monotonic() * 1000)

    def _log(self, *parts):
        if DEBUG_LOG:
            print("[WifiCommandServer]", *parts)

    # Registration
    def command(self, command_id, label=None, motion=False, on_release=None):
        """Decorate a no-argument action; on_release makes its button holdable."""
        def decorator(func):
            self.register_command(
                command_id,
                func,
                label=label,
                motion=motion,
                on_release=on_release,
            )
            return func

        return decorator

    def register_command(self, command_id, handler, label=None, motion=False, on_release=None):
        """Register an action and its dashboard button without a decorator."""
        self._commands[command_id] = {
            "handler": handler,
            "motion": bool(motion),
            "on_release": on_release,
        }
        self._controls.append(
            {
                "type": "button",
                "id": command_id,
                "label": label or command_id,
                "on_release": bool(on_release),
                "motion": bool(motion),
            }
        )

    def slider(self, slider_id, min=0, max=100, default=0, label=None, step=1, motion=False):
        """Decorate a numeric setter. Registration does not call it with default."""
        def decorator(func):
            self.register_slider(
                slider_id,
                func,
                min=min,
                max=max,
                default=default,
                label=label,
                step=step,
                motion=motion,
            )
            return func

        return decorator

    def register_slider(
        self, slider_id, handler, min=0, max=100, default=0, label=None,
        step=1, motion=False,
    ):
        """Register a setter and slider; step constrains the browser, not the server."""
        self._sliders[slider_id] = {
            "handler": handler,
            "min": min,
            "max": max,
            "default": default,
            "step": step,
            "motion": bool(motion),
        }
        self._state[slider_id] = default
        self._controls.append(
            {
                "type": "slider",
                "id": slider_id,
                "label": label or slider_id,
                "min": min,
                "max": max,
                "default": default,
                "step": step,
                "motion": bool(motion),
            }
        )

    def telemetry(self, telemetry_id, label=None):
        """Decorate a quick, no-argument getter for a JSON-compatible status value."""
        def decorator(func):
            self.register_telemetry(telemetry_id, func, label=label)
            return func

        return decorator

    def register_telemetry(self, telemetry_id, getter, label=None):
        """Register a status getter without a decorator."""
        self._telemetry[telemetry_id] = getter
        self._telemetry_meta.append({"id": telemetry_id, "label": label or telemetry_id})

    def set_emergency_stop(self, handler):
        """Set the no-argument stop action used by Emergency Stop and the watchdog."""
        self._emergency_handler = handler

    def set_idle_callback(self, callback):
        """Set a short callback for accept timeouts; it has no guaranteed cadence."""
        self._idle_callback = callback

    # WiFi and HTTP transport
    def _format_mac(self, value, separator=""):
        try:
            return separator.join("%02X" % octet for octet in value)
        except Exception:
            return ""

    def _resolve_ap_ssid(self):
        if not self.unique_ssid:
            return self.ssid

        mac = getattr(wifi.radio, "mac_address_ap", None)
        if not mac:
            mac = getattr(wifi.radio, "mac_address", None)
        suffix = self._format_mac(mac[-3:] if mac else None)
        if not suffix:
            self._log("Could not read AP MAC; using unsuffixed SSID")
            return self.ssid

        # With an ASCII prefix, 25 + "-" + 6 hex digits fits the 32-byte SSID limit.
        prefix = str(self.ssid)[:25]
        return prefix + "-" + suffix

    def start_ap(self):
        """Start or reuse the AP and return its IPv4 address as a string."""
        self._ap_ssid = self._resolve_ap_ssid()
        self._log("AP MAC:", self._format_mac(getattr(wifi.radio, "mac_address_ap", None), ":"))
        if getattr(wifi.radio, "connected", False):
            self._log("Station mode is also connected; AP will share its WiFi channel")

        if getattr(wifi.radio, "ap_active", False):
            # Pico W AP state can survive soft reloads. Restarting it can fail
            # until a hardware reset, so leave an active AP alone.
            self._log("AP already active after reload; reusing existing radio state")
            self._log("Power-cycle to apply a changed SSID or AP channel")
        else:
            self._log("Starting AP:", self._ap_ssid, "channel=", self.ap_channel)
            wifi.radio.start_ap(
                self._ap_ssid,
                self.password,
                channel=self.ap_channel,
            )
        while wifi.radio.ipv4_address_ap is None:
            time.sleep(0.2)
        self._ap_ip = str(wifi.radio.ipv4_address_ap)
        self._log("AP ready at", self._ap_ip)
        return self._ap_ip

    def _start_socket(self):
        pool = socketpool.SocketPool(wifi.radio)
        server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        server.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(2)
        server.settimeout(self.poll_timeout_s)
        self._log(
            "HTTP server listening:",
            "http://%s:%d/" % (self._ap_ip, self.port),
        )
        return server

    def _decode_component(self, value):
        value = (value or "").replace("+", " ")
        out = ""
        i = 0
        while i < len(value):
            ch = value[i]
            if ch == "%" and i + 2 < len(value):
                try:
                    out += chr(int(value[i + 1 : i + 3], 16))
                    i += 3
                    continue
                except Exception:
                    pass
            out += ch
            i += 1
        return out

    def _parse_query(self, query):
        parsed = {}
        if not query:
            return parsed
        for part in query.split("&"):
            if not part:
                continue
            if "=" in part:
                key, value = part.split("=", 1)
            else:
                key, value = part, ""
            parsed[self._decode_component(key)] = self._decode_component(value)
        return parsed

    def _json_response(self, conn, payload, status_code=200):
        self._log("Sending JSON response", status_code, payload)
        body = json.dumps(payload)
        self._send_response(conn, body, status_code=status_code, content_type="application/json")

    def _send_response(self, conn, body, status_code=200, content_type="text/plain"):
        reasons = {
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            405: "Method Not Allowed",
            409: "Conflict",
            500: "Server Error",
        }
        reason = reasons.get(status_code, "OK")
        if not isinstance(body, str):
            body = str(body)
        body_data = body.encode("utf-8")
        response_head = (
            "HTTP/1.1 %d %s\r\n" % (status_code, reason)
            + "Content-Type: %s\r\n" % content_type
            + "Connection: close\r\n"
            + "Content-Length: %d\r\n\r\n" % len(body_data)
        )
        data = response_head.encode("utf-8") + body_data
        self._log("Sending response", status_code, content_type, "bytes=", len(data))
        sent = 0
        last_progress = time.monotonic()
        while sent < len(data):
            end = min(sent + SEND_CHUNK_BYTES, len(data))
            try:
                count = conn.send(data[sent:end])
            except OSError as exc:
                errno = getattr(exc, "errno", None)
                if errno is None and exc.args:
                    errno = exc.args[0]
                stalled = time.monotonic() - last_progress >= SEND_STALL_TIMEOUT_S
                if errno not in WOULD_BLOCK_ERRNOS or stalled:
                    raise

                # ESP32-S3 asset sends can fill the socket buffer. Wait briefly
                # for space, checking the watchdog between retries.
                self._check_timeout()
                time.sleep(SEND_RETRY_DELAY_S)
                continue

            if not count:
                raise OSError("socket send failed")
            sent += count
            last_progress = time.monotonic()
            # Successful chunks can also be slow; check even after the last one.
            self._check_timeout()

    def _parse_request(self, raw):
        request = raw.decode("utf-8")
        lines = request.split("\r\n")
        request_line = lines[0]
        parts = request_line.split(" ")
        if len(parts) < 2:
            return None

        method = parts[0].upper()
        target = parts[1]
        path, query = target, ""
        if "?" in target:
            path, query = target.split("?", 1)
        headers = {}
        for line in lines[1:]:
            if not line:
                break
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
        body = ""
        sep = request.find("\r\n\r\n")
        if sep != -1:
            body = request[sep + 4 :]

        parsed = {
            "method": method,
            "path": path,
            "query": self._parse_query(query),
            "body": body,
            "headers": headers,
        }
        self._log("Parsed request", parsed["method"], parsed["path"], parsed["query"])
        return parsed

    def _socket_recv(self, conn, max_bytes):
        if hasattr(conn, "recv"):
            return conn.recv(max_bytes)
        if hasattr(conn, "recv_into"):
            buf = bytearray(max_bytes)
            count = conn.recv_into(buf)
            if not count:
                return b""
            return bytes(buf[:count])
        raise RuntimeError("socket object has no recv/recv_into")

    def _read_request_bytes(self, conn, max_bytes=4096):
        """Read an HTTP request, including body bytes up to max_bytes."""
        data = b""
        while len(data) < max_bytes:
            try:
                chunk = self._socket_recv(conn, min(512, max_bytes - len(data)))
            except OSError as exc:
                errno = getattr(exc, "errno", None)
                if errno is None and exc.args:
                    errno = exc.args[0]
                # Browsers may pre-open connections without sending a request.
                # An idle receive timeout is not an HTTP 500.
                if errno in WOULD_BLOCK_ERRNOS or errno in (110, 116):
                    break
                raise
            if not chunk:
                break
            data += chunk

            head_end = data.find(b"\r\n\r\n")
            if head_end == -1:
                continue

            header_blob = data[:head_end].decode("utf-8", "ignore")
            content_length = 0
            for line in header_blob.split("\r\n")[1:]:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                if key.strip().lower() == "content-length":
                    try:
                        content_length = int(value.strip())
                    except Exception:
                        content_length = 0
                    break

            total_needed = head_end + 4 + max(0, content_length)
            if len(data) >= total_needed:
                self._log("Request bytes read:", len(data), "content_length=", content_length)
                return data[:total_needed]

        self._log("Request bytes read (partial/end):", len(data))
        return data

    # Schema and current readings
    def _build_schema(self):
        return {
            "title": self.title,
            "controls": self._controls,
            "telemetry": self._telemetry_meta,
        }

    def _build_state(self):
        state = {}
        for key in self._state:
            state[key] = self._state[key]

        for telemetry_id, getter in self._telemetry.items():
            try:
                state[telemetry_id] = getter()
            except Exception as exc:
                self._log("[TELEMETRY]", telemetry_id, "failed ->", exc)
                state[telemetry_id] = None
        return state

    # Command dispatch and motion state
    def _touch_motion(self, command_id=None, event="press"):
        self._movement_active = True
        self._active_motion_command = command_id
        self._last_motion_ms = self._now_ms()
        self._log(
            "[MOTION] ACTIVE",
            "event=", event,
            "command=", command_id,
            "at_ms=", self._last_motion_ms,
            "timeout_ms=", self.command_timeout_ms,
        )

    def _mark_safe(self, reason="stop"):
        """Clear motion state after a stop handler succeeds; does not touch motors."""
        previous_command = self._active_motion_command
        was_active = self._movement_active
        self._movement_active = False
        self._active_motion_command = None
        self._last_motion_ms = self._now_ms()
        self._log(
            "[MOTION] SAFE",
            "reason=", reason,
            "was_active=", was_active,
            "previous_command=", previous_command,
            "at_ms=", self._last_motion_ms,
        )

    def _stop_after_handler_error(self):
        """Best-effort stop after a handler may have changed motor output."""
        status, _out = self._handle_emergency_stop(reason="handler_error")
        if status != 200:
            # Keep the watchdog armed so it retries the stop on the next check.
            self._movement_active = True

    def _apply_command(self, command_id, event="press"):
        self._log("Applying command", "id=", command_id, "event=", event)
        if not isinstance(command_id, str) or not command_id:
            self._log("Command rejected: bad command id")
            return 400, {"ok": False, "error": "bad command id"}

        meta = self._commands.get(command_id)
        if meta is None:
            self._log("Command rejected: unknown command", command_id)
            return 404, {"ok": False, "error": "unknown command"}

        if event not in ("press", "keepalive", "release"):
            self._log("Command rejected: bad event", event)
            return 400, {"ok": False, "error": "bad event"}

        if event == "keepalive":
            # A refresh cannot start motion or repeat the drive handler.
            if (
                not meta["motion"]
                or not self._movement_active
                or self._active_motion_command != command_id
            ):
                self._log("Keepalive rejected: motion is not active", command_id)
                return 409, {"ok": False, "error": "motion not active"}
            self._touch_motion(command_id, event="keepalive")
            return 200, {"ok": True}

        if event == "release" and meta["on_release"] is None:
            self._log("Command rejected: release is not supported", command_id)
            return 400, {"ok": False, "error": "release not supported"}

        try:
            if event == "release":
                meta["on_release"]()
            else:
                meta["handler"]()

            if meta["motion"]:
                if event == "release":
                    self._mark_safe(reason="release:%s" % command_id)
                else:
                    self._touch_motion(command_id, event="press")
            if command_id in ("stop", "emergency_stop"):
                self._mark_safe(reason="command:%s" % command_id)
            self._log("Command applied", command_id, event)
            return 200, {"ok": True}
        except Exception as exc:
            self._log("Command error", command_id, "->", exc)
            if meta["motion"] or self._movement_active or command_id in ("stop", "emergency_stop"):
                self._stop_after_handler_error()
            return 500, {"ok": False, "error": str(exc)}

    def _apply_slider(self, slider_id, value):
        self._log("Applying slider", "id=", slider_id, "value=", value)
        if not isinstance(slider_id, str) or not slider_id:
            self._log("Slider rejected: bad slider id")
            return 400, {"ok": False, "error": "bad slider id"}

        meta = self._sliders.get(slider_id)
        if meta is None:
            self._log("Slider rejected: unknown slider", slider_id)
            return 404, {"ok": False, "error": "unknown slider"}

        if value != value:
            self._log("Slider rejected: value is not a number", slider_id)
            return 400, {"ok": False, "error": "bad value"}

        try:
            if value < meta["min"]:
                value = meta["min"]
            if value > meta["max"]:
                value = meta["max"]
            meta["handler"](value)
            self._state[slider_id] = value
            if meta["motion"]:
                self._touch_motion(event="slider:%s" % slider_id)
            self._log("Slider applied", slider_id, "stored=", value)
            return 200, {"ok": True, "value": value}
        except Exception as exc:
            self._log("Slider error", slider_id, "->", exc)
            if meta["motion"] or self._movement_active:
                self._stop_after_handler_error()
            return 500, {"ok": False, "error": str(exc)}

    def _handle_emergency_stop(self, reason="request"):
        self._log("Handling emergency stop", "reason=", reason)
        handler = self._emergency_handler
        if handler is None and "stop" in self._commands:
            handler = self._commands["stop"]["handler"]
        if handler is None:
            self._log("Emergency stop unavailable: no stop handler registered")
            return 500, {"ok": False, "error": "emergency stop unavailable"}

        try:
            handler()
            self._mark_safe(reason="emergency_stop:%s" % reason)
            self._log("Emergency stop handled")
            return 200, {"ok": True}
        except Exception as exc:
            self._log("Emergency stop error ->", exc)
            return 500, {"ok": False, "error": str(exc)}

    def _check_timeout(self):
        if not self._movement_active:
            return
        if self.command_timeout_ms <= 0:
            return
        if self._now_ms() - self._last_motion_ms < self.command_timeout_ms:
            return

        elapsed_ms = self._now_ms() - self._last_motion_ms
        self._log(
            "[WATCHDOG] TIMEOUT",
            "command=", self._active_motion_command,
            "elapsed_ms=", elapsed_ms,
            "limit_ms=", self.command_timeout_ms,
        )
        self._handle_emergency_stop(reason="watchdog_timeout")

    def _validate_motion_safety(self):
        has_motion = any(meta["motion"] for meta in self._commands.values())
        if not has_motion:
            has_motion = any(meta["motion"] for meta in self._sliders.values())
        if not has_motion:
            return

        if self.command_timeout_ms is None or self.command_timeout_ms <= 0:
            raise RuntimeError("motion controls require a positive command_timeout_ms")
        if self._emergency_handler is None and "stop" not in self._commands:
            raise RuntimeError("motion controls require an emergency stop handler")

    # Routes and server loop
    def _route(self, req):
        method = req["method"]
        path = req["path"]
        query = req.get("query", {})
        self._log("Routing", method, path, query)

        if method == "GET" and path == "/":
            return 200, HTML, "text/html"
        if method == "GET" and path == "/app.js":
            return 200, JS, "application/javascript"
        if method == "GET" and path == "/app.css":
            return 200, CSS, "text/css"
        if method == "GET" and path == "/api/ping":
            return 200, {"ok": True, "ip": self._ap_ip}, "json"
        if method == "GET" and path == "/api/schema":
            return 200, self._build_schema(), "json"
        if method == "GET" and path == "/api/state":
            return 200, self._build_state(), "json"

        if method == "GET" and path == "/api/command":
            command_id = query.get("id")
            event = query.get("event", "press")
            status, out = self._apply_command(command_id, event=event)
            return status, out, "json"

        if method == "GET" and path == "/api/set":
            slider_id = query.get("id")
            try:
                value = float(query.get("value"))
            except Exception:
                return 400, {"ok": False, "error": "bad payload"}, "json"
            status, out = self._apply_slider(slider_id, value)
            return status, out, "json"

        if method == "GET" and path == "/api/emergency_stop":
            status, out = self._handle_emergency_stop()
            return status, out, "json"

        if method == "POST" and path == "/api/command":
            try:
                payload = json.loads(req["body"] or "{}")
                if not isinstance(payload, dict):
                    raise ValueError("payload must be an object")
                command_id = payload.get("id")
                event = payload.get("event", "press")
            except Exception:
                return 400, {"ok": False, "error": "bad json"}, "json"
            status, out = self._apply_command(command_id, event=event)
            return status, out, "json"

        if method == "POST" and path == "/api/set":
            try:
                payload = json.loads(req["body"] or "{}")
                slider_id = payload.get("id")
                value = payload.get("value")
                if value is None:
                    raise ValueError("missing value")
                value = float(value)
            except Exception:
                return 400, {"ok": False, "error": "bad payload"}, "json"
            status, out = self._apply_slider(slider_id, value)
            return status, out, "json"

        if method == "POST" and path == "/api/emergency_stop":
            status, out = self._handle_emergency_stop()
            return status, out, "json"

        if path.startswith("/api/"):
            if method not in ("GET", "POST"):
                return 405, {"ok": False, "error": "method not allowed"}, "json"
            return 404, {"ok": False, "error": "not found"}, "json"

        return 404, "Not Found", "text/plain"

    def run(self):
        """Validate motion configuration and serve requests until stop() succeeds."""
        self._validate_motion_safety()
        self._log("=== TERMINAL DEBUG ENABLED ===")
        self._log("Dashboard title:", self.title)
        if self.unique_ssid:
            self._log("SSID prefix:", self.ssid)
        else:
            self._log("Configured SSID:", self.ssid)
        self._log("Commands:", ", ".join(self._commands.keys()))
        self._log("Sliders:", ", ".join(self._sliders.keys()))
        self._log("Telemetry:", ", ".join(self._telemetry.keys()))
        self._log("Motion timeout (ms):", self.command_timeout_ms)
        self.start_ap()
        server = self._start_socket()

        while self._running:
            try:
                conn, _addr = server.accept()
                self._log("Accepted connection from", _addr)
            except OSError:
                self._check_timeout()
                if self._idle_callback is not None:
                    try:
                        self._idle_callback()
                    except Exception:
                        pass
                continue

            try:
                try:
                    conn.settimeout(0.4)
                except Exception:
                    pass
                raw = self._read_request_bytes(conn, 2048)
                if not raw:
                    self._log("Empty request payload received")
                    conn.close()
                    continue
                self._log("Received packet from dashboard bytes=", len(raw))

                req = self._parse_request(raw)
                if req is None:
                    self._log("Malformed request")
                    self._send_response(conn, "Malformed request", status_code=400)
                    conn.close()
                    continue

                status, payload, content_type = self._route(req)
                if content_type == "json":
                    self._json_response(conn, payload, status_code=status)
                else:
                    self._send_response(conn, payload, status_code=status, content_type=content_type)

            except Exception as exc:
                self._log("Server exception while handling request:", exc)
                try:
                    self._send_response(conn, "Server error: %s" % exc, status_code=500)
                except Exception as send_exc:
                    # A disconnected client must not take the watchdog down.
                    self._log("Could not send server error response:", send_exc)
            finally:
                self._check_timeout()
                try:
                    conn.close()
                except Exception:
                    pass

    def stop(self):
        """Stop active motion and exit the loop; return False if the stop fails."""
        if self._movement_active:
            status, _out = self._handle_emergency_stop(reason="server_stop")
            if status != 200:
                return False
        self._running = False
        return True
