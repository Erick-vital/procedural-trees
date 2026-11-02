extends "res://review_season_calendar.gd"
## T3: pruebas sobre importación real, extremos, mezcla GPU y secuencias reversibles.
var camera: Camera3D
var world: WorldEnvironment
var tree: Node3D
var center := Vector3.ZERO
var span := 15.0
var output := ""
var report := {"passed":false,"checks":{},"captures":[],"probe":[],"frames":[]}

func verify(ok: bool, name: String) -> void:
	report.checks[name]=ok
	check(ok,name)

func fingerprint(image: Image) -> String:
	var context := HashingContext.new();context.start(HashingContext.HASH_SHA256)
	context.update(image.get_data());return context.finish().hex_encode()

func draw_image() -> Image:
	for frame in 2:
		await process_frame
		await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func capture(name: String) -> Image:
	var image=await draw_image()
	check(image.save_png(output.path_join(name+".png"))==OK,"Guardar captura")
	report.captures.append(name+".png")
	return image

func view(p: float=0.0, orbital: bool=false) -> void:
	var angle=.7+TAU*p if orbital else .7
	camera.size=span*1.15
	camera.position=center+Vector3(sin(angle)*cos(.3),sin(.3),cos(angle)*cos(.3))*span*3
	camera.look_at(center)

func standard(texture: Texture2D) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.resource_name="Painted_Foliage";mat.albedo_texture=texture;mat.roughness=.95
	mat.cull_mode=BaseMaterial3D.CULL_DISABLED
	mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold=.5
	mat.alpha_antialiasing_mode=BaseMaterial3D.ALPHA_ANTIALIASING_OFF
	mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return mat

func constants(texture: Texture2D) -> void:
	for j in tree.foliage_meshes.size():tree.foliage_meshes[j].set_surface_override_material(tree.foliage_surfaces[j],standard(texture))

func probe() -> void:
	tree.visible=false
	var mesh := MeshInstance3D.new();root.add_child(mesh)
	var a := [];a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX]=PackedVector3Array([Vector3(-1,-1,0),Vector3(1,-1,0),Vector3(1,1,0),Vector3(-1,1,0)])
	a[Mesh.ARRAY_NORMAL]=PackedVector3Array([Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD])
	a[Mesh.ARRAY_TEX_UV]=PackedVector2Array([Vector2(.5,.5),Vector2(.5,.5),Vector2(.5,.5),Vector2(.5,.5)])
	a[Mesh.ARRAY_INDEX]=PackedInt32Array([0,1,2,0,2,3])
	var shader := Shader.new()
	shader.code=FileAccess.get_file_as_string("res://paint_transition.gdshader").replace("render_mode cull_disabled,","render_mode unshaded, cull_disabled,")
	var mat := ShaderMaterial.new();mat.shader=shader
	var colors := [Color8(32,160,64),Color8(220,90,15)]
	for j in 2:
		var image=Image.create(2,2,false,Image.FORMAT_RGBA8);image.fill(colors[j]);image.generate_mipmaps()
		mat.set_shader_parameter("summer_texture" if j==0 else "autumn_texture",ImageTexture.create_from_image(image))
	var arrays=tree.foliage_meshes[0].mesh.surface_get_arrays(tree.foliage_surfaces[0])
	var imported: Vector2=arrays[Mesh.ARRAY_TEX_UV2][0]
	for calendar in [Vector2(.25,.25),imported]:
		a[Mesh.ARRAY_TEX_UV2]=PackedVector2Array([calendar,calendar,calendar,calendar])
		var geometry := ArrayMesh.new();geometry.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a);mesh.mesh=geometry;mesh.material_override=mat
		camera.size=3;camera.position=Vector3(0,0,3);camera.look_at(Vector3.ZERO)
		for p in [0.0,calendar.x+calendar.y*.5,1.0]:
			mesh.set_instance_shader_parameter("season_phase",p)
			var image=await draw_image();var actual=image.get_pixel(root.size.x/2,root.size.y/2)
			var w=smoothstep(calendar.x,calendar.x+calendar.y,p)
			var expected=colors[0].srgb_to_linear().lerp(colors[1].srgb_to_linear(),w).linear_to_srgb()
			# Oráculo CPU pintado en un material estándar sin luz: misma conversión
			# final del motor, independiente de la mezcla shader bajo prueba.
			var oracle_image=Image.create(2,2,false,Image.FORMAT_RGBA8);oracle_image.fill(expected)
			var oracle=standard(ImageTexture.create_from_image(oracle_image));oracle.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
			mesh.material_override=oracle
			var reference=(await draw_image()).get_pixel(root.size.x/2,root.size.y/2)
			mesh.material_override=mat
			var delta=maxf(absf(actual.r-reference.r),maxf(absf(actual.g-reference.g),absf(actual.b-reference.b)))
			report.probe.append({"p":p,"calendar":[calendar.x,calendar.y],"weight":w,"actual":[actual.r8,actual.g8,actual.b8],"expected":[expected.r8,expected.g8,expected.b8],"standard_reference":[reference.r8,reference.g8,reference.b8],"max_error":delta})
			verify(delta<=3.0/255,"gpu-linear-%d"%report.probe.size())
	mesh.free();tree.visible=true;view()

