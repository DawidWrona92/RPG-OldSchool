extends Node2D
## Scena testowa: podłoże w skali 60 px/m, głaz z kotwicą z kontraktu,
## 8 stojących bohaterów (po jednym na kierunek) i dwóch chodzących wokół głazu.

const WALK_RADIUS_M := 1.4
const RING_RADIUS_M := 3.2
const GROUND_TILE_M := 4.0  # tekstura 1024 px pokrywa 4 m podłoża

var hero: WeleszaAtlas
var walkers: Array[Actor] = []
var walker_angles: Array[float] = [deg_to_rad(60.0), deg_to_rad(240.0)]
var frame_count := 0


func _ready() -> void:
	hero = WeleszaAtlas.new("res://assets/hero/bohater.json")
	_check_anchor()
	_add_ground()
	var world := Node2D.new()
	world.y_sort_enabled = true
	add_child(world)
	world.add_child(_static_sprite("res://assets/glaz/glaz.png", "res://assets/glaz/glaz_shadow.png", Vector2.ZERO))
	for d in 8:
		var phi := -d * PI / 4.0
		var pos := Vector2(cos(phi), sin(phi)) * RING_RADIUS_M
		world.add_child(Actor.new().setup(hero, pos, d))
	for a in walker_angles:
		var walker := Actor.new().setup(hero, Vector2(cos(a), sin(a)) * WALK_RADIUS_M, 0)
		walkers.append(walker)
		world.add_child(walker)
	var camera := Camera2D.new()
	camera.position = Vector2(0, -30)
	add_child(camera)


func _process(delta: float) -> void:
	var speed: float = hero.data.animations.chod.root_speed_mps
	for i in walkers.size():
		walker_angles[i] += speed / WALK_RADIUS_M * delta
		var a := walker_angles[i]
		walkers[i].world_pos = Vector2(cos(a), sin(a)) * WALK_RADIUS_M
		walkers[i].play("chod", WeleszaAtlas.direction_index(Vector2(-sin(a), cos(a))))
	frame_count += 1
	if frame_count == 10:
		var mib := 1024.0 * 1024.0
		print("WELESZA_TEXTURE_MEM_MIB %.1f" % (Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / mib))
		print("WELESZA_VIDEO_MEM_MIB %.1f" % (Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / mib))
		print("WELESZA_DRAW_CALLS %d" % Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))


func _check_anchor() -> void:
	# Kamera celuje w (0; 0; 1,2) m = środek klatki 96 px; kotwica musi leżeć
	# dokładnie tyle niżej, ile wynosi rzut 1,2 m wysokości.
	var centre := WeleszaAtlas.world_to_screen(Vector3(0, 0, 1.2))
	var expected := Vector2(96.0, 96.0) - hero.anchor
	print("WELESZA_ANCHOR_CHECK projected=%s expected=%s ok=%s" % [centre, expected, centre.is_equal_approx(expected)])


func _add_ground() -> void:
	var ground := Sprite2D.new()
	ground.texture = load("res://assets/ground/forest_litter_mixed.png")
	ground.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	ground.region_enabled = true
	ground.region_rect = Rect2(0, 0, 1024 * 8, 1024 * 8)
	var px := ground.texture.get_width()
	var tile := WeleszaAtlas.world_to_screen(Vector3(GROUND_TILE_M, GROUND_TILE_M, 0))
	ground.scale = Vector2(tile.x / px, tile.y / px)
	ground.z_index = -10
	add_child(ground)


func _static_sprite(body_path: String, shadow_path: String, world: Vector2) -> Node2D:
	var root := Node2D.new()
	root.position = WeleszaAtlas.world_to_screen(Vector3(world.x, world.y, 0))
	for path in [shadow_path, body_path]:
		var sprite := Sprite2D.new()
		sprite.texture = load(path)
		sprite.centered = false
		sprite.offset = -hero.anchor  # ta sama kamera => ta sama kotwica
		if path == shadow_path:
			sprite.z_index = -1
		root.add_child(sprite)
	return root
