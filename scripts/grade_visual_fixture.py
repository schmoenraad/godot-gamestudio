#!/usr/bin/env python3
"""Grade the deterministic visual-hud Godot benchmark fixture."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import zlib
from pathlib import Path


def find_godot() -> str | None:
    candidates = (
        os.environ.get("GODOT_BIN"),
        shutil.which("godot4"),
        shutil.which("godot"),
        "/Applications/Godot.app/Contents/MacOS/Godot",
    )
    return next((value for value in candidates if value and Path(value).is_file()), None)


def png_details(path: Path) -> dict:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    if depth != 8 or color_type not in {2, 6}:
        return {"width": width, "height": height, "unique_colors": None, "color_type": color_type}
    channels = 3 if color_type == 2 else 4
    chunks = []
    position = 8
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        if kind == b"IDAT":
            chunks.append(payload)
        position += 12 + length
    raw = zlib.decompress(b"".join(chunks))
    stride = width * channels
    previous = bytearray(stride)
    offset = 0
    colors = set()
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset:offset + stride])
        offset += stride
        for index in range(stride):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                row[index] = (row[index] + left) & 255
            elif filter_type == 2:
                row[index] = (row[index] + up) & 255
            elif filter_type == 3:
                row[index] = (row[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                predictor = (left, up, upper_left)[distances.index(min(distances))]
                row[index] = (row[index] + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")
        for index in range(0, stride, channels):
            colors.add(bytes(row[index:index + channels]))
            if len(colors) >= 256:
                break
        previous = row
    return {"width": width, "height": height, "unique_colors": len(colors), "color_type": color_type}


def run(command: list[str], timeout: int) -> dict:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return {"exit_code": result.returncode, "stdout": result.stdout[-8000:], "stderr": result.stderr[-8000:]}
    except subprocess.TimeoutExpired as error:
        return {
            "exit_code": None,
            "timeout": True,
            "stdout": (error.stdout or "")[-8000:] if isinstance(error.stdout, str) else "",
            "stderr": (error.stderr or "")[-8000:] if isinstance(error.stderr, str) else "",
        }


def grade(project: Path) -> dict:
    godot = find_godot()
    checks = []
    if not godot:
        return {"status": "inconclusive", "reason": "Godot executable unavailable", "checks": checks}
    project_file = project / "project.godot"
    checks.append({"id": "project-file", "passed": project_file.is_file()})
    scene_files = list(project.rglob("*.tscn"))
    script_files = list(project.rglob("*.gd"))
    checks.append({"id": "scene-created", "passed": bool(scene_files), "count": len(scene_files)})
    checks.append({"id": "script-created", "passed": bool(script_files), "count": len(script_files)})
    source = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in scene_files + script_files)
    checks.append({"id": "health-label", "passed": bool(re.search(r"health", source, re.I))})
    checks.append({"id": "objective-label", "passed": bool(re.search(r"objective", source, re.I))})
    imported = run([godot, "--headless", "--path", str(project), "--editor", "--quit-after", "5"], 30)
    checks.append({"id": "godot-import", "passed": imported.get("exit_code") == 0, "result": imported})
    screenshot = project / "artifacts" / "result.png"
    if screenshot.is_file():
        shutil.copy2(screenshot, screenshot.with_name("agent-result.png"))
    screenshot.unlink(missing_ok=True)
    runtime = run([godot, "--headless", "--path", str(project)], 30)
    checks.append({"id": "runtime-exit", "passed": runtime.get("exit_code") == 0, "result": runtime})
    details = None
    if screenshot.is_file():
        try:
            details = png_details(screenshot)
        except (OSError, ValueError, zlib.error) as error:
            details = {"error": str(error)}
    checks.append({"id": "screenshot-created", "passed": details is not None, "path": str(screenshot)})
    checks.append({"id": "screenshot-size", "passed": bool(details and details.get("width") == 320 and details.get("height") == 180), "details": details})
    checks.append({"id": "visual-color-range", "passed": bool(details and (details.get("unique_colors") or 0) >= 5), "details": details})
    passed = all(item["passed"] for item in checks)
    return {"status": "pass" if passed else "fail", "checks": checks, "screenshot": str(screenshot) if screenshot.is_file() else None}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    args = parser.parse_args()
    print(json.dumps(grade(Path(args.project).resolve()), indent=2))


if __name__ == "__main__":
    main()
