extends CharacterBody3D
class_name ArenaPlayer

@export var walk_speed: float = 10.0
@export var run_speed: float = 16.0
@export var jump_velocity: float = 13.0
@export var mouse_sensitivity: float = 0.0025
@export var fire_cooldown: float = 0.18
@export var weapon_range: float = 140.0
@export var weapon_damage: int = 25
@export var max_health: int = 100

var player_id: int = 1
var nickname: String = "Runner"
var health: int = 100
var network_manager: Node
var hud: Node

var _look_pitch: float = 0.0
var _shoot_timer: float = 0.0
var _pending_fire: bool = false

@onready var _head: Node3D = $Head
@onready var _camera: Camera3D = $Head/Camera3D
@onready var _muzzle: Marker3D = $Head/Muzzle

func _ready() -> void:
    health = max_health
    if is_multiplayer_authority():
        Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
        _camera.current = true
    else:
        _camera.current = false
    if is_multiplayer_authority() and hud:
        hud.show_crosshair(true)
        hud.set_health(health, max_health)
    set_physics_process(true)

func _unhandled_input(event: InputEvent) -> void:
    if not is_multiplayer_authority():
        return
    if event is InputEventMouseMotion:
        rotate_y(-event.relative.x * mouse_sensitivity)
        _look_pitch = clamp(_look_pitch - event.relative.y * mouse_sensitivity, -1.3, 1.3)
        _head.rotation.x = _look_pitch
    elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
        Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

func _physics_process(delta: float) -> void:
    if is_on_floor():
        if Input.is_action_just_pressed("jump"):
            velocity.y = jump_velocity
    else:
        velocity.y -= ProjectSettings.get_setting("physics/3d/default_gravity") * delta

    if is_multiplayer_authority():
        _shoot_timer = maxf(_shoot_timer - delta, 0.0)
        var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
        var forward := -global_transform.basis.z
        var right := global_transform.basis.x
        var direction := (forward * input_dir.y) + (right * input_dir.x)
        var speed := Input.is_action_pressed("sprint") ? run_speed : walk_speed
        var target_velocity := direction.normalized() * speed
        velocity.x = target_velocity.x
        velocity.z = target_velocity.z
        if Input.is_action_pressed("fire"):
            _pending_fire = true
    move_and_slide()
    if is_multiplayer_authority():
        _send_state()
    if _pending_fire and _shoot_timer <= 0.0 and is_multiplayer_authority():
        _pending_fire = false
        _shoot_timer = fire_cooldown
        _fire_weapon()

func _fire_weapon() -> void:
    if network_manager == null:
        return
    var origin := _muzzle.global_position
    var direction := -_camera.global_transform.basis.z
    network_manager.request_fire(origin, direction, weapon_range, weapon_damage)

@rpc("call_remote", "unreliable")
func receive_state(position: Vector3, basis: Basis, linear_velocity: Vector3) -> void:
    if is_multiplayer_authority():
        return
    global_transform.origin = position
    global_transform.basis = basis.orthonormalized()
    velocity = linear_velocity

func _send_state() -> void:
    rpc_unreliable("receive_state", global_transform.origin, global_transform.basis, velocity)

@rpc("call_local")
func set_health(value: int) -> void:
    health = clamp(value, 0, max_health)
    if is_multiplayer_authority() and hud:
        hud.set_health(health, max_health)

@rpc("call_local")
func respawn_at(position: Vector3) -> void:
    global_position = position
    velocity = Vector3.ZERO
    health = max_health
    if is_multiplayer_authority() and hud:
        hud.set_health(health, max_health)
        hud.set_message("You respawned", 1.5)
    _pending_fire = false
    _shoot_timer = 0.0
