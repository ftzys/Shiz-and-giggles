const DEFAULT_TICK_RATE = 60;
const DEFAULT_SNAPSHOT_RATE = 20;
const MAX_PLAYERS = 16;
const MAX_HISTORY_MS = 1500;

const MESSAGE_TYPES = Object.freeze({
  HANDSHAKE: "handshake",
  INPUT: "input",
  SNAPSHOT: "snapshot",
  SCORE: "score",
  PICKUP: "pickup",
  ACK: "ack",
  PING: "ping",
  PONG: "pong",
  FIRE: "fire"
});

function estimateSnapshotBytes(playerCount = MAX_PLAYERS) {
  const headerBytes = 32;
  const perPlayerBytes = 48;
  const scoreBytes = 8;
  return headerBytes + playerCount * (perPlayerBytes + scoreBytes);
}

function budgetedSnapshotRate({ playerCount = MAX_PLAYERS, bandwidthKbps = 256, desiredRate = DEFAULT_SNAPSHOT_RATE }) {
  const snapshotBytes = estimateSnapshotBytes(playerCount);
  const snapshotBits = snapshotBytes * 8;
  const availableBitsPerSecond = bandwidthKbps * 1000;
  const maxSnapshotsPerSecond = Math.max(1, Math.floor(availableBitsPerSecond / snapshotBits));
  return Math.min(desiredRate, maxSnapshotsPerSecond);
}

function clamp01(value) {
  return Math.min(1, Math.max(0, value));
}

function directionFromInput(input) {
  const x = clamp01(input.right) - clamp01(input.left);
  const y = clamp01(input.forward) - clamp01(input.backward);
  return { x, y };
}

module.exports = {
  MESSAGE_TYPES,
  DEFAULT_TICK_RATE,
  DEFAULT_SNAPSHOT_RATE,
  MAX_PLAYERS,
  MAX_HISTORY_MS,
  estimateSnapshotBytes,
  budgetedSnapshotRate,
  clamp01,
  directionFromInput
};
