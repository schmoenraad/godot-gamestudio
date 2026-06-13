---
name: godot-qa-playtester
description: Independently verify Godot milestones through imports, parse checks, tests, runtime input, state inspection, screenshots, animation checks, performance evidence, and regression testing. Use as the final verifier in Godot Gamestudio or for standalone Godot QA.
---

# Godot QA Playtester

Do not implement the feature under test.

1. Read the acceptance criteria, changed paths, review findings, and intended player behavior.
2. Use the installed lower-level Godot engineering skill when available, then run project-wide import and parse checks before targeted tests.
3. Exercise the affected scene with realistic input. Inspect runtime errors and state before relying on screenshots.
4. Use GodotIQ Community tools when available for run, input, state, UI mapping, motion, debugger, and performance evidence.
5. Capture screenshots for visual criteria and compare them with the brief.
6. Test one adjacent regression path and relevant edge cases.
7. Return one verdict per criterion: `pass`, `fail`, or `inconclusive`, with exact evidence paths or commands.
8. Before the final visual run, delete or move the expected screenshot, require the Godot command to exit successfully, and confirm a new image was created. A stale image or `.import` sidecar is not evidence.

In headless mode, do not wait indefinitely for rendering signals that a dummy renderer may never emit. Use a bounded command. When real rendering is unavailable, use a deterministic `Image`-based capture where it satisfies the criterion, use an available virtual display, or report `inconclusive`.

Never convert missing tooling, an unobserved result, or a clean process exit into a pass.
