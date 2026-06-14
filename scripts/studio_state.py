#!/usr/bin/env python3
"""Manage resumable Godot Gamestudio milestones and acceptance gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from inspect_project import inspect
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


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_project_path(value: str) -> str:
    candidate = PurePosixPath(value.replace("\\", "/"))
    parts = tuple(part for part in candidate.parts if part not in {"", "."})
    if candidate.is_absolute() or not parts or ".." in parts:
        raise SystemExit(f"Path must be project-relative without '..': {value}")
    normalized = PurePosixPath(*parts)
    if normalized.parts[0] == STATE_DIR:
        raise SystemExit(f"Deliverables and evidence cannot own studio state: {value}")
    return normalized.as_posix()


def upgrade_state(state: dict[str, Any]) -> dict[str, Any]:
    version = state.get("schema_version", 1)
    if version > 2:
        raise SystemExit(f"Unsupported studio state schema: {version}")
    if version == 2:
        return state
    milestone = state.get("current_milestone")
    if milestone:
        for deliverable in milestone.get("deliverables", []):
            deliverable.setdefault("artifact_revision", 1 if deliverable.get("status") == "completed" else 0)
            for review in milestone.get("reviews", {}).get(deliverable.get("id"), []):
                review.setdefault("artifact_revision", deliverable["artifact_revision"])
        for records in milestone.get("evidence", {}).values():
            for record in records:
                record.setdefault("actor", "legacy-unverified")
        milestone["blockers"] = [
            blocker if isinstance(blocker, dict) else {
                "id": f"b{index}",
                "reason": blocker,
                "status": "open",
                "recorded_at": milestone.get("started_at", now()),
            }
            for index, blocker in enumerate(milestone.get("blockers", []), start=1)
        ]
    state["schema_version"] = 2
    state["migrated_from_schema"] = version
    return state


def load(project: Path) -> dict[str, Any]:
    path = state_path(project)
    if not path.is_file():
        raise SystemExit(f"Missing {path}; run the init command first")
    state = upgrade_state(json.loads(path.read_text(encoding="utf-8")))
    state["project"]["root"] = str(project)
    state["project"]["project_file"] = str(project / "project.godot")
    return state


def save(project: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now()
    write_json(state_path(project), state)


def init_state(project: Path) -> dict[str, Any]:
    project_text = (project / "project.godot").read_text(encoding="utf-8", errors="replace")
    feature_match = re.search(r'config/features\s*=\s*PackedStringArray\(([^\n]+)\)', project_text)
    features = re.findall(r'"([^"]+)"', feature_match.group(1)) if feature_match else []
    return {
        "schema_version": 2,
        "project": {
            "root": str(project),
            "project_file": str(project / "project.godot"),
            "godot_features": features,
            "inspection": inspect(project),
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


def open_blockers(milestone: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in milestone.get("blockers", []) if item.get("status", "open") == "open"]


def add_blocker(milestone: dict[str, Any], reason: str) -> dict[str, Any]:
    blocker = {
        "id": f"b{len(milestone.get('blockers', [])) + 1}",
        "reason": reason,
        "status": "open",
        "recorded_at": now(),
    }
    milestone.setdefault("blockers", []).append(blocker)
    return blocker


def gate_failures(state: dict[str, Any]) -> list[str]:
    milestone = current(state)
    failures: list[str] = []
    if open_blockers(milestone):
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
        elif reviews[-1].get("artifact_revision") != deliverable.get("artifact_revision"):
            failures.append(f"deliverable {deliverable['id']} changed after its final review")
    final_review_times = [
        parse_time(reviews[-1]["recorded_at"])
        for reviews in milestone.get("reviews", {}).values()
        if reviews and reviews[-1].get("verdict") == "approved"
    ]
    latest_review_time = max(final_review_times) if final_review_times else None
    expected_qa = milestone.get("team", {}).get("qa", "godot-qa-playtester")
    project = Path(state["project"]["root"])
    for criterion in milestone.get("acceptance_criteria", []):
        if not criterion.get("required", True):
            continue
        evidence = milestone.get("evidence", {}).get(criterion["id"], [])
        if not evidence:
            failures.append(f"criterion {criterion['id']} has no evidence")
            continue
        latest = evidence[-1]
        if latest.get("verdict") != "pass":
            failures.append(f"criterion {criterion['id']} latest evidence is {latest.get('verdict')}")
        if latest.get("actor") != expected_qa:
            failures.append(f"criterion {criterion['id']} evidence was not recorded by {expected_qa}")
        if latest_review_time and parse_time(latest["recorded_at"]) < latest_review_time:
            failures.append(f"criterion {criterion['id']} evidence predates the final review")
        relative = latest.get("path")
        try:
            normalized = normalize_project_path(relative) if relative else None
        except SystemExit:
            normalized = None
            failures.append(f"criterion {criterion['id']} evidence path is unsafe")
        artifact = project / normalized if normalized else None
        if not artifact or not artifact.is_file():
            failures.append(f"criterion {criterion['id']} evidence artifact is missing")
        elif (
            latest.get("sha256") != file_digest(artifact)
            or latest.get("modified_ns") != artifact.stat().st_mtime_ns
        ):
            failures.append(f"criterion {criterion['id']} evidence artifact changed after recording")
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
    team = select_team(
        args.request,
        state["policy"]["max_active_specialists"],
        max_makers=1 if args.mode == "quick" else None,
    )
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
    assignments = {item["maker"]: item["reviewer"] for item in milestone["team"]["assignments"]}
    if args.owner not in assignments:
        raise SystemExit(f"Owner {args.owner} is not a selected maker for this milestone")
    if assignments[args.owner] != args.reviewer:
        raise SystemExit(f"Expected reviewer {assignments[args.owner]} for maker {args.owner}")
    normalized_paths = [normalize_project_path(value) for value in args.path]
    incoming = [PurePosixPath(value) for value in normalized_paths]
    for existing in milestone["deliverables"]:
        for existing_path in map(PurePosixPath, existing.get("paths", [])):
            for incoming_path in incoming:
                if existing_path == incoming_path or existing_path in incoming_path.parents or incoming_path in existing_path.parents:
                    raise SystemExit(
                        f"Path ownership conflict: {incoming_path} overlaps {existing_path} owned by {existing['id']}"
                    )
    milestone["deliverables"].append({
        "id": args.id,
        "owner": args.owner,
        "reviewer": args.reviewer,
        "brief": args.brief or milestone["request"],
        "paths": normalized_paths,
        "status": "pending",
        "artifact_revision": 0,
    })
    save(project, state)


def command_constraint(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    state["constraints"][args.key] = args.value
    save(project, state)


def command_inspect(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    state["project"]["inspection"] = inspect(project)
    save(project, state)
    print(json.dumps(state["project"]["inspection"], indent=2))


def command_complete_deliverable(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    item = find_deliverable(current(state), args.id)
    item["status"] = "completed"
    item["artifact_revision"] = item.get("artifact_revision", 0) + 1
    item["completed_at"] = now()
    save(project, state)


def command_review(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    item = find_deliverable(milestone, args.deliverable)
    if args.reviewer != item["reviewer"]:
        raise SystemExit(f"Expected reviewer {item['reviewer']} for {args.deliverable}")
    if item.get("status") != "completed":
        raise SystemExit(f"Deliverable {args.deliverable} must be completed before review")
    milestone["reviews"].setdefault(args.deliverable, []).append({
        "reviewer": args.reviewer,
        "verdict": args.verdict,
        "summary": args.summary,
        "artifact_revision": item.get("artifact_revision", 0),
        "recorded_at": now(),
    })
    if args.verdict == "changes_requested":
        item["status"] = "needs_revision"
        milestone["status"] = "needs_revision"
    save(project, state)


def command_evidence(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    valid_ids = {criterion["id"] for criterion in milestone["acceptance_criteria"]}
    if args.criterion not in valid_ids:
        raise SystemExit(f"Unknown criterion: {args.criterion}")
    expected_qa = milestone["team"]["qa"]
    if args.actor != expected_qa:
        raise SystemExit(f"Final evidence must be recorded by {expected_qa}")
    relative = normalize_project_path(args.path)
    artifact = project / relative
    if not artifact.is_file():
        raise SystemExit(f"Evidence artifact does not exist: {artifact}")
    if datetime.fromtimestamp(artifact.stat().st_mtime, timezone.utc) < parse_time(milestone["started_at"]):
        raise SystemExit(f"Evidence artifact predates the milestone: {artifact}")
    milestone["evidence"].setdefault(args.criterion, []).append({
        "actor": args.actor,
        "kind": args.kind,
        "path": relative,
        "sha256": file_digest(artifact),
        "size": artifact.stat().st_size,
        "modified_ns": artifact.stat().st_mtime_ns,
        "verdict": args.verdict,
        "summary": args.summary,
        "recorded_at": now(),
    })
    save(project, state)


def command_revision(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    if args.deliverable:
        item = find_deliverable(milestone, args.deliverable)
        item["status"] = "in_progress"
    milestone["revision_round"] += 1
    maximum = state["policy"]["max_revision_rounds"]
    if milestone["revision_round"] > maximum:
        milestone["status"] = "blocked"
        add_blocker(milestone, f"revision limit exceeded: {maximum}")
    else:
        milestone["status"] = "in_progress"
    save(project, state)


def command_brief(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    payload: dict[str, Any] = {
        "milestone": {key: milestone[key] for key in ("id", "title", "request", "mode")},
        "constraints": state.get("constraints", {}),
        "acceptance_criteria": milestone.get("acceptance_criteria", []),
    }
    if args.phase in {"maker", "reviewer"}:
        if not args.deliverable:
            raise SystemExit("--deliverable is required for maker and reviewer briefs")
        item = find_deliverable(milestone, args.deliverable)
        payload["role"] = item["owner"] if args.phase == "maker" else item["reviewer"]
        payload["deliverable"] = {
            key: item[key]
            for key in ("id", "brief", "paths", "status", "artifact_revision")
        }
        if args.phase == "reviewer":
            payload["instruction"] = "Review independently. Do not edit files or use maker reasoning."
    else:
        payload["role"] = milestone["team"]["qa"]
        payload["instruction"] = "Verify independently after final reviews. Do not implement the feature."
        payload["deliverables"] = milestone.get("deliverables", [])
        payload["reviews"] = milestone.get("reviews", {})
    print(json.dumps(payload, indent=2))


def command_block(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    add_blocker(milestone, args.reason)
    milestone["status"] = "blocked"
    save(project, state)


def command_resolve_blocker(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    blocker = next((item for item in milestone.get("blockers", []) if item.get("id") == args.id), None)
    if not blocker:
        raise SystemExit(f"Unknown blocker: {args.id}")
    if blocker.get("status") == "resolved":
        raise SystemExit(f"Blocker is already resolved: {args.id}")
    blocker["status"] = "resolved"
    blocker["resolution"] = args.resolution
    blocker["resolved_at"] = now()
    if not open_blockers(milestone):
        milestone["status"] = "in_progress"
    save(project, state)


def command_assess(args: argparse.Namespace) -> None:
    project = find_project_root(args.project)
    state = load(project)
    milestone = current(state)
    failures = gate_failures(state)
    if not failures:
        milestone["status"] = "passed"
        milestone["completed_at"] = now()
    elif open_blockers(milestone) or milestone["revision_round"] >= state["policy"]["max_revision_rounds"]:
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
    add.add_argument("--brief")
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

    inspect_command = commands.add_parser("inspect")
    inspect_command.add_argument("project")
    inspect_command.set_defaults(func=command_inspect)

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
    evidence.add_argument("--actor", required=True)
    evidence.add_argument("--kind", required=True)
    evidence.add_argument("--path", required=True)
    evidence.add_argument("--verdict", choices=("pass", "fail", "inconclusive"), required=True)
    evidence.add_argument("--summary", required=True)
    evidence.set_defaults(func=command_evidence)

    revision = commands.add_parser("revision")
    revision.add_argument("project")
    revision.add_argument("--deliverable")
    revision.set_defaults(func=command_revision)

    brief = commands.add_parser("brief")
    brief.add_argument("project")
    brief.add_argument("--phase", choices=("maker", "reviewer", "qa"), required=True)
    brief.add_argument("--deliverable")
    brief.set_defaults(func=command_brief)

    block = commands.add_parser("block")
    block.add_argument("project")
    block.add_argument("--reason", required=True)
    block.set_defaults(func=command_block)

    resolve = commands.add_parser("resolve-blocker")
    resolve.add_argument("project")
    resolve.add_argument("--id", required=True)
    resolve.add_argument("--resolution", required=True)
    resolve.set_defaults(func=command_resolve_blocker)

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
