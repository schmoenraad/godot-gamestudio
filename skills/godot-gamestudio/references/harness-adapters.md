# Harness Adapters

Use the same role names and evidence contract on every harness.

| Harness | Specialist mechanism | Invocation guidance |
| --- | --- | --- |
| Codex | Project-local TOML profiles | Generate with `scripts/install_agents.py --harness codex`; delegate only after explicit studio invocation. |
| Claude Code | Plugin or project Markdown agents | Prefer bundled agents; Claude may route automatically from each description. |
| Gemini CLI | Extension or project Markdown agents | Prefer bundled agents; explicit `@agent-name` is available when routing must be forced. |
| Kimi Code CLI | Built-in `coder`, `explore`, and `plan` sub-agents | Use `coder` for makers and executable QA, `explore` for independent read-only review, and `plan` for design-only planning. Include the selected role instructions in every dispatch. |

Never claim named custom Kimi agents were created. Preserve reviewer independence by passing the brief, artifact, criteria, and evidence without maker reasoning.
