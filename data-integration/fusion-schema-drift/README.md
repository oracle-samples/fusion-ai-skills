# Fusion Schema Drift

This repository contains an **Agent Skills-compliant** library for detecting and remediating schema and data drift in Oracle Fusion extraction pipelines that feed Data Transforms and AI DP.

## What this library delivers

- Baseline and current **schema snapshots** (JSON canonical format)
- Baseline and current **data profile snapshots** (JSON canonical format)
- Drift detection with severity ratings (`critical`, `high`, `medium`, `low`, `info`)
- Remediation plan generation prioritized by critical findings
- Optional contract checks against the **ODT target database schema contract**

## Comparison modes

1. `source_drift`: snapshot vs snapshot (baseline BICC vs current BICC)
2. `target_contract`: current snapshot vs ODT target schema contract
3. `combined`: runs both modes and merges findings in the remediation plan

## Format convention

- **Input extracts:** CSV (from BICC output)
- **Canonical snapshots + drift reports:** JSON
- **Optional summary output:** Markdown (human review)

## Skills included

- `skills/fusion-bicc-schema-drift-detect`
- `skills/fusion-bicc-data-drift-detect`
- `skills/fusion-bicc-drift-remediation`

See each skill's `SKILL.md` and `scripts/README.md` for usage examples.