const players = [
  { name: "Avery", kills: 12, deaths: 6, ping: 34 },
  { name: "Nova", kills: 9, deaths: 8, ping: 48 },
  { name: "Rey", kills: 8, deaths: 10, ping: 52 },
  { name: "Kael", kills: 6, deaths: 11, ping: 61 },
];

const killFeedEvents = [
  { killer: "Avery", victim: "Kael", weapon: "CARV" },
  { killer: "Nova", victim: "Rey", weapon: "Rocket" },
  { killer: "Rey", victim: "Nova", weapon: "Sniper" },
  { killer: "Kael", victim: "Avery", weapon: "SMG" },
];

const keybinds = [
  ["Move Forward", "W"],
  ["Move Back", "S"],
  ["Strafe Left", "A"],
  ["Strafe Right", "D"],
  ["Jump", "Space"],
  ["Crouch", "Ctrl"],
  ["Sprint", "Shift"],
  ["Interact", "E"],
  ["Reload", "R"],
  ["Melee", "V"],
  ["Equipment", "Q"],
  ["Scoreboard", "Tab"],
  ["Pause", "Esc"],
];

let timerValue = 9 * 60 + 45;
let scoreboardVisible = true;
let killFeedIndex = 0;

const healthFill = document.getElementById("health-fill");
const armorFill = document.getElementById("armor-fill");
const healthValue = document.getElementById("health-value");
const armorValue = document.getElementById("armor-value");
const timer = document.getElementById("match-timer");
const scoreboardBody = document.getElementById("scoreboard-body");
const killFeedList = document.getElementById("kill-feed-list");
const toggleScoreboard = document.getElementById("toggle-scoreboard");
const pauseMenu = document.getElementById("pause-menu");
const resumeBtn = document.getElementById("resume-btn");
const keybindList = document.getElementById("keybind-list");
const sensRange = document.getElementById("mouse-sens");
const sensReading = document.getElementById("mouse-sens-reading");
const fovRange = document.getElementById("fov");
const fovReading = document.getElementById("fov-reading");
const audioRange = document.getElementById("audio");
const audioReading = document.getElementById("audio-reading");
const browserRegion = document.getElementById("browser-region");
const browserMode = document.getElementById("browser-mode");
const serverEntries = document.getElementById("server-entries");
const refreshServers = document.getElementById("refresh-servers");
const readyToggle = document.getElementById("ready-toggle");
const readyStatus = document.getElementById("ready-status");
const teamSelect = document.getElementById("team-select");
const readyList = document.getElementById("ready-list");
const selectedServer = document.getElementById("selected-server");
const joinBtn = document.getElementById("join-btn");

function clamp(value) {
  return Math.max(0, Math.min(100, value));
}

function renderHUD() {
  const health = clamp(healthValue.textContent);
  const armor = clamp(armorValue.textContent);
  healthFill.style.width = `${health}%`;
  armorFill.style.width = `${armor}%`;
}

function renderTimer() {
  const minutes = String(Math.floor(timerValue / 60)).padStart(2, "0");
  const seconds = String(timerValue % 60).padStart(2, "0");
  timer.textContent = `${minutes}:${seconds}`;
}

function tickTimer() {
  timerValue = Math.max(0, timerValue - 1);
  renderTimer();
}

function renderScoreboard() {
  scoreboardBody.innerHTML = "";
  players
    .slice()
    .sort((a, b) => b.kills - a.kills)
    .forEach((player) => {
      const row = document.createElement("tr");
      row.innerHTML = `<td>${player.name}</td><td>${player.kills}</td><td>${player.deaths}</td><td>${player.ping}ms</td>`;
      scoreboardBody.appendChild(row);
    });
}

function renderKillFeed() {
  killFeedList.innerHTML = "";
  killFeedEvents.slice(-5).forEach((event) => {
    const li = document.createElement("li");
    li.textContent = `${event.killer} eliminated ${event.victim} with ${event.weapon}`;
    killFeedList.appendChild(li);
  });
}

function addKillFeedEvent() {
  const sample = killFeedEvents[killFeedIndex % killFeedEvents.length];
  const next = { ...sample, weapon: ["SMG", "AR", "Laser", "Rail"][killFeedIndex % 4] };
  killFeedEvents.push(next);
  if (killFeedEvents.length > 12) killFeedEvents.shift();
  killFeedIndex += 1;
  renderKillFeed();
}

function renderKeybinds() {
  keybindList.innerHTML = "";
  keybinds.forEach(([action, key]) => {
    const li = document.createElement("li");
    li.textContent = `${action}: ${key}`;
    keybindList.appendChild(li);
  });
}

