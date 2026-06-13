# Security

Godot Gamestudio instructions can cause an agent to execute project commands and modify game files. Review third-party projects before running them and use each harness's normal permission controls.

Report suspected command-injection, path-escape, destructive-edit, or evidence-forgery issues privately through GitHub security advisories once the public repository is available. Do not include private game assets or credentials in reports.

The benchmark runner may copy existing CLI authentication into an isolated temporary home for the duration of one run. It removes that home in an unconditional cleanup block and excludes all raw results from Git. Do not interrupt the host machine during credential setup; after an interrupted run, remove any `home` directory under `evals/results/` before sharing artifacts.
