# Sprite Factory

Use this reference when creating or reviewing production sprites, sprite sheets, outfit variants, props, or animation sheets.

## Contract First

Before generation, define:

- asset role: `player`, `npc`, `prop`, `pickup`, `outfit`, `fx`, or `tileset`
- final cell size and grid: for example `2x2` at `32x32` cells, or `4x4` for four-direction walk
- anchor: `feet` / bottom-center for grounded actors, center for floating FX
- view: top-down, side, 3/4, or UI icon
- allowed palette and outline weight
- target output paths for raw source, processed frames, contact sheet, and Godot-ready atlas

Do not generate a mixed-action atlas as the raw source for a controllable character. Generate one coherent action family at a time, then assemble engine atlases deterministically.

## Prompt Guardrails

Use a flat `#FF00FF` background for raw sheets. Require:

- exact grid count only
- no text, labels, UI, borders, dividers, arrows, or frame numbers
- same identity in every cell
- same pixel scale and bounding box in every cell
- no edge contact; leave magenta margin on all sides
- no detached effects for body actions unless they are intentionally part of the asset

For player and NPC body animation, keep attacks, projectiles, muzzle flashes, slash arcs, and impact bursts as separate FX sheets unless the runtime supports explicit origins and variable cells.

## Process And Grade

Save generated raw sheets under a work-in-progress path. Before integration, run:

```bash
python3 scripts/grade_sprite_sheet.py raw-sheet.png --rows 2 --cols 2
```

The grader rejects wrong grid dimensions, missing cells, edge contact, large scale drift, anchor drift, and non-magenta corner backgrounds. Treat a failing sheet as source material, not as game-ready art.

If the raw sheet is visually useful but fails because the background is not exactly keyed, cells are too large, or sprites need deterministic centering, normalize it before integration:

```bash
python3 scripts/normalize_sprite_sheet.py raw-sheet.png processed-sheet.png --rows 2 --cols 2 --cell-size 32
python3 scripts/grade_sprite_sheet.py processed-sheet.png --rows 2 --cols 2
```

Use normalization as a recovery step, not as permission to accept bad art. Reject or regenerate sheets with missing frames, inconsistent character identity, wrong perspective, merged props, unreadable silhouettes, or animation poses that do not match the brief.

When a sheet passes, extract or normalize frames, create a contact sheet, integrate into Godot imports or `SpriteFrames`, and capture a runtime screenshot. Approval requires the processed asset to read correctly in the game viewport, not only in the raw image.

## Review Evidence

Return:

- raw prompt and raw sheet path
- grader JSON path
- normalization JSON path when a recovery step was used
- processed frame or atlas paths
- contact sheet path
- Godot runtime screenshot path
- known limitations and whether the asset is final or WIP
