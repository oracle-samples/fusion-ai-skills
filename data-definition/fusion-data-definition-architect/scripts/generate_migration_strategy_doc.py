#!/usr/bin/env python3
"""Generate an example end-to-end data migration strategy Word document.

This hard-coded sample creates a lightweight .docx document without third-party
dependencies. Use it for demonstrations or workshop scaffolding, then adapt the
content before treating it as customer-specific output.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence
from xml.sax.saxutils import escape as xml_escape
import zipfile


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "output" / "example_data_migration_strategy_ebs_to_fusion_erp.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def paragraph(text: str, style: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    safe_text = xml_escape(text)
    return (
        f'<w:p>{ppr}'
        '<w:r><w:t xml:space="preserve">'
        f'{safe_text}'
        '</w:t></w:r></w:p>'
    )


def table(rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return ""

    column_count = max(len(row) for row in rows)
    grid = "".join('<w:gridCol w:w="2400"/>' for _ in range(column_count))
    borders = (
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
        '</w:tblBorders>'
    )

    row_xml: List[str] = []
    for row_index, row in enumerate(rows):
        cells: List[str] = []
        for value in row:
            cell_text = xml_escape(value)
            cell_props = '<w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr>'
            paragraph_props = (
                '<w:pPr><w:rPr><w:b/></w:rPr></w:pPr>'
                if row_index == 0
                else ''
            )
            cells.append(
                '<w:tc>'
                f'{cell_props}'
                '<w:p>'
                f'{paragraph_props}'
                f'<w:r><w:t xml:space="preserve">{cell_text}</w:t></w:r>'
                '</w:p>'
                '</w:tc>'
            )
        if len(row) < column_count:
            for _ in range(column_count - len(row)):
                cells.append(
                    '<w:tc><w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr><w:p/></w:tc>'
                )
        row_xml.append(f'<w:tr>{"".join(cells)}</w:tr>')

    return (
        '<w:tbl>'
        '<w:tblPr>'
        '<w:tblW w:w="0" w:type="auto"/>'
        f'{borders}'
        '</w:tblPr>'
        f'<w:tblGrid>{grid}</w:tblGrid>'
        f'{"".join(row_xml)}'
        '</w:tbl>'
    )


def build_document_body() -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts: List[str] = []

    parts.append(paragraph("Example Data Migration Strategy: Oracle EBS to Oracle Fusion ERP", "Title"))
    parts.append(paragraph(f"Generated: {generated_at}"))

    parts.append(paragraph("1. Inputs Summary", "Heading1"))
    parts.append(
        table(
            [
                ["Input", "Value"],
                ["Source System", "Oracle EBS"],
                ["Target Platform", "Oracle Fusion ERP"],
                ["Primary Objective", "Deliver a controlled, reconciled, business-ready migration from EBS to Fusion"],
                ["Example Source Table", "PO_HEADERS_ALL"],
                ["Example Target Object", "PurchaseOrderHeader"],
                ["Artifact Type", "End-to-end migration strategy"],
            ]
        )
    )

    parts.append(paragraph("2. Object Identification", "Heading1"))
    parts.append(
        paragraph(
            "The migration should start with object identification by business domain, source ownership, and target Fusion object alignment."
        )
    )
    parts.append(
        table(
            [
                ["Business Domain", "EBS Source", "Fusion Target", "Purpose"],
                ["Procurement", "PO_HEADERS_ALL", "PurchaseOrderHeader", "Purchase order header migration"],
                ["Procurement", "PO_LINES_ALL", "PurchaseOrderLine", "Purchase order line migration"],
                ["Suppliers", "AP_SUPPLIERS", "Supplier", "Supplier master migration"],
                ["Customers", "HZ_CUST_ACCOUNTS", "Customer Account", "Receivables customer migration"],
                ["Payables", "AP_INVOICES_ALL", "PayablesInvoice", "Invoice and liability migration"],
            ]
        )
    )

    parts.append(paragraph("3. Migration Approach", "Heading1"))
    for line in [
        "• Model for Fusion first, then map EBS into that model.",
        "• Separate discovery, mapping, validation, reconciliation, cutover, and hypercare into explicit work packages.",
        "• Preserve legacy keys and source lineage for auditability and reconciliation.",
        "• Use wave-based migration where volume, geography, business unit, or risk profile require sequencing.",
    ]:
        parts.append(paragraph(line))

    parts.append(paragraph("4. Migration Phases", "Heading1"))
    parts.append(
        table(
            [
                ["Phase", "Objective", "Key Activities", "Exit Criteria"],
                ["Discover", "Confirm scope and dependencies", "Identify source objects, target objects, volumes, and owners", "Approved object inventory and scope baseline"],
                ["Map", "Define target alignment", "Create canonical model, source-to-target mappings, and reference data crosswalks", "Signed-off mapping workbook"],
                ["Validate", "Prove data readiness", "Run completeness, quality, and transformation validation", "Defect backlog within agreed tolerance"],
                ["Migrate", "Load target data", "Extract, transform, load, and execute mock cycles", "Successful mock load and sign-off"],
                ["Cutover", "Move to production safely", "Freeze source changes, load production data, reconcile outputs", "Business and IT cutover approval"],
                ["Hypercare", "Stabilize after go-live", "Monitor issues, complete reconciliation closure, transition to BAU", "Open issues reduced to steady-state levels"],
            ]
        )
    )

    parts.append(paragraph("5. Mapping Table", "Heading1"))
    parts.append(
        paragraph(
            "Below is a reusable procurement example that can be lifted into workshop materials or a migration workbook."
        )
    )
    parts.append(
        table(
            [
                ["Source Table", "Source Column", "Fusion Object", "Fusion Attribute", "Transformation"],
                ["PO_HEADERS_ALL", "SEGMENT1", "PurchaseOrderHeader", "OrderNumber", "Direct"],
                ["PO_HEADERS_ALL", "TYPE_LOOKUP_CODE", "PurchaseOrderHeader", "DocumentTypeCode", "Reference-data normalization"],
                ["PO_HEADERS_ALL", "VENDOR_ID", "PurchaseOrderHeader", "SupplierId", "Resolve supplier cross-reference"],
                ["PO_HEADERS_ALL", "CURRENCY_CODE", "PurchaseOrderHeader", "CurrencyCode", "Direct"],
                ["PO_HEADERS_ALL", "AUTHORIZATION_STATUS", "PurchaseOrderHeader", "DocumentStatusCode", "Status crosswalk"],
            ]
        )
    )

    parts.append(paragraph("6. Validation Results", "Heading1"))
    parts.append(
        paragraph(
            "Validation should be executed in every mock cycle and before production cutover. The strategy requires explicit reporting of completeness, quality, and transformation outcomes."
        )
    )
    parts.append(
        table(
            [
                ["Validation Area", "Rule", "Target Outcome", "Owner"],
                ["Completeness", "All mandatory target fields populated", "100% for in-scope critical fields", "Data Migration Lead"],
                ["Uniqueness", "No duplicate business keys created in target", "0 unresolved duplicates", "Data Steward / MDM"],
                ["Reference Data", "All source codes mapped to valid Fusion values", "0 invalid target codes", "Functional Lead"],
                ["Transformation", "Derived and defaulted values reconciled to rules", "100% rule compliance for approved mappings", "Conversion Lead"],
                ["Load Outcome", "Load errors within tolerance", "Agreed defect threshold met", "Technical Lead"],
            ]
        )
    )

    parts.append(paragraph("7. Reconciliation Strategy", "Heading1"))
    parts.append(
        table(
            [
                ["Reconciliation Layer", "Measure", "Tolerance", "Timing"],
                ["Record Count", "Source vs staged vs loaded counts", "0 unexplained variance for critical objects", "Every mock and production cycle"],
                ["Control Totals", "Amounts, quantities, and key totals", "Within approved tolerance", "Post-load and post-cutover"],
                ["Business Keys", "Document numbers, supplier numbers, account numbers", "100% traceability", "Before sign-off"],
                ["Exceptions", "Rejected or corrected rows", "Tracked and dispositioned", "Daily during load window"],
                ["Sign-off", "Business + IT acceptance", "Formal approval recorded", "End of each migration cycle"],
            ]
        )
    )

    parts.append(paragraph("8. Governance and Approval Model", "Heading1"))
    for line in [
        "• Business owners approve in-scope objects, critical data rules, and reconciliation tolerances.",
        "• Functional leads approve target object design, mappings, and reference-data crosswalks.",
        "• Technical leads approve extraction, transformation, load, and cutover execution readiness.",
        "• Data stewards own duplicate resolution, exception handling, and post-load issue closure.",
    ]:
        parts.append(paragraph(line))

    parts.append(paragraph("9. Cutover and Hypercare", "Heading1"))
    for line in [
        "• Freeze source changes according to agreed blackout windows.",
        "• Execute final extraction, transformation, load, validation, and reconciliation in sequence.",
        "• Track production defects through a command-center model during hypercare.",
        "• Transition unresolved items into business-as-usual support only after reconciliation closure.",
    ]:
        parts.append(paragraph(line))

    parts.append(paragraph("10. Recommended Deliverables", "Heading1"))
    for line in [
        "• Object inventory and scope matrix",
        "• Canonical model and source-to-target mapping workbook",
        "• Reference-data crosswalks",
        "• Validation rule set and defect log",
        "• Reconciliation framework and sign-off checklist",
        "• Cutover runbook and hypercare tracker",
    ]:
        parts.append(paragraph(line))

    parts.append('<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>')
    return "".join(parts)


def build_document_xml() -> str:
    body = build_document_body()
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}">'
        f'<w:body>{body}</w:body>'
        '</w:document>'
    )


def write_docx(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>'
    )
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:styles xmlns:w="{W_NS}">'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="Title">'
        '<w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading1">'
        '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>'
        '</w:styles>'
    )
    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties '
        'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>Example Data Migration Strategy</dc:title>'
        '<dc:creator>fusion-data-definition-architect</dc:creator>'
        '<cp:lastModifiedBy>fusion-data-definition-architect</cp:lastModifiedBy>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
        '</cp:coreProperties>'
    )
    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>fusion-data-definition-architect</Application>'
        '</Properties>'
    )

    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", root_rels)
        docx.writestr("word/document.xml", build_document_xml())
        docx.writestr("word/_rels/document.xml.rels", document_rels)
        docx.writestr("word/styles.xml", styles_xml)
        docx.writestr("docProps/core.xml", core_xml)
        docx.writestr("docProps/app.xml", app_xml)


def main() -> int:
    write_docx(OUTPUT_PATH)
    print(f"Example Word document created: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
