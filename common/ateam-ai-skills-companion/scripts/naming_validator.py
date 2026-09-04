## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import re


MAX_SKILL_NAME_LENGTH = 64
VALID_SKILL_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<body>.*?)\n---", re.DOTALL)


def normalize_package_name(package_name):
    if not package_name:
        return None

    normalized = str(package_name).strip().replace("\\", "/").rstrip("/")
    if not normalized:
        return None

    return normalized.split("/")[-1] or None


def extract_skill_name(text):
    match = FRONTMATTER_RE.match(text or "")
    if not match:
        return ""

    for line in match.group("body").splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        if key.strip() == "name":
            return value.strip().strip("\"'")

    return ""


def validate_skill_name(name, package_name=None):
    issues = []
    clean_name = (name or "").strip()

    if not clean_name:
        issues.append({
            "file": "SKILL.md",
            "issue": "Missing skill name",
            "why": "Codex skills need a frontmatter name so they can be identified and invoked reliably.",
            "fix": "Add a `name` value in SKILL.md frontmatter using lowercase hyphen-case.",
        })
        return issues

    if len(clean_name) > MAX_SKILL_NAME_LENGTH:
        issues.append({
            "file": "SKILL.md",
            "issue": "Skill name is too long",
            "why": f"Skill names should stay at or below {MAX_SKILL_NAME_LENGTH} characters for readability and portability.",
            "fix": f"Shorten `{clean_name}` to {MAX_SKILL_NAME_LENGTH} characters or fewer.",
        })

    if "_" in clean_name:
        issues.append({
            "file": "SKILL.md",
            "issue": "Skill name contains underscores",
            "why": "Skill names should use hyphen-case, not snake_case.",
            "fix": f"Rename `{clean_name}` using hyphens instead of underscores.",
        })

    if any(char.isspace() for char in clean_name):
        issues.append({
            "file": "SKILL.md",
            "issue": "Skill name contains spaces",
            "why": "Spaces make skill names harder to reference consistently.",
            "fix": f"Rename `{clean_name}` using lowercase hyphen-case.",
        })

    if clean_name.startswith("-") or clean_name.endswith("-"):
        issues.append({
            "file": "SKILL.md",
            "issue": "Skill name has leading or trailing hyphen",
            "why": "Leading or trailing hyphens make names look unfinished and can break simple tooling assumptions.",
            "fix": f"Remove leading or trailing hyphens from `{clean_name}`.",
        })

    if clean_name.lower() != clean_name:
        issues.append({
            "file": "SKILL.md",
            "issue": "Skill name must be lowercase",
            "why": "Lowercase names are easier to compare, package, and invoke consistently.",
            "fix": f"Rename `{clean_name}` using lowercase letters, digits, and hyphens only.",
        })

    if not VALID_SKILL_NAME_RE.match(clean_name):
        issues.append({
            "file": "SKILL.md",
            "issue": "Skill name must use lowercase hyphen-case",
            "why": "Skill names should contain only lowercase letters, digits, and hyphens.",
            "fix": f"Rename `{clean_name}` to a value like `skill-reviewer`.",
        })

    clean_package = normalize_package_name(package_name)
    if clean_package:
        if clean_package and clean_package != clean_name:
            issues.append({
                "file": "SKILL.md",
                "issue": "Package folder name does not match skill name",
                "why": "Matching package and skill names make ZIP review, publishing, and troubleshooting simpler.",
                "fix": f"Rename the package folder to `{clean_name}` or update SKILL.md `name` to `{clean_package}`.",
            })

    return _dedupe_issues(issues)


def is_valid_skill_name(name, package_name=None):
    return not validate_skill_name(name, package_name)


def _dedupe_issues(issues):
    seen = set()
    unique = []

    for issue in issues:
        key = (issue["file"], issue["issue"], issue["fix"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)

    return unique
