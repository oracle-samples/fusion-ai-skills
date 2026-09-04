## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import re

from naming_validator import validate_skill_name


WEIGHTS = {
    "metadata": 10,
    "inputs_outputs": 15,
    "prompts": 15,
    "workflow": 15,
    "quick_start": 10,
    "examples": 10,
    "supporting_scripts": 15,
    "security": 10,
}


def _lower_join(values):
    return "\n".join(str(value).lower() for value in values)


def _all_text(ctx):
    return _lower_join(ctx.get("file_text", {}).values())


def _file_text(ctx, filename):
    return ctx.get("file_text", {}).get(filename, "")


def _headings_text(ctx):
    headings = []
    for file_headings in ctx.get("file_headings", {}).values():
        headings.extend(file_headings)
    return _lower_join(headings)


def _has_any(text, terms):
    return any(term in text for term in terms)


def _specific_count(items):
    generic = {"file", "files", "input", "output", "summary", "result", "results"}
    count = 0

    for item in items:
        words = [word for word in re.split(r"[^a-z0-9]+", item.lower()) if word]
        if len(words) >= 2 and not all(word in generic for word in words):
            count += 1

    return count


def _prompt_quality(prompts):
    action_words = (
        "review",
        "improve",
        "validate",
        "identify",
        "extract",
        "show",
        "what",
        "is",
    )
    useful = 0

    for prompt in prompts:
        text = prompt.strip().lower()
        if len(text.split()) >= 3 and text.startswith(action_words):
            useful += 1

    return useful


def _script_files(ctx):
    return sorted(path for path in ctx.get("file_text", {}) if path.startswith("scripts/") and path.endswith(".py"))


def _add_reason(
    reasons,
    category,
    points,
    max_points,
    detail,
    issue=None,
    file="SKILL.md",
    why=None,
    fix=None,
    force_issue=False,
):
    status = "pass"
    if points <= 0:
        status = "fail"
    elif points < max_points:
        status = "warning"

    reason = {
        "category": category,
        "points": points,
        "max_points": max_points,
        "status": status,
        "detail": detail,
    }

    if issue:
        reason.update({
            "file": file,
            "issue": issue,
            "why": why or detail,
            "fix": fix or "Improve this area before submission.",
        })
        if force_issue:
            reason["force_issue"] = True

    reasons.append(reason)


def _score_metadata(ctx, reasons):
    max_points = WEIGHTS["metadata"]
    metadata = ctx.get("file_metadata", {}).get("SKILL.md", {})
    agent_text = (_file_text(ctx, "openai.yaml") or _file_text(ctx, "agents/openai.yaml")).lower()
    name_issues = validate_skill_name(metadata.get("name"), ctx.get("package_name"))
    points = 0

    if "SKILL.md" in ctx.get("file_text", {}):
        points += 2

    if metadata.get("name"):
        points += 1

    if not name_issues:
        points += 1

    description = metadata.get("description", "")
    if description:
        points += 3 if len(description.split()) >= 5 else 2

    if "display_name" in agent_text:
        points += 1

    if "short_description" in agent_text:
        points += 1

    if "README.md" in ctx.get("file_text", {}):
        points += 1

    issue = None
    why = "Complete metadata helps Codex and users discover and understand the skill."
    fix = "Ensure SKILL.md has name and a specific description, README.md exists, and agents/openai.yaml has display metadata."
    if name_issues:
        issue = "Skill name does not follow naming convention"
        why = name_issues[0]["why"]
        fix = name_issues[0]["fix"]
    elif points < max_points:
        issue = "Metadata is incomplete"

    _add_reason(
        reasons,
        "metadata",
        points,
        max_points,
        "Metadata includes SKILL.md frontmatter, naming convention, README, and agent display metadata.",
        issue=issue,
        why=why,
        fix=fix,
        force_issue=bool(name_issues),
    )
    return points


