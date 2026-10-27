class_name WeleszaAtlas
## Czyta JSON sprite'a według kontraktu renderu (docs/art/KONTRAKT-RENDERU.md)
## i buduje SpriteFrames: animacja "<nazwa>_<kierunek>" dla postaci i cienia.

const PIXELS_PER_METER := 60.0
const ELEVATION_DEG := 30.0

var data: Dictionary
var anchor: Vector2
var directions: PackedStringArray
var body := SpriteFrames.new()
var shadow := SpriteFrames.new()


static func world_to_screen(world: Vector3) -> Vector2:
	# Świat: +X do kamery (w dół ekranu), +Y w prawo, +Z w górę; metry.
	var e := deg_to_rad(ELEVATION_DEG)
	return Vector2(world.y, world.x * sin(e) - world.z * cos(e)) * PIXELS_PER_METER


## Kierunek z ruchu w płaszczyźnie świata (x, y): S=+X, SW, W=-Y, ..., E=+Y.
static func direction_index(velocity: Vector2) -> int:
	var phi := atan2(velocity.y, velocity.x)
	return posmod(roundi(-phi / (PI / 4.0)), 8)


func _init(json_path: String) -> void:
	data = JSON.parse_string(FileAccess.get_file_as_string(json_path))
	assert(data != null, "Nie można odczytać " + json_path)
	assert(is_equal_approx(data.pixels_per_meter, PIXELS_PER_METER), "Skala inna niż 60 px/m")
	anchor = Vector2(data.anchor_px[0], data.anchor_px[1])
	directions = PackedStringArray(data.directions)
	var base := json_path.get_base_dir()
	var size := Vector2(data.frame_size[0], data.frame_size[1])
	for anim_name in data.animations:
		var anim: Dictionary = data.animations[anim_name]
		_add(body, anim_name, anim, load(base.path_join(anim.file)), size)
		if anim.has("shadow_file"):
			_add(shadow, anim_name, anim, load(base.path_join(anim.shadow_file)), size)
	body.remove_animation("default")
	shadow.remove_animation("default")


func _add(frames: SpriteFrames, anim_name: String, anim: Dictionary, sheet: Texture2D, size: Vector2) -> void:
	for d in directions.size():
		var key := "%s_%d" % [anim_name, d]
		frames.add_animation(key)
		frames.set_animation_loop(key, anim.get("loop", true))
		# 1000 kl./s i czas klatki w ms => dokładne durations_ms z JSON.
		frames.set_animation_speed(key, 1000.0)
		for i in int(anim.frames):
			var region := AtlasTexture.new()
			region.atlas = sheet
			region.region = Rect2(Vector2(i, d) * size, size)
			frames.add_frame(key, region, float(anim.durations_ms[i]))
