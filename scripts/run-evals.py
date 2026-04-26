#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Run an Agent Skill's eval set with and without the skill, capture timing.

For each eval in evals.json, spawns the configured runner twice:
  1. with the skill enabled (target dir under <workspace>/iteration-N/eval-<id>/with_skill/)
  2. with no skill (under .../without_skill/)

Captures stdout, stderr, exit code, wall time. Drops a `grading_prompt.md`
next to each pair so the grading step can be done by a separate LLM session.

The runner is a shell command that takes a prompt on stdin or as an argument
and writes its outputs to a directory you point it at via {OUT}. Default:
`claude -p {PROMPT} --output-dir {OUT}`. Override via --runner if your client
differs.

This script does NOT grade outputs (that requires content judgment) and does
NOT load the skill into the runner — it just sets up the file shape and
invokes the runner. The runner needs to know how to find the skill itself
(e.g. SKILL_DIRS env var, --skill flag, or a symlink); pass that wiring
through --runner-with-skill / --runner-without-skill if needed.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def load_evals(evals_path: Path) -> dict[str, Any]:
    data = json.loads(evals_path.read_text(encoding="utf-8"))
    if "evals" not in data or not isinstance(data["evals"], list):
        raise ValueError(f"{evals_path} missing top-level 'evals' list")
    return data


def run_one(
    runner: str,
    prompt: str,
    files: list[Path],
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = out_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    for f in files:
        if f.is_file():
            (outputs_dir / f.name).write_bytes(f.read_bytes())

    cmd = runner.replace("{PROMPT}", shlex.quote(prompt)).replace(
        "{OUT}", shlex.quote(str(outputs_dir))
    )

    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        (out_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (out_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        timing = {
            "duration_ms": duration_ms,
            "exit_code": result.returncode,
            "total_tokens": None,
        }
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        (out_dir / "stdout.txt").write_text(exc.stdout or "", encoding="utf-8")
        (out_dir / "stderr.txt").write_text(
            (exc.stderr or "") + "\n[TIMEOUT after 600s]", encoding="utf-8"
        )
        timing = {"duration_ms": duration_ms, "exit_code": -1, "total_tokens": None}

    (out_dir / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    return timing


def write_grading_prompt(eval_dir: Path, eval_case: dict[str, Any]) -> None:
    assertions = eval_case.get("assertions", [])
    bullet_list = "\n".join(f"- {a}" for a in assertions) or "- (no assertions defined)"
    text = f"""# Grading prompt — {eval_case.get('id')}

You are grading the output of an agent run. Read the contents of `outputs/`
and `stdout.txt`, then evaluate each assertion below as PASS or FAIL with
specific evidence (quote files, names, exact text). Produce a JSON object
matching this shape and write it to `grading.json` in the same directory:

```json
{{
  "assertion_results": [
    {{ "text": "...", "passed": true,  "evidence": "..." }}
  ],
  "summary": {{ "passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0 }}
}}
```

Original prompt the agent saw:

> {eval_case.get('prompt', '').strip()}

Expected output:

> {eval_case.get('expected_output', '').strip()}

Assertions to grade:

{bullet_list}

Rules:
- Concrete evidence required for PASS — a label without substance is FAIL.
- Don't grade with the benefit of the doubt.
- Compute pass_rate = passed / total.
"""
    (eval_dir / "grading_prompt.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="run-evals.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--skill", required=True, type=Path, help="Skill directory")
    parser.add_argument("--evals", required=True, type=Path, help="Path to evals.json")
    parser.add_argument(
        "--workspace", required=True, type=Path, help="Workspace dir for iteration outputs"
    )
    parser.add_argument("--iteration", type=int, default=1, help="Iteration number (default: 1)")
    parser.add_argument("--runs", type=int, default=1, help="Runs per (eval, configuration)")
    parser.add_argument(
        "--runner-with-skill",
        default=None,
        help='Runner command for the with-skill case. Use {PROMPT} and {OUT} placeholders. '
             'Default: "claude -p {PROMPT} --output-dir {OUT}"',
    )
    parser.add_argument(
        "--runner-without-skill",
        default=None,
        help='Runner command for the without-skill (baseline) case. '
             'Default: same as with-skill, with skill discovery disabled.',
    )
    parser.add_argument(
        "--runner",
        default="claude -p {PROMPT} --output-dir {OUT}",
        help="Default runner template (used as fallback for both configurations).",
    )
    args = parser.parse_args()

    if not args.skill.is_dir():
        print(f"--skill must be a directory: {args.skill}", file=sys.stderr)
        return 2
    if not args.evals.is_file():
        print(f"--evals must be a file: {args.evals}", file=sys.stderr)
        return 2

    runner_with = args.runner_with_skill or args.runner
    runner_without = args.runner_without_skill or args.runner

    data = load_evals(args.evals)
    evals_dir = args.evals.parent
    iter_dir = args.workspace / f"iteration-{args.iteration}"
    iter_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict[str, Any]] = []
    for case in data["evals"]:
        eval_id = str(case.get("id", "unknown"))
        eval_dir = iter_dir / f"eval-{eval_id}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        write_grading_prompt(eval_dir, case)

        files = [evals_dir / p if not Path(p).is_absolute() else Path(p) for p in case.get("files", [])]
        prompt = case.get("prompt", "")

        for run_idx in range(args.runs):
            run_label = "" if args.runs == 1 else f"-run{run_idx + 1}"
            print(f"[{eval_id}{run_label}] with_skill", file=sys.stderr)
            with_timing = run_one(
                runner_with, prompt, files, eval_dir / f"with_skill{run_label}"
            )
            print(f"[{eval_id}{run_label}] without_skill", file=sys.stderr)
            without_timing = run_one(
                runner_without, prompt, files, eval_dir / f"without_skill{run_label}"
            )
            summary.append(
                {
                    "eval_id": eval_id,
                    "run": run_idx + 1,
                    "with_skill": with_timing,
                    "without_skill": without_timing,
                }
            )

    print(json.dumps({"iteration": args.iteration, "runs": summary}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
