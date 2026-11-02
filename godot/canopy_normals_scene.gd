extends Node3D
## T4: misma escena/material estándar para originales y candidatas.
const VIEWS := [Vector3(0,.1,1),Vector3(1,.1,0),Vector3(1,.45,1),Vector3(-1,.3,-1),Vector3(.01,1,.01),Vector3(1,-.5,1)]
const LIGHTS := [Vector3(-35,-25,0),Vector3(-35,-90,0),Vector3(-35,155,0)]
var camera := Camera3D.new()
var sun := DirectionalLight3D.new()
var environment := WorldEnvironment.new()
var ground := MeshInstance3D.new()
var asset: Node3D
var center := Vector3.ZERO
var span := 15.0
var paint_materials := {}
var yaw := .7
var pitch := .3
var zoom := 1.15

func _ready() -> void:
	add_child(camera);camera.current=true;camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.near=.01;camera.far=300
	add_child(sun);sun.light_energy=1.2;sun.shadow_enabled=true
	environment.environment=Environment.new();add_child(environment)
	environment.environment.background_mode=Environment.BG_COLOR;environment.environment.background_color=Color("EEE9DF")
	environment.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color=Color.WHITE;environment.environment.ambient_light_energy=.5
	environment.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	var plane := PlaneMesh.new();plane.size=Vector2(200,200);ground.mesh=plane;add_child(ground)
	var material := StandardMaterial3D.new();material.albedo_color=Color("B7B1A3");material.roughness=1
	ground.material_override=material;ground.visible=false
	for season in ["summer","autumn"]:
		var mat := StandardMaterial3D.new();mat.resource_name="Painted_Foliage";mat.albedo_texture=load("res://"+season+".png")
		mat.roughness=.95;mat.cull_mode=BaseMaterial3D.CULL_DISABLED
		mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR;mat.alpha_scissor_threshold=.5
		mat.alpha_antialiasing_mode=BaseMaterial3D.ALPHA_ANTIALIASING_OFF
		mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		paint_materials[season]=mat

func show_case(identifier: String, season: String) -> void:
	if is_instance_valid(asset):asset.free()
	asset=load("res://"+identifier+".glb").instantiate();add_child(asset)
	var boxes := []
	configure(asset,season,boxes)
	var bounds: AABB=boxes[0]
	for b in boxes:bounds=bounds.merge(b)
	center=bounds.get_center();span=maxf(bounds.size.x,maxf(bounds.size.y,bounds.size.z))

func configure(node: Node, season: String, boxes: Array) -> void:
	if node is MeshInstance3D:
		boxes.append(node.global_transform*node.mesh.get_aabb())
		node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		for i in node.mesh.get_surface_count():
			if node.mesh.surface_get_material(i).resource_name=="Painted_Foliage":node.set_surface_override_material(i,paint_materials[season])
	for child in node.get_children():configure(child,season,boxes)

func shot(view_index: int, scale: float, light_index: int, receiver: bool=false, bias: float=1.0) -> void:
	sun.rotation_degrees=LIGHTS[light_index];sun.shadow_normal_bias=bias
	ground.visible=receiver
	camera.size=span*scale
	camera.position=center+VIEWS[view_index].normalized()*span*3;camera.look_at(center)
