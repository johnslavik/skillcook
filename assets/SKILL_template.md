---
name: {{NAME}}
description: <One short paragraph. Imperative voice ("Use this skill when…"). Both what + when. Include user-side trigger phrases. Be pushy about coverage — "even if they don't say X". ≤1024 chars.>
metadata:
  cooked-with: johnslavik/skillcook
  cooked-with-version: "{{COOKED_WITH_VERSION}}"
---

# {{NAME}}

<One-paragraph statement of the unit of work this skill encapsulates.>

## Workflow

<!-- Use a checklist when there are 3+ steps. Otherwise plain bullets. -->

- [ ] Step 1: <action>
- [ ] Step 2: <action>
- [ ] Step 3: Validate (e.g. `uv run scripts/check.py output/`)
- [ ] Step 4: <action>

## Inputs

<!-- What the agent should expect from the user. What to ask for if it's missing. What NOT to invent. -->

## Defaults

<!-- The single tool / approach to use first. Mention alternatives only as named escape hatches. -->

## Gotchas

<!-- Highest-value section. Each entry: imperative or declarative one-liner + the *why*. The why lets the agent extrapolate. Add to this every time you correct the agent during a real run. -->

- <Gotcha 1 — what defies reasonable assumptions, and why.>
- <Gotcha 2.>

## References

<!-- One bullet per file in references/. Each line MUST include an explicit "Read X if Y" trigger. Vague pointers like "see references/" do not activate progressive disclosure. -->

- **`references/<file>.md`** — read when <specific condition>.

## Available scripts

<!-- Delete this section if no scripts/. Otherwise list them with one-line descriptions. -->

- **`scripts/<name>.py [args]`** — <what it does>.

## Output

<!-- What the user should see when the skill finishes. State facts, don't market the result. -->

---

<sub>[![Cooked with skillcook](https://img.shields.io/badge/cooked_with-skillcook-d97757)](https://github.com/johnslavik/skillcook)</sub>
