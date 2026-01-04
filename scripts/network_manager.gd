extends Node

@export var server_port: int = 8910
@export var max_clients: int = 16
@export var arena_scene: PackedScene = preload("res://scenes/arena.tscn")
@export var player_scene: PackedScene = preload("res://scenes/player.tscn")
@export var respawn_delay: float = 2.0

var _peer: ENetMultiplayerPeer
var _world: Node3D
var _spawn_points: Array[Node3D] = []
var _players: Dictionary = {}
var _scoreboard: Dictionary = {}
var _pending_names: Dictionary = {}
var _rng := RandomNumberGenerator.new()
var _local_name := "Runner"

@onready var _hud: Control = $UI/HUD
@onready var _menu: Control = $UI/Menu
@onready var _world_root: Node3D = $WorldRoot
@onready var _menu_status: Label = $UI/Menu/Panel/MarginContainer/VBox/MenuStatus
@onready var _name_entry: LineEdit = $UI/Menu/Panel/MarginContainer/VBox/NameBox/NameEntry
@onready var _join_address: LineEdit = $UI/Menu/Panel/MarginContainer/VBox/JoinBox/JoinAddress

func _ready() -> void:
    add_to_group("network_manager")
    _wire_ui()
    _ensure_input_map()
    multiplayer.peer_connected.connect(_on_peer_connected)
    multiplayer.peer_disconnected.connect(_on_peer_disconnected)
    multiplayer.connected_to_server.connect(_on_connected_to_server)
    multiplayer.connection_failed.connect(_on_connection_failed)
    multiplayer.server_disconnected.connect(_on_server_disconnected)
    var headless := OS.has_feature("server") or OS.has_feature("dedicated_server")
    if headless:
        _local_name = "Dedicated"
        _start_server(false)
        _hud.visible = false
        _menu.visible = false
    else:
        _menu.visible = true
        _hud.visible = false
        _menu_status.text = "Host a new match or join an existing server."

func _wire_ui() -> void:
    var host_button: Button = $UI/Menu/Panel/MarginContainer/VBox/HostButton
    var join_button: Button = $UI/Menu/Panel/MarginContainer/VBox/JoinButton
    host_button.pressed.connect(_on_host_pressed)
    join_button.pressed.connect(_on_join_pressed)

func _ensure_input_map() -> void:
    var actions := {
        "move_forward": KEY_W,
        "move_back": KEY_S,
        "move_left": KEY_A,
        "move_right": KEY_D,
        "jump": KEY_SPACE,
        "fire": MOUSE_BUTTON_LEFT,
        "sprint": KEY_SHIFT
    }
    for action in actions.keys():
        if not InputMap.has_action(action):
            InputMap.add_action(action)
            var ev := InputEventKey.new()
            if actions[action] == MOUSE_BUTTON_LEFT:
                var mouse := InputEventMouseButton.new()
                mouse.button_index = MOUSE_BUTTON_LEFT
                InputMap.action_add_event(action, mouse)
                continue
            ev.physical_keycode = actions[action]
            InputMap.action_add_event(action, ev)

func _on_host_pressed() -> void:
    if _peer:
        return
    _local_name = _name_entry.text.is_empty() ? "Host" : _name_entry.text
    _menu_status.text = "Starting server on port %d..." % server_port
    _start_server()
    _menu.visible = false
    _hud.visible = true
    _hud.set_status("Hosting on port %d" % server_port)
    _hud.toggle_menu_hint(false)

func _on_join_pressed() -> void:
    if _peer:
        return
    _local_name = _name_entry.text.is_empty() ? "Fragster" : _name_entry.text
    connect_to_server(_join_address.text)
    _menu_status.text = "Connecting to %s:%d..." % [_join_address.text, server_port]

func _initialize_world() -> void:
    if _world:
        return
    _world = arena_scene.instantiate()
    _world_root.add_child(_world)
    var spawner := _world.get_node_or_null("SpawnPoints")
    if spawner:
        _spawn_points = spawner.get_children()

