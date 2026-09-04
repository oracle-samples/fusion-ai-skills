#!/usr/bin/env python3
"""Assertion helper for synthetic drift test-pack outputs.

This checker validates scenario-specific conditions and can optionally verify that
all expected finding/action signatures are present in the generated report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


def load_json(path: str) -> Dict:
    """Load JSON from disk with explicit error handling."""
    file_path = Path(path)
    if not file_path.exists():
        raise SystemExit(f"Missing JSON file: {path}")
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def fail(message: str) -> None:
    """Fail fast with a clear assertion message."""
    raise SystemExit(f"ASSERTION FAILED: {message}")


def scenario_schema(report: Dict) -> None:
    """Validate required schema-drift characteristics for synthetic scenario."""
    findings = report.get("findings", [])
    if not findings:
        fail("Schema report has no findings.")

    summary = report.get("summary", {})
    if int(summary.get("critical_findings", 0)) < 1:
        fail("Expected at least one critical schema finding.")

    if not any(
        f.get("drift_type") == "column_removed"
        and f.get("column") == "INVOICE_ID"
        and f.get("severity") == "critical"
        for f in findings
    ):
        fail("Expected critical column_removed finding for INVOICE_ID.")

    if not any(
        f.get("drift_type") in {"column_type_changed", "type_mismatch"}
        and f.get("column") == "AMOUNT"
        and f.get("severity") in {"critical", "high"}
        for f in findings
    ):
        fail("Expected AMOUNT type drift finding (high/critical).")


def scenario_data(report: Dict) -> None:
    """Validate required data-drift characteristics for synthetic scenario."""
    findings = report.get("findings", [])
    if not findings:
        fail("Data report has no findings.")

    summary = report.get("summary", {})
    if int(summary.get("critical_findings", 0)) < 1:
        fail("Expected at least one critical data finding.")

    if not any(
        f.get("drift_type") == "row_count_drop" and f.get("severity") == "critical"
        for f in findings
    ):
        fail("Expected critical row_count_drop finding.")

    if not any(
        f.get("drift_type") == "null_ratio_increase"
        and f.get("column") == "SUPPLIER_ID"
        and f.get("severity") == "critical"
        for f in findings
    ):
        fail("Expected critical null_ratio_increase on SUPPLIER_ID.")


def scenario_remediation(plan: Dict) -> None:
    """Validate required remediation-plan properties for combined scenario."""
    actions = plan.get("actions", [])
    if not actions:
        fail("Remediation plan has no actions.")

    summary = plan.get("summary", {})
    if int(summary.get("critical_actions", 0)) < 1:
        fail("Expected at least one critical remediation action.")

    if not any(a.get("source_report") == "schema_drift" for a in actions):
        fail("Expected schema_drift actions in remediation plan.")

    if not any(a.get("source_report") == "data_drift" for a in actions):
        fail("Expected data_drift actions in remediation plan.")

    critical_actions = [a for a in actions if a.get("severity") == "critical"]
    if not critical_actions:
        fail("Expected critical actions in remediation plan.")

    if not all(a.get("release_decision") == "block" for a in critical_actions):
        fail("All critical actions should have release_decision=block.")


def finding_signature(entry: Dict) -> Tuple[str, str, str, str]:
    """Create stable signature for findings/actions comparison."""
    return (
        str(entry.get("severity", "")),
        str(entry.get("drift_type", "")),
        str(entry.get("object", "")),
        str(entry.get("column", "")),
    )


def action_signature(entry: Dict) -> Tuple[str, str, str, str]:
    """Create stable signature for remediation actions comparison."""
    return (
        str(entry.get("severity", "")),
        str(entry.get("drift_type", "")),
        str(entry.get("object", "")),
        str(entry.get("column", "")),
    )


def signatures(payload: Dict) -> Set[Tuple[str, str, str, str]]:
    """Extract signatures from findings or actions payloads."""
    if "findings" in payload:
        return {finding_signature(f) for f in payload.get("findings", [])}
    if "actions" in payload:
        return {action_signature(a) for a in payload.get("actions", [])}
    return set()


def assert_expected(actual: Dict, expected: Dict) -> None:
    """Assert that all expected signatures exist in actual payload."""
    act = signatures(actual)
    exp = signatures(expected)
    missing = sorted(exp - act)
    if missing:
        fail(f"Actual output is missing expected signatures: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assert synthetic drift test reports")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=["schema", "data", "remediation"],
        help="Scenario assertion profile",
    )
    parser.add_argument("--report", required=True, help="Generated report/plan JSON path")
    parser.add_argument(
        "--expected",
        help="Optional expected JSON path. Ensures expected signatures exist in output.",
    )
    args = parser.parse_args()

    actual = load_json(args.report)

    if args.scenario == "schema":
        scenario_schema(actual)
    elif args.scenario == "data":
        scenario_data(actual)
    else:
        scenario_remediation(actual)

    if args.expected:
        expected = load_json(args.expected)
        assert_expected(actual, expected)

    print(f"PASS: {args.scenario} assertions satisfied")


if __name__ == "__main__":
    main()
