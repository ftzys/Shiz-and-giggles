import json
import logging
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional
from urllib import error, parse, request

SERVER_TTL_SECONDS = 120


@dataclass
class ServerAnnouncement:
    address: str
    port: int
    region: str
    max_players: int
    map_name: str
    tick_rate: int
    last_seen: float


class _Registry:
    def __init__(self):
        self._servers: Dict[str, ServerAnnouncement] = {}
        self._lock = threading.Lock()

    def register(self, announcement: ServerAnnouncement) -> None:
        with self._lock:
            self._servers[self._key(announcement)] = announcement

    def list_active(self) -> List[ServerAnnouncement]:
        with self._lock:
            now = time.time()
            self._servers = {k: v for k, v in self._servers.items() if now - v.last_seen <= SERVER_TTL_SECONDS}
            return list(self._servers.values())

    @staticmethod
    def _key(announcement: ServerAnnouncement) -> str:
        return f"{announcement.address}:{announcement.port}"


class MatchmakingBackend:
    """
    Lightweight HTTP server list backend.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self._registry = _Registry()
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        handler = self._build_handler()
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        logging.info("Matchmaking backend started on %s:%s", self.host, self.port)

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=1)

    def _build_handler(self):
        registry = self._registry

        class Handler(BaseHTTPRequestHandler):
            def _send(self, code: int, payload: dict):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                if self.path != "/register":
                    self._send(404, {"error": "not found"})
                    return
                content_length = int(self.headers.get("Content-Length", "0"))
                try:
                    raw = self.rfile.read(content_length)
                    payload = json.loads(raw)
                    announcement = ServerAnnouncement(
                        address=payload["address"],
                        port=int(payload["port"]),
                        region=payload.get("region", "global"),
                        max_players=int(payload.get("max_players", 0)),
                        map_name=payload.get("map_name", "unknown"),
                        tick_rate=int(payload.get("tick_rate", 0)),
                        last_seen=time.time(),
                    )
                    registry.register(announcement)
                    self._send(200, {"status": "ok"})
                except Exception as exc:  # noqa: BLE001
                    logging.exception("failed to register server: %s", exc)
                    self._send(400, {"error": "invalid payload"})

            def do_GET(self):
                if self.path != "/servers":
                    self._send(404, {"error": "not found"})
                    return
                servers = registry.list_active()
                body = [
                    {
                        "address": s.address,
                        "port": s.port,
                        "region": s.region,
                        "max_players": s.max_players,
                        "map_name": s.map_name,
                        "tick_rate": s.tick_rate,
                        "last_seen": s.last_seen,
                    }
                    for s in servers
                ]
                self._send(200, {"servers": body})

            def log_message(self, format: str, *args) -> None:  # noqa: A003
                logging.info("matchmaking: " + format, *args)

        return Handler


class MatchmakingClient:
    """
    Simple client that registers the server to the matchmaking backend.
    """

    def __init__(self, endpoint: str, api_key: str | None = None):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key

    def register_server(
        self,
        address: str,
        port: int,
        region: str,
        max_players: int,
        map_name: str,
        tick_rate: int,
    ) -> bool:
        payload = {
            "address": address,
            "port": port,
            "region": region,
            "max_players": max_players,
            "map_name": map_name,
            "tick_rate": tick_rate,
        }
        data = json.dumps(payload).encode("utf-8")
        url = f"{self.endpoint}/register"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        req = request.Request(url, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except error.URLError as exc:
            logging.warning("failed to register with matchmaking backend: %s", exc)
            return False
