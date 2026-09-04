# Checklists for BOSS Extract Automation

## Pre-Run Checklist
- [ ] All required env vars set (BOSS_HOST, IDCS_CLIENT_ID, etc.).
- [ ] `mapping.json` points to the intended default PVO/business view.
- [ ] `extract_config.json` contains the intended runtime defaults.
- [ ] Database connection tested (wallet, user, password).
- [ ] View name validated against catalog (run ExtractCatalog.py if needed).
- [ ] Output directory exists and is writable.
- [ ] No conflicting extract/group names (or allow auto-retry).

## Execution Checklist
- [ ] Build extraction query from DB metadata.
- [ ] Create export definition.
- [ ] Create export group.
- [ ] Schedule extract (verify frequency/parameters).
- [ ] Poll ESS status until terminal state.
- [ ] Locate SaaS-Batch job.
- [ ] Poll batch status to SUCCEEDED.
- [ ] Download all output files.

## Validation Checklist
- [ ] Confirm export IDs in API responses.
- [ ] Verify ESS state is SUCCEEDED.
- [ ] Check batch job status is SUCCEEDED.
- [ ] Outputs saved to OUTPUT_DIR without errors.
- [ ] Files contain expected data (e.g., spot-check CSV/ZIP).

## Troubleshooting Checklist
- [ ] Review error message/stack trace (set `debug` in `extract_config.json`).
- [ ] Check for missing env vars.
- [ ] Verify API hosts/scopes.
- [ ] Test token generation separately.
- [ ] Retry with unique names if duplicate error.
- [ ] Increase poll timeout if timing out.

Use these to ensure reliable runs.