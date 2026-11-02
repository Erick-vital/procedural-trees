extends Node3D
## Visor del piloto: fase directa, avance reversible, comparación y órbita.
var asset: Node3D
var camera := Camera3D.new()
var slider := HSlider.new()
var status := Label.new()
var play_button := Button.new()
var direction_button := Button.new()
var playing := false
var direction := 1.0
var orbit := false
var yaw := .7
var pitch := .3
var zoom := 1.15
var center := Vector3.ZERO
var span := 15.0
var modes := ["Calendario por grupo","Mezcla uniforme","Verano pintado","Otoño pintado","Tinte experimental anterior"]

func _ready() -> void:
	DisplayServer.window_set_title("Roble · transición pintada T3")
	get_viewport().msaa_3d=Viewport.MSAA_4X
	asset=preload("res://pilot.tscn").instantiate();add_child(asset)
	add_child(camera);camera.current=true;camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.near=.01;camera.far=300
	var config=JSON.parse_string(FileAccess.get_file_as_string("res://transition-config.json"))
	var bounds=config.bounds_godot
	center=Vector3(bounds.center[0],bounds.center[1],bounds.center[2]);span=bounds.span
	var sun := DirectionalLight3D.new();add_child(sun)
	sun.rotation_degrees=Vector3(-35,-25,0);sun.light_energy=1.2;sun.shadow_enabled=true
	var world := WorldEnvironment.new();world.environment=Environment.new();add_child(world)
	world.environment.background_mode=Environment.BG_COLOR;world.environment.background_color=Color("EEE9DF")
	world.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	world.environment.ambient_light_color=Color.WHITE;world.environment.ambient_light_energy=.5
	world.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	var canvas := CanvasLayer.new();add_child(canvas)
	var panel := PanelContainer.new();canvas.add_child(panel);panel.position=Vector2(16,16)
	var box := VBoxContainer.new();panel.add_child(box)
	var title := Label.new();title.text="Roble · verano → otoño · copa completa";box.add_child(title)
	box.add_child(status)
	slider.min_value=0;slider.max_value=1;slider.step=.001;slider.custom_minimum_size=Vector2(490,30)
	box.add_child(slider);slider.value_changed.connect(func(value):asset.set_phase(value);refresh())
	var row := HBoxContainer.new();box.add_child(row)
	play_button.text="Reproducir";row.add_child(play_button)
	play_button.pressed.connect(func():playing=not playing;refresh())
	direction_button.text="Sentido: avance";row.add_child(direction_button)
	direction_button.pressed.connect(func():direction=-direction;refresh())
	var orbit_button := CheckButton.new();orbit_button.text="Órbita";row.add_child(orbit_button)
	orbit_button.toggled.connect(func(value):orbit=value)
	var choices := OptionButton.new();box.add_child(choices)
	for label in modes:choices.add_item(label)
	choices.item_selected.connect(func(index):asset.set_mode(index);refresh())
	var help := Label.new();help.text="Arrastrar: girar · rueda: zoom · R: restablecer cámara\nPrototipo T3 · pintura y calendario pendientes de aceptación";box.add_child(help)
	refresh()

func _process(delta: float) -> void:
	if playing:
		var value=slider.value+direction*delta/10.0
		if value>=1.0 or value<=0.0:playing=false
		slider.value=clampf(value,0,1)
	if orbit:yaw+=delta*.25
	if playing or orbit:refresh()

func refresh() -> void:
	status.text="Fase %.3f · %s · 6812 tris · 2 materiales" % [asset.phase,modes[asset.mode]]
	play_button.text="Pausar" if playing else "Reproducir"
	direction_button.text="Sentido: avance" if direction>0 else "Sentido: retroceso"
	camera.size=span*zoom
	camera.position=center+Vector3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))*span*3
	camera.look_at(center)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		yaw-=event.relative.x*.008;pitch=clampf(pitch+event.relative.y*.008,-1.4,1.4)
	if event is InputEventMouseButton and event.pressed:
		if event.button_index==MOUSE_BUTTON_WHEEL_UP:zoom=maxf(.25,zoom*.9)
		if event.button_index==MOUSE_BUTTON_WHEEL_DOWN:zoom=minf(5,zoom/.9)
	if event is InputEventKey and event.pressed and event.keycode==KEY_R:
		yaw=.7;pitch=.3;zoom=1.15
	refresh()
