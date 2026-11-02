@tool
extends Node3D
## Adaptador reutilizable: un solo material de follaje compartido por árbol.
@export var profile_path := "res://season-profile.json"
var seasonal_material: ShaderMaterial

func _ready() -> void:
	var profile = JSON.parse_string(FileAccess.get_file_as_string(profile_path))
	seasonal_material = ShaderMaterial.new()
	seasonal_material.resource_name = profile.foliage_material
	seasonal_material.shader = preload("res://seasonal_foliage.gdshader")
	for pair in [["palette_dark", 0], ["palette_copper", 1], ["palette_gold", 2]]:
		seasonal_material.set_shader_parameter(pair[0], Color(profile.palette_srgb[pair[1]]).srgb_to_linear())
	seasonal_material.set_shader_parameter("season_amount", float(profile.amount))
	seasonal_material.set_shader_parameter("season_seed", float(int(profile.seed) % 8191))
	seasonal_material.set_shader_parameter("green_retention", float(profile.green_retention))
	seasonal_material.set_shader_parameter("patch_scale_m", float(profile.patch_scale_m))
	apply_season(self, profile.foliage_material)

func apply_season(node: Node, target: String) -> void:
	if node is MeshInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			var original = node.mesh.surface_get_material(i)
			if original.resource_name == target:
				seasonal_material.set_shader_parameter("foliage_texture", original.albedo_texture)
				node.set_surface_override_material(i, seasonal_material)
	for child in node.get_children():
		apply_season(child, target)

func set_season_amount(value: float) -> void:
	seasonal_material.set_shader_parameter("season_amount", clampf(value, 0, 1))
