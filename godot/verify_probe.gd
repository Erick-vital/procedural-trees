extends SceneTree

var triangles := 0
var materials := {}
var bounds := AABB()
var first := true
var failed := false
var output_dir := OS.get_environment("ARBOLES_F0_OUTPUT")

func check(ok: bool, message: String) -> void:
	if not ok:
		push_error(message)
		failed = true

func visit(node: Node) -> void:
	if node is MeshInstance3D:
		var mesh: Mesh = node.mesh
		var box: AABB = node.global_transform * mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
		for i in mesh.get_surface_count():
			var arrays := mesh.surface_get_arrays(i)
			var indices = arrays[Mesh.ARRAY_INDEX]
			var count: int = (indices.size() if indices != null and indices.size() else arrays[Mesh.ARRAY_VERTEX].size()) / 3
			triangles += count
			var mat := mesh.surface_get_material(i)
			check(mat != null, "Superficie sin material")
			if mat != null:
				materials[mat.resource_name] = materials.get(mat.resource_name, 0) + count
	for child in node.get_children():
		visit(child)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var packed = load("res://probe.glb")
	if not packed is PackedScene:
		push_error("GLB no importado como PackedScene")
		quit(1)
		return
	var asset = packed.instantiate()
	root.add_child(asset)
	visit(asset)
	var expected = JSON.parse_string(FileAccess.get_file_as_string(output_dir.path_join("blender-report.json")))
	var bmin = expected.bounds_blender[0]
	var bmax = expected.bounds_blender[1]
	var expected_min := Vector3(bmin[0], bmin[2], -bmax[1])
	var expected_max := Vector3(bmax[0], bmax[2], -bmin[1])
	check(bounds.position.distance_to(expected_min) < 0.0001, "Origen/orientación incorrectos")
	check(bounds.end.distance_to(expected_max) < 0.0001, "Escala/orientación incorrectas")
	check(triangles == 64, "Pérdida de triángulos")
	check(materials == {"Probe_Bark": 44, "Probe_Foliage": 20}, "Pérdida de curva, follaje o materiales")
	var report := {"godot": Engine.get_version_info().string, "triangles": triangles,
		"triangles_by_material": materials, "bounds_min": [bounds.position.x, bounds.position.y, bounds.position.z],
		"bounds_max": [bounds.end.x, bounds.end.y, bounds.end.z], "passed": not failed}
	var file := FileAccess.open(output_dir.path_join("godot-report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	print(JSON.stringify(report))
	if "--visual" in OS.get_cmdline_user_args() and not failed:
		var camera := Camera3D.new()
		root.add_child(camera)
		camera.position = Vector3(4, 3, 6)
		camera.look_at(Vector3(0.2, 1.25, 0))
		camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		camera.size = 3.6
		camera.current = true
		var light := DirectionalLight3D.new()
		root.add_child(light)
		light.rotation_degrees = Vector3(-35, -25, 0)
		light.light_energy = 1.5
		var env := WorldEnvironment.new()
		env.environment = Environment.new()
		env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.environment.ambient_light_color = Color.WHITE
		env.environment.ambient_light_energy = 0.5
		root.add_child(env)
		# Dejar que recursos y shaders terminen antes de capturar la ventana.
		for frame in range(8):
			await process_frame
			await RenderingServer.frame_post_draw
		await create_timer(0.5).timeout
		root.get_texture().get_image().save_png(output_dir.path_join("godot-preview.png"))
	quit(1 if failed else 0)
