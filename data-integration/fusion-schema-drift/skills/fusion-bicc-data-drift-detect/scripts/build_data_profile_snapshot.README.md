# build_data_profile_snapshot.py

Generates a baseline/current **data profile snapshot** from BICC CSV extracts.

## What it captures

- object row counts
- per-column null counts/ratios
- distinct counts
- numeric stats (`min`, `max`, `mean`)
- top categorical values for domain-shift checks

## Required arguments

- `--input-dir`: directory with input CSV files
- `--output`: output JSON path

## Optional arguments

- `--sample-rows`: maximum rows sampled per object
- `--top-n`: number of top values per column
- `--key-pattern`: regex for key-like columns
