# Evaluation And Improvement

Every candidate release is compared in clean contexts against the previous release and a no-skill baseline.

## Conditions

- No Godot Gamestudio skill
- Community skill
- Community without independent reviewer
- Community without Supervisor evidence gate
- Pro visual-feedback loop when available

Run each condition on every supported harness with at least three repetitions after the pilot phase. Record model, harness version, Godot version, platform, prompt, output, changed files, duration, tokens, retries, screenshots, video, and grader decisions.

## Metrics

- Godot import, parse, startup, and runtime criterion pass rate
- Visual and animation criterion pass rate
- False-pass and inconclusive rates
- Reviewer precision on seeded defects
- Scope violations and overlapping ownership
- Time, tokens, cost, retries, and files changed
- Blind human preference for readability, coherence, and polish

Deterministic structural checks come before perceptual similarity. Visual fixtures use fixed viewport, camera, seed, assets, and scripted input. Perceptual metrics are supporting evidence, not sole approval authority.

## Continual Improvement

Store immutable benchmark results per release. Cluster failures by role, harness, and gate. Generate candidate changes on a branch, rerun the full affected category, and require human review before merging. Reject changes that improve one fixture while degrading another harness or category.

Production installations never rewrite their own skills. Improvement happens through measured candidate releases, beta channels, changelogs, and rollback.
