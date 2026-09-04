---
name: fusion-resilient-agentic-data-pipeline-odt-contracts
description: Design resilient, contract-driven Oracle Fusion data pipelines with Oracle Data Transforms as a first-class transformation target, using deterministic anti-hallucination controls and measurable quality gates.
license: Apache-2.0
compatibility: Requires access to Oracle Fusion extraction metadata references, OCI/ADB target context, Oracle Data Transforms runtime conventions, and Python 3.10+ for evaluation tooling.
metadata:
  domain: data-integration-resilience
  audience: dma-a-team
  patterns: resilient-integration,data-contracts,odt-operations,anti-hallucination,evaluation-gates
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Fusion Resilient Agentic Data Pipeline (ODT + Contracts) Skill

Use this skill to produce resilient, testable, and governable Oracle Fusion data pipelines where Oracle Data Transforms (ODT) is a first-class transformation runtime and data contracts are enforced end-to-end.

## Use when

- You need a standard architecture for Fusion REST/BICC/OTBI extraction into governed analytics/data products.
- You need restart-safe behavior across retries, partial failures, schema drift, and release changes.
- You need explicit contract checks before transform and before publish.

## Inputs expected

- Confirmed source metadata artifacts for Fusion REST/BICC/OTBI (`UNVERIFIED` when absent).
- Data contract scope: entities, fields, quality rules, compatibility policy, owners.
- ODT environment profile and operational constraints (orchestration boundary, retry policy, checkpoint persistence).
- Security constraints (masking rules, least-privilege model, data residency constraints).
- Runtime targets for freshness, latency, cost, and reliability.

## Output contract

1. Pipeline architecture with extraction/staging/transform/publish control points.
2. Data contract package (spec template + versioning policy + validation gates).
3. ODT implementation controls for idempotency, retries, checkpoints, and recovery.
4. Anti-hallucination guardrail matrix and evidence ledger.
5. Evaluation suite and scorecards for usefulness/performance gating.

## Method (CRAFT + advanced prompting)

Take a deep breath and work through this step by step.

1. **Context**
   - Capture enterprise objective, risk, and constraints in deterministic sections. [source: https://agentskills.io/home]
   - Align design to resilient integration principles (fault tolerance, restartability, observability, controlled operations). [source: https://docs.oracle.com/en/solutions/best-practices-resilient-data-integration/index.html]
2. **Role**
   - Operate as: Senior Oracle data architect + Senior Python engineer + ODT operator/reviewer.
3. **Action**
   - Produce implementation-ready pipeline design, contract controls, and execution/evaluation assets.
4. **Format**
   - Deterministic section names, evidence tags, and explicit `UNVERIFIED` markers.
5. **Target**
   - Data Management and Analytics A-Team architects and engineers.
6. **Advanced method requirements**
   - EmotionPrompt stakes framing: inaccurate guidance can propagate enterprise-wide defects.
   - ExpertPrompting: explicit trade-off decisions (latency vs cost, strictness vs agility).
   - Role-play prompting with responsibilities:
     - Architect: design decisions + constraints.
     - Reviewer: policy and evidence compliance.
     - Operator: runability, restartability, on-call controls.
   - Principled instruction style: no fabrication, focused clarifying questions, deterministic output contract. [source: agent-skills-fusion/fusion-skill-prompt-architect/references/method-mapping.md]

## ODT-first implementation guidance

1. **Staging controls**
   - Land immutable extraction snapshots/incrementals before transformation.
   - Persist run lineage: source artifact identifier, extraction mode, extraction window, counts.
2. **Transformation controls**
   - Separate canonicalization from business-rule enrichment.
   - Bind each transformation unit to explicit input/output contract version.
3. **Idempotency and retry controls**
   - Reruns with identical run keys must converge to same target state.
   - Retries only for retriable classes; terminal failures require operator intervention.
4. **Recovery controls**
   - Persist checkpoints: `extract_complete`, `stage_validated`, `transform_complete`, `publish_complete`.
   - Resume from last successful checkpoint when safe.
5. **Operational controls**
   - Standard run states: `queued`, `running`, `failed_retriable`, `failed_terminal`, `completed`.
   - Emit metrics for SLO observability and incident triage.

## Data contract-driven design guidance

- Define contract dimensions: structure, semantics, quality rules, freshness, compatibility, ownership. [source: https://datacontract.com/]
- Enforce compatibility policy (`major`, `minor`, `patch`) and mandatory migration notes on breaking changes.
- Validate contracts at stage-to-transform and transform-to-publish boundaries.
- Block publish when mandatory contract checks fail.

## Fusion anti-hallucination protocol (mandatory)

1. Never invent Fusion REST endpoints, BICC PVOs, OTBI subject areas, or undocumented query/date/pagination behavior.
2. Every critical technical claim must include `[source: <url-or-repo-path>]`.
3. Unknown values must be labeled `UNVERIFIED`.
4. If required input is missing, ask focused clarifying questions before finalizing.

## Validation checklist

- Deterministic required sections are present. [source: agent-skills-fusion/fusion-skill-prompt-architect/assets/prompt-template.md]
- Facts vs assumptions vs open questions are separated. [source: agent-skills-fusion/fusion-skill-prompt-architect/assets/prompt-review-checklist.md]
- Critical claims are evidence-tagged.
- Unresolved metadata is labeled `UNVERIFIED`.
- Evaluation gates satisfied:
  - `task_success_rate >= 0.90`
  - `fusion_fidelity_rate >= 0.95`
  - `hallucination_rate <= 0.02`
  - `p95_latency_ms <= 3000`
  - `avg_iteration_count <= 2.0`
  [source: agent-skills-fusion/fusion-skill-prompt-architect/references/evaluation-metrics.md]

## References

- Oracle resilient data integration best practices: https://docs.oracle.com/en/solutions/best-practices-resilient-data-integration/index.html
- Data Contracts reference: https://datacontract.com/
- agentskills overview: https://agentskills.io/home
- agentskills evaluation guidance: https://agentskills.io/skill-creation/evaluating-skills
- Local skill prompt architecture assets: `agent-skills-fusion/fusion-skill-prompt-architect/`

## Companion Enrichment (Inputs/Outputs/Workflow/Prompts)

This section standardizes quick-operational usage using the fusion-skill-prompt-architect pattern of explicit input/output contracts, deterministic workflow, and reusable prompt examples.

Inputs:
- Source-to-target contract definitions and quality expectations
- ODT transformation requirements and execution constraints
- Resilience requirements (retry, idempotency, failure isolation)
- Governance controls for anti-hallucination and evidence tagging

Outputs:
- Contract-driven pipeline blueprint with ODT-first transformation plan
- Resilience control model for retries, fallback, and recoverability
- Validation gates covering contract fidelity and runtime quality
- Evidence ledger with known facts, assumptions, and unresolved items

Workflow:
1. Ground design in explicit contracts and authoritative references
2. Translate contracts into ODT transformation and orchestration components
3. Embed resilience controls for replay safety and failure recovery
4. Run deterministic validation gates for quality and compliance
5. Publish operational handoff with unresolved risks clearly tagged

Prompts:
- Design a resilient ODT-first pipeline for Fusion AP data with strict contracts.
- Generate anti-hallucination guardrails for this agentic transformation workflow.
- Validate whether this pipeline design is replay-safe and contract-compliant.
- Create a runbook for failure isolation and recovery in ODT-based processing.

