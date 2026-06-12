# Contributing

Keep all role identity, routing, and harness prompts in `roles/roles.json`. Run `python3 scripts/generate_adapters.py` after changing it and commit generated outputs.

Every behavior change needs a focused test. Changes to orchestration or evidence gates must include a regression case proving that missing or inconclusive evidence cannot pass. Changes to visual workflows should include a deterministic fixture, screenshot, or video assertion.

Before opening a pull request, run:

```bash
python3 scripts/generate_adapters.py --check
python3 -m unittest discover -s tests -v
python3 scripts/validate_repo.py
```

Do not add third-party code or substantial documentation excerpts without recording its source, revision, and compatible license in `NOTICE`.
