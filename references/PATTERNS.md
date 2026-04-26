# PATTERNS

Copy-and-adapt blocks for the body of a SKILL.md. Each pattern has a one-line *use when* trigger.

## Workflow checklist

**Use when** the task has 3+ steps, especially if steps depend on previous outputs or have validation gates.

```markdown
## Workflow

- [ ] Step 1: <action> (run `scripts/<x>.py`)
- [ ] Step 2: <action> (edit `<file>.json`)
- [ ] Step 3: Validate (run `scripts/validate.py`)
- [ ] Step 4: <action>
- [ ] Step 5: Verify output
```

Why checklists work: the agent tracks progress visibly and is less likely to skip a validation step.

## Gotchas

**Use when** the project has non-obvious facts that defy reasonable assumptions — basically always; the gotchas section is the highest-value part of most skills.

```markdown
## Gotchas

- The `users` table uses soft deletes. Queries must include
  `WHERE deleted_at IS NULL` or results will include deactivated accounts.
- The user ID is `user_id` in the database, `uid` in the auth service,
  and `accountId` in the billing API. All three refer to the same value.
- The `/health` endpoint returns 200 as long as the web server is running,
  even if the database connection is down. Use `/ready` to check full
  service health.
```

Each entry: imperative or declarative one-liner + the *why*. The why lets the agent extrapolate to edge cases the gotcha didn't enumerate.

When the agent makes a mistake mid-task and you correct it, append a gotcha. This is the most direct iterative improvement available.

## Output template

**Use when** you need the output in a specific structure. Templates outperform prose descriptions because models pattern-match on shapes.

````markdown
## Report structure

Use this template, adapting sections as needed:

```markdown
# [Analysis Title]

## Executive summary
[One paragraph]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```
````

Short templates go inline. Templates >30 lines or only-sometimes-used belong in `assets/` and are referenced from the body.

## Validation loop

**Use when** the agent's work needs a self-check before moving on (formatted output, generated code, structured config).

```markdown
## Editing workflow

1. Make your edits.
2. Run validation: `python scripts/validate.py output/`
3. If validation fails:
   - Read the error message.
   - Fix the issues.
   - Re-run validation.
4. Only proceed when validation passes.
```

The validator can be a script, a checklist in a reference file, or a self-review prompt — whatever produces a deterministic pass/fail.

## Plan-validate-execute

**Use when** the operation is destructive, batched, or expensive to redo (form filling, bulk migrations, mass renames).

```markdown
## Form filling

1. Extract form fields: `python scripts/analyze_form.py input.pdf` → `form_fields.json`
   (lists every field name, type, required-ness)
2. Create `field_values.json` mapping each field to its intended value.
3. Validate: `python scripts/validate_fields.py form_fields.json field_values.json`
   (checks names exist, types match, required fields present)
4. If validation fails, revise `field_values.json` and re-validate.
5. Execute: `python scripts/fill_form.py input.pdf field_values.json output.pdf`
```

Step 3 is the load-bearing one: a script that diffs the plan against the source of truth and emits actionable errors ("Field 'signature_date' not found — available: customer_name, order_total, signature_date_signed"). The error text lets the agent self-correct without another round trip.

## Defaults with escape hatches

**Use when** multiple tools or approaches are valid, but choosing on every run wastes context.

````markdown
Use `pdfplumber` for text extraction:

```python
import pdfplumber
```

For scanned PDFs requiring OCR, use `pdf2image` with `pytesseract` instead.
````

State the default, give one alternative for the named edge case. Don't list four options of equal weight.

## Reference loading triggers

**Use when** material is too long for the body but sometimes needed.

```markdown
If the API returns a non-200 status, read `references/api-errors.md`
and match the response code against the table.

Read `references/schema.yaml` once at the start of any analytical query
to find relevant tables and column types.
```

The trigger is "Read X if Y". Vague pointers like "see references/" don't activate progressive disclosure — the agent just keeps going with what it has.

## Procedures over declarations

**Use when** writing any non-trivial instruction. Compare:

```markdown
<!-- Specific answer — only useful for this exact task -->
Join the `orders` table to `customers` on `customer_id`, filter where
`region = 'EMEA'`, and sum the `amount` column.

<!-- Reusable method — works for any analytical query -->
1. Read the schema from `references/schema.yaml` to find relevant tables.
2. Join tables using the `_id` foreign key convention.
3. Apply filters from the user's request as WHERE clauses.
4. Aggregate numeric columns as needed and format as a markdown table.
```

The skill will be invoked on prompts you didn't plan for. Teach the *approach*, not the answer.

## When to be prescriptive vs. flexible

**Match specificity to fragility.**

Flexible (give the agent freedom):

```markdown
## Code review process

1. Check database queries for SQL injection (parameterized queries).
2. Verify auth checks on every endpoint.
3. Look for race conditions in concurrent paths.
4. Confirm error messages don't leak internal details.
```

Prescriptive (consistency matters, sequence is fragile):

````markdown
## Database migration

Run exactly this sequence:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
````

Most skills mix both. Calibrate per section, not per skill.
