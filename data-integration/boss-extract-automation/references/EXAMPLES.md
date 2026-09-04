# Examples for BOSS Extract Automation Skill

## Example 1: Preflight
**Agent Prompt**: "Check whether this environment is ready for a live BOSS extract run."
**Actions**:
- Ensure `.env`, `mapping.json`, and `extract_config.json` are populated.
- Run `python ai_skills/boss_extract_automation/scripts/GenerateTEMS_Extracts.py preflight`.
**Expected Output**: JSON with `status`, `missing_env`, `missing_dependencies`, and `unsupported_environment`.

## Example 2: Offline Dry Run
**Agent Prompt**: "Validate the extract flow without touching DB or APIs."
**Actions**:
- Set `dry_run` to `true` and `metadata_fixture` to `ai_skills/boss_extract_automation/assets/metadata_fixture.json` in `extract_config.json`.
- Run `python ai_skills/boss_extract_automation/scripts/GenerateTEMS_Extracts.py run`.
**Expected Output**: JSON with `status: dry-run`, derived names, extraction query preview, and planned API calls.

## Example 3: Scheduled Extract
**Agent Prompt**: "Schedule weekly extracts on Mondays, starting now."
**Actions**:
- Update `extract_config.json` with `frequency: "Weekly"`, `frequency_days_in_week: "MON"`, and `start_time: "<current_iso>"`.
- Run script with polling after a successful preflight.
**Expected Output**: JSON containing created IDs and any downloaded files.

## Example 4: Troubleshooting
**Agent Prompt**: "Extract failed with duplicate name error."
**Actions**:
- Suggest retry with explicit `group_name` or `extract_name` in `extract_config.json`.
- Or enable auto-retry in script.
**Expected Output**: JSON showing the successful created IDs after retry.

## Example 5: Custom Filter
**Agent Prompt**: "Run extract with date filter for last month."
**Actions**:
- Set `filter_condition` in `extract_config.json` to `lastUpdateDate >= '2026-01-01'`.
- Execute and verify outputs.
**Expected Output**: JSON summary with `downloaded_files`.

These demonstrate typical interactions; adapt for your agent.