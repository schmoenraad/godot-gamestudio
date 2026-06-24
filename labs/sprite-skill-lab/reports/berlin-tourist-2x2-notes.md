# Berlin Tourist 2x2 Sprite Lab Notes

## Test

Generated a 2x2 Berlin tourist overworld sprite sheet from the Sprite Studio contract prompt.

Raw image:

- `/Users/koenraad/plugins/godot-gamestudio/labs/sprite-skill-lab/inputs/berlin-tourist-2x2-raw.png`

Processed image:

- `/Users/koenraad/plugins/godot-gamestudio/labs/sprite-skill-lab/outputs/berlin-tourist-2x2-normalized.png`

## Findings

The raw generation produced a readable, consistent character, but the magenta background was a gradient rather than exact `#FF00FF`.

The raw grade failed:

- `magenta-corners`: failed
- `no-cell-edge-contact`: failed, because the non-exact background was treated as content in every cell

After normalization, the processed sheet passed:

- grid: `2x2`
- output atlas: `64x64`
- cell size: `32x32`
- no edge contact
- no scale drift
- no anchor drift

## Skill Update

Sprite Studio now includes a deterministic recovery step:

```bash
python3 scripts/normalize_sprite_sheet.py raw-sheet.png processed-sheet.png --rows 2 --cols 2 --cell-size 32
python3 scripts/grade_sprite_sheet.py processed-sheet.png --rows 2 --cols 2
```

Normalization is useful for keyed-background cleanup, oversized generated sheets, and deterministic frame centering. It should not be used to accept missing frames, wrong perspective, identity drift, or unreadable silhouettes.
