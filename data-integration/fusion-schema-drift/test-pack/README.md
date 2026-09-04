# Fusion Schema Drift Test Pack

This test pack validates the skill library using **synthetic inputs and synthetic expected outputs**.

> Important: this pack is intentionally outside `skills/` as requested.

## Folder layout

- `inputs/` synthetic datasets (baseline, schema-drift current, data-drift current, ODT contract)
- `scripts/` test runners, assertions, and expected-output refresh script
- `expected/` deterministic script outputs representing baseline snapshots, schema drift, data drift, and remediation
- `output/` runtime outputs generated during test execution

## Prerequisites

- `python3`

The test pack uses JSON policy files, so no additional Python packages are required.

## Scenarios

1. **Schema drift scenario**
   - Removed key-like column (`INVOICE_ID`)
   - Type break (`AMOUNT` number -> string)
   - ODT target contract mismatches

2. **Data drift scenario**
   - Row-count collapse (>50% drop)
   - Null ratio spike on required-like field (`SUPPLIER_ID`)
   - Numeric distribution shift (`AMOUNT`)

3. **Combined remediation scenario**
   - Combines schema + data drift reports
   - Verifies critical-first remediation plan

## Run tests

From repository root:

```bash
bash test-pack/scripts/run_schema_drift_test.sh
bash test-pack/scripts/run_data_drift_test.sh
bash test-pack/scripts/run_combined_remediation_test.sh
```

If all checks pass, scripts print `PASS`.

## Refresh synthetic expected outputs

If you intentionally change drift logic and want to regenerate expected outputs:

```bash
bash test-pack/scripts/refresh_expected_outputs.sh
```

Then rerun the tests to validate consistency.
