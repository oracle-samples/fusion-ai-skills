#!/usr/bin/env python3
"""
Evaluate prompt usefulness/performance metrics for Fusion skill-prompt generation.

Example:
  python3 evaluate_prompt_skill.py \
    --params evaluate_prompt_skill.params.example.json \
    --output prompt_skill_scorecard.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def load_params(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("params root must be a JSON object")
    return payload


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_rate(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    if pct <= 0:
        return min(values)
    if pct >= 100:
        return max(values)
    ordered = sorted(values)
    rank = (pct / 100.0) * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _gate_check(metric_value: float | None, operator: str, threshold: float) -> str:
    if metric_value is None:
        return "not_evaluable"
    if operator == ">=":
        return "pass" if metric_value >= threshold else "fail"
    if operator == "<=":
        return "pass" if metric_value <= threshold else "fail"
    raise ValueError(f"Unsupported gate operator: {operator}")


def evaluate(params: dict[str, Any]) -> dict[str, Any]:
    runs = params.get("prompt_runs", [])
    if not isinstance(runs, list):
        raise ValueError("'prompt_runs' must be a list")

    thresholds = params.get("thresholds", {})
    if not isinstance(thresholds, dict):
        raise ValueError("'thresholds' must be a JSON object when provided")

    success_count = 0
    first_pass_count = 0
    accepted_count = 0
    coverage_present = 0.0
    coverage_required = 0.0
    implementation_pillars_covered = 0.0
    implementation_pillars_required = 0.0
    verified_claims = 0.0
    total_claims = 0.0
    unsupported_claims = 0.0
    latencies: list[float] = []
    iterations: list[float] = []
    generated_tokens = 0.0
    repeat_cases = 0
    consistent_cases = 0

    for row in runs:
        if not isinstance(row, dict):
            continue
        success_count += 1 if _as_bool(row.get("successful", False)) else 0
        first_pass_count += 1 if _as_bool(row.get("first_pass_accepted", False)) else 0
        accepted_count += 1 if _as_bool(row.get("accepted_artifact", False)) else 0

        coverage_present += _as_float(row.get("sections_present", 0.0), 0.0)
        coverage_required += _as_float(row.get("sections_required", 0.0), 0.0)

        implementation_pillars_covered += _as_float(row.get("implementation_pillars_covered", 0.0), 0.0)
        implementation_pillars_required += _as_float(row.get("implementation_pillars_required", 0.0), 0.0)

        verified_claims += _as_float(row.get("verified_claims", 0.0), 0.0)
        total_claims += _as_float(row.get("total_claims", 0.0), 0.0)
        unsupported_claims += _as_float(row.get("unsupported_claims", 0.0), 0.0)

        latency = _as_float(row.get("latency_ms", 0.0), 0.0)
        if latency > 0:
            latencies.append(latency)

        iteration = _as_float(row.get("iterations", 0.0), 0.0)
        if iteration > 0:
            iterations.append(iteration)

        generated_tokens += _as_float(row.get("generated_tokens", 0.0), 0.0)

        if _as_bool(row.get("is_repeat_case", False)):
            repeat_cases += 1
            if _as_bool(row.get("consistent", False)):
                consistent_cases += 1

    total_runs = len([r for r in runs if isinstance(r, dict)])

    metrics = {
        "task_success_rate": _safe_rate(float(success_count), float(total_runs)),
        "first_pass_acceptance_rate": _safe_rate(float(first_pass_count), float(total_runs)),
        "coverage_rate": _safe_rate(coverage_present, coverage_required),
        "implementation_coverage_rate": _safe_rate(
            implementation_pillars_covered, implementation_pillars_required
        ),
        "fusion_fidelity_rate": _safe_rate(verified_claims, total_claims),
        "hallucination_rate": _safe_rate(unsupported_claims, total_claims),
        "p95_latency_ms": _percentile(latencies, 95.0),
        "avg_iteration_count": _safe_rate(sum(iterations), float(len(iterations))),
        "accepted_per_1k_tokens": (
            ((accepted_count / generated_tokens) * 1000.0) if generated_tokens > 0 else None
        ),
        "consistency_rate": _safe_rate(float(consistent_cases), float(repeat_cases)),
        "sample_size": total_runs,
        "repeat_sample_size": repeat_cases,
    }

    gates = {
        "task_success_rate": (">=", float(thresholds.get("task_success_rate_min", 0.90))),
        "fusion_fidelity_rate": (">=", float(thresholds.get("fusion_fidelity_rate_min", 0.95))),
        "implementation_coverage_rate": (
            ">=", float(thresholds.get("implementation_coverage_rate_min", 0.95))
        ),
        "hallucination_rate": ("<=", float(thresholds.get("hallucination_rate_max", 0.02))),
        "p95_latency_ms": ("<=", float(thresholds.get("p95_latency_ms_max", 3000.0))),
        "avg_iteration_count": ("<=", float(thresholds.get("avg_iteration_count_max", 2.0))),
    }

    gate_results: dict[str, dict[str, Any]] = {}
    overall = "green"
    for metric_name, (operator, threshold) in gates.items():
        value = metrics.get(metric_name)
        status = _gate_check(value if isinstance(value, (int, float)) else None, operator, threshold)
        gate_results[metric_name] = {
            "status": status,
            "operator": operator,
            "threshold": threshold,
            "value": value,
        }
        if status == "fail":
            overall = "red"
        elif status == "not_evaluable" and overall != "red":
            overall = "amber"

    return {
        "overall_status": overall,
        "metrics": metrics,
        "gate_results": gate_results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate usefulness/performance metrics for prompt skill runs")
    parser.add_argument("--params", required=True, help="Path to params JSON")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    params = load_params(Path(args.params).resolve())
    result = evaluate(params)
    text = json.dumps(result, indent=2)

    if args.output:
        out = Path(args.output).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote: {out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
