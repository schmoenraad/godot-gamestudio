---
name: godot-audio-designer
description: Design Godot-native audio architecture, buses, SFX behavior, music states, ambience, voice playback, spatial audio, mixing, and implementation specifications. Use for audio deliverables and audio-system planning in Godot projects.
---

# Godot Audio Designer

1. Inspect existing buses, players, assets, state systems, and target platforms.
2. Define audio purpose, trigger, priority, variation, concurrency, attenuation, transitions, and ducking.
3. Prefer AudioServer buses, snapshots expressed through bus effects, and Godot audio nodes unless middleware already exists.
4. Separate content specifications from playback implementation and expose tuning values.
5. Check clipping, repetition, missing fallbacks, pause behavior, and save/settings integration.
6. Provide an audition or runtime evidence plan even when final audio assets are unavailable.
