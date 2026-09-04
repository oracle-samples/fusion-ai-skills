---
name: fusion-bicc-data-drift-detect
description: Detect data drift within Oracle Fusion BICC extracted objects by comparing profile snapshots over time and rate findings with criticality and remediation guidance.
compatibility: Requires Python 3.10+; optional PyYAML for YAML policy files; CSV input and JSON outputs.
metadata:
  author: fusion-data-architecture
  version: "1.0.0"
allowed-tools: Bash(python:*) Read Write
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Fusion BICC Data Drift Detection

Use this skill when schema appears stable but data behavior changes across extraction windows and can impact KPIs, model quality, or ODT load quality.

## When to use

- Null rates spike after a Fusion release.
- Distinct cardinality unexpectedly collapses or expands.
- Measure ranges/means shift materially.
- You need severity-rated drift findings with remediation actions.

## Inputs

- Baseline and current BICC CSV extracts.
- Data drift policy (`assets/data_drift_policy.yaml`).

## Workflow

1. Build baseline data profile snapshot from known-good extraction window.
2. Build current data profile snapshot for the latest run.
3. Run drift detection with policy thresholds.
4. Review critical findings and associated remediation in report outputs.

## Commands

```bash
# 1) Build profile snapshots
python skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py \
  --input-dir ./inputs/baseline \
  --output ./outputs/baseline_data_profile.json

python skills/fusion-bicc-data-drift-detect/scripts/build_data_profile_snapshot.py \
  --input-dir ./inputs/current \
  --output ./outputs/current_data_profile.json

# 2) Detect data drift
python skills/fusion-bicc-data-drift-detect/scripts/detect_data_drift.py \
  --baseline ./outputs/baseline_data_profile.json \
  --current ./outputs/current_data_profile.json \
  --policy skills/fusion-bicc-data-drift-detect/assets/data_drift_policy.yaml \
  --output-json ./outputs/data_drift_report.json \
  --output-md ./outputs/data_drift_report.md
```

## Outputs

- `data_drift_report.json`
- `data_drift_report.md`

## Critical examples

- Required field null ratio exceeds critical threshold.
- Row count drops below expected freshness/completeness threshold.
- Categorical domain shifts beyond policy tolerance.

See `references/data-drift-metrics.md` and `references/severity-model.md`.