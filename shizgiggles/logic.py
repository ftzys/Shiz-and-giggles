from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class PlayerState:
    player_id: str
    position: Tuple[float, float] = (0.0, 0.0)
    velocity: Tuple[float, float] = (0.0, 0.0)
    health: int = 100
    ammo: int = 30
    last_fired_tick: int = -1

    def move(self, delta: Tuple[float, float], boundaries: Tuple[float, float] = (100.0, 100.0)) -> None:
        new_x = max(min(self.position[0] + delta[0], boundaries[0]), -boundaries[0])
        new_y = max(min(self.position[1] + delta[1], boundaries[1]), -boundaries[1])
        self.velocity = delta
        self.position = (new_x, new_y)

    def can_fire(self, tick: int, fire_rate: int = 2) -> bool:
        if self.ammo <= 0:
            return False
        if self.last_fired_tick < 0:
            return True
        return (tick - self.last_fired_tick) >= fire_rate

    def fire(self, tick: int, fire_rate: int = 2, damage: int = 10) -> int:
        if not self.can_fire(tick, fire_rate):
            return 0
        self.ammo -= 1
        self.last_fired_tick = tick
        return damage


@dataclass
class WorldState:
    tick: int = 0
    players: Dict[str, PlayerState] = field(default_factory=dict)

    def step(self) -> None:
        self.tick += 1

    def ensure_player(self, player_id: str) -> PlayerState:
        if player_id not in self.players:
            self.players[player_id] = PlayerState(player_id=player_id)
        return self.players[player_id]

    def move_player(self, player_id: str, delta: Tuple[float, float]) -> PlayerState:
        player = self.ensure_player(player_id)
        player.move(delta)
        return player

    def fire_weapon(self, player_id: str) -> Tuple[PlayerState, int]:
        player = self.ensure_player(player_id)
        damage = player.fire(self.tick)
        return player, damage
