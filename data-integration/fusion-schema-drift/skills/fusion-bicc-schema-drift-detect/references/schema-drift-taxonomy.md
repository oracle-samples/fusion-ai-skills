# Schema Drift Taxonomy for Fusion BICC

This reference defines drift types detected by the schema skill and how severity is interpreted.

## Drift types

- `object_removed`: A previously extracted object/PVO file no longer exists.
- `object_added`: A new extracted object/PVO file appears.
- `column_removed`: Existing column is no longer present.
- `column_added`: New column appears.
- `column_type_changed`: Datatype transition between baseline and current.
- `column_nullability_relaxed`: Column changed from non-null to nullable in extracts.
- `column_nullability_tightened`: Column changed from nullable to non-null in extracts.

## Severity guidance

- `critical`: Immediate pipeline break or data contract violation likely.
- `high`: Significant transformation or semantic risk.
- `medium`: Manageable change requiring review.
- `low`: Minimal risk, usually additive.
- `info`: Informational observation.

## Critical criteria examples

- Key columns removed.
- Type change from numeric/date to string on key measures.
- Required target-contract columns missing.
