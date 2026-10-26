@tool
extends Node3D
## Adjuntar al nodo raíz del GLB PP4 para aplicar la decisión PP3 en Godot.
## Filtrado anisotrópico y sombras dobles son propiedades del motor, no del GLB.

func _ready() -> void:
	configure(self)

func configure(node: Node) -> void:
	if node is MeshInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for index in node.mesh.get_surface_count():
			var source = node.mesh.surface_get_material(index)
			if not source is StandardMaterial3D or not source.resource_name.begins_with('Painted_'):
				continue
			var mat: StandardMaterial3D = source.duplicate()
			mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			mat.roughness = .95
			mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
			if mat.resource_name == 'Painted_Foliage':
				mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
				mat.alpha_scissor_threshold = .5
				mat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_OFF
			node.set_surface_override_material(index, mat)
	for child in node.get_children():
		configure(child)
