## Shiz and Giggles – Netcode scaffolding

This repository contains a lightweight authoritative server and matching client scaffolding for a 16-player arcade-style session. The server owns movement, hitscan firing, pickups, and scoring. Clients use prediction, reconciliation, interpolation, and lag-compensated firing (rewind) to hide latency while staying in sync.

### Features

- **Authoritative server**: Movement, pickups, and scoring are all resolved on the server; clients send intent only.
- **Client-side prediction + reconciliation**: Clients apply their own inputs immediately and roll back to server snapshots when acknowledgements arrive.
- **Lag compensation**: Hitscan shots include the client firing timestamp; the server rewinds to the closest historical snapshot to evaluate hits.
- **Interpolation for remote players**: Remote entities are buffered and interpolated to produce smooth motion despite snapshot pacing.
- **Snapshot controls and bandwidth budgeting**: Desired snapshot rate is clamped by a bandwidth budget sized for up to 16 players; the server adapts the rate in real time if the player count changes.

### Structure

- `src/shared/protocol.js` – Message types, defaults, and helpers for budgeting and movement.
- `src/server/index.js` – Authoritative WebSocket server, simulation loop, hit-rewind, snapshotting, and scoring.
- `src/client/index.js` – Client with prediction, reconciliation, remote interpolation, and lag-compensated firing timestamps.

### Running locally

1) Install dependencies (Node 18+ is required):

```bash
npm install
```

2) Start the server:

```bash
npm run server
```

3) Connect a client (headless demo will move forward continuously):

```bash
npm run client
```

### Configuration

- Tick rate: `DEFAULT_TICK_RATE` in `protocol.js` (server simulation rate and client input cadence).
- Snapshot rate: `DEFAULT_SNAPSHOT_RATE` in `protocol.js`; automatically clamped by `budgetedSnapshotRate` for 16 players and the configured bandwidth budget (default 256 kbps).
- History/rewind: `MAX_HISTORY_MS` and `HISTORY_LIMIT` in `src/server/index.js` control the window used for lag-compensated hitscan.
- Movement and hitscan tuning: `DEFAULT_MOVE_SPEED` and `DEFAULT_FIRE_RANGE` in `src/server/index.js`.

### Notes

- The included `npm install` may be blocked in some environments; if so, mirror or vendor the `ws` and `uuid` dependencies or run in a networked environment.
- The scaffolding is intentionally small: integrate the classes into your engine loop and replace the placeholder collision logic to match your game.
