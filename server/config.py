from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ServerConfig:
    """
    Configuration for the dedicated server runtime.
    """

    host: str = "0.0.0.0"
    port: int = 7777
    maps: List[str] = field(default_factory=lambda: ["arena"])
    player_limit: int = 16
    tick_rate: int = 30
    password: Optional[str] = None
    region: str = "global"
    matchmaking_endpoint: Optional[str] = None
    matchmaking_api_key: Optional[str] = None
    metrics_interval_seconds: int = 30
    rate_limit_per_second: int = 10
    max_message_size: int = 4096
