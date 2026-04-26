# EVAL_LOOP

How to evaluate a freshly-written skill against a baseline (no skill), aggregate the results, and decide whether the skill earns its tokens.

The pattern is from https://agentskills.io/skill-creation/evaluating-skills: run each test case once *with* the skill and once *without*, capture outputs and timing, grade against assertions, and compute a delta.

## Files involved

```
<skill-dir>/
└── evals/
    ├── evals.json
    └── files/                # input files referenced by evals
```

```
<workspace-dir>/
└── iteration-N/
    ├── eval-<id>/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json
    │   │   ├── grading.json    # produced by grading step
    │   │   └── grading_prompt.md
    │   └── without_skill/
    │       └── … same shape
    └── benchmark.json          # produced by aggregate.py
```

## `evals.json` schema

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": "top-months-chart",
      "prompt": "I have a CSV of monthly sales in data/sales_2025.csv. Find the top 3 months by revenue and make a bar chart.",
      "expected_output": "A bar chart image showing the top 3 months by revenue, with labeled axes and values.",
      "files": ["evals/files/sales_2025.csv"],
      "assertions": [
        "The output includes a bar chart image file",
        "The chart shows exactly 3 months",
        "Both axes are labeled",
        "The chart title or caption mentions revenue"
      ]
    }
  ]
}
```

Start with 2-3 cases. Don't over-invest before the first pass.

### Writing assertions

Good:
- "The output file is valid JSON" — programmatically verifiable.
- "The bar chart has labeled axes" — specific and observable.
- "The report includes at least 3 recommendations" — countable.

Weak:
- "The output is good" — too vague to grade.
- "The output uses the exact phrase 'Total Revenue: $X'" — too brittle; correct output with different wording fails.

Reserve assertions for things that can be checked objectively. Style and "feels right" are caught in human review, not assertions.

## Running the loop

### 1. Spawn runs

```bash
uv run scripts/run-evals.py \
  --skill <target-skill-dir> \
  --evals <target-skill-dir>/evals/evals.json \
  --workspace <workspace-dir> \
  --iteration 1 \
  --runs 1 \
  --runner "claude -p"
```

For each eval, the script:
1. Runs the prompt *with* the skill enabled. Captures stdout, stderr, exit code, wall time, and any files written under `outputs/`.
2. Runs the prompt *without* the skill (baseline). Same capture.
3. Writes `with_skill/timing.json` and `without_skill/timing.json`.
4. Drops `grading_prompt.md` next to each pair containing the assertions and a request the user (or another agent) can paste into a fresh session to produce `grading.json`.

`--runs 3` for repeated runs per case once the skill is stable. Multiple runs let you compute stddev and detect flakiness.

### 2. Grade

For each `eval-<id>/{with_skill,without_skill}/`, write a `grading.json`:

```json
{
  "assertion_results": [
    { "text": "…", "passed": true,  "evidence": "Found chart.png (45KB) in outputs directory" },
    { "text": "…", "passed": false, "evidence": "Y-axis is labeled 'Revenue ($)' but X-axis has no label" }
  ],
  "summary": { "passed": 3, "failed": 1, "total": 4, "pass_rate": 0.75 }
}
```

The simplest path: paste `grading_prompt.md` plus the outputs into an LLM session and ask it to produce `grading.json`. For mechanical checks (file exists, valid JSON, exact row count), prefer a small verification script.

Grading rules:
- **Concrete evidence required for PASS.** "Includes a summary" + a section titled "Summary" with one vague sentence = FAIL. The label is there but the substance isn't.
- **Watch the assertions themselves.** If an assertion always passes regardless of skill quality, it's not measuring anything; replace it. If one always fails even on good output, it's broken; fix it.

### 3. Aggregate

```bash
uv run scripts/aggregate.py --workspace <workspace-dir> --iteration 1
```

Reads every `grading.json` and `timing.json`, computes per-configuration mean / stddev for `pass_rate`, `time_seconds`, `tokens`, and writes `benchmark.json`:

```json
{
  "run_summary": {
    "with_skill":    { "pass_rate": { "mean": 0.83, "stddev": 0.06 },
                       "time_seconds": { "mean": 45.0, "stddev": 12.0 },
                       "tokens": { "mean": 3800, "stddev": 400 } },
    "without_skill": { "pass_rate": { "mean": 0.33, "stddev": 0.10 },
                       "time_seconds": { "mean": 32.0, "stddev": 8.0 },
                       "tokens": { "mean": 2100, "stddev": 300 } },
    "delta": { "pass_rate": 0.50, "time_seconds": 13.0, "tokens": 1700 }
  }
}
```

## Reading the result

The decision is the `delta`.

- `delta.pass_rate` — what the skill buys.
- `delta.tokens` and `delta.time_seconds` — what it costs.

Sample readings:

- `delta.pass_rate = 0.50`, `delta.tokens = +1700` — clear win; ship.
- `delta.pass_rate = 0.05`, `delta.tokens = +3000` — overhead exceeds value; either tighten the skill or skip it for this domain.
- `delta.pass_rate = 0.30`, `stddev high` — skill works but is inconsistent; ambiguous instructions, add examples, re-run.
- Both `with_skill` and `without_skill` pass everything → assertions are too easy. Replace with harder ones.
- Both fail everything → either the assertions are wrong or the test cases are too hard. Investigate before iterating on the skill.

## Iteration

After grading, the signals are:

- **Failed assertions** — specific gaps in the skill.
- **Human feedback** — broader quality issues the assertions missed.
- **Execution transcripts** — *why* things went wrong; ambiguous instructions, wasted steps, ignored guidance.

To iterate:
1. Hand all three signals + the current `SKILL.md` to an LLM.
2. Ask for skill improvements. Generalize from feedback (the skill will be invoked on prompts beyond the test set).
3. Apply changes.
4. Re-run in `iteration-<N+1>/`.

Stop when feedback is consistently empty or improvements plateau.

## When to *not* run the loop

- The skill is for one user one time, not for shared use.
- The doc was already a polished playbook and the skill is mostly a copy.
- The user explicitly said "skip evals, just give me the skill."

In all other cases, the loop is the only way to know whether the skill is worth the context cost.
