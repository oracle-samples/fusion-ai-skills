## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Changelog

All notable changes to the Supplier Onboarding skill package are documented here.

## 1.2 - 2026-05-02

- Added Oracle setup and feature anchor traceability in `references/oracle_setup_feature_anchor_matrix.md`.
- Expanded golden examples for operating model, control matrix, and migration/cutover planning.
- Strengthened release validation for workbook sheets, sensitive-data scanning, required files, and traceability assets.
- Added clearer Codex installation, invocation, out-of-scope, and client-final verification guidance.
- Documented package-versus-workstream versioning expectations.
- Strengthened data-handling guidance to never reproduce full supplier bank account numbers, tax IDs, TINs, IBANs, SWIFT details, personal contact data, or uploaded supplier documents.
- Tightened prompt-handling guidance so raw bank, tax, identity, address, phone, and personal email values must be represented only with masked placeholders.
- Added a common local AI-safety block to standalone examples and workbook guidance so copied collateral preserves redaction, untrusted-input, and output-masking rules.
- Expanded validation for supplier-sensitive identifiers, all text-like package files, workbook safety terms, and risky XLSX package parts such as macros, external links, connections, queries, OLE, and ActiveX content.
- Disabled implicit invocation in production metadata so sensitive supplier-data workflows require explicit `$supplier-onboarding` invocation.
- Added a standard-library runtime redaction helper for consuming applications and documented pre-prompt, log, telemetry, response, and error masking expectations.
- Strengthened reusable prompts with explicit untrusted supplier evidence delimiters and extraction-only handling for pasted context.
- Added bounded workbook XML/text read limits to validation to reduce oversized XLSX package risk.
- Expanded address redaction for labeled, multiline, P.O. box, and international-style address patterns.
- Added strict redaction reporting APIs and CLI fail-closed mode, plus validation canaries for sensitive placeholder coverage.
- Tightened strict redaction for labeled bank-account, identity/document, postal-code, and country/address subfield values.
- Extended strict redaction to tax/VAT/GST labels and regional bank-routing labels such as sort code, BSB, branch, bank, routing, and clearing codes.
- Hardened supplier-name masking for punctuation-heavy legal names, added label-aware local phone masking, expanded supplier-sensitive scanning to all text-like package files, and added static validation before loading the redaction helper.

## 1.1 - 2026-05-02

- Added workbook assets, reusable output templates, examples, security guidance, and package validation.
- Consolidated workstream selection and quality criteria in `SKILL.md`.

## 1.0 - 2026-04-06

- Initial Supplier Onboarding skill package for Oracle EBS to Oracle Fusion transformation deliverables.
