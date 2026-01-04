extends Control

@onready var _status_label: Label = $Margin/VBox/Status
@onready var _scoreboard_label: Label = $Margin/VBox/Scoreboard
@onready var _health_label: Label = $Margin/VBox/Health
@onready var _center_message: Label = $Center/Message
@onready var _crosshair: Label = $Crosshair

func set_status(text: String) -> void:
    _status_label.text = text

func set_health(current: int, max_value: int) -> void:
    _health_label.text = "Health: %d / %d" % [current, max_value]

func set_message(text: String, duration: float = 2.0) -> void:
    _center_message.text = text
    if text.is_empty():
        return
    var timer := get_tree().create_timer(duration)
    timer.timeout.connect(func ():
        _center_message.text = ""
    )

func update_scoreboard(board: Dictionary) -> void:
    var rows: Array[String] = []
    var sorted_ids := board.keys()
    sorted_ids.sort()
    for id in sorted_ids:
        var entry: Dictionary = board[id]
        var name := entry.get("name", "Player %d" % int(id))
        var kills := int(entry.get("kills", 0))
        var deaths := int(entry.get("deaths", 0))
        rows.append("%s — Kills: %d  Deaths: %d" % [name, kills, deaths])
    _scoreboard_label.text = rows.join("\n")

func show_crosshair(show: bool) -> void:
    _crosshair.visible = show

func toggle_menu_hint(visible: bool) -> void:
    _status_label.visible = visible
