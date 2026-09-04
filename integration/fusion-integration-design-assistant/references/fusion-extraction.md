# Fusion Applications Cloud Extraction References

Use this file when the design extracts high-volume or analytical data from Fusion Applications using reports, BICC, REST, SOAP, events, or other extraction options.

## Use first

### Data Extraction Options and Guidelines for Oracle Fusion Applications Suite
- URL: https://www.ateam-oracle.com/data-extraction-options-and-guidelines-for-oracle-fusion-applications-suite
- Type: a-team blog
- Category: Fusion Applications Cloud extraction
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: selecting a Fusion extraction mechanism based on volume, latency, object support, transformations, and downstream consumption.
- Do not use for: non-Fusion extraction designs.

## Design cues

- Match extraction mechanism to volume, latency, supported object, transformation needs, and downstream consumption.
- Include pagination, delta strategy, scheduling window, data retention, and reconciliation.
- Avoid using BIP extracts for integration use cases unless there is a strong constraint. For real-time integrations prefer Fusion REST APIs over BIP extracts. For scheduled integration use cases prefer the Data Extraction Tool or BICC for extracts over BIP when appropriate.

## Extraction decision matrix

Use this matrix when a design must choose between REST APIs, SOAP services, business events, BICC, Data Extraction Tool, BI Publisher, FBDI/output files, or product-specific publication/extract features. Prefer the narrowest supported mechanism that satisfies object coverage, latency, volume, and replay requirements.

| Extraction option | Best fit | Latency | Volume fit | Object support | Delta strategy | Pagination/chunking | Replay/recovery | Avoid or use cautiously when |
|---|---|---|---|---|---|---|---|---|
| Fusion REST APIs | Operational object sync, targeted lookup, low-to-medium volume integrations, near-real-time reads after a trigger. | Seconds to minutes, depending on schedule and throttling. | Low to medium; can support higher volumes only with proven pagination, throttling, and target load tests. | Only objects exposed by the published REST resource and configured child resources. | Query by last update timestamp or status where supported; use overlap window and deterministic ordering. | Use `limit`/`offset` or response links; avoid large expanded child payloads unless tested. | Replay by source window, page token/query, or object id; idempotent target merge required. | Avoid as the main path for very high-volume recurring extracts, very wide child payloads, or objects without reliable filter/sort support. |
| Fusion SOAP services | Service operations not available in REST, legacy service contracts, or transactional service calls. | Seconds to minutes. | Low to medium; service-call oriented. | Only supported SOAP service operations. | Operation dependent; often requires explicit query criteria. | Service dependent; may require manual batching. | Replay by request criteria or object id; preserve request/response metadata. | Avoid for bulk analytical extracts or when OAuth/JWT/certificate setup adds unnecessary complexity compared with REST or extract tools. |
| Business events | Event-driven integrations where downstream systems need notification of business changes. | Near real time. | Event volume dependent; requires durable parking for bursts. | Only events published by Fusion for the business object and lifecycle moment. | Event id and event timestamp; not a complete extract unless event payload is complete or enrichment is added. | Not page based; use queue/parking table and dispatcher batching. | Replay from event parking/dead-letter store; handle duplicate and out-of-order events. | Avoid when the requirement is full snapshot, hourly batch, analytical extract, or complete child-object replication not present in the event payload. |
| BICC incremental extract | High-volume scheduled extracts to downstream databases, lakes, warehouses, or staging files. | Batch, typically hourly/daily or scheduled windows. | High, when objects/data stores are supported and tuned. | BICC-supported view objects/data stores; validate coverage and relationships. | Incremental extract/watermark by supported last update or extract metadata. | File-based output; split by object, schedule, or configured extract size. | Replay from retained extract files and control tables; reconcile source counts to staged counts. | Avoid for low-latency request/reply needs, unsupported objects, or when business semantics require product APIs rather than data-store extracts. |
| Data Extraction Tool | Fusion Applications extract use cases where the tool supports the needed product objects and downstream file consumption. | Batch, scheduled. | Medium to high, depending on supported object and output structure. | Tool-supported Fusion objects; confirm target release coverage. | Tool-provided delta or configured source timestamp strategy. | File/object output; use manifest, checksums, and staging tables. | Replay by extract run, manifest, and output files; keep files for retention window. | Avoid if the required object is unsupported, child-update semantics are unclear, or output shape cannot be reconciled. |
| BI Publisher report | Human-readable reports, small controlled extracts, or constrained cases where no supported API/extract exists. | Batch/report runtime. | Low to limited medium; highly dependent on report SQL, bursting, and runtime limits. | Custom SQL/model coverage, but more fragile and less product-contract-like. | Custom query logic; must implement own overlap, timestamp, and reconciliation rules. | Report output files; chunking and pagination are custom and often brittle. | Replay by report parameters and retained output; harder to prove completeness. | Do not use as the default integration extract for high-volume operational sync. Avoid when supported REST, BICC, Data Extraction Tool, events, or product-specific extracts can meet the requirement. |
| Product-specific publication/extract | Product-managed exports such as item publication, order/status publication, FBDI-related outputs, or module-specific extract features. | Batch or event-like, depending on product feature. | Medium to high when designed for that business object. | Specific business object and lifecycle supported by the product feature. | Product feature dependent; may include publication criteria, last update, status, or change order logic. | Usually file/job based; use manifest/job id/output document id. | Replay by publication job, output document, file, or source object id. | Avoid if the product feature omits required fields, lacks delta semantics, or cannot expose child objects needed by the target. |
| FBDI/export files | File-oriented integration patterns, bulk import/export workflows, and staging around Fusion jobs. | Batch. | High for supported bulk file patterns. | Depends on the Fusion import/export template or job. | Usually job/file controlled; delta must be designed externally unless the job supports it. | File chunking and archive/error folders required. | Replay by file id, job id, and archive object; duplicate file detection required. | Avoid for simple low-volume API reads or where no supported export job/template exists. |

## Selection guidance

- For high-volume scheduled synchronization into ATP, ADW, data lakes, or operational replicas, start with Data Extraction Tool, BICC, or a product-specific publication/extract. Use REST only for enrichment, lookup, validation, or replay when bulk extract coverage is insufficient.
- For near-real-time notification, start with business events. Add REST/SOAP enrichment only when the event payload is not complete enough for the target.
- For user-facing or request/reply use cases, start with REST or SOAP APIs and explicitly design throttling, timeout, and retry behavior.
- For file-based partner or bulk integration, use product-specific file/FBDI patterns or SFTP/Object Storage staging, with archive, duplicate detection, and replay rules.
- Use BI Publisher only when other supported integration mechanisms do not cover the requirement, the expected volume is modest, and the design includes strict runtime, query, and reconciliation controls.
- Always document why the selected option fits the required latency, volume, object coverage, delta strategy, replay needs, and operational ownership.
