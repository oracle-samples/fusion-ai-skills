# Sample Artifact Generators

Read this file only when you need bundled example artifacts for demonstration or workshop scaffolding.

The following scripts are hard-coded examples. They are not generic mapping engines and should not be presented as customer-specific outputs without review and adaptation.

## Customer Canonical Workbook Example

```bash
python3 fusion-data-definition-architect/scripts/generate_customer_canonical_workbook.py
```

Creates an example Excel workbook for Oracle EBS customer data mapped to Oracle Fusion ERP concepts.

Output:

```text
fusion-data-definition-architect/scripts/output/example_customer_canonical_model_ebs_to_fusion_erp.xlsx
```

## Migration Strategy Document Example

```bash
python3 fusion-data-definition-architect/scripts/generate_migration_strategy_doc.py
```

Creates an example Word document for an Oracle EBS to Oracle Fusion ERP migration strategy.

Output:

```text
fusion-data-definition-architect/scripts/output/example_data_migration_strategy_ebs_to_fusion_erp.docx
```
