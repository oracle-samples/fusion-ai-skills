# Schema Drift Report

Generated at: 2026-04-24T12:45:58.331129+00:00
Mode: combined

## Severity Summary

- critical: 4
- high: 1
- medium: 0
- low: 0
- info: 0

## Critical Findings & Immediate Actions

- **AP_INVOICES::AMOUNT** (column_type_changed): Update transform casts and AI DP contract type mappings.
- **AP_INVOICES::AMOUNT** (type_mismatch): Add deterministic cast/format transform before loading to ODT.
- **AP_INVOICES::INVOICE_ID** (column_removed): Create transform fallback or restore column extraction before deployment.
- **AP_INVOICES::SUPPLIER_ID** (type_mismatch): Add deterministic cast/format transform before loading to ODT.

## All Findings

### CRITICAL - column_type_changed
- object: AP_INVOICES
- column: AMOUNT
- mode: source_drift
- message: Column AMOUNT type changed in AP_INVOICES: number -> string.
- recommended_action: Update transform casts and AI DP contract type mappings.

### CRITICAL - type_mismatch
- object: AP_INVOICES
- column: AMOUNT
- mode: target_contract
- message: Type mismatch in AP_INVOICES.AMOUNT: source=string, target=number.
- recommended_action: Add deterministic cast/format transform before loading to ODT.

### CRITICAL - column_removed
- object: AP_INVOICES
- column: INVOICE_ID
- mode: source_drift
- message: Column INVOICE_ID was removed from object AP_INVOICES.
- recommended_action: Create transform fallback or restore column extraction before deployment.

### CRITICAL - type_mismatch
- object: AP_INVOICES
- column: SUPPLIER_ID
- mode: target_contract
- message: Type mismatch in AP_INVOICES.SUPPLIER_ID: source=integer, target=number.
- recommended_action: Add deterministic cast/format transform before loading to ODT.

### HIGH - missing_optional_column
- object: AP_INVOICES
- column: INVOICE_ID
- mode: target_contract
- message: Target column INVOICE_ID in AP_INVOICES is not present in current extraction.
- recommended_action: Add source mapping or revise target schema contract.
