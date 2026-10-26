class_name RpgAtlas
extends RefCounted
## Adapter for rpg-sprite-v4 JSON and the user's original Sheet.gd metadata.
## Does not modify existing project. Copy file to res://scripts/ and use explicitly.
## Direction order must match game's Iso.dir_index() (yaw 0..315 in 45 degree steps).

static func load_meta(path: String) -> Dictionary:
	var txt: String = FileAccess.get_file_as_string(path)
	if txt.is_empty():
		push_error("RpgAtlas: empty or missing metadata: " + path)
		return {}
	var parsed: Variant = JSON.parse_string(txt)
	if not (parsed is Dictionary):
		push_error("RpgAtlas: invalid JSON object: " + path)
		return {}
	return parsed

static func make_frames(sheet_path: String, meta_path: String, prefix: String = "walk", fps: float = 10.0, loop: bool = true) -> SpriteFrames:
	var meta: Dictionary = load_meta(meta_path)
	var texture: Texture2D = load(sheet_path)
	if texture == null or meta.is_empty():
		push_error("RpgAtlas: asset missing: " + sheet_path)
		return null
	var sz: Array = meta.get("frame_size", [])
	if sz.size() != 2:
		push_error("RpgAtlas: frame_size missing")
		return null
	var fw: int = int(sz[0])
	var fh: int = int(sz[1])
	if fw <= 0 or fh <= 0:
		push_error("RpgAtlas: invalid frame dimensions")
		return null
	var result := SpriteFrames.new()
	if result.has_animation("default") and prefix != "default":
		result.remove_animation("default")
	for entry in meta.get("frames", []):
		var x: int = int(entry.get("x", -1))
		var y: int = int(entry.get("y", -1))
		if x < 0 or y < 0 or x + fw > texture.get_width() or y + fh > texture.get_height():
			push_error("RpgAtlas: frame outside texture")
			return null
		var angle: float = float(entry.get("view_angle_deg", int(entry.get("direction", 0)) * 45))
		var dir: int = posmod(int(round(angle / 45.0)), 8)
		var anim: String = "%s_%d" % [prefix, dir]
		if not result.has_animation(anim):
			result.add_animation(anim)
			result.set_animation_speed(anim, fps)
			result.set_animation_loop(anim, loop)
		var region := AtlasTexture.new()
		region.atlas = texture
		region.region = Rect2(x, y, fw, fh)
		result.add_frame(anim, region)
		# Godot duration is a multiplicative factor relative to animation speed.
		var ms: float = float(entry.get("duration_ms", meta.get("duration_ms", 1000.0 / fps)))
		var last: int = result.get_frame_count(anim) - 1
		result.set_frame_duration(anim, last, maxf(0.01, ms * fps / 1000.0))
	return result

static func anchor_offset(meta_path: String) -> Vector2:
	var m: Dictionary = load_meta(meta_path)
	var sz: Array = m.get("frame_size", [0, 0])
	var anchor: Array = m.get("anchor", [0, 0])
	return Vector2(float(sz[0]) * 0.5 - float(anchor[0]), float(sz[1]) * 0.5 - float(anchor[1]))

static func make_sprite(sheet_path: String, meta_path: String, prefix: String = "walk", fps: float = 10.0) -> AnimatedSprite2D:
	var frames: SpriteFrames = make_frames(sheet_path, meta_path, prefix, fps)
	if frames == null:
		return null
	var spr := AnimatedSprite2D.new()
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.sprite_frames = frames
	spr.offset = anchor_offset(meta_path)
	spr.play("%s_0" % prefix)
	return spr
