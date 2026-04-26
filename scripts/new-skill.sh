#!/usr/bin/env bash
# Scaffold a new Agent Skill directory from the bundled templates.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: new-skill.sh <parent-dir> <skill-name> [--force]

Scaffolds a new skill at <parent-dir>/<skill-name>/ with:
  - SKILL.md          (from assets/SKILL_template.md, {{NAME}} substituted)
  - references/
  - scripts/
  - assets/
  - evals/evals.json  (from assets/evals_template.json)
  - evals/files/

Options:
  --force   Overwrite an existing non-empty SKILL.md.
  -h, --help

Exit codes:
  0  Created.
  1  Refused to overwrite (use --force).
  2  Bad arguments.
EOF
}

force=0
positional=()

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
    --force) force=1 ;;
    --*) echo "Unknown flag: $arg" >&2; usage >&2; exit 2 ;;
    *) positional+=("$arg") ;;
  esac
done

if [[ ${#positional[@]} -ne 2 ]]; then
  usage >&2
  exit 2
fi

parent_dir="${positional[0]}"
skill_name="${positional[1]}"

if ! [[ "$skill_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "Error: skill name must be kebab-case (lowercase a-z, 0-9, hyphens; no leading/trailing/consecutive hyphens)." >&2
  echo "       Got: '$skill_name'" >&2
  exit 2
fi

if (( ${#skill_name} > 64 )); then
  echo "Error: skill name must be 1-64 characters. Got ${#skill_name}." >&2
  exit 2
fi

target="$parent_dir/$skill_name"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "$script_dir/.." && pwd)"
template_skill="$skill_root/assets/SKILL_template.md"
template_evals="$skill_root/assets/evals_template.json"

if [[ ! -f "$template_skill" ]]; then
  echo "Error: template missing at $template_skill" >&2
  exit 2
fi
if [[ ! -f "$template_evals" ]]; then
  echo "Error: template missing at $template_evals" >&2
  exit 2
fi

mkdir -p "$target/references" "$target/scripts" "$target/assets" "$target/evals/files"

skill_md="$target/SKILL.md"
if [[ -s "$skill_md" && $force -eq 0 ]]; then
  echo "Refusing to overwrite non-empty $skill_md (use --force)." >&2
  exit 1
fi

# Resolve the skillcook version (git short SHA of this checkout, or "unknown").
cooked_version="$(cd "$skill_root" && git rev-parse --short HEAD 2>/dev/null || echo unknown)"

# Substitute placeholders in template, write to target.
sed -e "s/{{NAME}}/$skill_name/g" \
    -e "s/{{COOKED_WITH_VERSION}}/$cooked_version/g" \
    "$template_skill" > "$skill_md"

evals_json="$target/evals/evals.json"
if [[ ! -s "$evals_json" || $force -eq 1 ]]; then
  sed "s/{{NAME}}/$skill_name/g" "$template_evals" > "$evals_json"
fi

cat <<EOF
Scaffolded skill at: $target
Files written:
  $skill_md
  $evals_json
Next:
  1. Edit SKILL.md — fill in description and body.
  2. Run: uv run $skill_root/scripts/validate.py $target
EOF
