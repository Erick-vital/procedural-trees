extends Node3D
## T4 separado de T3: pinturas fijas y normales exportadas.
var scene: Node3D
var variant := 0
var season := 0
var scope := 1
var light := 0
var receiver := true
var label := Label.new()
var config: Dictionary

func _ready() -> void:
	DisplayServer.window_set_title("Roble · comparación de normales T4")
	get_viewport().msaa_3d=Viewport.MSAA_4X
	config=JSON.parse_string(FileAccess.get_file_as_string("res://normal-review-config.json"))
	scene=preload("res://canopy_normals_scene.gd").new();add_child(scene)
	var layer := CanvasLayer.new();add_child(layer)
	var panel := PanelContainer.new();layer.add_child(panel);panel.position=Vector2(16,16)
	var box := VBoxContainer.new();panel.add_child(box);box.add_child(label)
	for entry in [["Normales",["Originales","Volumen local · 35 %","Volumen local · 65 %"]],["Pintura",["Verano","Otoño"]],["Muestra",["Rama del piloto","Piloto completo"]],["Luz",["Referencia","Lateral","Contraluz"]]]:
		var choices := OptionButton.new();box.add_child(choices)
		for value in entry[1]:choices.add_item(value)
		match entry[0]:
			"Normales":choices.item_selected.connect(func(i):variant=i;refresh(true))
			"Pintura":choices.item_selected.connect(func(i):season=i;refresh(true))
			"Muestra":
				choices.select(scope);choices.item_selected.connect(func(i):scope=i;refresh(true))
			"Luz":choices.item_selected.connect(func(i):light=i;refresh(false))
	var shadows := CheckButton.new();shadows.text="Suelo y sombras";shadows.button_pressed=true;box.add_child(shadows)
	shadows.toggled.connect(func(value):receiver=value;refresh(false))
	var text := Label.new();text.text="Arrastrar: girar · rueda: zoom · R: cámara\nEnsayo T4 · aceptación de normales pendiente";box.add_child(text)
	refresh(true)

func refresh(reload_asset: bool) -> void:
	if reload_asset:scene.show_case(config.scopes[scope]+"-"+config.variants[variant]+"-"+config.seasons[season],config.seasons[season])
	scene.sun.rotation_degrees=scene.LIGHTS[light];scene.ground.visible=receiver
	scene.camera.size=scene.span*scene.zoom
	scene.camera.position=scene.center+Vector3(sin(scene.yaw)*cos(scene.pitch),sin(scene.pitch),cos(scene.yaw)*cos(scene.pitch))*scene.span*3
	scene.camera.look_at(scene.center)
	label.text="T4 · %s · %s · %s\nMaterial estándar · geometría intacta"%[config.scopes[scope],config.variants[variant],config.seasons[season]]

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		scene.yaw-=event.relative.x*.008;scene.pitch=clampf(scene.pitch+event.relative.y*.008,-1.4,1.4)
	if event is InputEventMouseButton and event.pressed:
		if event.button_index==MOUSE_BUTTON_WHEEL_UP:scene.zoom=maxf(.25,scene.zoom*.9)
		if event.button_index==MOUSE_BUTTON_WHEEL_DOWN:scene.zoom=minf(6,scene.zoom/.9)
	if event is InputEventKey and event.pressed and event.keycode==KEY_R:
		scene.yaw=.7;scene.pitch=.3;scene.zoom=1.15
	refresh(false)
