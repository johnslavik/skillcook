---
name: skillcook
description: Turn any kind of source — a document (runbook, RFC, README, API doc, wiki page, PDF), a prompt or short request ("make me a skill for reviewing Python diffs"), an ad-hoc description, a chat transcript or conversation, code with comments, error logs, examples of past work, or a vague gesture at a workflow — into one or more working Agent Skills. Drafts each SKILL.md with valid frontmatter, splits detail into references/, scaffolds scripts/ and evals/, validates the result, and optionally runs the with-skill / without-skill eval loop. Splits a single broad source into multiple coherent skills when the material covers more than one unit of work. Use when the user says "make a skill", "turn this into a skill(s)", "wrap this as a skill", "package this for an agent", or hands over material (doc, prompt, transcript, anything) and asks for reusable agent guidance — even if they don't say the word "skill".
license: MIT
compatibility: Requires uv (for scripts/validate.py and scripts/run-evals.py). The eval loop additionally needs an LLM CLI (default `claude -p`).
allowed-tools: Read Write Edit Bash(uv:*) Bash(bash:*) Bash(mkdir:*) Bash(ls:*)
metadata:
  cooked-with: johnslavik/skillcook
  cooked-with-version: self
---

# skillcook

Turn any source — a document, a prompt, a chat transcript, an ad-hoc description, code, anything — into one or more working Agent Skills that conform to the format at https://agentskills.io. Output is one or more skill directories the user can drop into their agent client.

## Workflow

Follow these steps in order. Don't skip — most failure modes (skills that won't trigger, skills that bloat context, skills that miss the actual gotchas) come from compressing the early steps.

- [ ] **1. Identify the source type and gather it.** The source can be any of:
  - **Document** — file path, URL, pasted text. Fetch URLs; read files; for large PDFs read only the section relevant to step 2 and re-read on demand.
  - **Prompt or short request** — the user describes what they want a skill for in one or two sentences ("make me a skill for reviewing Python diffs"). The "source" is the user's intent. Ask 2-4 short follow-up questions to surface project specifics, gotchas, defaults, and the unit of work — without those, the skill will be a generic restatement of the prompt and won't beat the baseline agent.
  - **Conversation / transcript** — a hands-on session where corrections, context, and steps are visible. This is the highest-signal source. Lift the corrections as gotchas and the worked sequence as the workflow.
  - **Ad-hoc description** — verbal / chat explanation. Treat like a prompt but with more material; still ask follow-ups for the *why* behind each step.
  - **Code or examples** — a script, a config, a sample output. Reverse-engineer the procedure from the artifact and confirm the inferred steps with the user.
  - **A mix** — a doc plus a prompt plus a few corrections. Common case; treat each piece as evidence and reconcile.

  If the user gave you nothing concrete (just "make a skill for X" with no project specifics), do not fabricate domain content. Ask: what tools do you use? what gotchas have you hit? what's the typical input/output? Each answered question becomes a candidate inline-or-reference entry; each refused question is a sign the skill might not have enough substance to be worth writing (see *When NOT to make a skill* below).
- [ ] **2. Identify the coherent unit(s) of work.** A *single* skill should encapsulate a single well-scoped task you can name in one sentence. A source can yield more than one skill: a wiki page covering deploy + rollback + monitoring is three skills, not one. Before drafting, list the units of work the source covers; if there's more than one, confirm with the user whether to produce multiple skills or focus on one. Read `references/EXTRACTION.md` for how to mine procedures, gotchas, and defaults; read the *Splitting* section there for the heuristics on when to split.
- [ ] **3. Pick the skill `name`.** Kebab-case, 1-64 chars, lowercase `a-z0-9` and hyphens, no leading/trailing/consecutive hyphens. **Must equal the parent directory name.** See `references/FRONTMATTER.md` if unsure.
- [ ] **4. Pick the target directory.** Confirm with the user. The directory's basename will be the skill name. Default if user is silent: `<cwd>/<name>/` or `~/.claude/skills/<name>/`.
- [ ] **5. Draft the `description`.** Imperative voice ("Use when…"), states *what* + *when*, ≤1024 chars, includes user-side keywords that real prompts will contain. Read `references/DESCRIPTION_WRITING.md` before writing.
- [ ] **6. Decide what stays in `SKILL.md` body vs. moves to `references/`.** Body must be <500 lines. Inline: workflow, gotchas, defaults, short templates. References: long format templates, per-error troubleshooting, deep technical specs, anything only sometimes needed. Each reference must be loaded by an explicit "Read X if Y" trigger in the body — never a vague "see references/".
- [ ] **7. Identify reusable scripts.** If the source describes mechanical work the agent will reinvent on every run (validation, parsing, formatting), bundle a script. Read `references/SCRIPTS.md` for agentic-design rules.
- [ ] **8. Scaffold.** For each output skill, run:
  ```bash
  bash scripts/new-skill.sh <target-parent-dir> <skill-name>
  ```
  This creates the directory tree and seeds `SKILL.md` and `evals/evals.json` from the templates. Repeat per output skill if step 2 yielded more than one.
