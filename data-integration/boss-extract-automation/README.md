## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# boss-extract-automation

## Description
create, schedule, monitor, troubleshoot, and download boss and tems extracts from oracle fusion using the bundled automation. use when chatgpt needs to help run extract jobs, validate business views, monitor ess or saas-batch status, download output files, or troubleshoot this specific extract automation workflow.

## Quick Start
Use this starter prompt:
- "Create and schedule a BOSS extract run for tonight, then show the monitoring checklist."

## Inputs:
- Fusion environment connection details and authentication method
- Extract job configuration (BOSS/TEMS view names, schedule, and parameters)
- Execution mode: run-now, schedule, monitor, retry, or download outputs
- Operational constraints (time window, retention, and destination folder)

## Outputs:
- Validated run plan and execution command sequence
- Job status timeline with ESS/SaaS-batch checkpoints
- Download artifacts manifest and local output paths
- Troubleshooting guidance for failed or stalled extract jobs

## Workflow:
1. Validate required credentials, extract definitions, and runtime prerequisites
2. Create or schedule extraction run based on requested operating mode
3. Monitor ESS/SaaS-batch state transitions until completion or timeout
4. Download produced files and verify integrity/expected record availability
5. Summarize outcomes, failures, and concrete remediation next steps

## Prompts:
- "Create and schedule a BOSS extract run for tonight, then show the monitoring checklist."
- "Monitor this extract job and tell me exactly when to retry versus wait."
- "Download output files for the last successful run and provide a manifest."
- "Troubleshoot this failed extract execution and propose the safest recovery sequence."

## References
- `SKILL.md`
