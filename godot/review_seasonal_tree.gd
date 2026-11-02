extends "res://verify_oak.gd"
## Verificación importada y capturas reales con condiciones comunes.
func inspect_season(node: Node, shader_material: ShaderMaterial) -> void:
	if node is MeshInstance3D:
		for i in node.mesh.get_surface_count():
			var original = node.mesh.surface_get_material(i)
			var active = node.get_active_material(i)
			if original.resource_name == "Painted_Foliage":
				check(active == shader_material, "Follaje sin material estacional compartido")
				check(active.get_shader_parameter("foliage_texture") == original.albedo_texture, "Atlas alterado")
			else:
				check(active == original, "Madera modificada")
			var arrays = node.mesh.surface_get_arrays(i)
			check(arrays[Mesh.ARRAY_TEX_UV] != null, "UV ausentes")
			for n in arrays[Mesh.ARRAY_NORMAL]:
				check(n.is_finite() and absf(n.length()-1) < .002, "Normal inválida")
	for child in node.get_children(): inspect_season(child, shader_material)

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
		var asset = load("res://"+item.id+".tscn").instantiate()
		root.add_child(asset)
		triangles = 0
		materials = {}
		first = true
		visit(asset)
		inspect_season(asset, asset.seasonal_material)
		check(triangles == int(item.metrics.triangles) and triangles < 7000, "Presupuesto geométrico")
		check(materials.size() == 2, "Presupuesto de materiales")
		report.cases[item.id] = {"triangles": triangles, "materials": materials}
		var center := bounds.get_center()
		var span := maxf(bounds.size.x, maxf(bounds.size.y, bounds.size.z))
		var views := [["front", Vector3(0,.1,1), 1.15], ["side", Vector3(1,.1,0), 1.15],
			["perspective", Vector3(1,.45,1), 1.15], ["back", Vector3(-1,.3,-1), 1.15],
			["below", Vector3(1,-.5,1), 1.15], ["medium", Vector3(1,.45,1), 3.0],
			["far", Vector3(1,.45,1), 7.0], ["repeat", Vector3(1,.45,1), 1.15]]
		for season in ["summer", "autumn"]:
			asset.set_season_amount(0.0 if season == "summer" else 1.0)
			for view in views:
				camera.position = center+view[1].normalized()*span*3
				camera.look_at(center)
				camera.size = span*view[2]
				for frame in range(3):
					await process_frame
					await RenderingServer.frame_post_draw
				var filename = item.id+"-"+season+"-"+view[0]+".png"
				check(root.get_texture().get_image().save_png(output.path_join(filename)) == OK, "Captura fallida")
				report.captures.append(filename)
		asset.free()
	report.passed = not failed
	var file = FileAccess.open(output.path_join("godot-report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ")+"\n")
	quit(1 if failed else 0)