- [ ] **9. Fill in the SKILL.md body** for each output skill. Use `assets/SKILL_template.md` as the starting structure. Apply patterns from `references/PATTERNS.md` (gotchas, checklists, validation loops, plan-validate-execute) where they fit. When you produce multiple skills, mention sibling skills only when one needs the other to make sense; don't cross-reference for organizational tidiness.
- [ ] **10. Validate** each output skill.
  ```bash
  uv run scripts/validate.py <target-skill-dir>
  ```
  Fix every error and warning before proceeding.
- [ ] **11. Write 2-3 starter evals** per output skill. See `assets/evals_template.json`. One happy path, one near-miss negative (similar keywords, different intent — should *not* trigger), one boundary case.
- [ ] **12. (Optional, on user request) Run the eval loop** per output skill. Read `references/EVAL_LOOP.md`. Use `scripts/run-evals.py` and `scripts/aggregate.py`. Check the `delta` in `benchmark.json`: if the skill doesn't measurably help, it's overhead — say so to the user.

## Inputs

What you need before step 5, regardless of source type:
- The source material itself (path, URL, pasted content, prompt, transcript, code).
- The target directory (or permission to default).
- Any constraints the user cares about: target agent client, license, expected runtime tools.

Per-input-type playbook:

- **Doc.** Read it. Skim for procedure, gotchas, defaults, names, templates. Don't transcribe the doc into the skill — extract.
- **Prompt-only.** Ask 2-4 follow-up questions before drafting: *what tools / scripts do you use today? what mistakes have you made that we can encode as gotchas? what's the input and output? what does success look like?* Without answers, you have a generic procedure the agent already knows; stop and tell the user.
- **Transcript / conversation.** Treat *corrections* as gotchas, the *worked sequence* as the workflow, *user-supplied context* as inline content or reference material. Quote exact strings the user used (file paths, table names, flag names).
- **Code or examples.** Read the artifact, infer the procedure, confirm with the user before drafting. Names, flags, and edge-case branches in code become inline content; long type/schema dumps become references.
- **Mix.** Reconcile sources: the doc says *A*, the user said *B* — ask which is current. Don't paper over contradictions.

What you should *not* invent under any source type: project-specific facts, API behaviours, gotchas, tool names. If the source is silent on something the skill needs, ask.

## One source, one or many skills

A source can yield zero, one, or several skills. Decide *before* drafting any frontmatter.

**Produce one skill** when the source describes a single coherent task you can name in a sentence ("triage Postgres replica-lag alerts", "review Python diffs for security issues").

**Produce multiple skills** when the source covers tasks that:
- Trigger on different user prompts (a "deploy" prompt vs. a "rollback" prompt vs. a "monitor" prompt are three trigger surfaces).
- Have meaningfully different procedures (different scripts, different validations, different gotchas).
- Would force one fat description to either overgrow 1024 chars or fail to trigger reliably on any of the sub-tasks.

A wiki page titled "Service operations" covering deploy + rollback + monitoring + incident response is *four* skills, not one. Each one will trigger more reliably and stay leaner than a single mega-skill.

**Produce zero skills** when:
- The agent already does this task well without help (run the prompt against a baseline first if unsure — see *When NOT to make a skill*).
- The source is too thin to encode a real procedure or gotchas. A one-line "use jq to filter JSON" produces nothing the agent doesn't already know.

When in doubt, ask the user which slice they want first. List the candidate units of work explicitly: *"Your runbook covers deploy, rollback, and monitoring. I think these are three skills. Do you want all three, or should we start with one?"* Don't silently pick.

When producing multiple skills, complete each one through validation (steps 8-10) before moving to the next — don't half-finish several. The shared source is read once; each skill's body is drafted independently.

## Naming (quick rules)

- Match the parent directory name *exactly*.
- Kebab: `pdf-processing`, `oncall-runbook`, `gh-pr-review`. No `PDF-Processing`, no `--`, no leading/trailing `-`.
- Names describe what the skill *does*, not the team that owns it.
- Full rules + regex: `references/FRONTMATTER.md`.

## Description (quick rules)

- Imperative: "Use this skill when…" / "Turn X into Y when the user…".
- *What* the skill does + *when* to trigger it. Both, or it won't activate.
- Include user-side trigger phrases — what the user actually types, not internal jargon.
- Be pushy about coverage: "even if they don't explicitly mention 'CSV'."
- ≤1024 chars (hard limit; spec rejects longer).
- Full guide + how to test triggering: `references/DESCRIPTION_WRITING.md`.

## Body vs. references heuristic

Inline in `SKILL.md`:
- Workflow checklist.
- Gotchas (always — the agent encounters them mid-task without warning).
- Default tool / approach.
- Short output templates (<30 lines).

Move to `references/`:
- Full API tables / error code lists.
- Long output templates (also acceptable in `assets/`).
- Per-tool deep-dives only one branch of the workflow needs.
- Anything that turns the body into a wall of detail.

The trigger to load a reference goes in the body, like: "If the response is non-200, read `references/api-errors.md`." Vague pointers don't activate progressive disclosure.

## Gotchas

These are the rules an agent producing a skill will get wrong without being told. Treat them as non-negotiable.