func static_review() -> void:
	await probe()
	var other=load("res://pilot.tscn").instantiate();root.add_child(other);other.position.x=40
	verify(tree.foliage_meshes[0].get_active_material(tree.foliage_surfaces[0])==other.foliage_meshes[0].get_active_material(other.foliage_surfaces[0]),"material-shared-between-trees")
	var geometry=tree.foliage_meshes[0].mesh.get_rid()
	other.set_phase(.8);tree.set_phase(.2)
	camera.position+=Vector3(40,0,0)
	var before=fingerprint(await draw_image())
	tree.set_phase(.9)
	verify(fingerprint(await draw_image())==before,"second-tree-render-independent")
	verify(other.phase==.8 and other.foliage_meshes[0].get_instance_shader_parameter("season_phase")==.8,"second-tree-phase-independent")
	other.free();view()
	tree.set_phase(.2);var direct=fingerprint(await draw_image());tree.set_phase(.9);await draw_image();tree.set_phase(.2)
	verify(fingerprint(await draw_image())==direct,"direct-jump-reversible-pixels")
	verify(not tree.set_phase(NAN) and not tree.set_phase(-.1) and not tree.set_phase(1.1),"invalid-phase-rejected")
	verify(not tree.set_mode(-1) and not tree.set_mode(5),"invalid-mode-rejected")
	var shared=tree.foliage_meshes[0].get_active_material(tree.foliage_surfaces[0])
	for name in ["summer_texture","autumn_texture"]:
		var texture=shared.get_shader_parameter(name)
		verify(texture.get_image().has_mipmaps(),name+"-mips")
	var phases=[0.0,.25,.5,.75,1.0]
	for mode in 5:
		tree.set_mode(mode)
		for j in phases.size():
			tree.set_phase(phases[j]);await capture("mode-%d-p%d"%[mode,j])
	tree.set_mode(0);tree.set_phase(0);var zero=await capture("endpoint-summer-shader")
	constants(load("res://pilot_foliage.png"));var ref_zero=await capture("endpoint-summer-standard")
	tree.set_mode(0);tree.set_phase(1);var one=await capture("endpoint-autumn-shader")
	constants(load("res://autumn.png"));var ref_one=await capture("endpoint-autumn-standard")
	report.endpoint_exact={"summer":fingerprint(zero)==fingerprint(ref_zero),"autumn":fingerprint(one)==fingerprint(ref_one)}
	tree.set_mode(0)
	# Máscara negra común para comparar recorte sin que el pigmento o luz lo oculten.
	var saved=[]
	for mesh in tree.foliage_meshes:
		for i in mesh.mesh.get_surface_count():
			if mesh.mesh.surface_get_material(i).resource_name!="Painted_Bark":continue
			saved.append([mesh,i,mesh.get_active_material(i)])
			var black := StandardMaterial3D.new();black.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;black.albedo_color=Color.BLACK
			mesh.set_surface_override_material(i,black)
	tree.set_mask(true);world.environment.background_color=Color.WHITE
	var mask=""
	for j in phases.size():
		tree.set_phase(phases[j]);var im=await capture("mask-p%d"%j)
		if j==0:mask=fingerprint(im)
		verify(fingerprint(im)==mask,"alpha-mask-constant-%d"%j)
	for item in saved:item[0].set_surface_override_material(item[1],item[2])
	tree.set_mask(false);world.environment.background_color=Color("EEE9DF")
	verify(tree.foliage_meshes[0].mesh.get_rid()==geometry,"mesh-resource-not-rebuilt")