func _start_server(spawn_local: bool = true) -> void:
    _peer = ENetMultiplayerPeer.new()
    var result := _peer.create_server(server_port, max_clients)
    if result != OK:
        push_error("Failed to create server on port %d: %s" % [server_port, result])
        _peer = null
        _menu_status.text = "Failed to host. Error code %s" % result
        return
    multiplayer.multiplayer_peer = _peer
    _initialize_world()
    if spawn_local:
        _spawn_player(1, _local_name)
    _hud.set_status("Server listening on port %d" % server_port)

func connect_to_server(host: String) -> void:
    _peer = ENetMultiplayerPeer.new()
    var result := _peer.create_client(host, server_port)
    if result != OK:
        push_error("Failed to connect to %s:%d: %s" % [host, server_port, result])
        _peer = null
        _menu_status.text = "Connection failed. Error code %s" % result
        return
    multiplayer.multiplayer_peer = _peer
    _hud.visible = true
    _menu.visible = false
    _hud.set_status("Connecting to %s:%d" % [host, server_port])

@rpc("any_peer")
func register_player_name(name: String) -> void:
    if not multiplayer.is_server():
        return
    var id := multiplayer.get_remote_sender_id()
    _pending_names[id] = name
    if _scoreboard.has(id):
        _scoreboard[id].name = name
        _sync_scoreboard()
    if _players.has(id):
        var player: Node = _players[id]
        player.nickname = name

func _on_connected_to_server() -> void:
    _initialize_world()
    _hud.set_status("Connected. Waiting for spawn...")
    register_player_name.rpc_id(1, _local_name)

func _on_connection_failed() -> void:
    _menu.visible = true
    _hud.visible = false
    _peer = null
    _menu_status.text = "Connection failed. Check the address and try again."

func _on_server_disconnected() -> void:
    _menu.visible = true
    _hud.visible = false
    _menu_status.text = "Server closed the match."
    _peer = null

func _on_peer_connected(id: int) -> void:
    if not multiplayer.is_server():
        return
    var name := _pending_names.get(id, "Player %d" % id)
    _spawn_player(id, name)
    _send_existing_players(id)
    _sync_scoreboard()

func _on_peer_disconnected(id: int) -> void:
    if _players.has(id):
        var player: Node = _players[id]
        if is_instance_valid(player):
            player.queue_free()
    _players.erase(id)
    if not multiplayer.is_server():
        return
    _scoreboard.erase(id)
    _pending_names.erase(id)
    _sync_scoreboard()

func _send_existing_players(peer_id: int) -> void:
    for other_id in _players.keys():
        if other_id == peer_id:
            continue
        var other_player: Node = _players[other_id]
        spawn_player_remote.rpc_id(peer_id, other_player.global_position, other_id, other_player.nickname)

func _spawn_player(peer_id: int, nickname: String) -> void:
    if not _world:
        _initialize_world()
    var spawn := _choose_spawn_point()
    var player := player_scene.instantiate()
    player.name = "Player_%d" % peer_id
    player.player_id = peer_id
    player.nickname = nickname
    player.set_multiplayer_authority(peer_id)
    _world.add_child(player, true)
    player.global_transform.origin = spawn
    _players[peer_id] = player
    _scoreboard[peer_id] = {
        "name": nickname,
        "kills": _scoreboard.get(peer_id, {}).get("kills", 0),
        "deaths": _scoreboard.get(peer_id, {}).get("deaths", 0)
    }
    if peer_id == multiplayer.get_unique_id():
        player.hud = _hud
        player.network_manager = self
        _hud.set_health(player.health, player.max_health)
        _hud.set_status("You are %s — frag everything that moves." % nickname)
    spawn_player_remote.rpc(spawn, peer_id, nickname)
    _sync_scoreboard()

