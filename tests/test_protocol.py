from shizgiggles.protocol import Message, MessageType


def test_message_round_trip():
    original = Message.move("p1", (1.0, -1.5))
    payload = original.to_json()
    restored = Message.from_json(payload)
    assert restored.type == MessageType.MOVE
    assert restored.player_id == "p1"
    assert restored.payload["dx"] == 1.0
    assert restored.payload["dy"] == -1.5
