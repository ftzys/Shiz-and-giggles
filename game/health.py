from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class HitFeedback:
    hitmarker: bool
    sound: Optional[str]
    screen_flash: bool


@dataclass
class DamageReport:
    damage_applied: float
    remaining_health: float
    remaining_armor: float
    defeated: bool
    feedback: Optional[HitFeedback] = None


class HealthArmor:
    def __init__(
        self,
        max_health: float = 100.0,
        max_armor: float = 100.0,
        health: Optional[float] = None,
        armor: Optional[float] = None,
    ) -> None:
        self.max_health = max_health
        self.max_armor = max_armor
        self.health = health if health is not None else max_health
        self.armor = armor if armor is not None else 0.0

    def heal(self, amount: float) -> float:
        old_health = self.health
        self.health = min(self.max_health, self.health + amount)
        return self.health - old_health

    def add_armor(self, amount: float) -> float:
        old_armor = self.armor
        self.armor = min(self.max_armor, self.armor + amount)
        return self.armor - old_armor

    def apply_damage(
        self,
        amount: float,
        *,
        allow_armor: bool = True,
        feedback: bool = True,
    ) -> DamageReport:
        if amount <= 0:
            return DamageReport(0.0, self.health, self.armor, False, None)

        damage_remaining = amount
        armor_absorbed = 0.0
        if allow_armor and self.armor > 0:
            armor_absorbed = min(self.armor, damage_remaining)
            self.armor -= armor_absorbed
            damage_remaining -= armor_absorbed

        health_lost = min(self.health, damage_remaining)
        self.health -= health_lost
        defeated = self.health <= 0

        feedback_payload = None
        if feedback:
            feedback_payload = HitFeedback(
                hitmarker=True,
                sound="hit_confirm" if amount > 0 else None,
                screen_flash=True,
            )

        return DamageReport(
            damage_applied=armor_absorbed + health_lost,
            remaining_health=self.health,
            remaining_armor=self.armor,
            defeated=defeated,
            feedback=feedback_payload,
        )


class HealthPickup:
    def __init__(self, amount: float) -> None:
        self.amount = amount

    def apply(self, target: HealthArmor) -> float:
        return target.heal(self.amount)


class ArmorPickup:
    def __init__(self, amount: float) -> None:
        self.amount = amount

    def apply(self, target: HealthArmor) -> float:
        return target.add_armor(self.amount)
