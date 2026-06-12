#!/usr/bin/env python3
"""Build deterministic source archives for supported agent harnesses."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


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
                ".git", "dist", "__pycache__", "*.pyc", ".godot", "artifacts"
            ),
        )
        archive = shutil.make_archive(str(base), "zip", root_dir=stage.parent, base_dir=stage.name)
    print(archive)


if __name__ == "__main__":
    main()
