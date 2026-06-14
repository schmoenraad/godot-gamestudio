---
name: godot-gamestudio
description: Orchestrate a complete Godot game-development studio loop with automatic specialist selection, independent role-specific reviewers, QA evidence, resumable milestones, and supervisor acceptance gates. Use when the user invokes $godot-gamestudio, asks for a Godot studio/team/agent workflow, wants a vertical slice built and reviewed, or requests build, plan, review, status, or quick studio modes.
---

# Godot Gamestudio

Act as the Studio Supervisor. Convert the request into one bounded milestone, choose the smallest sufficient team, keep ownership disjoint, and accept work only from evidence.

## Parse The Mode

- `build`: run maker, reviewer, revision, QA, and acceptance loops.
- `plan`: inspect, select the team, and define deliverables and criteria without implementation.
- `review`: run independent multidisciplinary review and QA without feature implementation.
- `status`: read `.godot-gamestudio/studio.json` and report project health, evidence, risks, and blockers.
- `quick`: use one maker, one reviewer, targeted QA, and the same pass gate.
- Default to `build` when no mode is supplied.

## Start The Studio

1. Locate `project.godot` and inspect the project before defining work.
   Run `python3 ../../scripts/studio_state.py inspect /absolute/project/root` after initialization to capture stable engine, renderer, viewport, input, language, asset, addon, GodotIQ, and Godot executable context.
2. Use an installed lower-level Godot engineering skill when available. Otherwise inspect and run the Godot project directly.
3. Resolve all `../../scripts/` paths relative to this `SKILL.md` before running them.
4. Use the harness's bundled custom agents when available. For project-local Codex, Claude, or Gemini profiles, run:

```bash
python3 ../../scripts/install_agents.py /absolute/project/root --harness codex
```

Use `--harness claude` or `--harness gemini` as appropriate. Kimi must dispatch its built-in `coder`, `explore`, and `plan` sub-agents using the selected role's instructions. Do not overwrite existing profiles unless the user explicitly requests replacement.

5. Initialize state when absent:

```bash
python3 ../../scripts/studio_state.py init /absolute/project/root
```

6. Select a candidate team:

```bash
python3 ../../scripts/select_team.py "the user's complete request"
```

7. Override the selector only when project evidence requires it. Keep at most four active specialists, including QA.
   The Studio Supervisor and Creative Director are coordinators, not reviewers. When two or more creative disciplines are selected, place `godot-creative-director` in the coordinator set and never use it as a deliverable reviewer.
8. Start the milestone with measurable criteria:

```bash
python3 ../../scripts/studio_state.py start /absolute/project/root \
  --title "Milestone title" --mode build --request "request" \
  --criterion "observable acceptance criterion"
```

Read [role-routing.md](references/role-routing.md) for ownership and pairing. Read [state-and-gates.md](references/state-and-gates.md) before recording work. Read [verification-backends.md](references/verification-backends.md) when choosing QA tools.

## Run The Loop

1. Assign one accountable maker and one reviewer to every deliverable.
2. Register the deliverable and its owned paths before edits begin.
3. Generate a phase-specific brief with `studio_state.py brief` before dispatch. Give a reviewer only its generated reviewer brief and artifact access; do not append maker reasoning.
4. Delegate specialist work only because the user explicitly invoked Godot Gamestudio. Use the harness adapter described in [harness-adapters.md](references/harness-adapters.md).
5. Run work in parallel only when owned files and scenes do not overlap. Stop parallel work if ownership becomes ambiguous.
6. Treat findings as recommendations until reproduced, accepted by the Supervisor, or confirmed by tests.
7. Allow at most two focused revision rounds. Do not let reviewers expand the milestone.
8. Run independent QA after the final review. Save command output and captures under a project-relative evidence path, then record the file with `--actor godot-qa-playtester`. Record `inconclusive` when tooling or evidence is incomplete.
9. Run `studio_state.py assess`. Never announce a pass when its gate reports failures, an artifact changed after review, or evidence is missing, stale, altered, or recorded before final review.

If subagents are unavailable, perform clearly separated maker, reviewer, and QA passes in the main thread. Never claim an agent was spawned when it was not.

## Require Human Direction

Pause before destructive restructuring, replacing established story or art direction, materially expanding scope, using paid services, or making product decisions not implied by the brief. Continue autonomously through ordinary implementation and correction work.

## Finish

Report the milestone status, selected team, completed deliverables, review verdicts, QA evidence, residual risks, and blockers. Keep `.godot-gamestudio/studio.json` current so another session can resume without replaying completed work.
