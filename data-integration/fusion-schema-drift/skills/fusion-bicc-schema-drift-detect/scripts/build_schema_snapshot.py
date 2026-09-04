#!/usr/bin/env python3
"""Build a canonical schema snapshot from a directory of BICC CSV extracts.

The snapshot is JSON so downstream drift detectors can compare structures without
re-reading raw files. This script intentionally uses only the Python standard
library to keep deployment lightweight.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)


def infer_value_type(raw: str) -> str:
    """Infer a coarse Oracle-compatible logical type from a raw string value."""
    value = raw.strip()
    if value == "":
        return "null"

    lowered = value.lower()
    if lowered in {"true", "false", "y", "n", "yes", "no", "0", "1"}:
        return "boolean"

    if DATE_RE.match(value):
        return "date"
    if TIMESTAMP_RE.match(value):
        return "timestamp"

    try:
        # Decimal gives safer numeric checks than float for profile use.
        number = Decimal(value)
        return "integer" if number == number.to_integral_value() else "number"
    except Exception:
        return "string"


def merge_types(existing: Optional[str], incoming: str) -> str:
    """Merge two inferred types to a stable superset type.

    Example: integer + number => number, number + string => string.
    """
    if existing in (None, "null"):
        return incoming
    if incoming == "null":
        return existing
    if existing == incoming:
        return existing

    # Numeric widening.
    if {existing, incoming} <= {"integer", "number"}:
        return "number"

    # Date + timestamp should become timestamp.
    if {existing, incoming} <= {"date", "timestamp"}:
        return "timestamp"

    # Any mixed non-compatible types degrade to string for safe contract checks.
    return "string"


def load_csv_schema(csv_path: Path, sample_rows: int, key_pattern: re.Pattern[str]) -> Dict:
    """Read one CSV file and produce a schema object structure."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return {"row_sampled": 0, "columns": []}

        columns = [name.strip() for name in reader.fieldnames]
        inferred_types: Dict[str, Optional[str]] = {name: None for name in columns}
        nullable: Dict[str, bool] = {name: False for name in columns}
        row_sampled = 0

        for row in reader:
            row_sampled += 1
            for col in columns:
                raw = (row.get(col) or "")
                value_type = infer_value_type(raw)
                inferred_types[col] = merge_types(inferred_types[col], value_type)
                if raw.strip() == "":
                    nullable[col] = True

            if row_sampled >= sample_rows:
                break

    schema_columns: List[Dict] = []
    for idx, col in enumerate(columns, start=1):
        schema_columns.append(
            {
                "name": col,
                "position": idx,
                "type": inferred_types[col] or "string",
                "nullable": nullable[col],
                "key_hint": bool(key_pattern.search(col)),
            }
        )

    return {
        "row_sampled": row_sampled,
        "columns": schema_columns,
    }


def discover_csv_files(input_dir: Path) -> Iterable[Path]:
    """Yield CSV files recursively in deterministic order."""
    return sorted(p for p in input_dir.rglob("*.csv") if p.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(description="Build schema snapshot from CSV extracts")
    parser.add_argument("--input-dir", required=True, help="Directory containing CSV files")
    parser.add_argument("--output", required=True, help="Output JSON snapshot path")
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=5000,
        help="Maximum rows sampled per file for inference",
    )
    parser.add_argument(
        "--key-pattern",
        default=r"(_ID$|^ID$)",
        help="Regex for identifying key-like columns",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output = Path(args.output)
    key_pattern = re.compile(args.key_pattern, re.IGNORECASE)

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    objects: Dict[str, Dict] = {}
    for csv_file in discover_csv_files(input_dir):
        object_name = csv_file.stem
        objects[object_name] = load_csv_schema(csv_file, args.sample_rows, key_pattern)

    snapshot = {
        "snapshot_type": "schema",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_input_dir": str(input_dir),
        "object_count": len(objects),
        "objects": objects,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Schema snapshot written: {output}")


if __name__ == "__main__":
    main()
