# State And Gates

The authoritative file is `<project>/.godot-gamestudio/studio.json`. Use `../../scripts/studio_state.py` rather than hand-editing normal lifecycle fields.

Core commands:

```bash
python3 ../../scripts/studio_state.py add-deliverable PROJECT --id player --owner godot-gameplay-engineer --reviewer godot-code-reviewer --path scripts/player.gd
python3 ../../scripts/studio_state.py complete-deliverable PROJECT --id player
python3 ../../scripts/studio_state.py review PROJECT --deliverable player --reviewer godot-code-reviewer --verdict approved --summary "No blocking findings"
python3 ../../scripts/studio_state.py evidence PROJECT --criterion c1 --kind runtime --path evidence/player-run.log --verdict pass --summary "Movement verified"
python3 ../../scripts/studio_state.py revision PROJECT
python3 ../../scripts/studio_state.py assess PROJECT
python3 ../../scripts/studio_state.py status PROJECT
python3 ../../scripts/studio_state.py set-constraint PROJECT --key target_platform --value desktop
```

A build or quick milestone passes only when every deliverable is completed, every final review is approved, every required criterion has latest evidence marked `pass`, and no blockers remain. Missing, failed, or inconclusive evidence prevents a pass.
