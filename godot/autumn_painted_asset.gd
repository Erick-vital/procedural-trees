@tool
extends Node3D
## Configuración del material estándar; color otoñal ya embebido en el GLB.
func _ready() -> void:
	configure(self)

func configure(node: Node) -> void:
	if node is MeshInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			var source = node.mesh.surface_get_material(i)
			if source.resource_name != "Painted_Foliage": continue
			var mat = source.duplicate()
			mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			mat.alpha_scissor_threshold = .5
			mat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_OFF
			mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
			node.set_surface_override_material(i, mat)
	for child in node.get_children(): configure(child)
