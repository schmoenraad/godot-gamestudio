#!/usr/bin/env python3
"""Validate repository manifests, skills, generated adapters, and fixtures."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def require_json(relative: str) -> dict:
    path = ROOT / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Invalid JSON in {relative}: {error}") from error


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(f"Missing YAML frontmatter: {path}")
    try:
        raw = text.split("---\n", 2)[1]
    except IndexError as error:
        raise SystemExit(f"Unclosed YAML frontmatter: {path}") from error
    values = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def validate_skills() -> None:
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        metadata = frontmatter(path)
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if name != path.parent.name or not NAME_PATTERN.fullmatch(name):
            raise SystemExit(f"Invalid skill name in {path}: {name!r}")
        if not 1 <= len(description) <= 1024:
            raise SystemExit(f"Invalid skill description length in {path}")


def validate_manifests() -> None:
    codex = require_json(".codex-plugin/plugin.json")
    claude = require_json(".claude-plugin/plugin.json")
    require_json(".claude-plugin/marketplace.json")
    gemini = require_json("gemini-extension.json")
    kimi = require_json("kimi.plugin.json")
    marketplace = require_json(".agents/plugins/marketplace.json")
    names = {codex.get("name"), claude.get("name"), gemini.get("name"), kimi.get("name")}
    if names != {"godot-gamestudio"}:
        raise SystemExit(f"Manifest names disagree: {sorted(names)}")
    versions = {codex.get("version"), claude.get("version"), gemini.get("version"), kimi.get("version")}
    if len(versions) != 1:
        raise SystemExit(f"Manifest versions disagree: {sorted(versions)}")
    entry = marketplace.get("plugins", [{}])[0]
    if entry.get("source", {}).get("path") != "./plugins/godot-gamestudio":
        raise SystemExit("Codex marketplace does not target the generated package")


def main() -> None:
    validate_skills()
    validate_manifests()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_adapters.py"), "--check"], check=True)
    print("Repository validation passed")


if __name__ == "__main__":
    main()
