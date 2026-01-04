const { WebSocketServer } = require("ws");
const { v4: uuid } = require("uuid");
const {
  MESSAGE_TYPES,
  DEFAULT_TICK_RATE,
  DEFAULT_SNAPSHOT_RATE,
  MAX_HISTORY_MS,
  MAX_PLAYERS,
  budgetedSnapshotRate,
  directionFromInput
} = require("../shared/protocol");

const DEFAULT_PORT = process.env.PORT || 3001;
const HISTORY_LIMIT = 128;
const DEFAULT_MOVE_SPEED = 8;
const DEFAULT_FIRE_RANGE = 50;

function distanceSquared(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return dx * dx + dy * dy;
}

function cloneState(state) {
  return {
    id: state.id,
    position: { ...state.position },
    velocity: { ...state.velocity },
    score: state.score,
    health: state.health,
    lastProcessedInput: state.lastProcessedInput,
    lastAck: state.lastAck,
    lastSeen: state.lastSeen
  };
}

class PlayerState {
  constructor(id) {
    this.id = id;
    this.position = { x: 0, y: 0 };
    this.velocity = { x: 0, y: 0 };
    this.score = 0;
    this.health = 100;
    this.lastProcessedInput = 0;
    this.lastAck = 0;
    this.lastSeen = Date.now();
  }
}

class Simulation {
  constructor({
    tickRate = DEFAULT_TICK_RATE,
    desiredSnapshotRate = DEFAULT_SNAPSHOT_RATE,
    bandwidthKbps = 256,
    port = DEFAULT_PORT
  } = {}) {
    this.tickRate = tickRate;
    this.tickMs = 1000 / tickRate;
    this.desiredSnapshotRate = desiredSnapshotRate;
    this.bandwidthKbps = bandwidthKbps;
    this.snapshotRate = budgetedSnapshotRate({
      playerCount: MAX_PLAYERS,
      bandwidthKbps,
      desiredRate: desiredSnapshotRate
    });
    this.snapshotMs = 1000 / this.snapshotRate;
    this.players = new Map();
    this.history = [];
    this.server = new WebSocketServer({ port });
    this.lastSnapshotAt = 0;
    this.lastBandwidthAudit = 0;
    this._bootstrap();
  }

  _bootstrap() {
    this.server.on("connection", (socket) => {
      const id = uuid();
      const player = new PlayerState(id);
      this.players.set(id, player);
      socket.__id = id;
      socket.send(JSON.stringify({ type: MESSAGE_TYPES.HANDSHAKE, id }));
      socket.on("message", (raw) => this._onMessage(id, raw));
      socket.on("close", () => this._removePlayer(id));
      socket.on("error", () => this._removePlayer(id));
    });

    setInterval(() => this._tick(), this.tickMs);
  }

  _tick() {
    const now = Date.now();
    this._pruneHistory(now);
    this._snapshot(now);
  }

  _pruneHistory(now) {
    while (this.history.length > 0) {
      const tooOld = now - this.history[0].timestamp > MAX_HISTORY_MS;
      const tooLarge = this.history.length > HISTORY_LIMIT;
      if (!tooOld && !tooLarge) break;
      this.history.shift();
    }
  }

  _onMessage(playerId, raw) {
    const player = this.players.get(playerId);
    if (!player) return;
    player.lastSeen = Date.now();

    let payload;
    try {
      payload = JSON.parse(raw);
    } catch (err) {
      return;
    }

    if (payload.type === MESSAGE_TYPES.INPUT) {
      this._applyInput(player, payload);
    } else if (payload.type === MESSAGE_TYPES.FIRE) {
      this._handleFire(player, payload);
    } else if (payload.type === MESSAGE_TYPES.PING) {
      this._send(playerId, { type: MESSAGE_TYPES.PONG, nonce: payload.nonce });
    }
  }

  _applyInput(player, payload) {
    if (payload.sequence <= player.lastProcessedInput) return;
    player.lastProcessedInput = payload.sequence;
    const direction = directionFromInput(payload.input);
    const delta = (payload.dt || 0) / 1000;
    player.velocity.x = direction.x * DEFAULT_MOVE_SPEED;
    player.velocity.y = direction.y * DEFAULT_MOVE_SPEED;
    player.position.x += player.velocity.x * delta;
    player.position.y += player.velocity.y * delta;
    if (payload.input.pickup) {
      this._handlePickup(player);
    }
    player.lastAck = payload.sequence;
  }

  _handlePickup(player) {
    player.score += 1;
    this._send(player.id, { type: MESSAGE_TYPES.PICKUP, score: player.score });
  }

