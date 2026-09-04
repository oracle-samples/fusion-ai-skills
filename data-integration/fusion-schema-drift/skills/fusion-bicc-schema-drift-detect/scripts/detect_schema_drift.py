#!/usr/bin/env python3
"""Detect schema drift and rate each finding with severity + remediation.

Supported comparison modes:
- source_drift: baseline snapshot vs current snapshot
- target_contract: current snapshot vs ODT target contract snapshot
- combined: both source_drift and target_contract
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
    """Load JSON file with a clear error if missing or invalid."""
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"JSON file not found: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def load_policy(path: Optional[str]) -> Dict:
    """Load policy from YAML or JSON.

    YAML support is optional so this script can still run in minimal environments.
    """
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
            "PyYAML is required for YAML policy files. Install pyyaml or pass a JSON policy."
        ) from exc

    with policy_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def index_columns(obj: Dict) -> Dict[str, Dict]:
    """Convert an object's column array into a name->column map."""
    return {col["name"]: col for col in obj.get("columns", [])}


def severity_sort_key(finding: Dict) -> tuple:
    """Stable sort key: severity first, then object and column names."""
    return (
        SEVERITY_ORDER.get(finding.get("severity", "info"), 99),
        finding.get("object", ""),
        finding.get("column", ""),
        finding.get("drift_type", ""),
    )


