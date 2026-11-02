extends "res://seasonal_tree_viewer.gd"
var mode := 0
var modes := ["Pintura otoñal", "Shader experimental", "Verano"]

func _ready() -> void:
	super._ready()
	DisplayServer.window_set_title("Roble · pintura / shader / verano")

func select_case() -> void:
	if is_instance_valid(asset): asset.free()
	var prefix := "painted-" if mode == 0 else ""
	asset = load("res://"+prefix+cases[selected].id+".tscn").instantiate()
	add_child(asset)
	var b = cases[selected].metrics.bounds_blender
	center = Vector3((b[0][0]+b[1][0])/2, (b[0][2]+b[1][2])/2, -(b[0][1]+b[1][1])/2)
	span = maxf(b[1][0]-b[0][0], maxf(b[1][1]-b[0][1], b[1][2]-b[0][2]))
	refresh()

func refresh() -> void:
	if asset.has_method("set_season_amount"): asset.set_season_amount(1.0 if mode == 1 else 0.0)
	label.text = "Roble · %s · %s | %d tris · 2 materiales\nO: pintura / shader / verano · N: otro árbol · Arrastrar: girar · Rueda: zoom · R: cámara" % [modes[mode], cases[selected].id, int(cases[selected].metrics.triangles)]
	camera.size = span*zoom
	camera.position = center+Vector3(sin(yaw)*cos(pitch), sin(pitch), cos(yaw)*cos(pitch))*span*3
	camera.look_at(center)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_O:
		mode = (mode+1)%3
		select_case()
		return
	super._unhandled_input(event)
