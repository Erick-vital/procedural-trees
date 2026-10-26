extends "res://verify_oak.gd"
# PP3 aislada: texturas permitidas aquí; verificadores históricos intactos.
var material_rows := []
var draw_materials := []

func converted(v: Array) -> Vector3:
	return Vector3(v[0], v[2], -v[1])

func inspect(node: Node, expected: Dictionary) -> void:
	if node is MeshInstance3D:
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			var arrays = node.mesh.surface_get_arrays(i)
			var vertices = arrays[Mesh.ARRAY_VERTEX]
			var normals = arrays[Mesh.ARRAY_NORMAL]
			var uv = arrays[Mesh.ARRAY_TEX_UV]
			check(normals != null and normals.size() == vertices.size(), "Normales ausentes")
			check(uv != null and uv.size() == vertices.size(), "UV ausentes")
			for n in normals:
				check(n.is_finite() and absf(n.length()-1) < .002, "Normal inválida")
			for p in uv:
				check(p.is_finite(), "UV no finita")
			var source = node.mesh.surface_get_material(i)
			check(source is StandardMaterial3D, "Material importado inesperado")
			var mat: StandardMaterial3D = source.duplicate()
			node.set_surface_override_material(i, mat)
			var painted: bool = mat.resource_name.begins_with('Painted_')
			var foliage: bool = mat.resource_name == 'Painted_Foliage'
			check(mat.cull_mode == BaseMaterial3D.CULL_DISABLED, "Reversos descartados")
			check(not mat.normal_enabled, "Mapa normal inesperado")
			if painted:
				check(mat.albedo_texture != null, "Textura ausente")
				check(absf(mat.roughness-.95) < .001, "Rugosidad alterada")
			else:
				check(mat.albedo_texture == null, "Textura en original")
			if foliage:
				check(mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR, "GLB sin Alpha Scissor")
				check(absf(mat.alpha_scissor_threshold-.5) < .001, "Umbral alfa alterado")
			else:
				check(mat.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED, "Madera/original transparente")
			var row := {'name':mat.resource_name,'transparency':mat.transparency,'cutoff':mat.alpha_scissor_threshold,
				'roughness':mat.roughness,'cull_mode':mat.cull_mode,'normal_map':mat.normal_enabled,
				'imported_texture_filter':mat.texture_filter,'shadow_casting':node.cast_shadow}
			if painted:
				var im: Image = mat.albedo_texture.get_image()
				row['texture_size'] = [im.get_width(),im.get_height()]
				row['mipmaps'] = im.has_mipmaps()
				row['mipmap_count'] = im.get_mipmap_count()
				check(im.get_width()==1254 and im.get_height()==1254, 'Dimensiones de textura alteradas')
				check(im.has_mipmaps(), 'Mipmaps ausentes')
				# Ajuste explícito compartido entre variantes pintadas.
				mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
			if foliage:
				mat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_OFF
			row['review_texture_filter'] = mat.texture_filter
			material_rows.append(row)
			draw_materials.append(mat)
	for child in node.get_children():
		inspect(child,expected)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var config = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	root.size=Vector2i(900,900)
	root.msaa_3d=Viewport.MSAA_4X
	var camera := Camera3D.new()
	root.add_child(camera);camera.current=true
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.near=.01;camera.far=200
	var light := DirectionalLight3D.new()
	root.add_child(light);light.light_energy=1.2;light.shadow_enabled=true
	light.directional_shadow_max_distance=60
	light.shadow_bias=.1;light.shadow_normal_bias=2.0
	var world := WorldEnvironment.new()
	world.environment=Environment.new()
	world.environment.background_mode=Environment.BG_COLOR
	world.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	world.environment.ambient_light_color=Color.WHITE
	world.environment.ambient_light_energy=.5
	world.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	world.environment.tonemap_exposure=1.0
	root.add_child(world)
	# Receptor solo en las tomas shadow_*; la rama también recibe sus sombras.
	var receiver := MeshInstance3D.new()
	var plane := PlaneMesh.new();plane.size=Vector2(config.span*8,config.span*8)
	receiver.mesh=plane
	var ground := StandardMaterial3D.new();ground.albedo_color=Color(.65,.65,.65);ground.roughness=1
	receiver.material_override=ground
	receiver.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(receiver);receiver.visible=false
	receiver.position=converted(config.center)
	receiver.position.y=float(config.original_low[2])-.15
	var result := {'passed':false,'godot':Engine.get_version_info(),
		'renderer':RenderingServer.get_current_rendering_method(),'video_adapter':RenderingServer.get_video_adapter_name(),
		'msaa':root.msaa_3d,'environment':{'ambient':.5,'exposure':1,'tonemap':'linear','sun_energy':1.2,
		'shadows':true,'shadow_bias':light.shadow_bias,'shadow_normal_bias':light.shadow_normal_bias},'assets':{},'captures':[]}
	for item in config.assets:
		triangles=0;materials={};first=true;material_rows=[];draw_materials=[]
		var packed = load(item.resource)
		check(packed is PackedScene,'GLB no importado')
		if not packed is PackedScene: continue
		var asset = packed.instantiate();root.add_child(asset)
		visit(asset);inspect(asset,item.metrics)
		var lo=item.metrics.bounds_blender[0];var hi=item.metrics.bounds_blender[1]
		check(bounds.position.distance_to(Vector3(lo[0],lo[2],-hi[1]))<.0001,'Origen/ejes importados')
		check(bounds.end.distance_to(Vector3(hi[0],hi[2],-lo[1]))<.0001,'Escala importada')
		check(triangles==int(item.metrics.triangles),'Triángulos importados')
		check(materials.size()==2,'Cantidad de materiales')
		for name in item.metrics.triangles_by_material:
			check(int(materials.get(name,-1))==int(item.metrics.triangles_by_material[name]),'Canal de material '+name)
		result.assets[item.id]={'triangles':triangles,'materials':material_rows}
		for shot in config.shots:
			if shot.get('only','') != '' and shot.only != item.id: continue
			camera.size=shot.camera.ortho_scale
			camera.position=converted(shot.camera.location)
			var cols=shot.camera.basis_columns
			camera.basis=Basis(converted(cols[0]),converted(cols[1]),converted(cols[2]))
			light.rotation_degrees=Vector3(shot.light[0],shot.light[1],shot.light[2])
			world.environment.background_color=Color(shot.background)
			receiver.visible=shot.get('receiver',false)
			for mat in draw_materials:
				if mat.resource_name=='Painted_Foliage':
					mat.alpha_antialiasing_mode=int(shot.get('alpha_aa',0))
					mat.alpha_antialiasing_edge=.3
					mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
					if shot.get('no_mips',false):mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR
			var settings_rows := []
			for mat in draw_materials:
				settings_rows.append({'name':mat.resource_name,'alpha_aa':mat.alpha_antialiasing_mode,
					'alpha_edge':mat.alpha_antialiasing_edge,'filter':mat.texture_filter})
			if '--visual' in args:
				for frame in range(2):
					await process_frame
					await RenderingServer.frame_post_draw
				var filename=item.id+'--'+shot.id+'.png'
				check(root.get_texture().get_image().save_png(config.output.path_join(filename))==OK,'Captura fallida')
				result.captures.append({'asset':item.id,'shot':shot.id,'path':filename,'material_settings':settings_rows})
		asset.free()
	result.passed=not failed
	var file=FileAccess.open(config.report,FileAccess.WRITE)
	file.store_string(JSON.stringify(result,'  ')+'\n')
	print('PP3: '+str(result.captures.size())+' capturas, passed='+str(result.passed))
	quit(1 if failed else 0)
