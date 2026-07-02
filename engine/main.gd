extends Node3D
## Escena principal Sprint 1: carga sample_room.gltf y genera colisión trimesh
## para cada mesh (muros + piso) en runtime, ya que las mallas no son convexas
## como conjunto. Esto reemplaza el paso manual "Create Collision > Trimesh
## Static Body" del editor, para que funcione también si el .gltf se
## regenera sin volver a tocar la escena a mano.

@onready var room: Node3D = $Room


func _ready() -> void:
	_generate_trimesh_collision(room)


func _generate_trimesh_collision(node: Node) -> void:
	for child in node.get_children():
		if child is MeshInstance3D:
			var mesh_instance: MeshInstance3D = child
			if mesh_instance.mesh != null:
				# Crea un StaticBody3D hijo con CollisionShape3D trimesh
				# a partir de la malla, preservando el surface_id como nombre.
				mesh_instance.create_trimesh_collision()
		_generate_trimesh_collision(child)
