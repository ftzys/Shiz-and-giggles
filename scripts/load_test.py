from __future__ import annotations

import argparse
import asyncio
import logging
from typing import List

from shizgiggles.client import send_actions
from shizgiggles.protocol import Message

logger = logging.getLogger(__name__)


async def run_fake_client(host: str, port: int, player_id: str) -> None:
    moves = [Message.move(player_id, (1, 0)), Message.move(player_id, (0, 1)), Message.fire(player_id)]
    await send_actions(host, port, player_id, moves)


async def load_test(host: str, port: int, client_count: int) -> None:
    tasks: List[asyncio.Task[None]] = []
    for idx in range(client_count):
        player_id = f"bot-{idx:02d}"
        tasks.append(asyncio.create_task(run_fake_client(host, port, player_id)))
    await asyncio.gather(*tasks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a lightweight load test against the dedicated server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--clients", type=int, default=16)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level.upper(), format="[%(asctime)s] %(levelname)s %(message)s")
    asyncio.run(load_test(args.host, args.port, args.clients))


if __name__ == "__main__":
    main()
