# Remediation Plan

Generated at: 2026-04-24T12:45:58.662449+00:00

## Severity Summary

- critical: 8
- high: 9
- medium: 0
- low: 0
- info: 0

## Critical Findings & Immediate Actions

- **data_drift:numeric_mean_shift:AP_INVOICES:AMOUNT** owner=analytics-owner decision=block
  - action: Validate business meaning and refresh model/aggregation baselines.
- **data_drift:distinct_count_shift:AP_INVOICES:SUPPLIER_ID** owner=data-platform-owner decision=block
  - action: Review source domain changes and update reference mappings.
- **data_drift:null_ratio_increase:AP_INVOICES:SUPPLIER_ID** owner=data-quality-owner decision=block
  - action: Apply null defaulting/imputation or fix source extraction logic.
- **schema_drift:column_type_changed:AP_INVOICES:AMOUNT** owner=data-transform-owner decision=block
  - action: Update transform casts and AI DP contract type mappings.
- **schema_drift:column_removed:AP_INVOICES:INVOICE_ID** owner=data-transform-owner decision=block
  - action: Create transform fallback or restore column extraction before deployment.
- **schema_drift:type_mismatch:AP_INVOICES:AMOUNT** owner=odt-model-owner decision=block
  - action: Add deterministic cast/format transform before loading to ODT.
- **schema_drift:type_mismatch:AP_INVOICES:SUPPLIER_ID** owner=odt-model-owner decision=block
  - action: Add deterministic cast/format transform before loading to ODT.
- **data_drift:row_count_drop:AP_INVOICES:-** owner=pipeline-operations-owner decision=block
  - action: Check extraction filters, incremental watermark logic, and source job status.

## Prioritized Action Queue

### CRITICAL - numeric_mean_shift
- action_id: data_drift:numeric_mean_shift:AP_INVOICES:AMOUNT
- source_report: data_drift
- owner: analytics-owner
- release_decision: block
- object: AP_INVOICES
- column: AMOUNT
- recommended_action: Validate business meaning and refresh model/aggregation baselines.

### CRITICAL - distinct_count_shift
- action_id: data_drift:distinct_count_shift:AP_INVOICES:SUPPLIER_ID
- source_report: data_drift
- owner: data-platform-owner
- release_decision: block
- object: AP_INVOICES
- column: SUPPLIER_ID
- recommended_action: Review source domain changes and update reference mappings.

### CRITICAL - null_ratio_increase
- action_id: data_drift:null_ratio_increase:AP_INVOICES:SUPPLIER_ID
- source_report: data_drift
- owner: data-quality-owner
- release_decision: block
- object: AP_INVOICES
- column: SUPPLIER_ID
- recommended_action: Apply null defaulting/imputation or fix source extraction logic.

### CRITICAL - column_type_changed
- action_id: schema_drift:column_type_changed:AP_INVOICES:AMOUNT
- source_report: schema_drift
- owner: data-transform-owner
- release_decision: block
- object: AP_INVOICES
- column: AMOUNT
- recommended_action: Update transform casts and AI DP contract type mappings.

### CRITICAL - column_removed
- action_id: schema_drift:column_removed:AP_INVOICES:INVOICE_ID
- source_report: schema_drift
- owner: data-transform-owner
- release_decision: block
- object: AP_INVOICES
- column: INVOICE_ID
- recommended_action: Create transform fallback or restore column extraction before deployment.

### CRITICAL - type_mismatch
- action_id: schema_drift:type_mismatch:AP_INVOICES:AMOUNT
- source_report: schema_drift
- owner: odt-model-owner
- release_decision: block
- object: AP_INVOICES
- column: AMOUNT
- recommended_action: Add deterministic cast/format transform before loading to ODT.

### CRITICAL - type_mismatch
- action_id: schema_drift:type_mismatch:AP_INVOICES:SUPPLIER_ID
- source_report: schema_drift
- owner: odt-model-owner
- release_decision: block
- object: AP_INVOICES
- column: SUPPLIER_ID
- recommended_action: Add deterministic cast/format transform before loading to ODT.

### CRITICAL - row_count_drop
- action_id: data_drift:row_count_drop:AP_INVOICES:-
- source_report: data_drift
- owner: pipeline-operations-owner
- release_decision: block
- object: AP_INVOICES
- column: -
- recommended_action: Check extraction filters, incremental watermark logic, and source job status.

### HIGH - numeric_mean_shift
- action_id: data_drift:numeric_mean_shift:AP_INVOICES:INVOICE_ID
- source_report: data_drift
- owner: analytics-owner
- release_decision: warn
- object: AP_INVOICES
- column: INVOICE_ID
- recommended_action: Validate business meaning and refresh model/aggregation baselines.

### HIGH - distinct_count_shift
- action_id: data_drift:distinct_count_shift:AP_INVOICES:AMOUNT
- source_report: data_drift
- owner: data-platform-owner
- release_decision: warn
- object: AP_INVOICES
- column: AMOUNT
- recommended_action: Review source domain changes and update reference mappings.

### HIGH - distinct_count_shift
- action_id: data_drift:distinct_count_shift:AP_INVOICES:INVOICE_DATE
- source_report: data_drift
- owner: data-platform-owner
- release_decision: warn
- object: AP_INVOICES
- column: INVOICE_DATE
- recommended_action: Review source domain changes and update reference mappings.

### HIGH - distinct_count_shift
- action_id: data_drift:distinct_count_shift:AP_INVOICES:INVOICE_ID
- source_report: data_drift
- owner: data-platform-owner
- release_decision: warn
- object: AP_INVOICES
- column: INVOICE_ID
- recommended_action: Review source domain changes and update reference mappings.

### HIGH - missing_optional_column
- action_id: schema_drift:missing_optional_column:AP_INVOICES:INVOICE_ID
- source_report: schema_drift
- owner: data-platform-owner
- release_decision: warn
- object: AP_INVOICES
- column: INVOICE_ID
- recommended_action: Add source mapping or revise target schema contract.

### HIGH - categorical_domain_shift
- action_id: data_drift:categorical_domain_shift:AP_INVOICES:AMOUNT
- source_report: data_drift
- owner: reference-data-owner
- release_decision: warn
- object: AP_INVOICES
- column: AMOUNT
- recommended_action: Review new/removed domain values and update mapping tables.

### HIGH - categorical_domain_shift
- action_id: data_drift:categorical_domain_shift:AP_INVOICES:INVOICE_DATE
- source_report: data_drift
- owner: reference-data-owner
- release_decision: warn
- object: AP_INVOICES
- column: INVOICE_DATE
- recommended_action: Review new/removed domain values and update mapping tables.

### HIGH - categorical_domain_shift
- action_id: data_drift:categorical_domain_shift:AP_INVOICES:INVOICE_ID
- source_report: data_drift
- owner: reference-data-owner
- release_decision: warn
- object: AP_INVOICES
- column: INVOICE_ID
- recommended_action: Review new/removed domain values and update mapping tables.

### HIGH - categorical_domain_shift
- action_id: data_drift:categorical_domain_shift:AP_INVOICES:SUPPLIER_ID
- source_report: data_drift
- owner: reference-data-owner
- release_decision: warn
- object: AP_INVOICES
- column: SUPPLIER_ID
- recommended_action: Review new/removed domain values and update mapping tables.
