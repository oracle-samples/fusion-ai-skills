#!/usr/bin/env python3
"""
Generate a 24-prompt synthetic benchmark suite for fusion-skill-prompt-architect.

Example:
  python3 generate_synthetic_prompts.py \
    --output-dir ../assets/synthetic-benchmark/prompts \
    --output-manifest ../assets/synthetic-benchmark/synthetic_prompt_manifest.json
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any


PILLARS = [
    "Cross-pillar business architecture (HCM/ERP/SCM/CX)",
    "Application integration architecture",
    "Governance and operating model",
    "Data definition and lifecycle architecture",
    "Security and compliance architecture",
    "Extensibility architecture",
    "Monitoring and observability architecture",
]


def scenarios() -> list[dict[str, Any]]:
    return [
        # Golden path (8)
        {
            "prompt_id": "golden-01",
            "category": "golden",
            "title": "ERP-HCM hire-to-retire architecture baseline",
            "objective": "Design a production-ready hire-to-retire Fusion architecture spanning HCM and ERP with governance and observability.",
            "focus": ["Cross-pillar", "Governance", "Observability"],
        },
        {
            "prompt_id": "golden-02",
            "category": "golden",
            "title": "ERP-SCM order-to-cash integration blueprint",
            "objective": "Generate a skill prompt for end-to-end O2C integration between ERP and SCM pillars with resilient interfaces.",
            "focus": ["Integration", "Security", "Data lifecycle"],
        },
        {
            "prompt_id": "golden-03",
            "category": "golden",
            "title": "CX-ERP revenue operations architecture",
            "objective": "Build a prompt for CX to ERP revenue orchestration with explicit ownership and release controls.",
            "focus": ["Cross-pillar", "Operating model", "Extensibility"],
        },
        {
            "prompt_id": "golden-04",
            "category": "golden",
            "title": "Fusion implementation governance operating model",
            "objective": "Create a prompt for enterprise governance and decision-rights across HCM/ERP/SCM/CX implementations.",
            "focus": ["Governance", "Security", "Observability"],
        },
        {
            "prompt_id": "golden-05",
            "category": "golden",
            "title": "Data definition and contract architecture",
            "objective": "Generate a prompt for canonical data contracts, lineage, and reconciliation across Fusion pillars.",
            "focus": ["Data lifecycle", "Integration", "Governance"],
        },
        {
            "prompt_id": "golden-06",
            "category": "golden",
            "title": "Security-first implementation architecture",
            "objective": "Produce a prompt for least-privilege and compliance-focused Fusion implementation design.",
            "focus": ["Security", "Governance", "Cross-pillar"],
        },
        {
            "prompt_id": "golden-07",
            "category": "golden",
            "title": "Upgrade-safe extensibility strategy",
            "objective": "Draft a prompt that balances Fusion extensibility needs with quarterly release safety.",
            "focus": ["Extensibility", "Governance", "Observability"],
        },
        {
            "prompt_id": "golden-08",
            "category": "golden",
            "title": "Unified monitoring and observability standard",
            "objective": "Build a prompt for SLO-backed observability design across all Fusion implementation pillars.",
            "focus": ["Observability", "Integration", "Security"],
        },
        # Edge-case stress (8)
        {
            "prompt_id": "edge-01",
            "category": "edge",
            "title": "Conflicting ownership across pillars",
            "objective": "Generate a prompt that resolves conflicting data ownership between HCM and ERP stakeholders.",
            "focus": ["Governance", "Data lifecycle", "Cross-pillar"],
        },
        {
            "prompt_id": "edge-02",
            "category": "edge",
            "title": "Integration pattern mismatch",
            "objective": "Create a prompt handling API-first requirements in one pillar and batch constraints in another.",
            "focus": ["Integration", "Observability", "Extensibility"],
        },
        {
            "prompt_id": "edge-03",
            "category": "edge",
            "title": "Security masking versus analytics utility",
            "objective": "Design a prompt that balances security masking with analytics usability for cross-pillar reports.",
            "focus": ["Security", "Data lifecycle", "ERP/SCM"],
        },
        {
            "prompt_id": "edge-04",
            "category": "edge",
            "title": "Latency-cost conflict under quarterly close",
            "objective": "Generate a prompt where latency targets and cost limits are both strict and potentially conflicting.",
            "focus": ["Observability", "Governance", "Integration"],
        },
        {
            "prompt_id": "edge-05",
            "category": "edge",
            "title": "Extension rollback and release gate",
            "objective": "Build a prompt for extension rollback strategy when release readiness gates fail.",
            "focus": ["Extensibility", "Governance", "Security"],
        },
        {
            "prompt_id": "edge-06",
            "category": "edge",
            "title": "Incomplete source metadata scenario",
            "objective": "Create a prompt that handles missing endpoint/PVO metadata without hallucination.",
            "focus": ["Data lifecycle", "Integration", "Hallucination control"],
        },
        {
            "prompt_id": "edge-07",
            "category": "edge",
            "title": "Cross-region deployment with compliance constraints",
            "objective": "Generate a prompt for multi-region rollout with strict data residency and audit obligations.",
            "focus": ["Security", "Governance", "Observability"],
        },
        {
            "prompt_id": "edge-08",
            "category": "edge",
            "title": "No agreed escalation model",
            "objective": "Produce a prompt that requires ownership/escalation definition before observability can be considered complete.",
            "focus": ["Observability", "Operating model", "Cross-pillar"],
        },
        # Adversarial / ambiguity-heavy (8)
        {
            "prompt_id": "adv-01",
            "category": "adversarial",
            "title": "Force unsupported metadata invention",
            "objective": "Generate a prompt that explicitly rejects unsupported requests to invent Fusion objects or APIs.",
            "focus": ["Anti-hallucination", "Security", "Governance"],
        },
        {
            "prompt_id": "adv-02",
            "category": "adversarial",
            "title": "Ambiguous scope spanning all pillars",
            "objective": "Create a prompt that converts vague scope into deterministic clarifying questions and output contracts.",
            "focus": ["Cross-pillar", "Governance", "Method discipline"],
        },
        {
            "prompt_id": "adv-03",
            "category": "adversarial",
            "title": "Conflicting architecture references",
            "objective": "Build a prompt that forces evidence ranking when references disagree across teams.",
            "focus": ["Governance", "Evidence", "Integration"],
        },
        {
            "prompt_id": "adv-04",
            "category": "adversarial",
            "title": "Unsafe customization pressure",
            "objective": "Generate a prompt that rejects non-upgrade-safe customizations and proposes extension-safe alternatives.",
            "focus": ["Extensibility", "Release safety", "Security"],
        },
        {
            "prompt_id": "adv-05",
            "category": "adversarial",
            "title": "Incomplete security assumptions",
            "objective": "Create a prompt that blocks final design when IAM or SoD assumptions are missing.",
            "focus": ["Security", "Governance", "Auditability"],
        },
        {
            "prompt_id": "adv-06",
            "category": "adversarial",
            "title": "Metric gaming attempt",
            "objective": "Build a prompt that requires measurable and falsifiable usefulness/performance metrics, not vanity KPIs.",
            "focus": ["Evaluation", "Observability", "Governance"],
        },
        {
            "prompt_id": "adv-07",
            "category": "adversarial",
            "title": "Pillar omission attack",
            "objective": "Generate a prompt that detects and rejects outputs omitting any of the seven implementation pillars.",
            "focus": ["Cross-pillar", "Quality gate", "Completeness"],
        },
        {
            "prompt_id": "adv-08",
            "category": "adversarial",
            "title": "Bypass quality-control instruction",
            "objective": "Create a prompt that enforces confidence scoring and refine-if-below-threshold behavior despite bypass attempts.",
            "focus": ["Quality control", "Reliability", "Process integrity"],
        },
    ]


def render_prompt(scenario: dict[str, Any]) -> str:
    return f"""[CONTEXT]
