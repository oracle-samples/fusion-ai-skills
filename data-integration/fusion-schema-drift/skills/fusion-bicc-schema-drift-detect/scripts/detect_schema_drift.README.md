# detect_schema_drift.py

Detects schema drift and contract mismatches, then rates each finding by severity.

## Purpose

- Compare baseline and current source snapshots (`source_drift`).
- Compare current snapshot with ODT target contract (`target_contract`).
- Support `combined` mode for both comparisons in one run.

## Inputs

- `--mode` (`source_drift|target_contract|combined`)
- `--baseline` (required for `source_drift` and `combined`)
- `--current` (required)
- `--target-contract` (required for `target_contract` and `combined`)
- `--policy` (optional YAML/JSON)

## Outputs

- `--output-json`: structured schema drift findings.
- `--output-md`: markdown summary with **Critical Findings & Immediate Actions**.

## Notes

- YAML policy parsing requires `pyyaml`; JSON policy works without extra packages.
- Findings include remediation metadata (`recommended_action`, `auto_apply_allowed`).
