from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Iterable

from shizgiggles.protocol import Message

logger = logging.getLogger(__name__)


async def send_actions(host: str, port: int, player_id: str, actions: Iterable[Message]) -> None:
    reader, writer = await asyncio.open_connection(host, port)
    writer.write((Message.join(player_id).to_json() + "\n").encode())
    await writer.drain()
    async def receiver() -> None:
        while True:
            data = await reader.readline()
            if not data:
                return
            logger.debug("Received: %s", data.decode().strip())
    recv_task = asyncio.create_task(receiver())
    try:
        for action in actions:
            writer.write((action.to_json() + "\n").encode())
            await writer.drain()
            await asyncio.sleep(0.05)
        writer.write((Message.ping(player_id).to_json() + "\n").encode())
        await writer.drain()
        await asyncio.sleep(0.1)
    finally:
        recv_task.cancel()
        writer.close()
        await writer.wait_closed()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Shiz and Giggles lightweight client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--player-id", default="client")
    parser.add_argument("--moves", nargs="*", default=["0,1", "1,0", "0,-1"])
    parser.add_argument("--fire", action="store_true", help="Fire once at the end of the script")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="[%(asctime)s] %(levelname)s %(message)s")
    actions = []
    for move in args.moves:
        dx, dy = move.split(",")
        actions.append(Message.move(args.player_id, (float(dx), float(dy))))
    if args.fire:
        actions.append(Message.fire(args.player_id))

    asyncio.run(send_actions(args.host, args.port, args.player_id, actions))


if __name__ == "__main__":
    main()
