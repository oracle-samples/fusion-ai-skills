# Error Handling, Scheduling, Retry, and Replay References

Use this file for any design with retries, recoverable faults, scheduled processing, replay, business validation errors, compensation, or operational recovery.

## Use first

### Error Handling Guide - Oracle Integration Cloud
- URL: https://www.ateam-oracle.com/error-handling-guide-oracle-integration-cloud
- Type: a-team blog
- Category: error handling
- Relevance: high
- Authority: design guidance
- Freshness: stable
- Use when: designing global fault handlers, scope-level fault handling, business versus technical error separation, and replay context.
- Do not use for: generic monitoring design unless paired with observability guidance.

### Advanced Error Handling and Scheduling Best Practices - Oracle Integration Cloud
- URL: https://www.ateam-oracle.com/advanced-error-handling-and-scheduling-best-practices-oracle-integration-cloud
- Type: a-team blog
- Category: error handling and scheduling
- Relevance: high
- Authority: design guidance
- Freshness: stable
- Use when: designing scheduled retries, backoff, retry thresholds, replay, notifications, escalation, and operational recovery.
- Do not use for: purely synchronous APIs with no scheduling or retry design.

## Design cues

- Separate business faults from technical faults.
- Include global fault handlers, scope-level fault handling, retry thresholds, backoff, scheduled retry, manual replay, and notification/escalation.
- Store enough error context to replay safely without creating duplicates.
- Define idempotency keys and duplicate handling for all retry/replay paths.
