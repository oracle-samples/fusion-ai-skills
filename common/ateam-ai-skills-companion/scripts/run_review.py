## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import argparse
import json
import os
import sys
import tempfile

from parser import analyze
from engine import calculate_score
from issue_utils import blocking_issues, enrich_issues, sort_issues, suggestion_for_issue
from mandatory_validator import validate_mandatory_content
from prompt_gen import generate_prompt_groups, generate_prompts
from scope_validator import detect_functionality_overload
from security_validator import detect_security_issues
from zip_loader import extract_zip, infer_package_name, read_package_text_files, read_skill_files_with_context


def _issue(file, issue, why, fix):
    return {
        "file": file,
        "issue": issue,
        "why": why,
        "fix": fix,
    }


def map_issues_to_files(ctx, file_map, score_reasons):
    issues = []

    if "README.md" not in file_map:
        issues.append(_issue(
            "README.md",
            "Missing README",
            "A skill package needs an onboarding surface users can scan before invoking it.",
            "Create README.md with Quick Start, Workflow, Real Example, and Prompts sections.",
        ))
    else:
        readme = file_map["README.md"].lower()

        if "quick start" not in readme:
            issues.append(_issue(
                "README.md",
                "Missing Quick Start section",
                "First-time users need to know the first prompt or command to run.",
                "Add a concise Quick Start with one copyable prompt or CLI command.",
            ))

        if "workflow" not in readme:
            issues.append(_issue(
                "README.md",
                "Missing Workflow section",
                "The review loop should be predictable: upload, review, fix, re-review, submit.",
                "Add a clear step-by-step workflow.",
            ))

        if "real example" not in readme:
            issues.append(_issue(
                "README.md",
                "Missing Real Example section",
                "Concrete input and output examples make the skill easier to trust.",
                "Add a small input-to-output example.",
            ))

    if "SKILL.md" not in file_map and file_map:
        issues.append(_issue(
            "SKILL.md",
            "Missing SKILL.md",
            "Codex skills require SKILL.md metadata and operating instructions.",
            "Create SKILL.md with frontmatter, inputs, outputs, workflow, and prompts.",
        ))

    if ctx["prompts_count"] < 3:
        issues.append(_issue(
            "SKILL.md",
            "Insufficient prompts (<3)",
            "Prompts are the primary interface and need enough coverage for review, improvement, and iteration.",
            "Add at least 3 strong prompts for usability.",
        ))

    if ctx["workflow_count"] == 0:
        issues.append(_issue(
            "SKILL.md",
            "Missing workflow definition",
            "Codex needs the intended procedure to produce consistent reviews.",
            "Define a step-by-step workflow under a Workflow section.",
        ))

    if ctx["inputs_count"] == 0:
        issues.append(_issue(
            "SKILL.md",
            "Missing inputs definition",
            "The reviewer must know which artifacts it can evaluate.",
            "Add an Inputs section with supported input types.",
        ))
    elif ctx["inputs_count"] < 2:
        issues.append(_issue(
            "SKILL.md",
            "Insufficient inputs definition",
            "A single input type makes the skill less useful for real submission workflows.",
            "Document ZIP packages, pasted text, and individual skill files where supported.",
        ))

    if ctx["outputs_count"] == 0:
        issues.append(_issue(
            "SKILL.md",
            "Missing outputs definition",
            "Users need to know what the review will return before relying on it.",
            "Add an Outputs section with expected review results.",
        ))
    elif ctx["outputs_count"] < 2:
        issues.append(_issue(
            "SKILL.md",
            "Insufficient outputs definition",
            "Useful reviews need more than a single status value.",
            "Document score, issues, fixes, security findings, generated prompts, and readiness.",
        ))

    handled = {issue["issue"].split(" (")[0].lower() for issue in issues}
    for reason in score_reasons:
        if isinstance(reason, dict):
            if reason.get("status") == "pass" or not reason.get("issue"):
                continue
            points = reason.get("points", 0)
            max_points = reason.get("max_points", 1) or 1
            is_material_gap = (
                reason.get("force_issue")
                or reason.get("status") == "fail"
                or (points / max_points) < 0.8
            )
            if not is_material_gap:
                continue

            base = reason["issue"].split(" (")[0].lower()
            if base in handled:
                continue

            issues.append(_issue(
                reason.get("file", "SKILL.md"),
                reason["issue"],
                reason.get("why", reason.get("detail", "This scoring gap lowers readiness.")),
                reason.get("fix", "Improve this area before submission."),
            ))
            handled.add(base)
            continue

        base = str(reason).split(" (")[0].lower()
        if base in handled:
            continue

        issues.append(_issue(
            "SKILL.md",
            str(reason),
            "This scoring gap prevents the package from meeting the readiness threshold.",
            "Update the relevant SKILL.md section so the score reflects the intended behavior.",
        ))
        handled.add(base)

    return issues


