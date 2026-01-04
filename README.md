## Shiz and Giggles Dedicated Server

This repository provides a small dedicated server skeleton with:

- CLI-driven server configuration (map rotation, player limit, tick rate, password, region).
- Optional matchmaking/public server list via a lightweight HTTP backend.
- Basic anti-cheat protections (password validation, message size validation, per-client rate limits).
- Periodic logging/metrics to track server health.

### Running the dedicated server

```bash
python main.py server \
  --host 0.0.0.0 \
  --port 7777 \
  --maps arena ascent sewers \
  --player-limit 24 \
  --tick-rate 60 \
  --password secret \
  --region na-east \
  --matchmaking-endpoint http://localhost:8080
```

Flags:

- `--maps`: Map rotation list. The server cycles maps over time and reports the active map to joining clients.
- `--player-limit`: Maximum concurrent players.
- `--tick-rate`: Simulation tick rate in Hz.
- `--password`: Optional password required on join. Omit to allow open access.
- `--region`: Region label advertised to matchmaking.
- `--matchmaking-endpoint`: When provided, the server registers itself every 30 seconds to the backend. Pair with `--matchmaking-api-key` if the backend requires it.
- `--metrics-interval`: Frequency (seconds) to log the current metrics snapshot.
- `--rate-limit`: Per-client messages per second before rate limiting responses are returned.
- `--max-message-size`: Maximum accepted inbound message size in bytes.

Clients connect via TCP and must send a single-line JSON blob to join:

```json
{"player_id": "alice", "password": "secret"}
```

Subsequent messages support `{"action": "ping"}` and `{"action": "rotate_map"}` for exercising the pipeline. Unknown or oversized messages are rejected.

### Matchmaking/public server list backend

Run a lightweight HTTP backend that maintains a public server list with TTL-based expiry:

```bash
python main.py matchmaking-backend --host 0.0.0.0 --port 8080
```

Endpoints:

- `POST /register` with JSON: `{"address":"1.2.3.4","port":7777,"region":"na-east","max_players":24,"map_name":"arena","tick_rate":60}`
- `GET /servers` to retrieve the active list. Servers expire if not refreshed within 120 seconds.

### Anti-cheat and validation

- Password validation guards access when configured.
- Message size validation drops oversized payloads before processing.
- Per-client token-bucket rate limiting throttles spam and increments metrics for rejected messages.
- The server runs authoritative command processing and rotates maps only server-side to avoid client-controlled state changes.

### Metrics and logging

- Metrics counters track joins, rejections, pings, map rotations, matchmaking registrations, and tick counts.
- The metrics logger runs in a background thread at the interval specified by `--metrics-interval`.
