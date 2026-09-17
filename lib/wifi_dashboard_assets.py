"""Dashboard HTML, CSS, and JavaScript served by WifiCommandServer.

Edit the strings directly; no bundler or separate asset files are needed.
"""

HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>WiFi Robot Car</title>
  <link rel=\"icon\" href=\"data:,\">
  <link rel=\"stylesheet\" href=\"/app.css\">
</head>
<body>
  <main class=\"app\">
    <header class=\"panel\">
      <h1 id=\"title\">WiFi Robot Car</h1>
      <p class=\"status\">Connection: <span id=\"connection\" data-state=\"connecting\">Connecting...</span></p>
      <p id=\"message\" class=\"message\" role=\"status\" aria-live=\"polite\">Loading controls...</p>
    </header>

    <section class=\"panel\">
      <h2>Drive</h2>
      <div class=\"controls-layout\">
        <div class=\"gamepad-shell\">
          <div id=\"gamepad-controls\" class=\"gamepad-grid\"></div>
        </div>
        <div class=\"system-controls-wrap\">
          <h3>Speed &amp; Safety</h3>
          <div id=\"system-controls\" class=\"controls\"></div>
          <button id=\"emergency-stop\" class=\"danger\" type=\"button\">EMERGENCY STOP</button>
        </div>
      </div>
    </section>

    <section class=\"panel\">
      <div class=\"custom-controls-header\">
        <h2>Custom Buttons</h2>
        <button id=\"add-custom-button\" class=\"secondary\" type=\"button\">Add Button</button>
      </div>
      <p class=\"message\">Add temporary buttons for registered non-motion commands.</p>
      <div id=\"custom-controls\" class=\"controls custom-controls\"></div>
    </section>

    <section class=\"panel\">
      <h2>Robot Status</h2>
      <div id=\"telemetry\" class=\"telemetry\"></div>
    </section>
  </main>
  <script src=\"/app.js\"></script>