  _handleFire(player, payload) {
    const firedAt = payload.firedAt || Date.now();
    const rewindState = this._rewindState(firedAt);
    const shooterPast = rewindState.get(player.id);
    if (!shooterPast) return;
    const direction = payload.direction || { x: 0, y: 1 };
    const hits = [];
    for (const [targetId, targetState] of rewindState.entries()) {
      if (targetId === player.id || targetState.health <= 0) continue;
      const hit = this._testHitscan(shooterPast, targetState, direction);
      if (hit) {
        hits.push(targetId);
        const liveTarget = this.players.get(targetId);
        if (liveTarget) {
          liveTarget.health -= 25;
          if (liveTarget.health <= 0) {
            player.score += 2;
          }
        }
      }
    }
    this._send(player.id, {
      type: MESSAGE_TYPES.FIRE,
      acknowledgedAt: Date.now(),
      hits
    });
  }

  _testHitscan(shooter, target, direction, range = DEFAULT_FIRE_RANGE) {
    const origin = shooter.position;
    const targetPos = target.position;
    const toTarget = { x: targetPos.x - origin.x, y: targetPos.y - origin.y };
    const distanceToTarget = Math.sqrt(distanceSquared(origin, targetPos));
    if (distanceToTarget > range) return false;
    const directionLength = Math.sqrt(direction.x * direction.x + direction.y * direction.y) || 1;
    const dirUnit = { x: direction.x / directionLength, y: direction.y / directionLength };
    const dot = toTarget.x * dirUnit.x + toTarget.y * dirUnit.y;
    if (dot < 0) return false;
    const projection = { x: dirUnit.x * dot, y: dirUnit.y * dot };
    const perpendicular = {
      x: toTarget.x - projection.x,
      y: toTarget.y - projection.y
    };
    const missRadiusSq = distanceSquared({ x: 0, y: 0 }, perpendicular);
    return missRadiusSq <= 1;
  }

  _rewindState(targetTimestamp) {
    const rewind = new Map();
    let closest = this.history[this.history.length - 1];
    for (let i = this.history.length - 1; i >= 0; i -= 1) {
      const entry = this.history[i];
      if (!closest || Math.abs(entry.timestamp - targetTimestamp) < Math.abs(closest.timestamp - targetTimestamp)) {
        closest = entry;
      }
      if (entry.timestamp <= targetTimestamp) break;
    }
    if (closest) {
      for (const [id, state] of closest.snapshot.entries()) {
        rewind.set(id, cloneState(state));
      }
    } else {
      for (const [id, state] of this.players.entries()) {
        rewind.set(id, cloneState(state));
      }
    }
    return rewind;
  }

  _snapshot(now) {
    if (now - this.lastSnapshotAt < this.snapshotMs) return;
    this.lastSnapshotAt = now;
    const snapshot = [];
    for (const [id, state] of this.players.entries()) {
      snapshot.push({
        id,
        position: state.position,
        velocity: state.velocity,
        score: state.score,
        health: state.health,
        lastAck: state.lastAck
      });
    }
    const historySnapshot = new Map();
    for (const [id, state] of this.players.entries()) {
      historySnapshot.set(id, cloneState(state));
    }
    this.history.push({ timestamp: now, snapshot: historySnapshot });
    if (this.history.length > HISTORY_LIMIT || now - this.history[0].timestamp > MAX_HISTORY_MS) {
      this.history.shift();
    }
    this._broadcast({ type: MESSAGE_TYPES.SNAPSHOT, at: now, players: snapshot });
    if (now - this.lastBandwidthAudit > 1000) {
      this._auditBandwidth();
      this.lastBandwidthAudit = now;
    }
  }

  _auditBandwidth() {
    const nextRate = budgetedSnapshotRate({
      playerCount: this.players.size || 1,
      bandwidthKbps: this.bandwidthKbps,
      desiredRate: this.desiredSnapshotRate
    });
    if (nextRate !== this.snapshotRate) {
      this.snapshotRate = nextRate;
      this.snapshotMs = 1000 / this.snapshotRate;
    }
  }

  _send(playerId, message) {
    for (const client of this.server.clients) {
      if (client.readyState !== client.OPEN) continue;
      if (client.__id === playerId) {
        client.send(JSON.stringify(message));
      }
    }
  }

  _broadcast(message) {
    const serialized = JSON.stringify(message);
    for (const client of this.server.clients) {
      if (client.readyState !== client.OPEN) continue;
      client.send(serialized);
    }
  }

  _removePlayer(id) {
    this.players.delete(id);
  }
}

function start() {
  const simulation = new Simulation();
  // eslint-disable-next-line no-console
  console.log(
    `Authoritative server listening on ${DEFAULT_PORT} | tick=${DEFAULT_TICK_RATE}hz | snapshots=${DEFAULT_SNAPSHOT_RATE}hz (budgeted=${simulation.snapshotRate}hz)`
  );
  return simulation;
}

if (require.main === module) {
  start();
}

module.exports = { Simulation, start };
