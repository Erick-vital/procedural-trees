extends "res://verify_oak.gd"

# Reutiliza la inspección de mallas; cámara y luces se fijan por pareja desde Q3.
func run() -> void:
	var study := OS.get_environment("ARBOLES_FUSION_STUDY")
	var config = JSON.parse_string(FileAccess.get_file_as_string(study.path_join("godot-input.json")))
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
		var packed = load("res://q3-fusion/" + item.id + ".glb")
		if not packed is PackedScene:
			check(false, "GLB no importado: " + item.id)
			continue
		var asset = packed.instantiate()
		root.add_child(asset)
		visit(asset)
		var manifest = JSON.parse_string(FileAccess.get_file_as_string(item.manifest))
		var low = manifest.metrics.bounds_blender[0]
		var high = manifest.metrics.bounds_blender[1]
		check(bounds.position.distance_to(Vector3(low[0], low[2], -high[1])) < .0001, item.id + ": orientación/origen")
		check(bounds.end.distance_to(Vector3(high[0], high[2], -low[1])) < .0001, item.id + ": escala")
		check(triangles == manifest.metrics.triangles, item.id + ": triángulos")
		for material_name in manifest.metrics.triangles_by_material:
			check(int(materials.get(material_name, -1)) == int(manifest.metrics.triangles_by_material[material_name]), item.id + ": material " + material_name)
		check(materials.size() == manifest.metrics.triangles_by_material.size(), item.id + ": materiales")
		var framing = item.framing
		var c = framing.center
		var center := Vector3(c[0], c[2], -c[1])
		var rig := {}
		for view in ["perspective", "game"]:
			camera.projection = Camera3D.PROJECTION_PERSPECTIVE
			camera.fov = rad_to_deg(2 * atan(18.0 / 50.0))
			camera.position = center + Vector3(1.3, .65, 1.8).normalized() * float(framing.span) * (7.5 if view == "game" else 2.5)
			camera.look_at(center)
			rig[view] = {"position": [camera.position.x, camera.position.y, camera.position.z], "rotation": [camera.rotation.x, camera.rotation.y, camera.rotation.z], "fov": camera.fov}
			if "--visual" in OS.get_cmdline_user_args():
				for frame in range(8):
					await process_frame
					await RenderingServer.frame_post_draw
				check(root.get_texture().get_image().save_png(item.output.path_join("godot-" + view + ".png")) == OK, "Captura fallida")
		reports[item.id] = {"triangles": triangles, "materials": materials, "height_m": bounds.size.y, "cameras": rig}
		asset.free()
	var file := FileAccess.open(study.path_join("godot-report.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed": not failed, "assets": reports, "godot": Engine.get_version_info().string}, "  ") + "\n")
	quit(1 if failed else 0)
