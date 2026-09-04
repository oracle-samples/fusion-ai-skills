#!/usr/bin/env bash
# Regenerate expected synthetic outputs from current script behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACK_ROOT="$REPO_ROOT/test-pack"

bash "$PACK_ROOT/scripts/run_schema_drift_test.sh"
bash "$PACK_ROOT/scripts/run_data_drift_test.sh"
bash "$PACK_ROOT/scripts/run_combined_remediation_test.sh"

mkdir -p "$PACK_ROOT/expected"

cp "$PACK_ROOT/output/schema/schema_drift_report.json" "$PACK_ROOT/expected/schema_drift_report.json"
cp "$PACK_ROOT/output/schema/schema_drift_report.md" "$PACK_ROOT/expected/schema_drift_report.md"

cp "$PACK_ROOT/output/data/data_drift_report.json" "$PACK_ROOT/expected/data_drift_report.json"
cp "$PACK_ROOT/output/data/data_drift_report.md" "$PACK_ROOT/expected/data_drift_report.md"

cp "$PACK_ROOT/output/remediation/remediation_plan.json" "$PACK_ROOT/expected/remediation_plan.json"
cp "$PACK_ROOT/output/remediation/remediation_plan.md" "$PACK_ROOT/expected/remediation_plan.md"

echo "Expected outputs refreshed under $PACK_ROOT/expected"