@rpc("call_remote")
func spawn_player_remote(spawn: Vector3, peer_id: int, nickname: String) -> void:
    if multiplayer.is_server():
        return
    if _players.has(peer_id):
        return
    _initialize_world()
    var player := player_scene.instantiate()
    player.name = "Player_%d" % peer_id
    player.player_id = peer_id
    player.nickname = nickname
    player.set_multiplayer_authority(peer_id)
    _world.add_child(player, true)
    player.global_position = spawn
    _players[peer_id] = player
    if peer_id == multiplayer.get_unique_id():
        player.hud = _hud
        player.network_manager = self
        _hud.set_health(player.health, player.max_health)
        _hud.set_status("Connected as %s" % nickname)

func _choose_spawn_point() -> Vector3:
    if _spawn_points.is_empty():
        return Vector3.ZERO
    var index := _rng.randi_range(0, _spawn_points.size() - 1)
    return _spawn_points[index].global_position

func request_fire(origin: Vector3, direction: Vector3, range: float, damage: int) -> void:
    if multiplayer.is_server():
        _server_handle_fire(origin, direction.normalized(), range, damage, multiplayer.get_unique_id())
    else:
        _server_handle_fire.rpc_id(1, origin, direction.normalized(), range, damage)

@rpc("any_peer")
func _server_handle_fire(origin: Vector3, direction: Vector3, range: float, damage: int) -> void:
    if not multiplayer.is_server():
        return
    var shooter_id := multiplayer.get_remote_sender_id()
    if shooter_id == 0:
        shooter_id = multiplayer.get_unique_id()
    var space := _world.get_world_3d().direct_space_state
    var query := PhysicsRayQueryParameters3D.create(origin, origin + direction.normalized() * range)
    query.collide_with_areas = false
    var exclude: Array = []
    if _players.has(shooter_id):
        exclude.append(_players[shooter_id])
    query.exclude = exclude
    var result := space.intersect_ray(query)
    play_shot_effects.rpc(origin, direction)
    if result.is_empty():
        return
    var collider := result.get("collider")
    if collider and collider is ArenaPlayer:
        _apply_damage(collider, shooter_id, damage)

func _apply_damage(target: ArenaPlayer, shooter_id: int, damage: int) -> void:
    if not multiplayer.is_server():
        return
    if not target or not _players.has(target.player_id):
        return
    target.health = max(target.health - damage, 0)
    _push_health(target)
    if target.health <= 0:
        _handle_frag(shooter_id, target.player_id)
        await get_tree().create_timer(respawn_delay).timeout
        _respawn_player(target.player_id)

@rpc("call_remote", "unreliable")
func play_shot_effects(origin: Vector3, direction: Vector3) -> void:
    # Placeholder for tracer or muzzle visuals. Clients can extend this script.
    pass

func _handle_frag(shooter_id: int, victim_id: int) -> void:
    if _scoreboard.has(victim_id):
        _scoreboard[victim_id].deaths = _scoreboard[victim_id].get("deaths", 0) + 1
    if shooter_id != 0 and _scoreboard.has(shooter_id):
        _scoreboard[shooter_id].kills = _scoreboard[shooter_id].get("kills", 0) + 1
    _sync_scoreboard()

func _respawn_player(peer_id: int) -> void:
    if not _players.has(peer_id):
        return
    var player: Node = _players[peer_id]
    var spawn := _choose_spawn_point()
    player.health = player.max_health
    player.global_position = spawn
    _push_health(player)
    player.rpc_id(peer_id, "respawn_at", spawn)

func _push_health(player: Node) -> void:
    player.set_health.rpc_id(player.player_id, player.health)
    if player.player_id == multiplayer.get_unique_id():
        player.set_health(player.health)

func _sync_scoreboard() -> void:
    if multiplayer.is_server():
        update_scoreboard_remote.rpc(_scoreboard)
    _hud.update_scoreboard(_scoreboard)

@rpc("call_remote")
func update_scoreboard_remote(board: Dictionary) -> void:
    _scoreboard = board
    if _hud:
        _hud.update_scoreboard(board)
