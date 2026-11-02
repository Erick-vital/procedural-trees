extends "res://willow_sample_viewer.gd"
## Visor del árbol completo; conserva controles de cámara de la muestra.
var cases := []
var selected := 0

func _ready() -> void:
	super._ready()
	DisplayServer.window_set_title("Sauce pintado · árbol completo · Godot")
	var config = JSON.parse_string(FileAccess.get_file_as_string("res://preview-config.json"))
	cases = config.cases
	refresh_label()

func refresh_label() -> void:
	for node in get_children():
		if node is CanvasLayer:
			var label = node.get_child(0).get_child(0)
			label.text = "Sauce · %s | %d tris · 2 materiales\nArrastrar: girar · Rueda: zoom · Espacio: giro automático\n1: follaje · 2: madera · N: siguiente semilla · B: fondo · L: luz · R: cámara" % [cases[selected].id, int(cases[selected].triangles)]

func _unhandled_input(event: InputEvent) -> void:
	super._unhandled_input(event)
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_N:
		var show_wood: bool = wood.visible
		asset.free()
		wood.free()
		selected = (selected+1)%cases.size()
		asset = load("res://tree-"+cases[selected].id+".tscn").instantiate()
		wood = load("res://wood-"+cases[selected].id+".tscn").instantiate()
		add_child(asset)
		add_child(wood)
		asset.visible = not show_wood
		wood.visible = show_wood
		refresh_label()
