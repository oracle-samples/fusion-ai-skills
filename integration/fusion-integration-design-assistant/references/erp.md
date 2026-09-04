# ERP Integration References

Use this file when Oracle Fusion Cloud ERP participates in financials, projects, expenses, payables, receivables, general ledger, assets, collections, cash management, or other ERP integrations.

## Use first

### Implement Common Patterns Using the Oracle ERP Cloud Adapter
- URL: https://docs.oracle.com/en/cloud/paas/application-integration/erp-adapter/implement-common-patterns-using-oracle-erp-cloud-adapter.html
- Type: oracle documentation
- Category: ERP integration
- Relevance: high
- Authority: product documentation
- Freshness: version-sensitive
- Use when: designing Oracle Integration flows that use the Oracle ERP Cloud Adapter for ERP business events, FBDI import, bulk export, callback, service invocation, or file-based ERP integration patterns.
- Do not use for: non-ERP flows where an HCM, SCM, CPQ, or generic OIC pattern reference is more specific.

## Design cues

- Identify the ERP business object, owning module, source of truth, accounting or transaction lifecycle state, and target posting or synchronization outcome.
- Use the Oracle ERP Cloud Adapter where it fits the required operation, including ERP events, FBDI imports, business object services, and callback patterns.
- Define idempotency, import job tracking, callback correlation, reconciliation, and operational replay behavior.
- Include financial controls, audit attribution, least privilege, segregation of duties, and data retention decisions where relevant.
