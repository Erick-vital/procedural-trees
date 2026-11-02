extends Node3D
## Escena T5: luz/materiales comunes y receptor que no proyecta sombra propia.
var camera := Camera3D.new()
var sun := DirectionalLight3D.new()
var world := WorldEnvironment.new()
var ground := MeshInstance3D.new()
var asset: Node3D
var center := Vector3.ZERO
var span := 15.0
var item: Dictionary

func _ready() -> void:
	add_child(camera);camera.current=true;camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.near=.01;camera.far=300
	add_child(sun);sun.rotation_degrees=Vector3(-35,-25,0);sun.light_energy=1.2;sun.shadow_enabled=true;sun.shadow_normal_bias=1
	world.environment=Environment.new();add_child(world)
	world.environment.background_mode=Environment.BG_COLOR;world.environment.background_color=Color("EEE9DF")
	world.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	world.environment.ambient_light_color=Color.WHITE;world.environment.ambient_light_energy=.5
	world.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	var plane := PlaneMesh.new();plane.size=Vector2(200,200);ground.mesh=plane;add_child(ground)
	ground.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;ground.visible=false
	var mat := StandardMaterial3D.new();mat.albedo_color=Color("B7B1A3");mat.roughness=1;ground.material_override=mat

func show_case(row: Dictionary, normals: String="selected") -> void:
	if is_instance_valid(asset):asset.free()
	item=row;asset=load("res://"+item.id+"-"+normals+".tscn").instantiate();add_child(asset)
	center=Vector3(item.bounds.center[0],item.bounds.center[1],item.bounds.center[2]);span=item.bounds.span

func view(yaw: float=.7,pitch: float=.3,zoom: float=1.15) -> void:
	camera.size=span*zoom
	camera.position=center+Vector3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))*span*3
	camera.look_at(center)
