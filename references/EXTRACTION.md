# EXTRACTION

How to mine the source for the parts that belong in a skill — and discard the parts that don't. Sources come in several shapes; this guide covers all of them.

The first draft of a skill from any source is almost always too long, too generic, and missing the actual gotchas. This guide is the procedure to avoid that.

## Source types

The user can hand you any of the following. Each type has a different *primary risk* and a different way to mine it.

| Source | Primary risk | Mining strategy |
| --- | --- | --- |
| Doc / runbook / README / RFC | Transcribing instead of extracting | Skim for procedure / gotchas / defaults; cut the rest |
| Prompt or short request | Generic restatement; no project specifics | Ask 2-4 follow-up questions before drafting |
| Conversation / transcript | Missing the corrections | Treat corrections as gotchas, the worked sequence as the workflow |
| Ad-hoc verbal description | Vagueness | Same as prompt: surface the *why* behind each step with follow-ups |
| Code or example artifact | Implicit-only assumptions | Reverse-engineer steps; confirm inferences with user |
| Mix of the above | Contradictions | Reconcile aloud with the user; don't paper over conflicts |
| Chat with a working agent right now | Losing the freshly-learned context | Capture corrections + worked steps before they're forgotten |

## Principle: only what the agent lacks

A skill should add what the agent *wouldn't know without it*. The agent already knows what HTTP is, what a PDF is, what a database migration is. It does not know:

- Project-specific conventions ("we always use the staging replica for read queries").
- Non-obvious gotchas ("the `users` table uses soft deletes; queries must filter `deleted_at IS NULL`").
- Naming inconsistencies across systems ("user ID is `user_id` in DB, `uid` in auth, `accountId` in billing").
- Particular tools / APIs / scripts to use vs. the generic alternatives.
- Failure modes the team has already learned from.

For each line you extract, ask: *would the agent get this wrong without it?* If no, cut.

## What to lift from a doc

Read the source with these categories in mind. Pull a sentence or quote into a working notes file under each one.

### 1. Coherent unit(s) of work

Find the task(s) the source is about. State each one in one sentence. If the source covers multiple tasks (e.g. "deploying *and* monitoring *and* incident response"), each is probably its own skill — see *Splitting into multiple skills* near the end of this file.

If you can't write a single sentence for any unit, the source isn't skill-shaped yet. Ask the user which slice they want.

### 2. The procedure

The ordered steps that lead to success. Note:
- Inputs at each step (what files, flags, or facts the step needs).
- Outputs at each step (what the next step consumes).
- Decision points (when to branch, with what test).
- Validation checkpoints (how you know the step succeeded).

Convert prose like "you'll typically want to back up the DB first, then run the migration, then verify" into an explicit checklist.

### 3. Gotchas

The highest-value content. These are facts that defy reasonable assumptions:
- "The `/health` endpoint returns 200 even when the DB is down. Use `/ready`."
- "Soft deletes everywhere — always filter `deleted_at IS NULL`."
- "Field names diverge: `user_id` (DB) ≠ `uid` (auth) ≠ `accountId` (billing)."

Look in the doc for: warning callouts, "note that…", footnotes, "do not…", "be careful with…", linked incidents, retros, "we learned the hard way…".

Convert each into one short imperative sentence with the *why* attached.

### 4. Defaults

When the doc presents multiple tools or approaches, pick one as the default. Don't transcribe a menu of options into the skill — that loads decision overhead onto the agent every run. Keep alternatives as escape hatches: "Use X. For case Y, fall back to Z."

### 5. Templates and constants

Output formats, schemas, error code lists, table headers. Short ones go inline as code blocks. Long ones move to `references/` or `assets/`.

### 6. Project-specific names

API names, table names, internal libraries, CLI tools. The agent needs to use the *exact* string. Don't paraphrase.

## What to discard

