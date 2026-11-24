"""
KAME Robot Controller — Demo Dashboard

Run:
    python kame_dashboard.py

Open:
    http://127.0.0.1:5000

Uses Python's standard library only.
All movements and telemetry are simulated.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import threading
import time
import webbrowser


HOST = "127.0.0.1"
PORT = 5000

lock = threading.Lock()
started_at = time.monotonic()

state = {
    "status": "Ready",
    "command": "home",
    "moving": False,
    "speed": 1.0,
    "ends_at": 0.0,
}

COMMANDS = {
    "forward": ("Walking forward", 4.0),
    "backward": ("Walking backward", 4.0),
    "left": ("Turning left", 3.0),
    "right": ("Turning right", 3.0),
    "home": ("Home position", 0.0),
    "bow": ("Bowing", 2.5),
    "dance": ("Dancing", 5.0),
    "wave": ("Waving", 3.0),
    "stop": ("Stopped", 0.0),
}


def snapshot():
    """Read simulation state and finish timed actions."""
    with lock:
        now = time.monotonic()

        if state["moving"] and now >= state["ends_at"]:
            state["moving"] = False
            state["status"] = "Ready"
            state["command"] = "home"

        elapsed = now - started_at

        return {
            "status": state["status"],
            "command": state["command"],
            "moving": state["moving"],
            "speed": state["speed"],
            "battery": 87,
            "temperature": round(
                33 + 0.6 * math.sin(elapsed / 8)
                + (1.2 if state["moving"] else 0),
                1,
            ),
            "uptime": int(elapsed),
        }


PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KAME | Demo Controller</title>

<style>
:root {
  color-scheme: dark;
  --bg: #0b1016;
  --panel: #121a24;
  --border: #263241;
  --text: #e7eef7;
  --muted: #8d9db0;
  --accent: #99d576;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background:
    radial-gradient(ellipse at 10% 0%, #21372655, transparent 45%),
    var(--bg);
  color: var(--text);
  font-family: "Segoe UI", Arial, sans-serif;
}

button, input {
  font: inherit;
}

button {
  cursor: pointer;
}

button:focus-visible, input:focus-visible {
  outline: 3px solid #99d576;
  outline-offset: 4px;
}

.dashboard {
  max-width: 1280px;
  margin: auto;
  padding: 30px;
}

header, .brand, .connection, .panel-heading {
  display: flex;
  align-items: center;
}

header {
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 28px;
}

.brand {
  gap: 14px;
}

.logo {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  background: #263c2a;
  border: 1px solid #4b6c40;
  border-radius: 15px;
  color: var(--accent);
  font-weight: 800;
  letter-spacing: 1px;
}

h1 {
  font-size: 23px;
  margin: 0 0 5px;
}

.subtitle {
  color: var(--muted);
  font-size: 13px;
}

.connection {
  gap: 9px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 30px;
  font-size: 12px;
  color: #bccbbd;
  background: #121d18;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 12px #99d57655;
}

.connection.offline {
  background: #2a1b1d;
  color: #ffb6b6;
}

.connection.offline .dot {
  background: #fa7777;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.card {
  background: linear-gradient(145deg, #151e29, #101720);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: 0 12px 28px #00000020;
}

.metric {
  padding: 20px;
}

.metric-label, .eyebrow {
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.metric-value {
  margin-top: 12px;
  font-size: 26px;
  font-weight: 650;
}

.metric-value.green {
  color: var(--accent);
}

.metric-value.blue {
  color: #81baff;
}

.metric-value.orange {
  color: #f3b77e;
}

.metric-unit {
  font-size: 14px;
  color: var(--muted);
}

.metric-note {
  margin-top: 8px;
  font-size: 11px;
  color: var(--muted);
}

.main {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 1fr);
  gap: 20px;
}

.visual-panel {
  padding: 22px;
  display: flex;
  flex-direction: column;
}

.panel-heading {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

h2 {
  font-size: 15px;
  margin: 0;
  font-weight: 600;
}

.chip {
  border: 1px solid #38503a;
  color: #a8cd98;
  padding: 6px 9px;
  border-radius: 7px;
  font-size: 10px;
  letter-spacing: 1px;
  white-space: nowrap;
}

.robot-stage {
  flex: 1;
  min-height: 390px;
  display: grid;
  place-items: center;
}

.robot {
  width: 100%;
  max-width: 540px;
}

.kame-svg {
  display: block;
  width: 100%;
  height: auto;
}

.top-leg {
  transform-box: view-box;
}

.fl { transform-origin: 163px 131px; }
.fr { transform-origin: 257px 131px; }
.rl { transform-origin: 163px 229px; }
.rr { transform-origin: 257px 229px; }

.robot[data-command="forward"] .fl,
.robot[data-command="forward"] .rr,
.robot[data-command="backward"] .fr,
.robot[data-command="backward"] .rl {
  animation: step var(--step-time, .45s) ease-in-out infinite alternate;
}

.robot[data-command="forward"] .fr,
.robot[data-command="forward"] .rl,
.robot[data-command="backward"] .fl,
.robot[data-command="backward"] .rr {
  animation: step var(--step-time, .45s) ease-in-out infinite alternate-reverse;
}

.robot[data-command="left"] .top-leg {
  animation: step var(--step-time, .45s) ease-in-out infinite alternate;
}

.robot[data-command="right"] .top-leg {
  animation: step var(--step-time, .45s) ease-in-out infinite alternate-reverse;
}

.robot[data-command="wave"] .fl {
  animation: wave var(--step-time, .45s) ease-in-out infinite alternate;
}

.robot[data-command="dance"] .top-leg {
  animation: step var(--step-time, .45s) ease-in-out infinite alternate;
}

.robot[data-command="dance"] .robot-assembly {
  transform-origin: 210px 180px;
  animation: dance .7s ease-in-out infinite alternate;
}

.robot[data-command="bow"] .robot-assembly {
  transform-origin: 210px 235px;
  animation: bow 1.2s ease-in-out infinite alternate;
}

@keyframes step {
  from { transform: rotate(-10deg); }
  to { transform: rotate(10deg); }
}

@keyframes wave {
  from { transform: rotate(-12deg); }
  to { transform: rotate(28deg); }
}

@keyframes dance {
  from { transform: rotate(-4deg); }
  to { transform: rotate(4deg); }
}

@keyframes bow {
  from { transform: scaleY(1); }
  to { transform: scaleY(.88); }
}

.state-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 17px;
  background: #0d141c;
  border: 1px solid #253141;
  border-radius: 12px;
}

.state-light {
  height: 10px;
  width: 10px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--accent);
}

.state-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}

.state-sub {
  font-size: 12px;
  color: var(--muted);
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-card {
  padding: 20px;
}

.dpad {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
  margin-top: 18px;
}

button {
  border: 1px solid #334457;
  background: #1c2a39;
  color: var(--text);
  border-radius: 11px;
  padding: 13px 8px;
  font-size: 12px;
  font-weight: 600;
  transition: background .15s, transform .15s;
}

button:hover {
  background: #2b4054;
}

button:active {
  transform: scale(.97);
}

.home-button {
  color: var(--accent);
  background: #233224;
  border-color: #40583b;
}

.actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 9px;
  margin-top: 15px;
}

.speed-row {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  font-size: 12px;
  color: var(--muted);
}

#speedValue {
  color: var(--accent);
}

input[type="range"] {
  width: 100%;
  margin-top: 13px;
  accent-color: var(--accent);
  cursor: pointer;
}

.stop-button {
  width: 100%;
  padding: 16px;
  background: #432426;
  border-color: #804043;
  color: #ffb5b5;
  letter-spacing: 1px;
}

.stop-button:hover {
  background: #623033;
}

.log-panel {
  margin-top: 20px;
  padding: 20px;
}

.clear-button {
  font-size: 11px;
  padding: 6px 10px;
  background: transparent;
}

.log {
  height: 145px;
  overflow: auto;
  font-family: Consolas, monospace;
  font-size: 12px;
  line-height: 1.9;
  color: #b0bece;
}

.log-time {
  color: #71869d;
  margin-right: 12px;
}

.log-error {
  color: #ffaaaa;
}

footer {
  text-align: center;
  font-size: 11px;
  color: var(--muted);
  margin-top: 22px;
  line-height: 1.8;
}

@media (max-width: 860px) {
  .main { grid-template-columns: 1fr; }
  .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 480px) {
  .dashboard { padding: 16px; }
  header { align-items: flex-start; flex-direction: column; }
  .metric { padding: 15px; }
  .metric-value { font-size: 21px; }
  .robot-stage { min-height: 280px; }
}

@media (prefers-reduced-motion: reduce) {
  .robot *, button {
    animation: none !important;
    transition: none !important;
  }
}
</style>
</head>

<body>
<div class="dashboard">

  <header>
    <div class="brand">
      <div class="logo">K</div>
      <div>
        <h1>KAME Control</h1>
        <div class="subtitle">Quadruped robot · Local demo controller</div>
      </div>
    </div>

    <div class="connection" id="connection">
      <span class="dot"></span>
      <span id="connectionText">Connecting to local app</span>
    </div>
  </header>

  <section class="metrics">
    <div class="card metric">
      <div class="metric-label">Robot status</div>
      <div class="metric-value green" id="status">Ready</div>
      <div class="metric-note">Simulation only</div>
    </div>

    <div class="card metric">
      <div class="metric-label">Demo battery</div>
      <div class="metric-value blue">
        <span id="battery">87</span><span class="metric-unit"> %</span>
      </div>
      <div class="metric-note">Simulated value</div>
    </div>

    <div class="card metric">
      <div class="metric-label">Demo temperature</div>
      <div class="metric-value orange">
        <span id="temperature">33.0</span><span class="metric-unit"> °C</span>
      </div>
      <div class="metric-note">Simulated value</div>
    </div>

    <div class="card metric">
      <div class="metric-label">Session uptime</div>
      <div class="metric-value" id="uptime">00:00</div>
      <div class="metric-note">Local application runtime</div>
    </div>
  </section>

  <main class="main">

    <section class="card visual-panel">
      <div class="panel-heading">
        <h2>Robot visualization</h2>
        <span class="chip">TOP VIEW</span>
      </div>

      <div class="robot-stage">
        <div class="robot" id="robot" data-command="home">
          <svg
            class="kame-svg"
            viewBox="0 0 420 360"
            role="img"
            aria-label="Top-down diagram of a green and black KAME-style robot"
          >
            <defs>
              <pattern
                id="grid"
                width="24"
                height="24"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M24 0H0V24"
                  fill="none"
                  stroke="#293748"
                  stroke-width=".6"
                />
              </pattern>

              <linearGradient id="green" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#83ad67"/>
                <stop offset="100%" stop-color="#365d31"/>
              </linearGradient>
            </defs>

            <rect
              x="10" y="10" width="400" height="340" rx="22"
              fill="#0d151e"
            />
            <rect
              x="10" y="10" width="400" height="340" rx="22"
              fill="url(#grid)"
            />

            <path d="M210 33L201 47H219Z" fill="#99d576"/>
            <text
              x="210" y="65" text-anchor="middle"
              fill="#8d9db0" font-size="10" letter-spacing="3"
            >FRONT</text>

            <g class="robot-assembly">

              <!-- Front-left leg -->
              <g class="top-leg fl">
                <path
                  d="M163 131L108 104L69 142"
                  fill="none" stroke="#638c50" stroke-width="23"
                  stroke-linejoin="round" stroke-linecap="round"
                />
                <path
                  d="M108 104L69 142"
                  fill="none" stroke="#242b30" stroke-width="10"
                  stroke-linecap="round"
                />
                <circle cx="108" cy="104" r="10" fill="#343d43"/>
                <circle cx="108" cy="104" r="4" fill="#b7c0c8"/>
                <rect
                  x="53" y="132" width="32" height="25" rx="7"
                  fill="#527b42" transform="rotate(-30 69 144)"
                />
              </g>

              <!-- Front-right leg -->
              <g class="top-leg fr">
                <path
                  d="M257 131L312 104L351 142"
                  fill="none" stroke="#638c50" stroke-width="23"
                  stroke-linejoin="round" stroke-linecap="round"
                />
                <path
                  d="M312 104L351 142"
                  fill="none" stroke="#242b30" stroke-width="10"
                  stroke-linecap="round"
                />
                <circle cx="312" cy="104" r="10" fill="#343d43"/>
                <circle cx="312" cy="104" r="4" fill="#b7c0c8"/>
                <rect
                  x="335" y="132" width="32" height="25" rx="7"
                  fill="#527b42" transform="rotate(30 351 144)"
                />
              </g>

              <!-- Rear-left leg -->
              <g class="top-leg rl">
                <path
                  d="M163 229L108 256L69 218"
                  fill="none" stroke="#638c50" stroke-width="23"
                  stroke-linejoin="round" stroke-linecap="round"
                />
                <path
                  d="M108 256L69 218"
                  fill="none" stroke="#242b30" stroke-width="10"
                  stroke-linecap="round"
                />
                <circle cx="108" cy="256" r="10" fill="#343d43"/>
                <circle cx="108" cy="256" r="4" fill="#b7c0c8"/>
                <rect
                  x="53" y="205" width="32" height="25" rx="7"
                  fill="#527b42" transform="rotate(30 69 217)"
                />
              </g>

              <!-- Rear-right leg -->
              <g class="top-leg rr">
                <path
                  d="M257 229L312 256L351 218"
                  fill="none" stroke="#638c50" stroke-width="23"
                  stroke-linejoin="round" stroke-linecap="round"
                />
                <path
                  d="M312 256L351 218"
                  fill="none" stroke="#242b30" stroke-width="10"
                  stroke-linecap="round"
                />
                <circle cx="312" cy="256" r="10" fill="#343d43"/>
                <circle cx="312" cy="256" r="4" fill="#b7c0c8"/>
                <rect
                  x="335" y="205" width="32" height="25" rx="7"
                  fill="#527b42" transform="rotate(-30 351 217)"
                />
              </g>

              <!-- Chassis -->
              <rect
                x="148" y="102" width="124" height="156" rx="24"
                fill="url(#green)" stroke="#87ac71" stroke-width="2"
              />

              <!-- Electronics cover -->
              <rect
                x="166" y="124" width="88" height="112" rx="13"
                fill="#20272d" stroke="#454f58" stroke-width="2"
              />

              <g fill="#b0bac3">
                <circle cx="177" cy="136" r="3"/>
                <circle cx="243" cy="136" r="3"/>
                <circle cx="177" cy="224" r="3"/>
                <circle cx="243" cy="224" r="3"/>
              </g>

              <circle cx="210" cy="151" r="5" fill="#a7e17e"/>

              <text
                x="210" y="184" text-anchor="middle"
                fill="#e4ebdf" font-size="18"
                font-weight="700" letter-spacing="2"
              >KAME</text>

              <text
                x="210" y="204" text-anchor="middle"
                fill="#8fa28d" font-size="9" letter-spacing="2"
              >DEMO UNIT</text>
            </g>

            <text
              x="210" y="324" text-anchor="middle"
              fill="#7d91a7" font-size="10" letter-spacing="2"
            >OVERHEAD VIEW · SIMULATION</text>
          </svg>
        </div>
      </div>

      <div class="state-box" role="status">
        <span class="state-light"></span>
        <div>
          <div class="state-title" id="stateTitle">Ready</div>
          <div class="state-sub" id="stateSub">
            Select a command to start the demo.
          </div>
        </div>
      </div>
    </section>

    <aside class="controls">
      <section class="card control-card">
        <div class="panel-heading">
          <h2>Movement control</h2>
          <span class="eyebrow">W A S D</span>
        </div>

        <div class="dpad">
          <span></span>
          <button onclick="sendCommand('forward')">↑ Forward</button>
          <span></span>

          <button onclick="sendCommand('left')">← Left</button>
          <button class="home-button" onclick="sendCommand('home')">
            Home
          </button>
          <button onclick="sendCommand('right')">Right →</button>

          <span></span>
          <button onclick="sendCommand('backward')">↓ Backward</button>
          <span></span>
        </div>

        <div class="speed-row">
          <label for="speed">Animation speed</label>
          <span id="speedValue">1.0×</span>
        </div>

        <input
          id="speed" type="range"
          min="0.5" max="2.5" step="0.1" value="1"
          oninput="previewSpeed(this.value)"
          onchange="setSpeed(this.value)"
        >
      </section>

      <section class="card control-card">
        <h2>Demo actions</h2>
        <div class="actions">
          <button onclick="sendCommand('bow')">Bow</button>
          <button onclick="sendCommand('dance')">Dance</button>
          <button onclick="sendCommand('wave')">Wave</button>
        </div>
      </section>

      <section class="card control-card">
        <button class="stop-button" onclick="sendCommand('stop')">
          STOP SIMULATION
        </button>
        <div class="metric-note" style="text-align:center;margin-top:12px">
          Keyboard shortcut: Space
        </div>
      </section>

      <section class="card control-card">
        <div class="eyebrow">Demo mode</div>
        <p style="font-size:13px;color:var(--muted);line-height:1.8;margin-bottom:0">
          No robot is connected. Commands animate the diagram only.
          Timed actions return to the home pose automatically.
        </p>
      </section>
    </aside>
  </main>

  <section class="card log-panel">
    <div class="panel-heading">
      <h2>Activity log</h2>
      <button
        class="clear-button"
        onclick="document.getElementById('log').replaceChildren()"
      >Clear</button>
    </div>
    <div class="log" id="log" aria-label="Activity log"></div>
  </section>

  <footer>
    KAME Demo Controller · No hardware connection<br>
    W / ↑ Forward · S / ↓ Backward · A / ← Left · D / → Right · H Home · Space Stop
  </footer>
</div>

<script>
let commandPending = false;

function addLog(message, error = false) {
  const log = document.getElementById("log");
  const row = document.createElement("div");

  const timestamp = document.createElement("span");
  timestamp.className = "log-time";
  timestamp.textContent = new Date().toLocaleTimeString();

  const text = document.createElement("span");
  text.textContent = message;
  if (error) text.className = "log-error";

  row.append(timestamp, text);
  log.prepend(row);

  while (log.children.length > 100) {
    log.lastChild.remove();
  }
}

function setConnection(online) {
  document.getElementById("connection").classList.toggle("offline", !online);
  document.getElementById("connectionText").textContent =
    online ? "Local demo online" : "Local app unavailable";

  if (!online) {
    document.getElementById("robot").dataset.command = "home";
    document.getElementById("stateTitle").textContent = "Disconnected";
    document.getElementById("stateSub").textContent =
      "Check that the Python application is still running.";
  }
}

function previewSpeed(value) {
  const speed = Number(value);
  document.getElementById("speedValue").textContent = speed.toFixed(1) + "×";
  document.getElementById("robot").style.setProperty(
    "--step-time", (0.45 / speed) + "s"
  );
}

function updateDashboard(data) {
  setConnection(true);

  document.getElementById("status").textContent = data.status;
  document.getElementById("battery").textContent = data.battery;
  document.getElementById("temperature").textContent =
    Number(data.temperature).toFixed(1);

  const minutes = Math.floor(data.uptime / 60);
  const seconds = data.uptime % 60;
  document.getElementById("uptime").textContent =
    String(minutes).padStart(2, "0") + ":" +
    String(seconds).padStart(2, "0");

  document.getElementById("stateTitle").textContent = data.status;
  document.getElementById("stateSub").textContent = data.moving
    ? "Executing a timed demo animation. No hardware connected."
    : "Simulation idle. Select a movement or demo action.";

  document.getElementById("robot").dataset.command =
    data.moving ? data.command : "home";

  // Avoid overwriting the slider while the user is adjusting it.
  if (document.activeElement !== document.getElementById("speed")) {
    document.getElementById("speed").value = data.speed;
    previewSpeed(data.speed);
  }
}

async function requestJSON(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    signal: AbortSignal.timeout(4000),
    cache: "no-store"
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function sendCommand(command) {
  // Stop is allowed even when another command request is pending.
  if (commandPending && command !== "stop") return;

  commandPending = true;
  try {
    const data = await requestJSON("/command", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({command})
    });
    updateDashboard(data);
    addLog("Demo command: " + data.status);
  } catch (error) {
    setConnection(false);
    addLog(error.message, true);
  } finally {
    commandPending = false;
  }
}

async function setSpeed(value) {
  try {
    const data = await requestJSON("/speed", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({speed: Number(value)})
    });
    updateDashboard(data);
    addLog("Animation speed: " + data.speed.toFixed(1) + "×");
  } catch (error) {
    setConnection(false);
    addLog(error.message, true);
  }
}

async function poll() {
  try {
    const data = await requestJSON("/telemetry");
    // A later poll will synchronize state after a command finishes.
    if (!commandPending) updateDashboard(data);
  } catch (error) {
    setConnection(false);
  } finally {
    setTimeout(poll, 500);
  }
}

document.addEventListener("keydown", event => {
  const target = event.target;
  if (
    target instanceof HTMLElement &&
    target.closest("input, textarea, select, button, [contenteditable]")
  ) return;

  const keys = {
    w: "forward", ArrowUp: "forward",
    s: "backward", ArrowDown: "backward",
    a: "left", ArrowLeft: "left",
    d: "right", ArrowRight: "right",
    h: "home", " ": "stop"
  };

  const command = keys[event.key] || keys[event.key.toLowerCase()];
  if (command) {
    event.preventDefault();
    if (!event.repeat) sendCommand(command);
  }
});

previewSpeed(1);
addLog("Dashboard initialized. All controls are simulated.");
poll();
</script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def send_bytes(self, data, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_json(self, data, status=200):
        self.send_bytes(
            json.dumps(data).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/":
            self.send_bytes(
                PAGE.encode("utf-8"),
                "text/html; charset=utf-8",
            )
        elif path == "/telemetry":
            self.send_json(snapshot())
        elif path == "/favicon.ico":
            self.send_bytes(b"", "image/x-icon", 204)
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = self.path.split("?", 1)[0]

        if path not in ("/command", "/speed"):
            self.send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 4096:
                raise ValueError("Invalid request size")

            payload = json.loads(
                self.rfile.read(length).decode("utf-8")
            )

            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object")

        except (ValueError, UnicodeDecodeError):
            self.send_json({"error": "Invalid JSON request"}, 400)
            return

        if path == "/command":
            command = payload.get("command")

            if not isinstance(command, str) or command not in COMMANDS:
                self.send_json({"error": "Unknown command"}, 400)
                return

            label, duration = COMMANDS[command]

            with lock:
                state["command"] = command
                state["status"] = label
                state["moving"] = duration > 0
                state["ends_at"] = time.monotonic() + duration

        else:
            try:
                value = payload.get("speed")

                if isinstance(value, bool):
                    raise ValueError

                speed = float(value)

                if not math.isfinite(speed) or not 0.5 <= speed <= 2.5:
                    raise ValueError

            except (TypeError, ValueError):
                self.send_json(
                    {"error": "Speed must be between 0.5 and 2.5"},
                    400,
                )
                return

            with lock:
                state["speed"] = round(speed, 1)

        self.send_json(snapshot())

    def log_message(self, format_string, *args):
        # Suppress routine browser polling messages.
        pass


def main():
    try:
        server = ThreadingHTTPServer(
            (HOST, PORT),
            DashboardHandler,
        )
    except OSError as error:
        print(f"Could not start dashboard: {error}")
        print(
            "Close any previous dashboard instance, "
            "or change PORT near the top of this file."
        )
        return

    url = f"http://{HOST}:{PORT}"
    print(f"KAME demo dashboard: {url}")
    print("No hardware connected. Press Ctrl+C to stop.")

    def open_browser():
        try:
            webbrowser.open(url)
        except Exception:
            pass

    browser_timer = threading.Timer(0.8, open_browser)
    browser_timer.daemon = True
    browser_timer.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()