## What changed

Describe the user-visible behavior and why it belongs in Godot Gamestudio.

## Evidence

List focused tests, Godot commands, fixtures, screenshots, or benchmark results.

## Checklist

- [ ] I kept role identity and routing changes in `roles/roles.json` and regenerated adapters.
- [ ] I added or updated a focused regression test for behavior changes.
- [ ] Missing or inconclusive mandatory evidence still cannot pass.
- [ ] I recorded new third-party sources and compatible licensing in `NOTICE` when applicable.
- [ ] I removed credentials, raw auth data, private assets, and machine-specific paths.
- [ ] `python3 -m unittest discover -s tests -v` passes.
- [ ] `python3 scripts/validate_repo.py` passes.
