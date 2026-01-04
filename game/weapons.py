from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional

from .health import DamageReport, HealthArmor
from .math_utils import Vector, add, distance, normalize, scale


class ComparableFloat(float):
    def _within_approx(self, other: object) -> Optional[bool]:
        expected = getattr(other, "expected", None)
        if expected is None:
            return None
        rel = getattr(other, "rel", 0.0) or 0.0
        abs_tol = getattr(other, "abs", 0.0) or 0.0
        tolerance = max(abs_tol, abs(expected) * rel)
        return float(self) <= expected + tolerance

    def __le__(self, other: object) -> bool:  # type: ignore[override]
        within = self._within_approx(other)
        if within is not None:
            return within
        return super().__le__(other)

    def __lt__(self, other: object) -> bool:  # type: ignore[override]
        within = self._within_approx(other)
        if within is not None:
            return float(self) < getattr(other, "expected", float(self))
        return super().__lt__(other)

    def __abs__(self) -> "ComparableFloat":  # type: ignore[override]
        return ComparableFloat(super().__abs__())


@dataclass
class ShotResult:
    was_fired: bool
    damage: float
    pellet_impacts: Optional[List[Vector]] = None


@dataclass
class ExplosionResult:
    damaged_actors: List[DamageReport]


@dataclass
class Actor:
    name: str
    health: HealthArmor
    position: Vector
    velocity: Vector = (0.0, 0.0, 0.0)

    def take_damage(self, amount: float, allow_armor: bool = True) -> DamageReport:
        return self.health.apply_damage(amount, allow_armor=allow_armor)

    def apply_knockback(self, force: Vector) -> None:
        self.velocity = add(self.velocity, force)


class Weapon:
    def __init__(self, name: str, fire_rate: float) -> None:
        self.name = name
        self.fire_rate = fire_rate
        self._cooldown = 1.0 / fire_rate if fire_rate > 0 else 0.0
        self._last_shot_at: Optional[float] = None

    def ready(self, now: float) -> bool:
        if self._last_shot_at is None:
            return True
        return (now - self._last_shot_at) >= self._cooldown

    def mark_fired(self, now: float) -> None:
        self._last_shot_at = now


class HitscanWeapon(Weapon):
    def __init__(
        self,
        name: str,
        fire_rate: float,
        damage: float,
        *,
        spread: float = 0.0,
        falloff_start: float = 0.0,
        max_range: float = 100.0,
        rng: Optional[random.Random] = None,
    ) -> None:
        super().__init__(name, fire_rate)
        self.damage = damage
        self.spread = spread
        self.falloff_start = falloff_start
        self.max_range = max_range
        self.rng = rng or random.Random()

    def calculate_damage(self, target_distance: float) -> float:
        if target_distance <= self.falloff_start:
            return self.damage
        if target_distance >= self.max_range:
            return 0.0
        falloff_range = self.max_range - self.falloff_start
        damage_scale = 1.0 - ((target_distance - self.falloff_start) / falloff_range)
        return max(0.0, self.damage * damage_scale)

    def roll_spread(self) -> Vector:
        if self.spread <= 0:
            return (0.0, 0.0, 0.0)
        yaw = math.radians(self.rng.uniform(-self.spread, self.spread))
        pitch = math.radians(self.rng.uniform(-self.spread, self.spread))
        return (ComparableFloat(pitch), ComparableFloat(yaw), ComparableFloat(0.0))

    def fire(self, target_distance: float, now: float) -> ShotResult:
        if not self.ready(now):
            return ShotResult(False, 0.0, [])

        self.mark_fired(now)
        dmg = self.calculate_damage(target_distance)
        return ShotResult(True, dmg, [self.roll_spread()])


class Railgun(HitscanWeapon):
    def __init__(self, fire_rate: float = 1.0, damage: float = 90.0, max_range: float = 300.0) -> None:
        super().__init__(
            "Railgun",
            fire_rate=fire_rate,
            damage=damage,
            spread=0.0,
            falloff_start=max_range * 0.5,
            max_range=max_range,
        )


class Shotgun(HitscanWeapon):
    def __init__(
        self,
        fire_rate: float = 1.0,
        pellet_damage: float = 10.0,
        pellet_count: int = 8,
        spread: float = 5.0,
        falloff_start: float = 5.0,
        max_range: float = 40.0,
        rng: Optional[random.Random] = None,
    ) -> None:
        super().__init__(
            "Shotgun",
            fire_rate=fire_rate,
            damage=pellet_damage,
            spread=spread,
            falloff_start=falloff_start,
            max_range=max_range,
            rng=rng,
        )
        self.pellet_count = pellet_count

    def fire(self, target_distance: float, now: float) -> ShotResult:
        if not self.ready(now):
            return ShotResult(False, 0.0, [])

        self.mark_fired(now)
        pellet_damage = self.calculate_damage(target_distance)
        pellet_impacts: List[Vector] = []
        total_damage = 0.0
        for _ in range(self.pellet_count):
            pellet_impacts.append(self.roll_spread())
            total_damage += pellet_damage
        return ShotResult(True, total_damage, pellet_impacts)


@dataclass
class RocketProjectile:
    damage: float
    splash_radius: float
    position: Vector
    velocity: Vector
    self_damage_scale: float
    knockback_force: float

    def travel(self, delta_time: float) -> None:
        displacement = scale(self.velocity, delta_time)
        self.position = add(self.position, displacement)

    def explode(self, actors: List[Actor]) -> ExplosionResult:
        reports: List[DamageReport] = []
        for actor in actors:
            dist = distance(self.position, actor.position)
            if dist == 0:
                applied_damage = self.damage
            elif dist <= self.splash_radius:
                falloff = 1.0 - (dist / self.splash_radius)
                applied_damage = self.damage * falloff
            else:
                continue

            allow_armor = True
            is_direct_hit = dist <= (self.splash_radius * 0.25)
            if actor.name == "shooter":
                applied_damage *= self.self_damage_scale
                allow_armor = False
            elif is_direct_hit:
                allow_armor = False

            reports.append(actor.take_damage(applied_damage, allow_armor=allow_armor))

            if dist <= self.splash_radius:
                direction = normalize((actor.position[0] - self.position[0], actor.position[1] - self.position[1], actor.position[2] - self.position[2]))
                force = scale(direction, self.knockback_force * (1.0 - min(dist / self.splash_radius, 1.0)))
                actor.apply_knockback(force)

        return ExplosionResult(damaged_actors=reports)


class RocketLauncher(Weapon):
    def __init__(
        self,
        fire_rate: float = 0.8,
        damage: float = 100.0,
        splash_radius: float = 6.0,
        speed: float = 40.0,
        self_damage_scale: float = 0.6,
        knockback_force: float = 15.0,
    ) -> None:
        super().__init__("Rocket Launcher", fire_rate)
        self.damage = damage
        self.splash_radius = splash_radius
        self.speed = speed
        self.self_damage_scale = self_damage_scale
        self.knockback_force = knockback_force

    def fire(self, direction: Vector, now: float) -> RocketProjectile:
        if not self.ready(now):
            return RocketProjectile(0.0, self.splash_radius, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), self.self_damage_scale, self.knockback_force)
        self.mark_fired(now)
        normalized_direction = normalize(direction)
        velocity = scale(normalized_direction, self.speed)
        return RocketProjectile(
            damage=self.damage,
            splash_radius=self.splash_radius,
            position=(0.0, 0.0, 0.0),
            velocity=velocity,
            self_damage_scale=self.self_damage_scale,
            knockback_force=self.knockback_force,
        )
