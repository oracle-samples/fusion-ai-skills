# SCM Integration References

Use this file when Oracle Fusion Cloud Supply Chain Management or Procurement participates in order orchestration, inventory, manufacturing, maintenance, logistics, purchasing, sourcing, supplier, requisition, receiving, or other SCM and procurement integrations.

## Use first

### SCM Integration Playbook
- URL: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/faips/overview-of-the-scm-integration-playbooks.html
- Type: oracle documentation
- Category: SCM integration
- Relevance: high
- Authority: product documentation
- Freshness: version-sensitive
- Use when: designing Oracle Fusion SCM integrations and selecting playbook guidance for supply chain and manufacturing business processes.
- Do not use for: integrations that do not involve Oracle Fusion SCM, supply chain, manufacturing, maintenance, logistics, or inventory business processes.

### SCM PROC Integration Playbook
- URL: https://docs.oracle.com/en/cloud/saas/procurement/26b/fainp/overview-of-the-procurement-integration-playbooks.html
- Type: oracle documentation
- Category: SCM integration
- Relevance: high
- Authority: product documentation
- Freshness: version-sensitive
- Use when: designing Oracle Fusion Procurement integrations for requisitions, purchase orders, suppliers, sourcing, receiving, or procurement lifecycle processes.
- Do not use for: non-procurement SCM flows when the supply chain and manufacturing playbook is more specific.

### Implement Common Patterns Using the Oracle ERP Cloud Adapter
- URL: https://docs.oracle.com/en/cloud/paas/application-integration/erp-adapter/implement-common-patterns-using-oracle-erp-cloud-adapter.html
- Type: oracle documentation
- Category: SCM integration
- Relevance: high
- Authority: product documentation
- Freshness: version-sensitive
- Use when: designing Oracle Integration flows that use the Oracle ERP Cloud Adapter for SCM, Procurement, FBDI, business events, bulk import, or ERP/SCM service interactions.
- Do not use for: adapter-neutral SCM design decisions where the SCM or Procurement playbook is the primary source.

## Design cues

- Identify the SCM or Procurement business object, owning module, lifecycle state, source of truth, and downstream consuming process.
- Select the relevant playbook before choosing REST, SOAP, ERP Cloud Adapter, events, FBDI, BICC, or file-based patterns.
- Define orchestration boundaries, idempotency keys, lifecycle/status transitions, duplicate handling, and reconciliation controls.
- Include supply chain operational impacts such as inventory availability, fulfillment timing, supplier collaboration, receiving status, and procurement approval state where relevant.
