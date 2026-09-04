---
name: fusion-bicc-schema-drift-detect
description: Detect schema drift in Oracle Fusion BICC extracted objects and rate findings by severity so Data Transforms and AI DP pipelines can remediate before load failures.
compatibility: Requires Python 3.10+; optional PyYAML for YAML policy files; CSV input and JSON outputs.
metadata:
  author: fusion-data-architecture
  version: "1.0.0"
allowed-tools: Bash(python:*) Read Write
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Fusion BICC Schema Drift Detection

Use this skill when you need to detect structural drift in BICC extraction outputs and, optionally, compare current extraction shape to an ODT target schema contract.

## When to use

- New quarterly Fusion update changed PVO structure.
- Data Transforms mapping started failing with missing/renamed columns.
- AI DP ingestion contracts need proactive compatibility checks.
- You need a severity-rated report with clear remediation actions.

## Inputs

- BICC CSV extracts for baseline and current runs.
- Optional ODT target schema export (CSV with table/column/type/nullability).
- Drift policy file (`assets/drift_policy.yaml`) to tune critical/high thresholds.

## Core workflow

1. Build schema snapshots from baseline and current BICC extracts.
2. (Optional) Build target schema contract snapshot from ODT metadata export.
3. Run schema drift detection in one of the modes:
   - `source_drift` (baseline vs current)
   - `target_contract` (current vs ODT contract)
   - `combined` (both)
4. Review `schema_drift_report.json`, focusing first on `critical` findings.

## Commands

```bash
# 1) Build baseline and current schema snapshots
python skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py \
  --input-dir ./inputs/baseline \
  --output ./outputs/baseline_schema_snapshot.json

python skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py \
  --input-dir ./inputs/current \
  --output ./outputs/current_schema_snapshot.json

# 2) Optional: build ODT target contract snapshot
python skills/fusion-bicc-schema-drift-detect/scripts/build_target_contract_snapshot.py \
  --input-csv ./inputs/odt_schema_export.csv \
  --output ./outputs/odt_target_contract_snapshot.json

# 3) Detect drift
python skills/fusion-bicc-schema-drift-detect/scripts/detect_schema_drift.py \
  --mode combined \
  --baseline ./outputs/baseline_schema_snapshot.json \
  --current ./outputs/current_schema_snapshot.json \
  --target-contract ./outputs/odt_target_contract_snapshot.json \
  --policy skills/fusion-bicc-schema-drift-detect/assets/drift_policy.yaml \
  --output-json ./outputs/schema_drift_report.json \
  --output-md ./outputs/schema_drift_report.md
```

## Output

- `schema_drift_report.json`: structured findings with severity and remediation.
- `schema_drift_report.md`: human-readable summary with critical-first ordering.

## Critical examples

- Required column removed.
- Breaking datatype change for key/measure fields.
- Current extraction incompatible with ODT target column datatype/nullability.

See `references/schema-drift-taxonomy.md` and `references/odt-target-contract-mode.md` for domain guidance.