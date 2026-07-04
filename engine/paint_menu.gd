extends CanvasLayer
## Sprint 5 — panel de selección de material para repintado.
## Escena separada de menu.tscn (pausa): se abre por acción del jugador
## (raycast sobre una superficie), no por Esc, y su ciclo de vida es
## independiente. Muestra qué superficie fue tocada (surface_id, con
## prefijo de piso incluido) y 3 botones: Madera / Cemento / Pintura.

signal material_selected(material_name: String)
signal closed

@onready var panel: Panel = $Panel
@onready var surface_label: Label = $Panel/MarginContainer/VBox/SurfaceLabel
@onready var wood_button: Button = $Panel/MarginContainer/VBox/WoodButton
@onready var concrete_button: Button = $Panel/MarginContainer/VBox/ConcreteButton
@onready var paint_button: Button = $Panel/MarginContainer/VBox/PaintButton
@onready var cancel_button: Button = $Panel/MarginContainer/VBox/CancelButton


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	wood_button.pressed.connect(_on_material_pressed.bind("madera"))
	concrete_button.pressed.connect(_on_material_pressed.bind("cemento"))
	paint_button.pressed.connect(_on_material_pressed.bind("pintura"))
	cancel_button.pressed.connect(_on_cancel_pressed)


## Muestra el panel identificando la superficie golpeada por el raycast.
func open_for(surface_id: String) -> void:
	surface_label.text = "Superficie:\n%s" % surface_id
	visible = true


func _on_material_pressed(material_name: String) -> void:
	visible = false
	material_selected.emit(material_name)


func _on_cancel_pressed() -> void:
	visible = false
	closed.emit()
