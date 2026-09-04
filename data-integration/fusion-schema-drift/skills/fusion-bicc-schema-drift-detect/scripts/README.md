# Scripts - fusion-bicc-schema-drift-detect

This folder contains the executable scripts used by the schema drift skill.

## 1) build_schema_snapshot.py

Builds a canonical **schema snapshot JSON** from BICC CSV extracts.

### Inputs

- `--input-dir`: directory containing object CSV files.
- `--sample-rows` (optional): rows sampled per CSV for type/nullability inference.
- `--key-pattern` (optional): regex to mark key-like columns.

### Outputs

- `--output`: JSON schema snapshot with per-object column definitions.

### Example

```bash
python skills/fusion-bicc-schema-drift-detect/scripts/build_schema_snapshot.py \
  --input-dir ./inputs/current \
  --output ./outputs/current_schema_snapshot.json
```

---

## 2) build_target_contract_snapshot.py

Builds an ODT target schema contract snapshot from metadata CSV export.

### Inputs

- `--input-csv`: ODT schema export.
- Column mapping flags if your CSV headers differ from defaults.

### Outputs

- `--output`: JSON target contract snapshot.

### Example

```bash
python skills/fusion-bicc-schema-drift-detect/scripts/build_target_contract_snapshot.py \
  --input-csv ./inputs/odt_schema_export.csv \
  --output ./outputs/odt_target_contract_snapshot.json
```

---

## 3) detect_schema_drift.py

Compares snapshots and emits severity-rated findings with remediation guidance.

### Inputs

- `--mode`: `source_drift`, `target_contract`, or `combined`.
- `--baseline` for source comparisons.
- `--current` for current extraction snapshot.
- `--target-contract` for target mode.
- `--policy`: YAML/JSON policy with severity and transition rules.

### Outputs

- `--output-json`: structured report (`schema_drift_report.json`).
- `--output-md`: human-readable report (`schema_drift_report.md`).

### Example

```bash
python skills/fusion-bicc-schema-drift-detect/scripts/detect_schema_drift.py \
  --mode combined \
  --baseline ./outputs/baseline_schema_snapshot.json \
  --current ./outputs/current_schema_snapshot.json \
  --target-contract ./outputs/odt_target_contract_snapshot.json \
  --policy skills/fusion-bicc-schema-drift-detect/assets/drift_policy.yaml \
  --output-json ./outputs/schema_drift_report.json \
  --output-md ./outputs/schema_drift_report.md
```
