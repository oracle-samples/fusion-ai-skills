# Method Mapping: CRAFT + Advanced Prompting for Fusion Skill Design

This reference maps each prompting method to practical actions for Oracle Fusion skill-prompt construction.

Scope note: This skill now covers both data/analytics and full Fusion Cloud implementation architecture.

## 1) CRAFT baseline

| Method element | What to include | Fusion-specific expectation |
|---|---|---|
| Context | Org goals, business stakes, constraints, references | Explicit HCM/ERP/SCM/CX scope, source artifacts, and cross-pillar handoffs |
| Role | Expert persona and boundaries | Senior Oracle data architect + Python engineer framing |
| Action | Concrete task + sequence | Skill artifact goals (`SKILL.md`, scripts, references, checks) including implementation architecture decisions |
| Format | Deterministic output schema | Sectioned output with evidence ledger + confidence block + 7-pillar coverage map |
| Target | Audience and delivery style | DMA A-Team operational handoff quality |

## 2) EmotionPrompt (stakes framing)

- Add urgency and consequence statements to prioritize correctness.
- Example: “This output is used to standardize extraction logic across enterprise teams; inaccuracies propagate operational risk.”

## 3) OPRO cue (stepwise optimization)

- Include: **“Take a deep breath and work through this step by step.”**
- Require explicit sequential reasoning outputs (requirements, guardrails, design, edge cases, evaluation).

## 4) ExpertPrompting

- Constrain role to known specialties.
- Require trade-off justification in areas like latency vs cost, REST vs BICC, extensibility vs upgrade safety, and control strictness vs delivery speed.

## 5) Role-Play Prompting

Define working roles in the prompt:

- **Architect:** designs the solution and constraints.
- **Reviewer:** checks compliance, grounding, and risk.
- **Operator:** validates runnability and operational fit.

## 6) Principled Instructions (clarity and control)

- Use explicit acceptance criteria.
- Use delimiters and output contracts.
- Ask for missing required data instead of guessing.

## 7) Recommended layering order

1. Start with CRAFT skeleton.
2. Add expert persona and role-play responsibilities.
3. Add OPRO cue and methodological sequence.
4. Add stakes framing.
5. Add anti-hallucination and evidence requirements.
6. Add measurable evaluation and quality gates.

## 8) 7-pillar implementation mapping

When prompts target implementation architecture, require explicit coverage for:

1. Cross-pillar business architecture (HCM/ERP/SCM/CX)
2. Application integration architecture
3. Governance and operating model
4. Data definition and lifecycle architecture
5. Security and compliance architecture
6. Extensibility architecture
7. Monitoring and observability architecture
