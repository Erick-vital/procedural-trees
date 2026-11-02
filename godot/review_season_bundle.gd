extends "res://review_season_calendar.gd"
## Utilidades de revisión de mezcla conservadas de T3 para el paquete autónomo T5.
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
		RenderingServer.force_draw(false)
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


## T5: cuatro casos; originales/seleccionadas, extremos estándar y mezcla conjunta.
var scene: Node3D
var config: Dictionary
var current_item: Dictionary
var oracle_hashes := {}
const LIGHTS := [Vector3(-35,-25,0),Vector3(-35,-90,0),Vector3(-35,155,0)]
const PHASES := [0.0,.25,.5,.75,1.0]

func image_hash(texture: Texture2D) -> String:
	var im=texture.get_image();im.clear_mipmaps();im.convert(Image.FORMAT_RGBA8)
	return fingerprint(im)

func oracle_hash(name: String) -> String:
	return config.resource_pixels_sha256[name]

func imported_audit(node: Node, grid: Dictionary, state: Dictionary, standard_only: bool, season: String) -> void:
	if node is MeshInstance3D:
		for surface in node.mesh.get_surface_count():
			var source=node.mesh.surface_get_material(surface)
			var mat=node.get_active_material(surface)
			if standard_only:
				check(mat is StandardMaterial3D,"Extremo estático depende de shader")
				var name="bark" if source.resource_name=="Painted_Bark" else season
				check(image_hash(mat.albedo_texture)==oracle_hash(name),"Píxeles embebidos distintos: "+name)
				check(mat.albedo_texture.get_image().has_mipmaps(),"Extremo sin mipmaps")
			if source.resource_name!="Painted_Foliage":continue
			var arrays=node.mesh.surface_get_arrays(surface)
			var vertices=arrays[Mesh.ARRAY_VERTEX];var uv=arrays[Mesh.ARRAY_TEX_UV];var normals=arrays[Mesh.ARRAY_NORMAL];var calendar=arrays[Mesh.ARRAY_TEX_UV2]
			check(calendar!=null and calendar.size()==vertices.size(),"Calendario ausente")
			var owners=[]
			for j in vertices.size():
				var v: Vector3=node.global_transform*vertices[j];var matches=[]
				for x in [-1,0,1]:
					for y in [-1,0,1]:
						for z in [-1,0,1]:
							for row in grid.get(grid_key(v,uv[j],Vector3i(x,y,z)),[]):
								var p=Vector3(row.position[0],row.position[1],row.position[2])
								if v.distance_to(p)<=.0007 and absf(uv[j].x-row.uv[0])<=.00005 and absf(uv[j].y-row.uv[1])<=.00005:matches.append(row)
				var ids={};var error=INF;var time_error=INF
				for row in matches:
					ids[row.group_id]=true
					error=minf(error,normals[j].distance_to(Vector3(row.normal[0],row.normal[1],row.normal[2])))
					if calendar!=null:time_error=minf(time_error,calendar[j].distance_to(Vector2(row.calendar[0],row.calendar[1])))
				check(ids.size()==1,"Grupo ambiguo o perdido")
				check(error<=float(state.tolerance) and normals[j].is_finite() and absf(normals[j].length()-1)<.002,"Normal importada incorrecta")
				check(time_error<.0004,"Calendario importado distinto")
				state.normal_error=maxf(state.normal_error,error);state.calendar_error=maxf(state.calendar_error,time_error)
				state.vertices+=1
				if ids.size()==1:
					var id=ids.keys()[0];state.groups[id]=true;owners.append(id)
			var indices=arrays[Mesh.ARRAY_INDEX]
			if owners.size()==vertices.size():
				for j in range(0,indices.size(),3):
					var id=owners[indices[j]]
					check(id==owners[indices[j+1]] and id==owners[indices[j+2]],"Cara mezcla grupos")
					state.faces[id]=state.faces.get(id,0)+1
	for child in node.get_children():imported_audit(child,grid,state,standard_only,season)

