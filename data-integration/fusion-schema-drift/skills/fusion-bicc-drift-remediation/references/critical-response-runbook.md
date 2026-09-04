# Critical Drift Response Runbook

When any finding is classified as `critical`, execute the following in order:

1. **Gate release**
   - Pause promotion of affected Data Transforms / AI DP ingestion jobs.
2. **Assign owner**
   - Use remediation plan ownership mapping.
3. **Apply immediate mitigation**
   - Add transform-level fallback or cast/null default where possible.
4. **Root cause review**
   - Confirm whether drift originated in source release, extraction config, or target contract mismatch.
5. **Re-validate**
   - Regenerate snapshots and re-run drift reports.
6. **Close only when critical count is zero**
   - Keep release gated until critical findings are resolved or explicitly waived.
