# SCRIPTS

Designing scripts that agents can use. Scripts are how a skill bundles reusable logic that would otherwise be reinvented on every run — a chart builder, a parser, a validator, a scaffolder.

## Hard rules

These are not preferences. Violate them and the script breaks the agent loop.

### No interactive prompts

Agents run in non-TTY shells. A script that blocks on input hangs the whole run.

```
# Hangs forever — agent has no way to respond
$ python scripts/deploy.py
Target environment: _
```

Replace with explicit flags + a clear error:

```
$ python scripts/deploy.py
Error: --env is required. Options: development, staging, production.
Usage: python scripts/deploy.py --env staging --tag v1.2.3
```

Accept all input via flags, env vars, or stdin. Never `input()`, never `read -p`, never password prompts.

### Always implement `--help`

`--help` is the agent's primary way to learn the interface. Keep it concise — it lands in the agent's context window.

```
Usage: scripts/process.py [OPTIONS] INPUT_FILE

Process input data and produce a summary report.

Options:
  --format FORMAT   Output format: json, csv, table (default: json)
  --output FILE     Write output to FILE instead of stdout
  --verbose         Print progress to stderr

Examples:
  scripts/process.py data.csv
  scripts/process.py --format csv --output report.csv data.csv
```

### Structured output

Prefer JSON / CSV / TSV over free-form text. Both the agent and standard tools (`jq`, `cut`, `awk`) can consume structured output.

```
# Bad: whitespace-aligned, hard to parse
NAME          STATUS    CREATED
my-service    running   2025-01-15

# Good: unambiguous boundaries
{"name": "my-service", "status": "running", "created": "2025-01-15"}
```

### Separate data from diagnostics

stdout = the structured result. stderr = progress, warnings, debug info. This lets the agent capture clean output and still see diagnostics when needed.

### Helpful error messages

When the agent gets an error, the message shapes its next attempt directly. Opaque messages waste a turn.

```
# Bad
Error: invalid input.

# Good
Error: --format must be one of: json, csv, table.
       Received: "xml"
```

State what was wrong, what was expected, what to try. Quote the offending value.

## Strong preferences

### Idempotency

Agents may retry. "Create if not exists" is safer than "create and fail on duplicate". For destructive ops, accept a `--force` flag with a clear default of "fail rather than overwrite".

### Dry-run support

For destructive or stateful operations, a `--dry-run` flag lets the agent preview the effect without commitment.

### Closed-set inputs

Reject ambiguous input with a clear error rather than guessing. Use enums where possible.

### Meaningful exit codes

Distinct codes for distinct failure types (not-found, invalid args, auth failure). Document them in `--help`.

### Predictable output size

Agent harnesses commonly truncate tool output beyond ~10-30K chars. If your script may produce more, default to a summary or a limit, with `--offset`/`--limit` flags for paging, or require an `--output` flag for large results so stdout-flooding is opt-in.

## Implementation: Python via uv

Inline PEP 723 dependencies make scripts self-contained — no separate manifest, no install step.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///

"""Validate a SKILL.md against the Agent Skills spec."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="…")
    # …
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Run with `uv run scripts/script.py …`. The shebang lets it also be executed directly if marked +x.

## Implementation: Bash

Use bash for scaffolding, file shuffling, simple orchestration. Keep it short — anything past 50 lines belongs in Python.

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/new-skill.sh <parent-dir> <skill-name>

Scaffold a new Agent Skill directory.
EOF
}

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 2
fi

# …
```

Always `set -euo pipefail`. Always `usage()` to stderr on bad args. Quote variable expansions.

## Designing for the agent loop

The agent reads stdout/stderr to decide what to do next. Design the script to make that decision easy:

- A successful run prints the structured result and nothing else to stdout.
- A failure prints a diagnostic to stderr that names the variable / arg / file at fault.
- Exit codes match the failure category.
- Help text covers the "I have no idea how to call this" case in one short page.

If you find the agent regularly retrying or asking for help interpreting your output, tighten the error messages or add a `--quiet` / `--verbose` flag pair.

## When to write a script vs. inline a command

One-off command in `SKILL.md`:
- Existing tool already does the job (e.g. `uvx ruff@0.8.0 check .`).
- Pinning a version is enough for reproducibility.
- The invocation is short (a flag or two).

Bundle a script in `scripts/`:
- The logic is non-trivial or fragile to get right on the first try.
- Multiple steps need to be coordinated (e.g. parse → validate → emit).
- The agent would otherwise reinvent the same helper on every run.
- The output needs to be structured for a downstream step.

When iterating on a skill via evals (see `EVAL_LOOP.md`), watch for the agent reinventing the same helper across runs — that's the signal to script it.
