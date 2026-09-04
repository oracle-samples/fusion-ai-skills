# detect_data_drift.py

Detects **data living in the schema** drift by comparing baseline and current data profile snapshots.

## Required inputs

- `--baseline`: baseline profile snapshot JSON
- `--current`: current profile snapshot JSON
- `--output-json`: structured drift report output
- `--output-md`: markdown drift report output

## Optional input

- `--policy`: YAML/JSON thresholds and severity rules

## Drift checks included

- object missing/new detection
- row count drop thresholds
- null ratio increase thresholds
- distinct cardinality shift thresholds
- numeric mean shift thresholds
- categorical top-value overlap shift

## Output highlights

- per-finding `severity` (`critical/high/medium/low/info`)
- `recommended_action`
- `business_impact` and `pipeline_impact`
- critical-first markdown summary section