- **`name` must equal the parent directory basename.** Not the project name, not the repo name, not what the user typed in chat. The validator enforces this; a mismatch means the skill won't load in some clients.
- **The `description` is the *entire* trigger surface.** Agents only read `name` + `description` at startup. Body content is invisible until the description matches. A perfect body with a vague description is a dead skill.
- **Don't restate things the agent already knows.** No "PDF is a file format…", no "HTTP is a protocol…". Add only what the agent *lacks* — project conventions, non-obvious edges, specific tools.
- **Procedures, not declarations.** Teach the *approach* ("read the schema, then join on `_id`"), not a one-shot answer for one query. The skill will be invoked on prompts you didn't anticipate.
- **Reference files need explicit triggers.** "See `references/foo.md`" doesn't load it on demand — agents read what they're told to read. Write "Read `references/foo.md` when X happens."
- **Scripts must be non-interactive.** Agents run in non-TTY shells. Any prompt for input hangs the whole run. All input via flags / env / stdin.
- **Don't promise capabilities the host may not have.** If the skill assumes `gh`, `docker`, `uv`, network access — declare it in the `compatibility` field, or provide an escape hatch.
- **Source contradictions surface to the user.** If the doc says one thing in step 2 and the opposite in step 5, ask before guessing. Don't bake a wrong choice into the skill.
- **Description ≠ marketing copy.** Don't write "powerful skill that handles many tasks". Write the trigger phrases the user types.
- **Match scope to a coherent unit.** Too narrow → many skills load for one task, conflicting instructions. Too broad → won't activate precisely. A query-and-format skill is one unit; that-plus-DB-administration is two.

## When NOT to make a skill

If the agent already produces good output for the user's task without the skill, the skill is pure context overhead. Before finalizing:

- Try the prompt against a baseline agent (no skill, no extra context).
- If the baseline is fine, tell the user the skill won't help and ask whether they still want it.
- The eval loop in step 12 measures this: a `delta.pass_rate` near zero across the eval set means the skill isn't earning its tokens.

This is also the reason for the boundary eval case — to make the "skip-the-skill" decision visible.

## References

Each file is loaded only when the trigger below fires.

- **`references/FRONTMATTER.md`** — read when picking `name`, deciding whether to use `compatibility` / `license` / `metadata` / `allowed-tools`, or hitting any frontmatter validation error.
- **`references/DESCRIPTION_WRITING.md`** — read at step 5, or when a description fails to trigger on prompts the user expects.
- **`references/EXTRACTION.md`** — read at step 2 when staring at a source doc and unsure what to lift out.
- **`references/PATTERNS.md`** — read at step 9 to copy a checklist / gotchas / template / validation-loop / plan-validate-execute block.
- **`references/SCRIPTS.md`** — read at step 7 when designing or bundling a script.
- **`references/EVAL_LOOP.md`** — read at step 12 before invoking `run-evals.py`, or when interpreting `benchmark.json`.

## Available scripts

- **`scripts/new-skill.sh <parent-dir> <skill-name>`** — scaffold a new skill directory from the templates. Idempotent; refuses to overwrite without `--force`.
- **`scripts/validate.py <skill-dir> [--strict]`** — validate frontmatter + structure. Exit 0 if clean. JSON report on stdout.
- **`scripts/run-evals.py --skill <dir> --evals <path> --workspace <dir> --iteration N`** — spawn with-skill / without-skill runs and capture outputs and timing.
- **`scripts/aggregate.py --workspace <dir> --iteration N`** — read grading + timing JSON, write `benchmark.json`.

All scripts support `--help`.

## Output you produce for the user

When done, the user has one or more directories, each shaped like:

```
<target>/
├── SKILL.md
├── references/         # only if needed
├── scripts/            # only if needed
├── assets/             # only if needed
└── evals/
    └── evals.json
```

Per output skill, report: the path, the line count of `SKILL.md`, and whether validation passed. If the eval loop ran, summarize `delta.pass_rate` and `delta.tokens` from `benchmark.json`. Don't claim a skill is good — claim it's *valid* and let the eval numbers speak.

When you produce multiple skills, end with a short summary table — one row per skill — listing the same facts across all of them, so the user sees the whole batch at a glance.

## Watermark

Every skill produced by skillcook carries a watermark in two places. The `assets/SKILL_template.md` already contains both — `scripts/new-skill.sh` substitutes the version at scaffold time. Don't strip them when editing the body.

1. **Frontmatter `metadata`**:
   ```yaml
   metadata:
     cooked-with: johnslavik/skillcook
     cooked-with-version: <git-short-sha>
   ```
2. **Body footer** (very last lines of `SKILL.md`):
   ```markdown
   ---

   <sub>[![Cooked with skillcook](https://img.shields.io/badge/cooked_with-skillcook-d97757)](https://github.com/johnslavik/skillcook)</sub>
   ```

The user can remove the watermark on any individual skill if they prefer — it's not enforced by the validator. But by default, every skill that comes out of skillcook is marked.

---

<sub>[![Cooked with skillcook](https://img.shields.io/badge/cooked_with-skillcook-d97757)](https://github.com/johnslavik/skillcook)</sub>
