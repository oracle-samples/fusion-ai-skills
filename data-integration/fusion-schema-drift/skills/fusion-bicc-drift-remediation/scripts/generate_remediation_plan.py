#!/usr/bin/env python3
"""Generate a critical-first remediation plan from drift reports.

Inputs are schema and/or data drift JSON reports. The output plan consolidates
actions, assigns owners, and proposes release decisions by severity.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


SEVERITY_ORDER_DEFAULT = ["critical", "high", "medium", "low", "info"]


def load_json(path: Optional[str]) -> Optional[Dict]:
    """Load optional JSON report path safely."""
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"JSON not found: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def load_policy(path: Optional[str]) -> Dict:
    """Load policy from YAML/JSON. YAML requires optional PyYAML."""
    if not path:
        return {}

    policy_path = Path(path)
    if not policy_path.exists():
        raise SystemExit(f"Policy file not found: {path}")

    if policy_path.suffix.lower() == ".json":
        return load_json(path) or {}

    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required for YAML policy files. Install pyyaml or pass JSON policy."
        ) from exc

    with policy_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def severity_rank(severity: str, order: List[str]) -> int:
    """Map severity to ordinal rank for sorting and prioritization."""
    try:
        return order.index((severity or "info").lower())
    except ValueError:
        return len(order)


def normalize_finding(finding: Dict, source_report: str, policy: Dict) -> Dict:
    """Convert finding payload into a remediation action entry."""
    severity = (finding.get("severity") or "info").lower()
    drift_type = finding.get("drift_type", "unknown")

    owner = policy.get("owner_by_drift_type", {}).get(
        drift_type, policy.get("default_owner", "data-platform-owner")
    )
    release_decision = policy.get("default_release_decision", {}).get(severity, "warn")

    # Create a deterministic action ID for tracking and ticketing.
    object_name = finding.get("object", "unknown-object")
    column_name = finding.get("column") or "-"
    action_id = f"{source_report}:{drift_type}:{object_name}:{column_name}"

    return {
        "action_id": action_id,
        "source_report": source_report,
        "severity": severity,
        "release_decision": release_decision,
        "owner": owner,
        "object": object_name,
        "column": finding.get("column"),
        "drift_type": drift_type,
        "message": finding.get("message"),
        "business_impact": finding.get("business_impact"),
        "pipeline_impact": finding.get("pipeline_impact"),
        "recommended_action": finding.get("recommended_action"),
        "auto_apply_allowed": bool(finding.get("auto_apply_allowed", False)),
        "details": finding.get("details", {}),
    }


def collect_actions(schema_report: Optional[Dict], data_report: Optional[Dict], policy: Dict) -> List[Dict]:
    """Collect and normalize actions from available report sources."""
    actions: List[Dict] = []

    if schema_report:
        for finding in schema_report.get("findings", []):
            actions.append(normalize_finding(finding, "schema_drift", policy))

    if data_report:
        for finding in data_report.get("findings", []):
            actions.append(normalize_finding(finding, "data_drift", policy))

    return actions


def write_markdown(plan: Dict, output_md: str) -> None:
    """Write remediation plan markdown with critical-first sections."""
    actions = plan.get("actions", [])
    critical = [a for a in actions if a.get("severity") == "critical"]

    lines: List[str] = [
        "# Remediation Plan",
        "",
        f"Generated at: {plan.get('generated_at')}",
        "",
        "## Severity Summary",
        "",
    ]

    for sev, count in plan.get("summary", {}).get("counts_by_severity", {}).items():
        lines.append(f"- {sev}: {count}")

    lines.extend(["", "## Critical Findings & Immediate Actions", ""])
    if not critical:
        lines.append("- No critical findings.")
    else:
        for action in critical:
            lines.append(
                f"- **{action['action_id']}** owner={action['owner']} decision={action['release_decision']}"
            )
            lines.append(f"  - action: {action.get('recommended_action')}")

    lines.extend(["", "## Prioritized Action Queue", ""])
    for action in actions:
        lines.extend(
            [
                f"### {action['severity'].upper()} - {action['drift_type']}",
                f"- action_id: {action['action_id']}",
                f"- source_report: {action['source_report']}",
                f"- owner: {action['owner']}",
                f"- release_decision: {action['release_decision']}",
                f"- object: {action['object']}",
                f"- column: {action.get('column') or '-'}",
                f"- recommended_action: {action.get('recommended_action')}",
                "",
            ]
        )

    out = Path(output_md)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate consolidated remediation plan")
    parser.add_argument("--schema-report", help="Schema drift report JSON")
    parser.add_argument("--data-report", help="Data drift report JSON")
    parser.add_argument("--policy", help="Remediation policy YAML/JSON")
    parser.add_argument("--output-json", required=True, help="Output remediation plan JSON")
    parser.add_argument("--output-md", required=True, help="Output remediation plan markdown")
    args = parser.parse_args()

    if not args.schema_report and not args.data_report:
        raise SystemExit("At least one input report is required (--schema-report or --data-report).")

    schema_report = load_json(args.schema_report)
    data_report = load_json(args.data_report)
    policy = load_policy(args.policy)
    severity_order = policy.get("severity_order", SEVERITY_ORDER_DEFAULT)

    actions = collect_actions(schema_report, data_report, policy)
    actions.sort(
        key=lambda a: (
            severity_rank(a.get("severity", "info"), severity_order),
            a.get("owner", ""),
            a.get("object", ""),
            a.get("column") or "",
            a.get("drift_type", ""),
        )
    )

    counts = Counter([a.get("severity", "info") for a in actions])
    summary = {
        "total_actions": len(actions),
        "counts_by_severity": {
            sev: counts.get(sev, 0) for sev in severity_order
        },
        "critical_actions": counts.get("critical", 0),
    }

    plan = {
        "plan_type": "drift_remediation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "actions": actions,
    }

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    write_markdown(plan, args.output_md)

    print(f"Remediation plan written: {args.output_json}")
    print(f"Remediation markdown written: {args.output_md}")


if __name__ == "__main__":
    main()
