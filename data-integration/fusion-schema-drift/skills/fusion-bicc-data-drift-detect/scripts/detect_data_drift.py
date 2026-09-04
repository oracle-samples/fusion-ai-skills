#!/usr/bin/env python3
"""Detect data drift between baseline and current profile snapshots.

This script rates each finding with severity and remediation guidance, with
special handling for critical drift conditions in required/key-like columns.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def load_json(path: str) -> Dict:
    """Load a JSON file with explicit error handling."""
    file_path = Path(path)
    if not file_path.exists():
        raise SystemExit(f"JSON not found: {path}")
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def load_policy(path: Optional[str]) -> Dict:
    """Load policy from YAML/JSON; YAML requires optional PyYAML dependency."""
    if not path:
        return {}

    policy_path = Path(path)
    if not policy_path.exists():
        raise SystemExit(f"Policy file not found: {path}")

    if policy_path.suffix.lower() == ".json":
        return load_json(path)

    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required for YAML policy files. Install pyyaml or pass JSON policy."
        ) from exc

    with policy_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def index_columns(obj: Dict) -> Dict[str, Dict]:
    """Create a name->column metric map for quicker comparisons."""
    return {col["name"]: col for col in obj.get("columns", [])}


def as_float(value: Optional[object], default: float = 0.0) -> float:
    """Convert optional values to float with safe fallback."""
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default


def severity_from_thresholds(value: float, thresholds: Dict[str, float]) -> Optional[str]:
    """Assign severity using descending threshold checks.

    Expected keys: critical, high, medium
    """
    if value >= float(thresholds.get("critical", 10**9)):
        return "critical"
    if value >= float(thresholds.get("high", 10**9)):
        return "high"
    if value >= float(thresholds.get("medium", 10**9)):
        return "medium"
    return None


def row_drop_severity(drop_pct: float, row_policy: Dict[str, float]) -> Optional[str]:
    """Translate row-count drop percentage into severity."""
    if drop_pct >= float(row_policy.get("critical_pct", 10**9)):
        return "critical"
    if drop_pct >= float(row_policy.get("high_pct", 10**9)):
        return "high"
    if drop_pct >= float(row_policy.get("medium_pct", 10**9)):
        return "medium"
    return None


def jaccard_similarity(values_a: List[str], values_b: List[str]) -> float:
    """Compute Jaccard similarity on categorical top-value sets."""
    a = set(values_a)
    b = set(values_b)
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def matches_required(column_name: str, patterns: List[str]) -> bool:
    """Check if column name matches policy-defined required column regex patterns."""
    return any(re.search(pattern, column_name, re.IGNORECASE) for pattern in patterns)


def make_finding(
    *,
    drift_type: str,
    severity: str,
    object_name: str,
    column_name: Optional[str],
    message: str,
    recommended_action: str,
    business_impact: str,
    pipeline_impact: str,
    auto_apply_allowed: bool,
    details: Optional[Dict] = None,
) -> Dict:
    """Construct a normalized finding object."""
    payload = {
        "drift_type": drift_type,
        "severity": severity,
        "object": object_name,
        "column": column_name,
        "message": message,
        "business_impact": business_impact,
        "pipeline_impact": pipeline_impact,
        "recommended_action": recommended_action,
        "auto_apply_allowed": auto_apply_allowed,
    }
    if details:
        payload["details"] = details
    return payload


def detect_drift(baseline: Dict, current: Dict, policy: Dict) -> List[Dict]:
    """Compare baseline and current data-profile snapshots."""
    findings: List[Dict] = []

    required_patterns = policy.get("required_column_patterns", [])
    row_policy = policy.get("row_count_drop", {})
    null_policy = policy.get("null_ratio_delta", {})
    distinct_policy = policy.get("distinct_ratio_change", {})
    numeric_policy = policy.get("numeric_mean_shift_pct", {})
    categorical_policy = policy.get("categorical_top_values", {})

    base_objects = baseline.get("objects", {})
    curr_objects = current.get("objects", {})

    base_set = set(base_objects)
    curr_set = set(curr_objects)

    # Missing objects are severe from a completeness perspective.
    for object_name in sorted(base_set - curr_set):
        findings.append(
            make_finding(
                drift_type="object_missing",
                severity="critical",
                object_name=object_name,
                column_name=None,
                message=f"Object {object_name} is missing in current extraction profiles.",
                business_impact="Entire dataset slice is absent for downstream analytics.",
                pipeline_impact="Load and transformation jobs may fail or produce stale outputs.",
                recommended_action="Stop release and restore extraction for this object before rerun.",
                auto_apply_allowed=False,
            )
        )

    for object_name in sorted(curr_set - base_set):
        findings.append(
            make_finding(
                drift_type="object_new",
                severity="low",
                object_name=object_name,
                column_name=None,
                message=f"Object {object_name} appears in current extraction but not baseline.",
                business_impact="Potential new data source for enrichment.",
                pipeline_impact="Usually non-breaking unless strict object allow-lists are enabled.",
                recommended_action="Review whether this object should be included in governed contracts.",
                auto_apply_allowed=True,
            )
        )

    for object_name in sorted(base_set & curr_set):
        base_obj = base_objects[object_name]
        curr_obj = curr_objects[object_name]

        base_rows = int(base_obj.get("row_count", 0))
        curr_rows = int(curr_obj.get("row_count", 0))

        if base_rows > 0 and curr_rows < base_rows:
            drop_pct = (base_rows - curr_rows) / base_rows
            sev = row_drop_severity(drop_pct, row_policy)
            if sev:
                findings.append(
                    make_finding(
                        drift_type="row_count_drop",
                        severity=sev,
                        object_name=object_name,
                        column_name=None,
                        message=(
                            f"Row count dropped for {object_name}: baseline={base_rows}, current={curr_rows}."
                        ),
                        business_impact="Potential under-reporting and incomplete subject area coverage.",
                        pipeline_impact="May breach load completeness/freshness SLAs.",
                        recommended_action="Check extraction filters, incremental watermark logic, and source job status.",
                        auto_apply_allowed=False,
                        details={"drop_pct": drop_pct},
                    )
                )

        base_cols = index_columns(base_obj)
        curr_cols = index_columns(curr_obj)

        for column_name in sorted(set(base_cols) & set(curr_cols)):
            b_col = base_cols[column_name]
            c_col = curr_cols[column_name]

            is_required = bool(b_col.get("key_hint")) or matches_required(
                column_name, required_patterns
            )

            # Null ratio increase checks.
            b_null = as_float(b_col.get("null_ratio"))
            c_null = as_float(c_col.get("null_ratio"))
            null_delta = c_null - b_null
            null_sev = severity_from_thresholds(null_delta, null_policy)
            if null_sev:
                # Escalate required columns by one level if needed.
                if is_required and null_sev == "high":
                    null_sev = "critical"
                findings.append(
                    make_finding(
                        drift_type="null_ratio_increase",
                        severity=null_sev,
                        object_name=object_name,
                        column_name=column_name,
                        message=(
                            f"Null ratio increased for {object_name}.{column_name}: "
                            f"baseline={b_null:.4f}, current={c_null:.4f}."
                        ),
                        business_impact="Data completeness degradation can distort KPI outcomes.",
                        pipeline_impact="NOT NULL targets or quality checks may fail.",
                        recommended_action="Apply null defaulting/imputation or fix source extraction logic.",
                        auto_apply_allowed=False,
                        details={"null_ratio_delta": null_delta, "required_column": is_required},
                    )
                )

            # Distinct cardinality ratio change.
            b_distinct = int(b_col.get("distinct_count", 0))
            c_distinct = int(c_col.get("distinct_count", 0))
            denom = max(b_distinct, 1)
            distinct_change = abs(c_distinct - b_distinct) / denom
            distinct_sev = severity_from_thresholds(distinct_change, distinct_policy)
            if distinct_sev:
                findings.append(
                    make_finding(
                        drift_type="distinct_count_shift",
                        severity=distinct_sev,
                        object_name=object_name,
                        column_name=column_name,
                        message=(
                            f"Distinct count shifted for {object_name}.{column_name}: "
                            f"baseline={b_distinct}, current={c_distinct}."
                        ),
                        business_impact="Category coverage changes can impact segmentation and trend analysis.",
                        pipeline_impact="Dimension mapping and surrogate key joins may degrade.",
                        recommended_action="Review source domain changes and update reference mappings.",
                        auto_apply_allowed=distinct_sev in {"low", "info"},
                        details={"distinct_ratio_change": distinct_change},
                    )
                )

            # Numeric mean shift checks.
            if b_col.get("mean") is not None and c_col.get("mean") is not None:
                b_mean = as_float(b_col.get("mean"))
                c_mean = as_float(c_col.get("mean"))
                denom_mean = max(abs(b_mean), 1.0)
                mean_shift = abs(c_mean - b_mean) / denom_mean
                mean_sev = severity_from_thresholds(mean_shift, numeric_policy)
                if mean_sev:
                    findings.append(
                        make_finding(
                            drift_type="numeric_mean_shift",
                            severity=mean_sev,
                            object_name=object_name,
                            column_name=column_name,
                            message=(
                                f"Numeric mean shifted for {object_name}.{column_name}: "
                                f"baseline={b_mean:.4f}, current={c_mean:.4f}."
                            ),
                            business_impact="Measure distribution shifts can indicate semantic source changes.",
                            pipeline_impact="Downstream model calibration and anomaly alerts may drift.",
                            recommended_action="Validate business meaning and refresh model/aggregation baselines.",
                            auto_apply_allowed=False,
                            details={"mean_shift_pct": mean_shift},
                        )
                    )

            # Categorical top-value overlap drift.
            b_top = [str(v["value"]) for v in b_col.get("top_values", [])]
            c_top = [str(v["value"]) for v in c_col.get("top_values", [])]
            if b_top or c_top:
                jaccard = jaccard_similarity(b_top, c_top)
                high_below = float(categorical_policy.get("high_jaccard_below", -1))
                med_below = float(categorical_policy.get("medium_jaccard_below", -1))
                cat_sev = None
                if jaccard < high_below:
                    cat_sev = "high"
                elif jaccard < med_below:
                    cat_sev = "medium"
                if cat_sev:
                    findings.append(
                        make_finding(
                            drift_type="categorical_domain_shift",
                            severity=cat_sev,
                            object_name=object_name,
                            column_name=column_name,
                            message=(
                                f"Categorical top-value overlap dropped for {object_name}.{column_name}: "
                                f"jaccard={jaccard:.4f}."
                            ),
                            business_impact="Domain-level changes can alter cohort behavior and reporting slices.",
                            pipeline_impact="Lookup/reference mapping coverage may become incomplete.",
                            recommended_action="Review new/removed domain values and update mapping tables.",
                            auto_apply_allowed=False,
                            details={"jaccard_similarity": jaccard},
                        )
                    )

    findings.sort(
        key=lambda f: (
            SEVERITY_ORDER.get(f.get("severity", "info"), 99),
            f.get("object", ""),
            f.get("column") or "",
            f.get("drift_type", ""),
        )
    )
    return findings


def write_markdown(report: Dict, output_md: str) -> None:
    """Write report in markdown format with critical findings at top."""
    findings = report.get("findings", [])
    critical = [f for f in findings if f.get("severity") == "critical"]

    lines: List[str] = [
        "# Data Drift Report",
        "",
        f"Generated at: {report.get('generated_at')}",
        "",
        "## Severity Summary",
        "",
    ]
    for sev, count in report.get("summary", {}).get("counts_by_severity", {}).items():
        lines.append(f"- {sev}: {count}")

    lines.extend(["", "## Critical Findings & Immediate Actions", ""])
    if not critical:
        lines.append("- No critical findings.")
    else:
        for finding in critical:
            lines.append(
                f"- **{finding['object']}::{finding.get('column') or '-'}** "
                f"({finding['drift_type']}): {finding['recommended_action']}"
            )

    lines.extend(["", "## All Findings", ""])
    for finding in findings:
        lines.extend(
            [
                f"### {finding['severity'].upper()} - {finding['drift_type']}",
                f"- object: {finding['object']}",
                f"- column: {finding.get('column') or '-'}",
                f"- message: {finding['message']}",
                f"- recommended_action: {finding['recommended_action']}",
                "",
            ]
        )

    out = Path(output_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect data drift from profile snapshots")
    parser.add_argument("--baseline", required=True, help="Baseline data profile snapshot JSON")
    parser.add_argument("--current", required=True, help="Current data profile snapshot JSON")
    parser.add_argument("--policy", help="Data drift policy YAML/JSON")
    parser.add_argument("--output-json", required=True, help="Output data drift report JSON")
    parser.add_argument("--output-md", required=True, help="Output data drift report markdown")
    args = parser.parse_args()

    baseline = load_json(args.baseline)
    current = load_json(args.current)
    policy = load_policy(args.policy)

    findings = detect_drift(baseline, current, policy)
    counts = Counter([f.get("severity", "info") for f in findings])
    summary = {
        "total_findings": len(findings),
        "counts_by_severity": {
            sev: counts.get(sev, 0) for sev in ["critical", "high", "medium", "low", "info"]
        },
        "critical_findings": counts.get("critical", 0),
    }

    report = {
        "report_type": "data_drift",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "findings": findings,
    }

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, args.output_md)

    print(f"Data drift report written: {args.output_json}")
    print(f"Data drift markdown written: {args.output_md}")


if __name__ == "__main__":
    main()
