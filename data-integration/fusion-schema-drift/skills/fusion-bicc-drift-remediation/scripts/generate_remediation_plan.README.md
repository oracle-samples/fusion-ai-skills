# generate_remediation_plan.py

Builds a single remediation plan from one or more drift reports.

## Required output args

- `--output-json`: machine-readable plan
- `--output-md`: markdown runbook

## Optional input args

- `--schema-report`: schema drift report JSON
- `--data-report`: data drift report JSON
- `--policy`: remediation policy YAML/JSON

At least one report (`--schema-report` or `--data-report`) is required.

## What it adds

- critical-first prioritization
- owner assignment by drift type
- release decision suggestion (`block|warn|proceed`)
- normalized action IDs for traceability
