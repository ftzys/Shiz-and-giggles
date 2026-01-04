import asyncio
import json
import logging
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from server.anti_cheat import AntiCheat
from server.config import ServerConfig
from server.matchmaking import MatchmakingClient
from server.metrics import Metrics


@dataclass
class PlayerSession:
    player_id: str
    writer: StreamWriter
    rate_limit_label: str


@dataclass
class ServerState:
    config: ServerConfig
    current_map_index: int = 0
    players: Dict[str, PlayerSession] = field(default_factory=dict)

    @property
    def current_map(self) -> str:
        return self.config.maps[self.current_map_index % len(self.config.maps)]

    def rotate_map(self) -> None:
        self.current_map_index = (self.current_map_index + 1) % len(self.config.maps)

    def has_capacity(self) -> bool:
        return len(self.players) < self.config.player_limit


class GameServer:
    """
    Simple TCP-based authoritative server loop with matchmaking hooks.
    """

    def __init__(self, config: ServerConfig, metrics: Metrics):
        self.config = config
        self.metrics = metrics
        self.state = ServerState(config=config)
        self.matchmaking_client: Optional[MatchmakingClient] = None
        if config.matchmaking_endpoint:
            self.matchmaking_client = MatchmakingClient(
                config.matchmaking_endpoint, api_key=config.matchmaking_api_key
            )
        self.anti_cheat = AntiCheat(
            metrics=metrics, rate_limit_per_second=config.rate_limit_per_second, max_message_size=config.max_message_size
        )
        self._server: Optional[asyncio.AbstractServer] = None
        self._tick_task: Optional[asyncio.Task] = None
        self._matchmaking_task: Optional[asyncio.Task] = None

    async def start(self):
        self._server = await asyncio.start_server(self._handle_client, host=self.config.host, port=self.config.port)
        self._tick_task = asyncio.create_task(self._tick_loop())
        if self.matchmaking_client:
            self._matchmaking_task = asyncio.create_task(self._matchmaking_loop())
        logging.info("server started on %s:%s [%s]", self.config.host, self.config.port, self.config.region)

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if self._tick_task:
            self._tick_task.cancel()
        if self._matchmaking_task:
            self._matchmaking_task.cancel()
        logging.info("server stopped")

    async def _matchmaking_loop(self):
        assert self.matchmaking_client
        while True:
            success = self.matchmaking_client.register_server(
                address=self.config.host,
                port=self.config.port,
                region=self.config.region,
                max_players=self.config.player_limit,
                map_name=self.state.current_map,
                tick_rate=self.config.tick_rate,
            )
            self.metrics.increment("matchmaking_register_attempts")
            if success:
                self.metrics.increment("matchmaking_register_success")
            await asyncio.sleep(30)

    async def _tick_loop(self):
        tick_interval = 1 / self.config.tick_rate
        while True:
            await asyncio.sleep(tick_interval)
            # Here you'd run simulation logic. We only rotate maps every 3 minutes.
            if self.state.players and self.metrics.snapshot().get("ticks", 0) % (self.config.tick_rate * 180) == 0:
                self.state.rotate_map()
                logging.info("rotated to next map: %s", self.state.current_map)
            self.metrics.increment("ticks")

    async def _handle_client(self, reader: StreamReader, writer: StreamWriter):
        peername = writer.get_extra_info("peername")
        client_id = f"{peername[0]}:{peername[1]}"
        logging.info("connection from %s", client_id)
        self.metrics.increment("connections_opened")

        if not self.state.has_capacity():
            writer.write(b"server full\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            self.metrics.increment("connections_rejected_full")
            return

        try:
            join_message = await reader.readline()
            if not self.anti_cheat.validate_message_size(join_message):
                writer.write(b"message too large\n")
                await writer.drain()
                return
            try:
                payload = json.loads(join_message.decode())
            except json.JSONDecodeError:
                writer.write(b"invalid join payload\n")
                await writer.drain()
                self.metrics.increment("connections_rejected_invalid")
                return

            player_id = payload.get("player_id") or client_id
            supplied_password = payload.get("password", "")
            if not self.anti_cheat.validate_password(supplied_password, self.config.password):
                writer.write(b"invalid password\n")
                await writer.drain()
                self.metrics.increment("connections_rejected_auth")
                return

            session = PlayerSession(player_id=player_id, writer=writer, rate_limit_label=client_id)
            self.state.players[player_id] = session
            self.metrics.increment("players_joined")
            writer.write(
                json.dumps({"status": "ok", "map": self.state.current_map, "tick_rate": self.config.tick_rate}).encode()
                + b"\n"
            )
            await writer.drain()

            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                if not self.anti_cheat.validate_message_size(line):
                    writer.write(b"message too large\n")
                    await writer.drain()
                    continue
                if not self.anti_cheat.allow_message(client_id):
                    writer.write(b"rate limited\n")
                    await writer.drain()
                    continue
                try:
                    message = json.loads(line.decode())
                except json.JSONDecodeError:
                    writer.write(b"invalid message\n")
                    await writer.drain()
                    self.metrics.increment("messages_rejected_parse")
                    continue
                await self._process_message(session, message)
        finally:
            self.state.players.pop(client_id, None)
            writer.close()
            await writer.wait_closed()
            self.metrics.increment("connections_closed")
            logging.info("connection closed: %s", client_id)

    async def _process_message(self, session: PlayerSession, message: dict):
        action = message.get("action")
        if action == "ping":
            session.writer.write(b'{"action":"pong"}\n')
            await session.writer.drain()
            self.metrics.increment("pings")
        elif action == "rotate_map":
            self.state.rotate_map()
            session.writer.write(json.dumps({"map": self.state.current_map}).encode() + b"\n")
            await session.writer.drain()
            self.metrics.increment("map_rotations_manual")
        else:
            session.writer.write(b'{"error":"unknown action"}\n')
            await session.writer.drain()
            self.metrics.increment("messages_rejected_unknown")