func inspect_asset(asset: Node3D, normal_kind: String, label: String, standard_only: bool=false, season: String="summer",roundtrip: bool=false) -> void:
	var grid={}
	for row in JSON.parse_string(FileAccess.get_file_as_string("res://data/"+current_item.id+"/"+normal_kind+"-normals.json")):
		var key=grid_key(Vector3(row.position[0],row.position[1],row.position[2]),Vector2(row.uv[0],row.uv[1]))
		if not grid.has(key):grid[key]=[]
		grid[key].append(row)
	triangles=0;materials={};first=true;visit(asset)
	verify(triangles==int(current_item.triangles) and triangles<7000 and materials.size()==2,label+"-budget")
	var state={"tolerance":.012 if roundtrip else .003,"normal_error":0.0,"calendar_error":0.0,"vertices":0,"groups":{},"faces":{}}
	imported_audit(asset,grid,state,standard_only,season)
	verify(state.groups.size()==264 and state.faces.size()==264,label+"-264-groups")
	for id in state.faces:check(state.faces[id]==6,"Grupo sin tres láminas")
	if not report.has("imports"):report.imports={}
	report.imports[label]={"triangles":triangles,"materials":materials,"groups":state.groups.size(),"vertices":state.vertices,
		"normal_error":state.normal_error,"calendar_error":state.calendar_error}

func configure_static(node: Node) -> void:
	if node is MeshInstance3D:
		node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			var mat=node.get_active_material(i).duplicate() as StandardMaterial3D
			mat.roughness=.95
			if mat.resource_name=="Painted_Foliage":
				mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
				mat.alpha_antialiasing_mode=BaseMaterial3D.ALPHA_ANTIALIASING_OFF
			node.set_surface_override_material(i,mat)
	for child in node.get_children():configure_static(child)

func matrix_review() -> void:
	await probe()
	# Comprobar las texturas visibles y también las retenidas en las superficies.
	var mat=tree.foliage_meshes[0].get_active_material(tree.foliage_surfaces[0])
	verify(image_hash(mat.get_shader_parameter("summer_texture"))==oracle_hash("summer"),"runtime-summer-exact")
	verify(image_hash(mat.get_shader_parameter("autumn_texture"))==oracle_hash("autumn"),"runtime-autumn-exact")
	var other_item=config.cases[(config.cases.find(current_item)+1)%4]
	var other=load("res://"+other_item.id+"-selected.tscn").instantiate();scene.add_child(other)
	verify(other.foliage_meshes[0].get_active_material(other.foliage_surfaces[0])==mat,"shared-paint-across-cases")
	other.position=Vector3(1000,0,0);other.set_phase(.8)
	var target=Vector3(other_item.bounds.center[0],other_item.bounds.center[1],other_item.bounds.center[2])+other.position
	camera.size=other_item.bounds.span*1.15;camera.position=target+Vector3(1,.45,1).normalized()*other_item.bounds.span*3;camera.look_at(target)
	var before=fingerprint(await draw_image());tree.set_phase(.9)
	verify(fingerprint(await draw_image())==before,"other-case-render-independent")
	other.free();view()
	tree.set_phase(.2);var direct=fingerprint(await draw_image());tree.set_phase(.9);await draw_image();tree.set_phase(.2)
	verify(fingerprint(await draw_image())==direct,"jump-.9-.2-exact")
	verify(not tree.set_phase(NAN) and not tree.set_phase(-.1) and not tree.set_phase(1.1),"invalid-phase-rejected")
	var refs={}
	for kind in ["original","selected"]:
		for season in ["summer","autumn"]:
			for roundtrip in [false,true]:
				var label=("roundtrip-" if roundtrip else "")+current_item.id+"-"+season+"-"+kind
				var asset=load("res://static/"+label+".glb").instantiate();scene.add_child(asset)
				inspect_asset(asset,kind,label,true,season,roundtrip);configure_static(asset)
				tree.visible=false;view()
				var im=await capture(label)
				if kind=="selected" and not roundtrip:refs[season]=fingerprint(im)
				asset.free();tree.visible=true
	for bg in ["light","dark"]:
		world.environment.background_color=Color("EEE9DF") if bg=="light" else Color("182027")
		for light in 3:
			scene.sun.rotation_degrees=LIGHTS[light]
			for distance in 3:
				view();camera.size=span*[1.15,2.8,6.0][distance]
				for j in PHASES.size():
					tree.set_phase(PHASES[j]);var im=await capture("mix-"+bg+"-l%d-d%d-p%d"%[light,distance,j])
					if bg=="light" and light==0 and distance==0 and j in [0,4]:
						verify(fingerprint(im)==refs["summer" if j==0 else "autumn"],"static-runtime-endpoint-%d"%j)
	world.environment.background_color=Color("EEE9DF")
	scene.ground.visible=true
	for light in 3:
		scene.sun.rotation_degrees=LIGHTS[light];view();camera.size=span*2.5
		for j in [0,2,4]:tree.set_phase(PHASES[j]);await capture("shadow-l%d-p%d"%[light,j])
	scene.ground.visible=false;scene.sun.rotation_degrees=LIGHTS[0];view()
	var saved=[]
	for mesh in tree.foliage_meshes:
		for i in mesh.mesh.get_surface_count():
			if mesh.mesh.surface_get_material(i).resource_name!="Painted_Bark":continue
			saved.append([mesh,i,mesh.get_active_material(i)])
			var black := StandardMaterial3D.new();black.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;black.albedo_color=Color.BLACK;mesh.set_surface_override_material(i,black)
	tree.set_mask(true);world.environment.background_color=Color.WHITE;var mask=""
	for j in PHASES.size():
		tree.set_phase(PHASES[j]);var im=await capture("mask-p%d"%j)
		if j==0:mask=fingerprint(im)
		verify(fingerprint(im)==mask,"mask-phase-%d"%j)
	for item in saved:item[0].set_surface_override_material(item[1],item[2])
	tree.set_mask(false)

