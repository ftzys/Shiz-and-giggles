from shizgiggles.logic import PlayerState, WorldState


def test_fire_respects_rate_of_fire():
    player = PlayerState(player_id="p1")
    world = WorldState(players={"p1": player})
    player.fire(world.tick)
    world.step()
    damage = player.fire(world.tick)
    assert damage == 0
    world.tick += 3
    damage = player.fire(world.tick)
    assert damage > 0


def test_ammo_decrements_and_blocks_when_empty():
    player = PlayerState(player_id="p2", ammo=1)
    world = WorldState(players={"p2": player})
    damage = player.fire(world.tick)
    assert damage > 0
    damage = player.fire(world.tick + 10)
    assert damage == 0
