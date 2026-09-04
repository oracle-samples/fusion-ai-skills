#!/usr/bin/env python3
"""
Run prompt-skill evaluation and always generate a browser-ready HTML report.

This wrapper enforces the operational policy that every prompt-generation run
must produce both:
1) JSON scorecard
2) HTML report (sortable/filterable)

Example:
  python3 evaluate_prompt_skill_with_report.py \
    --params ../assets/synthetic-benchmark/synthetic_eval_params.json \
    --manifest ../assets/synthetic-benchmark/synthetic_prompt_manifest.json \
    --scorecard-output ../assets/synthetic-benchmark/synthetic_scorecard.json \
    --html-output ../assets/synthetic-benchmark/synthetic_scorecard_report.html
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluate_prompt_skill import evaluate, load_params
from render_scorecard_report import build_rows, render_html


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _default_html_output(scorecard_output: Path) -> Path:
    if scorecard_output.suffix.lower() == ".json":
        return scorecard_output.with_name(scorecard_output.stem + "_report.html")
    return scorecard_output.with_suffix(".report.html")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate prompt-skill runs and generate required browser scorecard report"
    )
    parser.add_argument("--params", required=True, help="Path to evaluate_prompt_skill params JSON")
    parser.add_argument("--manifest", required=True, help="Path to prompt manifest JSON")
    parser.add_argument("--scorecard-output", required=True, help="Output JSON scorecard path")
    parser.add_argument("--html-output", help="Optional output HTML report path")
    args = parser.parse_args()

    params_path = Path(args.params).resolve()
    manifest_path = Path(args.manifest).resolve()
    scorecard_output = Path(args.scorecard_output).resolve()
    html_output = Path(args.html_output).resolve() if args.html_output else _default_html_output(scorecard_output)

    params = load_params(params_path)
    scorecard = evaluate(params)

    scorecard_output.parent.mkdir(parents=True, exist_ok=True)
    scorecard_output.write_text(json.dumps(scorecard, indent=2), encoding="utf-8")

    manifest = _load_json(manifest_path)
    rows = build_rows(eval_params=params, manifest=manifest)
    html = render_html(scorecard=scorecard, eval_params=params, manifest=manifest, rows=rows)

    html_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(html, encoding="utf-8")

    print(f"Wrote scorecard JSON: {scorecard_output}")
    print(f"Wrote browser report: {html_output}")


if __name__ == "__main__":
    main()
