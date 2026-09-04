## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import argparse
import importlib.util
import json
import os
import sys

from issue_utils import enrich_issues, sort_issues
from mandatory_validator import validate_mandatory_content
from naming_validator import extract_skill_name, validate_skill_name


REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "LICENSE.txt",
    "agents/openai.yaml",
    "scripts/engine.py",
    "scripts/issue_utils.py",
    "scripts/mandatory_requirements.json",
    "scripts/mandatory_validator.py",
    "scripts/naming_validator.py",
    "scripts/parser.py",
    "scripts/prompt_gen.py",
    "scripts/run_review.py",
    "scripts/scope_validator.py",
    "scripts/security_validator.py",
    "scripts/zip_loader.py",
    "scripts/version_compare.py",
    "tests/test_review.py",
]

PLACEHOLDER_MARKERS = [
    "PASTE" + "_FULL_",
]


def _package_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            dirname for dirname in dirnames
            if dirname not in {"__pycache__", ".git"} and not dirname.startswith(".")
        ]

        for filename in filenames:
            if filename == ".DS_Store" or filename.endswith(".pyc"):
                continue
            yield os.path.relpath(os.path.join(dirpath, filename), root).replace(os.sep, "/")


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        return ""
    except OSError:
        return ""


def _check_importable(root, rel_path):
    module_name = os.path.splitext(rel_path.replace("/", "_"))[0]
    path = os.path.join(root, rel_path)
    scripts_dir = os.path.join(root, "scripts")

    inserted = False
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
        inserted = True

    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if inserted:
            try:
                sys.path.remove(scripts_dir)
            except ValueError:
                pass


def validate_package(root="."):
    root = os.path.abspath(root)
    issues = []
    files = sorted(_package_files(root))
    file_set = set(files)

    for required in REQUIRED_FILES:
        if required not in file_set:
            issues.append({
                "file": required,
                "issue": "Missing required package file",
                "why": "Submission packages need the expected files so review, packaging, and runtime checks are repeatable.",
                "fix": f"Create or restore {required}.",
            })

    if "SKILL.md" in file_set:
        skill_text = _read_text(os.path.join(root, "SKILL.md"))
        folder_name = os.path.basename(root)
        issues.extend(validate_skill_name(extract_skill_name(skill_text), folder_name))

    text_files = {
        rel_path: _read_text(os.path.join(root, rel_path))
        for rel_path in files
    }
    issues.extend(validate_mandatory_content(text_files, files))

    for rel_path in files:
        content = text_files.get(rel_path, "")
        for marker in PLACEHOLDER_MARKERS:
            if marker in content:
                issues.append({
                    "file": rel_path,
                    "issue": f"Placeholder marker found: {marker}",
                    "why": "Placeholder content means the package still contains unfinished implementation.",
                    "fix": "Replace placeholder content with a working implementation.",
                })

    for rel_path in files:
        if not rel_path.startswith("scripts/") or not rel_path.endswith(".py"):
            continue

        try:
            _check_importable(root, rel_path)
        except Exception as exc:
            issues.append({
                "file": rel_path,
                "issue": f"Python script is not importable: {exc}",
                "why": "Importable scripts are easier to validate and less likely to fail during review or packaging.",
                "fix": "Fix syntax errors, import errors, or top-level side effects.",
            })

    issues = sort_issues(enrich_issues(issues))

    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "checked_files": files,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the merged skill package.")
    parser.add_argument("root", nargs="?", default=".", help="Skill package root.")
    args = parser.parse_args(argv)

    print(json.dumps(validate_package(args.root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
