# Fusion Data Extraction Decision Guide

## Selection matrix

| Option | Best for | Volume | Mode | Typical output | Notes |
|---|---|---:|---|---|---|
| Fusion Desktop Integration / UI export | one-off user export | low | user-driven | excel, csv | not an architecture choice for recurring extracts |
| Export Management | cx object export | high | batch | csv | purpose-built for cx export |
| HCM Extracts | hcm outbound extracts | high | batch | csv, xml, excel, html, rtf, pdf | purpose-built for hcm |
| Financial Reporting Center | financial statements for users | medium | user-driven | excel | reporting only |
| Item / Product Data Publication | product hub item publication | high | batch / async | xml | item-focused pattern |
| OTBI | ad hoc analytics and light export | low | user-driven | excel, xml | reporting only; not extraction architecture |
| BIP | formatted reports | medium | batch | word, excel, pdf, rtf, html | avoid custom-sql extraction pattern |
| BICC | bulk outbound replication | high | batch | csv | supports incremental extract |
| REST API | object-level integration | very low | real-time | json | do not use for bulk export |
| SOAP services | legacy or missing-rest integration | very low | real-time | xml | fallback when rest is not suitable |
| Fusion Analytics Warehouse | prebuilt analytics | high | batch | managed analytics | subscription and platform decision |

## Guardrails

### Strong recommendations
- prefer purpose-built extraction utilities first
- choose BICC for recurring bulk outbound replication from ERP, SCM, and often CX
- choose HCM Extracts for HCM extraction needs
- choose REST for real-time, low-volume retrieval

### Explicit cautions
- do not recommend OTBI for bulk extracts or synchronous integrations
- do not frame BIP as the default data extraction platform
- avoid REST and SOAP for large datasets
- do not recommend UI export for automated interfaces

## Questions that change the answer

1. Is the requirement reporting for humans or data movement for systems?
2. Is the interface batch, near real-time, or real-time?
3. Is the data volume high enough to require a bulk extractor?
4. Is incremental extract required?
5. Is there a pillar-specific utility that already fits the object domain?
6. Is the target a warehouse / lake / analytics platform or another transactional application?

## Realistic prompt examples

### Prompt 1
A customer is implementing Fusion ERP and SCM and wants nightly full plus incremental extracts into OCI Object Storage for a downstream enterprise data warehouse. They are considering OTBI, BIP, BICC, and REST. Which option should they use and why?

Expected answer shape:
- recommend BICC
- explain batch, high volume, warehouse replication, incremental support
- reject OTBI and BIP as reporting-oriented
- reject REST as too chatty for bulk extraction

### Prompt 2
A customer needs a scheduled worker and assignment extract from Fusion HCM, delivered as CSV and XML to a payroll processor. They are comparing HCM Extracts, BICC, and REST.

Expected answer shape:
- recommend HCM Extracts
- explain HCM-specific, scheduled, high-volume, multi-format fit
- narrow BICC to analytics scenarios
- narrow REST to real-time low-volume only

### Prompt 3
A CX team wants a one-time export of customer and opportunity objects to CSV for offline review and data enrichment.

Expected answer shape:
- recommend Export Management
- mention BICC only if this becomes a recurring broad replication pattern
- keep OTBI in the ad hoc analytics lane
