# Common Workflows for BOSS Extract Automation

## End-to-End Extract Creation and Run
1. Run `preflight`.
2. Validate the view using DB metadata or an offline fixture.
3. Build extraction query JSON.
4. Create export definition via BOSS API.
5. Create export group.
6. Schedule the group (immediate or recurring).
7. Monitor ESS and SaaS-Batch.
8. Download outputs.

## Stage-by-Stage Workflow
- `preflight` → validate dependencies, env, wallet path, output dir, optional network reachability.
- `validate-view` → confirm metadata and preview extraction query.
- `create-extract` → create export definition only.
- `monitor` → monitor ESS and/or batch jobs using known IDs.
- `download` → download output files for a known job request.

## Scheduling an Extract
- Immediate: set `frequency` to `Immediate` in `extract_config.json`.
- Hourly: set `frequency` to `Hourly` and `frequency_hourly_interval` to the desired interval.
- Weekly: set `frequency` to `Weekly`, `frequency_days_in_week` to the target days, and `start_time` / `end_time` as needed.
- Monitor with polling or manual status checks.

## Troubleshooting Failures
1. Run `preflight` again and inspect `missing_env`, `missing_dependencies`, and `unsupported_environment`.
2. Set `dry_run` to `true` in `extract_config.json` to confirm names and intended API calls without making changes.
3. Verify API responses for HTTP errors (e.g., 409 duplicate).
4. Poll ESS/SaaS-Batch for detailed status.
5. Set `debug` to `true` in `extract_config.json` for stack traces.

## Extending for New Views
1. Add view to DB query in `ExtractCatalog.py`.
2. Update alias generation if needed.
3. Update `mapping.json` to point the default PVO to the new view.
4. Test with a sample run using the existing `run` command.

See `CHECKLISTS.md` for validation steps.