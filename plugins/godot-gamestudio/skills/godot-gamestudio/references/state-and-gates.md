# State And Gates

The authoritative file is `<project>/.godot-gamestudio/studio.json`. Use `../../scripts/studio_state.py` rather than hand-editing normal lifecycle fields.

Core commands:

```bash
python3 ../../scripts/studio_state.py add-deliverable PROJECT --id player --owner godot-gameplay-engineer --reviewer godot-code-reviewer --path scripts/player.gd
python3 ../../scripts/studio_state.py brief PROJECT --phase maker --deliverable player
python3 ../../scripts/studio_state.py complete-deliverable PROJECT --id player
python3 ../../scripts/studio_state.py brief PROJECT --phase reviewer --deliverable player
python3 ../../scripts/studio_state.py review PROJECT --deliverable player --reviewer godot-code-reviewer --verdict approved --summary "No blocking findings"
python3 ../../scripts/studio_state.py brief PROJECT --phase qa
python3 ../../scripts/studio_state.py evidence PROJECT --criterion c1 --actor godot-qa-playtester --kind runtime --path evidence/player-run.log --verdict pass --summary "Movement verified"
python3 ../../scripts/studio_state.py revision PROJECT --deliverable player
python3 ../../scripts/studio_state.py block PROJECT --reason "Needs a user decision on save compatibility"
python3 ../../scripts/studio_state.py resolve-blocker PROJECT --id b1 --resolution "User chose migration"
python3 ../../scripts/studio_state.py assess PROJECT
python3 ../../scripts/studio_state.py status PROJECT
python3 ../../scripts/studio_state.py set-constraint PROJECT --key target_platform --value desktop
```

A build or quick milestone passes only when every deliverable is completed, its approval targets the current artifact revision, every required criterion has fresh QA evidence marked `pass`, and no blockers remain. Evidence must be a project-relative file created during the milestone; the state records its SHA-256 digest and rejects missing or changed artifacts. QA evidence recorded before the final approval is stale.
