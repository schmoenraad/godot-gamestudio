#!/usr/bin/env python3
"""Inspect a Godot project and emit stable orchestration context as JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


IGNORED_DIRS = {".git", ".godot", ".godot-gamestudio", "artifacts", "dist", "evals/results"}
FILE_GROUPS = {
    "scenes": {".tscn", ".scn"},
    "scripts": {".gd", ".cs"},
    "resources": {".tres", ".res"},
    "images": {".png", ".jpg", ".jpeg", ".webp", ".svg"},
    "audio": {".wav", ".ogg", ".mp3"},
    "models": {".glb", ".gltf", ".blend", ".fbx", ".obj"},
}


def find_godot() -> str | None:
    candidates = (
        os.environ.get("GODOT_BIN"),
        shutil.which("godot4"),
        shutil.which("godot"),
        "/Applications/Godot.app/Contents/MacOS/Godot",
    )
    return next((value for value in candidates if value and Path(value).is_file()), None)


def match_string(text: str, key: str) -> str | None:
    match = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]*)"', text, re.MULTILINE)
    return match.group(1) if match else None


def match_int(text: str, key: str) -> int | None:
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(\d+)", text, re.MULTILINE)
    return int(match.group(1)) if match else None


def section(text: str, name: str) -> str:
    match = re.search(rf"^\[{re.escape(name)}\]\s*$([\s\S]*?)(?=^\[|\Z)", text, re.MULTILINE)
    return match.group(1) if match else ""


def project_files(project: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(project):
        relative_root = Path(root).relative_to(project)
        dirs[:] = [
            name for name in dirs
            if name not in IGNORED_DIRS and (relative_root / name).as_posix() not in IGNORED_DIRS
        ]
        files.extend(Path(root) / name for name in names)
    return files


def inspect(project: Path) -> dict[str, Any]:
    project = project.expanduser().resolve()
    project_file = project / "project.godot"
    if not project_file.is_file():
        raise SystemExit(f"No project.godot found at {project}")
    text = project_file.read_text(encoding="utf-8", errors="replace")
    feature_match = re.search(r"config/features\s*=\s*PackedStringArray\(([^\n]+)\)", text)
    features = re.findall(r'"([^"]+)"', feature_match.group(1)) if feature_match else []
    input_actions = re.findall(r"^([A-Za-z0-9_./-]+)\s*=\s*\{", section(text, "input"), re.MULTILINE)
    files = project_files(project)
    counts = {
        group: sum(path.suffix.lower() in suffixes for path in files)
        for group, suffixes in FILE_GROUPS.items()
    }
    addons_root = project / "addons"
    addons = sorted(path.name for path in addons_root.iterdir() if path.is_dir()) if addons_root.is_dir() else []
    languages = []
    if any(path.suffix.lower() == ".gd" for path in files):
        languages.append("GDScript")
    if any(path.suffix.lower() == ".cs" for path in files):
        languages.append("C#")
    return {
        "root": str(project),
        "name": match_string(text, "config/name"),
        "engine_features": features,
        "main_scene": match_string(text, "run/main_scene"),
        "renderer": match_string(text, "renderer/rendering_method"),
        "viewport": {
            "width": match_int(text, "window/size/viewport_width"),
            "height": match_int(text, "window/size/viewport_height"),
            "stretch_mode": match_string(text, "window/stretch/mode"),
        },
        "input_actions": sorted(input_actions),
        "languages": languages,
        "file_counts": counts,
        "addons": addons,
        "godotiq": {
            "detected": any("godotiq" in name.lower() for name in addons),
            "tier": os.environ.get("GODOTIQ_TIER", "unknown"),
        },
        "godot_binary": find_godot(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    args = parser.parse_args()
    print(json.dumps(inspect(Path(args.project)), indent=2))


if __name__ == "__main__":
    main()
