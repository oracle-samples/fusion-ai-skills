## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# A-Team Fusion Integration Design Assistant

Create Oracle Integration Cloud (OIC) integration design documents from business requirements. The skill produces a Markdown design and a PDF version, with architecture, adapters, payload handling, security, scalability, error handling, operations, testing, risks, assumptions, and relevant Oracle A-Team references.

## How to Use

Use the skill when you need an implementation-ready OIC design rather than a short recommendation.

1. Start with a business requirement. Include source and target systems, business trigger, expected payload, volume, latency, security constraints, and known integration preferences when available.
2. Invoke the skill with a prompt such as: `Use $fusion-integration-design-assistant to create an OIC design for the following requirement...`
3. The skill classifies the integration pattern, opens `references/index.md`, then loads only the relevant category reference files.
4. The skill creates a Markdown document under `output/designs/`.
5. The skill generates a polished PDF and checks layout where possible before delivery.

Recommended minimum input:

- Business process and purpose.
- Source and target applications.
- Trigger type: event, schedule, API call, file arrival, or manual run.
- Key entities and payload fields.
- Expected volume and latency.
- Authentication and network constraints.
- Error handling or replay expectations.

## Reference Organization

`SKILL.md` is intentionally a compact router. Detailed source guidance lives under `references/`:

- `index.md`: start here; maps user topics to the right reference files.
- `source-ranking-rules.md`: rules for choosing and citing sources.
- `connectivity-networking.md`: private endpoints, network flows, connectivity agent, cross-tenancy/private OCI resources.
- `event-driven.md`: event channels, subscribers, item load/status events, order status events, replay and duplicates.
- `cpq.md`: Oracle CPQ quote, pricing, configuration, and order handoff patterns.
- `file-based.md`: SFTP, object storage, CSV/XML files, batch, archive/error folders, reprocessing.
- `error-handling.md`: retries, scheduled recovery, fault handling, replay, idempotency.
- `identity-propagation.md`: end-user identity propagation and service-account tradeoffs.
- `security-authentication.md`: OAuth, IAM domains, SOAP JWT, TLS, secrets, least privilege.
- `observability-operations.md`: OIC tracking fields, Logging Analytics, dashboards, alerts, runbooks.
- `fusion-extraction.md`: Fusion extraction options, delta strategy, BICC/BIP/REST/SOAP/event choices.

The skill should not read every reference file for every request. It should select only the most relevant files and cite only the sources that materially influenced the design.

## Output Checklist

The generated design should include these sections in order:

- Purpose and Scope
- Functional Requirement
- Assumptions
- Pattern Selection and Rationale
- High-Level Architecture
- Sequence (Logical)
- Security Architecture
- Scalability and Performance Design
- Error Handling, Replay, and Recovery
- Monitoring and Operations
- Testing Strategy
- Risks and Mitigations
- Assumptions and Open Decisions
- References

Before delivery, confirm:

- The Markdown file is complete and saved under `output/designs/`.
- The PDF file is generated under `output/designs/`.
- The selected pattern matches the requirement and rejected alternatives are explained when useful.
- Trigger, invokes, adapters, endpoint paths, payload handling, and tracking identifiers are explicit.
- Retry, replay, idempotency, duplicate handling, and recovery steps are implementable.
- Security covers authentication, authorization, secrets, network path, TLS, and identity propagation where relevant.
- Scalability covers volume, concurrency, payload size, batching, throttling, pagination, scheduling windows, and target limits.
- Monitoring covers OIC tracking fields, correlation IDs, structured logs, alerts, dashboards, and operations ownership.
- References include only Oracle docs and A-Team sources that materially influenced the design.
- The PDF has clean page breaks, readable tables, and complete source links.

## Sample Prompts
- $fusion-integration-design-assistant I want to synchronize Items from PDH into an ATP database hosted in the same region of OCI but a different tenancy from the Fusion SaaS instance. Create a design for this integration. The key requirements are: hourly sync of Fusion SaaS Items into ATP database, skip the integration if there are no delta updates to Items in Fusion PDH, and handle peak volumes of 20,000 items per hour.
- Use $fusion-integration-design-assistant Create a design for an Fusion HCM OIC integrations which are called from Front end Custom Timecard application. Integration should fetch all current open timecards from Fusion HCM. Application users are Line Managers. The timecards should be accessed from HCM using the user context. User will further view and approve selected timecards, which is outside the integration scope.
- Use A-Team Fusion Integration Design Assistant to create a file-based OIC design that picks up supplier CSV files from SFTP, validates records, archives processed files, rejects invalid rows, and loads valid data into Fusion Procurement. The expected volume is about 100 suppliers expected per day.
- $fusion-integration-design-assistant Create a design for event based integration from Fusion Order management to CPQ. Order status update events should be interfaced using CPQ REST API. The integration should scale to peak volumes of 10000 events per hour and have built in error handling to reprocess failed event processing