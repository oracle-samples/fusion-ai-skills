## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# bicc-boss-mapper

## Description
Map Oracle BICC PVOs to BOSS Business View names and produce column-level CSV mappings from Oracle workbooks following the naming pattern Business_Object_Views_to_BICC_Database_Mapping_<version>.xlsx. Use this skill when a user asks which BOSS Business View replaces a BICC PVO, requests the corresponding Business View name, needs column mapping between a PVO and a BOSS view, or wants bulk mapping for multiple PVOs from the Master tab of the Oracle workbook.

## Quick Start
Use this starter prompt:
- "Map this PVO to its BOSS Business View for Fusion 26B and show the replacement name only."

## Inputs:
- Oracle workbook: Business_Object_Views_to_BICC_Database_Mapping_<version>.xlsx
- Fusion version (or infer from workbook filename)
- Requested PVO name(s) or pvo-file path for bulk mode
- Output preference: conversational answer and/or CSV mapping export

## Outputs:
- Business View replacement for each requested PVO
- CSV column mapping with source/target attributes and notes
- Not-found list for unmatched PVOs
- Version-aware summary of what was mapped

## Workflow:
1. Validate workbook presence, readability, and Fusion version context
2. Use Master sheet as authoritative source and run mapping script
3. Resolve single or bulk PVO lookups without guessing missing matches
4. Generate conversational summary and optional CSV export
5. Report mapped count, not-found PVOs, and workbook/version used

## Prompts:
- "Map this PVO to its BOSS Business View for Fusion 26B and show the replacement name only."
- "Generate CSV column mappings for these PVOs and save the file under `outputs/`."
- "Review this workbook and list any requested PVOs that are not found in Master."
- "Explain the mapping result in plain language and then ask if I want column-level details."

## References
- `SKILL.md`
