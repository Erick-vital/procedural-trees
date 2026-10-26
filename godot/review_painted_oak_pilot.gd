extends "res://review_painted_pine.gd"
## Pase independiente de máscara: conserva alfa y elimina iluminación/color.
func inspect(node: Node, expected: Dictionary) -> void:
	super.inspect(node, expected)
	var config = JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	if config.get('mask_pass', false):
		for mat in draw_materials:
			mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			mat.albedo_color = Color(0, 0, 0, 1)
