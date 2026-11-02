extends Node3D
## Comparación de estaciones con la misma geometría y cámara.
var camera := Camera3D.new()
var asset: Node3D
var cases: Array
var selected := 0
var autumn := true
var center := Vector3.ZERO
var span := 15.0
var yaw := .7
var pitch := .3
var zoom := 1.15
var label := Label.new()

func _ready() -> void:
	DisplayServer.window_set_title("Roble · otoño / verano")
	get_viewport().msaa_3d = Viewport.MSAA_4X
	cases = JSON.parse_string(FileAccess.get_file_as_string("res://preview-config.json")).cases
	add_child(camera)
	camera.current = true
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = .01
	camera.far = 300
	var sun := DirectionalLight3D.new()
	add_child(sun)
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
	add_child(world)
	var canvas := CanvasLayer.new()
	add_child(canvas)
	canvas.add_child(label)
	label.position = Vector2(18, 18)
	label.add_theme_color_override("font_color", Color("29221B"))
	select_case()

func select_case() -> void:
	if is_instance_valid(asset): asset.free()
	asset = load("res://"+cases[selected].id+".tscn").instantiate()
	add_child(asset)
	var b = cases[selected].metrics.bounds_blender
	center = Vector3((b[0][0]+b[1][0])/2, (b[0][2]+b[1][2])/2, -(b[0][1]+b[1][1])/2)
	span = maxf(b[1][0]-b[0][0], maxf(b[1][1]-b[0][1], b[1][2]-b[0][2]))
	refresh()

func refresh() -> void:
	asset.set_season_amount(1.0 if autumn else 0.0)
	label.text = "Roble · %s · %s | %d tris · 2 materiales\nArrastrar: girar · Rueda: zoom · O: otoño/verano · N: otro árbol · R: cámara" % ["Otoño" if autumn else "Verano", cases[selected].id, int(cases[selected].metrics.triangles)]
	camera.size = span*zoom
	camera.position = center+Vector3(sin(yaw)*cos(pitch), sin(pitch), cos(yaw)*cos(pitch))*span*3
	camera.look_at(center)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		yaw -= event.relative.x*.008
		pitch = clampf(pitch+event.relative.y*.008, -1.4, 1.4)
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP: zoom = maxf(.25, zoom*.9)
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN: zoom = minf(5, zoom/.9)
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_O: autumn = not autumn
			KEY_N:
				selected = (selected+1)%cases.size()
				select_case()
			KEY_R:
				yaw = .7
				pitch = .3
				zoom = 1.15
	refresh()
