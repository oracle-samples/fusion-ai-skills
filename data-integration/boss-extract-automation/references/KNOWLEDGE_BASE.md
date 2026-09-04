# Knowledge Base for BOSS Extract Automation

## Key Concepts
- **BOSS Extracts**: Automated data exports from Oracle Fusion using Business Views (e.g., costDistributionExtract).
- **TEMS**: Refers to the extract scheduling and execution in the script.
- **Workflow Components**: Preflight → Metadata validation → Export definition/group creation → Scheduling → Polling (ESS/SaaS-Batch) → Download.
- **Error Handling**: Auto-retries for duplicates, lazy dependency loading, structured JSON summaries, configurable polling timeouts, debug mode.

## Environment Variables
- Hosts: BOSS_HOST, IDCS_HOST.
- Auth: IDCS_CLIENT_ID/SECRET, BOSS_USERNAME/PASSWORD, ESS_USERNAME/PASSWORD.
- Defaults: DEFAULT_OWNER, DEFAULT_EMAILS, OUTPUT_DIR, DEFAULT_PVO.
- DB: DB_USER/PASSWORD, DB_CONNECT_STRING, DB_WALLET_LOCATION/DB_WALLET_PASSWORD.
- Optional metadata: CATALOG_CSV_PATH.
- Polling: POLL_INTERVAL_SEC, POLL_TIMEOUT_SEC.

## Configuration Files
- `assets/.env` stores secrets and environment-specific values.
- `assets/mapping.json` stores PVO to business-view mappings and supplies the default `business_view_name`.
- `assets/extract_config.json` stores non-secret runtime options such as dry run, debug, `metadata_source`, `metadata_fixture`, `catalog_csv_path`, filter condition, scheduling values, and known monitor/download IDs.

## APIs and Endpoints
- Token: /oauth2/v1/token (IDCS).
- Export Definition: /api/boss/data/objects/ora/commonBoss/dataExport/v1/exportDefinitions.
- Export Group: /api/boss/data/objects/ora/commonBoss/dataExport/v1/exportGroupDefinitions.
- Schedule: /api/boss/data/objects/ora/scmCore/dataExtract/v1/$en/extractSchedules.
- ESS Status: /ess/rest/scheduler/v1/requests/{id}.
- Batch Jobs: /api/saas-batch/jobscheduler/v1/jobRequests/.
- Output Files: /api/saas-batch/jobfilemanager/v1/jobRequests/{id}/outputFiles.

## Scripts Overview
- **GenerateTEMS_Extracts.py**: Main automation script with staged commands (`preflight`, `validate-view`, `create-extract`, `monitor`, `download`, `run`) and multiple metadata sources (`auto`, `fixture`, `mapping`, `db`).
- **ExtractCatalog.py**: Fetches catalog view metadata to CSV so business view names can be mapped to module names.
- **assets/mapping.json**: Static mapping used to derive the business view from the selected/default PVO.
- **assets/extract_config.json**: Configuration file used instead of exposing many CLI flags.
- **assets/metadata_fixture.json**: Offline sample metadata fixture for restricted environments.

## Metadata Source Behavior
- `fixture`: reads `module` and `attributes` from `assets/metadata_fixture.json` (or configured fixture path).
- `mapping`: reads attributes from `assets/mapping.json` and resolves `module_name` from `catalog_csv_path`.
- `auto`: tries fixture first if provided, then mapping + catalog CSV, then DB fallback.
- `db`: queries Oracle DB directly using `V_BUSINESS_OBJECTS`.

## Common Issues
- Missing env vars → Use `preflight` and inspect `missing_env`.
- Missing `oracledb` → Install from `requirements.txt`; the script now fails with an explicit command.
- Missing module name in mapping mode → Regenerate or correct `catalog_output.csv` and verify `catalog_csv_path`.
- Duplicate names → Auto-appends timestamp.
- Timeouts → Adjust `POLL_TIMEOUT_SEC`.
- API Failures → Check scopes, hosts, reachability, and enable `debug` in `extract_config.json`.

This is distilled from repo docs/scripts; expand as needed.