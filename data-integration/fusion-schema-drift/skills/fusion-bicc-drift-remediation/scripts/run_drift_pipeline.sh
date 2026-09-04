#!/usr/bin/env bash
# End-to-end wrapper for Fusion BICC drift workflow.
#
# Runs:
# 1) schema snapshot baseline/current
# 2) optional target contract snapshot
# 3) schema drift detection
# 4) data profile baseline/current
# 5) data drift detection
# 6) remediation plan generation

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_drift_pipeline.sh \
    --baseline-dir <path> \
    --current-dir <path> \
    --out-dir <path> \
    [--target-contract-csv <path>] \
    [--schema-policy <path>] \
    [--data-policy <path>] \
    [--remediation-policy <path>]

Notes:
  - If --target-contract-csv is provided, schema mode runs in `combined`.
  - Otherwise schema mode runs in `source_drift`.
USAGE
}

BASELINE_DIR=""
CURRENT_DIR=""
OUT_DIR=""
TARGET_CONTRACT_CSV=""
SCHEMA_POLICY="skills/fusion-bicc-schema-drift-detect/assets/drift_policy.yaml"
DATA_POLICY="skills/fusion-bicc-data-drift-detect/assets/data_drift_policy.yaml"
REMEDIATION_POLICY="skills/fusion-bicc-drift-remediation/assets/remediation_policy.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --baseline-dir)
      BASELINE_DIR="$2"; shift 2 ;;
    --current-dir)
      CURRENT_DIR="$2"; shift 2 ;;
    --out-dir)
      OUT_DIR="$2"; shift 2 ;;
    --target-contract-csv)
      TARGET_CONTRACT_CSV="$2"; shift 2 ;;
    --schema-policy)
      SCHEMA_POLICY="$2"; shift 2 ;;
    --data-policy)
      DATA_POLICY="$2"; shift 2 ;;
    --remediation-policy)
      REMEDIATION_POLICY="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1 ;;
  esac
done

if [[ -z "$BASELINE_DIR" || -z "$CURRENT_DIR" || -z "$OUT_DIR" ]]; then
  echo "Missing required arguments." >&2
  usage
  exit 1
fi

mkdir -p "$OUT_DIR"

BASELINE_SCHEMA="$OUT_DIR/baseline_schema_snapshot.json"
CURRENT_SCHEMA="$OUT_DIR/current_schema_snapshot.json"
TARGET_SCHEMA="$OUT_DIR/odt_target_contract_snapshot.json"
SCHEMA_REPORT_JSON="$OUT_DIR/schema_drift_report.json"
SCHEMA_REPORT_MD="$OUT_DIR/schema_drift_report.md"

BASELINE_PROFILE="$OUT_DIR/baseline_data_profile.json"
CURRENT_PROFILE="$OUT_DIR/current_data_profile.json"
DATA_REPORT_JSON="$OUT_DIR/data_drift_report.json"
DATA_REPORT_MD="$OUT_DIR/data_drift_report.md"

REMEDIATION_PLAN_JSON="$OUT_DIR/remediation_plan.json"
REMEDIATION_PLAN_MD="$OUT_DIR/remediation_plan.md"

echo "[1/6] Building schema snapshots..."
python skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py \
  --input-dir "$BASELINE_DIR" \
  --output "$BASELINE_SCHEMA"

python skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py \
  --input-dir "$CURRENT_DIR" \
  --output "$CURRENT_SCHEMA"

SCHEMA_MODE="source_drift"
SCHEMA_EXTRA_ARGS=()

if [[ -n "$TARGET_CONTRACT_CSV" ]]; then
  echo "[2/6] Building target contract snapshot..."
  python skills/fusion-bicc-schema-drift-detect/scripts/build_target_contract_snapshot.py \
    --input-csv "$TARGET_CONTRACT_CSV" \
    --output "$TARGET_SCHEMA"

  SCHEMA_MODE="combined"
  SCHEMA_EXTRA_ARGS+=(--target-contract "$TARGET_SCHEMA")
else
  echo "[2/6] Skipping target contract snapshot (not provided)."
fi

echo "[3/6] Detecting schema drift (${SCHEMA_MODE})..."
python skills/fusion-bicc-schema-drift-detect/scripts/detect_schema_drift.py \
  --mode "$SCHEMA_MODE" \
  --baseline "$BASELINE_SCHEMA" \
  --current "$CURRENT_SCHEMA" \
  --policy "$SCHEMA_POLICY" \
  --output-json "$SCHEMA_REPORT_JSON" \
  --output-md "$SCHEMA_REPORT_MD" \
  "${SCHEMA_EXTRA_ARGS[@]}"

echo "[4/6] Building data profile snapshots..."
python skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py \
  --input-dir "$BASELINE_DIR" \
  --output "$BASELINE_PROFILE"

python skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py \
  --input-dir "$CURRENT_DIR" \
  --output "$CURRENT_PROFILE"

echo "[5/6] Detecting data drift..."
python skills/fusion-bicc-data-drift-detect/scripts/detect_data_drift.py \
  --baseline "$BASELINE_PROFILE" \
  --current "$CURRENT_PROFILE" \
  --policy "$DATA_POLICY" \
  --output-json "$DATA_REPORT_JSON" \
  --output-md "$DATA_REPORT_MD"

echo "[6/6] Generating remediation plan..."
python skills/fusion-bicc-drift-remediation/scripts/generate_remediation_plan.py \
  --schema-report "$SCHEMA_REPORT_JSON" \
  --data-report "$DATA_REPORT_JSON" \
  --policy "$REMEDIATION_POLICY" \
  --output-json "$REMEDIATION_PLAN_JSON" \
  --output-md "$REMEDIATION_PLAN_MD"

echo "Drift pipeline completed. Outputs in: $OUT_DIR"
