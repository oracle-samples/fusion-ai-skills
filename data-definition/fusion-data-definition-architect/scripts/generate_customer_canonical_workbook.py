#!/usr/bin/env python3
"""Generate an example customer canonical workbook for EBS to Fusion ERP.

This hard-coded sample creates an Excel file with:
- Canonical customer model rows
- Detailed EBS-to-Fusion mapping rows
- Object/domain summary rows

Use it for demonstrations or workshop scaffolding, then adapt the content before
treating it as customer-specific output. It does not require live Fusion access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Sequence, Tuple
from xml.sax.saxutils import escape as xml_escape
import zipfile


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "output" / "example_customer_canonical_model_ebs_to_fusion_erp.xlsx"


def column_letter(index: int) -> str:
    result = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def worksheet_xml(rows: List[List[Any]]) -> str:
    row_xml: List[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: List[str] = []
        for column_index, value in enumerate(row, start=1):
            cell_ref = f"{column_letter(column_index)}{row_index}"
            rendered = "" if value is None else str(value)
            cells.append(
                f'<c r="{cell_ref}" t="inlineStr"><is><t xml:space="preserve">'
                f'{xml_escape(rendered)}</t></is></c>'
            )
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        '</worksheet>'
    )


def write_excel_workbook(output_path: Path, sheets: Sequence[Tuple[str, List[List[Any]]]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content_types_overrides = [
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    workbook_sheets: List[str] = []
    workbook_rels: List[str] = []

    with zipfile.ZipFile(output_path, mode="w", compression=zipfile.ZIP_DEFLATED) as workbook:
        for index, (sheet_name, rows) in enumerate(sheets, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", worksheet_xml(rows))
            workbook_sheets.append(
                f'<sheet name="{xml_escape(sheet_name[:31])}" sheetId="{index}" r:id="rId{index}"/>'
            )
            workbook_rels.append(
                f'<Relationship Id="rId{index}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{index}.xml"/>'
            )
            content_types_overrides.append(
                f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            )

        workbook.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            + "".join(content_types_overrides)
            + '</Types>',
        )
        workbook.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
            'Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
            'Target="docProps/app.xml"/>'
            '</Relationships>',
        )
        workbook.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<workbookPr/>'
            '<bookViews><workbookView xWindow="0" yWindow="0" windowWidth="24000" windowHeight="12000"/>'
            '</bookViews>'
            f'<sheets>{"".join(workbook_sheets)}</sheets>'
            '</workbook>',
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(workbook_rels)
            + f'<Relationship Id="rId{len(sheets) + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
            '</Relationships>',
        )
        workbook.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="2"><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill></fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
            '</styleSheet>',
        )

        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        workbook.writestr(
            "docProps/core.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties '
            'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:title>Example Customer Canonical Model</dc:title>'
            '<dc:creator>fusion-data-definition-architect</dc:creator>'
            '<cp:lastModifiedBy>fusion-data-definition-architect</cp:lastModifiedBy>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
            '</cp:coreProperties>',
        )
        workbook.writestr(
            "docProps/app.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            '<Application>fusion-data-definition-architect</Application>'
            f'<TitlesOfParts><vt:vector size="{len(sheets)}" baseType="lpstr">'
            + "".join(f'<vt:lpstr>{xml_escape(name[:31])}</vt:lpstr>' for name, _ in sheets)
            + '</vt:vector></TitlesOfParts>'
            f'<HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>{len(sheets)}</vt:i4></vt:variant></vt:vector></HeadingPairs>'
            '</Properties>',
        )


def rows_from_iterable(header: Sequence[str], rows: Iterable[Sequence[Any]]) -> List[List[Any]]:
    return [list(header)] + [list(row) for row in rows]


def canonical_model_rows() -> List[List[str]]:
    header = [
        "Canonical Entity",
        "Canonical Attribute",
        "Description",
        "Required",
        "Fusion Object",
        "Fusion Field",
        "EBS Source Table",
        "EBS Source Column",
        "Transformation Rule",
        "Notes",
    ]
    rows = [
        ["Party", "PartyType", "Organization or person customer classification", "Yes", "Party", "PartyType", "HZ_PARTIES", "PARTY_TYPE", "Direct + normalize", "Required to distinguish organization vs person customers."],
        ["Party", "PartyName", "Core party name", "Yes", "Customer Account", "PartyName", "HZ_PARTIES", "PARTY_NAME", "Direct", "Preserve party identity separately from account behavior."],
        ["Party", "PartyNumber", "Party reference number", "Recommended", "Customer Account", "PartyNumber", "HZ_PARTIES", "PARTY_NUMBER", "Direct", "Useful for lineage and reconciliation."],
        ["Customer Account", "AccountNumber", "Customer account number", "Yes", "Customer Account", "AccountNumber", "HZ_CUST_ACCOUNTS", "ACCOUNT_NUMBER", "Direct", "Primary business key within migration scope."],
        ["Customer Account", "AccountName", "Customer account display name", "Yes", "Customer Account", "AccountName", "HZ_CUST_ACCOUNTS / HZ_PARTIES", "ACCOUNT_NAME / PARTY_NAME", "Coalesce / prefer account name", "Use account name when separately maintained; otherwise default from party name."],
        ["Customer Account", "CustomerType", "Customer type / segment classification", "Conditional", "Customer Account", "CustomerType", "HZ_CUST_ACCOUNTS", "CUSTOMER_TYPE", "Reference-data normalization", "Align to enterprise-approved Fusion values."],
        ["Customer Account", "Status", "Operational account status", "Yes", "Customer Account", "Status", "HZ_CUST_ACCOUNTS", "STATUS", "Status crosswalk", "Map EBS active/inactive codes explicitly."],
        ["Customer Account", "AccountClass", "Customer class / classification", "No", "Customer Account", "AccountClass", "HZ_CUST_ACCOUNTS", "CUSTOMER_CLASS_CODE", "Reference-data crosswalk", "Use controlled target account class values."],
        ["Customer Account", "SalesChannel", "Sales channel", "No", "Customer Account", "SalesChannel", "HZ_CUST_ACCOUNTS", "SALES_CHANNEL_CODE", "Reference-data crosswalk", "Optional depending on reporting design."],
        ["Customer Account", "MarketSegment", "Market segment", "No", "Customer Account", "MarketSegment", "HZ_CUST_ACCOUNTS", "MARKET_SEGMENT_CODE", "Reference-data crosswalk", "Optional depending on segmentation design."],
        ["Customer Account", "Industry", "Industry classification", "No", "Customer Account", "Industry", "HZ_PARTIES", "SIC_CODE / industry attribute", "Crosswalk", "Enterprise-specific industry mapping."],
        ["Customer Account", "SourceSystem", "Migration source system name", "Yes for conversion", "Customer Account", "SourceSystem", "Derived", "Constant 'EBS'", "Default literal", "Recommended for migration lineage and reconciliation."],
        ["Customer Account", "SourceSystemReferenceValue", "Legacy cross-reference key", "Yes for conversion", "Customer Account", "SourceSystemReferenceValue", "HZ_CUST_ACCOUNTS", "ORIG_SYSTEM_REFERENCE or CUST_ACCOUNT_ID", "Direct", "Preserve legacy ID for auditability and load reconciliation."],
        ["Customer Account", "StartDateActive", "Account effective start date", "Recommended", "Customer Account", "StartDateActive", "HZ_CUST_ACCOUNTS", "START_DATE_ACTIVE", "Direct / date conversion", "Populate when available in the source."],
        ["Customer Account", "EndDateActive", "Account effective end date", "No", "Customer Account", "EndDateActive", "HZ_CUST_ACCOUNTS", "END_DATE_ACTIVE", "Direct / date conversion", "Populate when available in the source."],
        ["Customer Account Site", "SiteReference", "Customer account site identifier", "Yes", "Customer Account Site", "SiteNumber / SiteReference", "HZ_CUST_ACCT_SITES_ALL", "CUST_ACCT_SITE_ID", "Direct or derive stable key", "Use a stable site identifier during migration."],
        ["Customer Account Site", "AddressLine1", "Primary address line", "Yes", "Customer Account Site", "AddressLine1", "HZ_LOCATIONS", "ADDRESS1", "Direct", "Minimum address completeness requirement."],
        ["Customer Account Site", "AddressLine2", "Secondary address line", "No", "Customer Account Site", "AddressLine2", "HZ_LOCATIONS", "ADDRESS2", "Direct", "Optional."],
        ["Customer Account Site", "AddressLine3", "Tertiary address line", "No", "Customer Account Site", "AddressLine3", "HZ_LOCATIONS", "ADDRESS3", "Direct", "Optional."],
        ["Customer Account Site", "City", "City / locality", "Yes", "Customer Account Site", "City", "HZ_LOCATIONS", "CITY", "Direct", "Core address component."],
        ["Customer Account Site", "State", "State / province / region", "Conditional", "Customer Account Site", "State", "HZ_LOCATIONS", "STATE", "Direct + normalize", "Normalize abbreviations where required."],
        ["Customer Account Site", "PostalCode", "Postal / ZIP code", "Conditional", "Customer Account Site", "PostalCode", "HZ_LOCATIONS", "POSTAL_CODE", "Direct + format validation", "Apply country-sensitive postal validation."],
        ["Customer Account Site", "Country", "Country code / name", "Yes", "Customer Account Site", "Country", "HZ_LOCATIONS", "COUNTRY", "Normalize to target standard", "Prefer ISO-style target representation."],
        ["Customer Site Use", "BillToSite", "Bill-to site designation", "Conditional", "Customer Account", "BillToSite", "HZ_CUST_SITE_USES_ALL", "SITE_USE_CODE = BILL_TO", "Derive from active site-use rows", "Create only from valid active bill-to usages."],
        ["Customer Site Use", "ShipToSite", "Ship-to site designation", "Conditional", "Customer Account", "ShipToSite", "HZ_CUST_SITE_USES_ALL", "SITE_USE_CODE = SHIP_TO", "Derive from active site-use rows", "Create only from valid active ship-to usages."],
        ["Customer Site Use", "SiteUseStatus", "Operational site-use status", "Recommended", "Customer Site Use", "Status", "HZ_CUST_SITE_USES_ALL", "STATUS", "Status crosswalk", "Prevent inactive site uses from becoming transactable."],
        ["Customer Contact", "PrimaryContactName", "Primary customer contact name", "No", "Customer Account", "PrimaryContactName", "HZ_ORG_CONTACTS / HZ_RELATIONSHIPS", "Contact person name fields", "Derive primary contact", "Use business rule to identify the default contact."],
        ["Customer Contact", "EmailAddress", "Contact email address", "Recommended", "Customer Account / Customer Contact", "EmailAddress", "HZ_CONTACT_POINTS", "EMAIL_ADDRESS", "Direct", "Prefer contact-level load when multiple contacts exist."],
        ["Customer Contact", "PhoneNumber", "Contact phone number", "No", "Customer Account / Customer Contact", "PhoneNumber", "HZ_CONTACT_POINTS", "PHONE_NUMBER / RAW_PHONE_NUMBER", "Phone normalization", "Standardize formatting and country codes."],
        ["Customer Profile", "PaymentTerms", "Default payment terms", "Conditional", "Customer Account", "PaymentTerms", "HZ_CUSTOMER_PROFILES", "STANDARD_TERMS or terms reference", "Lookup to target terms", "Validate against target payment terms setup."],
        ["Customer Profile", "StatementCycle", "Statement cycle", "No", "Customer Profile", "StatementCycle", "HZ_CUSTOMER_PROFILES", "STATEMENT_CYCLE_ID", "Lookup / translate", "Use only where statement processing is in scope."],
        ["Customer Profile", "Collector", "Assigned collector", "No", "Customer Account", "Collector", "HZ_CUSTOMER_PROFILES", "COLLECTOR_ID", "Lookup ID to name/code", "Requires collector reference-data crosswalk."],
        ["Customer Profile", "CreditLimit", "Overall credit limit", "Conditional", "Customer Account", "CreditLimit", "HZ_CUST_PROFILE_AMTS", "Overall credit limit column", "Numeric conversion", "Preserve currency context and rounding rules."],
        ["Customer Profile", "CreditClassification", "Credit classification", "No", "Customer Account", "CreditClassification", "HZ_CUSTOMER_PROFILES", "CREDIT_CLASSIFICATION", "Reference-data crosswalk", "Normalize to target credit policy values."],
        ["Customer Tax Profile", "TaxpayerIdentificationNumber", "Tax registration / identifier", "Conditional", "Customer Account", "TaxpayerIdentificationNumber", "ZX_PARTY_TAX_PROFILE or equivalent", "Tax registration number", "Direct + tax-format validation", "Validate by country and jurisdiction."],
        ["Customer Tax Profile", "TaxClassification", "Tax classification", "Conditional", "Customer Account", "TaxClassification", "EBS tax classification source", "Tax classification column", "Crosswalk", "Map to Fusion-supported tax classification values."],
    ]
    return rows_from_iterable(header, rows)


def mapping_detail_rows() -> List[List[str]]:
    header = ["Source (EBS)", "Target (Fusion)", "Transformation", "Notes"]
    rows = [
        ["HZ_PARTIES.PARTY_TYPE", "Party.PartyType", "Direct + normalization", "Distinguish organization vs person customers in the target model."],
        ["HZ_CUST_ACCOUNTS.ACCOUNT_NUMBER", "Customer Account.AccountNumber", "Direct", "Primary customer account identifier."],
        ["HZ_CUST_ACCOUNTS.ACCOUNT_NAME or HZ_PARTIES.PARTY_NAME", "Customer Account.AccountName", "Coalesce / prefer account-specific name", "Use account name when maintained separately; otherwise default from party name."],
        ["HZ_PARTIES.PARTY_NAME", "Customer Account.PartyName", "Direct", "Preserves core party identity."],
        ["HZ_PARTIES.PARTY_NUMBER", "Customer Account.PartyNumber", "Direct", "Useful for cross-reference and auditability."],
        ["HZ_CUST_ACCOUNTS.CUSTOMER_TYPE", "Customer Account.CustomerType", "Value-set normalization", "Align EBS customer type values to Fusion enterprise values."],
        ["HZ_CUST_ACCOUNTS.STATUS", "Customer Account.Status", "Normalize status codes", "Example: A/I to Active/Inactive or equivalent enterprise standard."],
        ["HZ_CUST_ACCOUNTS.CUSTOMER_CLASS_CODE", "Customer Account.AccountClass", "Crosswalk to target class values", "Use controlled reference-data mapping."],
        ["HZ_CUST_ACCOUNTS.ATTRIBUTE_CATEGORY + ATTRIBUTE columns", "Fusion DFF/EFF", "Map only approved extensions", "Keep custom attributes separate from core Day-1 mapping."],
        ["Constant 'EBS'", "Customer Account.SourceSystem", "Default / derived", "Recommended for migration lineage."],
        ["HZ_CUST_ACCOUNTS.ORIG_SYSTEM_REFERENCE or legacy surrogate key", "Customer Account.SourceSystemReferenceValue", "Direct", "Preserve legacy cross-reference for reconciliation."],
        ["HZ_CUST_ACCT_SITES_ALL site identifier", "Customer Account Site.SiteNumber / Site reference", "Direct or derived", "Use a stable site key during conversion."],
        ["HZ_LOCATIONS.ADDRESS1", "Customer Account Site.AddressLine1", "Direct", "Required for valid site creation."],
        ["HZ_LOCATIONS.ADDRESS2", "Customer Account Site.AddressLine2", "Direct", "Optional."],
        ["HZ_LOCATIONS.ADDRESS3", "Customer Account Site.AddressLine3", "Direct", "Optional."],
        ["HZ_LOCATIONS.CITY", "Customer Account Site.City", "Direct", "Core address component."],
        ["HZ_LOCATIONS.STATE", "Customer Account Site.State", "Direct", "Normalize abbreviations where needed."],
        ["HZ_LOCATIONS.POSTAL_CODE", "Customer Account Site.PostalCode", "Direct + format validation", "Apply country-sensitive postal validation."],
        ["HZ_LOCATIONS.COUNTRY", "Customer Account Site.Country", "Normalize to target country code standard", "Prefer ISO-style target representation."],
        ["HZ_CUST_SITE_USES_ALL.SITE_USE_CODE = 'BILL_TO'", "Customer Account.BillToSite / Customer Site Use.BillTo", "Derive from site-use rows", "Build bill-to association from active site-use records."],
        ["HZ_CUST_SITE_USES_ALL.SITE_USE_CODE = 'SHIP_TO'", "Customer Account.ShipToSite / Customer Site Use.ShipTo", "Derive from site-use rows", "Build ship-to association from active site-use records."],
        ["HZ_CUST_SITE_USES_ALL.STATUS", "Customer Site Use.Status", "Normalize status", "Ensure inactive site uses do not become transactable in Fusion."],
        ["HZ_CONTACT_POINTS.EMAIL_ADDRESS", "Customer Account.EmailAddress or Customer Contact.EmailAddress", "Direct", "Prefer contact-level load when multiple contacts exist."],
        ["HZ_CONTACT_POINTS.PHONE_NUMBER / RAW_PHONE_NUMBER", "Customer Account.PhoneNumber or Customer Contact.PhoneNumber", "Standardize phone format", "Apply country code and punctuation normalization."],
        ["HZ_ORG_CONTACTS / HZ_RELATIONSHIPS contact person name", "Customer Account.PrimaryContactName", "Derive primary contact", "Use business rule to choose default contact."],
        ["HZ_CUSTOMER_PROFILES.STANDARD_TERMS or terms reference", "Customer Account.PaymentTerms", "Lookup to target terms name/code", "Validate against Fusion payment-terms setup."],
        ["HZ_CUSTOMER_PROFILES.STATEMENT_CYCLE_ID / statement reference", "Customer Profile.StatementCycle", "Lookup / translate", "Use only where statement processing is in scope."],
        ["HZ_CUSTOMER_PROFILES.COLLECTOR_ID", "Customer Account.Collector", "Lookup ID to collector name/code", "Requires reference-data crosswalk."],
        ["HZ_CUST_PROFILE_AMTS overall credit limit", "Customer Account.CreditLimit", "Numeric conversion", "Preserve currency context and rounding rules."],
        ["HZ_CUSTOMER_PROFILES.CREDIT_CLASSIFICATION", "Customer Account.CreditClassification", "Reference-data mapping", "Normalize to Fusion credit policy values."],
        ["HZ_PARTIES.SIC_CODE / industry attribute or equivalent", "Customer Account.Industry", "Crosswalk", "Optional, enterprise-specific."],
        ["HZ_CUST_ACCOUNTS.SALES_CHANNEL_CODE or equivalent", "Customer Account.SalesChannel", "Reference-data mapping", "Optional, depends on target reporting model."],
        ["HZ_CUST_ACCOUNTS.MARKET_SEGMENT_CODE or equivalent", "Customer Account.MarketSegment", "Reference-data mapping", "Optional, depends on target segmentation design."],
        ["ZX_PARTY_TAX_PROFILE / EBS tax registration number", "Customer Account.TaxpayerIdentificationNumber", "Direct + tax-format validation", "Validate by country/jurisdiction."],
        ["EBS tax classification source", "Customer Account.TaxClassification", "Crosswalk", "Map to Fusion-supported tax classification values."],
    ]
    return rows_from_iterable(header, rows)


def object_summary_rows() -> List[List[str]]:
    header = ["Canonical Domain", "Fusion Target Object", "Primary EBS Sources", "Purpose"]
    rows = [
        ["Party", "Party", "HZ_PARTIES", "Preserve legal and trading identity of the customer."],
        ["Customer Account", "Customer Account", "HZ_CUST_ACCOUNTS + HZ_PARTIES", "Core receivables account and business classification."],
        ["Customer Account Site", "Customer Account Site", "HZ_CUST_ACCT_SITES_ALL + HZ_PARTY_SITES + HZ_LOCATIONS", "Account-level address and site relationship."],
        ["Customer Site Use", "Customer Site Use", "HZ_CUST_SITE_USES_ALL", "Operational site usage such as bill-to and ship-to."],
        ["Customer Contact", "Customer Contact", "HZ_CONTACT_POINTS + HZ_ORG_CONTACTS / HZ_RELATIONSHIPS", "Primary and operational customer contacts."],
        ["Customer Profile", "Customer Profile / Credit Profile", "HZ_CUSTOMER_PROFILES + HZ_CUST_PROFILE_AMTS", "Terms, collector, statement, credit, and collections attributes."],
        ["Customer Tax Profile", "Customer Tax Profile", "ZX_PARTY_TAX_PROFILE or equivalent tax source", "Tax registration and tax classification mapping."],
    ]
    return rows_from_iterable(header, rows)


def main() -> int:
    sheets = [
        ("Canonical_Model", canonical_model_rows()),
        ("Mapping_Detail", mapping_detail_rows()),
        ("Object_Summary", object_summary_rows()),
    ]
    write_excel_workbook(OUTPUT_PATH, sheets)
    print(f"Example workbook created: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
