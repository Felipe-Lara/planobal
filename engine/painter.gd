extends Node
## Sprint 5 — Repintado + persistencia.
## Lanza un raycast desde la cámara del player al presionar la acción "paint"
## (click izquierdo, con el mouse capturado en modo FPS). Si golpea una
## malla pintable, abre PaintMenu para elegir madera/cemento/pintura y
## aplica un StandardMaterial3D vía material_override (no toca el mesh
## resource compartido del .gltf importado).
##
## surface_id = nombre del nodo MeshInstance3D golpeado por el raycast.
## OJO: viene CON el prefijo de piso (ej. "p0_room_sala.piso",
## "p1_w_sur_jamb_0.cara_interior") porque building.json puede tener el
## mismo plano repetido en varios pisos con el mismo nombre "puro" de
## superficie — sin el prefijo no podríamos pintar cada piso por separado.
## Ese nombre completo (con prefijo) es la clave real que usamos acá y la
## que se persiste en paint_state.json.
##
## paint_state.json es el ÚNICO archivo que el engine escribe (contrato,
## ver pipeline/schema/paint_state.py). Se guarda en res://paint_state.json
## (junto al proyecto, fácil de inspeccionar a mano).

const RAY_LENGTH := 6.0
const PAINT_STATE_PATH := "res://paint_state.json"
const MATERIALS_DIR := "res://assets/materials/"

## Asignados por main.gd tras instanciar la escena (evita acoplar este
## script a paths de árbol específicos de Main).
var camera: Camera3D
var room: Node3D
var paint_menu: CanvasLayer

## surface_id -> nombre de material ("madera" | "cemento" | "pintura").
## Estado en memoria, espejo de lo que se persiste en paint_state.json.
var paint_state: Dictionary = {}

## Cache de StandardMaterial3D por nombre de material, para no recargar
## texturas repetidas veces al pintar varias superficies con el mismo material.
var _material_cache: Dictionary = {}

var _current_target: MeshInstance3D = null


func setup(p_camera: Camera3D, p_room: Node3D, p_paint_menu: CanvasLayer) -> void:
	camera = p_camera
	room = p_room
	paint_menu = p_paint_menu
	paint_menu.material_selected.connect(_on_material_selected)
	paint_menu.closed.connect(_on_menu_closed)


## Lee paint_state.json (si existe) y aplica cada material a su
## MeshInstance3D correspondiente. Si un surface_id no existe en la escena
## actual (el .gltf fue regenerado), se ignora con un aviso — nunca crashea.
func load_paint_state() -> void:
	if not FileAccess.file_exists(PAINT_STATE_PATH):
		return

	var file := FileAccess.open(PAINT_STATE_PATH, FileAccess.READ)
	var text := file.get_as_text()
	file.close()

	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("painter: paint_state.json inválido o corrupto, se ignora")
		return

	for surface_id: String in parsed.keys():
		var material_name: String = parsed[surface_id]
		var mesh_instance := _find_mesh_by_name(room, surface_id)
		if mesh_instance == null:
			print("painter: surface_id '%s' de paint_state.json no existe en la escena actual, se ignora" % surface_id)
			continue
		_apply_material(mesh_instance, material_name)
		paint_state[surface_id] = material_name


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("paint") and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_try_raycast()


func _try_raycast() -> void:
	if camera == null:
		return

	var from := camera.global_position
	var to := from + (-camera.global_transform.basis.z) * RAY_LENGTH
	var space_state := camera.get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(from, to)
	var result := space_state.intersect_ray(query)
	if result.is_empty():
		return

	# create_trimesh_collision() crea un StaticBody3D hijo del MeshInstance3D
	# original; el collider golpeado es ese StaticBody3D, así que subimos al
	# padre para llegar a la malla real y leer su surface_id (= nombre).
	var collider: Object = result.get("collider")
	if collider == null or not (collider is Node):
		return
	var parent := (collider as Node).get_parent()
	if parent == null or not (parent is MeshInstance3D):
		return

	var mesh_instance := parent as MeshInstance3D
	if mesh_instance.name == "TestGround":
		return  # piso de seguridad de pruebas, no es una superficie pintable real

	_current_target = mesh_instance
	paint_menu.open_for(mesh_instance.name)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	get_tree().paused = true


func _on_material_selected(material_name: String) -> void:
	if _current_target == null:
		_close_paint_menu()
		return
	_apply_material(_current_target, material_name)
	paint_state[_current_target.name] = material_name
	_save_paint_state()
	_close_paint_menu()


func _on_menu_closed() -> void:
	_close_paint_menu()


func _close_paint_menu() -> void:
	get_tree().paused = false
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_current_target = null


func _apply_material(mesh_instance: MeshInstance3D, material_name: String) -> void:
	mesh_instance.material_override = _get_or_create_material(material_name)


func _get_or_create_material(material_name: String) -> StandardMaterial3D:
	if _material_cache.has(material_name):
		return _material_cache[material_name]

	var base_path := MATERIALS_DIR + material_name + "/"
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = load(base_path + "albedo.jpg")
	mat.roughness_texture = load(base_path + "roughness.jpg")
	mat.normal_enabled = true
	mat.normal_texture = load(base_path + "normal.jpg")

	_material_cache[material_name] = mat
	return mat


func _save_paint_state() -> void:
	var file := FileAccess.open(PAINT_STATE_PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(paint_state, "\t"))
	file.close()


func _find_mesh_by_name(node: Node, target_name: String) -> MeshInstance3D:
	for child in node.get_children():
		if child is MeshInstance3D and child.name == target_name:
			return child
		var found := _find_mesh_by_name(child, target_name)
		if found != null:
			return found
	return null
