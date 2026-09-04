---
name: bicc-boss-mapper
description: Map Oracle BICC PVOs to BOSS Business Views and output deterministic JSON/CSV from Business_Object_Views_to_BICC_Database_Mapping_<version>.xlsx.
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# BICC → BOSS Mapping Skill (Compact)

## Behavior Priorities
1. Accuracy over completeness.
2. Deterministic outputs.
3. Minimal verbosity (be brief unless user asks for explanation).
4. Do not generate summaries when files are provided. If content is too long, generate a csv to download the mapping report
5. Tool-first execution: do not answer from memory when workbook/path is available.

## Runtime Contract (Strict)
- For mapping requests, ALWAYS use `scripts/map_bicc_to_boss.py`.
- Return script stdout JSON as-is (no markdown wrapper, no prose before/after).
- If the user asks for a human explanation, provide it only after the JSON block and keep it brief.
- Never produce bullet-list mappings unless explicitly requested as prose.
- If the request implies column-level mapping or long output, force `mode=columns` and return `csv_path` payload.

## Source of Truth
- Workbook: `Business_Object_Views_to_BICC_Database_Mapping_<version>.xlsx`
- Sheet: `Master` only.
- Never fabricate mappings.

## Required Preconditions
- Workbook is mandatory. If missing: `Please upload the Oracle mapping workbook to proceed.`
- Required `Master` headers:
  - Pillar
  - Business View Label
  - Business View Name
  - View Object
  - View Object Attribute
  - Business View Attribute
  - Database Table
  - Database Column
- If missing sheet/headers: `Invalid workbook: Missing 'Master' sheet or required columns.`
- If unreadable: `Unable to read the workbook. Please upload a valid file.`

## Version Resolution
Priority:
1. User-provided version
2. Extract from filename (`<version>`)
3. Ask user if unclear

Always include `version` in JSON responses.

## Matching Rules
- Match requested PVO to `View Object`.
- Normalize for matching only: case-insensitive, trim whitespace, ignore underscores vs spaces.
- If not found: `{ "pvo": "...", "reason": "not present in workbook" }`

## Invocation Patterns
- One PVO quick lookup:
  - `python scripts/map_bicc_to_boss.py <workbook> --pvo "<PVO>" --mode single`
- Multiple PVOs:
  - `python scripts/map_bicc_to_boss.py <workbook> --pvo-file <file> --mode summary`
- Column mapping export:
  - `python scripts/map_bicc_to_boss.py <workbook> --pvo-file <file> --mode columns --csv-out <absolute_path>`

## Response Guardrails for ChatGPT Skill
- If user says “give me mapping for these PVOs” and attaches many items, prefer `mode=columns`.
- Avoid inline long mapping lists in chat.
- If context is near limit, return compact JSON + file path only.

## Modes
`--mode {single,summary,columns}` (default: `summary`)

### Global output rules
- stdout must be JSON only.
- No narrative text in stdout.
- Deterministic key order.
- No extra keys beyond the mode contract.

### `mode=single`
- Input: exactly 1 PVO (else error).
- Output keys exactly:
```json
{
  "version": "...",
  "pvo": "...",
  "business_view_name": "...",
  "pillar": "...",
  "match_type": "exact"
}
```

### `mode=summary`
- Input: one or more PVOs.
- Output keys exactly:
```json
{
  "version": "...",
  "requested_pvos": ["..."],
  "found_count": 0,
  "not_found_count": 0,
  "not_found": [
    {"pvo": "...", "reason": "not present in workbook"}
  ]
}
```

### `mode=columns`
- Trigger: user requests columns/mapping.
- Always write CSV.
- Do not return column arrays in JSON.
- Default CSV path if omitted: `outputs/bicc_to_boss_mapping_<version>.csv`
- Output keys exactly:
```json
{
  "version": "...",
  "csv_path": "<repo_relative_path>",
  "row_count": 0,
  "found_count": 0,
  "not_found": [
    {"pvo": "...", "reason": "not present in workbook"}
  ]
}
```
- CSV headers (fixed order):
`version,pillar,business_view_label,business_view_name,pvo,pvo_column,business_view_column,database_table,database_column,notes`
- Mapping specifics:
  - one CSV row per `Master` record
  - `pvo = View Object`
  - `pvo_column = View Object Attribute`
  - `business_view_column = Business View Attribute`
  - preserve workbook naming exactly in output values
  - if `Business View Attribute == Not in business view`, set `notes = not in business view`

## Conversation-Length Guardrail
- Keep responses concise.
- Prefer file outputs over long inline data.
- For very large requests, process in batches and report counts + paths.
- If chat context becomes large, provide a short state summary (max 8 bullets) and ask user to continue in a new chat.