def generate_suggestions(issues):
    suggestions = []
    seen = set()

    for issue in issues:
        suggestion = suggestion_for_issue(issue)
        if suggestion not in seen:
            seen.add(suggestion)
            suggestions.append(suggestion)

    return suggestions


def run_from_text(
    text,
    file_map=None,
    package_name=None,
    mandatory_file_map=None,
    package_files=None,
    mandatory_requirements=None,
):
    ctx = analyze(text)
    if package_name:
        ctx["package_name"] = package_name

    security = detect_security_issues(text, file_map or ctx.get("file_text"))
    score, reasons = calculate_score(ctx, security)
    prompts = generate_prompts(ctx)
    prompt_groups = generate_prompt_groups(ctx)

    review_file_map = file_map or {}
    mandatory_file_map = mandatory_file_map or review_file_map
    package_files = package_files or list(mandatory_file_map)

    issues = map_issues_to_files(ctx, review_file_map, reasons)
    issues.extend(validate_mandatory_content(mandatory_file_map, package_files, mandatory_requirements))
    issues.extend(detect_functionality_overload(ctx, file_map or ctx.get("file_text")))
    issues = sort_issues(enrich_issues(issues, security))
    suggestions = generate_suggestions(issues)
    approval_blockers = blocking_issues(issues)
    readiness = "READY" if score >= 90 and not approval_blockers else "NOT_READY"

    return {
        "summary": "Skill reviewed with file-level diagnostics",
        "score": score,
        "issues": issues,
        "suggestions": suggestions,
        "security": security,
        "score_reasons": reasons,
        "prompt_groups": prompt_groups,
        "prompts": prompts,
        "readiness": readiness,
    }


def run_from_zip(zip_path, mandatory_requirements=None):
    with tempfile.TemporaryDirectory(prefix="skill_review_") as folder:
        extract_zip(zip_path, folder)
        text, file_map = read_skill_files_with_context(folder)
        mandatory_file_map, package_files = read_package_text_files(folder)
        return run_from_text(
            text,
            file_map,
            infer_package_name(folder),
            mandatory_file_map,
            package_files,
            mandatory_requirements,
        )


def run_from_directory(folder, mandatory_requirements=None):
    text, file_map = read_skill_files_with_context(folder)
    mandatory_file_map, package_files = read_package_text_files(folder)
    return run_from_text(
        text,
        file_map,
        infer_package_name(folder) or os.path.basename(os.path.abspath(folder)),
        mandatory_file_map,
        package_files,
        mandatory_requirements,
    )


def run_from_file(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
    except OSError as exc:
        raise ValueError(f"Unable to read input file: {path}") from exc

    name = os.path.basename(path)
    return run_from_text(f"\n\n### FILE: {name}\n{content}", {name: content})


def detect_input_type(input_data):
    if isinstance(input_data, str) and os.path.isdir(input_data):
        return "directory"

    if isinstance(input_data, str) and os.path.isfile(input_data):
        if input_data.lower().endswith(".zip"):
            return "zip"
        return "file"

    if isinstance(input_data, str):
        return "text"

    return "unknown"


def run(input_data):
    input_type = detect_input_type(input_data)

    if input_type == "directory":
        return run_from_directory(input_data)

    if input_type == "zip":
        return run_from_zip(input_data)

    if input_type == "file":
        return run_from_file(input_data)

    if input_type == "text":
        return run_from_text(input_data)

    raise ValueError("Unsupported input type")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review an AI skill package.")
    parser.add_argument("input", nargs="?", help="Skill directory, ZIP, file, or raw text. Reads stdin when omitted.")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON without indentation.")
    args = parser.parse_args(argv)

    input_data = args.input
    if input_data is None:
        input_data = sys.stdin.read()

    try:
        result = run(input_data)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    indent = None if args.compact else 2
    print(json.dumps(result, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
