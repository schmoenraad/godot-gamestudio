# Berlin Bytes Sprite Contract

Use this reference for Berlin Bytes / The Tourister sprites.

## Visual Target

- Top-down Game Boy Color / Pokemon-like RPG readability.
- Native viewport is `320x288`; maps use `16x16` tiles.
- Production direction is not voxel, isometric, painterly, or full-scene background art.
- Gameplay readability comes before mood and detail.

## Sprite Priorities

1. Readable silhouette at native scale.
2. Clear facing direction.
3. Stable feet anchor.
4. Outfit distinction.
5. Berlin atmosphere through broad shapes and limited accents.

## Character Rules

Player:

- small tourist silhouette with strong dark outline
- clear head/body separation
- one readable accessory such as cap, bag, sunglasses, scarf, or mask detail
- outfit variants: normal tourist, Berghain black, Sisyphos colorful, Kater Blau artsy, KitKat black with mask/choker detail

NPCs:

- silhouette role first, color second
- bouncer is tall, black, high-contrast, and calm
- queue NPCs should differ by body shape and posture, not tiny costume details

Props:

- mattress, chair, crate, U-Bahn sign, Späti props, bins, bikes, queue posts, and door lights must read by silhouette first
- pickups should be more readable than background clutter

## Berlin Prompt Additions

Add these constraints to raw sprite prompts:

```text
Top-down Game Boy Color RPG sprite for a 320x288 Godot game with 16x16 tiles.
Pokemon-like overworld readability, crisp dark outline, limited palette, nearest-neighbor pixel art.
Same character scale and same feet baseline in every cell.
Flat #FF00FF background, no labels, no UI, no borders, no isometric or voxel angle.
```

Use project art docs when available: `docs/ART_BIBLE.md`, `docs/VISUAL_SOURCE_AUDIT.md`, and recent screenshots.
