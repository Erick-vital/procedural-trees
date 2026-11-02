extends SceneTree
## Comprobación adicional T5: referencias reales compartidas y bytes de Image.
var active_materials := {}
var retained_materials := {}
var textures := {}

func texture_row(texture: Texture2D) -> void:
	var id=str(texture.get_rid().get_id())
	if textures.has(id):return
	var im=texture.get_image()
	textures[id]={"path":texture.resource_path,"width":im.get_width(),"height":im.get_height(),
		"image_format":im.get_format(),"mipmap_count":im.get_mipmap_count(),"readback_bytes_with_mips":im.get_data().size()}

func material_row(mat: Material, active: bool) -> void:
	var id=str(mat.get_rid().get_id())
	retained_materials[id]=true
	if active:active_materials[id]=true
	if mat is StandardMaterial3D:texture_row(mat.albedo_texture)
	elif mat is ShaderMaterial:
		texture_row(mat.get_shader_parameter("summer_texture"));texture_row(mat.get_shader_parameter("autumn_texture"))

func inspect(node: Node) -> void:
	if node is MeshInstance3D:
		for surface in node.mesh.get_surface_count():
			material_row(node.mesh.surface_get_material(surface),false)
			material_row(node.get_active_material(surface),true)
	for child in node.get_children():inspect(child)

func _initialize() -> void:call_deferred("run")

func run() -> void:
	var config=JSON.parse_string(FileAccess.get_file_as_string("res://bundle-config.json"))
	for item in config.cases:
		var asset=load("res://"+item.id+"-selected.tscn").instantiate();root.add_child(asset);inspect(asset)
	var total=0
	for row in textures.values():total+=int(row.readback_bytes_with_mips)
	var passed=active_materials.size()==2 and retained_materials.size()==2 and textures.size()==3
	FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,
		"instances":4,"active_shared_materials":active_materials.size(),"retained_surface_materials":retained_materials.size(),
		"unique_textures":textures.size(),"textures":textures.values(),"readback_bytes_total":total,
		"note":"Bytes de Image devueltos por Godot; no equivalen a VRAM medida ni rendimiento."},"  ")+"\n")
	quit(0 if passed else 1)
