import asyncio
import json

from server.config import ServerConfig
from server.game_server import GameServer
from server.metrics import Metrics


def test_player_session_removed_on_disconnect():
    async def run():
        config = ServerConfig(host="127.0.0.1", port=0, maps=["arena"])
        metrics = Metrics()
        server = GameServer(config=config, metrics=metrics)
        await server.start()

        assert server._server is not None
        host, port, *_ = server._server.sockets[0].getsockname()

        reader, writer = await asyncio.open_connection(host, port)
        writer.write(json.dumps({"player_id": "p1"}).encode() + b"\n")
        await writer.drain()
        await reader.readline()

        writer.close()
        await writer.wait_closed()

        await asyncio.sleep(0.05)
        assert "p1" not in server.state.players

        await server.stop()

    asyncio.run(run())
