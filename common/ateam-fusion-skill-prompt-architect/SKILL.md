---
name: ateam-fusion-skill-prompt-architect
description: Build production-grade prompt specifications for Oracle Fusion Cloud implementation and data/analytics agent skills using CRAFT plus advanced prompting methods, with strict anti-hallucination guardrails and measurable usefulness/performance outcomes.
license: Apache-2.0
compatibility: Requires access to project requirements, Fusion reference artifacts (implementation architecture, REST/BICC/OTBI/object catalogs), and ability to run Python 3.10+ scripts for prompt generation/evaluation.
metadata:
  domain: prompt-engineering
  audience: dma-a-team
  patterns: craft,expert-prompting,role-play,quality-gates,evaluation,cross-pillar-implementation
---

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Fusion Skill Prompt Architect

Use this skill to generate reliable, reusable prompt specifications that help the Data Management and Analytics A-Team create high-quality Oracle Fusion skills across **implementation architecture and data/analytics** workstreams.

## Implementation architecture span

This skill must support prompts that cover, at minimum:

- Cross-pillar architecture (HCM, ERP, SCM, CX).
- Application integration (Fusion-to-Fusion, Fusion-to-PaaS, Fusion-to-third-party).
- Governance and operating model.
- Data definition, ownership, lifecycle, and contracts.
- Security (IAM, SoD, masking, encryption, auditability).
- Extensibility (PaaS extensions, event/model driven integration, customization boundaries).
- Monitoring and observability (functional, technical, and business telemetry).

Reference framing:
- A-Team architecture coverage: `https://www.ateam-oracle.com/oracle-fusion-cloud-implementation-architecture-a-7-pillar-framework-for-scalable-and-ai-ready-deployments`

## Use when

- You need to author a new `agentskills.io` skill prompt for Fusion implementation architecture, operations, or data/analytics work.
- You want repeatable prompt quality across multiple architects and agents.
- You need stronger controls against hallucinated Fusion objects/endpoints/query syntax.
- You need consistent architecture outputs that remain coherent across HCM/ERP/SCM/CX boundaries.
- You need measurable prompt quality (usefulness + performance) before broad rollout.

## Inputs expected

- Business objective and target users.
- Functional scope and domain boundaries (HCM/ERP/SCM/CX, object list, process boundaries, KPI list).
- Fusion architecture references (pillar standards, integration patterns, governance principles, extensibility policies).
- Fusion technical references (REST endpoints, BICC PVO names, OTBI subject areas, version constraints) where data topics apply.
- Non-functional constraints (freshness SLO, latency, cost, compliance/security masking).
- Required output format (`SKILL.md`, scripts, references, templates, or prompt-only artifact).
- Acceptance criteria and review owners.

## Output contract

Produce all of the following:

1. **Prompt Specification** using `assets/prompt-template.md`.
2. **Evidence Ledger** mapping each Fusion claim to source-of-truth artifacts.
3. **Guardrail Matrix** covering hallucination prevention, ambiguity handling, version safety, and cross-pillar consistency.
4. **Evaluation Scorecard** using `scripts/evaluate_prompt_skill.py` + params JSON.
5. **Refinement Notes** listing unresolved `UNVERIFIED` items and closure actions.

## Method (CRAFT+ stack)

1. **C — Context grounding**
   - Capture organizational context, domain boundaries, and known constraints.
   - Explicitly record which Fusion references are authoritative.
   - Encode cross-pillar dependencies (process handoffs across HCM/ERP/SCM/CX).

2. **R — Role calibration**
   - Define the agent as senior Oracle data architect + senior software engineer.
   - State expected technical rigor (e.g., object fidelity, pagination semantics, date format discipline).

3. **A — Action definition**
   - Define the exact deliverable (new skill, enhancement, implementation blueprint, extraction blueprint, evaluation artifact).
   - Specify sequencing requirements and mandatory checks.

4. **F — Format contract**
   - Require deterministic output shape (sections, tables, code blocks, scoring block).
   - Include mandatory confidence scoring with refine-if-<0.9 gate.

5. **T — Target and tone alignment**
   - Target DMA A-Team practitioners.
   - Keep language operational and implementation-ready (no generic advisory-only responses).
   - Ensure guidance is directly consumable by architects, integration engineers, and operations owners.

6. **Enhance with advanced prompting methods**
   - **EmotionPrompt / stakes framing:** include business criticality to increase focus.
   - **OPRO cue:** include “Take a deep breath and work step-by-step”.
   - **ExpertPrompting:** force explicit expert persona and specialization boundaries.
   - **Role-Play Prompting:** define actor responsibilities (architect, reviewer, operator).
   - **Principled instructions (26 principles):** use clear constraints, delimiters, and verification instructions.

7. **Apply anti-hallucination guardrails**
   - Every Fusion technical claim must include one source reference.
   - Unknown items must be labeled `UNVERIFIED` (never invented).
   - Separate “Known facts” vs “Assumptions” vs “Open questions”.
   - Check that each proposed decision has explicit cross-pillar impact analysis.

8. **Evaluate and iterate**
   - Run the mandatory evaluation+report wrapper with real run data.
   - If any critical metric misses threshold, revise prompt and re-score.

## Guardrails (mandatory)

