---
name: godot-sprite-studio
description: Art-direct, generate, process, and integrate Godot sprites, pixel art, character sheets, tilesets, props, portraits, and 2D animation assets. Use when visual assets require consistent prompts, deterministic frame processing, Godot imports, or SpriteFrames integration.
---

# Godot Sprite Studio

1. Establish or read the style bible: dimensions, palette, perspective, outline, light direction, anchors, and naming.
2. Read [sprite-factory.md](references/sprite-factory.md) before generating production sheets, animation sheets, outfit variants, or prop packs.
3. For Berlin Bytes / The Tourister work, also read [berlin-bytes-sprite-contract.md](references/berlin-bytes-sprite-contract.md).
4. Use an available image-generation capability for raster creation and deterministic scripts for extraction, grading, cleanup, and contact sheets.
5. Generate one coherent action family at a time. Keep detached effects separate when their geometry differs.
6. Before integration, run `scripts/grade_sprite_sheet.py` on raw sheets when the task uses a fixed grid.
7. If a sheet is visually useful but fails for keyed-background, oversized-cell, or centering issues, run `scripts/normalize_sprite_sheet.py`, then grade the normalized output.
8. Inspect every frame for edge contact, scale drift, anchor drift, silhouette loss, transparency, and palette inconsistency.
9. Integrate assets into imports, SpriteFrames, AnimationPlayer, TileSet, or scenes as appropriate.
10. Produce grader JSON plus normalization JSON, a contact sheet, or runtime capture as review evidence when applicable.

Do not treat a concept image as a finished playable asset.
