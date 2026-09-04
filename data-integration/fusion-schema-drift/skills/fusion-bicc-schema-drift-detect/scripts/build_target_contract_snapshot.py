#!/usr/bin/env python3
"""Build a target-contract schema snapshot from ODT metadata export CSV.

The output JSON is used by `detect_schema_drift.py` in `target_contract` or
`combined` mode to detect compatibility issues before load execution.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def as_bool(raw: str, default: bool = False) -> bool:
    """Parse common truthy/falsy tokens from CSV metadata fields."""
    if raw is None:
        return default
    normalized = str(raw).strip().lower()
    if normalized in {"1", "y", "yes", "true", "t"}:
        return True
    if normalized in {"0", "n", "no", "false", "f"}:
        return False
    return default


def normalize_type(raw_type: str) -> str:
    """Normalize source-specific type labels to coarse logical classes."""
    t = (raw_type or "string").strip().lower()
    if any(token in t for token in ["number", "decimal", "int", "float", "double"]):
        return "number"
    if "timestamp" in t:
        return "timestamp"
    if "date" in t:
        return "date"
    if "bool" in t:
        return "boolean"
    return "string"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ODT target contract snapshot")
    parser.add_argument("--input-csv", required=True, help="ODT metadata export CSV")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--object-column", default="object_name", help="CSV object column name")
    parser.add_argument("--column-column", default="column_name", help="CSV column name column")
    parser.add_argument("--type-column", default="data_type", help="CSV datatype column")
    parser.add_argument("--nullable-column", default="nullable", help="CSV nullable flag column")
    parser.add_argument(
        "--required-column",
        default="required",
        help="CSV required flag column (if missing, derived from nullable)",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv)
    output = Path(args.output)
    if not input_csv.exists():
        raise SystemExit(f"Input CSV not found: {input_csv}")

    objects: Dict[str, Dict] = {}
    with input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            object_name = (row.get(args.object_column) or "").strip()
            column_name = (row.get(args.column_column) or "").strip()
            if not object_name or not column_name:
                # Skip malformed metadata rows while allowing partial extracts.
                continue

            data_type = normalize_type(row.get(args.type_column, "string"))
            nullable = as_bool(row.get(args.nullable_column, "true"), default=True)
            required_raw = row.get(args.required_column)
            required = as_bool(required_raw, default=not nullable)

            entry = objects.setdefault(object_name, {"columns": []})
            entry["columns"].append(
                {
                    "name": column_name,
                    "type": data_type,
                    "nullable": nullable,
                    "required": required,
                }
            )

    snapshot = {
        "snapshot_type": "target_contract",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_input_csv": str(input_csv),
        "object_count": len(objects),
        "objects": objects,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Target contract snapshot written: {output}")


if __name__ == "__main__":
    main()
