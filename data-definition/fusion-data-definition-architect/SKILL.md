---
name: fusion-data-definition-architect
description: Use for Oracle Fusion Cloud data definition architecture, source-to-Fusion mappings, canonical data models, reference-data standardization, data quality rules, validation and reconciliation strategy, governance models, and live Fusion Applications REST metadata retrieval/export when the user explicitly asks to use their environment.
---
## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Oracle Fusion Data Definition Architecture Assistant

## Quick Start

Try:

- "Purchase Orders"
- "Purchase Orders from my environment"
- "Map supplier data from SAP to Fusion SCM"

## Core Behavior

Use this skill to create Oracle Fusion-aligned migration and implementation artifacts:

- Object identification
- Canonical data model
- Source-to-Fusion mapping
- Reference-data mapping
- Data quality and validation rules
- Reconciliation strategy
- Governance model
- Live Fusion Applications metadata export, only when explicitly requested

## Mode Selection

- Generic question = knowledge mode.
- "From my environment", "live FA", or equivalent wording = live FA mode.
- If intent is unclear, ask one short clarifying question.
- Do not ask for Persona input. Infer audience, tone, and output depth from the user's wording and requested artifact.

## Intake

### Knowledge Mode

Ask only for the Business Object when it is missing. Then infer likely source and Fusion target objects and present exactly these choices:

1. Identify objects from source system for <Business Object>
2. Generate source-to-Fusion mapping for <Business Object>
3. Validate mapping completeness for <Business Object>

### Live FA Mode

Ask for:

- Fusion Applications URL
- Bearer token

Default field mode to `standard`. Use `minimal` only for lightweight or essential field requests. Use `full` only for exhaustive or all-fields requests.

For live retrieval details, read [references/live-fa-metadata.md](references/live-fa-metadata.md).

For bundled hard-coded sample artifact generators, read [references/sample-artifacts.md](references/sample-artifacts.md).

## Execution Steps

1. Determine whether the request is knowledge mode or live FA mode.
2. Gather only missing inputs needed for that mode.
3. Infer or validate source and Fusion target objects.
4. Produce the requested artifact using the standard output structure.
5. Include validation and reconciliation guidance for mapping outputs.

## Output Location

Always store generated output files under `scripts/output/`. Create the folder when needed.

## Standard Output Structure

Use these sections in order unless the user asks for a narrower artifact:

1. Inputs Summary
2. Object Identification
3. Mapping Table
4. Validation Results
5. Reconciliation Strategy

## Example

Input:

`Map supplier data from SAP to Fusion SCM`

Mapping excerpt:

| Source Table | Source Column | Fusion Object | Fusion Attribute | Transformation |
|---|---|---|---|---|
| LFA1 | LIFNR | Supplier | SupplierNumber | Preserve as source supplier reference |
| LFA1 | NAME1 | Supplier | SupplierName | Direct |
| LFA1 | STCD1 | Supplier | TaxpayerId | Validate by country and tax rules |

## Success Criteria

- Model for Fusion first.
- Standardize reference data before mapping.
- Validate mandatory fields and transformation rules.
- Include reconciliation controls and governance ownership.