function updateRangeDisplay(range, label, suffix = "") {
  label.textContent = `${range.value}${suffix}`;
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function generateServers(region, mode) {
  const names = ["Sapphire", "Obsidian", "Aurora", "Monarch", "Harbor", "Summit"];
  return Array.from({ length: 6 }).map((_, idx) => {
    const population = randomInt(2, 16);
    return {
      id: `${region}-${mode}-${idx}`,
      name: `${names[idx]} ${mode}`,
      region,
      ping: randomInt(18, 90),
      players: population,
      capacity: 16,
    };
  });
}

let servers = generateServers(browserRegion.value, browserMode.value);
let lobbyReady = new Map();
let selectedServerId = null;

function renderServers() {
  serverEntries.innerHTML = "";
  servers.forEach((server) => {
    const li = document.createElement("li");
    li.className = "server-card";
    li.innerHTML = `
      <div>
        <strong>${server.name}</strong>
        <small>${server.region}</small>
      </div>
      <div>
        <div>${server.players} / ${server.capacity} players</div>
        <small>${server.ping} ms</small>
      </div>
      <div>
        <button data-id="${server.id}" class="join-server">Select</button>
      </div>
    `;
    serverEntries.appendChild(li);
  });
}

function refreshLobbyList() {
  readyList.innerHTML = "";
  lobbyReady.forEach((state, name) => {
    const li = document.createElement("li");
    li.textContent = `${name} — ${state ? "Ready" : "Not ready"}`;
    li.style.color = state ? "var(--success)" : "var(--warn)";
    readyList.appendChild(li);
  });
}

function setPauseMenu(open) {
  pauseMenu.classList.toggle("hidden", !open);
  if (open) {
    pauseMenu.focus();
  }
}

function selectServer(id) {
  selectedServerId = id;
  const server = servers.find((s) => s.id === id);
  selectedServer.textContent = server ? `${server.name} • ${server.players}/${server.capacity} • ${server.ping}ms` : "No server selected";
  joinBtn.disabled = !server;
}

function mockJoin() {
  if (!selectedServerId) return;
  const team = teamSelect.value;
  lobbyReady.set("You", true);
  lobbyReady.set("Nova", Math.random() > 0.3);
  lobbyReady.set("Rey", Math.random() > 0.3);
  lobbyReady.set("Kael", Math.random() > 0.3);
  refreshLobbyList();
  readyStatus.textContent = `Joined as ${team.toUpperCase()}`;
  readyStatus.style.background = "rgba(63, 185, 80, 0.15)";
  readyStatus.style.borderColor = "var(--success)";
}

function init() {
  renderHUD();
  renderTimer();
  renderScoreboard();
  renderKillFeed();
  renderKeybinds();
  renderServers();
  refreshLobbyList();

  sensRange.addEventListener("input", () => updateRangeDisplay(sensRange, sensReading));
  fovRange.addEventListener("input", () => updateRangeDisplay(fovRange, fovReading, "°"));
  audioRange.addEventListener("input", () => updateRangeDisplay(audioRange, audioReading, "%"));

  toggleScoreboard.addEventListener("click", () => {
    scoreboardVisible = !scoreboardVisible;
    document.querySelector(".scoreboard").style.display = scoreboardVisible ? "block" : "none";
  });

  refreshServers.addEventListener("click", () => {
    servers = generateServers(browserRegion.value, browserMode.value);
    renderServers();
    joinBtn.disabled = true;
    selectedServer.textContent = "No server selected";
  });

  serverEntries.addEventListener("click", (event) => {
    const btn = event.target.closest(".join-server");
    if (!btn) return;
    selectServer(btn.dataset.id);
  });

  readyToggle.addEventListener("change", (event) => {
    const isReady = event.target.checked;
    readyStatus.textContent = isReady ? "Ready" : "Not Ready";
    readyStatus.style.borderColor = isReady ? "var(--success)" : "var(--border)";
    readyStatus.style.background = isReady ? "rgba(63, 185, 80, 0.12)" : "rgba(255, 255, 255, 0.05)";
    lobbyReady.set("You", isReady);
    refreshLobbyList();
  });

  joinBtn.addEventListener("click", mockJoin);
  resumeBtn.addEventListener("click", () => setPauseMenu(false));

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      const opening = pauseMenu.classList.contains("hidden");
      setPauseMenu(opening);
    }
  });

  setInterval(tickTimer, 1000);
  setInterval(addKillFeedEvent, 2000);
}

init();
