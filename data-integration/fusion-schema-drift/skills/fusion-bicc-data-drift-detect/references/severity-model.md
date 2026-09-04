# Severity Model for Data Drift

The data drift skill classifies each finding into one of five severities:

- `critical`: Immediate business or pipeline impact likely.
- `high`: Major degradation risk requiring rapid mitigation.
- `medium`: Notable change requiring planned remediation.
- `low`: Minor shift; monitor and review.
- `info`: Informational only.

## Critical examples

- Row count drops beyond critical threshold.
- Required column null ratio increases beyond critical threshold.
- Numeric mean shifts beyond critical policy tolerance on KPI-driving fields.

## Decision usage

Use severity levels to drive runbooks:

- `critical/high`: block or gate release, require remediation approval.
- `medium`: warn + ticket for backlog remediation.
- `low/info`: monitor, optionally auto-accept.