1. **No fabricated Fusion metadata or architecture constraints**
   - Do not invent REST resources, BICC PVOs, OTBI subject areas, query params, version behavior, or governance/security policies.

2. **Evidence-tagged assertions**
   - Each key claim must cite one of:
     - repository artifact path,
     - official Oracle/A-Team URL,
     - validated run output.

3. **Version + environment awareness**
   - State Fusion release/API context if known.
   - If unknown, mark `UNVERIFIED` and request clarification.

4. **Progressive disclosure**
   - Include only domain-relevant logic in primary output; move non-essential material to optional notes.

5. **Cross-pillar consistency**
   - Do not optimize one pillar in a way that violates another pillar's control objectives.
   - Surface integration and data ownership impact for each major decision.

6. **Ambiguity protocol**
   - If required inputs are missing, ask targeted follow-up questions before finalizing.

## Edge cases to handle

- Conflicting source definitions for object/endpoint naming.
- Missing query semantics (`q`, date filters, pagination tokens).
- Requirements that cannot satisfy both latency and cost targets simultaneously.
- Mixed-scope requests (ERP + HCM + SCM) with uneven source readiness.
- Cross-pillar operating model conflicts (e.g., governance model differs by pillar).
- Extensibility demand that conflicts with Fusion SaaS upgrade-safe boundaries.
- Monitoring requirements with no agreed ownership/escalation model.
- Security constraints requiring data minimization/masking not present in initial prompt.

## Evaluation protocol (usefulness + performance)

Use the mandatory wrapper `scripts/evaluate_prompt_skill_with_report.py`.

Minimum required artifacts per run:

1. JSON scorecard
2. Browser HTML scorecard report

Example command:

```bash
python3 agent-skills-fusion/fusion-skill-prompt-architect/scripts/evaluate_prompt_skill_with_report.py \
  --params <eval_params.json> \
  --manifest <prompt_manifest.json> \
  --scorecard-output <scorecard.json> \
  --html-output <scorecard_report.html>
```

The raw evaluator `scripts/evaluate_prompt_skill.py` is still available, but should be treated as a library-level primitive. Operational runs must use the wrapper so that HTML reporting is always produced.

Track these metrics:

- **Usefulness**
  - `task_success_rate`
  - `first_pass_acceptance_rate`
  - `coverage_rate`
  - `fusion_fidelity_rate`
  - `implementation_coverage_rate`
- **Performance**
  - `p95_latency_ms`
  - `avg_iteration_count`
  - `accepted_per_1k_tokens`
  - `consistency_rate`
- **Reliability/Safety**
  - `hallucination_rate`

Default gate guidance:

- `task_success_rate >= 0.90`
- `fusion_fidelity_rate >= 0.95`
- `implementation_coverage_rate >= 0.95`
- `hallucination_rate <= 0.02`
- `p95_latency_ms <= 3000`
- `avg_iteration_count <= 2.0`

## Quality bar

- Output includes all mandatory sections in the template.
- No untagged technical claims.
- All unresolved items clearly marked `UNVERIFIED` with next action.
- Evaluation scorecard attached and threshold compliance stated.
- Confidence scores (0-1) included for: scalability, effectiveness, reliability, completeness.
- If any confidence score < 0.9, refine output before final delivery.
- Benchmark can be executed on 24 synthetic prompts generated by `scripts/generate_synthetic_prompts.py`.
- Each benchmark/evaluation execution must emit an HTML report for browser navigation/filtering.

## References

- Prompt template: `assets/prompt-template.md`
- Review checklist: `assets/prompt-review-checklist.md`
- Method mapping: `references/method-mapping.md`
- Evaluation definitions: `references/evaluation-metrics.md`
- Pillar framework guide: `references/implementation-pillar-framework.md`
- Synthetic benchmark scripts:
  - `scripts/generate_synthetic_prompts.py`
  - `scripts/build_synthetic_eval_params.py`
  - `scripts/evaluate_prompt_skill_with_report.py`
  - `scripts/render_scorecard_report.py`

## Companion Enrichment (Inputs/Outputs/Workflow/Prompts)

This section standardizes quick-operational usage using the fusion-skill-prompt-architect pattern of explicit input/output contracts, deterministic workflow, and reusable prompt examples.

Inputs:
- Skill objective, target users, and implementation scope
- Authoritative Fusion references and architecture constraints
- Expected output artifacts (prompt spec, evidence ledger, scorecard)
- Acceptance thresholds for usefulness, fidelity, latency, and safety

Outputs:
- Production-grade prompt specification with deterministic structure
- Guardrail matrix and evidence ledger for all key claims
- Evaluation scorecard with HTML/JSON reporting artifacts
- Refinement notes for unresolved UNVERIFIED items and next actions

Workflow:
1. Ground prompt context and constraints using CRAFT context discipline
2. Define role/action/format/target with explicit guardrails
3. Apply anti-hallucination checks and evidence tagging
4. Evaluate against usefulness/performance/safety thresholds
5. Iterate until acceptance gates are met and confidence is high

Prompts:
- Create a prompt specification for a new Fusion extraction skill using CRAFT+ methods.
- Review this draft prompt and identify anti-hallucination gaps with fixes.
- Generate evaluation parameters and scoring guidance for this prompt skill.
- Refine the prompt until it meets task success and fidelity thresholds.

