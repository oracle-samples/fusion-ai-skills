# Remediation Playbook

Use this playbook to move from drift detection to controlled remediation.

## Step 1: Triage by severity

1. Resolve all `critical` findings first.
2. Review `high` findings for release gating impact.
3. Plan `medium/low` into managed backlog where safe.

## Step 2: Apply remediation by drift category

- **Schema contract drifts**: update Data Transforms mappings, casts, and target model alignment.
- **Target mismatches**: align ODT target schema or source transformations.
- **Data quality drifts**: patch extraction logic, defaults, reference mappings, and validation rules.

## Step 3: Validate and re-run

After applying actions, regenerate snapshots and rerun drift checks to confirm critical findings are closed.
