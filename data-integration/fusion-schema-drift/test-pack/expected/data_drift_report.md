# Data Drift Report

Generated at: 2026-04-24T12:45:58.553199+00:00

## Severity Summary

- critical: 4
- high: 8
- medium: 0
- low: 0
- info: 0

## Critical Findings & Immediate Actions

- **AP_INVOICES::-** (row_count_drop): Check extraction filters, incremental watermark logic, and source job status.
- **AP_INVOICES::AMOUNT** (numeric_mean_shift): Validate business meaning and refresh model/aggregation baselines.
- **AP_INVOICES::SUPPLIER_ID** (distinct_count_shift): Review source domain changes and update reference mappings.
- **AP_INVOICES::SUPPLIER_ID** (null_ratio_increase): Apply null defaulting/imputation or fix source extraction logic.

## All Findings

### CRITICAL - row_count_drop
- object: AP_INVOICES
- column: -
- message: Row count dropped for AP_INVOICES: baseline=8, current=3.
- recommended_action: Check extraction filters, incremental watermark logic, and source job status.

### CRITICAL - numeric_mean_shift
- object: AP_INVOICES
- column: AMOUNT
- message: Numeric mean shifted for AP_INVOICES.AMOUNT: baseline=1118.3500, current=2550.0000.
- recommended_action: Validate business meaning and refresh model/aggregation baselines.

### CRITICAL - distinct_count_shift
- object: AP_INVOICES
- column: SUPPLIER_ID
- message: Distinct count shifted for AP_INVOICES.SUPPLIER_ID: baseline=8, current=1.
- recommended_action: Review source domain changes and update reference mappings.

### CRITICAL - null_ratio_increase
- object: AP_INVOICES
- column: SUPPLIER_ID
- message: Null ratio increased for AP_INVOICES.SUPPLIER_ID: baseline=0.0000, current=0.6667.
- recommended_action: Apply null defaulting/imputation or fix source extraction logic.

### HIGH - categorical_domain_shift
- object: AP_INVOICES
- column: AMOUNT
- message: Categorical top-value overlap dropped for AP_INVOICES.AMOUNT: jaccard=0.0000.
- recommended_action: Review new/removed domain values and update mapping tables.

### HIGH - distinct_count_shift
- object: AP_INVOICES
- column: AMOUNT
- message: Distinct count shifted for AP_INVOICES.AMOUNT: baseline=8, current=3.
- recommended_action: Review source domain changes and update reference mappings.

### HIGH - categorical_domain_shift
- object: AP_INVOICES
- column: INVOICE_DATE
- message: Categorical top-value overlap dropped for AP_INVOICES.INVOICE_DATE: jaccard=0.0000.
- recommended_action: Review new/removed domain values and update mapping tables.

### HIGH - distinct_count_shift
- object: AP_INVOICES
- column: INVOICE_DATE
- message: Distinct count shifted for AP_INVOICES.INVOICE_DATE: baseline=8, current=3.
- recommended_action: Review source domain changes and update reference mappings.

### HIGH - categorical_domain_shift
- object: AP_INVOICES
- column: INVOICE_ID
- message: Categorical top-value overlap dropped for AP_INVOICES.INVOICE_ID: jaccard=0.0000.
- recommended_action: Review new/removed domain values and update mapping tables.

### HIGH - distinct_count_shift
- object: AP_INVOICES
- column: INVOICE_ID
- message: Distinct count shifted for AP_INVOICES.INVOICE_ID: baseline=8, current=3.
- recommended_action: Review source domain changes and update reference mappings.

### HIGH - numeric_mean_shift
- object: AP_INVOICES
- column: INVOICE_ID
- message: Numeric mean shifted for AP_INVOICES.INVOICE_ID: baseline=1004.5000, current=2002.0000.
- recommended_action: Validate business meaning and refresh model/aggregation baselines.

### HIGH - categorical_domain_shift
- object: AP_INVOICES
- column: SUPPLIER_ID
- message: Categorical top-value overlap dropped for AP_INVOICES.SUPPLIER_ID: jaccard=0.0000.
- recommended_action: Review new/removed domain values and update mapping tables.
