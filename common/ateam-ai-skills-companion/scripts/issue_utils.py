## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

PRIORITY_ORDER = {
    "P0": 0,
    "P1": 1,
    "P2": 2,
    "P3": 3,
}

OVERLOAD_ISSUE = "Possible functionality overload"

P0_BLOCKING_ISSUES = {
    "Missing mandatory publishing file",
    "Missing mandatory compliance content",
    "Unable to inspect mandatory compliance content",
    "Missing required package file",
    "Missing SKILL.md",
    "Missing skill name",
    "Skill name is too long",
    "Skill name contains underscores",
    "Skill name contains spaces",
    "Skill name has leading or trailing hyphen",
    "Skill name must be lowercase",
    "Skill name must use lowercase hyphen-case",
    "Skill name does not follow naming convention",
    "Package folder name does not match skill name",
}

P1_BLOCKING_ISSUES = {
    "Missing README",
    "Missing Quick Start section",
    "Missing Workflow section",
    "Insufficient prompts (<3)",
    "Missing workflow definition",
    "Missing inputs definition",
    "Missing outputs definition",
    "Insufficient inputs definition",
    "Insufficient outputs definition",
    "Workflow is incomplete",
    "Inputs and outputs need more specificity",
    "Prompts need stronger coverage",
    "Quick Start is not clear enough",
}

P2_ISSUES = {
    "Missing Real Example section",
    "Examples are missing or weak",
    "Metadata is incomplete",
    "Supporting scripts need stronger readiness signals",
}

BLOCKING_SECURITY_SEVERITIES = {"critical", "high"}


def enrich_issues(issues, security_findings=None):
    return [classify_issue(issue, security_findings) for issue in issues]


def classify_issue(issue, security_findings=None):
    enriched = dict(issue)
    priority, blocking = _classify(enriched, security_findings or [])

    if _valid_priority(enriched.get("priority")):
        priority = enriched["priority"]

    if isinstance(enriched.get("blocking"), bool):
        blocking = enriched["blocking"]

    enriched["priority"] = priority
    enriched["blocking"] = bool(blocking)
    return enriched


def sort_issues(issues):
    return sorted(issues, key=issue_sort_key)


def issue_sort_key(issue):
    priority = issue.get("priority", "P2")
    return (
        0 if issue.get("blocking") else 1,
        PRIORITY_ORDER.get(priority, PRIORITY_ORDER["P2"]),
        str(issue.get("file", "")),
        str(issue.get("issue", "")),
    )


def blocking_issues(issues):
    return [issue for issue in issues if issue.get("blocking")]


def suggestion_for_issue(issue):
    return f"[{issue['file']}] {issue['fix']}"


def _classify(issue, security_findings):
    issue_text = str(issue.get("issue", "")).strip()
    issue_lower = issue_text.lower()

    if issue_text == OVERLOAD_ISSUE:
        return "P3", False

    if issue_text in P0_BLOCKING_ISSUES:
        return "P0", True

    if issue_text in P1_BLOCKING_ISSUES:
        return "P1", True

    if issue_text in P2_ISSUES:
        return "P2", False

    if "placeholder marker found" in issue_lower:
        return "P0", True

    if "python script is not importable" in issue_lower:
        return "P0", True

    if _is_unsafe_package_issue(issue_lower):
        return "P0", True

    if issue_text == "Security findings reduce readiness":
        if _has_blocking_security(security_findings):
            return "P0", True
        return "P1", False

    return "P2", False


def _is_unsafe_package_issue(issue_lower):
    unsafe_terms = (
        "unsafe zip",
        "invalid zip",
        "path traversal",
        "absolute path in zip",
        "escapes extraction root",
        "too many files in zip",
        "zip package is too large",
        "zip member is too large",
        "symlink entries are not allowed",
    )
    return any(term in issue_lower for term in unsafe_terms)


def _has_blocking_security(security_findings):
    for finding in security_findings:
        severity = str(finding.get("severity", "")).lower()
        if severity in BLOCKING_SECURITY_SEVERITIES:
            return True
    return False


def _valid_priority(priority):
    return priority in PRIORITY_ORDER
