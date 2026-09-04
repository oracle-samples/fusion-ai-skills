# Oracle Data Transforms Resilience Controls

## Objective
Operationalize resilient, restart-safe, contract-enforced transformation runs while keeping unknown product specifics explicitly marked as `UNVERIFIED`.

## Controls

1. **Staging discipline**
   - Land extraction output in immutable/raw stage before any transform.
   - Persist run metadata (run_id, extraction window, source artifact identifier, count checks).

2. **Transform discipline**
   - Separate canonicalization from business-rule enrichment.
   - Bind every transform unit to input/output contract versions.

3. **Idempotency discipline**
   - Use stable run keys and deterministic merge/upsert semantics.
   - Replays for the same run key must converge to same output state.

4. **Retry + recovery discipline**
   - Classify errors into retriable/terminal classes.
   - Persist checkpoints: `extract_complete`, `stage_validated`, `transform_complete`, `publish_complete`.
   - Resume from last successful checkpoint when safe.

5. **Operational discipline**
   - Standard run-state taxonomy: `queued`, `running`, `failed_retriable`, `failed_terminal`, `completed`.
   - Emit metrics: `run_duration_ms`, `records_in`, `records_out`, `rejected_records`, `retry_count`.

6. **Security discipline**
   - Enforce least privilege for extract/stage/transform/publish roles.
   - Apply masking policy before broad publish where required by contract.

## Evidence
- [source: https://docs.oracle.com/en/solutions/best-practices-resilient-data-integration/index.html]
- [source: https://datacontract.com/]
- [source: https://agentskills.io/skill-creation/evaluating-skills]
