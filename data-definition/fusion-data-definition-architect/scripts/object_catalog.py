#!/usr/bin/env python3
"""Business-object catalog for onboarding and artifact generation.

This module maps business-facing object names to commonly used Oracle EBS
source objects and Oracle Fusion target objects so first-time users do not need
to know technical object names up front.
"""

from __future__ import annotations

from typing import Dict, List


OBJECT_CATALOG: List[Dict[str, object]] = [
    {
        "business_object": "Purchase Orders",
        "aliases": ["purchase order", "purchase orders", "po", "procurement"],
        "source_systems": ["oracle ebs", "ebs"],
        "target_modules": ["oracle fusion erp", "oracle fusion procurement", "fusion erp", "fusion procurement"],
        "source_object": "PO_HEADERS_ALL",
        "target_object": "PurchaseOrderHeader",
    },
    {
        "business_object": "Expenses",
        "aliases": ["expense", "expenses", "expense reports"],
        "source_systems": ["oracle ebs", "ebs"],
        "target_modules": ["oracle fusion erp", "oracle fusion expenses", "fusion erp", "fusion expenses"],
        "source_object": "AP_EXPENSE_REPORT_HEADERS_ALL",
        "target_object": "ExpenseReport",
    },
    {
        "business_object": "Suppliers",
        "aliases": ["supplier", "suppliers", "vendor", "vendors"],
        "source_systems": ["sap", "sap ecc", "sap s 4hana", "sap s/4hana", "s4hana", "s/4hana"],
        "target_modules": ["oracle fusion erp", "oracle fusion scm", "oracle fusion procurement", "fusion erp", "fusion scm", "fusion procurement"],
        "source_object": "LFA1",
        "target_object": "Supplier",
    },
    {
        "business_object": "Suppliers",
        "aliases": ["supplier", "suppliers", "vendor", "vendors"],
        "source_systems": ["oracle ebs", "ebs"],
        "target_modules": ["oracle fusion erp", "oracle fusion scm", "oracle fusion procurement", "fusion erp", "fusion scm", "fusion procurement"],
        "source_object": "AP_SUPPLIERS",
        "target_object": "Supplier",
    },
    {
        "business_object": "Customers",
        "aliases": ["customer", "customers", "customer accounts"],
        "source_systems": ["oracle ebs", "ebs"],
        "target_modules": ["oracle fusion erp", "oracle fusion receivables", "fusion erp", "fusion receivables"],
        "source_object": "HZ_CUST_ACCOUNTS",
        "target_object": "CustomerAccount",
    },
    {
        "business_object": "Payables Invoices",
        "aliases": ["payables invoice", "payables invoices", "ap invoice", "ap invoices"],
        "source_systems": ["oracle ebs", "ebs"],
        "target_modules": ["oracle fusion erp", "oracle fusion payables", "fusion erp", "fusion payables"],
        "source_object": "AP_INVOICES_ALL",
        "target_object": "PayablesInvoice",
    },
    {
        "business_object": "Receivables Invoices",
        "aliases": ["receivables invoice", "receivables invoices", "ar invoice", "ar invoices"],
        "source_systems": ["oracle ebs", "ebs"],
        "target_modules": ["oracle fusion erp", "oracle fusion receivables", "fusion erp", "fusion receivables"],
        "source_object": "RA_CUSTOMER_TRX_ALL",
        "target_object": "ReceivablesInvoice",
    },
    {
        "business_object": "Service Requests",
        "aliases": ["service request", "service requests", "sr", "support tickets", "cases"],
        "source_systems": ["oracle ebs", "ebs"],
        "target_modules": ["oracle fusion cx", "oracle fusion service", "fusion cx", "fusion service", "oracle fusion"],
        "source_object": "CS_INCIDENTS_ALL_B",
        "target_object": "ServiceRequest",
    },
]


def normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().replace("_", " ").replace("-", " ").split())


def infer_source_target_objects(source_system: str, target_module: str, business_object: str) -> Dict[str, str]:
    normalized_source = normalize(source_system)
    normalized_target = normalize(target_module)
    normalized_object = normalize(business_object)

    for item in OBJECT_CATALOG:
        aliases = [normalize(alias) for alias in item.get("aliases", [])]
        source_systems = [normalize(source) for source in item.get("source_systems", [])]
        target_modules = [normalize(module) for module in item.get("target_modules", [])]
        if normalized_object in aliases and (not source_systems or normalized_source in source_systems) and (
            not target_modules or normalized_target in target_modules
        ):
            return {
                "business_object": str(item["business_object"]),
                "source_object": str(item["source_object"]),
                "target_object": str(item["target_object"]),
                "resolution": "catalog",
                "resolution_note": "Source and target objects inferred from the onboarding catalog.",
            }

    fallback_target = "".join(ch for ch in business_object.title() if ch.isalnum()) or "BusinessObject"
    return {
        "business_object": business_object,
        "source_object": f"INFER_{fallback_target.upper()}_SOURCE",
        "target_object": fallback_target,
        "resolution": "fallback",
        "resolution_note": "No catalog match found. Source and target objects were derived heuristically and should be reviewed.",
    }