- Background that explains the *domain* the agent already understands.
- Marketing prose, mission statements, organizational history.
- Long rationales for past decisions (keep the decision; drop the why-we-chose-this).
- Generic best-practices unattached to a project specific ("write good code", "test thoroughly").
- Step-by-step tutorials for general-purpose tools that have docs of their own.
- Anything that begins with "as you know…".

When in doubt, cut. You can always grow the skill back; you cannot easily remove bloat once an agent has read it.

## From hands-on tasks (preferred)

If the user is mid-task and just figured something out together with an agent, that conversation is gold. Pay attention to:

- **Steps that worked** — the sequence of actions that led to success.
- **Corrections the user made** — places where the agent's first approach was wrong. Each correction is a candidate gotcha.
- **Context the user supplied** — facts the agent didn't already know. These often become inline content or references.
- **Input/output shapes** — exact filenames, schemas, response formats.

Then write the skill *as if* the agent were doing the same task fresh, with the gotchas pre-loaded.

## From a static doc (when no transcript is available)

Treat the doc as a witness, not a script. Ask:

- What does the doc *implicitly* assume the reader already knows?
- What does the doc warn against? (gotchas)
- What does the doc default to when alternatives exist? (defaults)
- What sequence does the doc imply, even when not explicitly numbered? (procedure)
- Where does the doc contradict itself? (flag for the user — don't paper over)

If the doc is reference material (an API spec), the skill is probably "use this API to do X" — use the spec as a *reference*/, and the body of the skill is the procedure. Don't transcribe the API spec into the body.

## Splitting body vs. references

After extraction, sort the notes into three buckets.

**Body of `SKILL.md`** (loaded when the skill activates):
- The workflow checklist.
- All gotchas.
- The chosen default.
- Short templates (<30 lines).
- One-line pointers to references with explicit triggers.

**`references/`** (loaded only on explicit trigger):
- Long error-code tables.
- Per-tool deep-dives where only one workflow branch needs them.
- Detailed schemas.
- Long output templates (or stash in `assets/`).
- Edge cases the workflow rarely hits.

**Discard**:
- Anything in the "what to discard" list above.

Each reference file should have a clear purpose stated in its first paragraph, so the agent knows when to load it.

## Splitting into multiple skills

A single source can produce more than one skill. Split when:

- **Different trigger surfaces.** "Deploy", "rollback", and "monitor" are three distinct user prompts. Each needs its own description; one skill can't trigger reliably on all three.
- **Different procedures.** If the steps, scripts, or gotchas don't overlap, a combined skill is two skills under one frontmatter — the agent will load detail it doesn't need.
- **The combined description would exceed 1024 chars or read as marketing.** A bloated description fails to trigger reliably. If you can't compress the union into a tight what-and-when, split.
- **Different audiences or contexts.** A skill for the on-call engineer at 3am has different defaults than a skill for the developer planning a migration two weeks out — even if both touch the same system.

Don't split when:

- **One sub-task only makes sense in the context of another** (e.g. validation that's only meaningful inside a specific procedure). Keep them together; cohesion beats granularity.
- **The split would force the agent to load multiple skills for the same prompt.** That's the failure mode of over-narrow scoping — overhead and conflicting instructions.

When the source covers multiple units of work, list them all to the user before scaffolding any: *"This source covers deploy, rollback, and monitoring. I think these are three skills. Want all three, or one specific one first?"* Don't silently pick.

When proceeding with multiple skills, mine each one's content separately — extract gotchas relevant to *deploy* into the deploy skill, gotchas relevant to *rollback* into the rollback skill. Shared gotchas can be duplicated; the cost of two skills repeating one fact is far less than the cost of one skill loading detail unrelated to the current prompt.

## Output of this step

By the end of extraction, you should have:

- A list of one-sentence statements — one per output skill.
- A working notes file (or in-conversation summary) per skill, with sections for procedure, gotchas, defaults, templates, names.
- A clear sense of what is body vs. reference for each skill.
- A list of candidate scripts (mechanical work the agent will reinvent) per skill.

Move on to step 9 of the workflow with these in hand. If multiple skills are in scope, complete each one through validation before starting the next.
