#!/usr/bin/env python3
"""
Build evaluate_prompt_skill-compatible params from a synthetic prompt manifest.

This utility creates deterministic, synthetic run metrics for benchmarking and can
be replaced later with real observed run telemetry.

Example:
  python3 build_synthetic_eval_params.py \
    --manifest ../assets/synthetic-benchmark/synthetic_prompt_manifest.json \
    --output ../assets/synthetic-benchmark/synthetic_eval_params.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest root must be a JSON object")
    prompts = payload.get("prompts")
    if not isinstance(prompts, list):
        raise ValueError("manifest must contain a 'prompts' list")
    return payload


def synthetic_run_metrics(index: int, category: str, base_latency_ms: float) -> dict[str, Any]:
    # Deterministic shaping by category
    if category == "golden":
        success = True
        first_pass = True
        sections_present = 12
        sections_required = 12
        impl_covered = 7
        impl_required = 7
        verified = 30
        total_claims = 30
        unsupported = 0
        iterations = 1
        generated_tokens = 1500
        consistent = True
    elif category == "edge":
        success = True
        first_pass = index % 3 != 0
        sections_present = 11
        sections_required = 12
        impl_covered = 7
        impl_required = 7
        verified = 28
        total_claims = 29
        unsupported = 0
        iterations = 2
        generated_tokens = 1700
        consistent = True
    else:  # adversarial
        success = True
        first_pass = index % 2 == 0
        sections_present = 11
        sections_required = 12
        impl_covered = 6 if index % 4 == 0 else 7
        impl_required = 7
        verified = 27
        total_claims = 28
        unsupported = 1 if index in {17, 22} else 0
        iterations = 2
        generated_tokens = 1800
        consistent = index % 5 != 0

    return {
        "successful": success,
        "first_pass_accepted": first_pass,
        "accepted_artifact": success,
        "sections_present": sections_present,
        "sections_required": sections_required,
        "implementation_pillars_covered": impl_covered,
        "implementation_pillars_required": impl_required,
        "verified_claims": verified,
        "total_claims": total_claims,
        "unsupported_claims": unsupported,
        "latency_ms": round(base_latency_ms, 2),
        "iterations": iterations,
        "generated_tokens": generated_tokens,
        "is_repeat_case": index < 8,
        "consistent": consistent,
    }


def build_params(manifest: dict[str, Any]) -> dict[str, Any]:
    prompt_rows = manifest.get("prompts", [])
    runs: list[dict[str, Any]] = []
    for i, row in enumerate(prompt_rows):
        if not isinstance(row, dict):
            continue
        category = str(row.get("category", "adversarial"))
        run = {
            "run_id": f"synthetic-{i+1:03d}",
            "prompt_id": str(row.get("prompt_id", f"p-{i+1}")),
            "category": category,
        }
        run.update(
            synthetic_run_metrics(
                index=i,
                category=category,
                base_latency_ms=1800.0 + (i % 6) * 170.0,
            )
        )
        runs.append(run)

    return {
        "thresholds": {
            "task_success_rate_min": 0.9,
            "fusion_fidelity_rate_min": 0.95,
            "implementation_coverage_rate_min": 0.95,
            "hallucination_rate_max": 0.02,
            "p95_latency_ms_max": 3000,
            "avg_iteration_count_max": 2.0,
        },
        "prompt_runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build synthetic evaluation params from synthetic prompt manifest")
    parser.add_argument("--manifest", required=True, help="Path to synthetic prompt manifest JSON")
    parser.add_argument("--output", required=True, help="Path to output params JSON")
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest).resolve())
    params = build_params(manifest)

    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(params, indent=2), encoding="utf-8")
    print(f"Wrote: {out}")
    print(f"Runs: {len(params.get('prompt_runs', []))}")


if __name__ == "__main__":
    main()
