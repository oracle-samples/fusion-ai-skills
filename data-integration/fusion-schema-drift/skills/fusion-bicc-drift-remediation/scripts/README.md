# Scripts - fusion-bicc-drift-remediation

This folder contains scripts to convert drift findings into executable remediation plans.

## 1) generate_remediation_plan.py

Combines schema/data drift reports into a critical-first action queue.

### Inputs

- `--schema-report` (optional)
- `--data-report` (optional)
- `--policy` (optional)

At least one report is required.

### Outputs

- `--output-json`: consolidated remediation plan
- `--output-md`: markdown runbook with critical action section

## 2) run_drift_pipeline.sh

Runs the full workflow:

1. schema snapshots
2. optional ODT target contract snapshot
3. schema drift report
4. data profile snapshots
5. data drift report
6. remediation plan
