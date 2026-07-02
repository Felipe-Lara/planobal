extends CharacterBody3D
## Controlador de primera persona básico: WASD + mouse look + gravedad.
## Sprint 1 — solo movimiento y colisión. Sin raycast de repintado (Sprint 5).
## Sprint 4 — Esc ya no libera el mouse directamente: main.gd escucha
## "ui_cancel" y abre/cierra el menú de pausa, que a su vez captura/libera
## el mouse. Este script expone spawn_position + reset_to_spawn() para que
## el menú pueda "Reiniciar posición".

const SPEED := 4.0
const JUMP_VELOCITY := 4.5
const MOUSE_SENSITIVITY := 0.0025

@onready var camera: Camera3D = $Camera3D

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8)

## Posición/rotación de spawn originales, capturadas en _ready() para que
## el menú de pausa pueda usarlas en "Reiniciar posición".
var spawn_transform: Transform3D


func _ready() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	spawn_transform = global_transform


## Teletransporta al player de vuelta a su posición/rotación de spawn
## original y anula la velocidad para que no siga la inercia previa.
func reset_to_spawn() -> void:
	global_transform = spawn_transform
	velocity = Vector3.ZERO


## Teletransporta al player a la elevación (Y) de otro piso, manteniendo
## su X/Z actual. Usado por el menú de pausa para cambiar de piso.
func teleport_to_elevation(elevation: float) -> void:
	global_position.y = elevation + spawn_transform.origin.y
	velocity = Vector3.ZERO


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.relative.x * MOUSE_SENSITIVITY)
		camera.rotate_x(-event.relative.y * MOUSE_SENSITIVITY)
		camera.rotation.x = clamp(camera.rotation.x, deg_to_rad(-89.0), deg_to_rad(89.0))


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()

	if direction:
		velocity.x = direction.x * SPEED
		velocity.z = direction.z * SPEED
	else:
		velocity.x = move_toward(velocity.x, 0.0, SPEED)
		velocity.z = move_toward(velocity.z, 0.0, SPEED)

	move_and_slide()