You are supporting the Oracle Data Management and Analytics A-Team in Oracle Fusion Cloud implementation and data/analytics architecture.
Primary architecture framing: https://www.ateam-oracle.com/oracle-fusion-cloud-implementation-architecture-a-7-pillar-framework-for-scalable-and-ai-ready-deployments [source: https://www.ateam-oracle.com/oracle-fusion-cloud-implementation-architecture-a-7-pillar-framework-for-scalable-and-ai-ready-deployments]
Prompt engineering framework: https://agentskills.io/home [source: https://agentskills.io/home]
Evaluation method: https://agentskills.io/skill-creation/evaluating-skills [source: https://agentskills.io/skill-creation/evaluating-skills]

Scenario category: {scenario['category']}
Scenario title: {scenario['title']}
Objective: {scenario['objective']}
Focus hints: {", ".join(scenario['focus'])}

[ROLE]
Act as a senior Oracle Fusion implementation architect, senior data architect, and senior Python engineer.
You must operate across HCM, ERP, SCM, and CX and produce implementation-ready skill artifacts.

[ACTION]
Generate a production-grade prompt that will create an agentskills.io skill artifact.
The output prompt must enforce CRAFT + EmotionPrompt + OPRO + ExpertPrompting + Role-Play prompting.
Take a deep breath and work through this step by step.
Do not invent Fusion metadata, architecture standards, or security controls.
Unknowns must be marked UNVERIFIED.

[FORMAT]
Return deterministic sections:
1) Requirements Summary
2) Skill Package Blueprint
3) 7-pillar implementation coverage map
4) Technical guardrails and edge cases
5) Evaluation plan and runtime commands
6) Confidence scoring with refine-if-<0.9

[TARGET]
Data Management and Analytics A-Team architects and engineers.

[METHODOLOGY]
1. Consider fundamental requirements.
2. Maximize anti-hallucination guardrails.
3. Design the optimal prompt/skill architecture.
4. Address edge cases and operating risks.
5. Define usefulness/performance measurement gates.

[QUALITY CONTROL]
Rate confidence (0-1) on scalability, effectiveness, reliability, completeness.
If any score < 0.9, refine until all are >= 0.9.

7-pillar architecture checklist (must be explicit):
1. {PILLARS[0]}
2. {PILLARS[1]}
3. {PILLARS[2]}
4. {PILLARS[3]}
5. {PILLARS[4]}
6. {PILLARS[5]}
7. {PILLARS[6]}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic benchmark prompts for fusion-skill-prompt-architect")
    parser.add_argument("--output-dir", required=True, help="Directory to write synthetic prompt text files")
    parser.add_argument("--output-manifest", required=True, help="Path to output manifest JSON")
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.output_manifest).resolve()

    entries = []
    for scenario in scenarios():
        started = time.perf_counter()
        text = render_prompt(scenario)
        prompt_file = out_dir / f"{scenario['prompt_id']}.txt"
        prompt_file.write_text(text, encoding="utf-8")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        prompt_ref = Path(os.path.relpath(prompt_file, manifest_path.parent)).as_posix()

        row = dict(scenario)
        row.update(
            {
                "prompt_file": prompt_ref,
                "generation_latency_ms": elapsed_ms,
                "word_count": len(text.split()),
            }
        )
        entries.append(row)

    manifest = {
        "generator": "fusion-skill-prompt-architect/scripts/generate_synthetic_prompts.py",
        "version": "1.0",
        "prompt_count": len(entries),
        "categories": {
            "golden": 8,
            "edge": 8,
            "adversarial": 8,
        },
        "prompts": entries,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(entries)} prompts")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
