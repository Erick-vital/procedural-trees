extends Node3D
## Visor de rama: giro libre y zoom; recursos congelados de la muestra.
var camera := Camera3D.new()
var sun := DirectionalLight3D.new()
var environment := WorldEnvironment.new()
var asset: Node3D
var wood: Node3D
var center := Vector3.ZERO
var span := 3.0
var yaw := .7
var pitch := .35
var zoom := 1.2
var spinning := false
var dark := false

func _ready() -> void:
	DisplayServer.window_set_title("Sauce · rama de muestra · Godot")
	get_viewport().msaa_3d = Viewport.MSAA_4X
	asset = load("res://crossed.tscn").instantiate()
	wood = load("res://wood.tscn").instantiate()
	add_child(asset)
	add_child(wood)
	wood.visible = false
	var config = JSON.parse_string(FileAccess.get_file_as_string("res://preview-config.json"))
	center = Vector3(config.center[0], config.center[2], -config.center[1])
	span = config.span
	add_child(camera)
	camera.current = true
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = .01
	camera.far = 100
	add_child(sun)
	sun.rotation_degrees = Vector3(-35, -25, 0)
	sun.light_energy = .75
	sun.shadow_enabled = true
	add_child(environment)
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color("EEE9DF")
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color.WHITE
	environment.environment.ambient_light_energy = .35
	var canvas := CanvasLayer.new()
	add_child(canvas)
	var panel := PanelContainer.new()
	canvas.add_child(panel)
	panel.position = Vector2(16, 16)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var label := Label.new()
	label.text = "Sauce · rama de muestra | %d tris · 2 materiales\nArrastrar: girar · Rueda: zoom · Espacio: giro automático\n1: follaje · 2: madera · B: fondo · L: luz · R: restablecer" % int(config.triangles)
	label.add_theme_constant_override("outline_size", 3)
	panel.add_child(label)
	update_camera()

func update_camera() -> void:
	camera.size = span*zoom
	camera.position = center + Vector3(sin(yaw)*cos(pitch), sin(pitch), cos(yaw)*cos(pitch))*span*3
	camera.look_at(center)

func _process(delta: float) -> void:
	if spinning:
		yaw += delta*.35
		update_camera()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and (Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)):
		yaw -= event.relative.x*.008
		pitch = clampf(pitch+event.relative.y*.008, -1.5, 1.5)
		update_camera()
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom = maxf(.25, zoom*.9)
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom = minf(5, zoom/ .9)
		update_camera()
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE: spinning = not spinning
			KEY_1:
				asset.visible = true
				wood.visible = false
			KEY_2:
				asset.visible = false
				wood.visible = true
			KEY_B:
				dark = not dark
				environment.environment.background_color = Color("252A28") if dark else Color("EEE9DF")
			KEY_L: sun.rotation_degrees.y += 60
			KEY_R:
				yaw = .7
				pitch = .35
				zoom = 1.2
		update_camera()