def _score_inputs_outputs(ctx, reasons):
    max_points = WEIGHTS["inputs_outputs"]
    inputs = ctx.get("inputs_list", [])
    outputs = ctx.get("outputs_list", [])
    points = 0

    if inputs:
        points += 4
    if len(inputs) >= 2:
        points += 2
    if _specific_count(inputs) >= 2:
        points += 2

    if outputs:
        points += 3
    if len(outputs) >= 4:
        points += 2

    output_text = _lower_join(outputs)
    if _has_any(output_text, ["score", "issue", "fix", "security", "readiness", "prompt"]):
        points += 2

    issue = None
    if points < max_points:
        issue = "Inputs and outputs need more specificity"

    _add_reason(
        reasons,
        "inputs_outputs",
        points,
        max_points,
        "Inputs and outputs are scored for presence, variety, specificity, and review usefulness.",
        issue=issue,
        why="Users need to know exactly what they can provide and what the skill will return.",
        fix="List concrete input formats and detailed output fields such as score, issues, fixes, security findings, prompts, and readiness.",
    )
    return points


def _score_prompts(ctx, reasons):
    max_points = WEIGHTS["prompts"]
    prompts = ctx.get("prompts_list", [])
    prompt_text = _lower_join(prompts)
    quality_count = _prompt_quality(prompts)
    points = 0

    if prompts:
        points += 4
    if len(prompts) >= 3:
        points += 3
    if len(prompts) >= 6:
        points += 2
    if quality_count >= min(3, len(prompts)):
        points += 3
    if _has_any(prompt_text, ["review", "improve", "validate", "ready", "blocks", "confuse"]):
        points += 3

    issue = None
    if points < max_points:
        issue = "Prompts need stronger coverage"

    _add_reason(
        reasons,
        "prompts",
        points,
        max_points,
        "Prompt scoring checks count, action wording, and coverage across review, improvement, and readiness workflows.",
        issue=issue,
        why="Prompts are the product; weak prompts make the skill hard to invoke reliably.",
        fix="Add clear action-oriented prompts for review, improvement, re-review, readiness, and blocker analysis.",
    )
    return points


def _score_workflow(ctx, reasons):
    max_points = WEIGHTS["workflow"]
    workflow = ctx.get("workflow_steps", [])
    workflow_text = _lower_join(workflow)
    points = 0

    if workflow:
        points += 5
    if len(workflow) >= 3:
        points += 4
    if len(workflow) >= 5:
        points += 2
    if _has_any(workflow_text, ["detect", "extract", "read", "analyze", "identify", "generate", "output", "review"]):
        points += 4

    issue = None
    if points < max_points:
        issue = "Workflow is incomplete"

    _add_reason(
        reasons,
        "workflow",
        points,
        max_points,
        "Workflow scoring checks step count and whether the procedure covers intake, analysis, and output.",
        issue=issue,
        why="A clear workflow helps Codex produce consistent reviews instead of ad hoc feedback.",
        fix="Document a step-by-step workflow from input detection through extraction, analysis, issue mapping, suggestions, and readiness output.",
    )
    return points


def _score_quick_start(ctx, reasons):
    max_points = WEIGHTS["quick_start"]
    text = _all_text(ctx)
    headings = _headings_text(ctx)
    points = 0

    if "quick start" in headings or "quick start" in text:
        points += 4
    if re.search(r'"[^"\n]*(review|improve|validate|ready)[^"\n]*"', text):
        points += 2
    if "python3 scripts/run_review.py" in text or "copy and run" in text:
        points += 2
    if "30 seconds" in text or "usable in <30 seconds" in text:
        points += 2

    issue = None
    if points < max_points:
        issue = "Quick Start is not clear enough"

    _add_reason(
        reasons,
        "quick_start",
        points,
        max_points,
        "Quick Start scoring checks for a visible heading, copyable invocation, and fast onboarding language.",
        issue=issue,
        file="README.md",
        why="A first-time user should know what to run within seconds.",
        fix="Add a Quick Start with one copyable prompt or CLI command and a short expected result.",
    )
    return points


