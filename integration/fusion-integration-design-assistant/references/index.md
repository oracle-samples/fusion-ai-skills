# A-Team Fusion Integration Design Reference Index

Use this file first to choose the minimum relevant reference files for the user's requirement. Do not load every file by default.

## Source selection rules

Open `source-ranking-rules.md` whenever the design cites references, compares guidance, or needs to decide whether a blog should influence the solution.

## Connectivity, private endpoints, and network paths

Open `connectivity-networking.md` when the integration reaches private or on-premises endpoints, private Fusion endpoints, private OCI resources, cross-tenancy OCI services, or any endpoint not exposed publicly.

Typical signals: private endpoint, connectivity agent, service gateway, DRG, VCN, on-premises, firewall, DNS, TLS, private ATP, cross-tenancy.

## Event-driven integration

Open `event-driven.md` when the requirement includes business events, near-real-time processing, order status publication, item import/load completion, event channels, subscriber behavior, replay, duplicate events, or asynchronous decoupling.

## HCM integration

Open `hcm.md` when Oracle Cloud HCM participates in worker, employment, payroll, benefits, absence, recruiting, talent, or other HCM data and process integrations.

Typical signals: HCM Cloud Adapter, worker sync, employee, person, assignment, payroll, benefits, absence, recruiting, talent, HDL, HCM Extracts, workforce data.

## SCM integration

Open `scm.md` when Oracle Fusion Cloud SCM or Procurement participates in order orchestration, inventory, manufacturing, maintenance, logistics, purchasing, sourcing, supplier, requisition, receiving, or other SCM and procurement integrations.

Typical signals: SCM, Procurement, purchasing, requisition, purchase order, supplier, sourcing, receiving, inventory, manufacturing, maintenance, logistics, supply chain, FBDI, playbook.

## ERP integration

Open `erp.md` when Oracle Fusion Cloud ERP participates in financials, projects, expenses, payables, receivables, general ledger, assets, collections, cash management, or other ERP integrations.

Typical signals: ERP Cloud Adapter, financials, GL, general ledger, journal, AP, payables, AR, receivables, invoice, payment, asset, cash management, expenses, projects, FBDI.

## CPQ integration

Open `cpq.md` when Oracle CPQ participates in quote, pricing, configuration, order capture, approval, order handoff, or Fusion orchestration flows.

## File-based and batch integration

Open `file-based.md` when the requirement mentions files, CSV/XML payload drops, SFTP, object storage, scheduled batch, large payloads, archive/error folders, duplicate file detection, or bulk import.

## Error handling, scheduling, retry, and replay

Open `error-handling.md` for any design with recoverable faults, business validation errors, retries, scheduled processing, replay, compensation, dead-letter patterns, or operational recovery.

## Identity propagation and service-account security

Open `identity-propagation.md` when the design must preserve user identity, call Fusion SaaS or another target on behalf of the initiating user, compare service-account access with identity propagation, or explain audit attribution.

## Security and authentication

Open `security-authentication.md` when choosing OAuth flows, Fusion authentication, IAM domain setup, SOAP JWT authentication, TLS, secrets, least privilege, or certificate/key management.

## Observability and operations

Open `observability-operations.md` when defining monitoring, dashboards, alerts, correlation identifiers, OIC tracking fields, Logging Analytics, structured logs, retention, support diagnostics, or runbooks.

## Fusion Applications Cloud extraction

Open `fusion-extraction.md` when the design extracts high-volume or analytical data from Fusion Applications using REST, SOAP, reports, BICC, events, or other extraction options.

Typical signals: Fusion extraction, BICC, BIP, delta extract, pagination, high-volume sync, scheduled extract, reconciliation.
