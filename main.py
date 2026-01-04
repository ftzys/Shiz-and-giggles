import argparse
import asyncio
import logging
import threading

from server.config import ServerConfig
from server.game_server import GameServer
from server.matchmaking import MatchmakingBackend
from server.metrics import Metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shiz-and-giggles dedicated server")
    subparsers = parser.add_subparsers(dest="command", required=True)

    server_parser = subparsers.add_parser("server", help="Run the dedicated server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Bind address for the server")
    server_parser.add_argument("--port", type=int, default=7777, help="Port for the server")
    server_parser.add_argument("--maps", nargs="+", default=["arena", "ascent", "sewers"], help="Map rotation list")
    server_parser.add_argument("--player-limit", type=int, default=16, help="Maximum number of players")
    server_parser.add_argument("--tick-rate", type=int, default=30, help="Server tick rate in Hz")
    server_parser.add_argument("--password", help="Optional server password")
    server_parser.add_argument("--region", default="global", help="Region identifier for matchmaking")
    server_parser.add_argument("--matchmaking-endpoint", help="URL of the matchmaking backend to register with")
    server_parser.add_argument("--matchmaking-api-key", help="Optional API key for the matchmaking backend")
    server_parser.add_argument("--metrics-interval", type=int, default=30, help="How often to log metrics (seconds)")
    server_parser.add_argument("--rate-limit", type=int, default=10, help="Messages per second per client")
    server_parser.add_argument("--max-message-size", type=int, default=4096, help="Maximum message size in bytes")

    backend_parser = subparsers.add_parser("matchmaking-backend", help="Run the matchmaking backend server list")
    backend_parser.add_argument("--host", default="0.0.0.0", help="Bind address for the matchmaking backend")
    backend_parser.add_argument("--port", type=int, default=8080, help="Port for the matchmaking backend")

    return parser.parse_args()


def run_matchmaking_backend(host: str, port: int):
    backend = MatchmakingBackend(host=host, port=port)
    backend.start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        backend.stop()


async def run_server(args: argparse.Namespace):
    metrics = Metrics()
    config = ServerConfig(
        host=args.host,
        port=args.port,
        maps=args.maps,
        player_limit=args.player_limit,
        tick_rate=args.tick_rate,
        password=args.password,
        region=args.region,
        matchmaking_endpoint=args.matchmaking_endpoint,
        matchmaking_api_key=args.matchmaking_api_key,
        metrics_interval_seconds=args.metrics_interval,
        rate_limit_per_second=args.rate_limit,
        max_message_size=args.max_message_size,
    )
    server = GameServer(config=config, metrics=metrics)
    metrics_stop_event = threading.Event()
    metrics_thread = threading.Thread(
        target=metrics.log_periodically, args=(config.metrics_interval_seconds, metrics_stop_event), daemon=True
    )
    metrics_thread.start()

    await server.start()
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await server.stop()
        metrics_stop_event.set()
        metrics_thread.join()


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
    args = parse_args()
    if args.command == "matchmaking-backend":
        run_matchmaking_backend(args.host, args.port)
    elif args.command == "server":
        asyncio.run(run_server(args))


if __name__ == "__main__":
    main()
