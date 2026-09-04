# Prompt Review Checklist — Fusion Skill Prompt Architect

Use this checklist during peer review before promoting a prompt to team-wide reuse.

## A. Structural compliance

- [ ] Prompt follows CRAFT sections: Context, Role, Action, Format, Target.
- [ ] Prompt includes advanced method add-ons (EmotionPrompt, OPRO, ExpertPrompting, Role-Play, principled instructions).
- [ ] Prompt explicitly requests confidence scoring and refine-if-<0.9 behavior.
- [ ] Prompt includes a 7-pillar implementation coverage map (cross-pillar, integration, governance, data, security, extensibility, observability).

## B. Fusion technical grounding

- [ ] Every Fusion object/endpoint/PVO/subject-area claim is evidence-tagged.
- [ ] No fabricated metadata; unknowns marked `UNVERIFIED`.
- [ ] API/version assumptions are explicit.
- [ ] Query/date/pagination conventions are validated against provided references.
- [ ] Cross-pillar decisions (HCM/ERP/SCM/CX) include impact notes for integration, governance, and security.

## C. Hallucination controls

- [ ] Facts vs assumptions vs open questions are separated.
- [ ] Missing required input triggers follow-up questions.
- [ ] Prompt contains explicit no-fabrication rule.

## D. Output usability

- [ ] Output format is deterministic and implementation-ready.
- [ ] Required sections align to target audience (DMA A-Team architects/operators).
- [ ] Edge cases and trade-offs are explicitly addressed.
- [ ] Monitoring and observability guidance includes ownership and escalation path.

## E. Measurability

- [ ] Prompt evaluation metrics are defined and calculable.
- [ ] Gate thresholds are specified.
- [ ] Scorecard is generated via `scripts/evaluate_prompt_skill_with_report.py`.
- [ ] `implementation_coverage_rate` is captured and thresholded.
- [ ] Browser HTML report is produced for every evaluation run.

## Reviewer summary

- Reviewer:
- Date:
- Decision (approve / revise):
- Major findings:
- Required fixes:
