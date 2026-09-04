#!/usr/bin/env bash
# Run full synthetic test matrix and emit JSON + HTML run report.
#
# Includes:
# - passing schema/data/remediation scenarios
# - expected-fail schema and data scenarios
# - command-by-command captured output and exit codes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACK_ROOT="$REPO_ROOT/test-pack"

SCHEMA_OUT="$PACK_ROOT/output/schema"
DATA_OUT="$PACK_ROOT/output/data"
REMEDIATION_OUT="$PACK_ROOT/output/remediation"

RUN_RESULTS_DIR="$PACK_ROOT/run-results"
RAW_LOG="$RUN_RESULTS_DIR/commands-and-output.log"
SUMMARY_NDJSON="$RUN_RESULTS_DIR/run-summary.ndjson"
SUMMARY_JSON="$RUN_RESULTS_DIR/run-summary.json"
HTML_REPORT="$RUN_RESULTS_DIR/TEST_RUN_RESULTS.html"

# User requested removal of existing results.
rm -rf "$RUN_RESULTS_DIR"
mkdir -p "$RUN_RESULTS_DIR" "$REMEDIATION_OUT"
: > "$RAW_LOG"
: > "$SUMMARY_NDJSON"

OVERALL_RC=0

run_case() {
  local case_name="$1"
  local expected_fail="$2" # yes/no
  local cmd="$3"
  local out_file
  local start_ts
  local end_ts
  local ec
  local status
  local notes

  out_file="$(mktemp)"
  start_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  {
    echo "--------------------------------------------------------------------------------"
    echo "CASE: $case_name"
    echo "EXPECTED_FAIL: $expected_fail"
    echo "COMMAND: $cmd"
    echo "START: $start_ts"
  } | tee -a "$RAW_LOG"

  set +e
  bash -lc "$cmd" >"$out_file" 2>&1
  ec=$?
  set -e

  cat "$out_file" | tee -a "$RAW_LOG"

  if [[ "$expected_fail" == "yes" ]]; then
    if [[ $ec -ne 0 ]]; then
      status="EXPECTED_FAIL"
      notes="Failure observed as expected for negative test scenario."
    else
      status="UNEXPECTED_PASS"
      notes="Scenario was expected to fail but command succeeded."
      OVERALL_RC=1
    fi
  else
    if [[ $ec -eq 0 ]]; then
      status="PASS"
      notes="Scenario succeeded."
    else
      status="FAIL"
      notes="Scenario failed unexpectedly."
      OVERALL_RC=1
    fi
  fi

  end_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  {
    echo "RESULT: $status"
    echo "EXIT_CODE: $ec"
    echo "END: $end_ts"
    echo
  } | tee -a "$RAW_LOG"

  python3 - "$SUMMARY_NDJSON" "$case_name" "$expected_fail" "$status" "$ec" "$start_ts" "$end_ts" "$cmd" "$notes" "$out_file" <<'PY'
import json
import pathlib
import sys

summary_path = pathlib.Path(sys.argv[1])
case_name = sys.argv[2]
expected_fail = sys.argv[3]
status = sys.argv[4]
exit_code = int(sys.argv[5])
start_ts = sys.argv[6]
end_ts = sys.argv[7]
command = sys.argv[8]
notes = sys.argv[9]
output_path = pathlib.Path(sys.argv[10])

payload = {
    "case": case_name,
    "expected_fail": expected_fail == "yes",
    "status": status,
    "exit_code": exit_code,
    "start": start_ts,
    "end": end_ts,
    "command": command,
    "notes": notes,
    "output": output_path.read_text(encoding="utf-8", errors="replace"),
}

with summary_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(payload) + "\n")
PY

  rm -f "$out_file"
}

PLAN_JSON="$REMEDIATION_OUT/remediation_plan.json"
PLAN_MD="$REMEDIATION_OUT/remediation_plan.md"

run_case "schema-pass" "no" "bash '$PACK_ROOT/scripts/run_schema_drift_test.sh'"
run_case "data-pass" "no" "bash '$PACK_ROOT/scripts/run_data_drift_test.sh'"

run_case "remediation-pass" "no" \
  "python3 '$REPO_ROOT/skills/fusion-bicc-drift-remediation/scripts/generate_remediation_plan.py' \
    --schema-report '$SCHEMA_OUT/schema_drift_report.json' \
    --data-report '$DATA_OUT/data_drift_report.json' \
    --policy '$PACK_ROOT/policies/remediation_policy.json' \
    --output-json '$PLAN_JSON' \
    --output-md '$PLAN_MD' \
    && python3 '$PACK_ROOT/scripts/assert_reports.py' --scenario remediation --report '$PLAN_JSON' --expected '$PACK_ROOT/expected/remediation_plan.json'"

