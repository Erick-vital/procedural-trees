extends Node3D
## T5 0.1.0: recursos compartidos, estado por instancia y mallas exclusivas del paquete.
const PAINT := preload("res://paint_transition.tres")
const BARK := preload("res://bark.tres")
const LEGACY_SHADER := preload("res://legacy_control.gdshader")
var phase := 0.0
var mode := 0
var foliage_meshes: Array[MeshInstance3D] = []
var foliage_surfaces: Array[int] = []
var legacy: ShaderMaterial

func _ready() -> void:
	legacy = ShaderMaterial.new()
	legacy.shader = LEGACY_SHADER
	legacy.resource_name = "Painted_Foliage"
	var profile = JSON.parse_string(FileAccess.get_file_as_string("res://legacy-profile.json"))
	for pair in [["palette_dark",0],["palette_copper",1],["palette_gold",2]]:
		legacy.set_shader_parameter(pair[0],Color(profile.palette_srgb[pair[1]]).srgb_to_linear())
	for key in ["green_retention","patch_scale_m"]:legacy.set_shader_parameter(key,profile[key])
	legacy.set_shader_parameter("season_seed",float(int(profile.seed)%8191))
	legacy.set_shader_parameter("foliage_texture",preload("res://resources/summer.png"))
	configure(self)
	set_phase(phase)

func configure(node: Node) -> void:
	if node is MeshInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			if node.mesh.surface_get_material(i).resource_name == "Painted_Bark":
				node.mesh.surface_set_material(i,BARK)
				continue
			if node.mesh.surface_get_material(i).resource_name != "Painted_Foliage":continue
			foliage_meshes.append(node)
			foliage_surfaces.append(i)
			node.mesh.surface_set_material(i,PAINT)
			node.set_surface_override_material(i,PAINT)
	for child in node.get_children():configure(child)

func set_phase(value: float) -> bool:
	if not is_finite(value) or value < 0.0 or value > 1.0:return false
	phase = value
	for mesh in foliage_meshes:mesh.set_instance_shader_parameter("season_phase",phase)
	if legacy != null:legacy.set_shader_parameter("season_amount",phase)
	return true

func set_mode(value: int) -> bool:
	if value < 0 or value > 4:return false
	mode = value
	for j in foliage_meshes.size():
		foliage_meshes[j].set_surface_override_material(foliage_surfaces[j],legacy if mode==4 else PAINT)
		foliage_meshes[j].set_instance_shader_parameter("season_mode",mode)
	return true

func set_mask(enabled: bool) -> void:
	for mesh in foliage_meshes:mesh.set_instance_shader_parameter("mask_mode",enabled)
