from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SpawnPoint:
    """Spawn point with optional weight for randomness."""

    id: str
    weight: float = 1.0
    location: Optional[str] = None

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("SpawnPoint weight must be positive")


@dataclass
class PlayerState:
    """Per-player match state."""

    name: str
    frags: int = 0
    deaths: int = 0
    invulnerable_until: float = 0.0
    alive: bool = True

    def record_kill(self) -> None:
        self.frags += 1

    def record_death(self) -> None:
        self.deaths += 1
        self.alive = False


@dataclass
class KillFeedEntry:
    attacker: str
    victim: str
    weapon: Optional[str] = None
    timestamp: float = 0.0


@dataclass
class KillFeed:
    entries: List[KillFeedEntry] = field(default_factory=list)
    max_entries: int = 20

    def add(self, entry: KillFeedEntry) -> None:
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]


@dataclass
class ScoreBoard:
    players: Dict[str, PlayerState] = field(default_factory=dict)

    def ensure_player(self, name: str) -> PlayerState:
        if name not in self.players:
            self.players[name] = PlayerState(name=name)
        return self.players[name]

    def record_kill(self, attacker: str, victim: str) -> None:
        attacker_state = self.ensure_player(attacker)
        victim_state = self.ensure_player(victim)
        attacker_state.record_kill()
        victim_state.record_death()

    def top_frags(self) -> List[PlayerState]:
        return sorted(self.players.values(), key=lambda p: p.frags, reverse=True)
