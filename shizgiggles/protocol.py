from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


class MessageType(str, Enum):
    JOIN = "join"
    MOVE = "move"
    FIRE = "fire"
    SNAPSHOT = "snapshot"
    PING = "ping"


@dataclass
class MovePayload:
    dx: float
    dy: float


@dataclass
class Message:
    type: MessageType
    player_id: str
    payload: Dict[str, Any] | None = None

    def to_json(self) -> str:
        return json.dumps({"type": self.type.value, "player_id": self.player_id, "payload": self.payload or {}})

    @staticmethod
    def move(player_id: str, delta: Tuple[float, float]) -> "Message":
        return Message(type=MessageType.MOVE, player_id=player_id, payload={"dx": delta[0], "dy": delta[1]})

    @staticmethod
    def fire(player_id: str) -> "Message":
        return Message(type=MessageType.FIRE, player_id=player_id, payload={})

    @staticmethod
    def join(player_id: str) -> "Message":
        return Message(type=MessageType.JOIN, player_id=player_id, payload={})

    @staticmethod
    def ping(player_id: str) -> "Message":
        return Message(type=MessageType.PING, player_id=player_id, payload={})

    @classmethod
    def from_json(cls, payload: str) -> "Message":
        data = json.loads(payload)
        return cls(type=MessageType(data["type"]), player_id=data["player_id"], payload=data.get("payload", {}))
