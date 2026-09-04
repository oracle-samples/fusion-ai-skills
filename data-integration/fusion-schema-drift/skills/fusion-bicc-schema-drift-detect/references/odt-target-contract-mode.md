# ODT Target Contract Mode

`target_contract` mode compares the **current BICC extraction snapshot** to the schema contract expected by the ODT target database.

## Why use this mode

- Prevent load failures before Data Transforms execution.
- Detect incompatible datatype/nullability shifts early.
- Confirm required target columns are still supplied by source extracts.

## Expected target metadata export

Provide a CSV with at least:

- table/object name
- column name
- datatype
- nullable and/or required indicator

You can adapt the input using CLI flags in `build_target_contract_snapshot.py`.

## Typical critical findings

- Target-required column missing from current extraction.
- Datatype mismatch where target cannot safely coerce input.
- Entire target object contract missing from extracted set.
