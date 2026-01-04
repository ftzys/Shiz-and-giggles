from shizgiggles.logic import PlayerState, WorldState


def test_player_moves_within_boundaries():
    player = PlayerState(player_id="p1")
    player.move((10, 10), boundaries=(5, 5))
    assert player.position == (5, 5)


def test_world_tracks_player_velocity():
    world = WorldState()
    player = world.move_player("p2", (1, -2))
    assert player.velocity == (1, -2)
    assert player.position == (1, -2)
    world.step()
    player = world.move_player("p2", (2, 0))
    assert world.tick == 1
    assert player.position == (3, -2)
