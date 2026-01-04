const WebSocket = require("ws");
const {
  MESSAGE_TYPES,
  DEFAULT_TICK_RATE,
  DEFAULT_SNAPSHOT_RATE,
  MAX_HISTORY_MS,
  directionFromInput
} = require("../shared/protocol");

class RemotePlayerBuffer {
  constructor(bufferMs = 100) {
    this.bufferMs = bufferMs;
    this.frames = [];
  }

  push(frame) {
    this.frames.push(frame);
    const cutoff = Date.now() - this.bufferMs;
    this.frames = this.frames.filter((entry) => entry.timestamp >= cutoff);
  }

  interpolate(renderTime) {
    const frames = [...this.frames].sort((a, b) => a.timestamp - b.timestamp);
    if (frames.length === 0) return null;
    if (frames.length === 1 || renderTime <= frames[0].timestamp) return frames[0];
    for (let i = 0; i < frames.length - 1; i += 1) {
      const current = frames[i];
      const next = frames[i + 1];
      if (renderTime >= current.timestamp && renderTime <= next.timestamp) {
        const t = (renderTime - current.timestamp) / (next.timestamp - current.timestamp);
        return {
          timestamp: renderTime,
          position: {
            x: current.position.x + (next.position.x - current.position.x) * t,
            y: current.position.y + (next.position.y - current.position.y) * t
          },
          velocity: next.velocity,
          id: current.id
        };
      }
    }
    return frames[frames.length - 1];
  }
}

class GameClient {
  constructor({
    url = "ws://localhost:3001",
    tickRate = DEFAULT_TICK_RATE,
    snapshotRate = DEFAULT_SNAPSHOT_RATE,
    interpolationBufferMs = 100
  } = {}) {
    this.url = url;
    this.socket = null;
    this.playerId = null;
    this.localState = {
      position: { x: 0, y: 0 },
      velocity: { x: 0, y: 0 },
      score: 0
    };
    this.remotePlayers = new Map();
    this.pendingInputs = [];
    this.lastInputSequence = 0;
    this.tickMs = 1000 / tickRate;
    this.snapshotRate = snapshotRate;
    this.interpolationBufferMs = interpolationBufferMs;
    this.latencyMs = 0;
  }

  connect() {
    this.socket = new WebSocket(this.url);
    this.socket.on("open", () => {
      this._startLoops();
    });
    this.socket.on("message", (raw) => this._handleMessage(raw));
    this.socket.on("close", () => this._stopLoops());
    this.socket.on("error", () => this._stopLoops());
  }

  queueInput(input, dt = this.tickMs) {
    const sequence = ++this.lastInputSequence;
    const payload = {
      type: MESSAGE_TYPES.INPUT,
      sequence,
      dt,
      input,
      timestamp: Date.now()
    };
    this.pendingInputs.push(payload);
    this._applyPrediction(input, dt);
    this._send(payload);
  }

  fire(direction) {
    const payload = {
      type: MESSAGE_TYPES.FIRE,
      direction,
      firedAt: Date.now() - this.latencyMs / 2
    };
    this._send(payload);
  }

  _applyPrediction(input, dt) {
    const direction = directionFromInput(input);
    const speed = input.speed || 8;
    this.localState.velocity.x = direction.x * speed;
    this.localState.velocity.y = direction.y * speed;
    const delta = dt / 1000;
    this.localState.position.x += this.localState.velocity.x * delta;
    this.localState.position.y += this.localState.velocity.y * delta;
  }

  _handleMessage(raw) {
    let message;
    try {
      message = JSON.parse(raw);
    } catch (err) {
      return;
    }
    switch (message.type) {
      case MESSAGE_TYPES.HANDSHAKE:
        this.playerId = message.id;
        break;
      case MESSAGE_TYPES.SNAPSHOT:
        this._ingestSnapshot(message);
        break;
      case MESSAGE_TYPES.FIRE:
        this._handleFireAck(message);
        break;
      case MESSAGE_TYPES.PONG:
        this.latencyMs = Date.now() - message.nonce;
        break;
      default:
        break;
    }
  }

  _ingestSnapshot(snapshot) {
    const renderDelay = this.interpolationBufferMs + this.latencyMs + snapshot.at - Date.now();
    const renderTime = Date.now() - renderDelay;
    snapshot.players.forEach((player) => {
      if (player.id === this.playerId) {
        this._reconcile(player);
      } else {
        if (!this.remotePlayers.has(player.id)) {
          this.remotePlayers.set(player.id, new RemotePlayerBuffer(this.interpolationBufferMs));
        }
        this.remotePlayers.get(player.id).push({
          id: player.id,
          timestamp: snapshot.at,
          position: player.position,
          velocity: player.velocity
        });
      }
    });
    this.remotePlayers.forEach((buffer, id) => {
      if (!snapshot.players.find((p) => p.id === id)) {
        this.remotePlayers.delete(id);
      }
    });
    this.renderedRemoteStates = [...this.remotePlayers.values()].map((buffer) => buffer.interpolate(renderTime));
  }

  _reconcile(authoritative) {
    this.localState.position = authoritative.position;
    this.localState.velocity = authoritative.velocity;
    this.localState.score = authoritative.score;
    this.pendingInputs = this.pendingInputs.filter((input) => input.sequence > authoritative.lastAck);
    this.pendingInputs.forEach((input) => this._applyPrediction(input.input, input.dt));
  }

  _handleFireAck(message) {
    // could update tracers, sound, etc. Here we simply log acknowledged hits.
    // eslint-disable-next-line no-console
    console.log(`Server confirmed hits: ${message.hits.join(", ") || "none"}`);
  }

  _startLoops() {
    this.tickInterval = setInterval(() => this._send({ type: MESSAGE_TYPES.PING, nonce: Date.now() }), 1000);
    this.snapshotInterval = setInterval(() => this._requestSnapshot(), 1000 / this.snapshotRate);
  }

  _requestSnapshot() {
    // Clients do not request snapshots directly; this hook is kept to show predictable pacing for interpolation calculations.
  }

  _stopLoops() {
    clearInterval(this.tickInterval);
    clearInterval(this.snapshotInterval);
  }

  _send(payload) {
    if (!this.socket || this.socket.readyState !== this.socket.OPEN) return;
    this.socket.send(JSON.stringify(payload));
  }
}

if (require.main === module) {
  const client = new GameClient();
  client.connect();
  setInterval(() => {
    client.queueInput({ forward: 1 });
  }, 100);
}

module.exports = { GameClient };
