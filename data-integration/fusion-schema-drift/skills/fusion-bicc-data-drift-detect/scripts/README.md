# Scripts - fusion-bicc-data-drift-detect

This folder contains the data profiling and data drift detection executables.

## 1) build_data_profile_snapshot.py

Builds a canonical profile snapshot from BICC CSV extracts.

### Output highlights

- row counts per object
- null ratios per column
- distinct counts per column
- numeric metrics (`min`, `max`, `mean`) where applicable
- top categorical values

## 2) detect_data_drift.py

Compares baseline and current profile snapshots and emits:

- severity-rated findings (`critical/high/medium/low/info`)
- business/pipeline impact
- recommended remediation action
- markdown report with **Critical Findings & Immediate Actions**
