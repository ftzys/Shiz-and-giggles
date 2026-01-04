extends Node

@export var server_port: int = 8910
@export var max_clients: int = 32

var _peer: ENetMultiplayerPeer

func _ready() -> void:
    multiplayer.peer_connected.connect(_on_peer_connected)
    multiplayer.peer_disconnected.connect(_on_peer_disconnected)
    # Decide based on feature tags whether we should boot as server or client.
    # Headless exports include the "server" feature by default.
    if OS.has_feature("server") or OS.has_feature("dedicated_server"):
        _start_server()
    else:
        print("Client build ready. Use `connect_to_server(host)` to join a server.")

func _start_server() -> void:
    _peer = ENetMultiplayerPeer.new()
    var result := _peer.create_server(server_port, max_clients)
    if result != OK:
        push_error("Failed to create server on port %d: %s" % [server_port, result])
        return
    multiplayer.multiplayer_peer = _peer
    print("Server listening on port %d" % server_port)

func connect_to_server(host: String) -> void:
    _peer = ENetMultiplayerPeer.new()
    var result := _peer.create_client(host, server_port)
    if result != OK:
        push_error("Failed to connect to %s:%d: %s" % [host, server_port, result])
        return
    multiplayer.multiplayer_peer = _peer
    print("Connecting to %s:%d" % [host, server_port])

@rpc("any_peer", "call_local")
func broadcast_ping(message: String) -> void:
    print("Ping from %s: %s" % [str(multiplayer.get_remote_sender_id()), message])

func _input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and event.keycode == KEY_P:
        broadcast_ping.rpc_id(1, "local ping")

func _on_peer_connected(id: int) -> void:
    print("Peer %d connected" % id)

func _on_peer_disconnected(id: int) -> void:
    print("Peer %d disconnected" % id)
