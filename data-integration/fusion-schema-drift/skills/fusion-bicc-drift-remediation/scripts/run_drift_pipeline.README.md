# run_drift_pipeline.sh

Runs the full Fusion Schema Drift workflow from snapshots through remediation.

## Required arguments

- `--baseline-dir`: baseline extraction CSV directory
- `--current-dir`: current extraction CSV directory
- `--out-dir`: output folder for snapshots/reports/plans

## Optional arguments

- `--target-contract-csv`: ODT target schema metadata export CSV
- `--schema-policy`: schema drift policy file
- `--data-policy`: data drift policy file
- `--remediation-policy`: remediation policy file

## Behavior

- Without `--target-contract-csv`, schema comparison runs in `source_drift` mode.
- With `--target-contract-csv`, schema comparison runs in `combined` mode.

## Outputs generated

- `baseline_schema_snapshot.json`
- `current_schema_snapshot.json`
- `schema_drift_report.json` + `.md`
- `baseline_data_profile.json`
- `current_data_profile.json`
- `data_drift_report.json` + `.md`
- `remediation_plan.json` + `.md`
