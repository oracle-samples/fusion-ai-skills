---
name: boss-extract-automation
description: create, schedule, monitor, troubleshoot, and download boss and tems extracts from oracle fusion using the bundled automation. use when chatgpt needs to help run extract jobs, validate business views, monitor ess or saas-batch status, download output files, or troubleshoot this specific extract automation workflow.
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# BOSS Extract Automation

## When to use this skill
Use this skill when the user needs help with BOSS/TEMS extract automation in this repository, including:

- Creating or running a BOSS extract from a business view.
- Scheduling immediate, hourly, weekly, or custom recurring extract jobs.
- Monitoring ESS or SaaS-Batch job status.
- Downloading generated output files.
- Troubleshooting configuration, API, polling, or duplicate-name errors.
- Extending the extract automation for new business views or filters.

Do not use this skill for unrelated Oracle Fusion tasks, live credential management, or database changes outside the read-only metadata access used by the existing scripts.

## How to use this skill
1. Identify the requested outcome: run an extract, schedule it, troubleshoot a failure, or extend the automation.
2. Gather the minimum required inputs before execution.
3. Follow the core procedure in this file first.
4. Load additional resources only when needed:
   - `references/INSTRUCTIONS.md` for setup and configuration-driven CLI usage.
   - `references/WORKFLOWS.md` for step-by-step process flows.
   - `references/CHECKLISTS.md` for pre-run, execution, validation, and troubleshooting checks.
   - `references/KNOWLEDGE_BASE.md` for environment variables, endpoints, scripts, and domain concepts.
   - `references/EXAMPLES.md` for example prompts, actions, and expected outputs.
   - `assets/.env` for environment and secret values.
   - `assets/mapping.json` for PVO to business-view mappings.
   - `assets/extract_config.json` for non-secret extract runtime defaults.

This skill is designed for progressive disclosure: use this `SKILL.md` as the activation entrypoint and only open the supporting files that are relevant to the current task.

## Folder structure
- `SKILL.md` — activation entrypoint with metadata and core operating guidance.
- `references/` — supporting documentation loaded on demand.
- `scripts/` — portable execution helpers or wrappers for this skill.
- `assets/` — environment values, mapping data, extract runtime configuration, and offline fixtures.
- `requirements.txt` — deterministic Python dependencies for this skill.

## Required inputs
- Valid `command` choice for the script (`run`, `preflight`, `validate-view`, `create-extract`, `monitor`, `download`).
- Environment variables and credentials configured in `assets/.env`.
- A valid default mapping in `assets/mapping.json`.
- Runtime defaults configured in `assets/extract_config.json`.

## Optional inputs
- Updates to `assets/extract_config.json` when you need custom names, filters, polling behavior, metadata source selection, fixture usage, catalog CSV usage, or scheduling parameters.
- Updates to `assets/mapping.json` when you need a different default PVO/business view.

## Minimum working setup
1. Install dependencies: `python -m pip install -r ai_skills/boss_extract_automation/requirements.txt`
2. Populate the required environment variables in `assets/.env`.
3. Confirm `assets/mapping.json` points to the desired default business view/PVO.
4. Confirm `assets/extract_config.json` contains the intended runtime defaults.
5. First run: `python ai_skills/boss_extract_automation/scripts/GenerateTEMS_Extracts.py preflight`
4. Expected success output: JSON with `"status": "ok"` and no `missing_env` or `missing_dependencies`.

## Core operating procedure
1. Run preflight first:
   - Confirm Python dependencies are installed.
   - Confirm required environment variables are present.
   - Confirm wallet path exists.
   - Confirm output directory is writable.
   - Optionally confirm BOSS/IDCS hosts are reachable.
2. Choose the right stage:
   - `preflight`
   - `validate-view`
   - `create-extract`
   - `monitor`
   - `download`
   - `run` for full end-to-end flow
3. Update `assets/extract_config.json` to control dry-run, polling, metadata source selection, filters, and schedule behavior.
4. Choose metadata mode in `assets/extract_config.json`:
   - `metadata_source: "auto"` → fixture first if provided, then mapping + catalog CSV, then DB fallback.
   - `metadata_source: "fixture"` → requires `metadata_fixture`.
   - `metadata_source: "mapping"` → uses `mapping.json` + `catalog_csv_path`.
   - `metadata_source: "db"` → forces Oracle DB metadata lookup.
5. Use `metadata_fixture` only when fixture mode is desired, or as the first preference in `auto` mode.
6. Capture the JSON summary fields: status, failed_step, missing_dependencies, missing_env, created_ids, downloaded_files.
7. If execution fails, use the troubleshooting checklist and report concrete recovery steps.

## Expected outputs
- Created export definitions and groups.
- Scheduled extract jobs with IDs.
- Polled status reports from ESS and SaaS-Batch.
- Downloaded output files such as ZIP archives.
- Error diagnostics, likely causes, and next-step recovery guidance.

## Boundaries
- Relies on pre-configured environment variables and does not manage credentials.
- Limited to read-only database queries for metadata.
- Does not modify external systems beyond the API calls already defined in the repository scripts.
- Assumes access to Oracle Fusion APIs and handles common operational cases, not every possible edge case.

## Success criteria
- Extract runs complete with `SUCCEEDED` status.
- Files are downloaded to the expected output directory.
- Key IDs, timestamps, and status transitions are captured and reportable.
- Errors are surfaced clearly with actionable retry or recovery guidance.