extends CanvasLayer
## Menú de pausa (Sprint 4). Base extensible: la sección "Navegación" vive acá
## ahora (Continuar / Reiniciar posición / botones de piso); Sprint 5 va a
## agregar una sección "Materiales" para selección de repintado, sin tocar
## esta estructura.
##
## No lee building.json ni geometry.json (el engine no conoce el pipeline).
## Las elevaciones de piso están hardcodeadas como constantes acá abajo,
## tomadas de pipeline/schema/examples/building.example.json al momento del
## Sprint 4 (elevaciones [0.0, 2.7] para "Planta baja" / "Primer piso"). Si
## el contrato building.json llega a exponer esto de forma legible desde
## Godot en el futuro, este diccionario debería leerse de ahí en vez de
## hardcodearse — fuera de alcance para este sprint.

signal closed
signal opened

## piso_nombre -> elevación en metros (Y en Godot, que ya viene con Y arriba
## desde el .gltf).
const FLOORS := {
	"Planta baja": 0.0,
	"Primer piso": 2.7,
}

@onready var panel: Panel = $Panel
@onready var floors_container: VBoxContainer = $Panel/MarginContainer/VBox/NavigationSection/Floors
@onready var continue_button: Button = $Panel/MarginContainer/VBox/NavigationSection/ContinueButton
@onready var reset_button: Button = $Panel/MarginContainer/VBox/NavigationSection/ResetButton

## Callbacks inyectados por main.gd (evita que este menú tenga que conocer
## el árbol de escena de Main/Player directamente).
var reset_position_callback: Callable
var change_floor_callback: Callable


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	continue_button.pressed.connect(_on_continue_pressed)
	reset_button.pressed.connect(_on_reset_pressed)
	_build_floor_buttons()


func _build_floor_buttons() -> void:
	for floor_name in FLOORS.keys():
		var button := Button.new()
		button.text = floor_name
		button.pressed.connect(_on_floor_pressed.bind(floor_name))
		floors_container.add_child(button)


func open() -> void:
	visible = true
	opened.emit()


func close() -> void:
	visible = false
	closed.emit()


func _on_continue_pressed() -> void:
	close()


func _on_reset_pressed() -> void:
	if reset_position_callback.is_valid():
		reset_position_callback.call()
	close()


func _on_floor_pressed(floor_name: String) -> void:
	if change_floor_callback.is_valid():
		change_floor_callback.call(FLOORS[floor_name])
	close()