func ui_review() -> void:
	var viewer=load("res://viewer.tscn").instantiate();root.add_child(viewer);viewer.set_process(false)
	viewer.slider.value=.2
	viewer.case_picker.select(1);viewer.case_picker.item_selected.emit(1);viewer.slider.value=.8
	viewer.case_picker.select(0);viewer.case_picker.item_selected.emit(0)
	verify(is_equal_approx(viewer.scene.asset.phase,.2),"viewer-preserves-case-phase")
	for i in 4:
		viewer.case_picker.select(i);viewer.case_picker.item_selected.emit(i)
		verify(viewer.selected==i,"viewer-case-%d"%i)
	for i in 2:
		viewer.normal_picker.select(i);viewer.normal_picker.item_selected.emit(i)
		verify(viewer.normal_kind==("selected" if i==0 else "original"),"viewer-normals-%d"%i)
	viewer.normal_picker.select(0);viewer.normal_picker.item_selected.emit(0)
	viewer.slider.value=.5;viewer.play_button.pressed.emit();viewer._process(.5)
	verify(is_equal_approx(viewer.scene.asset.phase,.55),"viewer-play")
	viewer.play_button.pressed.emit();viewer._process(.5);verify(is_equal_approx(viewer.scene.asset.phase,.55),"viewer-pause")
	viewer.direction_button.pressed.emit();viewer.play_button.pressed.emit();viewer._process(.5)
	verify(is_equal_approx(viewer.scene.asset.phase,.5),"viewer-reverse");viewer.play_button.pressed.emit()
	for i in 5:viewer.mode_picker.select(i);viewer.mode_picker.item_selected.emit(i);verify(viewer.scene.asset.mode==i,"viewer-mode-%d"%i)
	viewer.mode_picker.select(0);viewer.mode_picker.item_selected.emit(0)
	viewer.ground_toggle.button_pressed=true;verify(viewer.scene.ground.visible,"viewer-ground")
	viewer.orbit_toggle.button_pressed=true;viewer._process(.5);verify(viewer.yaw>.7,"viewer-orbit");viewer.orbit_toggle.button_pressed=false
	await capture("viewer");viewer.free()

func finish(stage: String) -> void:
	report.godot=Engine.get_version_info();report.passed=not failed
	FileAccess.open(output.path_join(stage+"-report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(1 if failed else 0)

func run() -> void:
	var args=OS.get_cmdline_user_args();output=args[0];var identifier=args[1];var stage=args[2]
	root.size=Vector2i(600,600);root.msaa_3d=Viewport.MSAA_4X
	config=JSON.parse_string(FileAccess.get_file_as_string("res://bundle-config.json"))
	if stage=="viewer":root.size=Vector2i(1000,900);await ui_review();finish(stage);return
	scene=load("res://season_bundle_scene.gd").new();root.add_child(scene)
	for item in config.cases:
		if stage!="portable" and item.id!=identifier:continue
		current_item=item;scene.show_case(item,"selected")
		tree=scene.asset;camera=scene.camera;world=scene.world;center=scene.center;span=scene.span;view()
		inspect_asset(tree,"selected",item.id+"-runtime")
		if stage=="portable":
			tree.set_phase(.5);await capture(item.id+"-portable")
		elif stage=="matrix":await matrix_review()
		else:await sequence(stage=="orbit")
	finish(stage)
