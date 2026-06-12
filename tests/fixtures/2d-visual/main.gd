extends Node2D


func _ready() -> void:
	DirAccess.make_dir_absolute("res://artifacts")
	var image := Image.create(320, 180, false, Image.FORMAT_RGBA8)
	image.fill(Color("18243a"))
	paint_rect(image, Rect2i(24, 108, 272, 40), Color("31556d"))
	paint_circle(image, Vector2i(160, 76), 30, Color("f4c95d"))
	paint_rect(image, Rect2i(148, 68, 24, 48), Color("df5b57"))
	paint_rect(image, Rect2i(142, 112, 36, 8), Color("f7f3e3"))
	var error := image.save_png("res://artifacts/smoke.png")
	get_tree().quit(0 if error == OK else 1)


func paint_rect(image: Image, rect: Rect2i, color: Color) -> void:
	for y in range(rect.position.y, rect.end.y):
		for x in range(rect.position.x, rect.end.x):
			image.set_pixel(x, y, color)


func paint_circle(image: Image, center: Vector2i, radius: int, color: Color) -> void:
	var radius_squared := radius * radius
	for y in range(center.y - radius, center.y + radius + 1):
		for x in range(center.x - radius, center.x + radius + 1):
			var offset := Vector2i(x, y) - center
			if offset.length_squared() <= radius_squared:
				image.set_pixel(x, y, color)
