# build_schema_snapshot.py

Builds a schema snapshot from BICC CSV extracts.

## Purpose

- Capture per-object column contracts from CSVs.
- Infer logical types and nullability.
- Produce JSON snapshot for drift detection.

## Inputs

- `--input-dir` (required): directory containing source CSVs.
- `--output` (required): output JSON snapshot path.
- `--sample-rows` (optional): row sampling limit per object.
- `--key-pattern` (optional): regex for key-hint columns.

## Output format

```json
{
  "snapshot_type": "schema",
  "generated_at": "...",
  "objects": {
    "OBJECT_NAME": {
      "columns": [
        {"name": "COL", "type": "string", "nullable": true, "key_hint": false}
      ]
    }
  }
}
```
