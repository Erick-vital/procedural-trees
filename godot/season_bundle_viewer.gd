extends Node3D
## Visor común T5: estado por ejemplar; controles de normales conservados.
var scene: Node3D
var config: Dictionary
var selected := 0
var normal_kind := "selected"
var states := {}
var slider := HSlider.new()
var status := Label.new()
var play_button := Button.new()
var direction_button := Button.new()
var case_picker := OptionButton.new()
var normal_picker := OptionButton.new()
var mode_picker := OptionButton.new()
var orbit_toggle := CheckButton.new()
var ground_toggle := CheckButton.new()
var playing := false
var direction := 1.0
var yaw := .7
var pitch := .3
var zoom := 1.15
var modes := ["Calendario por grupo","Mezcla uniforme","Verano fijo","Otoño fijo","Tinte anterior"]
var active_key := ""

func _ready() -> void:
	DisplayServer.window_set_title("Roble · cuatro casos estacionales T5")
	get_viewport().msaa_3d=Viewport.MSAA_4X
	config=JSON.parse_string(FileAccess.get_file_as_string("res://bundle-config.json"))
	scene=preload("res://season_bundle_scene.gd").new();add_child(scene)
	var canvas := CanvasLayer.new();add_child(canvas)
	var panel := PanelContainer.new();canvas.add_child(panel);panel.position=Vector2(16,16)
	var box := VBoxContainer.new();panel.add_child(box)
	box.add_child(status)
	for item in config.cases:case_picker.add_item(item.id)
	box.add_child(case_picker);case_picker.item_selected.connect(func(i):selected=i;select_case())
	normal_picker.add_item("Normales .35 aprobadas");normal_picker.add_item("Normales originales · control")
	box.add_child(normal_picker);normal_picker.item_selected.connect(func(i):normal_kind="selected" if i==0 else "original";select_case())
	slider.min_value=0;slider.max_value=1;slider.step=.001;slider.custom_minimum_size=Vector2(500,30)
	box.add_child(slider);slider.value_changed.connect(func(p):scene.asset.set_phase(p);refresh())
	var row := HBoxContainer.new();box.add_child(row)
	play_button.text="Reproducir";row.add_child(play_button);play_button.pressed.connect(func():playing=not playing;refresh())
	direction_button.text="Sentido: avance";row.add_child(direction_button);direction_button.pressed.connect(func():direction=-direction;refresh())
	for label in modes:mode_picker.add_item(label)
	box.add_child(mode_picker);mode_picker.item_selected.connect(func(i):scene.asset.set_mode(i);refresh())
	var flags := HBoxContainer.new();box.add_child(flags)
	orbit_toggle.text="Órbita";flags.add_child(orbit_toggle)
	ground_toggle.text="Suelo y sombras";flags.add_child(ground_toggle);ground_toggle.toggled.connect(func(value):scene.ground.visible=value;refresh())
	var help := Label.new();help.text="Arrastrar: girar · rueda: zoom · R: cámara\nCandidata T5 · copa completa · sin caída de hojas";box.add_child(help)
	select_case()

func select_case() -> void:
	var previous_phase=0.0
	if is_instance_valid(scene.asset):
		previous_phase=scene.asset.phase
		states[active_key]={"phase":scene.asset.phase,"mode":scene.asset.mode}
	active_key=config.cases[selected].id+":"+normal_kind
	scene.show_case(config.cases[selected],normal_kind)
	var saved=states.get(active_key,{"phase":previous_phase,"mode":0})
	scene.asset.set_phase(saved.phase);scene.asset.set_mode(saved.mode)
	slider.set_value_no_signal(saved.phase);mode_picker.select(saved.mode)
	refresh()

func refresh() -> void:
	var item=config.cases[selected]
	status.text="%s · fase %.3f · %d tris · 2 materiales"%[item.id,scene.asset.phase,int(item.triangles)]
	play_button.text="Pausar" if playing else "Reproducir"
	direction_button.text="Sentido: avance" if direction>0 else "Sentido: retroceso"
	scene.view(yaw,pitch,zoom)

func _process(delta: float) -> void:
	if playing:
		var p=slider.value+direction*delta/10.0
		if p>=1 or p<=0:playing=false
		slider.value=clampf(p,0,1)
	if orbit_toggle.button_pressed:yaw+=delta*.25
	if playing or orbit_toggle.button_pressed:refresh()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		yaw-=event.relative.x*.008;pitch=clampf(pitch+event.relative.y*.008,-1.4,1.4)
	if event is InputEventMouseButton and event.pressed:
		if event.button_index==MOUSE_BUTTON_WHEEL_UP:zoom=maxf(.25,zoom*.9)
		if event.button_index==MOUSE_BUTTON_WHEEL_DOWN:zoom=minf(6,zoom/.9)
	if event is InputEventKey and event.pressed and event.keycode==KEY_R:yaw=.7;pitch=.3;zoom=1.15
	refresh()
