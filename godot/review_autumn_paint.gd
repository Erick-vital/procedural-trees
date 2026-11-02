extends "res://review_seasonal_tree.gd"

func inspect_standard(node: Node) -> void:
	if node is MeshInstance3D:
		for i in node.mesh.get_surface_count():
			var mat = node.get_active_material(i)
			check(mat is StandardMaterial3D, "Pintura depende de shader personalizado")
			if mat.resource_name == "Painted_Foliage":
				check(mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR, "Alfa incorrecta")
				check(absf(mat.alpha_scissor_threshold-.5) < .001, "Umbral incorrecto")
				check(mat.albedo_texture.get_width() == 2000, "Atlas incorrecto")
	for child in node.get_children(): inspect_standard(child)

func mask_materials(node: Node, enabled: bool) -> void:
	if node is MeshInstance3D:
		for i in node.mesh.get_surface_count():
			var source = node.get_active_material(i)
			if source is ShaderMaterial:
				source.set_shader_parameter("mask_mode", enabled)
			else:
				var mat = source.duplicate()
				mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				mat.albedo_color = Color.BLACK
				node.set_surface_override_material(i, mat)
	for child in node.get_children(): mask_materials(child, enabled)

func run() -> void:
	var output = OS.get_cmdline_user_args()[0]
	var config = JSON.parse_string(FileAccess.get_file_as_string("res://preview-config.json"))
	root.size = Vector2i(900, 900)
	root.msaa_3d = Viewport.MSAA_4X
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.current = true
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = .01
	camera.far = 300
	var sun := DirectionalLight3D.new()
	root.add_child(sun)
	sun.rotation_degrees = Vector3(-35, -25, 0)
	sun.light_energy = 1.2
	sun.shadow_enabled = true
	var world := WorldEnvironment.new()
	world.environment = Environment.new()
	world.environment.background_mode = Environment.BG_COLOR
	world.environment.background_color = Color("EEE9DF")
	world.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	world.environment.ambient_light_color = Color.WHITE
	world.environment.ambient_light_energy = .5
	root.add_child(world)
	var report := {"passed": false, "godot": Engine.get_version_info(), "cases": {}, "captures": []}
	for item in config.cases:
		for style in ["summer", "shader", "painted"]:
			var prefix := "painted-" if style == "painted" else ""
			var asset = load("res://"+prefix+item.id+".tscn").instantiate()
			root.add_child(asset)
			triangles = 0
			materials = {}
			first = true
			visit(asset)
			if style == "painted": inspect_standard(asset)
			else:
				inspect_season(asset, asset.seasonal_material)
				asset.set_season_amount(0.0 if style == "summer" else 1.0)
			check(triangles == int(item.metrics.triangles) and triangles < 7000, "Triángulos incorrectos")
			check(materials.size() == 2, "Cantidad de materiales incorrecta")
			report.cases[item.id+"-"+style] = {"triangles": triangles, "materials": materials}
			var center := bounds.get_center()
			var span := maxf(bounds.size.x, maxf(bounds.size.y, bounds.size.z))
			var views := [["front", Vector3(0,.1,1), 1.15], ["side", Vector3(1,.1,0), 1.15],
				["perspective", Vector3(1,.45,1), 1.15], ["back", Vector3(-1,.3,-1), 1.15],
				["below", Vector3(1,-.5,1), 1.15], ["medium", Vector3(1,.45,1), 3.0],
				["far", Vector3(1,.45,1), 7.0], ["repeat", Vector3(1,.45,1), 1.15]]
			for mask in [false, true]:
				if mask: mask_materials(asset, true)
				world.environment.background_color = Color.WHITE if mask else Color("EEE9DF")
				for view in views:
					if mask and view[0] not in ["perspective", "side", "back"]: continue
					camera.position = center+view[1].normalized()*span*3
					camera.look_at(center)
					camera.size = span*view[2]
					for frame in range(3):
						await process_frame
						await RenderingServer.frame_post_draw
					var filename = item.id+"-"+style+"-"+("mask-" if mask else "")+view[0]+".png"
					check(root.get_texture().get_image().save_png(output.path_join(filename)) == OK, "Captura fallida")
					report.captures.append(filename)
			asset.free()
	report.passed = not failed
	var file = FileAccess.open(output.path_join("godot-report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ")+"\n")
	quit(1 if failed else 0)
