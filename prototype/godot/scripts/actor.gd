class_name Actor
extends Node2D
## Postać z atlasu: pozycja węzła = punkt styku z ziemią (kotwica), więc
## sortowanie po Y rodzica działa bez dodatkowych przesunięć.

var atlas: WeleszaAtlas
var world_pos := Vector2.ZERO  # metry (x do kamery, y w prawo)
var direction := 0
var animation_name := "spoczynek"
var body := AnimatedSprite2D.new()
var shadow := AnimatedSprite2D.new()


func setup(source: WeleszaAtlas, start: Vector2, facing: int) -> Actor:
	atlas = source
	world_pos = start
	direction = facing
	for sprite in [body, shadow]:
		sprite.centered = false
		sprite.offset = -atlas.anchor
	body.sprite_frames = atlas.body
	shadow.sprite_frames = atlas.shadow
	shadow.z_index = -1  # cienie pod wszystkimi obiektami, nad podłożem
	add_child(shadow)
	add_child(body)
	_apply()
	return self


func play(anim: String, facing: int) -> void:
	if anim == animation_name and facing == direction:
		return
	var frame := body.frame
	var progress := body.frame_progress
	animation_name = anim
	direction = facing
	_apply()
	# Zmiana kierunku w trakcie chodu nie resetuje fazy kroku.
	body.set_frame_and_progress(frame, progress)
	shadow.set_frame_and_progress(frame, progress)


func _apply() -> void:
	var key := "%s_%d" % [animation_name, direction]
	body.play(key)
	shadow.play(key)


func _process(_delta: float) -> void:
	position = WeleszaAtlas.world_to_screen(Vector3(world_pos.x, world_pos.y, 0.0))
