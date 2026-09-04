# build_target_contract_snapshot.py

Builds a normalized ODT target schema contract snapshot from CSV metadata export.

## Purpose

- Convert ODT repository metadata export to canonical JSON contract.
- Enable snapshot vs ODT target comparison in `target_contract` mode.

## Inputs

- `--input-csv` (required): metadata CSV exported from ODT target schema model.
- `--output` (required): output JSON path.
- Optional header mapping flags:
  - `--object-column`
  - `--column-column`
  - `--type-column`
  - `--nullable-column`
  - `--required-column`

## Output

`target_contract_snapshot.json` with per-object column definitions (`type`, `nullable`, `required`).
