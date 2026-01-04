const weaponPool = ["SMG", "CARV", "Rocket", "Rail", "Shotgun", "Lightning"];

let players = [
  { name: "You", kills: 11, deaths: 5, ping: 32 },
  { name: "Avery", kills: 12, deaths: 6, ping: 34 },
  { name: "Nova", kills: 9, deaths: 8, ping: 48 },
  { name: "Rey", kills: 8, deaths: 10, ping: 52 },
  { name: "Kael", kills: 6, deaths: 11, ping: 61 },
];

let killFeedEvents = [
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
let matchEnded = false;
let currentLeader = null;

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
const vfxLayer = document.getElementById("vfx-layer");
const hitMarker = document.getElementById("hit-marker");
const killBanner = document.getElementById("kill-banner");
const announcerCallout = document.getElementById("announcer-callout");

function clamp(value) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function randomInRange(min, max) {
  return Math.random() * (max - min) + min;
}

function randomChoice(list) {
  return list[Math.floor(Math.random() * list.length)];
}

class AudioManager {
  constructor() {
    this.ctx = null;
    this.unlocked = false;
  }

  unlock = async () => {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (this.ctx.state === "suspended") {
      await this.ctx.resume();
    }
    this.unlocked = true;
  };

  playTone(freq = 440, duration = 0.12, volume = 0.2, type = "square") {
    if (!this.unlocked) return;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.value = volume;
    osc.connect(gain).connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  playStep(sprinting = false) {
    this.playTone(sprinting ? 110 : 90, 0.08, 0.2, "sine");
  }

  playWeapon(kind = "rifle") {
    if (kind === "rocket") {
      this.playTone(160, 0.25, 0.25, "sawtooth");
      this.playTone(90, 0.35, 0.18, "square");
    } else {
      this.playTone(280, 0.08, 0.22, "triangle");
      this.playTone(140, 0.12, 0.18, "square");
    }
  }

  playAnnouncer(kind) {
    if (!this.unlocked) return;
    const tones = {
      spawn: [320, 420],
      lead: [520, 320],
      match_end: [240, 180, 140],
    };
    (tones[kind] || [400]).forEach((freq, idx) => {
      setTimeout(() => this.playTone(freq, 0.18, 0.2, "sine"), idx * 90);
    });
  }

  playHitConfirm() {
    this.playTone(660, 0.08, 0.22, "triangle");
  }

  playKillConfirm() {
    this.playTone(520, 0.1, 0.25, "sine");
    this.playTone(720, 0.1, 0.18, "triangle");
  }
}

const audio = new AudioManager();

const inputState = {
  keys: new Set(),
  moving: false,
  sprint: false,
  zoomed: false,
  footstepTimer: null,
};

const viewState = {
  bobPhase: 0,
  recoil: 0,
  fov: 1,
  targetFov: 1,
  lastTime: performance.now(),
};

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

function renderScoreboard() {
  scoreboardBody.innerHTML = "";
  const sorted = players.slice().sort((a, b) => b.kills - a.kills);
  sorted.forEach((player) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${player.name}</td><td>${player.kills}</td><td>${player.deaths}</td><td>${player.ping}ms</td>`;
    scoreboardBody.appendChild(row);
  });
  const leader = sorted[0]?.name || null;
  if (leader && leader !== currentLeader && leader === "You") {
    showAnnouncer("Lead Taken");
    audio.playAnnouncer("lead");
  }
  currentLeader = leader;
}

function renderKillFeed() {
  killFeedList.innerHTML = "";
  killFeedEvents.slice(-5).forEach((event) => {
    const li = document.createElement("li");
    li.textContent = `${event.killer} eliminated ${event.victim} with ${event.weapon}`;
    killFeedList.appendChild(li);
  });
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

function tickTimer() {
  timerValue = Math.max(0, timerValue - 1);
  renderTimer();
  if (timerValue === 0 && !matchEnded) {
    matchEnded = true;
    showAnnouncer("Match Over");
    audio.playAnnouncer("match_end");
  }
}

function randomImpactPoint() {
  return {
    x: window.innerWidth / 2 + randomInRange(-60, 60),
    y: window.innerHeight / 2 + randomInRange(-60, 60),
  };
}

function spawnMuzzleFlash(kind = "rifle") {
  const flash = document.createElement("div");
  flash.className = `muzzle-flash ${kind === "rocket" ? "rocket" : ""}`;
  const baseX = window.innerWidth * 0.68;
  const baseY = window.innerHeight * 0.75;
  flash.style.left = `${baseX + randomInRange(-16, 16)}px`;
  flash.style.top = `${baseY + randomInRange(-10, 8)}px`;
  vfxLayer.appendChild(flash);
  setTimeout(() => flash.remove(), 220);
}

function spawnTracer(angle = 0) {
  const tracer = document.createElement("div");
  tracer.className = "tracer";
  tracer.style.left = `${window.innerWidth / 2}px`;
  tracer.style.top = `${window.innerHeight / 2}px`;
  tracer.style.transform = `rotate(${angle}deg)`;
  vfxLayer.appendChild(tracer);
  setTimeout(() => tracer.remove(), 260);
}

function spawnImpact(x, y) {
  const impact = document.createElement("div");
  impact.className = "impact";
  impact.style.left = `${x}px`;
  impact.style.top = `${y}px`;
  vfxLayer.appendChild(impact);
  setTimeout(() => impact.remove(), 620);
}

function spawnRocketTrail(angle = 0) {
  const trail = document.createElement("div");
  trail.className = "rocket-trail";
  trail.style.left = `${window.innerWidth * 0.55}px`;
  trail.style.top = `${window.innerHeight * 0.62}px`;
  trail.style.transform = `rotate(${angle}deg)`;
  vfxLayer.appendChild(trail);
  setTimeout(() => trail.remove(), 520);
}

function showHitMarker() {
  hitMarker.classList.add("active");
  audio.playHitConfirm();
  setTimeout(() => hitMarker.classList.remove("active"), 140);
}

function showKillBanner(text) {
  killBanner.textContent = text;
  killBanner.classList.add("active");
  audio.playKillConfirm();
  setTimeout(() => killBanner.classList.remove("active"), 900);
}

function showAnnouncer(text) {
  announcerCallout.textContent = text;
  announcerCallout.classList.add("active");
  setTimeout(() => announcerCallout.classList.remove("active"), 1000);
}

function applyKillOutcome({ killer, victim }) {
  const killerEntry = players.find((p) => p.name === killer);
  const victimEntry = players.find((p) => p.name === victim);
  if (killerEntry) killerEntry.kills += 1;
  if (victimEntry) victimEntry.deaths += 1;
  if (!killerEntry) {
    players.push({ name: killer, kills: 1, deaths: 0, ping: 45 });
  }
  if (!victimEntry) {
    players.push({ name: victim, kills: 0, deaths: 1, ping: 55 });
  }
  renderScoreboard();
  if (killer === "You") {
    showKillBanner("Kill confirmed");
  }
}

function pushKillEvent(event) {
  killFeedEvents.push(event);
  if (killFeedEvents.length > 12) killFeedEvents.shift();
  renderKillFeed();
  applyKillOutcome(event);
}

function addKillFeedEvent() {
  const roster = players.map((p) => p.name);
  const killer = Math.random() > 0.35 ? randomChoice(roster) : "You";
  let victim = randomChoice(roster.filter((p) => p !== killer));
  if (!victim) {
    victim = killer === "You" ? "Avery" : "You";
  }
  const weapon = weaponPool[killFeedIndex % weaponPool.length];
  const event = { killer, victim, weapon };
  killFeedIndex += 1;
  pushKillEvent(event);
}

function simulateHitFromShot(mode) {
  const willHit = Math.random() > (mode === "rocket" ? 0.35 : 0.15);
  if (!willHit) return;
  const { x, y } = randomImpactPoint();
  spawnImpact(x, y);
  showHitMarker();
  const willKill = Math.random() > (mode === "rocket" ? 0.55 : 0.75);
  if (willKill) {
    const potentialVictims = players.filter((p) => p.name !== "You");
    const victimName = (randomChoice(potentialVictims) || { name: "Target" }).name;
    pushKillEvent({ killer: "You", victim: victimName, weapon: mode === "rocket" ? "Rocket" : "SMG" });
  }
}

function fireWeapon(mode = "hitscan") {
  spawnMuzzleFlash(mode === "rocket" ? "rocket" : "rifle");
  audio.playWeapon(mode === "rocket" ? "rocket" : "rifle");
  const angle = randomInRange(-4, 4);
  if (mode === "rocket") {
    spawnRocketTrail(angle);
    setTimeout(() => simulateHitFromShot(mode), 160);
  } else {
    spawnTracer(angle);
    simulateHitFromShot(mode);
  }
  viewState.recoil = Math.min(viewState.recoil + (mode === "rocket" ? 9 : 4), 12);
}

function setPauseMenu(open) {
  pauseMenu.classList.toggle("hidden", !open);
  if (open) {
    pauseMenu.focus();
  }
}

function startFootsteps() {
  if (inputState.footstepTimer) return;
  const interval = inputState.sprint ? 320 : 440;
  inputState.footstepTimer = setInterval(() => audio.playStep(inputState.sprint), interval);
}

function stopFootsteps() {
  if (inputState.footstepTimer) {
    clearInterval(inputState.footstepTimer);
    inputState.footstepTimer = null;
  }
}

function refreshFovTarget() {
  if (inputState.zoomed) {
    viewState.targetFov = 0.92;
  } else if (inputState.sprint) {
    viewState.targetFov = 1.06;
  } else {
    viewState.targetFov = 1;
  }
}

function updateMovementState() {
  const moving = ["w", "a", "s", "d"].some((key) => inputState.keys.has(key));
  if (moving && !inputState.moving) startFootsteps();
  if (!moving) stopFootsteps();
  inputState.moving = moving;
  refreshFovTarget();
}

function updateView(now) {
  const dt = (now - viewState.lastTime) / 1000;
  viewState.lastTime = now;
  if (inputState.moving) {
    viewState.bobPhase += dt * (inputState.sprint ? 12 : 7);
  } else {
    viewState.bobPhase *= 0.92;
  }
  const bobX = Math.cos(viewState.bobPhase * 2) * (inputState.moving ? (inputState.sprint ? 4 : 2.5) : 0);
  const bobY = Math.sin(viewState.bobPhase) * (inputState.moving ? (inputState.sprint ? 6 : 3.5) : 0);
  viewState.recoil *= 0.9;
  viewState.fov += (viewState.targetFov - viewState.fov) * 0.12;

  document.documentElement.style.setProperty("--view-x", `${bobX}px`);
  document.documentElement.style.setProperty("--view-y", `${bobY - viewState.recoil}px`);
  document.documentElement.style.setProperty("--view-tilt", `${bobX * 0.2}deg`);
  document.documentElement.style.setProperty("--fov-scale", viewState.fov.toFixed(3));

  requestAnimationFrame(updateView);
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
  showAnnouncer("Spawned");
  audio.playAnnouncer("spawn");
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
      return;
    }
    audio.unlock();
    const key = event.key.toLowerCase();
    if (["w", "a", "s", "d"].includes(key)) {
      inputState.keys.add(key);
      updateMovementState();
    }
    if (event.key === "Shift") {
      inputState.sprint = true;
      refreshFovTarget();
      if (inputState.moving) {
        stopFootsteps();
        startFootsteps();
      }
    }
    if (event.key === "z") {
      inputState.zoomed = true;
      refreshFovTarget();
    }
  });

  document.addEventListener("keyup", (event) => {
    const key = event.key.toLowerCase();
    if (["w", "a", "s", "d"].includes(key)) {
      inputState.keys.delete(key);
      updateMovementState();
    }
    if (event.key === "Shift") {
      inputState.sprint = false;
      refreshFovTarget();
      if (inputState.moving) {
        stopFootsteps();
        startFootsteps();
      }
    }
    if (event.key === "z") {
      inputState.zoomed = false;
      refreshFovTarget();
    }
  });

  document.addEventListener("mousedown", (event) => {
    audio.unlock();
    if (event.button === 0) {
      fireWeapon("hitscan");
    } else if (event.button === 2) {
      event.preventDefault();
      inputState.zoomed = true;
      refreshFovTarget();
      fireWeapon("rocket");
    }
  });

  document.addEventListener("mouseup", (event) => {
    if (event.button === 2) {
      inputState.zoomed = false;
      refreshFovTarget();
    }
  });

  document.addEventListener("contextmenu", (event) => event.preventDefault());

  setInterval(tickTimer, 1000);
  setInterval(addKillFeedEvent, 2200);
  requestAnimationFrame(updateView);

  setTimeout(() => {
    showAnnouncer("Spawned");
    audio.playAnnouncer("spawn");
  }, 450);
}

init();
