import random

import pytest

from game.health import ArmorPickup, HealthArmor, HealthPickup
from game.weapons import Actor, Railgun, RocketLauncher, Shotgun


class FixedRandom(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = values
        self._iter = iter(values)

    def uniform(self, a, b):
        try:
            value = next(self._iter)
        except StopIteration:
            value = 0.0
        return a + (b - a) * ((value + 1) / 2)


def test_fire_rate_prevents_spam():
    gun = Railgun(fire_rate=1.0)
    first = gun.fire(target_distance=10.0, now=0.0)
    second = gun.fire(target_distance=10.0, now=0.2)
    third = gun.fire(target_distance=10.0, now=1.1)

    assert first.was_fired is True
    assert second.was_fired is False
    assert third.was_fired is True


def test_shotgun_spread_and_damage_falloff():
    rng = FixedRandom([0.0, 0.5, -0.5, 0.25, -0.25, 0.0, 0.1, -0.1])
    shotgun = Shotgun(fire_rate=1.0, pellet_damage=8.0, pellet_count=8, spread=5.0, rng=rng)
    close_range = shotgun.fire(target_distance=4.0, now=0.0)
    far_range = shotgun.fire(target_distance=30.0, now=2.0)

    assert close_range.was_fired
    assert len(close_range.pellet_impacts) == 8
    assert close_range.damage == pytest.approx(64.0)

    assert far_range.damage < close_range.damage
    assert all(abs(pitch) <= pytest.approx(0.0873, rel=0.1) for pitch, yaw, roll in far_range.pellet_impacts)


def test_health_and_armor_pickups():
    stats = HealthArmor(max_health=150, max_armor=75, health=50, armor=10)
    healed = HealthPickup(40).apply(stats)
    armored = ArmorPickup(80).apply(stats)

    assert healed == 40
    assert armored == 65
    assert stats.health == 90
    assert stats.armor == 75


def test_damage_feedback_and_defeat():
    stats = HealthArmor(max_health=100, max_armor=50, health=60, armor=20)
    report = stats.apply_damage(45)

    assert report.damage_applied == 45
    assert report.remaining_health == 35
    assert report.remaining_armor == 0
    assert report.feedback and report.feedback.hitmarker and report.feedback.screen_flash

    fatal_report = stats.apply_damage(40)
    assert fatal_report.defeated is True


def test_rocket_splash_and_self_damage_with_knockback():
    shooter = Actor("shooter", health=HealthArmor(health=120, armor=0), position=(0.0, 0.0, 0.0))
    target = Actor("target", health=HealthArmor(health=150, armor=50), position=(0.0, 0.0, 3.0))

    launcher = RocketLauncher(damage=120, splash_radius=6.0, self_damage_scale=0.5, knockback_force=20.0)
    rocket = launcher.fire(direction=(0.0, 0.0, 1.0), now=0.0)

    rocket.travel(0.05)
    result = rocket.explode([shooter, target])

    assert len(result.damaged_actors) == 2
    assert target.health.health < 150
    assert shooter.health.health < 120
    assert target.velocity != (0.0, 0.0, 0.0)
    assert shooter.velocity != (0.0, 0.0, 0.0)
    assert target.health.health < shooter.health.health
