# Godot Gamestudio

Godot Gamestudio turns a coding agent into a supervised Godot team. A dynamic set of specialists creates the milestone, independent reviewers challenge the work, QA gathers runtime evidence, and the Supervisor only passes criteria that were actually observed.

It supports Codex, Claude Code, Gemini CLI, and Kimi Code CLI from one repository using the open Agent Skills format.

This repository brings the useful compatible lessons from GodotPrompter, Agent Sprite Forge, other public Godot skills, Agent Skills, GameDevBench, and optional GodotIQ workflows into one coherent distribution. See [SOURCES.md](SOURCES.md) for what was bundled, independently adapted, or used only as an integration reference.

## What It Adds

- Automatic routing across game design, narrative, worlds, sprites, gameplay, technical art, UI, audio, and QA
- Independent maker and reviewer roles
- Resumable `.godot-gamestudio/studio.json` milestones
- Disjoint file ownership and bounded revision loops
- Parse, startup, runtime, input, screenshot, animation, and regression evidence gates
- Optional GodotIQ integration when the user already has it installed

## Install

### Codex

```bash
codex plugin marketplace add schmoenraad/godot-gamestudio
codex plugin add godot-gamestudio@godot-gamestudio
```

### Claude Code

Inside Claude Code:

```text
/plugin marketplace add schmoenraad/godot-gamestudio
/plugin install godot-gamestudio@godot-gamestudio
```

For local development:

```bash
claude --plugin-dir /path/to/godot-gamestudio
```

### Gemini CLI

```bash
gemini extensions install https://github.com/schmoenraad/godot-gamestudio
```

### Kimi Code CLI

Inside Kimi Code:

```text
/plugins install https://github.com/schmoenraad/godot-gamestudio
/reload
```

Kimi currently exposes built-in `coder`, `explore`, and `plan` sub-agents rather than arbitrary plugin-defined agents. The Supervisor maps studio roles onto those agents while preserving the same maker-reviewer evidence contract.

## Use

Invoke the `godot-gamestudio` skill with one of these modes:

```text
godot-gamestudio build Create a playable top-down quest slice.
godot-gamestudio quick Fix player knockback and verify it.
godot-gamestudio plan Design a dialogue and quest milestone.
godot-gamestudio review Review the current vertical slice.
godot-gamestudio status
```

Skill syntax differs slightly by harness. Claude plugin skills are namespaced, for example `/godot-gamestudio:godot-gamestudio build ...`.

## Development

```bash
python3 scripts/generate_adapters.py
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
python3 scripts/run_benchmarks.py --suite routing --harness codex --harness gemini --case narrative-quest
```

Set `GODOT_BIN` when Godot is not discoverable as `godot4`, `godot`, or the default macOS app path.

The project is Apache-2.0 licensed. See [docs/product.md](docs/product.md) for Community and proposed Pro boundaries, and [docs/benchmarks.md](docs/benchmarks.md) for the evaluation plan.

The first executable pilot and its limitations are published in [docs/benchmark-results/2026-06-14-pilot.md](docs/benchmark-results/2026-06-14-pilot.md).
