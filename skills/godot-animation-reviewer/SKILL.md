---
name: godot-animation-reviewer
description: Independently review Godot sprite sheets and animations for timing, anchors, scale, silhouettes, loops, transitions, event timing, state coverage, and runtime playback. Use as the opposing reviewer for animated visual deliverables.
---

# Godot Animation Reviewer

Do not edit files and do not read maker reasoning.

1. Inspect raw frames, processed frames, import settings, SpriteFrames or AnimationPlayer data, and runtime playback.
2. Run or inspect `scripts/grade_sprite_sheet.py` output for fixed-grid sheets when available.
3. Check anchor and scale drift, clipping, edge contact, cadence, anticipation, impact, recovery, looping, and transition pops.
4. Verify animation names and state-machine transitions match gameplay code.
5. Check detached effects and event timing against the owning action.
6. Return concrete frame or runtime evidence and a final verdict.
