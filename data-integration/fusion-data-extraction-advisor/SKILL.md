---
name: fusion-data-extraction-advisor
description: advise customers on which oracle fusion applications data extraction or reporting option to choose based on use case. use when a user asks how to extract data from fusion, or wants a recommendation across otbi, bi publisher, hcm extracts, export management, item publication, bicc, rest api, soap services, fusion analytics warehouse, or desktop export. trigger for decisions involving data volume, batch vs real-time, incremental extract, pillar fit across cx hcm erp scm, output format, analytics vs integration, external warehouse replication, and performance or security tradeoffs.
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Fusion Data Extraction Advisor

Advise on the best-fit Oracle Fusion data extraction path by first classifying the use case, then recommending the narrowest purpose-built option that matches pillar, volume, latency, and downstream usage.

## Operating workflow

1. Classify the request across these dimensions:
   - pillar: cx, hcm, erp, scm, product hub, or cross-pillar
   - primary goal: ad hoc user analysis, operational report delivery, bulk replication, real-time integration, seeded object export, or prebuilt analytics
   - volume: very low, low, medium, high
   - mode: user-driven, scheduled batch, near real-time, or real-time
   - extract shape: full, incremental, point lookup, or formatted report
   - target: spreadsheet, external application, object storage, data warehouse, analytics platform, or re-import/mass update preparation
2. Recommend one primary option.
3. Name one or two secondary options only when they are genuinely viable.
4. Explicitly call out options that are common but not recommended for this use case.
5. State assumptions and the key validation questions that remain.

## Decision logic

### 1. Start with purpose-built options

Prefer purpose-built utilities over generic reporting or service interfaces.

- **HCM Extracts**: choose for high-volume HCM object extraction, scheduled batch delivery, and multi-format output needs.
- **Export Management**: choose for CX object export in batch CSV flows.
- **Item / Product Data Publication**: choose for Product Hub item publication and asynchronous item-oriented integrations.
- **Fusion Analytics Warehouse**: choose when the requirement is prebuilt cloud analytics rather than building a custom extract pipeline.

### 2. Use BICC for bulk replication patterns

Recommend **BICC** when the request is primarily about bulk extraction from ERP, SCM, or CX to an external reporting platform, data lake, or warehouse, especially when incremental extract is needed.

Also treat BICC as the default candidate for:
- scheduled high-volume replication
- recurring outbound batch interfaces
- extract to external storage before downstream transformation
- analytics or reporting platforms that need broad object coverage

For **HCM**, do not present BICC as the general default. Position it narrowly for Fusion Analytics Warehouse / Oracle Analytics scenarios when that constraint matters.

### 3. Use REST or SOAP only for low-volume integration patterns

Recommend **REST API** for low-volume, real-time, object-level retrieval and synchronous integration patterns.

Recommend **SOAP services** only when SOAP is already mandated or the needed capability is not available through REST.

Do not recommend REST or SOAP for high-volume extraction, warehouse replication, or full dataset export.

### 4. Keep reporting tools in the reporting lane

- **OTBI**: position for user-facing analytics and light ad hoc export only, not for system-to-system extraction.
- **BI Publisher (BIP)**: position for formatted report generation and seeded report delivery, not as the primary extraction pattern for integration.
- **Financial Reporting Center**: position for financial reporting consumption, not generalized data extraction.
- **Fusion Desktop Integration / UI export**: position for one-off user exports, never as the architecture recommendation for recurring data extraction.

When OTBI or BIP comes up, explicitly explain why it is attractive but limited for extraction workloads.

## Recommendation rules

### Prefer these mappings

- **Business user wants a small slice in Excel for analysis** → OTBI or built-in UI export, with a warning that this is not an extraction architecture.
- **CX batch export of business objects** → Export Management first; BICC if the requirement is broad, recurring, high-volume replication beyond the native CX export pattern.
- **HCM scheduled outbound extract** → HCM Extracts first.
- **ERP / SCM bulk extract for warehouse or external reporting** → BICC first.
- **Product / item publication from Product Hub** → Item / Product Data Publication first.
- **Low-latency app-to-app lookup or transaction sync** → REST first, SOAP second.
- **Prebuilt cross-pillar analytics with minimal custom extraction design** → Fusion Analytics Warehouse.
- **Formatted operational report for humans** → BIP or Financial Reporting Center, but label these as reporting choices rather than extraction platforms.

### Deprioritize or reject these patterns

Do not recommend these as primary extraction architectures unless the user is explicitly talking about reporting-only needs:
- OTBI for bulk export or synchronous integrations
- custom BIP SQL for large-scale data extraction
- REST or SOAP for high-volume historical export
- UI export / desktop integration for recurring interfaces

## Response format

Use this structure unless the user asks for a different one.

### Recommended option
State the primary recommendation in one sentence.

### Why it fits
Give 3 to 5 concise bullets tied to the use case dimensions.

### Alternatives worth considering
List only viable alternatives and when they become preferable.

### Not recommended
Name the tempting but poor-fit options and the reason each is a mismatch.

### Validation questions
Ask only the questions that would materially change the recommendation, typically around:
- expected volume and frequency
- need for incremental extract
- real-time vs batch
- target platform
- pillar and object scope
- report formatting vs raw data replication

## Example classifications

### Example A
User asks: "We need nightly incremental ERP and SCM extracts into our enterprise warehouse."

Expected recommendation:
- primary: BICC
- explain: high volume, batch, incremental, outbound replication
- not recommended: OTBI, BIP custom SQL, REST/SOAP

### Example B
User asks: "HR needs a scheduled worker extract with CSV and XML outputs for a payroll downstream process."

Expected recommendation:
- primary: HCM Extracts
- alternative: REST only if the actual requirement turns out to be low-volume real-time lookup

### Example C
User asks: "Sales operations wants a one-time CSV export of CX business objects for analysis."

Expected recommendation:
- primary: Export Management
- alternative: OTBI only if the need is user analysis on a small, report-oriented slice rather than object export

### Example D
User asks: "We need customer account details in real time during order capture."

Expected recommendation:
- primary: REST API
- alternative: SOAP only if REST does not expose the required service

## Use the bundled reference

When the request needs finer distinctions, consult `references/decision-guide.md` for:
- a compact selection matrix
- guardrails by tool
- example prompts and expected recommendations

## Companion Enrichment (Inputs/Outputs/Workflow/Prompts)

This section standardizes quick-operational usage using the fusion-skill-prompt-architect pattern of explicit input/output contracts, deterministic workflow, and reusable prompt examples.

Inputs:
- Business use case, consumers, and decision objective (analytics vs integration)
- Volume/timeliness profile (batch, near-real-time, incremental, one-time)
- Functional scope across ERP/SCM/HCM/CX and object-level requirements
- Constraints on tooling, security, and downstream warehouse targets

Outputs:
- Recommended extraction/reporting option with rationale and tradeoffs
- Alternative options with risk/cost/performance comparison
- Implementation checklist aligned to selected method
- Decision summary suitable for architecture review

Workflow:
1. Capture use-case constraints and classify decision dimensions
2. Evaluate candidate methods (OTBI, BIP, BICC, REST, SOAP, FAW, exports)
3. Score options by volume, latency, governance, and maintainability fit
4. Recommend primary approach plus fallback path
5. Produce execution checklist and validation criteria

Prompts:
- Given this use case, should we use BICC, REST, or OTBI and why?
- Create a decision matrix for extraction options across ERP and SCM domains.
- Recommend a low-risk path for incremental warehouse replication from Fusion.
- What tradeoffs should I expect if I choose BI Publisher instead of BICC?