</body>
</html>
"""

CSS = """:root {
  color-scheme: dark;
  --bg: #0f172a;
  --panel: #1e293b;
  --accent: #22d3ee;
  --stop: #f59e0b;
  --danger: #ef4444;
  --text: #e2e8f0;
  --muted: #94a3b8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
}
.app {
  max-width: 720px;
  margin: 0 auto;
  padding: 0.625rem;
  padding-bottom: 1rem;
  padding-bottom: calc(1rem + env(safe-area-inset-bottom));
  display: grid;
  gap: 0.625rem;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.panel {
  background: var(--panel);
  border-radius: 0.9rem;
  padding: 0.75rem;
}
header.panel { padding: 0.7rem 0.8rem; }
h1 {
  margin: 0 0 0.3rem;
  font-size: clamp(1.55rem, 7vw, 2rem);
  line-height: 1.1;
}
h2 {
  margin: 0 0 0.5rem;
  font-size: clamp(1.25rem, 5vw, 1.55rem);
  line-height: 1.15;
}
.status, .message {
  margin: 0.2rem 0 0;
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.25;
}
#connection[data-state=\"connected\"] { color: #34d399; }
#connection[data-state=\"offline\"] { color: var(--danger); }
.controls {
  display: grid;
  gap: 0.5rem;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
button, input[type=range] { width: 100%; min-height: 44px; }
button {
  border: 0;
  border-radius: 0.7rem;
  font-weight: 700;
  padding: 0.65rem;
  background: var(--accent);
  color: #001018;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
button:active { filter: brightness(0.92); }
button[aria-pressed=\"true\"] {
  filter: brightness(0.84);
  box-shadow: inset 0 0 0 3px rgba(248, 250, 252, 0.7);
}
button:focus-visible {
  outline: 3px solid #f8fafc;
  outline-offset: 2px;
}
.controls-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.55rem;
}
.gamepad-shell {
  background: rgba(15, 23, 42, 0.45);
  border: 1px solid #334155;
  border-radius: 0.8rem;
  padding: 0.45rem;
}
.gamepad-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-template-rows: repeat(3, auto);
  gap: 0.4rem;
}
.gamepad-grid .control-row { min-width: 0; }
.gamepad-grid button {
  height: 100%;
  min-height: clamp(54px, 16vw, 66px);
  padding: 0.35rem 0.2rem;
  font-size: clamp(0.85rem, 4vw, 1.05rem);
}
.gamepad-stop button { background: var(--stop); }
.system-controls-wrap {
  display: grid;
  gap: 0.45rem;
}
.system-controls-wrap h3 {
  display: none;
  margin: 0 0 0.1rem;
  color: var(--muted);
  font-size: 0.95rem;
}
.slider-control { gap: 0; }
.slider-control label { line-height: 1.15; }
.slider-control input[type=range] {
  min-height: 34px;
  margin: 0;
}
.custom-controls-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}
.secondary {
  background: #475569;
  color: #f8fafc;
  min-height: 42px;
  padding: 0.6rem 0.8rem;
}
.custom-controls {
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
}
.control-row {
  display: grid;
  gap: 0.3rem;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
label { color: var(--muted); font-size: 0.95rem; }
.telemetry { display: grid; gap: 0.45rem; }
.telemetry-row {
  display: flex;
  justify-content: space-between;
  background: rgba(15, 23, 42, 0.45);
  border: 1px solid #334155;
  border-radius: 0.6rem;
  padding: 0.55rem 0.7rem;
}
.danger {
  background: var(--danger);
  color: #fff;
}
#emergency-stop {
  min-height: 52px;
  font-size: 1rem;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
@media (min-width: 680px) {
  .app {
    padding: 1rem;
    padding-bottom: 2rem;
    padding-bottom: calc(2rem + env(safe-area-inset-bottom));
    gap: 1rem;
  }
  .panel { padding: 1rem; }
  header.panel { padding: 1rem; }
  .controls-layout {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
    gap: 1rem;
  }
  .system-controls-wrap h3 { display: block; }
}
"""

JS = """(function () {
  const titleEl = document.getElementById('title');
  const connectionEl = document.getElementById('connection');
  const messageEl = document.getElementById('message');
  const gamepadEl = document.getElementById('gamepad-controls');
  const systemControlsEl = document.getElementById('system-controls');
  const customControlsEl = document.getElementById('custom-controls');
  const addCustomButtonEl = document.getElementById('add-custom-button');
  const telemetryEl = document.getElementById('telemetry');
  const stopEl = document.getElementById('emergency-stop');

  let schema = null;
  let telemetryFields = [];
  let consecutivePollFailures = 0;
  const activeMotionHolds = new Set();
  const holdRefreshIntervalMs = 320;
  const connectionLabels = {
    connecting: 'Connecting...',
    connected: 'Connected',
    offline: 'Disconnected'
  };
  // These IDs only select positions; the schema defines button behavior.
  const gamepadPlacement = {
    forward: { column: 2, row: 1 },
    left: { column: 1, row: 2 },
    stop: { column: 2, row: 2 },
    right: { column: 3, row: 2 },
    reverse: { column: 2, row: 3 }
  };

  function setConnection(state, msg) {
    const previousState = connectionEl.dataset.state;
    connectionEl.dataset.state = state;
    connectionEl.textContent = connectionLabels[state] || state;
    if (msg) messageEl.textContent = msg;
    else if (state === 'connected' && previousState === 'offline') {
      messageEl.textContent = 'Robot reconnected.';
    }
  }

  async function getJson(url) {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) {
      const error = new Error('HTTP ' + res.status);
      error.status = res.status;
      throw error;
    }
    return await res.json();
  }

  function reportRequestFailure(error, rejectedMessage, offlineMessage) {
    if (error && error.status) {
      setConnection('connected', rejectedMessage + ' (HTTP ' + error.status + ').');
    } else {
      setConnection('offline', offlineMessage);
    }
  }

  function cancelAllMotionHolds() {
    // Cancel local timers. The caller must still send a stop request.
    Array.from(activeMotionHolds).forEach((cancel) => cancel());
  }

  function buildButton(control) {
    const row = document.createElement('div');
    row.className = 'control-row';
    const btn = document.createElement('button');
    btn.textContent = control.label || control.id;
    btn.type = 'button';
    btn.setAttribute('draggable', 'false');
    if (control.on_release) btn.setAttribute('aria-pressed', 'false');

    let pressed = false;
    let holdTimer = null;
    let refreshInFlight = false;
    const isMotionHold = control.on_release && control.motion;

    const stopHoldRefresh = () => {
      if (holdTimer !== null) {
        clearInterval(holdTimer);
        holdTimer = null;
      }
    };

    const cancelMotionHold = () => {
      pressed = false;
      if (control.on_release) btn.setAttribute('aria-pressed', 'false');
      stopHoldRefresh();
      activeMotionHolds.delete(cancelMotionHold);
    };

    const press = async (ev) => {
      if (ev) ev.preventDefault();
      if (pressed) return;
      pressed = true;
      if (control.on_release) btn.setAttribute('aria-pressed', 'true');
      if (isMotionHold) activeMotionHolds.add(cancelMotionHold);
      if (ev && typeof btn.setPointerCapture === 'function' && ev.pointerId != null) {
        try { btn.setPointerCapture(ev.pointerId); } catch (_) {}
      }
      try {
        await getJson('/api/command?id=' + encodeURIComponent(control.id) + '&event=press');
        // A quick release may have happened while the press request was pending.
        if (!pressed) return;
        if (isMotionHold) {
          console.log('[hold] start', control.id);
          stopHoldRefresh();
          holdTimer = setInterval(async () => {
            if (!pressed || refreshInFlight) return;
            refreshInFlight = true;
            try {
              await getJson('/api/command?id=' + encodeURIComponent(control.id) + '&event=keepalive');
              console.log('[hold] refresh', control.id);
            } catch (error) {
              if (pressed) {
                reportRequestFailure(
                  error,
                  'Motion hold was rejected by the robot',
                  'Motion connection lost. Trying to reconnect...'
                );
              }
            } finally {
              refreshInFlight = false;
            }
          }, holdRefreshIntervalMs);
        }
      } catch (error) {
        cancelMotionHold();
        reportRequestFailure(
          error,
          'Command was rejected by the robot',
          'Could not send command. Trying to reconnect...'
        );
      }
    };

    const release = async (ev) => {
      if (ev) ev.preventDefault();
      if (!pressed) return;
      cancelMotionHold();
      if (isMotionHold) console.log('[hold] end', control.id);
      if (!control.on_release) return;
      try {
        await getJson('/api/command?id=' + encodeURIComponent(control.id) + '&event=release');
      } catch (error) {
        reportRequestFailure(
          error,
          'Stop-on-release was rejected by the robot',
          'Release connection lost. Safety timeout is still active.'
        );
      }
    };

    if (control.on_release) {
      btn.addEventListener('pointerdown', press);
      btn.addEventListener('pointerup', release);
      btn.addEventListener('pointercancel', release);
      btn.addEventListener('pointerleave', (ev) => {
        if (ev.pointerType === 'mouse') release(ev);
      });
      btn.addEventListener('keydown', (ev) => {
        if ((ev.key === 'Enter' || ev.key === ' ') && !ev.repeat) press(ev);
      });
      btn.addEventListener('keyup', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') release(ev);
      });
      btn.addEventListener('blur', release);
    } else {
      btn.addEventListener('click', async (ev) => {
        ev.preventDefault();
        try {
          await getJson('/api/command?id=' + encodeURIComponent(control.id) + '&event=press');
        } catch (error) {
          reportRequestFailure(
            error,
            'Command was rejected by the robot',
            'Could not send command. Trying to reconnect...'
          );
        }
      });
    }
    row.appendChild(btn);
    return row;
  }

  function addGamepadButton(control) {
    const row = buildButton(control);
    const placement = gamepadPlacement[control.id];
    row.style.gridColumn = String(placement.column);
    row.style.gridRow = String(placement.row);
    if (control.id === 'stop') row.classList.add('gamepad-stop');
    gamepadEl.appendChild(row);
  }

  function addSystemButton(control) {
    const row = buildButton(control);
    systemControlsEl.appendChild(row);
  }

  function addSlider(control) {
    const row = document.createElement('div');
    row.className = 'control-row slider-control';

    const label = document.createElement('label');
    label.textContent = (control.label || control.id) + ': ';

    const value = document.createElement('span');
    value.textContent = String(control.default || 0);
    label.appendChild(value);

    const input = document.createElement('input');
    input.type = 'range';
    input.min = String(control.min == null ? 0 : control.min);
    input.max = String(control.max == null ? 100 : control.max);
    input.step = String(control.step == null ? 1 : control.step);
    input.value = String(control.default == null ? input.min : control.default);

    const send = async () => {
      value.textContent = input.value;
      try {
        await getJson('/api/set?id=' + encodeURIComponent(control.id) + '&value=' + encodeURIComponent(input.value));
      } catch (error) {
        reportRequestFailure(
          error,
          'Setting was rejected by the robot',
          'Could not update setting. Trying to reconnect...'
        );
      }
    };

    input.addEventListener('input', send);
    input.addEventListener('change', send);

    row.appendChild(label);
    row.appendChild(input);
    systemControlsEl.appendChild(row);
  }

  function addButton(control) {
    if (Object.prototype.hasOwnProperty.call(gamepadPlacement, control.id)) {
      addGamepadButton(control);
    }
    else addSystemButton(control);
  }

  // Add a renderer here when adding a new control type to the server schema.
  const controlRenderers = {
    button: addButton,
    slider: addSlider
  };

  function renderControl(control) {
    const renderer = controlRenderers[control.type];
    if (!renderer) {
      console.warn('Unsupported control type:', control.type);
      return;
    }
    renderer(control);
  }

  function addCustomButton(label, commandId) {
    // Press only: no release or refresh. Intended for non-motion commands.
    const row = document.createElement('div');
    row.className = 'control-row';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = label;
    btn.setAttribute('draggable', 'false');
    btn.className = 'secondary';
    btn.addEventListener('click', async (ev) => {
      ev.preventDefault();
      try {
        await getJson('/api/command?id=' + encodeURIComponent(commandId) + '&event=press');
      } catch (error) {
        reportRequestFailure(
          error,
          'Custom command was rejected. Check its registered command ID',
          'Could not send custom command. Trying to reconnect...'
        );
      }
    });
    row.appendChild(btn);
    customControlsEl.appendChild(row);
  }

  function renderTelemetry() {
    telemetryEl.textContent = '';
    for (const field of telemetryFields) {
      const row = document.createElement('div');
      row.className = 'telemetry-row';
      const label = document.createElement('span');
      label.textContent = field.label || field.id;
      const val = document.createElement('span');
      val.id = 'telemetry-' + field.id;
      val.textContent = '--';
      row.appendChild(label);
      row.appendChild(val);
      telemetryEl.appendChild(row);
    }
  }

  async function loadSchema() {
    schema = await getJson('/api/schema');
    const dashboardTitle = schema.title || 'WiFi Robot Car';
    titleEl.textContent = dashboardTitle;
    document.title = dashboardTitle;
    gamepadEl.textContent = '';
    systemControlsEl.textContent = '';
    customControlsEl.textContent = '';

    telemetryFields = Array.isArray(schema.telemetry) ? schema.telemetry : [];
    const controls = Array.isArray(schema.controls) ? schema.controls : [];

    controls.forEach(renderControl);

    renderTelemetry();
    setConnection('connected', 'Robot ready.');
  }

  async function pollState() {
    try {
      const state = await getJson('/api/state');
      consecutivePollFailures = 0;
      telemetryFields.forEach((field) => {
        const el = document.getElementById('telemetry-' + field.id);
        if (!el) return;
        const next = state[field.id];
        el.textContent = next == null ? '--' : String(next);
      });
      setConnection('connected');
    } catch (_) {
      consecutivePollFailures += 1;
      if (consecutivePollFailures >= 3) {
        setConnection('offline', 'Connection lost. Trying to reconnect...');
      }
    }
  }

  const sendEmergencyStop = async (ev) => {
    ev.preventDefault();
    cancelAllMotionHolds();
    try {
      await getJson('/api/emergency_stop');
      setConnection('connected', 'Emergency Stop sent.');
    } catch (error) {
      reportRequestFailure(
        error,
        'Emergency Stop was rejected by the robot',
        'Emergency Stop connection failed. Safety timeout is still active.'
      );
    }
  };

  stopEl.addEventListener('pointerdown', sendEmergencyStop);
  stopEl.addEventListener('keydown', (ev) => {
    if ((ev.key === 'Enter' || ev.key === ' ') && !ev.repeat) {
      sendEmergencyStop(ev);
    }
  });

  function stopForPageExit() {
    // Best effort: the page may disappear before delivery. The watchdog is backup.
    cancelAllMotionHolds();
    if (typeof navigator.sendBeacon === 'function') {
      navigator.sendBeacon('/api/emergency_stop', '');
    } else {
      fetch('/api/emergency_stop', { method: 'POST', keepalive: true }).catch(() => {});
    }
  }

  window.addEventListener('pagehide', stopForPageExit);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden' && activeMotionHolds.size > 0) {
      stopForPageExit();
    }
  });

  addCustomButtonEl.addEventListener('click', () => {
    const rawLabel = window.prompt('Button label (for example, Horn):');
    if (rawLabel == null) return;
    const label = rawLabel.trim().slice(0, 24);
    if (!label) return;

    const rawCommandId = window.prompt('Registered non-motion command ID (for example, horn):');
    if (rawCommandId == null) return;
    const commandId = rawCommandId.trim();
    if (!commandId) return;

    addCustomButton(label, commandId);
    messageEl.textContent = 'Added "' + label + '" for this browser session.';
  });

  loadSchema().catch(() => {
    setConnection('offline', 'Could not load robot controls. Reload this page to try again.');
  });
  setInterval(pollState, 800);
})();
"""
