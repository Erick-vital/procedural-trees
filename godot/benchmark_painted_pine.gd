extends SceneTree
## Benchmark estático reproducible; mediciones fuera de importación/capturas.
var settings: Dictionary
var prototypes := {}
var material_report := {}
var frame_rows: Array = []
var running := false
var last_tick := 0
var viewport_rid: RID

func _initialize() -> void:
	call_deferred('run')

func meshes(node: Node) -> Array:
	var found: Array = []
	if node is MeshInstance3D:
		found.append(node)
	for child in node.get_children():
		found.append_array(meshes(child))
	return found

func _process(_delta: float) -> bool:
	if running:
		var tick := Time.get_ticks_usec()
		frame_rows.append([
			(tick-last_tick)/1000.0,
			RenderingServer.viewport_get_measured_render_time_cpu(viewport_rid),
			RenderingServer.viewport_get_measured_render_time_gpu(viewport_rid),
			RenderingServer.get_frame_setup_time_cpu(),
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)
		])
		last_tick=tick
	return false

func wait_seconds(seconds: float) -> void:
	var until := Time.get_ticks_usec()+int(seconds*1000000)
	while Time.get_ticks_usec()<until:
		await process_frame

func run() -> void:
	settings=JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	Engine.max_fps=0
	OS.low_processor_usage_mode=false
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	root.size=Vector2i(1280,720)
	root.content_scale_size=Vector2i(int(settings.resolution[0]),int(settings.resolution[1]))
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_VIEWPORT
	root.content_scale_aspect=Window.CONTENT_SCALE_ASPECT_IGNORE
	root.msaa_3d=Viewport.MSAA_4X
	root.mesh_lod_threshold=0.0
	viewport_rid=root.get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(viewport_rid,true)
	var env_node := WorldEnvironment.new()
	env_node.environment=Environment.new()
	env_node.environment.background_mode=Environment.BG_COLOR
	env_node.environment.background_color=Color('#EEE9DF')
	env_node.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env_node.environment.ambient_light_color=Color.WHITE
	env_node.environment.ambient_light_energy=.5
	env_node.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	env_node.environment.tonemap_exposure=1.0
	root.add_child(env_node)
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.current=true
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.near=.1
	camera.far=1000
	var light := DirectionalLight3D.new()
	root.add_child(light)
	light.rotation_degrees=Vector3(-35,-25,0)
	light.light_energy=1.2
	light.shadow_enabled=settings.shadows
	light.directional_shadow_max_distance=500
	light.shadow_bias=.1
	light.shadow_normal_bias=2.0
	var ground := MeshInstance3D.new()
	ground.mesh=PlaneMesh.new()
	ground.mesh.size=Vector2(500,500)
	var ground_mat := StandardMaterial3D.new()
	ground_mat.albedo_color=Color(.45,.46,.39)
	ground_mat.roughness=1.0
	ground.material_override=ground_mat
	ground.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(ground)
	var configure=load('res://painted_pine_asset.gd').new()
	for version in ['baseline','candidate']:
		prototypes[version]=[]
		material_report[version]=[]
		for asset in settings.assets[version]:
			var node=load(asset).instantiate()
			configure.configure(node)
			prototypes[version].append(node)
			var material_rows: Array=[]
			for mesh_node in meshes(node):
				for surface in range(mesh_node.mesh.get_surface_count()):
					var mat=mesh_node.get_active_material(surface)
					material_rows.append({'name':mat.resource_name,'transparency':mat.transparency,'cull_mode':mat.cull_mode,
						'roughness':mat.roughness,'textured':mat.albedo_texture!=null,'shadow_casting':mesh_node.cast_shadow})
			material_report[version].append(material_rows)
	configure.free()
	var count: int=settings.count
	var cols := ceili(sqrt(float(count)))
	var rows := ceili(float(count)/cols)
	var span: float=max(cols,rows)*settings.spacing_m
	camera.size=18.0 if count==1 else span*1.12+18.0
	var center := Vector3(0,6,0)
	camera.position=center+Vector3(0, .65,1).normalized()*max(40.0,span*2)
	camera.look_at(center)
	var layout: Array=[]
	for i in range(count):
		layout.append({'position':[(i%cols-(cols-1)*.5)*settings.spacing_m,0,(i/cols-(rows-1)*.5)*settings.spacing_m],
			'rotation_y':fmod(i*2.399963229728653,TAU),'case':i%4})
	# División de índices explícita: evitar filas fraccionarias.
	for i in range(count):
		layout[i].position[2]=(floori(float(i)/cols)-(rows-1)*.5)*settings.spacing_m
	var results: Array=[]
	for trial in range(settings.order.size()):
		var version: String=settings.order[trial]
		var trees := Node3D.new()
		root.add_child(trees)
		var mesh_count := 0
		for placement in layout:
			var node=prototypes[version][placement['case']].duplicate()
			trees.add_child(node)
			node.position=Vector3(placement.position[0],0,placement.position[2])
			node.rotation.y=placement.rotation_y
			mesh_count+=meshes(node).size()
		await wait_seconds(float(settings.warmup_seconds))
		# Captura antes de medir y calentamiento adicional para excluir el readback.
		if trial<2:
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(settings.output.path_join(version+'.png'))
			await wait_seconds(1.0)
		frame_rows=[]
		last_tick=Time.get_ticks_usec()
		running=true
		await wait_seconds(float(settings.measurement_seconds))
		running=false
		results.append({'trial':trial,'version':version,'mesh_instances':mesh_count,'samples':frame_rows})
		print('trial ',trial,' ',version,' frames=',frame_rows.size())
		trees.free()
		await process_frame
	var report := {'settings':settings,'godot':Engine.get_version_info(),
		'renderer':RenderingServer.get_current_rendering_method(),
		'gpu':RenderingServer.get_video_adapter_name(),'driver':RenderingServer.get_video_adapter_api_version(),
		'actual_resolution':[root.get_texture().get_width(),root.get_texture().get_height()],
		'window_size':[root.size.x,root.size.y],'actual_msaa':root.msaa_3d,'actual_shadows':light.shadow_enabled,'actual_vsync':DisplayServer.window_get_vsync_mode(),
		'actual_max_fps':Engine.max_fps,'actual_lod_threshold':root.mesh_lod_threshold,
		'camera':{'position':[camera.position.x,camera.position.y,camera.position.z],'size':camera.size},
		'layout':layout,'materials':material_report,'columns':['frame_ms','render_cpu_ms','render_gpu_ms','render_setup_cpu_ms','draw_calls','primitives','objects'],
		'trials':results}
	FileAccess.open(settings.output.path_join('raw.json'),FileAccess.WRITE).store_string(JSON.stringify(report))
	for version in prototypes:
		for node in prototypes[version]:node.free()
	quit()
