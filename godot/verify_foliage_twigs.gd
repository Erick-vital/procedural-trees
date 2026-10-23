extends "res://verify_oak.gd"

func converted(v: Array) -> Vector3:
	return Vector3(v[0], v[2], -v[1])

func inspect_materials(node: Node) -> void:
	if node is MeshInstance3D:
		for i in node.mesh.get_surface_count():
			var mat = node.mesh.surface_get_material(i)
			check(mat is StandardMaterial3D, "Material inesperado")
			if mat is StandardMaterial3D:
				check(mat.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED, "Transparencia inesperada")
				check(mat.albedo_texture == null, "Textura inesperada")
				if mat.resource_name == "RF1_Leaf":
					check(mat.cull_mode == BaseMaterial3D.CULL_DISABLED, "Reverso descartado")
	for child in node.get_children():
		inspect_materials(child)

func run() -> void:
	var study := OS.get_environment("ARBOLES_RF2_TWIGS_STUDY")
	var input_path := study.path_join("godot-input.json")
	var report_path := study.path_join("godot-report.json")
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--input="):
			input_path = argument.trim_prefix("--input=")
		if argument.begins_with("--report="):
			report_path = argument.trim_prefix("--report=")
	var config = JSON.parse_string(FileAccess.get_file_as_string(input_path))
	root.size = Vector2i(900, 900)
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.current = true
	var light := DirectionalLight3D.new()
	root.add_child(light)
	light.rotation_degrees = Vector3(-35, -25, 0)
	light.light_energy = 1.2
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color.WHITE
	environment.environment.ambient_light_energy = .5
	root.add_child(environment)
	var reports := {}
	for item in config:
		triangles = 0
		materials = {}
		first = true
		var packed = load("res://rf2_twigs/" + item.id + ".glb")
		if not packed is PackedScene:
			check(false, "GLB no importado: " + item.id)
			continue
		var asset = packed.instantiate()
		root.add_child(asset)
		visit(asset)
		inspect_materials(asset)
		var manifest = JSON.parse_string(FileAccess.get_file_as_string(item.folder.path_join("manifest.json")))
		var metrics = manifest.metrics
		var low = metrics.bounds_blender[0]
		var high = metrics.bounds_blender[1]
		check(bounds.position.distance_to(Vector3(low[0], low[2], -high[1])) < .0001, item.id + ": origen/ejes")
		check(bounds.end.distance_to(Vector3(high[0], high[2], -low[1])) < .0001, item.id + ": escala")
		check(triangles == metrics.triangles, item.id + ": triángulos")
		check(materials.size() == metrics.triangles_by_material.size(), item.id + ": materiales")
		for name in metrics.triangles_by_material:
			check(int(materials.get(name, -1)) == int(metrics.triangles_by_material[name]), item.id + ": " + name)
		var cameras = JSON.parse_string(FileAccess.get_file_as_string(item.folder.path_join("cameras.json")))
		var rig := {}
		for view in cameras:
			var settings = cameras[view]
			camera.projection = Camera3D.PROJECTION_ORTHOGONAL
			camera.size = settings.ortho_scale
			camera.position = converted(settings.location)
			var columns = settings.basis_columns
			camera.basis = Basis(converted(columns[0]), converted(columns[1]), converted(columns[2]))
			rig[view] = settings
			if "--visual" in OS.get_cmdline_user_args() and item.capture:
				# Dos dibujos completados después de cambiar cámara/asset. Esperar
				# ocho por vista hacía depender el timeout de la cadencia de ventana.
				for frame in range(2):
					await process_frame
					await RenderingServer.frame_post_draw
				check(root.get_texture().get_image().save_png(item.folder.path_join("godot-"+view+".png")) == OK, "Captura fallida")
		reports[item.id] = {"triangles": triangles, "materials": materials, "cameras": rig}
		print(item.id + ": verificado/capturado")
		asset.free()
	var file := FileAccess.open(report_path, FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed": not failed, "godot": Engine.get_version_info().string,
		"renderer": "gl_compatibility", "light_rotation_deg": [-35, -25, 0], "light_energy": 1.2,
		"ambient_energy": .5, "assets": reports}, "  ") + "\n")
	quit(1 if failed else 0)
