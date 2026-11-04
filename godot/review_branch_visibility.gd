extends "res://review_painted_oak_pilot.gd"
## Diagnóstico auxiliar: madera roja, follaje blanco con su alfa real.
func inspect(node: Node, expected: Dictionary) -> void:
	super.inspect(node, expected)
	if node is MeshInstance3D:
		for i in node.mesh.get_surface_count():
			var source: StandardMaterial3D = node.get_active_material(i)
			var leaf: bool = source.resource_name == 'Painted_Foliage'
			var shader := Shader.new()
			shader.code = "shader_type spatial; render_mode unshaded, cull_disabled; uniform sampler2D atlas : filter_linear_mipmap_anisotropic; uniform bool foliage; void fragment(){ if(foliage && texture(atlas,UV).a < 0.5){discard;} ALBEDO=foliage?vec3(1.0):vec3(1.0,0.0,0.0); }"
			var material := ShaderMaterial.new()
			material.shader = shader
			material.set_shader_parameter('foliage',leaf)
			material.set_shader_parameter('atlas',source.albedo_texture)
			node.set_surface_override_material(i,material)
