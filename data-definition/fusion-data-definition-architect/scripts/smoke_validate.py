#!/usr/bin/env python3
"""Focused smoke checks for the Fusion Data Definition Architect skill."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import fusion_object_metadata as metadata  # noqa: E402
import guided_intake  # noqa: E402
from object_catalog import infer_source_target_objects  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def workbook_sheet_names(workbook_path: Path) -> list[str]:
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(workbook_path) as workbook:
        with workbook.open("xl/workbook.xml") as workbook_xml:
            root = ElementTree.parse(workbook_xml).getroot()
    return [
        str(sheet.attrib["name"])
        for sheet in root.findall(".//main:sheet", namespace)
    ]


def validate_guided_intake() -> None:
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "guided_intake.py"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert_true("--persona" not in help_result.stdout, "guided_intake.py still exposes --persona")

    config = {
        "source_system": "SAP",
        "target_module": "Oracle Fusion SCM",
        "business_object": "Suppliers",
        "source_object": "LFA1",
        "target_object": "Supplier",
        "resolution": "catalog",
        "resolution_note": "Source and target objects inferred from the onboarding catalog.",
        "desired_outputs": ["mapping table", "validation summary"],
        "mode": "knowledge",
    }
    manifest = guided_intake.build_manifest(config)
    summary = guided_intake.render_markdown_summary(manifest, Path("guided_intake.json"))
    assert_true("persona" not in str(manifest).lower(), "guided manifest still contains persona")
    assert_true("Persona" not in summary, "guided summary still contains Persona")


def validate_field_mode_and_filtering() -> None:
    assert_true(
        metadata.normalize_field_mode(None) == "standard",
        "normalize_field_mode(None) should default to standard",
    )

    fields = [
        {"field_name": "SupplierId", "data_type": "number"},
        {"field_name": "CurrencyCode", "data_type": "string"},
        {"field_name": "DocumentTypeCode", "data_type": "string"},
        {"field_name": "CreatedBy", "data_type": "string"},
        {"field_name": "ObjectVersionNumber", "data_type": "number"},
    ]
    result = metadata.apply_field_filters(fields, "standard", metadata.DEFAULT_FILTER_CONFIG)
    selected_names = {field["field_name"] for field in result["selected_fields"]}
    assert_true("SupplierId" in selected_names, "SupplierId was dropped from standard mode")
    assert_true("CurrencyCode" in selected_names, "CurrencyCode was dropped from standard mode")
    assert_true("DocumentTypeCode" in selected_names, "DocumentTypeCode was dropped from standard mode")
    assert_true("CreatedBy" not in selected_names, "CreatedBy should remain a system field")
    assert_true(
        "ObjectVersionNumber" not in selected_names,
        "ObjectVersionNumber should remain a system field",
    )


def validate_summary_sheet() -> None:
    data = {
        "filtering": {"mode": "standard"},
        "objects": [
            {
                "object_name": "Supplier",
                "status": "SUCCESS",
                "field_mode": "standard",
                "retrieved_field_count": 3,
                "sample_field_count": 0,
                "field_count": 3,
                "retrieved_flexfield_count": 0,
                "flexfield_count": 0,
                "category_counts": {metadata.CATEGORY_BUSINESS: 3},
                "resolved_endpoint": "/fscmRestApi/resources/latest/Suppliers/describe",
                "fields": [
                    {"field_name": "SupplierId", "data_type": "number"},
                    {"field_name": "CurrencyCode", "data_type": "string"},
                    {"field_name": "DocumentTypeCode", "data_type": "string"},
                ],
            }
        ],
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        workbook_path = Path(temp_dir) / "metadata.xlsx"
        metadata.export_to_excel(data, workbook_path)
        sheet_names = workbook_sheet_names(workbook_path)

    assert_true(sheet_names[0] == "Summary", "Excel export should start with a Summary sheet")
    assert_true("Supplier_Standard" in sheet_names, "Excel export should include object sheet")


def validate_catalog() -> None:
    inferred = infer_source_target_objects("SAP", "Oracle Fusion SCM", "Suppliers")
    assert_true(inferred["resolution"] == "catalog", "SAP supplier catalog lookup failed")
    assert_true(inferred["source_object"] == "LFA1", "SAP supplier source object should be LFA1")
    assert_true(inferred["target_object"] == "Supplier", "SAP supplier target object should be Supplier")


def main() -> int:
    validate_guided_intake()
    validate_field_mode_and_filtering()
    validate_summary_sheet()
    validate_catalog()
    print("Smoke validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