def _score_examples(ctx, reasons):
    max_points = WEIGHTS["examples"]
    text = _all_text(ctx)
    headings = _headings_text(ctx)
    points = 0

    if "real example" in headings or "real example" in text:
        points += 3
    if "sample output" in headings or "sample output" in text:
        points += 2
    if "input" in text and "output" in text:
        points += 2
    if _has_any(text, ["score:", "issues:", "readiness:"]):
        points += 2
    if _has_any(text, ["fix:", "suggestions:", "why:"]):
        points += 1

    issue = None
    if points < max_points:
        issue = "Examples are missing or weak"

    _add_reason(
        reasons,
        "examples",
        points,
        max_points,
        "Example scoring checks for real input, sample output, score/readiness, and fixes.",
        issue=issue,
        file="README.md",
        why="Examples let users see the review shape before they trust the skill.",
        fix="Add a realistic input-to-output example with score, issues, why/fix guidance, suggestions, and readiness.",
    )
    return points


def _score_supporting_scripts(ctx, reasons):
    max_points = WEIGHTS["supporting_scripts"]
    scripts = _script_files(ctx)

    if not scripts:
        _add_reason(
            reasons,
            "supporting_scripts",
            10,
            max_points,
            "No supporting scripts were detected; this is treated as a documentation-only skill.",
        )
        return 10

    points = 0
    script_names = set(scripts)
    script_text = _lower_join(ctx.get("file_text", {}).get(path, "") for path in scripts)

    if "scripts/run_review.py" in script_names:
        points += 4
    if "scripts/parser.py" in script_names and "scripts/engine.py" in script_names:
        points += 3
    if "scripts/merge_validator.py" in script_names or "scripts/version_compare.py" in script_names:
        points += 2
    if "argparse" in script_text and "if __name__" in script_text:
        points += 3
    if ("PASTE" + "_FULL_") not in script_text and "TODO" not in script_text:
        points += 3

    issue = None
    if points < max_points:
        issue = "Supporting scripts need stronger readiness signals"

    _add_reason(
        reasons,
        "supporting_scripts",
        points,
        max_points,
        "Supporting script scoring checks for a runner, parser/engine support, validation utilities, CLI entrypoints, and absence of placeholders.",
        issue=issue,
        file="scripts",
        why="Bundled scripts should be reliable enough to support repeatable skill reviews.",
        fix="Add or improve runner, parser/engine, validators, CLI entrypoints, and remove placeholders or TODOs.",
    )
    return points


def _score_security(reasons, security_findings):
    max_points = WEIGHTS["security"]
    findings = security_findings or []
    penalty = 0

    for finding in findings:
        severity = str(finding.get("severity", "")).lower()
        if severity in {"critical", "high"}:
            penalty += 5
        elif severity == "medium":
            penalty += 3
        else:
            penalty += 1

    points = max(max_points - penalty, 0)
    issue = None
    if points < max_points:
        issue = "Security findings reduce readiness"

    _add_reason(
        reasons,
        "security",
        points,
        max_points,
        f"Security scoring applies penalties for detected findings; findings detected: {len(findings)}.",
        issue=issue,
        file="SECURITY",
        why="Secrets, personal data, or unsafe instructions can block submission.",
        fix="Remove or redact sensitive values and replace unsafe operations with guarded workflows.",
    )
    return points


def calculate_score(ctx, security_findings=None):
    reasons = []
    score = 0

    score += _score_metadata(ctx, reasons)
    score += _score_inputs_outputs(ctx, reasons)
    score += _score_prompts(ctx, reasons)
    score += _score_workflow(ctx, reasons)
    score += _score_quick_start(ctx, reasons)
    score += _score_examples(ctx, reasons)
    score += _score_supporting_scripts(ctx, reasons)
    score += _score_security(reasons, security_findings)

    return max(min(int(round(score)), 100), 0), reasons
