---
name: fusion-integration-design-assistant
description: turn business requirements into oracle integration cloud integration design documents. use when chatgpt needs to create oic designs covering triggers, invokes, adapters, payload handling, error handling, retry/replay strategy, security, monitoring, performance, testing, assumptions, risks, and a-team references, with deliverables in markdown and pdf.
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# A-Team Fusion Integration Design Assistant

## Goal

Create an Oracle Integration Cloud (OIC) integration design from a business requirement. Produce both:

- A Markdown design document.
- A polished PDF generated from the Markdown.

Use A-Team guidance selectively. Cite only sources that materially influenced the design.

## Reference Routing

Treat this file as the workflow router, not the reference library.

1. Start with `references/index.md`.
2. Identify the user's integration topic, pattern, source/target systems, security model, and operational concerns.
3. Open only the most relevant category reference files listed in the index. Prefer one or two category files unless the user asks for a broad comparison or the design clearly spans several domains.
4. Apply `references/source-ranking-rules.md` when choosing between official docs, A-Team blogs, examples, and supporting references.
5. Do not read every reference file by default.
6. Do not cite all available sources. Cite only the references actually used in the design rationale.

## Required Workflow

1. Clarify only blockers. If the requirement is incomplete, make reasonable assumptions and capture them in the document. Ask the user only when missing information changes the integration pattern or security model materially.
2. Use `references/index.md` to select relevant guidance.
3. Classify the integration pattern:
   - Event-driven integration.
   - Synchronous request/reply API.
   - Scheduled orchestration.
   - File-based integration.
   - Fusion extraction/reporting integration.
   - HCM integration.
   - SCM integration.
   - ERP integration.
   - CPQ integration.
   - Hybrid pattern using private connectivity, connectivity agent, or private endpoint.
4. Design the integration explicitly:
   - Trigger, invokes, adapters, endpoints, and authentication.
   - Payload handling, enrichment, idempotency, and correlation identifiers.
   - Error handling, retry, replay, recovery, and poison-message strategy.
   - Monitoring, logging, operational ownership, and test strategy.
5. Create the Markdown document using the required section order below.
6. Generate the PDF from the final Markdown:
   - Use Python with `reportlab` when available, or an existing local Markdown-to-PDF pipeline that preserves headings, tables, lists, and references.
   - Use available local or bundled runtimes. Do not install dependencies automatically.
   - If `reportlab` is unavailable, create the Markdown deliverable, report that PDF generation could not be completed, and tell the user that `reportlab` is required.
   - Optionally use `pypdf` to validate page count, metadata, and basic text extraction.
7. Deliver paths to both final files.

## PDF Generation Prerequisites

This skill generates a PDF from the final Markdown design.

Required:

- Python with `reportlab` available.

Optional validation:

- `pypdf` for page count, metadata, and basic text extraction checks.

Do not install dependencies automatically. Use available local or bundled runtimes. If `reportlab` is unavailable, create the Markdown deliverable, report that PDF generation could not be completed, and tell the user that `reportlab` is required.

## Output File Conventions

Use stable, descriptive names derived from the integration name:

- Markdown: `output/designs/<integration-name>-design.md`
- PDF: `output/designs/<integration-name>-design.pdf`

Create directories as needed.

## Required Document Sections

Use this exact section order. Correct the typo in user-provided lists and use `Functional Requirement`.

1. Purpose and Scope
2. Functional Requirement
3. Assumptions
4. Pattern Selection and Rationale
5. High-Level Architecture
6. Sequence (Logical)
7. Security Architecture
8. Scalability and Performance Design
9. Error Handling, Replay, and Recovery
10. Monitoring and Operations
11. Testing Strategy
12. Risks and Mitigations
13. Assumptions and Open Decisions
14. References

## Section Guidance

### Purpose and Scope

State what the integration does, included systems, business process boundaries, and explicit out-of-scope items.

### Functional Requirement

Translate the user's requirement into numbered functional requirements. Include trigger conditions, business events, expected outcomes, payload expectations, and target system effects.

### Assumptions

List assumptions used to proceed with the design, such as source of truth, volume estimates, endpoint availability, identity model, payload format, and non-functional expectations.

### Pattern Selection and Rationale

Name the selected pattern and explain why it fits. Compare against at least one rejected alternative when the choice is non-obvious. Connect the rationale to A-Team guidance where relevant.

### High-Level Architecture

Describe systems, OIC integration style, adapters, trigger, invokes, network path, security boundary, logging destinations, and state/replay stores. Use Mermaid when useful:

```mermaid
flowchart LR
  Source["Source system"] --> OIC["Oracle Integration Cloud"]
  OIC --> Target["Target system"]
```

### Sequence (Logical)

Provide a logical step sequence from trigger to completion. Include validation, enrichment, routing, transformation, target invocation, acknowledgement, logging, and error path.

### Security Architecture

Cover authentication, authorization, credential storage, identity propagation if needed, OAuth/JWT choices, network access, TLS, secrets, least privilege, audit, and private endpoint/connectivity agent implications.

### Scalability and Performance Design

Cover expected volume, concurrency, throttling, payload size, batching, back pressure, scheduling windows, pagination, streaming/file chunking, timeout design, and target rate limits.

### Error Handling, Replay, and Recovery

Separate business errors, validation errors, transient technical errors, and unrecoverable errors. Specify retries, fault handlers, dead-letter or error persistence, replay approach, idempotency key, duplicate handling, and operational runbook actions.

### Monitoring and Operations

Specify dashboards, OIC tracking fields, correlation IDs, structured logs, Logging Analytics use, alerts, SLAs, ownership, deployment promotion, and support handoff.

### Testing Strategy

Include unit, mapper, contract, security, connectivity, negative, retry/replay, performance, volume, failover, and user acceptance tests. Include representative test data.

### Risks and Mitigations

List concrete risks and mitigations, especially around event loss, duplicate processing, payload drift, target throttling, security misconfiguration, network dependency, and operational replay.

### Assumptions and Open Decisions

Repeat only unresolved assumptions that require a decision. Use a table with owner, decision needed, options, recommendation, and due date when available.

### References

List the A-Team blogs and other Oracle documentation used in the design. Include title/category and URL. Do not include irrelevant blogs just because they exist in the catalog.

## Quality Bar

- Be decisive. Do not produce a generic checklist; tailor every section to the requirement.
- Make assumptions explicit instead of blocking on missing details.
- Keep architecture and sequence internally consistent with the chosen pattern.
- Include concrete adapter names where known, such as REST Adapter, SOAP Adapter, ERP Cloud Adapter, HCM Cloud Adapter, FTP/SFTP Adapter, File Adapter, Oracle CPQ Adapter, and database adapters.
- Include operational details that a build team can implement: tracking fields, fault scopes, retry thresholds, correlation IDs, and replay data.
- Ensure the PDF is generated with readable tables, clean page structure, and complete references when the required PDF dependency is available.