def make_finding(
    *,
    mode: str,
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
    """Build one normalized finding payload."""
    payload = {
        "mode": mode,
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


def matches_required_patterns(column_name: str, patterns: List[str]) -> bool:
    """Return True if the column name matches any configured required regex."""
    return any(re.search(pattern, column_name, re.IGNORECASE) for pattern in patterns)


def compare_source_drift(baseline: Dict, current: Dict, policy: Dict) -> List[Dict]:
    """Detect drift between baseline and current extraction snapshots."""
    findings: List[Dict] = []
    baseline_objects = baseline.get("objects", {})
    current_objects = current.get("objects", {})

    defaults = policy.get("default_severity", {})
    required_patterns = policy.get("required_column_patterns", [])
    critical_transitions = set(policy.get("critical_type_transitions", []))
    high_transitions = set(policy.get("high_type_transitions", []))

    base_set = set(baseline_objects)
    curr_set = set(current_objects)

    for object_name in sorted(base_set - curr_set):
        findings.append(
            make_finding(
                mode="source_drift",
                drift_type="object_removed",
                severity=defaults.get("object_removed", "high"),
                object_name=object_name,
                column_name=None,
                message=f"Object {object_name} exists in baseline but not in current extraction.",
                business_impact="Potential dataset loss for downstream analytics.",
                pipeline_impact="Transforms and ingestion jobs can fail due to missing object.",
                recommended_action="Block release for this object and update extraction scope or mappings.",
                auto_apply_allowed=False,
            )
        )

    for object_name in sorted(curr_set - base_set):
        findings.append(
            make_finding(
                mode="source_drift",
                drift_type="object_added",
                severity=defaults.get("object_added", "medium"),
                object_name=object_name,
                column_name=None,
                message=f"Object {object_name} is new in current extraction.",
                business_impact="May represent new data opportunities or source release changes.",
                pipeline_impact="Usually non-breaking but may require ingestion contract extension.",
                recommended_action="Review object relevance and decide whether to onboard it.",
                auto_apply_allowed=True,
            )
        )

    for object_name in sorted(base_set & curr_set):
        baseline_cols = index_columns(baseline_objects[object_name])
        current_cols = index_columns(current_objects[object_name])
        b_cols = set(baseline_cols)
        c_cols = set(current_cols)

        for column_name in sorted(b_cols - c_cols):
            base_col = baseline_cols[column_name]
            required = bool(base_col.get("key_hint")) or matches_required_patterns(
                column_name, required_patterns
            )
            severity = "critical" if required else defaults.get("column_removed", "high")
            findings.append(
                make_finding(
                    mode="source_drift",
                    drift_type="column_removed",
                    severity=severity,
                    object_name=object_name,
                    column_name=column_name,
                    message=f"Column {column_name} was removed from object {object_name}.",
                    business_impact="Required attributes may disappear from analytical datasets.",
                    pipeline_impact="Mappings referencing this column will fail.",
                    recommended_action="Create transform fallback or restore column extraction before deployment.",
                    auto_apply_allowed=False,
                )
            )

        for column_name in sorted(c_cols - b_cols):
            findings.append(
                make_finding(
                    mode="source_drift",
                    drift_type="column_added",
                    severity=defaults.get("column_added", "low"),
                    object_name=object_name,
                    column_name=column_name,
                    message=f"Column {column_name} was added to object {object_name}.",
                    business_impact="Can provide new enrichment opportunities.",
                    pipeline_impact="Typically non-breaking unless strict schema checks are enabled.",
                    recommended_action="Assess if downstream models should ingest the new column.",
                    auto_apply_allowed=True,
                )
            )

        for column_name in sorted(b_cols & c_cols):
            b_col = baseline_cols[column_name]
            c_col = current_cols[column_name]

            old_t = (b_col.get("type") or "string").lower()
            new_t = (c_col.get("type") or "string").lower()

            if old_t != new_t:
                transition = f"{old_t}->{new_t}"
                if transition in critical_transitions:
                    severity = "critical"
                elif transition in high_transitions:
                    severity = "high"
                else:
                    severity = defaults.get("column_type_changed", "high")

                findings.append(
                    make_finding(
                        mode="source_drift",
                        drift_type="column_type_changed",
                        severity=severity,
                        object_name=object_name,
                        column_name=column_name,
                        message=(
                            f"Column {column_name} type changed in {object_name}: "
                            f"{old_t} -> {new_t}."
                        ),
                        business_impact="Metric semantics and business logic may change.",
                        pipeline_impact="Type coercion failures can break transforms or ingestion jobs.",
                        recommended_action="Update transform casts and AI DP contract type mappings.",
                        auto_apply_allowed=False,
                        details={"transition": transition},
                    )
                )

            old_nullable = bool(b_col.get("nullable", True))
            new_nullable = bool(c_col.get("nullable", True))
            if old_nullable != new_nullable:
                if (not old_nullable) and new_nullable:
                    drift_type = "column_nullability_relaxed"
                    severity = defaults.get("column_nullability_relaxed", "medium")
                    if bool(b_col.get("key_hint")):
                        severity = "high"
                    message = (
                        f"Column {column_name} in {object_name} changed from non-null to nullable."
                    )
                else:
                    drift_type = "column_nullability_tightened"
                    severity = "low"
                    message = (
                        f"Column {column_name} in {object_name} changed from nullable to non-null."
                    )

                findings.append(
                    make_finding(
                        mode="source_drift",
                        drift_type=drift_type,
                        severity=severity,
                        object_name=object_name,
                        column_name=column_name,
                        message=message,
                        business_impact="Nullability shifts can alter KPI completeness and interpretation.",
                        pipeline_impact="May require null-handling updates in transformations.",
                        recommended_action="Adjust null rules/defaults and update validation checks.",
                        auto_apply_allowed=severity in {"low", "info"},
                    )
                )

    return findings


def compare_target_contract(current: Dict, target: Dict, policy: Dict) -> List[Dict]:
    """Detect mismatches between current extraction and ODT target schema contract."""
    findings: List[Dict] = []
    current_objects = current.get("objects", {})
    target_objects = target.get("objects", {})
    target_severity = policy.get("target_contract", {})

    curr_set = set(current_objects)
    tgt_set = set(target_objects)

    for object_name in sorted(tgt_set - curr_set):
        findings.append(
            make_finding(
                mode="target_contract",
                drift_type="missing_object",
                severity=target_severity.get("missing_object", "critical"),
                object_name=object_name,
                column_name=None,
                message=f"Target contract object {object_name} missing from current extraction.",
                business_impact="Target subject area cannot be populated.",
                pipeline_impact="Load jobs for this object will fail or remain stale.",
                recommended_action="Block deployment and restore extraction for this object.",
                auto_apply_allowed=False,
            )
        )

    for object_name in sorted(tgt_set & curr_set):
        curr_cols = index_columns(current_objects[object_name])
        tgt_cols = index_columns(target_objects[object_name])
        curr_names = set(curr_cols)
        tgt_names = set(tgt_cols)

        for column_name in sorted(tgt_names - curr_names):
            t_col = tgt_cols[column_name]
            required = bool(t_col.get("required", not t_col.get("nullable", True)))
            severity = (
                target_severity.get("missing_required_column", "critical")
                if required
                else "high"
            )
            findings.append(
                make_finding(
                    mode="target_contract",
                    drift_type="missing_required_column" if required else "missing_optional_column",
                    severity=severity,
                    object_name=object_name,
                    column_name=column_name,
                    message=(
                        f"Target column {column_name} in {object_name} is not present in current extraction."
                    ),
                    business_impact="Required target attributes may not load.",
                    pipeline_impact="Contract mismatch can halt load pipelines.",
                    recommended_action="Add source mapping or revise target schema contract.",
                    auto_apply_allowed=False,
                )
            )

        for column_name in sorted(curr_names & tgt_names):
            c_col = curr_cols[column_name]
            t_col = tgt_cols[column_name]
            curr_type = (c_col.get("type") or "string").lower()
            target_type = (t_col.get("type") or "string").lower()

            if curr_type != target_type:
                findings.append(
                    make_finding(
                        mode="target_contract",
                        drift_type="type_mismatch",
                        severity=target_severity.get("type_mismatch", "critical"),
                        object_name=object_name,
                        column_name=column_name,
                        message=(
                            f"Type mismatch in {object_name}.{column_name}: "
                            f"source={curr_type}, target={target_type}."
                        ),
                        business_impact="Loaded values may be rejected or semantically corrupted.",
                        pipeline_impact="Load failures likely without explicit casting rules.",
                        recommended_action="Add deterministic cast/format transform before loading to ODT.",
                        auto_apply_allowed=False,
                    )
                )

            source_nullable = bool(c_col.get("nullable", True))
            target_nullable = bool(t_col.get("nullable", True))
            if (not target_nullable) and source_nullable:
                findings.append(
                    make_finding(
                        mode="target_contract",
                        drift_type="nullable_conflict",
                        severity=target_severity.get("nullable_conflict", "high"),
                        object_name=object_name,
                        column_name=column_name,
                        message=(
                            f"Nullability conflict in {object_name}.{column_name}: "
                            "source nullable but target is non-nullable."
                        ),
                        business_impact="Potential incomplete facts/dimensions in target.",
                        pipeline_impact="Insert/update can fail due to NOT NULL constraints.",
                        recommended_action="Apply defaulting or reject-null rule in transforms before load.",
                        auto_apply_allowed=False,
                    )
                )

        for column_name in sorted(curr_names - tgt_names):
            findings.append(
                make_finding(
                    mode="target_contract",
                    drift_type="extra_column",
                    severity=target_severity.get("extra_column", "info"),
                    object_name=object_name,
                    column_name=column_name,
                    message=(
                        f"Source column {column_name} in {object_name} is not defined in target contract."
                    ),
                    business_impact="No direct risk unless strict schema sync is required.",
                    pipeline_impact="May be ignored by loader or require explicit mapping policy.",
                    recommended_action="Decide whether to extend target schema or ignore this column.",
                    auto_apply_allowed=True,
                )
            )

    return findings


def write_markdown(report: Dict, output_md: str) -> None:
    """Emit human-readable report with critical section first."""
    findings = report.get("findings", [])
    critical = [f for f in findings if f.get("severity") == "critical"]

    lines: List[str] = [
        "# Schema Drift Report",
        "",
        f"Generated at: {report.get('generated_at')}",
        f"Mode: {report.get('mode')}",
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
        for f in critical:
            lines.append(
                f"- **{f['object']}::{f.get('column') or '-'}** ({f['drift_type']}): "
                f"{f['recommended_action']}"
            )

    lines.extend(["", "## All Findings", ""])
    for f in findings:
        lines.extend(
            [
                f"### {f['severity'].upper()} - {f['drift_type']}",
                f"- object: {f['object']}",
                f"- column: {f.get('column') or '-'}",
                f"- mode: {f['mode']}",
                f"- message: {f['message']}",
                f"- recommended_action: {f['recommended_action']}",
                "",
            ]
        )

    Path(output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(output_md).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect schema drift between snapshots")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["source_drift", "target_contract", "combined"],
        help="Comparison mode",
    )
    parser.add_argument("--baseline", help="Baseline schema snapshot JSON")
    parser.add_argument("--current", required=True, help="Current schema snapshot JSON")
    parser.add_argument("--target-contract", help="Target contract snapshot JSON")
    parser.add_argument("--policy", help="Policy YAML/JSON path")
    parser.add_argument("--output-json", required=True, help="Output report JSON path")
    parser.add_argument("--output-md", required=True, help="Output report Markdown path")
    args = parser.parse_args()

    policy = load_policy(args.policy)
    current = load_json(args.current)

    findings: List[Dict] = []
    if args.mode in {"source_drift", "combined"}:
        if not args.baseline:
            raise SystemExit("--baseline is required for source_drift/combined mode")
        baseline = load_json(args.baseline)
        findings.extend(compare_source_drift(baseline, current, policy))

    if args.mode in {"target_contract", "combined"}:
        if not args.target_contract:
            raise SystemExit("--target-contract is required for target_contract/combined mode")
        target = load_json(args.target_contract)
        findings.extend(compare_target_contract(current, target, policy))

    findings.sort(key=severity_sort_key)
    counter = Counter([f.get("severity", "info") for f in findings])

    summary = {
        "total_findings": len(findings),
        "counts_by_severity": {
            sev: counter.get(sev, 0) for sev in ["critical", "high", "medium", "low", "info"]
        },
        "critical_findings": counter.get("critical", 0),
    }

    report = {
        "report_type": "schema_drift",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "summary": summary,
        "findings": findings,
    }

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, args.output_md)

    print(f"Schema drift report written: {args.output_json}")
    print(f"Schema drift markdown written: {args.output_md}")


if __name__ == "__main__":
    main()
