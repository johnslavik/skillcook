# skillcook

An [Agent Skill](https://agentskills.io) that turns any source — a document, a prompt, a chat transcript, an ad-hoc description, code — into one or more working Agent Skills.

When the source covers multiple units of work, skillcook produces multiple skills. When the source is too thin to beat a baseline agent, it says so instead of producing dead weight.

## What it does

Given a source, skillcook:

1. Identifies the unit(s) of work the source covers — and asks the user before silently picking.
2. Drafts a `SKILL.md` per output skill with valid frontmatter (kebab `name`, ≤1024-char `description`, etc.) per the [Agent Skills spec](https://agentskills.io/specification).
3. Splits detail into `references/` with explicit "Read X if Y" load triggers, and bundles reusable logic into `scripts/`.
4. Validates the result with a strict frontmatter checker.
5. Optionally runs the with-skill / without-skill eval loop so the user gets evidence the skill is worth its context cost.

## Install

Drop the directory wherever your agent client picks up skills.

For Claude Code:
```bash
git clone git@github.com:johnslavik/skillcook.git ~/.claude/skills/skillcook
```

For VS Code Copilot:
```bash
git clone git@github.com:johnslavik/skillcook.git <your-project>/.agents/skills/skillcook
```

The skill needs `uv` for the validator and eval-runner scripts. The eval loop additionally needs an LLM CLI (default `claude -p`).

## Usage

Trigger phrases the skill listens for:

- *"Make a skill from this runbook."*
- *"Turn this into a skill."*
- *"I want a skill for reviewing Python diffs."* (prompt-only — skill will ask follow-ups)
- *"Wrap this conversation as a skill."*
- *"Package this for an agent."*

Or hand it any document and ask for "reusable agent guidance" — the skill triggers without the word "skill" being present.

## Structure

```
skillcook/
├── SKILL.md                # main procedure
├── references/             # loaded on demand
│   ├── FRONTMATTER.md
│   ├── DESCRIPTION_WRITING.md
│   ├── EXTRACTION.md
│   ├── PATTERNS.md
│   ├── SCRIPTS.md
│   └── EVAL_LOOP.md
├── scripts/
│   ├── validate.py         # uv run scripts/validate.py <skill-dir>
│   ├── new-skill.sh        # bash scripts/new-skill.sh <parent> <name>
│   ├── run-evals.py        # spawns with/without runs
│   └── aggregate.py        # produces benchmark.json
├── assets/
│   ├── SKILL_template.md
│   └── evals_template.json
└── evals/
    ├── evals.json
    └── files/
        └── sample_runbook.md
```

## License

MIT — see [LICENSE](LICENSE).
