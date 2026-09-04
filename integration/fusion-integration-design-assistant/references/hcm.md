# HCM Integration References

Use this file when Oracle Cloud HCM participates in worker, employment, payroll, benefits, absence, recruiting, talent, or other HCM data and process integrations.

## Use first

### Oracle Cloud HCM Integration Using Oracle PaaS - Patterns & Use Cases
- URL: https://www.ateam-oracle.com/oracle-cloud-hcm-integration-using-oracle-paas-patterns-use-cases
- Type: a-team blog
- Category: HCM integration
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: selecting HCM integration patterns, including API, event, file, batch, PaaS, or hybrid approaches for Oracle Cloud HCM.
- Do not use for: integrations that do not involve Oracle Cloud HCM data, APIs, extracts, events, or business processes.

### Implement Common Patterns Using the Oracle HCM Cloud Adapter
- URL: https://docs.oracle.com/en/cloud/paas/application-integration/hcm-adapter/implement-common-patterns-using-oracle-hcm-cloud-adapter.html
- Type: oracle documentation
- Category: HCM integration
- Relevance: high
- Authority: product documentation
- Freshness: version-sensitive
- Use when: designing Oracle Integration flows with the Oracle HCM Cloud Adapter and its common supported patterns.
- Do not use for: non-HCM adapter designs or generic OIC patterns where a more specific reference applies.

### HCM Data Loader
- URL: https://docs.oracle.com/en/cloud/saas/human-resources/fahdl/index.html
- Type: oracle documentation
- Category: HCM data loading
- Relevance: high
- Authority: product documentation
- Freshness: version-sensitive
- Use when: designing HCM integrations that load, maintain, or bulk-import HCM business-object data using HCM Data Loader.
- Do not use for: real-time HCM API integrations, non-HCM file loads, or OIC adapter patterns where HCM Data Loader is not part of the design.

## Design cues

- Identify the HCM business object, source of truth, data sensitivity, and whether the flow is event-driven, scheduled, file-based, or request/reply.
- Use the Oracle HCM Cloud Adapter where it fits the required operation and object coverage.
- Include privacy, least privilege, audit attribution, data masking, and retention decisions for worker and employment data.
- Define reconciliation, replay, and duplicate-handling behavior for high-volume HCM extracts or recurring synchronization.
