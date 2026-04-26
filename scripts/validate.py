#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///

"""Validate an Agent Skill directory against the spec at https://agentskills.io.

Checks frontmatter, naming, length limits, and the parent-directory rule.
Prints a JSON report to stdout. Exits 0 on clean, 1 on validation failure,
2 on malformed input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9]|-(?!-))*[a-z0-9]$|^[a-z0-9]$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
REQUIRED_FIELDS = {"name", "description"}


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("SKILL.md does not start with a YAML frontmatter block (--- … ---)")
    raw, body = match.group(1), match.group(2)
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a YAML mapping (key: value pairs)")
    return data, body


def validate(skill_dir: Path, strict: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    stats: dict[str, Any] = {}

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"Missing SKILL.md at {skill_md}")
        return {"errors": errors, "warnings": warnings, "stats": stats}

    text = skill_md.read_text(encoding="utf-8")
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as exc:
        errors.append(str(exc))
        return {"errors": errors, "warnings": warnings, "stats": stats}
    except yaml.YAMLError as exc:
        errors.append(f"Frontmatter is not valid YAML: {exc}")
        return {"errors": errors, "warnings": warnings, "stats": stats}

    unknown = set(fm) - ALLOWED_FIELDS
    if unknown:
        warnings.append(f"Unknown frontmatter fields: {sorted(unknown)}")
    missing = REQUIRED_FIELDS - set(fm)
    if missing:
        errors.append(f"Missing required frontmatter fields: {sorted(missing)}")

    name = fm.get("name")
    if name is not None:
        if not isinstance(name, str):
            errors.append("`name` must be a string")
        else:
            if not (1 <= len(name) <= 64):
                errors.append(f"`name` length {len(name)} not in 1..64")
            if not NAME_RE.match(name):
                errors.append(
                    "`name` must be lowercase a-z/0-9/hyphens, no leading/trailing/consecutive hyphens"
                )
            if name != skill_dir.name:
                errors.append(
                    f"`name` ({name!r}) must equal parent directory basename ({skill_dir.name!r})"
                )

    desc = fm.get("description")
    if desc is not None:
        if not isinstance(desc, str):
            errors.append("`description` must be a string")
        else:
            stripped = desc.strip()
            if not (1 <= len(stripped) <= 1024):
                errors.append(f"`description` length {len(stripped)} not in 1..1024")
            if not stripped:
                errors.append("`description` is empty")
            stats["description_chars"] = len(stripped)

    compat = fm.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            errors.append("`compatibility` must be a string")
        elif len(compat) > 500:
            errors.append(f"`compatibility` length {len(compat)} exceeds 500")

    metadata = fm.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("`metadata` must be a mapping")

    allowed_tools = fm.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        errors.append("`allowed-tools` must be a string (space-separated tool list)")

    body_lines = body.count("\n") + (1 if body and not body.endswith("\n") else 0)
    stats["body_lines"] = body_lines
    if body_lines >= 500:
        msg = f"SKILL.md body is {body_lines} lines (spec recommends <500)"
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)
    elif body_lines >= 400:
        warnings.append(f"SKILL.md body is {body_lines} lines (approaching the 500-line ceiling)")

    if not body.strip():
        warnings.append("SKILL.md body is empty")

    for link_target in LINK_RE.findall(body):
        if link_target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = (skill_dir / link_target.split("#", 1)[0]).resolve()
        try:
            target_path.relative_to(skill_dir.resolve())
        except ValueError:
            warnings.append(f"Link target escapes skill dir: {link_target}")
            continue
        if not target_path.exists():
            warnings.append(f"Link target does not exist: {link_target}")

    stats["dir"] = str(skill_dir)
    stats["name"] = name
    return {"errors": errors, "warnings": warnings, "stats": stats}


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("skill_dir", type=Path, help="Path to the skill directory (containing SKILL.md)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote line-count warning (>=500 lines) to an error",
    )
    args = parser.parse_args()

    skill_dir: Path = args.skill_dir
    if not skill_dir.is_dir():
        print(f"Not a directory: {skill_dir}", file=sys.stderr)
        return 2

    report = validate(skill_dir.resolve(), args.strict)
    print(json.dumps(report, indent=2))
    if report["errors"]:
        print(f"FAIL: {len(report['errors'])} error(s)", file=sys.stderr)
        return 1
    if report["warnings"]:
        print(f"OK with {len(report['warnings'])} warning(s)", file=sys.stderr)
    else:
        print("OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
