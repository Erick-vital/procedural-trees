extends "res://review_painted_oak_pilot.gd"
## Follaje visible negro; madera blanca que conserva su oclusión real.
func inspect(node: Node, expected: Dictionary) -> void:
	super.inspect(node, expected)
	for mat in draw_materials:
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		if mat.resource_name == "Painted_Bark":
			mat.albedo_texture = null
			mat.albedo_color = Color.WHITE
		else:
			mat.albedo_color = Color.BLACK
