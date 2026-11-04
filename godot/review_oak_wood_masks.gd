extends "res://review_painted_oak_pilot.gd"
## Madera negra visible; follaje blanco recortado que conserva oclusión real.
func inspect(node: Node, expected: Dictionary) -> void:
	super.inspect(node, expected)
	wood_mask(node)

func wood_mask(node: Node) -> void:
	if node is MeshInstance3D:
		for i in range(node.mesh.get_surface_count()):
			var source = node.get_active_material(i)
			if source is ShaderMaterial:
				continue
			var shader = Shader.new()
			var mat = ShaderMaterial.new()
			if source.resource_name == "Painted_Bark":
				shader.code = "shader_type spatial; render_mode unshaded, cull_disabled; void fragment(){ALBEDO=vec3(0.0);}"
			else:
				shader.code = "shader_type spatial; render_mode unshaded, cull_disabled; uniform sampler2D atlas: source_color, filter_linear_mipmap; void fragment(){if(texture(atlas,UV).a<0.5){discard;} ALBEDO=vec3(1.0);}"
			mat.shader = shader
			if source.resource_name != "Painted_Bark":
				mat.set_shader_parameter("atlas", source.albedo_texture)
			node.set_surface_override_material(i, mat)
	for child in node.get_children():
		wood_mask(child)
