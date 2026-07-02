extends Node3D
## Escena principal Sprint 1: carga sample_room.gltf y genera colisión trimesh
## para cada mesh (muros + piso) en runtime, ya que las mallas no son convexas
## como conjunto. Esto reemplaza el paso manual "Create Collision > Trimesh
## Static Body" del editor, para que funcione también si el .gltf se
## regenera sin volver a tocar la escena a mano.
##
## _spawn_test_ground(): piso de seguridad SOLO para pruebas manuales en el
## editor (Sprint 2 abrió la puerta sur y no hay nada más allá de esa sala
## de ejemplo aislada). No es parte del contrato ni se exporta desde el
## pipeline — evita caer al vacío al cruzar la puerta mientras no exista
## un building.json con más de una habitación o terreno real.

@onready var room: Node3D = $Room


func _ready() -> void:
	_generate_trimesh_collision(room)
	_spawn_test_ground()


func _generate_trimesh_collision(node: Node) -> void:
	for child in node.get_children():
		if child is MeshInstance3D:
			var mesh_instance: MeshInstance3D = child
			if mesh_instance.mesh != null:
				# Crea un StaticBody3D hijo con CollisionShape3D trimesh
				# a partir de la malla, preservando el surface_id como nombre.
				mesh_instance.create_trimesh_collision()
		_generate_trimesh_collision(child)


func _spawn_test_ground() -> void:
	var plane_mesh := PlaneMesh.new()
	plane_mesh.size = Vector2(40.0, 40.0)

	var mesh_instance := MeshInstance3D.new()
	mesh_instance.name = "TestGround"
	mesh_instance.mesh = plane_mesh
	mesh_instance.position = Vector3(2.0, -0.5, -1.5)
	add_child(mesh_instance)
	mesh_instance.create_trimesh_collision()
