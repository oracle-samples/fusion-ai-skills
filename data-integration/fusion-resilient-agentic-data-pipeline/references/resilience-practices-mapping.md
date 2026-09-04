# Resilience Practices Mapping

| Practice Area | Control | Pipeline Effect |
|---|---|---|
| Fault tolerance | Retries with capped backoff + terminal classification | Reduces transient failure impact |
| Restartability | Persisted checkpoints and replay policy | Enables partial-load recovery |
| Data integrity | Idempotent reruns with deterministic keys | Prevents duplicate/divergent writes |
| Contract governance | Validate contract at stage->transform and transform->publish | Blocks unsafe schema/semantic drift |
| Observability | Runtime metrics + failure evidence bundle | Improves MTTR and operational control |
| Evaluation | Use thresholded scorecard gates | Enforces objective quality criteria |

Evidence:
- [source: https://docs.oracle.com/en/solutions/best-practices-resilient-data-integration/index.html]
- [source: https://datacontract.com/]
- [source: agent-skills-fusion/fusion-skill-prompt-architect/scripts/evaluate_prompt_skill.py]
