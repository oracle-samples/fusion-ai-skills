# DMA A-Team Fusion Skill Prompt Template (CRAFT+)

Use this template to generate prompts that produce **useful, performant, and low-hallucination** Oracle Fusion skill artifacts for both:

- Fusion Cloud implementation architecture
- Data management and analytics architecture

## 1) Context (C)

- Organization and mission context:
- Business outcome and success criteria:
- In-scope domains (HCM/ERP/SCM/CX):
- Authoritative references provided (URLs, repo paths, docs):
- Out-of-scope boundaries:
- Cross-pillar dependencies and handoffs:

## 2) Role (R)

- Agent persona (must be expert-level):
- Required specializations (Fusion implementation architecture, integration, governance, security, extensibility, observability, extraction, ADB, OAC):
- Technical rigor expectations:

## 3) Action (A)

- Exact task to execute (implementation architecture and/or data/analytics skill design):
- Required sequence of steps:
- Mandatory checks before completion:
- Clarifying-question trigger conditions (when to pause):

## 4) Format (F)

Required output sections:

1. Requirements summary
2. Proposed skill artifact(s)
3. 7-pillar implementation coverage map
4. Guardrails and edge cases
5. Evaluation plan (usefulness + performance)
6. Confidence scoring with refine-if-<0.9

Output constraints:

- Use deterministic section names.
- Mark unknown claims as `UNVERIFIED`.
- Distinguish facts vs assumptions.
- Include explicit cross-pillar impact statements for major design decisions.

## 5) Target (T)

- Target team/persona:
- Stakeholder consumption format (architect review, operator runbook, implementation handoff):
- Tone (operational, technically grounded, actionable):

## 6) Advanced prompting add-ons (required)

- **EmotionPrompt/stakes framing:** why this matters now.
- **OPRO cue:** “Take a deep breath and work through this step by step.”
- **ExpertPrompting:** force specialist behavior and explicit trade-offs.
- **Role-play roles:** architect, reviewer, and operator responsibilities.
- **Principled instructions:** concise constraints, clear delimiters, explicit acceptance criteria.

## 7) Anti-hallucination guardrails

- Do not invent Fusion REST endpoints, BICC PVO names, OTBI subject areas, API behavior, implementation standards, or security controls.
- Add an evidence ledger for every key technical claim.
- If a required reference is missing, ask follow-up question(s) before finalizing.
- Validate cross-pillar coherence (HCM/ERP/SCM/CX and shared governance/security requirements).

## 8) Evaluation block

Include or attach values for:

- `task_success_rate`
- `first_pass_acceptance_rate`
- `coverage_rate`
- `fusion_fidelity_rate`
- `implementation_coverage_rate`
- `hallucination_rate`
- `p95_latency_ms`
- `avg_iteration_count`
- `accepted_per_1k_tokens`
- `consistency_rate`

Mandatory execution policy:

- Always run evaluation via:
  `scripts/evaluate_prompt_skill_with_report.py`
- Required artifacts per evaluation run:
  1. JSON scorecard
  2. Browser HTML report

## 9) 7-pillar architecture checklist (minimum)

Prompt must explicitly account for these pillars:

1. Cross-pillar business architecture (HCM/ERP/SCM/CX)
2. Application integration architecture
3. Governance and operating model
4. Data definition and lifecycle architecture
5. Security and compliance architecture
6. Extensibility architecture
7. Monitoring and observability architecture

## 10) Mandatory runtime command template

```bash
python3 agent-skills-fusion/fusion-skill-prompt-architect/scripts/evaluate_prompt_skill_with_report.py \
  --params <eval_params.json> \
  --manifest <prompt_manifest.json> \
  --scorecard-output <scorecard.json> \
  --html-output <scorecard_report.html>
```
