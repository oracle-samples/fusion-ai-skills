#!/usr/bin/env bash
# Run data drift synthetic scenario and assert expected behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACK_ROOT="$REPO_ROOT/test-pack"

OUT_DIR="$PACK_ROOT/output/data"
mkdir -p "$OUT_DIR"

BASELINE_PROFILE="$OUT_DIR/baseline_data_profile.json"
CURRENT_PROFILE="$OUT_DIR/current_data_profile.json"
REPORT_JSON="$OUT_DIR/data_drift_report.json"
REPORT_MD="$OUT_DIR/data_drift_report.md"

python3 "$REPO_ROOT/skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py" \
  --input-dir "$PACK_ROOT/inputs/baseline" \
  --output "$BASELINE_PROFILE"

python3 "$REPO_ROOT/skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py" \
  --input-dir "$PACK_ROOT/inputs/current-data-drift" \
  --output "$CURRENT_PROFILE"

python3 "$REPO_ROOT/skills/fusion-bicc-data-drift-detect/scripts/detect_data_drift.py" \
  --baseline "$BASELINE_PROFILE" \
  --current "$CURRENT_PROFILE" \
  --policy "$PACK_ROOT/policies/data_policy.json" \
  --output-json "$REPORT_JSON" \
  --output-md "$REPORT_MD"

ASSERT_ARGS=(
  --scenario data
  --report "$REPORT_JSON"
)

if [[ -f "$PACK_ROOT/expected/data_drift_report.json" ]]; then
  ASSERT_ARGS+=(--expected "$PACK_ROOT/expected/data_drift_report.json")
fi

python3 "$PACK_ROOT/scripts/assert_reports.py" "${ASSERT_ARGS[@]}"

echo "PASS: data drift synthetic test"
