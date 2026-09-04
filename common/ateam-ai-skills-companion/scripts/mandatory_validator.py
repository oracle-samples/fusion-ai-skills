## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import json
import os


DEFAULT_REQUIREMENTS_FILE = os.path.join(os.path.dirname(__file__), "mandatory_requirements.json")
DEFAULT_REQUIRED_FILES = ("SKILL.md", "README.md", "LICENSE.txt")
DEFAULT_TEXT_EXCLUDED_FILES = {"baseline_hashes.json"}
DEFAULT_TEXT_EXCLUDED_SUFFIXES = {
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".zip",
}


def load_mandatory_requirements(path=None):
    requirements = {
        "required_files": list(DEFAULT_REQUIRED_FILES),
        "required_text_rules": [],
    }
    path = path or DEFAULT_REQUIREMENTS_FILE

    if not os.path.exists(path):
        return requirements

    with open(path, "r", encoding="utf-8") as file:
        configured = json.load(file)

    requirements.update({
        "required_files": configured.get("required_files", requirements["required_files"]),
        "required_text_rules": configured.get("required_text_rules", []),
    })
    return requirements


def validate_mandatory_content(file_map, package_files=None, requirements=None):
    file_map = file_map or {}
    package_files = list(package_files or file_map.keys())
    requirements = requirements or load_mandatory_requirements()
    issues = []

    for required in requirements.get("required_files", DEFAULT_REQUIRED_FILES):
        if not _has_required_file(required, package_files, file_map):
            issues.append({
                "file": required,
                "issue": "Missing mandatory publishing file",
                "why": f"Internal publishing checks require `{required}` before external submission.",
                "fix": f"Add `{required}` to the package.",
            })

    for rule in requirements.get("required_text_rules", []):
        issues.extend(_validate_text_rule(rule, file_map, package_files))

    return issues


def _validate_text_rule(rule, file_map, package_files):
    required_text = [str(text) for text in rule.get("required_text", []) if str(text)]
    if not required_text:
        return []

    scope = rule.get("scope", "all_text_files")
    paths = _rule_paths(scope, rule, package_files)
    issues = []

    for path in paths:
        normalized = _normalize_path(path)
        if scope != "file" and _text_rule_exempt(normalized, rule):
            continue

        content = _content_for_path(file_map, normalized)
        if content is None:
            issues.append({
                "file": normalized,
                "issue": "Unable to inspect mandatory compliance content",
                "why": _rule_why(rule, "must be inspected for mandatory compliance content."),
                "fix": "Ensure the file is UTF-8 text or add a file-type exemption with a clear reason.",
            })
            continue

        missing_text = [text for text in required_text if text not in str(content)]
        if missing_text:
            issues.append({
                "file": normalized,
                "issue": "Missing mandatory compliance content",
                "why": _rule_why(rule, "does not include required compliance content."),
                "fix": _rule_fix(rule, missing_text),
            })

    return issues


def _rule_paths(scope, rule, package_files):
    if scope == "file":
        paths = rule.get("paths") or [rule.get("path")]
        return [path for path in paths if path]

    return sorted(package_files)


def _rule_why(rule, default):
    name = rule.get("name", "mandatory compliance rule")
    return f"Internal publishing checks require `{name}`; this file {default}"


def _rule_fix(rule, missing_text):
    name = rule.get("name", "mandatory compliance content")
    content = " ".join(f"`{text}`" for text in missing_text)
    return f"Add the required `{name}` content: {content}"


def _content_for_path(file_map, normalized):
    if normalized in file_map:
        return file_map[normalized]

    for path, content in file_map.items():
        if _normalize_path(path) == normalized:
            return content

    return None


def _has_required_file(required, package_files, file_map):
    normalized_required = _normalize_path(required)
    names = {_normalize_path(path) for path in package_files}
    names.update(_normalize_path(path) for path in file_map)
    return normalized_required in names


def _normalize_path(path):
    return str(path).replace("\\", "/").strip("/")


def _text_rule_exempt(path, rule):
    name = os.path.basename(path)
    _, suffix = os.path.splitext(name.lower())
    excluded_files = set(rule.get("excluded_files", [])) | DEFAULT_TEXT_EXCLUDED_FILES
    excluded_suffixes = set(rule.get("excluded_suffixes", [])) | DEFAULT_TEXT_EXCLUDED_SUFFIXES
    return name in excluded_files or suffix in excluded_suffixes
