## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

GROUP_ORDER = [
    "Review",
    "Improve",
    "Security",
    "Documentation",
    "Packaging/submission",
    "Re-review",
]


def _contains_any(values, indicators):
    text = " ".join(str(value).lower() for value in values)
    return any(indicator in text for indicator in indicators)


def _append_unique(items, value):
    if value not in items:
        items.append(value)


def _detected_context(ctx):
    inputs = ctx.get("inputs_list", [])
    outputs = ctx.get("outputs_list", [])
    workflow = ctx.get("workflow_steps", [])
    all_context = inputs + outputs + workflow

    return {
        "has_zip": _contains_any(all_context, ["zip", "archive", "bundle", "package"]),
        "has_text": _contains_any(inputs, ["text", "paste", "definition"]),
        "has_files": _contains_any(inputs, ["readme", "skill.md", "yaml", "individual files"]),
        "has_security": _contains_any(outputs, ["security", "secret", "risk"]),
        "has_workflow": bool(workflow),
    }


def generate_prompt_groups(ctx):
    """
    Generate a small, curated prompt catalog grouped by user intent.
    """
    context = _detected_context(ctx)
    groups = {name: [] for name in GROUP_ORDER}

    _append_unique(groups["Review"], "Review this skill")
    if context["has_zip"]:
        _append_unique(groups["Review"], "Review this ZIP skill package for submission readiness")
    elif context["has_files"]:
        _append_unique(groups["Review"], "Review these skill files for submission readiness")

    if context["has_text"]:
        _append_unique(groups["Review"], "Review this pasted skill definition for submission readiness")

    _append_unique(groups["Improve"], "Improve this skill")
    _append_unique(groups["Improve"], "What are the top 3 improvements?")
    _append_unique(groups["Improve"], "What would confuse a first-time user?")

    _append_unique(groups["Security"], "Scan this skill package for secrets and unsafe operations")
    _append_unique(groups["Security"], "What security findings block submission?")

    _append_unique(groups["Documentation"], "Is documentation sufficient for a new user?")
    _append_unique(groups["Documentation"], "What documentation is missing or unclear?")

    _append_unique(groups["Packaging/submission"], "Is this ready for submission?")
    _append_unique(groups["Packaging/submission"], "What blocks approval?")
    if context["has_zip"]:
        _append_unique(groups["Packaging/submission"], "Validate this skill bundle before submission")

    _append_unique(groups["Re-review"], "Re-review after changes")
    _append_unique(groups["Re-review"], "Validate improvements made")

    return {name: prompts for name, prompts in groups.items() if prompts}


def generate_prompts(ctx):
    """
    Return the curated prompt catalog as a flat list for backwards compatibility.
    """
    prompts = []

    for group_prompts in generate_prompt_groups(ctx).values():
        for prompt in group_prompts:
            _append_unique(prompts, prompt)

    return prompts[:15]
