#!/usr/bin/env python3
"""Install Godot Gamestudio agent profiles into a Godot project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def toml_string(value: str) -> str:
    return json.dumps(value)


ROOT = Path(__file__).resolve().parent.parent
ROLE_FILE = ROOT / "roles" / "roles.json"


def load_role_data() -> dict[str, tuple[str, str]]:
    data = json.loads(ROLE_FILE.read_text(encoding="utf-8"))
    return {
        item["id"]: (item["description"], item["instructions"])
        for item in data["roles"]
    }


ROLE_DATA = load_role_data()


def render_codex_agent(role: str, description: str, instructions: str, skill_path: Path, godot_path: Path | None) -> str:
    lines = [
        f"name = {toml_string(role)}",
        f"description = {toml_string(description)}",
        f"developer_instructions = {toml_string(instructions)}",
        "",
        "[[skills.config]]",
        f"path = {toml_string(str(skill_path))}",
        "enabled = true",
    ]
    if godot_path and godot_path.is_file():
        lines.extend(["", "[[skills.config]]", f"path = {toml_string(str(godot_path))}", "enabled = true"])
    return "\n".join(lines) + "\n"


def render_markdown_agent(role: str, description: str, instructions: str) -> str:
    return (
        "---\n"
        f"name: {role}\n"
        f"description: {description}\n"
        "---\n\n"
        f"Use the installed `{role}` Agent Skill as your operating procedure.\n\n"
        f"{instructions}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Godot project root containing project.godot")
    parser.add_argument("--role", action="append", choices=sorted(ROLE_DATA), help="Install only selected roles")
    parser.add_argument("--harness", choices=("codex", "claude", "gemini"), default="codex")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not (project / "project.godot").is_file():
        raise SystemExit(f"No project.godot at {project}")
    plugin_root = ROOT
    target = {
        "codex": project / ".codex" / "agents",
        "claude": project / ".claude" / "agents",
        "gemini": project / ".gemini" / "agents",
    }[args.harness]
    target.mkdir(parents=True, exist_ok=True)
    godot_path = Path.home() / ".codex" / "skills" / "godot" / "SKILL.md"
    roles = args.role or sorted(ROLE_DATA)
    written = []
    for role in roles:
        suffix = ".toml" if args.harness == "codex" else ".md"
        destination = target / f"{role}{suffix}"
        if destination.exists() and not args.force:
            raise SystemExit(f"Refusing to overwrite {destination}; pass --force")
        description, instructions = ROLE_DATA[role]
        skill_path = plugin_root / "skills" / role / "SKILL.md"
        if args.harness == "codex":
            content = render_codex_agent(role, description, instructions, skill_path, godot_path)
        else:
            content = render_markdown_agent(role, description, instructions)
        destination.write_text(content, encoding="utf-8")
        written.append(str(destination))
    print(json.dumps({"installed": written}, indent=2))


if __name__ == "__main__":
    main()
