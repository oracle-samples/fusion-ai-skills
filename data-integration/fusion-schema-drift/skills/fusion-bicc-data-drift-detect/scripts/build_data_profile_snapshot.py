#!/usr/bin/env python3
"""Build a canonical data profile snapshot from BICC CSV extracts.

The output snapshot is used for baseline-vs-current data drift detection and
includes object-level and column-level profile metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)


def infer_value_type(raw: str) -> str:
    """Infer a coarse logical data type from a raw CSV string value."""
    v = raw.strip()
    if v == "":
        return "null"
    lv = v.lower()
    if lv in {"true", "false", "y", "n", "yes", "no", "0", "1"}:
        return "boolean"
    if DATE_RE.match(v):
        return "date"
    if TIMESTAMP_RE.match(v):
        return "timestamp"
    try:
        d = Decimal(v)
        return "integer" if d == d.to_integral_value() else "number"
    except Exception:
        return "string"


def merge_types(existing: Optional[str], incoming: str) -> str:
    """Merge two inferred types into one stable profile type."""
    if existing in (None, "null"):
        return incoming
    if incoming == "null" or incoming == existing:
        return existing
    if {existing, incoming} <= {"integer", "number"}:
        return "number"
    if {existing, incoming} <= {"date", "timestamp"}:
        return "timestamp"
    return "string"


def discover_csv_files(input_dir: Path) -> Iterable[Path]:
    """Yield CSV files recursively in a deterministic order."""
    return sorted(p for p in input_dir.rglob("*.csv") if p.is_file())


def profile_csv(
    csv_path: Path,
    sample_rows: int,
    top_n: int,
    key_pattern: re.Pattern[str],
) -> Dict:
    """Generate data profile metrics for one object CSV file."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = [f.strip() for f in (reader.fieldnames or [])]
        if not fieldnames:
            return {"row_count": 0, "columns": []}

        # Keep profile state per column.
        type_state: Dict[str, Optional[str]] = {col: None for col in fieldnames}
        null_count: Dict[str, int] = {col: 0 for col in fieldnames}
        distinct_values: Dict[str, set] = {col: set() for col in fieldnames}
        value_counter: Dict[str, Counter] = {col: Counter() for col in fieldnames}
        numeric_min: Dict[str, Optional[Decimal]] = {col: None for col in fieldnames}
        numeric_max: Dict[str, Optional[Decimal]] = {col: None for col in fieldnames}
        numeric_sum: Dict[str, Decimal] = {col: Decimal("0") for col in fieldnames}
        numeric_count: Dict[str, int] = {col: 0 for col in fieldnames}

        row_count = 0
        for row in reader:
            row_count += 1
            for col in fieldnames:
                raw = (row.get(col) or "")
                t = infer_value_type(raw)
                type_state[col] = merge_types(type_state[col], t)

                if raw.strip() == "":
                    null_count[col] += 1
                    continue

                distinct_values[col].add(raw)
                value_counter[col][raw] += 1

                if t in {"integer", "number"}:
                    try:
                        d = Decimal(raw.strip())
                        numeric_count[col] += 1
                        numeric_sum[col] += d
                        numeric_min[col] = d if numeric_min[col] is None else min(numeric_min[col], d)
                        numeric_max[col] = d if numeric_max[col] is None else max(numeric_max[col], d)
                    except (InvalidOperation, ValueError):
                        # Guard against malformed numeric values in mixed-type columns.
                        pass

            if row_count >= sample_rows:
                break

    columns: List[Dict] = []
    for col in fieldnames:
        col_type = type_state[col] or "string"
        row_denom = row_count if row_count > 0 else 1
        metric = {
            "name": col,
            "type": col_type,
            "key_hint": bool(key_pattern.search(col)),
            "null_count": null_count[col],
            "null_ratio": null_count[col] / row_denom,
            "distinct_count": len(distinct_values[col]),
            "top_values": [
                {"value": value, "count": count}
                for value, count in value_counter[col].most_common(top_n)
            ],
        }

        if col_type in {"integer", "number"} and numeric_count[col] > 0:
            mean = numeric_sum[col] / Decimal(numeric_count[col])
            metric.update(
                {
                    "min": str(numeric_min[col]),
                    "max": str(numeric_max[col]),
                    "mean": str(mean),
                    "numeric_count": numeric_count[col],
                }
            )

        columns.append(metric)

    return {
        "row_count": row_count,
        "columns": columns,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build data profile snapshot from CSV extracts")
    parser.add_argument("--input-dir", required=True, help="Directory containing source CSV files")
    parser.add_argument("--output", required=True, help="Output profile snapshot JSON path")
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=50000,
        help="Maximum rows sampled per object",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top values to retain for categorical drift checks",
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
        objects[object_name] = profile_csv(csv_file, args.sample_rows, args.top_n, key_pattern)

    snapshot = {
        "snapshot_type": "data_profile",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_input_dir": str(input_dir),
        "object_count": len(objects),
        "objects": objects,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Data profile snapshot written: {output}")


if __name__ == "__main__":
    main()
