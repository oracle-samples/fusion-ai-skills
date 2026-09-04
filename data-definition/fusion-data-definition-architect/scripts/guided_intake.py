#!/usr/bin/env python3
"""Guided intake for the Fusion Data Definition Architect skill.

This script gives first-time users a simple, low-friction way to start by
capturing a small set of inputs and converting them into:

- a structured intake manifest (JSON)
- a markdown onboarding summary
- recommended prompts inferred from the requested object and mode
- an optional one-command artifact bundle run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from generate_artifact_bundle import main as generate_artifact_bundle_main
from object_catalog import infer_source_target_objects


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
BUNDLE_SCRIPT = BASE_DIR / "generate_artifact_bundle.py"

DEFAULT_OUTPUTS = [
    "mapping table",
    "validation summary",
    "reconciliation strategy",
]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def slugify(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "artifact"


def parse_outputs(raw_values: List[str] | None) -> List[str]:
    if not raw_values:
        return list(DEFAULT_OUTPUTS)

    parsed: List[str] = []
    for raw in raw_values:
        for item in raw.split(","):
            value = item.strip()
            if value and value not in parsed:
                parsed.append(value)
    return parsed or list(DEFAULT_OUTPUTS)


def prompt_value(question: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    response = input(f"{question}{suffix}: ").strip()
    return response or (default or "")


def prompt_yes_no(question: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{question} {suffix}: ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def infer_mode(use_live_fa: bool) -> str:
    return "live-fa" if use_live_fa else "knowledge"


def infer_interaction_profile(config: Dict[str, Any]) -> Dict[str, str]:
    desired_text = " ".join(config.get("desired_outputs", [])).lower()
    if config.get("mode") == "live-fa" or any(
        marker in desired_text
        for marker in ("full", "strategy", "governance", "reconciliation")
    ):
        depth = "implementation-ready"
    elif any(marker in desired_text for marker in ("summary", "light", "minimal")):
        depth = "concise"
    else:
        depth = "standard"

    return {
        "tone": "business-friendly",
        "output_depth": depth,
    }


def build_recommended_prompts(config: Dict[str, Any]) -> Dict[str, Any]:
    source_object = config["source_object"]
    target_object = config["target_object"]
    business_object = config["business_object"]
    mode = config["mode"]

    live_prompt = (
        f"Retrieve Fusion object attributes for {target_object} from my environment and export to Excel"
    )
    choices = [
        f"Identify objects from source system for {business_object}",
        f"Generate source-to-Fusion mapping for {business_object}",
        f"Validate mapping completeness for {business_object}",
    ]

    starter = live_prompt if mode == "live-fa" else choices[0]
    expected_artifacts = [
        "Inputs Summary",
        "Object Identification",
        "Mapping Table",
        "Validation Results",
        "Reconciliation Strategy",
    ]
    if mode == "live-fa":
        expected_artifacts.append("JSON / Excel metadata export")

    return {
        "starter_prompt": starter,
        "recommended_choices": choices,
        "object_pair_prompt": f"Generate source-to-Fusion mapping for {source_object} to {target_object}",
        "expected_artifacts": expected_artifacts,
    }


def build_manifest(config: Dict[str, Any]) -> Dict[str, Any]:
    manifest = dict(config)
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["interaction_profile"] = infer_interaction_profile(config)
    manifest["entry_path"] = build_recommended_prompts(config)
    manifest["plain_mode_rule"] = {
        "knowledge": "Generic question = knowledge mode",
        "live-fa": '"From my environment" = live FA mode',
    }
    manifest["required_output_structure"] = [
        "Inputs Summary",
        "Object Identification",
        "Mapping Table",
        "Validation Results",
        "Reconciliation Strategy",
    ]
    return manifest


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_markdown_summary(manifest: Dict[str, Any], manifest_path: Path) -> str:
    entry = manifest["entry_path"]
    next_command = (
        f"python3 {BUNDLE_SCRIPT} --manifest {manifest_path}"
    )
    lines = [
        "# Guided Intake Summary",
        "",
        "## Inputs Summary",
        "",
        f"- Source System: {manifest['source_system']}",
        f"- Target Module: {manifest['target_module']}",
        f"- Business Object: {manifest['business_object']}",
        f"- Source Object: {manifest['source_object']}",
        f"- Target Object: {manifest['target_object']}",
        f"- Object Resolution: {manifest.get('resolution_note', 'Not provided')}",
        f"- Desired Outputs: {', '.join(manifest['desired_outputs'])}",
        f"- Mode: {manifest['mode']}",
        "",
        "## Plain Rule",
        "",
        "- Generic question = knowledge mode",
        '- "From my environment" = live FA mode',
        "",
        "## Recommended Entry Path",
        "",
        f"- Starter Prompt: `{entry['starter_prompt']}`",
        f"- Object Pair Prompt: `{entry['object_pair_prompt']}`",
        "- Recommended Choices:",
    ]
    lines.extend(f"  - `{prompt}`" for prompt in entry["recommended_choices"])
    lines.extend([
        "",
        "## Expected Artifacts",
        "",
    ])
    lines.extend(f"- {artifact}" for artifact in entry["expected_artifacts"])
    lines.extend([
        "",
        "## Recommended Next Command",
        "",
        f"```bash\n{next_command}\n```",
        "",
    ])
    return "\n".join(lines)


def collect_config(args: argparse.Namespace) -> Dict[str, Any]:
    interactive = sys.stdin.isatty()

    source_system = args.source_system or (prompt_value("Source system", "Oracle EBS") if interactive else "Oracle EBS")
    target_module = args.target_module or (prompt_value("Target Fusion module", "Oracle Fusion ERP") if interactive else "Oracle Fusion ERP")
    business_object = args.business_object or (prompt_value("Business object / domain", "Purchase Orders") if interactive else "Purchase Orders")
    inferred_objects = infer_source_target_objects(source_system, target_module, business_object)
    source_object = args.source_object or inferred_objects["source_object"]
    target_object = args.target_object or inferred_objects["target_object"]

    use_live_fa = args.live_fa
    if not args.live_fa and interactive:
        use_live_fa = prompt_yes_no("Use live Fusion Applications environment mode?", default=False)

    desired_outputs = parse_outputs(args.desired_outputs)
    if interactive and not args.desired_outputs:
        raw_outputs = prompt_value(
            "Desired outputs (comma-separated)",
            ", ".join(DEFAULT_OUTPUTS),
        )
        desired_outputs = parse_outputs([raw_outputs])

    return {
        "source_system": source_system,
        "target_module": target_module,
        "business_object": business_object,
        "source_object": source_object,
        "target_object": target_object,
        "resolution": inferred_objects["resolution"],
        "resolution_note": inferred_objects["resolution_note"],
        "desired_outputs": desired_outputs,
        "mode": infer_mode(use_live_fa),
    }


def run_bundle(manifest_path: Path) -> int:
    original_argv = sys.argv
    try:
        sys.argv = [str(BUNDLE_SCRIPT), "--manifest", str(manifest_path)]
        return generate_artifact_bundle_main()
    finally:
        sys.argv = original_argv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guided intake for the Fusion Data Definition Architect skill.")
    parser.add_argument("--source-system")
    parser.add_argument("--target-module")
    parser.add_argument("--business-object")
    parser.add_argument("--source-object")
    parser.add_argument("--target-object")
    parser.add_argument(
        "--desired-outputs",
        action="append",
        help="Desired outputs. Repeat the flag or use comma-separated values.",
    )
    parser.add_argument(
        "--live-fa",
        action="store_true",
        help="Use live Fusion Applications environment mode.",
    )
    parser.add_argument(
        "--generate-bundle",
        action="store_true",
        help="Deprecated: bundle generation now runs by default unless --intake-only is used.",
    )
    parser.add_argument(
        "--intake-only",
        action="store_true",
        help="Collect input and create intake files only, without generating the Excel bundle.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = collect_config(args)
    manifest = build_manifest(config)

    timestamp = utc_timestamp()
    slug = slugify(f"{config['source_system']}-{config['target_object']}")
    manifest_path = OUTPUT_DIR / f"guided_intake_{timestamp}_{slug}.json"
    summary_path = OUTPUT_DIR / f"guided_intake_{timestamp}_{slug}.md"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_text(summary_path, render_markdown_summary(manifest, manifest_path))

    print(f"Guided intake manifest created: {manifest_path}", flush=True)
    print(f"Guided intake summary created: {summary_path}", flush=True)
    print(f"Recommended starter prompt: {manifest['entry_path']['starter_prompt']}", flush=True)

    if not args.intake_only:
        print("Running one-command artifact bundle...", flush=True)
        sys.stdout.flush()
        return run_bundle(manifest_path)

    print(f"Next command: python3 {BUNDLE_SCRIPT} --manifest {manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
