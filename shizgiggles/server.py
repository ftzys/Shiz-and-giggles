from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Dict

from shizgiggles.logic import WorldState
from shizgiggles.protocol import Message, MessageType

logger = logging.getLogger(__name__)


class GameServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self.world = WorldState()
        self._clients: Dict[str, asyncio.StreamWriter] = {}
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, self.host, self.port)
        logger.info("Server listening on %s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Server stopped")

    async def broadcast_snapshot(self) -> None:
        snapshot = {
            pid: {"position": player.position, "health": player.health, "ammo": player.ammo}
            for pid, player in self.world.players.items()
        }
        message = Message(type=MessageType.SNAPSHOT, player_id="server", payload=snapshot).to_json() + "\n"
        for writer in list(self._clients.values()):
            try:
                writer.write(message.encode())
                await writer.drain()
            except ConnectionResetError:
                continue

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peername = writer.get_extra_info("peername")
        logger.info("Connection from %s", peername)
        player_id = None
        while True:
            raw = await reader.readline()
            if not raw:
                if player_id and player_id in self._clients:
                    del self._clients[player_id]
                writer.close()
                await writer.wait_closed()
                logger.info("Disconnected %s", peername)
                return
            message = Message.from_json(raw.decode())
            if message.type == MessageType.JOIN:
                player_id = message.player_id
                self._clients[player_id] = writer
                self.world.ensure_player(player_id)
                await self.broadcast_snapshot()
            elif message.type == MessageType.MOVE:
                delta = (float(message.payload.get("dx", 0)), float(message.payload.get("dy", 0)))
                self.world.move_player(message.player_id, delta)
                await self.broadcast_snapshot()
            elif message.type == MessageType.FIRE:
                self.world.fire_weapon(message.player_id)
                await self.broadcast_snapshot()
            elif message.type == MessageType.PING:
                writer.write((Message.ping("server").to_json() + "\n").encode())
                await writer.drain()


async def run_server(host: str, port: int) -> None:
    server = GameServer(host, port)
    await server.start()
    try:
        while True:
            await asyncio.sleep(0.1)
            server.world.step()
            if server.world.tick % 10 == 0:
                await server.broadcast_snapshot()
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Shiz-and-giggles dedicated server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="[%(asctime)s] %(levelname)s %(message)s")
    asyncio.run(run_server(args.host, args.port))


if __name__ == "__main__":
    main()
