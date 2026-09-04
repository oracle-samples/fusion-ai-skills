# Data Drift Metrics for Fusion BICC

This guide explains the metrics used to compare baseline and current extraction windows.

## Object-level metrics

- `row_count`: Number of rows profiled per object.
- `row_count_drop_pct`: Percentage decline from baseline row count.

## Column-level metrics

- `null_ratio`: `null_count / row_count`
- `distinct_count`: Cardinality estimate from observed values.
- `distinct_ratio_change`: Relative change between baseline and current distinct count.
- `mean`, `min`, `max` (numeric columns): Used for numeric distribution shift checks.
- `top_values`: Most frequent categorical values, used for set overlap drift checks.

## Drift detection intent

- Detect regressions likely to break ODT loads or data quality SLAs.
- Detect semantic drift likely to degrade analytics and AI DP model behavior.
- Prioritize findings using critical/high/medium/low/info severity ratings.
