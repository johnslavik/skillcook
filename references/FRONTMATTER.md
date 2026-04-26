# FRONTMATTER

Reference for the YAML frontmatter at the top of `SKILL.md`. Source of truth: https://agentskills.io/specification.

## Fields

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | yes | 1-64 chars; `a-z 0-9 -`; no leading/trailing/consecutive `-`; **must equal parent dir basename** |
| `description` | yes | 1-1024 chars; what + when |
| `license` | no | License name (e.g. `MIT`) or path to a bundled license file |
| `compatibility` | no | ≤500 chars; environment requirements (uv, docker, network, intended product) |
| `metadata` | no | string→string map for client-specific extras |
| `allowed-tools` | no | space-separated pre-approved tool list (experimental, support varies) |

## `name` regex

```
^[a-z0-9](?:[a-z0-9]|-(?!-))*[a-z0-9]$
```

Valid: `pdf-processing`, `oncall-runbook`, `gh-pr-review`, `data-analysis`.
Invalid: `PDF-Processing` (uppercase), `-pdf` (leading `-`), `pdf--processing` (consecutive `-`), `pdf_processing` (underscore).

## The parent-directory rule

The skill's `name` field MUST be identical to the basename of the directory containing `SKILL.md`. If you put the skill at `~/.claude/skills/oncall/SKILL.md`, then `name: oncall`. Mismatched names load inconsistently across agent clients.

`scripts/validate.py` enforces this — it diffs the YAML `name` against the directory it's in.

## `description` writing rules

Encoded fully in `references/DESCRIPTION_WRITING.md`. Quick version:
- Imperative ("Use this skill when…").
- Both *what* it does and *when* to trigger it.
- Include the words real users type, not internal jargon.
- ≤1024 chars; the spec is hard-limited.

## `license`

Two valid forms:

```yaml
license: MIT
```

```yaml
license: Proprietary. LICENSE.txt has complete terms
```

Keep it short. If you bundle a `LICENSE` or `LICENSE.txt` file, reference it by name in the field.

## `compatibility`

Use this only if the skill needs something the host environment may lack. Examples:

```yaml
compatibility: Designed for Claude Code (or similar products)
```

```yaml
compatibility: Requires git, docker, jq, and access to the internet
```

```yaml
compatibility: Requires Python 3.14+ and uv
```

If the skill is plain markdown procedures with no dependencies, omit the field. ≤500 chars enforced.

## `metadata`

Free-form string-to-string map for things the spec doesn't define — author, version, internal team, etc.

```yaml
metadata:
  author: example-org
  version: "1.0"
  team: platform
```

Keep keys reasonably unique (`pandadoc.team` not `team`) to avoid collisions when skills mix.

## `allowed-tools`

Experimental. Space-separated list of tools the skill may invoke without asking. Format and parsing are client-specific.

```yaml
allowed-tools: Read Edit Bash(git:*) Bash(jq:*)
```

If you don't know whether the target client supports it, omit it — clients without support will simply ignore the field.

## Minimal example

```yaml
---
name: oncall
description: Triage Postgres on-call alerts using the runbook conventions for the platform team. Use when the user receives a pager alert, mentions an on-call incident, or asks how to handle a database issue, even without saying "oncall".
---
```

## Example with all optional fields

```yaml
---
name: oncall
description: …
license: MIT
compatibility: Requires psql 14+ and read access to the prod replica.
allowed-tools: Read Bash(psql:*) Bash(gh:*)
metadata:
  author: platform-team
  version: "0.3"
---
```

## Common validation failures

- `name` contains uppercase or underscore → rewrite as kebab.
- `name` doesn't match parent dir → rename the dir or rename the field; pick whichever is canonical.
- Description >1024 chars → cut marketing copy, keep the trigger keywords and the `when` clause.
- Description doesn't say *when* to trigger → add a "Use when…" sentence.
- YAML doesn't parse (often a stray colon in a description) → quote the description: `description: "…"`.
