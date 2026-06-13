#!/usr/bin/env python3
"""Run reproducible Godot Gamestudio benchmarks across supported harnesses."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SUPPORTED_HARNESSES = ("codex", "claude", "gemini", "kimi")
SUPPORTED_CONDITIONS = ("baseline", "community")


def copy_if_present(source: Path, destination: Path) -> None:
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def isolated_environment(harness: str, run_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    home = run_dir / "home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    if harness == "codex":
        codex_home = home / ".codex"
        codex_home.mkdir()
        copy_if_present(Path.home() / ".codex" / "auth.json", codex_home / "auth.json")
        env["CODEX_HOME"] = str(codex_home)
    elif harness == "claude":
        claude_home = home / ".claude"
        claude_home.mkdir()
        for name in (".credentials.json", "settings.json"):
            copy_if_present(Path.home() / ".claude" / name, claude_home / name)
    elif harness == "gemini":
        gemini_home = home / ".gemini"
        gemini_home.mkdir()
        for name in ("oauth_creds.json", "google_accounts.json", "settings.json"):
            copy_if_present(Path.home() / ".gemini" / name, gemini_home / name)
    elif harness == "kimi":
        kimi_home = home / ".kimi-code"
        kimi_home.mkdir()
        for name in ("config.toml", "device_id"):
            copy_if_present(Path.home() / ".kimi-code" / name, kimi_home / name)
    return env


def find_godot() -> str | None:
    candidates = (
        os.environ.get("GODOT_BIN"),
        shutil.which("godot4"),
        shutil.which("godot"),
        "/Applications/Godot.app/Contents/MacOS/Godot",
    )
    return next((value for value in candidates if value and Path(value).is_file()), None)


def install_godot_guard(run_dir: Path, env: dict[str, str]) -> None:
    actual = find_godot()
    if not actual:
        return
    binary_dir = run_dir / "bin"
    binary_dir.mkdir(parents=True, exist_ok=True)
    guard = binary_dir / "godot"
    shutil.copy2(ROOT / "scripts" / "godot_guard.py", guard)
    guard.chmod(0o755)
    (binary_dir / "godot4").symlink_to(guard.name)
    env["REAL_GODOT_BIN"] = actual
    env["GODOT_BIN"] = str(guard)
    env["GODOT_GUARD_TIMEOUT"] = "45"
    env["PATH"] = str(binary_dir) + os.pathsep + env.get("PATH", "")


def install_skills(workspace: Path) -> None:
    destination = workspace / ".agents" / "skills"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "skills", destination)


def extract_json(text: str) -> dict[str, Any] | None:
    candidates = [text.strip()]
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        candidates.insert(0, fence.group(1))
    starts = [index for index, character in enumerate(text) if character == "{"]
    for start in reversed(starts):
        candidates.append(text[start:])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def normalize_response(harness: str, stdout: str, last_message: Path) -> str:
    if last_message.is_file():
        return last_message.read_text(encoding="utf-8", errors="replace")
    outer = extract_json(stdout)
    if harness == "gemini" and outer and isinstance(outer.get("response"), str):
        return outer["response"]
    if harness == "claude" and outer and isinstance(outer.get("result"), str):
        return outer["result"]
    return stdout


def classify_failure(output: str, exit_code: int | None, timed_out: bool) -> str:
    lowered = output.lower()
    if any(token in lowered for token in ("failed to authenticate", "authentication_error", "invalid authentication", "no model configured", "please set an auth method")):
        return "unavailable_auth"
    if any(token in lowered for token in ("enotfound", "getaddrinfo", "network is unreachable", "temporary failure in name resolution")):
        return "unavailable_network"
    if any(token in lowered for token in ("no such file or directory", "command not found", "is not recognized as an internal or external command")):
        return "unavailable_harness"
    if timed_out:
        return "timeout"
    return "completed" if exit_code == 0 else "harness_error"


def harness_command(harness: str, prompt: str, workspace: Path, run_dir: Path, condition: str, task_type: str) -> tuple[list[str], dict[str, str]]:
    env = isolated_environment(harness, run_dir)
    last_message = run_dir / "last-message.txt"
    writable = task_type == "creation"
    if harness == "codex":
        command = [
            "codex", "exec", "--skip-git-repo-check", "--ephemeral", "--ignore-user-config", "--ignore-rules",
            "--sandbox", "workspace-write" if writable else "read-only", "-C", str(workspace),
            "--output-last-message", str(last_message), prompt,
        ]
    elif harness == "claude":
        command = [
            "claude", "-p", prompt, "--no-session-persistence", "--output-format", "json", "--max-budget-usd", "2.00",
            "--permission-mode", "bypassPermissions" if writable else "plan",
        ]
        if condition == "community":
            command.extend(["--plugin-dir", str(ROOT), "--tools", "default"])
        else:
            command.append("--disable-slash-commands")
    elif harness == "gemini":
        command = [
            "gemini", "-p", prompt, "--skip-trust", "--output-format", "json",
            "--approval-mode", "yolo" if writable else "plan",
        ]
    elif harness == "kimi":
        command = ["kimi", "-p", prompt, "--output-format", "text"]
        if writable:
            command.append("--yolo")
        if condition == "community":
            command.extend(["--skills-dir", str(ROOT / "skills")])
    else:
        raise ValueError(harness)
    return command, env


def routing_prompt(case: dict[str, Any], condition: str) -> str:
    prefix = "Use the installed godot-gamestudio skill in plan mode. " if condition == "community" else "Plan this Godot request without using any installed Godot Gamestudio skill. "
    return (
        prefix
        + f"Request: {case['prompt']}\n"
        + "Do not edit files or run tools. Return only one JSON object with arrays named makers, reviewers, coordinators and a string named qa. Use exact role IDs when roles are needed."
    )


def creation_prompt(case: dict[str, Any], condition: str) -> str:
    prefix = "Use the installed godot-gamestudio skill in quick mode, including an independent review and QA pass. " if condition == "community" else "Complete this Godot task directly without using Godot Gamestudio roles or skills. "
    return prefix + case["prompt"] + " Work only inside the current project directory. Run every Godot command through the executable in the GODOT_BIN environment variable; it is guarded against hangs."


def grade_routing(case: dict[str, Any], response: str) -> dict[str, Any]:
    value = extract_json(response)
    if not value:
        return {"status": "fail", "reason": "No JSON response"}
    checks = []
    for field, expected_key in (("makers", "expected_makers"), ("reviewers", "expected_reviewers"), ("coordinators", "expected_coordinators")):
        expected = set(case.get(expected_key, []))
        actual = set(value.get(field, [])) if isinstance(value.get(field), list) else set()
        checks.append({"id": field, "passed": expected <= actual, "expected": sorted(expected), "actual": sorted(actual)})
    qa_passed = value.get("qa") == "godot-qa-playtester"
    checks.append({"id": "qa", "passed": qa_passed, "actual": value.get("qa")})
    return {"status": "pass" if all(item["passed"] for item in checks) else "fail", "checks": checks, "parsed": value}


def grade_creation(workspace: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "grade_visual_fixture.py"), str(workspace)],
        capture_output=True, text=True, timeout=90,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "inconclusive", "reason": "grader failed", "stdout": result.stdout, "stderr": result.stderr}


def load_cases(suite: str) -> tuple[str, list[dict[str, Any]]]:
    if suite == "routing":
        path = ROOT / "evals" / "smoke" / "evals.json"
        task_type = "routing"
    else:
        path = ROOT / "evals" / "creation" / "evals.json"
        task_type = "creation"
    data = json.loads(path.read_text(encoding="utf-8"))
    return task_type, data["cases"]


def run_one(harness: str, condition: str, task_type: str, case: dict[str, Any], run_dir: Path, timeout: int) -> dict[str, Any]:
    workspace = run_dir / "workspace"
    if task_type == "creation":
        shutil.copytree(ROOT / case["fixture"], workspace)
    else:
        workspace.mkdir(parents=True)
        (workspace / "project.godot").write_text('[application]\nconfig/name="Routing benchmark"\n', encoding="utf-8")
    if condition == "community" and harness in {"codex", "gemini"}:
        install_skills(workspace)
    prompt = routing_prompt(case, condition) if task_type == "routing" else creation_prompt(case, condition)
    command, env = harness_command(harness, prompt, workspace, run_dir, condition, task_type)
    if task_type == "creation":
        install_godot_guard(run_dir, env)
    started = time.monotonic()
    timed_out = False
    try:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout)
        exit_code = process.returncode
    except FileNotFoundError as error:
        exit_code = None
        stdout = ""
        stderr = str(error)
    except subprocess.TimeoutExpired as error:
        timed_out = True
        exit_code = None
        try:
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
    finally:
        shutil.rmtree(run_dir / "home", ignore_errors=True)
    duration = round(time.monotonic() - started, 3)
    (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    response = normalize_response(harness, stdout, run_dir / "last-message.txt")
    (run_dir / "response.txt").write_text(response, encoding="utf-8")
    classification = classify_failure(stdout + "\n" + stderr, exit_code, timed_out)
    if classification == "completed":
        grade = grade_routing(case, response) if task_type == "routing" else grade_creation(workspace)
    else:
        grade = {"status": "inconclusive", "reason": classification}
    result = {
        "harness": harness,
        "condition": condition,
        "task_type": task_type,
        "case": case["id"],
        "status": classification,
        "exit_code": exit_code,
        "duration_seconds": duration,
        "grade": grade,
        "workspace": str(workspace),
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("routing", "creation"), required=True)
    parser.add_argument("--harness", action="append", choices=SUPPORTED_HARNESSES, required=True)
    parser.add_argument("--condition", action="append", choices=SUPPORTED_CONDITIONS)
    parser.add_argument("--case", action="append", help="Run only selected case IDs")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output", default=str(ROOT / "evals" / "results"))
    args = parser.parse_args()
    task_type, cases = load_cases(args.suite)
    if args.case:
        cases = [case for case in cases if case["id"] in set(args.case)]
    if not cases:
        raise SystemExit("No benchmark cases selected")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S-%fZ")
    root = Path(args.output).resolve() / f"{args.suite}-{timestamp}-{os.getpid()}"
    conditions = args.condition or list(SUPPORTED_CONDITIONS)
    results = []
    for case in cases:
        for harness in args.harness:
            for condition in conditions:
                for repetition in range(1, args.repeat + 1):
                    run_dir = root / case["id"] / harness / condition / f"run-{repetition}"
                    run_dir.mkdir(parents=True, exist_ok=True)
                    result = run_one(harness, condition, task_type, case, run_dir, args.timeout)
                    results.append(result)
                    print(f"{case['id']} {harness} {condition}: {result['status']} / {result['grade']['status']}", flush=True)
    completed = [item for item in results if item["status"] == "completed"]
    passed = [item for item in completed if item["grade"]["status"] == "pass"]
    summary = {
        "schema_version": 1,
        "suite": args.suite,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runs": len(results),
        "completed": len(completed),
        "passed": len(passed),
        "pass_rate_completed": round(len(passed) / len(completed), 4) if completed else None,
        "results": results,
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(root / "summary.json")


if __name__ == "__main__":
    main()
