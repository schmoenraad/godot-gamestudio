#!/usr/bin/env python3
"""Select the smallest useful Godot Gamestudio team for a request."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Role:
    skill: str
    reviewer: str
    patterns: tuple[str, ...]
    creative: bool = False
    animation_reviewer: str | None = None


ROLE_FILE = Path(__file__).resolve().parent.parent / "roles" / "roles.json"


def load_roles() -> tuple[Role, ...]:
    data = json.loads(ROLE_FILE.read_text(encoding="utf-8"))
    return tuple(
        Role(
            skill=item["id"],
            reviewer=item["reviewer"],
            patterns=tuple(item["patterns"]),
            creative=item.get("creative", False),
            animation_reviewer=item.get("animation_reviewer"),
        )
        for item in data["roles"]
        if item.get("kind") == "maker"
    )


ROLES = load_roles()


def select_team(request: str, max_specialists: int = 4, max_makers: int | None = None) -> dict:
    text = request.lower()
    scored: list[tuple[int, int, Role]] = []
    for index, role in enumerate(ROLES):
        score = sum(1 for pattern in role.patterns if re.search(pattern, text))
        if score:
            scored.append((-score, index, role))

    scored.sort()
    makers = [entry[2] for entry in scored]
    if not makers:
        makers = [next(role for role in ROLES if role.skill == "godot-gameplay-engineer")]
    if max_makers is not None:
        makers = makers[:max_makers]

    animation_requested = bool(re.search(r"animat|frame|sprite sheet|spritesheet", text))
    assignments = []
    for role in makers:
        reviewer = role.reviewer
        if role.animation_reviewer and animation_requested:
            reviewer = role.animation_reviewer
        assignments.append({"maker": role.skill, "reviewer": reviewer})

    domains = {item["maker"] for item in assignments}
    creative_domains = {role.skill for role in ROLES if role.creative}
    coordinators = ["godot-gamestudio"]
    if len(domains & creative_domains) >= 2:
        coordinators.append("godot-creative-director")

    maker_names = [item["maker"] for item in assignments]
    reviewer_names = list(dict.fromkeys(item["reviewer"] for item in assignments))
    waves = []
    for phase, names in (("makers", maker_names), ("reviewers", reviewer_names)):
        for index in range(0, len(names), max_specialists):
            waves.append({"phase": phase, "agents": names[index:index + max_specialists]})
    waves.append({"phase": "qa", "agents": ["godot-qa-playtester"]})

    return {
        "request": request,
        "max_active_specialists": max_specialists,
        "coordinators": coordinators,
        "assignments": assignments,
        "qa": "godot-qa-playtester",
        "execution_waves": waves,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--max-specialists", type=int, default=4)
    args = parser.parse_args()
    if not 2 <= args.max_specialists <= 8:
        parser.error("--max-specialists must be between 2 and 8")
    print(json.dumps(select_team(args.request, args.max_specialists), indent=2))


if __name__ == "__main__":
    main()
