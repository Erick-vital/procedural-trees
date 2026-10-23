extends SceneTree

var output_dir := OS.get_environment("ARBOLES_F1_OUTPUT")
var asset_prefix := "res://f1/"
var case_names := ["joven", "adulto", "viejo"]
var failed := false
var triangles := 0
var materials := {}
var bounds := AABB()
var first := true

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
	if OS.has_environment("ARBOLES_F2_OUTPUT"):
		output_dir = OS.get_environment("ARBOLES_F2_OUTPUT")
		asset_prefix = OS.get_environment("ARBOLES_ASSET_PREFIX") if OS.has_environment("ARBOLES_ASSET_PREFIX") else "res://f2/"
		case_names = []
		var cases = JSON.parse_string(FileAccess.get_file_as_string(output_dir.path_join("cases.json")))
		for item in cases:
			case_names.append(item.id)
	var reports := {}
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.current = true
	var light := DirectionalLight3D.new()
	root.add_child(light)
	light.rotation_degrees = Vector3(-35, -25, 0)
	light.light_energy = 1.2
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color.WHITE
	env.environment.ambient_light_energy = 0.5
	root.add_child(env)
	for name in case_names:
		triangles = 0
		materials = {}
		first = true
		var packed = load(asset_prefix + name + ".glb")
		if not packed is PackedScene:
			check(false, "GLB no importado: " + name)
			continue
		var asset = packed.instantiate()
		root.add_child(asset)
		visit(asset)
		var manifest = JSON.parse_string(FileAccess.get_file_as_string(output_dir.path_join(name + "/manifest.json")))
		var metrics = manifest.metrics
		var low = metrics.bounds_blender[0]
		var high = metrics.bounds_blender[1]
		check(bounds.position.distance_to(Vector3(low[0], low[2], -high[1])) < 0.0001, name + ": orientación/origen")
		check(bounds.end.distance_to(Vector3(high[0], high[2], -low[1])) < 0.0001, name + ": escala")
		check(triangles == metrics.triangles, name + ": triángulos perdidos")
		check(materials.size() == metrics.triangles_by_material.size(), name + ": cantidad de materiales")
		for material_name in metrics.triangles_by_material:
			check(materials.has(material_name) and int(materials.get(material_name, -1)) == int(metrics.triangles_by_material[material_name]),
				name + ": corteza/follaje/material perdidos: " + material_name)
		reports[name] = {"triangles": triangles, "materials": materials, "height_m": bounds.size.y}
		if "--visual" in OS.get_cmdline_user_args():
			var center := bounds.get_center()
			var span := maxf(bounds.size.x, maxf(bounds.size.y, bounds.size.z))
			camera.position = center + Vector3(1.3, 0.8, 1.8).normalized() * span * 2.5
			camera.look_at(center)
			camera.size = span * 1.2
			for frame in range(8):
				await process_frame
				await RenderingServer.frame_post_draw
			await create_timer(0.4).timeout
			check(root.get_texture().get_image().save_png(output_dir.path_join(name + "/godot.png")) == OK, "No se guardó captura")
		asset.free()
	var report := {"passed": not failed, "godot": Engine.get_version_info().string, "assets": reports}
	var file := FileAccess.open(output_dir.path_join("godot-report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	print(JSON.stringify(report))
	quit(1 if failed else 0)
