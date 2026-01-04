from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from .config import MatchSettings
from .models import KillFeed, KillFeedEntry, PlayerState, ScoreBoard, SpawnPoint

RespawnSelector = Callable[[List[SpawnPoint], Optional[str]], SpawnPoint]


def weighted_spawn_selector(spawn_points: List[SpawnPoint], avoid: Optional[str] = None) -> SpawnPoint:
    candidates = [sp for sp in spawn_points if sp.id != avoid] or spawn_points
    weights = [sp.weight for sp in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


@dataclass
class Match:
    settings: MatchSettings
    spawn_points: List[SpawnPoint]
    now_fn: Callable[[], float] = time.time
    select_spawn: RespawnSelector = weighted_spawn_selector
    scoreboard: ScoreBoard = field(default_factory=ScoreBoard)
    kill_feed: KillFeed = field(default_factory=KillFeed)
    start_time: Optional[float] = None
    ended: bool = False

    def start(self) -> None:
        self.settings.validate()
        self.start_time = self.now_fn()
        self.ended = False

    def time_left(self) -> Optional[float]:
        if self.start_time is None:
            return None
        return max(0.0, self.settings.time_limit_seconds - (self.now_fn() - self.start_time))

    def is_over(self) -> bool:
        if self.ended:
            return True
        if self.start_time is None:
            return False
        if self.time_left() == 0:
            return True
        top_frag = next(iter(self.scoreboard.top_frags()), None)
        return bool(top_frag and top_frag.frags >= self.settings.frag_limit)

    def _mark_end(self) -> None:
        if not self.ended:
            self.ended = True

    def register_kill(self, attacker: str, victim: str, weapon: Optional[str] = None) -> None:
        if self.is_over():
            return
        self.scoreboard.record_kill(attacker, victim)
        self.kill_feed.add(
            KillFeedEntry(
                attacker=attacker,
                victim=victim,
                weapon=weapon,
                timestamp=self.now_fn(),
            )
        )
        if self.is_over():
            self._mark_end()

    def alive_players(self) -> Iterable[PlayerState]:
        return (p for p in self.scoreboard.players.values() if p.alive)

    def respawn_player(self, name: str, avoid_spawn: Optional[str] = None) -> SpawnPoint:
        player = self.scoreboard.ensure_player(name)
        spawn = self.select_spawn(self.spawn_points, avoid=avoid_spawn)
        player.alive = True
        player.invulnerable_until = self.now_fn() + self.settings.invulnerability_seconds
        return spawn

    def can_damage(self, attacker: str, victim: str) -> bool:
        victim_state = self.scoreboard.ensure_player(victim)
        if not victim_state.alive:
            return False
        return self.now_fn() >= victim_state.invulnerable_until

    def try_end(self) -> bool:
        if self.is_over():
            self._mark_end()
            return True
        return False
