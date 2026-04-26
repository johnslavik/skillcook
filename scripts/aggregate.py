#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Aggregate eval results into benchmark.json.

Walks <workspace>/iteration-N/eval-*/{with_skill*,without_skill*}/, reads
grading.json and timing.json, and writes <workspace>/iteration-N/benchmark.json
matching the schema in https://agentskills.io/skill-creation/evaluating-skills.

Mean / stddev are computed across all (eval, run) tuples per configuration.
A configuration with no grading.json files is reported with NaN means and a
warning on stderr.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


def stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "stddev": None}
    n = len(values)
    mean = sum(values) / n
    if n == 1:
        return {"mean": mean, "stddev": 0.0}
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return {"mean": mean, "stddev": math.sqrt(variance)}


def collect(iter_dir: Path, kind: str) -> dict[str, list[float]]:
    """kind is the dir-name prefix: 'with_skill' or 'without_skill'."""
    result = {"pass_rate": [], "time_seconds": [], "tokens": []}
    for eval_dir in sorted(iter_dir.glob("eval-*")):
        for run_dir in sorted(eval_dir.glob(f"{kind}*")):
            if not run_dir.is_dir():
                continue
            grading = run_dir / "grading.json"
            timing = run_dir / "timing.json"
            if grading.is_file():
                try:
                    g = json.loads(grading.read_text(encoding="utf-8"))
                    pr = g.get("summary", {}).get("pass_rate")
                    if isinstance(pr, (int, float)):
                        result["pass_rate"].append(float(pr))
                except (OSError, json.JSONDecodeError) as exc:
                    print(f"warn: bad grading.json at {grading}: {exc}", file=sys.stderr)
            else:
                print(f"warn: missing grading.json at {grading}", file=sys.stderr)
            if timing.is_file():
                try:
                    t = json.loads(timing.read_text(encoding="utf-8"))
                    if isinstance(t.get("duration_ms"), int):
                        result["time_seconds"].append(t["duration_ms"] / 1000.0)
                    if isinstance(t.get("total_tokens"), int):
                        result["tokens"].append(float(t["total_tokens"]))
                except (OSError, json.JSONDecodeError) as exc:
                    print(f"warn: bad timing.json at {timing}: {exc}", file=sys.stderr)
    return result


def summarize(samples: dict[str, list[float]]) -> dict[str, dict[str, float | None]]:
    return {key: stats(values) for key, values in samples.items()}


def delta(with_: dict[str, list[float]], without: dict[str, list[float]]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for key in ("pass_rate", "time_seconds", "tokens"):
        a = stats(with_[key])["mean"]
        b = stats(without[key])["mean"]
        if a is None or b is None:
            out[key] = None
        else:
            out[key] = a - b
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="aggregate.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--iteration", type=int, default=1)
    args = parser.parse_args()

    iter_dir: Path = args.workspace / f"iteration-{args.iteration}"
    if not iter_dir.is_dir():
        print(f"Not a directory: {iter_dir}", file=sys.stderr)
        return 2

    with_samples = collect(iter_dir, "with_skill")
    without_samples = collect(iter_dir, "without_skill")

    benchmark = {
        "run_summary": {
            "with_skill": summarize(with_samples),
            "without_skill": summarize(without_samples),
            "delta": delta(with_samples, without_samples),
        }
    }

    out_path = iter_dir / "benchmark.json"
    out_path.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    print(json.dumps(benchmark, indent=2))
    print(f"wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
