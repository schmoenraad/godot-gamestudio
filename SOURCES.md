# Sources And Consolidation

Godot Gamestudio consolidates useful Godot agent workflows into one installable, supervised toolkit for Codex, Claude Code, Gemini CLI, and Kimi Code CLI. The resulting orchestration, state model, reviewer pairing, evidence gates, portability layer, tests, and product structure are original to this repository.

“Consolidates” does not mean every source was copied. We distinguish three cases:

- **Bundled with attribution:** compatible MIT-licensed material or scripts may be incorporated and retain their notices.
- **Adapted independently:** public workflows informed an independently written implementation.
- **Integration only:** commercial or separately licensed products are detected and used only when the user already has them.

## Primary Sources

| Source | Contribution to the combined toolkit | Treatment |
| --- | --- | --- |
| [GodotPrompter](https://github.com/jame581/GodotPrompter) | Broad Godot discipline prompts and domain coverage | MIT-licensed material may be bundled with attribution. |
| [Agent Sprite Forge](https://github.com/0x0funky/agent-sprite-forge) | Sprite extraction, cleanup, sheet, and visual-production workflows | MIT-licensed scripts and concepts may be bundled with attribution. |
| [haxqer/godot-skill](https://github.com/haxqer/godot-skill) | Godot CLI workflow and skill-packaging ideas | Inspiration only; no source redistributed because the reviewed revision had no license. |
| [fernforestgames/agent-skill-godot](https://github.com/fernforestgames/agent-skill-godot) | Godot-focused agent workflow and project guidance | Reviewed as inspiration; no source copied into this repository. |
| [bfollington/godot](https://smithery.ai/skills/bfollington/godot) | Public Godot skill packaging and discovery | Reviewed as inspiration; no source copied. |
| [Godot Gameplay Scripter](https://explainx.ai/skills/msitarzewski/agency-agents/Godot%20Gameplay%20Scripter) | Gameplay-specialist role framing | Reviewed as inspiration; no source copied. |
| [GodotIQ](https://godotiq.com/) | Optional live-editor verification and Community/Pro product comparison | Integration only; GodotIQ is not redistributed or resold. |
| [Agent Skills](https://agentskills.io/specification) | Portable `SKILL.md` structure | Open interoperability specification. |
| [GameDevBench](https://github.com/waynchi/gamedevbench) | External Godot benchmark methodology and category balance | Benchmark reference; its task set is not bundled here. |
| [GodotPrompter Reddit discussion](https://www.reddit.com/r/godot/comments/1sixn0d/godotprompter_44_ai_coding_skills_for_godot_game/) | Community context and discoverability | Discussion reference only. |

This repository should be understood as one useful distribution that connects these compatible lessons with a new maker-reviewer-supervisor loop. Contributions that add imported material must document the exact source revision and license before merging.