func viewer_smoke() -> void:
	if is_instance_valid(tree):tree.visible=false
	var viewer=load("res://viewer.tscn").instantiate();root.add_child(viewer);viewer.set_process(false)
	viewer.slider.value=.5
	verify(is_equal_approx(viewer.asset.phase,.5),"viewer-slider-direct-phase")
	viewer.play_button.pressed.emit();viewer._process(.5)
	verify(is_equal_approx(viewer.asset.phase,.55),"viewer-play-advances")
	viewer.play_button.pressed.emit();viewer._process(.5)
	verify(is_equal_approx(viewer.asset.phase,.55),"viewer-pause-stops")
	viewer.direction_button.pressed.emit();viewer.play_button.pressed.emit();viewer._process(.5)
	verify(is_equal_approx(viewer.asset.phase,.5),"viewer-reverse-advances-backwards")
	viewer.play_button.pressed.emit()
	var choices=viewer.find_children("*","OptionButton",true,false)[0]
	for mode in 5:
		choices.item_selected.emit(mode)
		verify(viewer.asset.mode==mode,"viewer-mode-%d"%mode)
	choices.select(0);choices.item_selected.emit(0)
	var toggles=viewer.find_children("*","CheckButton",true,false)
	toggles[0].button_pressed=true;viewer._process(.5)
	verify(viewer.orbit and viewer.yaw>.7,"viewer-orbit")
	toggles[0].button_pressed=false
	root.size=Vector2i(1000,900)
	await capture("viewer")
	viewer.free()
	if is_instance_valid(tree):tree.visible=true

func sequence(orbital: bool) -> void:
	tree.set_mode(0)
	var shared=tree.foliage_meshes[0].get_active_material(tree.foliage_surfaces[0])
	var ids=[tree.foliage_meshes[0].mesh.get_rid(),shared.get_rid(),shared.get_shader_parameter("summer_texture").get_rid(),shared.get_shader_parameter("autumn_texture").get_rid()]
	var hashes := {};var frames := []
	for index in 241:
		var step=index if index<=120 else 240-index
		var p=float(step)/120.0
		tree.set_phase(p);view(p,orbital)
		var image=await capture("%s-%03d"%["orbit" if orbital else "fixed",index])
		var digest=fingerprint(image)
		if index<=120:hashes[step]=digest
		else:verify(hashes[step]==digest,"reverse-frame-%03d"%index)
		frames.append({"frame":index,"phase":p,"pixels_sha256":digest})
	verify(ids==[tree.foliage_meshes[0].mesh.get_rid(),shared.get_rid(),shared.get_shader_parameter("summer_texture").get_rid(),shared.get_shader_parameter("autumn_texture").get_rid()],"sequence-mesh-material-textures-reused")
	report.frames=frames
	report.camera="orbital-retraced" if orbital else "fixed"

func run() -> void:
	var args=OS.get_cmdline_user_args();output=args[0];var stage=args[1]
	root.size=Vector2i(600,600);root.msaa_3d=Viewport.MSAA_4X
	if stage=="viewer":
		root.size=Vector2i(1000,900)
		await viewer_smoke()
		report.godot=Engine.get_version_info();report.passed=not failed
		FileAccess.open(output.path_join(stage+"-report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
		quit(1 if failed else 0)
		return
	camera=Camera3D.new();root.add_child(camera);camera.current=true;camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.near=.01;camera.far=300
	var sun := DirectionalLight3D.new();root.add_child(sun);sun.rotation_degrees=Vector3(-35,-25,0);sun.light_energy=1.2;sun.shadow_enabled=true
	world=WorldEnvironment.new();root.add_child(world);world.environment=Environment.new()
	world.environment.background_mode=Environment.BG_COLOR;world.environment.background_color=Color("EEE9DF")
	world.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;world.environment.ambient_light_color=Color.WHITE;world.environment.ambient_light_energy=.5
	world.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	tree=load("res://pilot.tscn").instantiate();root.add_child(tree)
	triangles=0;materials={};first=true;visit(tree)
	verify(triangles==6812 and materials.size()==2,"6812-triangles-two-materials")
	var expected := {}
	for row in JSON.parse_string(FileAccess.get_file_as_string("res://binding.json")):
		var key=grid_key(Vector3(row.position[0],row.position[1],row.position[2]),Vector2(row.uv[0],row.uv[1]))
		if not expected.has(key):expected[key]=[]
		expected[key].append(row)
	var state={"missing":0,"error":0.0,"position_error":0.0,"groups":{},"vertices":0,"faces":{}}
	inspect_attributes(tree,expected,true,state)
	verify(state.missing==0 and state.groups.size()==264,"264-groups-imported")
	for id in state.groups:check(state.faces[id]==6,"Seis caras por grupo")
	report.import_audit=state
	center=bounds.get_center();span=maxf(bounds.size.x,maxf(bounds.size.y,bounds.size.z));view()
	if stage=="static":await static_review()
	else:await sequence(stage=="orbit")
	report.godot=Engine.get_version_info();report.passed=not failed
	FileAccess.open(output.path_join(stage+"-report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(1 if failed else 0)
