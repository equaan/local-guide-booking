#!/usr/bin/env bash
# Builds one Word report from the cover, deviations register, task list and every docs/task-NN.md.
# Needs: pandoc, and `pip install -r requirements-docs.txt`.
# Usage: bash scripts/build_report.sh [output.docx]
set -euo pipefail
cd "$(dirname "$0")/.."

OUT="${1:-build/report.docx}"
mkdir -p "$(dirname "$OUT")"

FILES=(docs/00-cover.md docs/00-deviations-register.md docs/00-task-list.md)
for f in docs/task-[0-9][0-9].md; do
  [ -e "$f" ] && FILES+=("$f")
done

pandoc "${FILES[@]}" \
  --from markdown+pipe_tables+fenced_code_blocks \
  --resource-path=docs \
  -o "$OUT"

python scripts/style_docx.py "$OUT"
echo "Built $OUT from ${#FILES[@]} files. Open it in Word, review, then export to PDF."
