# Architecture

The repository has one canonical Agent Skills layer and thin harness adapters.

`skills/` contains portable role procedures. `roles/roles.json` owns role identity, descriptions, routing patterns, reviewer pairings, and Kimi dispatch intent. `scripts/generate_adapters.py` produces common Claude/Gemini Markdown agents, Kimi's role map, and the Codex marketplace package. CI fails when generated output drifts.

The Supervisor stores project state in `.godot-gamestudio/studio.json`. State is independent of the model and harness, so a milestone can resume in another supported CLI.

Claude and Gemini consume the generated `agents/` directory. Codex can create project-local TOML profiles with `scripts/install_agents.py --harness codex`. Kimi receives the selected role prompt through its built-in sub-agent that best matches the task.

GodotIQ is an optional verification backend. The core remains useful with ordinary Godot commands and must never mark unavailable verification as passed.
