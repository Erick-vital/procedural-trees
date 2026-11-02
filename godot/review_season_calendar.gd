extends "res://verify_oak.gd"
## T0/T1: referencias fijas y auditoría del calendario, sin mezclar estaciones.
var current_materials := []

func binding_key(v: Vector3, uv: Vector2) -> String:
	var parts := PackedStringArray()
	for x in [v.x, v.y, v.z, uv.x, uv.y]: parts.append(str(roundi(x*10000)))
	return ",".join(parts)

func grid_key(v: Vector3, uv: Vector2, offset: Vector3i = Vector3i.ZERO) -> String:
	return "%d,%d,%d,%d,%d" % [floori(v.x/.002)+offset.x, floori(v.y/.002)+offset.y,
		floori(v.z/.002)+offset.z, roundi(uv.x*1000), roundi(uv.y*1000)]

func locate(v: Vector3, uv: Vector2, grid: Dictionary, state: Dictionary) -> Dictionary:
	# El importador comprime posiciones/UV: buscar por geometría con cota,
	# sin usar el propio calendario para decidir a qué grupo pertenece el vértice.
	var matches := {}
	for x in [-1, 0, 1]:
		for y in [-1, 0, 1]:
			for z in [-1, 0, 1]:
				for row in grid.get(grid_key(v, uv, Vector3i(x, y, z)), []):
					var p = Vector3(row.position[0], row.position[1], row.position[2])
					var delta = maxf(absf(v.x-p.x), maxf(absf(v.y-p.y), absf(v.z-p.z)))
					if delta <= .0005 and absf(uv.x-row.uv[0]) <= .00005 and absf(uv.y-row.uv[1]) <= .00005:
						matches[row.group_id] = row
						state.position_error = maxf(state.position_error, delta)
	if matches.size() != 1:
		state.missing += 1
		return {}
	return matches.values()[0]

func inspect_attributes(node: Node, expected: Dictionary, needed: bool, state: Dictionary) -> void:
	if node is MeshInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			var source = node.get_active_material(i)
			if source is StandardMaterial3D:
				var mat = source.duplicate()
				mat.roughness = .95
				mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
				mat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_OFF
				check(not mat.vertex_color_use_as_albedo, "Calendario usado como tinte")
				check(not mat.ao_on_uv2 and not mat.emission_on_uv2, "Material consume calendario como UV")
				node.set_surface_override_material(i, mat)
			else:
				check(source is ShaderMaterial, "Material inesperado")
			var arrays = node.mesh.surface_get_arrays(i)
			var vertices = arrays[Mesh.ARRAY_VERTEX]
			var uv = arrays[Mesh.ARRAY_TEX_UV]
			var uv2 = arrays[Mesh.ARRAY_TEX_UV2]
			var foliage: bool = node.mesh.surface_get_material(i).resource_name == "Painted_Foliage"
			if not foliage or not needed: continue
			check(uv2 != null and uv2.size() == vertices.size(), "UV2 ausentes o incompletos")
			if uv2 == null or uv2.size() != vertices.size(): continue
			var owners := []
			for j in vertices.size():
				var row = locate(node.global_transform*vertices[j], uv[j], expected, state)
				if row.is_empty(): continue
				var delta = maxf(absf(uv2[j].x-row.calendar[0]), absf(uv2[j].y-row.calendar[1]))
				check(delta < .0003, "Calendario UV2 distinto del grupo")
				state.error = maxf(state.error, delta)
				state.groups[row.group_id] = true
				state.vertices += 1
				owners.append(row.group_id)
			var ids = arrays[Mesh.ARRAY_INDEX]
			for j in range(0, ids.size(), 3):
				if owners.size() != vertices.size(): break
				var a = owners[ids[j]]
				check(a == owners[ids[j+1]] and a == owners[ids[j+2]], "Triángulo mezcla calendarios")
				state.faces[a] = state.faces.get(a, 0)+1
	for child in node.get_children(): inspect_attributes(child, expected, needed, state)

func run() -> void:
	var config = JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
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
	world.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	root.add_child(world)
	var expected := {}
	for row in config.binding:
		var k = grid_key(Vector3(row.position[0], row.position[1], row.position[2]), Vector2(row.uv[0], row.uv[1]))
		if not expected.has(k): expected[k] = []
		expected[k].append(row)
	var report := {"passed": false, "godot": Engine.get_version_info(), "assets": {}, "captures": []}
	for item in config.assets:
		var asset = load(item.resource).instantiate()
		root.add_child(asset)
		triangles = 0
		materials = {}
		first = true
		visit(asset)
		var state := {"error": 0.0, "groups": {}, "vertices": 0, "faces": {}, "missing": 0, "position_error": 0.0}
		inspect_attributes(asset, expected, item.get("calendar", false), state)
		check(triangles == int(config.triangles) and triangles < 7000 and materials.size() == 2, "Conteos importados distintos")
		if item.get("calendar", false):
			check(state.missing == 0, "Vértices sin correspondencia única dentro de la cota")
			check(state.groups.size() == int(config.group_count), "Grupos perdidos")
			for identifier in state.groups: check(int(state.faces.get(identifier, 0)) == 6, "Tres láminas incoherentes")
		report.assets[item.id] = {"triangles": triangles, "materials": materials,
			"max_uv2_error": state.error, "max_position_error": state.position_error,
			"groups": state.groups.size(), "vertices": state.vertices, "unmatched_vertices": state.missing}
		var center := bounds.get_center()
		var span := maxf(bounds.size.x, maxf(bounds.size.y, bounds.size.z))
		var views := [["front", Vector3(0,.1,1), 1.15], ["side", Vector3(1,.1,0), 1.15],
			["perspective", Vector3(1,.45,1), 1.15], ["back", Vector3(-1,.3,-1), 1.15],
			["far", Vector3(1,.45,1), 5.0]]
		if item.get("roundtrip", false): views = []
		for view in views:
			camera.position = center+view[1].normalized()*span*3
			camera.look_at(center)
			camera.size = span*view[2]
			for frame in range(3):
				await process_frame
				await RenderingServer.frame_post_draw
			var filename = config.id+"-"+item.id+"-"+view[0]+".png"
			check(root.get_texture().get_image().save_png(config.output.path_join(filename)) == OK, "Captura fallida")
			report.captures.append(filename)
		asset.free()
	report.passed = not failed
	var file = FileAccess.open(config.report, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ")+"\n")
	quit(1 if failed else 0)
