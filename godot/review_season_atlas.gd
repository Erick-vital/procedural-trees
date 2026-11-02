extends "res://verify_oak.gd"
## T2: extremos fijos sobre una rama y tablero de las 24 celdas; sin mezcla.
func materials_for(node: Node, texture: Texture2D) -> void:
	if node is MeshInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			var mat = node.mesh.surface_get_material(i).duplicate() as StandardMaterial3D
			mat.roughness = .95
			if mat.resource_name == "Painted_Foliage":
				mat.albedo_texture = texture
				mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
				mat.alpha_scissor_threshold = .5
				mat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_OFF
				mat.cull_mode = BaseMaterial3D.CULL_DISABLED
				mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
			node.set_surface_override_material(i,mat)
	for child in node.get_children(): materials_for(child,texture)

func board(texture: Texture2D) -> Node3D:
	var node := Node3D.new()
	for i in 24:
		var mesh := MeshInstance3D.new()
		var quad := QuadMesh.new()
		quad.size = Vector2(.92,.92)
		# QuadMesh UV arriba→abajo: atlas PNG en el mismo orden.
		mesh.mesh = quad
		mesh.position = Vector3(i%5,4-i/5,0)
		node.add_child(mesh)
		var mat := StandardMaterial3D.new()
		mat.resource_name = "Painted_Foliage"
		mat.uv1_scale = Vector3(.2,.2,1)
		mat.uv1_offset = Vector3((i%5)*.2,(i/5)*.2,0)
		quad.material = mat
	materials_for(node,texture)
	return node

func run() -> void:
	var output = OS.get_cmdline_user_args()[0]
	root.size = Vector2i(700,700)
	root.msaa_3d = Viewport.MSAA_4X
	var cam := Camera3D.new()
	root.add_child(cam);cam.current=true;cam.projection=Camera3D.PROJECTION_ORTHOGONAL
	var sun := DirectionalLight3D.new()
	root.add_child(sun);sun.rotation_degrees=Vector3(-35,-25,0);sun.light_energy=1.2;sun.shadow_enabled=true
	var env := WorldEnvironment.new()
	env.environment=Environment.new()
	env.environment.background_mode=Environment.BG_COLOR
	env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color=Color.WHITE;env.environment.ambient_light_energy=.5
	env.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	root.add_child(env)
	var report := {"passed":false,"godot":Engine.get_version_info(),"captures":[],"branch":{}}
	for style in ["summer-original","autumn-original","summer-common","autumn-common","summer-padded","autumn-padded"]:
		var texture = load("res://"+style+".png") as Texture2D
		check(texture.get_width()==2000 and texture.get_height()==2000,"Resolución atlas incorrecta")
		check(texture.get_image().has_mipmaps(),"Mipmaps ausentes")
		for scope in ["board","branch"]:
			var asset = board(texture) if scope=="board" else load("res://branch.glb").instantiate()
			root.add_child(asset)
			if scope=="branch":materials_for(asset,texture)
			triangles=0;materials={};first=true;visit(asset)
			if scope=="branch":
				check(triangles<7000 and materials.size()==2,"Presupuesto rama incorrecto")
				report.branch[style]={"triangles":triangles,"materials":materials}
			var center := bounds.get_center()
			var span := maxf(bounds.size.x,maxf(bounds.size.y,bounds.size.z))
			for bg in ["light","dark"]:
				env.environment.background_color=Color("EEE9DF") if bg=="light" else Color("182027")
				for distance in ["near","medium","far"]:
					cam.size=span*{"near":1.15,"medium":2.8,"far":6.0}[distance]
					cam.position=center+(Vector3(0,0,3) if scope=="board" else Vector3(1,.45,1).normalized()*3)*span
					cam.look_at(center)
					for frame in 3:
						await process_frame
						await RenderingServer.frame_post_draw
					var filename=scope+"-"+style+"-"+bg+"-"+distance+".png"
					check(root.get_texture().get_image().save_png(output.path_join(filename))==OK,"Captura fallida")
					report.captures.append(filename)
			asset.free()
	report.passed=not failed
	FileAccess.open(output.path_join("godot-report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(1 if failed else 0)
