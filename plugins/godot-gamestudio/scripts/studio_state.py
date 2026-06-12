#!/usr/bin/env python3
"""Manage resumable Godot Gamestudio milestones and acceptance gates."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from select_team import select_team


STATE_DIR = ".godot-gamestudio"
STATE_FILE = "studio.json"
VALID_MODES = {"build", "plan", "review", "quick"}
VALID_STATUSES = {"planned", "in_progress", "needs_revision", "blocked", "passed"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_project_root(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_file() and path.name == "project.godot":
        return path.parent
    if (path / "project.godot").is_file():
        return path
    matches = sorted(path.rglob("project.godot")) if path.is_dir() else []
    if len(matches) == 1:
        return matches[0].parent
    if not matches:
        raise SystemExit(f"No project.godot found under {path}")
    raise SystemExit(f"Multiple Godot projects found under {path}; pass the intended project root")


def state_path(project: Path) -> Path:
    return project / STATE_DIR / STATE_FILE


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def load(project: Path) -> dict[str, Any]:
    path = state_path(project)
    if not path.is_file():
        raise SystemExit(f"Missing {path}; run the init command first")
    return json.loads(path.read_text(encoding="utf-8"))


def save(project: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now()
    write_json(state_path(project), state)


def init_state(project: Path) -> dict[str, Any]:
    project_text = (project / "project.godot").read_text(encoding="utf-8", errors="replace")
    feature_match = re.search(r'config/features\s*=\s*PackedStringArray\(([^\n]+)\)', project_text)
    features = re.findall(r'"([^"]+)"', feature_match.group(1)) if feature_match else []
    return {
        "schema_version": 1,
        "project": {
            "root": str(project),
            "project_file": str(project / "project.godot"),
            "godot_features": features,
        },
        "constraints": {},
        "policy": {"max_active_specialists": 4, "max_revision_rounds": 2},
        "current_milestone": None,
        "history": [],
        "created_at": now(),
        "updated_at": now(),
    }


def current(state: dict[str, Any]) -> dict[str, Any]:
    milestone = state.get("current_milestone")
    if not milestone:
        raise SystemExit("No active milestone")
    return milestone


def gate_failures(state: dict[str, Any]) -> list[str]:
    milestone = current(state)
    failures: list[str] = []
    if milestone.get("blockers"):
        failures.append("unresolved blockers remain")
    if not milestone.get("acceptance_criteria"):
        failures.append("no acceptance criteria defined")
    if not milestone.get("deliverables") and milestone.get("mode") in {"build", "quick"}:
        failures.append("no deliverables registered")
    for deliverable in milestone.get("deliverables", []):
        if deliverable.get("status") != "completed":
            failures.append(f"deliverable {deliverable['id']} is not completed")
        reviews = milestone.get("reviews", {}).get(deliverable["id"], [])
        if not reviews or reviews[-1].get("verdict") != "approved":
            failures.append(f"deliverable {deliverable['id']} lacks an approved final review")
    for criterion in milestone.get("acceptance_criteria", []):
        if not criterion.get("required", True):
            continue
        evidence = milestone.get("evidence", {}).get(criterion["id"], [])
        if not evidence:
            failures.append(f"criterion {criterion['id']} has no evidence")
        elif evidence[-1].get("verdict") != "pass":
            failures.append(f"criterion {criterion['id']} latest evidence is {evidence[-1].get('verdict')}")
    return failures


def command_init(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    path = state_path(project)
    if path.exists() and not args.force:
        raise SystemExit(f"State already exists at {path}; pass --force to replace it")
    write_json(path, init_state(project))
    print(path)


def command_start(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    existing = state.get("current_milestone")
    if existing and existing.get("status") not in {"passed", "blocked"} and not args.force:
        raise SystemExit("An unfinished milestone exists; finish it or pass --force")
    if existing:
        state["history"].append(existing)
    if args.mode not in VALID_MODES:
        raise SystemExit(f"Invalid mode: {args.mode}")
    team = select_team(args.request, state["policy"]["max_active_specialists"])
    criteria = [
        {"id": f"c{index}", "text": text, "required": True}
        for index, text in enumerate(args.criterion, start=1)
    ]
    state["current_milestone"] = {
        "id": datetime.now(timezone.utc).strftime("milestone-%Y%m%d-%H%M%S"),
        "title": args.title,
        "request": args.request,
        "mode": args.mode,
        "status": "planned" if args.mode == "plan" else "in_progress",
        "team": team,
        "acceptance_criteria": criteria,
        "deliverables": [],
        "reviews": {},
        "evidence": {},
        "revision_round": 0,
        "blockers": [],
        "started_at": now(),
    }
    save(project, state)
    print(json.dumps(state["current_milestone"], indent=2))


def find_deliverable(milestone: dict[str, Any], deliverable_id: str) -> dict[str, Any]:
    for item in milestone.get("deliverables", []):
        if item.get("id") == deliverable_id:
            return item
    raise SystemExit(f"Unknown deliverable: {deliverable_id}")


def command_add_deliverable(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    if any(item.get("id") == args.id for item in milestone["deliverables"]):
        raise SystemExit(f"Deliverable already exists: {args.id}")
    incoming = [Path(value) for value in args.path]
    for existing in milestone["deliverables"]:
        for existing_path in map(Path, existing.get("paths", [])):
            for incoming_path in incoming:
                if existing_path == incoming_path or existing_path in incoming_path.parents or incoming_path in existing_path.parents:
                    raise SystemExit(
                        f"Path ownership conflict: {incoming_path} overlaps {existing_path} owned by {existing['id']}"
                    )
    milestone["deliverables"].append({
        "id": args.id,
        "owner": args.owner,
        "reviewer": args.reviewer,
        "paths": args.path,
        "status": "pending",
    })
    save(project, state)


def command_constraint(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    state["constraints"][args.key] = args.value
    save(project, state)


def command_complete_deliverable(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    item = find_deliverable(current(state), args.id)
    item["status"] = "completed"
    item["completed_at"] = now()
    save(project, state)


def command_review(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    item = find_deliverable(milestone, args.deliverable)
    if args.reviewer != item["reviewer"]:
        raise SystemExit(f"Expected reviewer {item['reviewer']} for {args.deliverable}")
    milestone["reviews"].setdefault(args.deliverable, []).append({
        "reviewer": args.reviewer,
        "verdict": args.verdict,
        "summary": args.summary,
        "recorded_at": now(),
    })
    if args.verdict == "changes_requested":
        milestone["status"] = "needs_revision"
    save(project, state)


def command_evidence(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    valid_ids = {criterion["id"] for criterion in milestone["acceptance_criteria"]}
    if args.criterion not in valid_ids:
        raise SystemExit(f"Unknown criterion: {args.criterion}")
    milestone["evidence"].setdefault(args.criterion, []).append({
        "kind": args.kind,
        "path": args.path,
        "verdict": args.verdict,
        "summary": args.summary,
        "recorded_at": now(),
    })
    save(project, state)


def command_revision(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    milestone["revision_round"] += 1
    maximum = state["policy"]["max_revision_rounds"]
    if milestone["revision_round"] > maximum:
        milestone["status"] = "blocked"
        milestone["blockers"].append(f"revision limit exceeded: {maximum}")
    else:
        milestone["status"] = "in_progress"
    save(project, state)


def command_block(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    milestone["blockers"].append(args.reason)
    milestone["status"] = "blocked"
    save(project, state)


def command_assess(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    failures = gate_failures(state)
    if not failures:
        milestone["status"] = "passed"
        milestone["completed_at"] = now()
    elif milestone.get("blockers") or milestone["revision_round"] >= state["policy"]["max_revision_rounds"]:
        milestone["status"] = "blocked"
    else:
        milestone["status"] = "needs_revision"
    save(project, state)
    print(json.dumps({"status": milestone["status"], "failures": failures}, indent=2))


def command_status(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = state.get("current_milestone")
    result = {
        "project": state["project"],
        "policy": state["policy"],
        "milestone": milestone,
        "gate_failures": gate_failures(state) if milestone else [],
    }
    print(json.dumps(result, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("project")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=command_init)

    start = commands.add_parser("start")
    start.add_argument("project")
    start.add_argument("--title", required=True)
    start.add_argument("--request", required=True)
    start.add_argument("--mode", choices=sorted(VALID_MODES), default="build")
    start.add_argument("--criterion", action="append", required=True)
    start.add_argument("--force", action="store_true")
    start.set_defaults(func=command_start)

    add = commands.add_parser("add-deliverable")
    add.add_argument("project")
    add.add_argument("--id", required=True)
    add.add_argument("--owner", required=True)
    add.add_argument("--reviewer", required=True)
    add.add_argument("--path", action="append", required=True)
    add.set_defaults(func=command_add_deliverable)

    complete = commands.add_parser("complete-deliverable")
    complete.add_argument("project")
    complete.add_argument("--id", required=True)
    complete.set_defaults(func=command_complete_deliverable)

    constraint = commands.add_parser("set-constraint")
    constraint.add_argument("project")
    constraint.add_argument("--key", required=True)
    constraint.add_argument("--value", required=True)
    constraint.set_defaults(func=command_constraint)

    review = commands.add_parser("review")
    review.add_argument("project")
    review.add_argument("--deliverable", required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--verdict", choices=("approved", "changes_requested", "inconclusive"), required=True)
    review.add_argument("--summary", required=True)
    review.set_defaults(func=command_review)

    evidence = commands.add_parser("evidence")
    evidence.add_argument("project")
    evidence.add_argument("--criterion", required=True)
    evidence.add_argument("--kind", required=True)
    evidence.add_argument("--path", required=True)
    evidence.add_argument("--verdict", choices=("pass", "fail", "inconclusive"), required=True)
    evidence.add_argument("--summary", required=True)
    evidence.set_defaults(func=command_evidence)

    revision = commands.add_parser("revision")
    revision.add_argument("project")
    revision.set_defaults(func=command_revision)

    block = commands.add_parser("block")
    block.add_argument("project")
    block.add_argument("--reason", required=True)
    block.set_defaults(func=command_block)

    assess = commands.add_parser("assess")
    assess.add_argument("project")
    assess.set_defaults(func=command_assess)

    status = commands.add_parser("status")
    status.add_argument("project")
    status.set_defaults(func=command_status)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