SCHEMA_FAIL_DIR="$PACK_ROOT/output/schema-fail"
mkdir -p "$SCHEMA_FAIL_DIR"
SCHEMA_FAIL_BASELINE="$SCHEMA_FAIL_DIR/baseline_schema_snapshot.json"
SCHEMA_FAIL_CURRENT="$SCHEMA_FAIL_DIR/current_schema_snapshot.json"
SCHEMA_FAIL_REPORT="$SCHEMA_FAIL_DIR/schema_drift_report.json"
SCHEMA_FAIL_MD="$SCHEMA_FAIL_DIR/schema_drift_report.md"

run_case "schema-expected-fail" "yes" \
  "python3 '$REPO_ROOT/skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py' --input-dir '$PACK_ROOT/inputs/baseline' --output '$SCHEMA_FAIL_BASELINE' \
    && python3 '$REPO_ROOT/skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py' --input-dir '$PACK_ROOT/inputs/baseline' --output '$SCHEMA_FAIL_CURRENT' \
    && python3 '$REPO_ROOT/skills/fusion-bicc-schema-drift-detect/scripts/detect_schema_drift.py' --mode source_drift --baseline '$SCHEMA_FAIL_BASELINE' --current '$SCHEMA_FAIL_CURRENT' --policy '$PACK_ROOT/policies/schema_policy.json' --output-json '$SCHEMA_FAIL_REPORT' --output-md '$SCHEMA_FAIL_MD' \
    && python3 '$PACK_ROOT/scripts/assert_reports.py' --scenario schema --report '$SCHEMA_FAIL_REPORT'"

DATA_FAIL_DIR="$PACK_ROOT/output/data-fail"
mkdir -p "$DATA_FAIL_DIR"
DATA_FAIL_BASELINE="$DATA_FAIL_DIR/baseline_data_profile.json"
DATA_FAIL_CURRENT="$DATA_FAIL_DIR/current_data_profile.json"
DATA_FAIL_REPORT="$DATA_FAIL_DIR/data_drift_report.json"
DATA_FAIL_MD="$DATA_FAIL_DIR/data_drift_report.md"

run_case "data-expected-fail" "yes" \
  "python3 '$REPO_ROOT/skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py' --input-dir '$PACK_ROOT/inputs/baseline' --output '$DATA_FAIL_BASELINE' \
    && python3 '$REPO_ROOT/skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py' --input-dir '$PACK_ROOT/inputs/baseline' --output '$DATA_FAIL_CURRENT' \
    && python3 '$REPO_ROOT/skills/fusion-bicc-data-drift-detect/scripts/detect_data_drift.py' --baseline '$DATA_FAIL_BASELINE' --current '$DATA_FAIL_CURRENT' --policy '$PACK_ROOT/policies/data_policy.json' --output-json '$DATA_FAIL_REPORT' --output-md '$DATA_FAIL_MD' \
    && python3 '$PACK_ROOT/scripts/assert_reports.py' --scenario data --report '$DATA_FAIL_REPORT'"

python3 - "$SUMMARY_NDJSON" "$SUMMARY_JSON" "$HTML_REPORT" <<'PY'
import html
import json
import pathlib
import sys
from datetime import datetime, timezone

ndjson_path = pathlib.Path(sys.argv[1])
summary_json_path = pathlib.Path(sys.argv[2])
html_path = pathlib.Path(sys.argv[3])

results = []
if ndjson_path.exists():
    for line in ndjson_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            results.append(json.loads(line))

status_counts = {}
for row in results:
    status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "summary": {
        "total_cases": len(results),
        "status_counts": status_counts,
    },
    "results": results,
}
summary_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

rows = []
for row in results:
    rows.append(
        f"<tr>"
        f"<td>{html.escape(row['case'])}</td>"
        f"<td>{'yes' if row.get('expected_fail') else 'no'}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{row['exit_code']}</td>"
        f"<td><pre>{html.escape(row['command'])}</pre></td>"
        f"<td><pre>{html.escape(row['output'])}</pre></td>"
        f"</tr>"
    )

status_items = "".join(
    f"<li><strong>{html.escape(k)}</strong>: {v}</li>" for k, v in sorted(status_counts.items())
)

doc = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Test Pack Run Results</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ background: #f5f5f5; }}
    pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; }}
  </style>
</head>
<body>
  <h1>Test Pack Run Results</h1>
  <p><strong>Generated at:</strong> {html.escape(payload['generated_at'])}</p>
  <h2>Summary</h2>
  <ul>
    <li><strong>Total cases:</strong> {payload['summary']['total_cases']}</li>
    {status_items}
  </ul>
  <h2>Command Results</h2>
  <table>
    <thead>
      <tr>
        <th>Case</th>
        <th>Expected Fail</th>
        <th>Status</th>
        <th>Exit Code</th>
        <th>Command</th>
        <th>Output</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""

html_path.write_text(doc, encoding="utf-8")
PY

rm -f "$SUMMARY_NDJSON"

echo "Run result artifacts:"
echo "- $RAW_LOG"
echo "- $SUMMARY_JSON"
echo "- $HTML_REPORT"

if [[ $OVERALL_RC -ne 0 ]]; then
  echo "One or more cases did not match expected outcome." >&2
fi

exit $OVERALL_RC
