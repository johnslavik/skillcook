# DESCRIPTION_WRITING

The `description` field is the entire trigger surface. Agents read only `name` + `description` at startup; the body is invisible until the description matches a user prompt. Treat the description like the most important sentence in the skill.

## Principles

1. **Imperative phrasing.** Address the agent directly: "Use this skill when…". Not "This skill helps with…". The agent is deciding whether to act.
2. **What + when.** Both, always. Skipping *when* leaves the trigger to the agent's guesswork.
3. **User-side vocabulary.** Match what real users type — file paths, casual phrases, abbreviations, typos. Not internal jargon.
4. **Pushy on coverage.** Explicitly include the cases where the user *won't* name the domain: "even if they don't say 'CSV' or 'analysis'."
5. **Concise.** Short paragraph at most. Hard limit 1024 chars.
6. **No marketing.** "Powerful comprehensive skill that handles all your needs" triggers nothing.

## Anti-patterns

```yaml
# Bad: too vague
description: Helps with PDFs.

# Bad: implementation focus
description: Wraps pdfplumber and pdf2image to provide PDF utilities.

# Bad: marketing copy
description: A comprehensive, professional-grade PDF processing skill.

# Bad: missing "when"
description: Extracts text from PDF files using pdfplumber and OCR.
```

## Pattern

```yaml
description: >
  <Verb-led summary of what the skill does, including the user-side terms it
  applies to.> Use when <list of user intents and phrasings, including the
  ambiguous cases where the domain isn't named directly>.
```

## Worked example

Before:

```yaml
description: Process CSV files.
```

After:

```yaml
description: >
  Analyze CSV and tabular data files — compute summary statistics, add derived
  columns, generate charts, and clean messy data. Use this skill when the user
  has a CSV, TSV, or Excel file and wants to explore, transform, or visualize
  the data, even if they don't explicitly mention "CSV" or "analysis".
```

The rewrite is more specific about *what* (summary stats, derived columns, charts, cleaning) and broader about *when* (CSV, TSV, Excel; even without explicit keywords).

## Designing trigger eval queries

Once a description is drafted, sanity-check it with a small set of queries. The eval loop in `scripts/run-evals.py` operates on the same files.

Aim for ~20 queries: 8-10 should-trigger, 8-10 should-not-trigger.

### Should-trigger

Vary along:
- **Phrasing**: formal, casual, abbreviated, typos.
- **Explicitness**: some name the domain ("analyze this CSV"), others don't ("my boss wants a chart from this data file").
- **Detail**: terse vs. context-heavy; mix file paths, column names, personal context.
- **Complexity**: single-step prompts and multi-step workflows where the skill is one link in the chain.

The most useful are the *implicit* cases — where a good description distinguishes itself.

### Should-not-trigger (near-misses)

Weak negatives are obviously irrelevant ("write fibonacci"). Strong negatives share keywords or concepts but need different work:

- "I need to update formulas in my Excel budget spreadsheet" — overlaps "spreadsheet" but is editing, not analysis.
- "Write a script that reads a CSV and uploads each row to Postgres" — overlaps "CSV" but is ETL, not analysis.

Strong negatives test whether the description is *precise*, not just broad.

### Realism

Real prompts contain personal context. Include:
- File paths (`~/Downloads/report_final_v2.xlsx`).
- "My manager asked me to…".
- Specific column names, company names, data values.
- Casual language and occasional typos.

## Iterating

Treat the description like code: revise, re-run, compare.

1. Run the queries through your agent with the skill installed.
2. Note which triggered, which didn't.
3. **Train/validation split** (~60 / 40, fixed across iterations): only revise based on the train set; check the validation set to verify changes generalize.
4. If should-trigger queries fail, the description is too narrow — broaden the *concept*, not by adding the failing query's exact keywords (that's overfitting).
5. If should-not-trigger queries false-trigger, add specificity about what the skill *doesn't* do, or sharpen the boundary with adjacent skills.
6. Keep the final under 1024 chars.

Five iterations is usually enough. If results plateau, the test set may be the bottleneck (too easy, too hard, or mislabeled).

## Quick checks before shipping

- [ ] Imperative voice present.
- [ ] Says what the skill does.
- [ ] Says when to trigger.
- [ ] Includes user-side trigger phrases.
- [ ] Mentions at least one "even if they don't say…" case.
- [ ] Under 1024 chars (use `wc -c <<< "$desc"`).
- [ ] No marketing adjectives ("powerful", "comprehensive", "robust").
- [ ] No internal jargon a user wouldn't type.
