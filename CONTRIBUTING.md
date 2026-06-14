# Contributing

Keep all role identity, routing, and harness prompts in `roles/roles.json`. Run `python3 scripts/generate_adapters.py` after changing it and commit generated outputs.

Every behavior change needs a focused test. Changes to orchestration or evidence gates must include a regression case proving that missing or inconclusive evidence cannot pass. Changes to visual workflows should include a deterministic fixture, screenshot, or video assertion.

## Benchmark Contributions

Use the benchmark issue form before investing in a large fixture. A useful submission includes the exact task, observable acceptance criteria, Godot and harness versions, repetitions, sanitized evidence, and a clear distinction between `fail` and `inconclusive`.

Prefer small fixtures that isolate one capability. Keep private game assets and credentials out of the repository. Seeded-defect reviewer tests should document the hidden defects in grader data rather than leaking them into the agent prompt.

## Good First Contributions

Documentation examples, additional routing cases, minimal Godot fixtures, and harness portability tests are good starting points. Comment on the issue before substantial work so parallel contributors do not duplicate the same fixture.

Before opening a pull request, run:

```bash
python3 scripts/generate_adapters.py --check
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
```

Do not add third-party code or substantial documentation excerpts without recording its source, revision, and compatible license in `NOTICE`.
