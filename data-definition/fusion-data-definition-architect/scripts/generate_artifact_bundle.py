#!/usr/bin/env python3
"""Generate a one-command onboarding artifact bundle.

This script consumes either direct CLI inputs or a guided intake manifest and
produces a consistent bundle with a fixed output structure:

1. Inputs Summary
2. Object Identification
3. Mapping Table
4. Validation Results
5. Reconciliation Strategy
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from generate_customer_canonical_workbook import write_excel_workbook
from object_catalog import infer_source_target_objects


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "bundle"


def parse_outputs(raw_values: List[str] | None) -> List[str]:
    if not raw_values:
        return ["mapping table", "validation summary", "reconciliation strategy"]
    parsed: List[str] = []
    for raw in raw_values:
        for item in raw.split(","):
            value = item.strip()
            if value and value not in parsed:
                parsed.append(value)
    return parsed


def load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def config_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    if args.manifest:
        manifest = load_manifest(Path(args.manifest))
        inferred = infer_source_target_objects(
            manifest.get("source_system", "Oracle EBS"),
            manifest.get("target_module", "Oracle Fusion ERP"),
            manifest["business_object"],
        )
        return {
            "source_system": manifest["source_system"],
            "target_module": manifest["target_module"],
            "business_object": manifest["business_object"],
            "source_object": manifest.get("source_object") or inferred["source_object"],
            "target_object": manifest.get("target_object") or inferred["target_object"],
            "desired_outputs": manifest.get("desired_outputs", []),
            "mode": manifest.get("mode", "knowledge"),
            "resolution": manifest.get("resolution") or inferred["resolution"],
            "resolution_note": manifest.get("resolution_note") or inferred["resolution_note"],
        }

    if not args.source_system or not args.target_module or not args.business_object:
        raise ValueError("source-system, target-module, and business-object are required when no manifest is provided.")

    inferred = infer_source_target_objects(
        args.source_system,
        args.target_module,
        args.business_object,
    )
    return {
        "source_system": args.source_system,
        "target_module": args.target_module,
        "business_object": args.business_object,
        "source_object": args.source_object or inferred["source_object"],
        "target_object": args.target_object or inferred["target_object"],
        "desired_outputs": parse_outputs(args.desired_outputs),
        "mode": "live-fa" if args.live_fa else "knowledge",
        "resolution": inferred["resolution"],
        "resolution_note": inferred["resolution_note"],
    }


def build_object_identification_rows(config: Dict[str, Any]) -> List[List[str]]:
    return [
        ["Category", "Value", "Notes"],
        ["Source System", config["source_system"], "Legacy/source application in scope"],
        ["Source Object", config["source_object"], "Primary source object/table for the initial work package"],
        ["Target Module", config["target_module"], "Target Fusion module"],
        ["Target Object", config["target_object"], "Primary Fusion object in scope"],
        ["Business Object", config["business_object"], "Business-facing scope label"],
        ["Object Resolution", config.get("resolution_note", "Not provided"), "How the source and target objects were determined"],
        ["Execution Mode", config["mode"], "Knowledge or live-fa"],
    ]


def build_inputs_summary_rows(config: Dict[str, Any]) -> List[List[str]]:
    return [
        ["Input", "Value"],
        ["Source System", config["source_system"]],
        ["Target Module", config["target_module"]],
        ["Business Object", config["business_object"]],
        ["Source Object", config["source_object"]],
        ["Target Object", config["target_object"]],
        ["Desired Outputs", ", ".join(config["desired_outputs"])],
        ["Mode", config["mode"]],
    ]


def build_mapping_rows(config: Dict[str, Any]) -> List[List[str]]:
    source_object = config["source_object"].upper()
    target_object = config["target_object"]

    if source_object == "PO_HEADERS_ALL" and target_object == "PurchaseOrderHeader":
        return [
            ["Source Table", "Source Column", "Fusion Object", "Fusion Attribute", "Transformation"],
            ["PO_HEADERS_ALL", "SEGMENT1", "PurchaseOrderHeader", "OrderNumber", "Direct"],
            ["PO_HEADERS_ALL", "TYPE_LOOKUP_CODE", "PurchaseOrderHeader", "DocumentTypeCode", "Reference-data normalization"],
            ["PO_HEADERS_ALL", "VENDOR_ID", "PurchaseOrderHeader", "SupplierId", "Resolve supplier cross-reference"],
            ["PO_HEADERS_ALL", "CURRENCY_CODE", "PurchaseOrderHeader", "CurrencyCode", "Direct"],
            ["PO_HEADERS_ALL", "AUTHORIZATION_STATUS", "PurchaseOrderHeader", "DocumentStatusCode", "Status crosswalk"],
        ]

    if source_object == "CS_INCIDENTS_ALL_B" and target_object == "ServiceRequest":
        return [
            ["Source Table", "Source Column", "Fusion Object", "Fusion Attribute", "Transformation"],
            ["CS_INCIDENTS_ALL_B", "INCIDENT_NUMBER", "ServiceRequest", "ServiceRequestNumber", "Direct"],
            ["CS_INCIDENTS_ALL_B", "SUMMARY", "ServiceRequest", "Title", "Direct or truncate to target length if needed"],
            ["CS_INCIDENTS_ALL_B", "INCIDENT_STATUS_ID", "ServiceRequest", "Status", "Lookup / status crosswalk"],
            ["CS_INCIDENTS_ALL_B", "SEVERITY_ID", "ServiceRequest", "Severity", "Lookup / severity crosswalk"],
            ["CS_INCIDENTS_ALL_B", "INCIDENT_TYPE_ID", "ServiceRequest", "Category", "Lookup / category crosswalk"],
            ["CS_INCIDENTS_ALL_B", "CUSTOMER_ID", "ServiceRequest", "CustomerId", "Resolve customer cross-reference"],
            ["CS_INCIDENTS_ALL_B", "INVENTORY_ITEM_ID", "ServiceRequest", "ProductId", "Resolve product cross-reference"],
            ["CS_INCIDENTS_ALL_B", "CREATION_DATE", "ServiceRequest", "ReportedDate", "Direct date conversion"],
            ["CS_INCIDENTS_ALL_B", "LAST_UPDATE_DATE", "ServiceRequest", "LastUpdateDate", "Direct datetime conversion"],
        ]

    if source_object == "LFA1" and target_object == "Supplier":
        return [
            ["Source Table", "Source Column", "Fusion Object", "Fusion Attribute", "Transformation"],
            ["LFA1", "LIFNR", "Supplier", "SupplierNumber", "Preserve as source supplier reference"],
            ["LFA1", "NAME1", "Supplier", "SupplierName", "Direct"],
            ["LFA1", "STCD1", "Supplier", "TaxpayerId", "Validate by country and tax rules"],
            ["LFA1", "LAND1", "Supplier", "Country", "Normalize to Fusion country reference data"],
            ["LFB1", "ZTERM", "Supplier", "PaymentTerms", "Map to Fusion payment terms"],
            ["LFM1", "EKORG", "Supplier", "ProcurementBU", "Cross-reference purchasing organization to procurement BU"],
        ]

    return [
        ["Source Table", "Source Column", "Fusion Object", "Fusion Attribute", "Transformation"],
        [config["source_object"], "Primary business key", config["target_object"], "Primary identifier", "Define during discovery"],
        [config["source_object"], "Status / type code", config["target_object"], "Status / type attribute", "Reference-data normalization"],
        [config["source_object"], "Ownership / relationship field", config["target_object"], "Relationship attribute", "Cross-reference or derive"],
    ]


def build_validation_rows(config: Dict[str, Any]) -> List[List[str]]:
    return [
        ["Validation Area", "Rule", "Target Outcome"],
        ["Completeness", "All mandatory target fields are populated", "100% coverage for critical fields"],
        ["Uniqueness", "No duplicate business keys in target", "0 unresolved duplicates"],
        ["Reference Data", "All mapped codes exist in Fusion", "0 invalid codes"],
        ["Transformation", "Derived values match approved rules", "100% approved-rule compliance"],
        ["Load Readiness", "All required inputs available for migration", "Ready for mock or production cycle"],
    ]


def build_reconciliation_rows(config: Dict[str, Any]) -> List[List[str]]:
    return [
        ["Reconciliation Layer", "Measure", "Timing"],
        ["Record Counts", "Source vs staged vs target counts", "Every migration cycle"],
        ["Business Keys", "Trace source keys to target keys", "Before sign-off"],
        ["Control Totals", "Amounts, quantities, or other agreed totals", "Post-load"],
        ["Exceptions", "Track rejects, fixes, and reprocessed rows", "Daily during migration window"],
        ["Final Sign-off", "Business and IT acceptance", "End of cycle"],
    ]


def markdown_table(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def render_bundle_markdown(config: Dict[str, Any]) -> str:
    inputs_rows = build_inputs_summary_rows(config)

    sections = [
        "# Artifact Bundle Summary",
        "",
        "## 1. Inputs Summary",
        "",
        markdown_table(inputs_rows),
        "",
        "## 2. Object Identification",
        "",
        markdown_table(build_object_identification_rows(config)),
        "",
        "## 3. Mapping Table",
        "",
        markdown_table(build_mapping_rows(config)),
        "",
        "## 4. Validation Results",
        "",
        markdown_table(build_validation_rows(config)),
        "",
        "## 5. Reconciliation Strategy",
        "",
        markdown_table(build_reconciliation_rows(config)),
        "",
    ]
    return "\n".join(sections)


def generate_bundle_workbook(bundle_dir: Path, config: Dict[str, Any]) -> Path:
    workbook_path = bundle_dir / "artifact_bundle.xlsx"
    sheets = [
        ("Inputs_Summary", build_inputs_summary_rows(config)),
        ("Object_Identification", build_object_identification_rows(config)),
        ("Mapping_Table", build_mapping_rows(config)),
        ("Validation_Results", build_validation_rows(config)),
        ("Reconciliation_Strategy", build_reconciliation_rows(config)),
    ]
    write_excel_workbook(workbook_path, sheets)
    return workbook_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a one-command onboarding artifact bundle.")
    parser.add_argument("--manifest", help="Path to guided intake JSON manifest")
    parser.add_argument("--source-system")
    parser.add_argument("--target-module")
    parser.add_argument("--business-object")
    parser.add_argument("--source-object")
    parser.add_argument("--target-object")
    parser.add_argument("--desired-outputs", action="append")
    parser.add_argument("--live-fa", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = config_from_args(args)

    timestamp = utc_timestamp()
    slug = slugify(f"{config['source_system']}-{config['target_object']}")
    bundle_dir = OUTPUT_DIR / "bundles" / f"{timestamp}_{slug}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    summary_path = bundle_dir / "artifact_bundle_summary.md"
    manifest_copy_path = bundle_dir / "bundle_manifest.json"
    manifest_copy_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    summary_path.write_text(render_bundle_markdown(config), encoding="utf-8")

    workbook_path = generate_bundle_workbook(bundle_dir, config)

    print(f"Artifact bundle created: {bundle_dir}")
    print(f"- Summary: {summary_path}")
    print(f"- Manifest: {manifest_copy_path}")
    print(f"- Workbook: {workbook_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
