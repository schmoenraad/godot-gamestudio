#!/usr/bin/env python3
"""Build deterministic source archives for supported agent harnesses."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SENSITIVE_NAMES = {"auth.json", "oauth_creds.json", ".credentials.json"}


def validate_archive(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        unsafe = []
        for name in archive.namelist():
            parts = Path(name).parts
            if "evals" in parts and "results" in parts:
                unsafe.append(name)
            elif any(part in {".git", "dist", "home"} for part in parts):
                unsafe.append(name)
            elif Path(name).name in SENSITIVE_NAMES:
                unsafe.append(name)
        if unsafe:
            preview = "\n".join(unsafe[:10])
            raise SystemExit(f"Release archive contains excluded paths:\n{preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT / "dist"))
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_repo.py")], check=True)
    output.mkdir(parents=True, exist_ok=True)
    base = output / "godot-gamestudio"
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp) / "godot-gamestudio"
        shutil.copytree(
            ROOT,
            stage,
            ignore=shutil.ignore_patterns(
                ".git", "dist", "results", "home", "__pycache__", "*.pyc", ".godot", "artifacts",
                "auth.json", "oauth_creds.json", ".credentials.json"
            ),
        )
        archive = shutil.make_archive(str(base), "zip", root_dir=stage.parent, base_dir=stage.name)
    validate_archive(Path(archive))
    print(archive)


if __name__ == "__main__":
    main()
