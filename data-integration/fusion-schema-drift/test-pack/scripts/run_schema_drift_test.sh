#!/usr/bin/env bash
# Run schema drift synthetic scenario and assert expected behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACK_ROOT="$REPO_ROOT/test-pack"

OUT_DIR="$PACK_ROOT/output/schema"
mkdir -p "$OUT_DIR"

BASELINE_SCHEMA="$OUT_DIR/baseline_schema_snapshot.json"
CURRENT_SCHEMA="$OUT_DIR/current_schema_snapshot.json"
TARGET_SCHEMA="$OUT_DIR/odt_target_contract_snapshot.json"
REPORT_JSON="$OUT_DIR/schema_drift_report.json"
REPORT_MD="$OUT_DIR/schema_drift_report.md"

python3 "$REPO_ROOT/skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py" \
  --input-dir "$PACK_ROOT/inputs/baseline" \
  --output "$BASELINE_SCHEMA"

python3 "$REPO_ROOT/skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py" \
  --input-dir "$PACK_ROOT/inputs/current-schema-drift" \
  --output "$CURRENT_SCHEMA"

python3 "$REPO_ROOT/skills/fusion-bicc-schema-drift-detect/scripts/build_target_contract_snapshot.py" \
  --input-csv "$PACK_ROOT/inputs/odt-target-contract/odt_schema_export.csv" \
  --output "$TARGET_SCHEMA"

python3 "$REPO_ROOT/skills/fusion-bicc-schema-drift-detect/scripts/detect_schema_drift.py" \
  --mode combined \
  --baseline "$BASELINE_SCHEMA" \
  --current "$CURRENT_SCHEMA" \
  --target-contract "$TARGET_SCHEMA" \
  --policy "$PACK_ROOT/policies/schema_policy.json" \
  --output-json "$REPORT_JSON" \
  --output-md "$REPORT_MD"

ASSERT_ARGS=(
  --scenario schema
  --report "$REPORT_JSON"
)

if [[ -f "$PACK_ROOT/expected/schema_drift_report.json" ]]; then
  ASSERT_ARGS+=(--expected "$PACK_ROOT/expected/schema_drift_report.json")
fi

python3 "$PACK_ROOT/scripts/assert_reports.py" "${ASSERT_ARGS[@]}"

echo "PASS: schema drift synthetic test"
