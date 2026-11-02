extends "res://review_season_calendar.gd"
## T4: auditoría de normales reales importadas, pinturas fijas y material estándar.
var scene: Node3D
var report := {"passed":false,"audits":{},"captures":[]}
var output := ""

func normal_audit(node: Node, grid: Dictionary, state: Dictionary) -> void:
	if node is MeshInstance3D:
		for i in node.mesh.get_surface_count():
			var mat=node.get_active_material(i)
			check(mat is StandardMaterial3D,"Depende de shader personalizado")
			if node.mesh.surface_get_material(i).resource_name!="Painted_Foliage":continue
			check(not mat.normal_enabled and not mat.ao_on_uv2,"Material sustituye normales o consume UV2")
			check(mat.albedo_texture.get_image().has_mipmaps(),"Mipmaps ausentes")
			var arrays=node.mesh.surface_get_arrays(i)
			var vertices=arrays[Mesh.ARRAY_VERTEX];var uv=arrays[Mesh.ARRAY_TEX_UV];var normals=arrays[Mesh.ARRAY_NORMAL]
			for j in vertices.size():
				var v: Vector3=node.global_transform*vertices[j]
				var matches := []
				for x in [-1,0,1]:
					for y in [-1,0,1]:
						for z in [-1,0,1]:
							for row in grid.get(grid_key(v,uv[j],Vector3i(x,y,z)),[]):
								var p=Vector3(row.position[0],row.position[1],row.position[2])
								if v.distance_to(p)<=.0007 and absf(uv[j].x-row.uv[0])<=.00005 and absf(uv[j].y-row.uv[1])<=.00005:matches.append(row)
				var ids := {};var delta=INF
				for row in matches:
					ids[row.group_id]=true
					delta=minf(delta,normals[j].distance_to(Vector3(row.normal[0],row.normal[1],row.normal[2])))
				check(ids.size()==1,"Grupo normal sin correspondencia única")
				check(normals[j].is_finite() and absf(normals[j].length()-1)<.002,"Normal importada inválida")
				check(delta<=float(state.tolerance),"Normal importada distinta del GLB")
				state.error=maxf(state.error,delta);state.vertices+=1
				for id in ids:state.groups[id]=true
	for child in node.get_children():normal_audit(child,grid,state)

func inspect_case(item: Dictionary) -> void:
	triangles=0;materials={};first=true;visit(scene.asset)
	check(triangles==int(item.triangles) and triangles<7000 and materials.size()==2,"Presupuesto importado distinto")
	var grid := {}
	for row in JSON.parse_string(FileAccess.get_file_as_string("res://"+item.expected)):
		var key=grid_key(Vector3(row.position[0],row.position[1],row.position[2]),Vector2(row.uv[0],row.uv[1]))
		if not grid.has(key):grid[key]=[]
		grid[key].append(row)
	var state={"error":0.0,"vertices":0,"groups":{},"tolerance":.012 if item.id.begins_with("roundtrip-") else .003}
	normal_audit(scene.asset,grid,state)
	check(state.groups.size()==int(item.groups),"Grupos importados perdidos")
	report.audits[item.id]={"max_normal_error":state.error,"vertices":state.vertices,"groups":state.groups.size(),"triangles":triangles,"materials":materials}

func capture(name: String) -> void:
	for frame in 2:
		await process_frame
		await RenderingServer.frame_post_draw
	check(root.get_texture().get_image().save_png(output.path_join(name+".png"))==OK,"Guardar captura")
	report.captures.append(name+".png")

func mask(node: Node) -> void:
	if node is MeshInstance3D:
		for i in node.mesh.get_surface_count():
			var mat=node.get_active_material(i).duplicate() as StandardMaterial3D
			mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;mat.albedo_color=Color.BLACK
			node.set_surface_override_material(i,mat)
	for child in node.get_children():mask(child)

func run() -> void:
	var args=OS.get_cmdline_user_args();output=args[0];var scope=args[1];var season=args[2]
	if scope=="viewer":
		root.size=Vector2i(1000,900);root.msaa_3d=Viewport.MSAA_4X
		var viewer=load("res://viewer.tscn").instantiate();root.add_child(viewer)
		var choices=viewer.find_children("*","OptionButton",true,false)
		for i in 3:
			choices[0].item_selected.emit(i);check(viewer.variant==i,"Visor no cambia normales")
		for i in 2:
			choices[1].item_selected.emit(i);check(viewer.season==i,"Visor no cambia pintura")
			choices[2].item_selected.emit(i);check(viewer.scope==i,"Visor no cambia muestra")
		for i in 3:
			choices[3].item_selected.emit(i);check(viewer.light==i,"Visor no cambia luz")
		choices[0].select(1);choices[0].item_selected.emit(1)
		choices[1].select(0);choices[1].item_selected.emit(0)
		choices[3].select(0);choices[3].item_selected.emit(0)
		var toggle=viewer.find_children("*","CheckButton",true,false)[0]
		toggle.button_pressed=false;check(not viewer.scene.ground.visible,"Visor no oculta suelo")
		toggle.button_pressed=true;check(viewer.scene.ground.visible,"Visor no muestra suelo")
		await capture("viewer")
		report.godot=Engine.get_version_info();report.passed=not failed
		FileAccess.open(output.path_join("godot-report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
		quit(1 if failed else 0);return
	root.size=Vector2i(600,600);root.msaa_3d=Viewport.MSAA_4X
	scene=load("res://canopy_normals_scene.gd").new();root.add_child(scene)
	var config=JSON.parse_string(FileAccess.get_file_as_string("res://normal-review-config.json"))
	for item in config.cases:
		if item.scope!=scope or item.season!=season:continue
		scene.show_case(item.id,season);inspect_case(item)
		for light in 3:
			for view in 6:
				for distance in 3:
					scene.shot(view,[1.15,2.8,6.0][distance],light)
					await capture(item.id+"-l%d-v%d-d%d"%[light,view,distance])
			for bias in [0,1]:
				scene.shot(2,1.75,light,true,float(bias))
				await capture(item.id+"-shadow-l%d-b%d"%[light,bias])
		mask(scene.asset);scene.environment.environment.background_color=Color.WHITE
		for view in 6:
			scene.shot(view,1.15,0);await capture(item.id+"-mask-v%d"%view)
		scene.environment.environment.background_color=Color("EEE9DF")
		# Comprobar también glTF reexportado por Blender; no se confía en índices.
		if season=="summer":
			scene.show_case("roundtrip-"+scope+"-"+item.variant,season)
			var roundtrip=item.duplicate();roundtrip.id="roundtrip-"+item.id;inspect_case(roundtrip)
	report.godot=Engine.get_version_info();report.passed=not failed
	FileAccess.open(output.path_join("godot-report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(1 if failed else 0)
