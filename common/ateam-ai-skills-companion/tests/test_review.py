## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import os
import sys
import tempfile
import unittest
import zipfile


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import run_review as run_review_module
from parser import analyze
from issue_utils import PRIORITY_ORDER
from mandatory_validator import validate_mandatory_content
from run_review import run_from_text, run_from_zip
from scope_validator import OVERLOAD_ISSUE
from scoring_fixture_check import (
    INVALID_NAME_SKILL,
    MISSING_WORKFLOW_SKILL,
    SHALLOW_SKILL,
    STRONG_SKILL,
    score_fixture,
)
from security_fixture_check import _benign_fixture, _secret_fixture
from security_validator import detect_security_issues


REQUIRED_HEADER = "\n".join([
    "## Copyright (c) 2026, Oracle and/or its affiliates.",
    "## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl",
])


OVERLOADED_SKILL = (
    STRONG_SKILL
    .replace(
        "Reviews complete skill packages for readiness and actionable improvements",
        (
            "Reviews skill ZIPs, builds a React web app, runs game engine checks, "
            "handles finance, legal, healthcare, payment, and CRM workflows, and "
            "performs a full codebase audit"
        ),
        1,
    )
    .replace(
        "Detect the input type",
        "Detect whether users want ZIP review, React web app generation, game engine setup, finance analysis, legal review, healthcare triage, payment workflows, CRM automation, or full codebase audit",
        1,
    )
    + f"""
### FILE: scripts/web_app.py
{REQUIRED_HEADER}
def build_frontend():
    return "react app"

### FILE: scripts/game_builder.py
{REQUIRED_HEADER}
def build_game():
    return "game engine"

### FILE: scripts/payment_sync.py
{REQUIRED_HEADER}
def sync_payments():
    return "payment workflow"

### FILE: scripts/crm_automation.py
{REQUIRED_HEADER}
def automate_crm():
    return "crm workflow"
"""
)


class ScoringFixtureTests(unittest.TestCase):
    def test_strong_skill_scores_ready_range(self):
        result = score_fixture("strong", STRONG_SKILL)
        self.assertGreaterEqual(result["score"], 90)

    def test_shallow_skill_scores_lower(self):
        strong = score_fixture("strong", STRONG_SKILL)
        shallow = score_fixture("shallow", SHALLOW_SKILL)

        self.assertLess(shallow["score"], strong["score"])
        self.assertLess(shallow["score"], 80)

    def test_missing_workflow_is_penalized(self):
        strong = score_fixture("strong", STRONG_SKILL)
        missing = score_fixture("missing_workflow", MISSING_WORKFLOW_SKILL)
        issues = {reason.get("issue") for reason in missing["reasons"]}

        self.assertLess(missing["score"], strong["score"])
        self.assertLess(missing["score"], 90)
        self.assertIn("Workflow is incomplete", issues)

    def test_invalid_naming_convention_is_reported_as_issue(self):
        file_map = analyze(INVALID_NAME_SKILL)["file_text"]
        result = run_from_text(INVALID_NAME_SKILL, file_map, "Useful_Reviewer")
        issues = {issue["issue"] for issue in result["issues"]}

        self.assertIn("Skill name does not follow naming convention", issues)
        naming_issue = _first_issue(result, "Skill name does not follow naming convention")
        self.assertEqual("P0", naming_issue["priority"])
        self.assertTrue(naming_issue["blocking"])
        self.assertEqual(result["readiness"], "NOT_READY")


class ScopeFixtureTests(unittest.TestCase):
    def test_overloaded_skill_gets_nonblocking_suggestion(self):
        file_map = analyze(OVERLOADED_SKILL)["file_text"]
        result = run_from_text(OVERLOADED_SKILL, file_map, "useful-reviewer")
        issues = {issue["issue"] for issue in result["issues"]}
        overload = _first_issue(result, OVERLOAD_ISSUE)

        self.assertIn(OVERLOAD_ISSUE, issues)
        self.assertEqual("P3", overload["priority"])
        self.assertFalse(overload["blocking"])
        self.assertEqual(result["readiness"], "READY")
        self.assertTrue(any(
            "Simplify around the core skill-review workflow" in suggestion
            for suggestion in result["suggestions"]
        ))

    def test_focused_zip_review_skill_has_no_overload_issue(self):
        file_map = analyze(STRONG_SKILL)["file_text"]
        result = run_from_text(STRONG_SKILL, file_map, "useful-reviewer")
        issues = {issue["issue"] for issue in result["issues"]}

        self.assertNotIn(OVERLOAD_ISSUE, issues)
        self.assertEqual(result["readiness"], "READY")


class MandatoryContentTests(unittest.TestCase):
    def test_valid_fixture_with_required_files_passes_placeholder_rules(self):
        text, file_map = _aggregate_files(_valid_skill_files("zip-reviewer"))
        result = run_from_text(text, file_map, "zip-reviewer", file_map, list(file_map))
        issues = {issue["issue"] for issue in result["issues"]}

        self.assertNotIn("Missing mandatory publishing file", issues)
        self.assertNotIn("Missing mandatory compliance content", issues)
        self.assertEqual(result["readiness"], "READY")

    def test_default_placeholder_rules_do_not_enforce_header_text(self):
        files = _valid_skill_files("zip-reviewer")
        files["scripts/parser.py"] = files["scripts/parser.py"].replace(REQUIRED_HEADER + "\n", "")
        issues = validate_mandatory_content(files, list(files))

        self.assertFalse(any(
            issue["issue"] == "Missing mandatory compliance content"
            for issue in issues
        ))

    def test_missing_license_is_blocking(self):
        files = _valid_skill_files("zip-reviewer")
        files.pop("LICENSE.txt")
        text, file_map = _aggregate_files(files)
        result = run_from_text(text, file_map, "zip-reviewer", file_map, list(file_map))
        issues = {issue["issue"] for issue in result["issues"]}

        self.assertIn("Missing mandatory publishing file", issues)
        missing = _first_issue(result, "Missing mandatory publishing file")
        self.assertEqual("P0", missing["priority"])
        self.assertTrue(missing["blocking"])
        self.assertEqual(result["readiness"], "NOT_READY")

    def test_missing_header_is_file_specific(self):
        files = _valid_skill_files("zip-reviewer")
        files["scripts/parser.py"] = files["scripts/parser.py"].replace(REQUIRED_HEADER + "\n", "")
        text, file_map = _aggregate_files(files)
        result = run_from_text(
            text,
            file_map,
            "zip-reviewer",
            file_map,
            list(file_map),
            _header_requirements(),
        )
        matching = [
            issue for issue in result["issues"]
            if issue["issue"] == "Missing mandatory compliance content"
        ]

        self.assertEqual("scripts/parser.py", matching[0]["file"])
        self.assertEqual("P0", matching[0]["priority"])
        self.assertTrue(matching[0]["blocking"])
        self.assertEqual(result["readiness"], "NOT_READY")

    def test_configured_license_content_rule_is_enforced(self):
        files = _valid_skill_files("zip-reviewer")
        files["LICENSE.txt"] = REQUIRED_HEADER + "\nTemporary license placeholder.\n"
        issues = validate_mandatory_content(files, list(files), _license_requirements())
        matching = [
            issue for issue in issues
            if issue["issue"] == "Missing mandatory compliance content"
        ]

        self.assertEqual("LICENSE.txt", matching[0]["file"])

    def test_mandatory_content_is_checked_inside_zip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "missing-header.zip")
            package_name = "zip-reviewer"
            files = _valid_skill_files(package_name)
            files["README.md"] = files["README.md"].replace(REQUIRED_HEADER + "\n", "")

            with zipfile.ZipFile(zip_path, "w") as zip_ref:
                for rel_path, content in files.items():
                    zip_ref.writestr(f"{package_name}/{rel_path}", content)

            result = run_from_zip(zip_path, _header_requirements())

        issues = {issue["issue"] for issue in result["issues"]}
        self.assertIn("Missing mandatory compliance content", issues)
        self.assertEqual(result["readiness"], "NOT_READY")


class SecurityFixtureTests(unittest.TestCase):
    def test_secret_security_issue_is_detected_and_redacted(self):
        full_token = "sk-" + ("A" * 32)
        findings = detect_security_issues("", _secret_fixture())
        finding_types = {finding["type"] for finding in findings}
        values = [finding["value"] for finding in findings]

        self.assertIn("generic_secret_assignment", finding_types)
        self.assertIn("openai_api_key", finding_types)
        self.assertTrue(all(full_token not in value for value in values))
        self.assertTrue(any("..." in value for value in values))

    def test_benign_package_has_no_security_findings(self):
        self.assertEqual([], detect_security_issues("", _benign_fixture()))

    def test_changelog_dates_are_not_phone_findings(self):
        findings = detect_security_issues("", {
            "CHANGELOG.md": "\n".join([
                "## 1.2 - 2026-05-02",
                "## 1.1 - 2026-05-02",
                "## 1.0 - 2026-04-06",
            ])
        })

        self.assertFalse(any(finding["type"] == "phone" for finding in findings))

    def test_portable_usr_bin_env_path_is_not_local_path(self):
        findings = detect_security_issues("", {
            "scripts/tool.py": "#!/usr/bin/env python3\nprint('ok')\n",
            "scripts/run.sh": "#!/usr/bin/env bash\necho ok\n",
            "README.md": "Use /usr/bin/env for portable executable examples.",
        })

        self.assertFalse(any(
            finding["type"] == "absolute_local_path"
            for finding in findings
        ))

    def test_service_paths_archive_parts_and_labels_are_not_local_paths(self):
        findings = detect_security_issues("", {
            "README.md": "\n".join([
                "Call /api/boss/data/objects/ora/commonBoss/dataExport/v1/exportDefinitions.",
                "Inspect /fscmRestApi/resources/latest/Suppliers/describe.",
                "Write archive member /xl/workbook.xml and /docProps/core.xml.",
                "Route to / Treasury / Compliance or / Add / Remove.",
            ])
        })

        self.assertFalse(any(
            finding["type"] == "absolute_local_path"
            for finding in findings
        ))

    def test_local_absolute_paths_are_detected(self):
        users_path = "/" + "Users/example/project/output.json"
        mnt_path = "/" + "mnt/data/generated.csv"
        findings = detect_security_issues("", {
            "README.md": "\n".join([
                f"Do not write output to {users_path}.",
                f"Do not rely on {mnt_path}.",
            ])
        })

        self.assertTrue(any(
            finding["type"] == "absolute_local_path"
            for finding in findings
        ))

    def test_runtime_password_references_are_not_secret_findings(self):
        findings = detect_security_issues("", {
            "scripts/tool.py": "\n".join([
                "args = parse_args()",
                "password = args.workbench_password or getpass('Password: ')",
                "token = os.getenv('API_TOKEN')",
            ])
        })

        self.assertFalse(any(
            finding["type"] == "generic_secret_assignment"
            for finding in findings
        ))


class ZipReviewTests(unittest.TestCase):
    def test_unsafe_zip_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "unsafe.zip")
            with zipfile.ZipFile(zip_path, "w") as zip_ref:
                zip_ref.writestr("../SKILL.md", "unsafe")

            with self.assertRaises(ValueError):
                run_from_zip(zip_path)

    def test_valid_zip_package_is_extracted_and_reviewed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "valid.zip")
            package_name = "zip-reviewer"
            files = _valid_skill_files(package_name)

            with zipfile.ZipFile(zip_path, "w") as zip_ref:
                for rel_path, content in files.items():
                    zip_ref.writestr(f"{package_name}/{rel_path}", content)

            result = run_from_zip(zip_path)

        self.assertGreaterEqual(result["score"], 90)
        self.assertEqual(result["readiness"], "READY")
        self.assertEqual([], result["issues"])
        self.assertEqual([], result["security"])
        self.assertTrue(result["prompts"])
        self.assertIn("score_reasons", result)

    def test_valid_root_zip_package_is_reviewed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "valid-root.zip")
            files = _valid_skill_files("zip-reviewer")

            with zipfile.ZipFile(zip_path, "w") as zip_ref:
                for rel_path, content in files.items():
                    zip_ref.writestr(rel_path, content)

            result = run_from_zip(zip_path)

        self.assertGreaterEqual(result["score"], 90)
        self.assertEqual("READY", result["readiness"])
        self.assertEqual([], result["issues"])

    def test_nested_required_files_do_not_satisfy_package_root_requirements(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "nested-docs.zip")
            package_name = "zip-reviewer"
            files = _valid_skill_files(package_name)

            with zipfile.ZipFile(zip_path, "w") as zip_ref:
                for rel_path, content in files.items():
                    target = f"docs/{rel_path}" if rel_path in {"SKILL.md", "README.md"} else rel_path
                    zip_ref.writestr(f"{package_name}/{target}", content)

            result = run_from_zip(zip_path)

        missing = [
            issue for issue in result["issues"]
            if issue["issue"] == "Missing mandatory publishing file"
        ]
        missing_files = {issue["file"] for issue in missing}

        self.assertEqual("NOT_READY", result["readiness"])
        self.assertIn("SKILL.md", missing_files)
        self.assertIn("README.md", missing_files)
        self.assertTrue(all(issue["priority"] == "P0" for issue in missing))
        self.assertTrue(all(issue["blocking"] for issue in missing))

    def test_zip_extraction_temp_directory_is_removed_after_review(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "cleanup.zip")
            package_name = "zip-reviewer"
            files = _valid_skill_files(package_name)

            with zipfile.ZipFile(zip_path, "w") as zip_ref:
                for rel_path, content in files.items():
                    zip_ref.writestr(f"{package_name}/{rel_path}", content)

            original_extract = run_review_module.extract_zip
            extracted_folders = []

            def recording_extract(path, extract_to=None):
                extracted_folders.append(extract_to)
                return original_extract(path, extract_to)

            run_review_module.extract_zip = recording_extract
            try:
                result = run_review_module.run_from_zip(zip_path)
            finally:
                run_review_module.extract_zip = original_extract

        self.assertEqual("READY", result["readiness"])
        self.assertTrue(extracted_folders)
        self.assertFalse(os.path.exists(extracted_folders[0]))


class IssuePriorityTests(unittest.TestCase):
    def test_all_issues_include_priority_and_blocking_metadata(self):
        files = _valid_skill_files("zip-reviewer")
        files.pop("LICENSE.txt")
        text, file_map = _aggregate_files(files)
        result = run_from_text(text, file_map, "zip-reviewer", file_map, list(file_map))

        self.assertTrue(result["issues"])
        for issue in result["issues"]:
            self.assertIn(issue["priority"], PRIORITY_ORDER)
            self.assertIsInstance(issue["blocking"], bool)

    def test_issues_are_sorted_with_blockers_first(self):
        files = _valid_skill_files("zip-reviewer")
        files.pop("LICENSE.txt")
        files["scripts/parser.py"] = files["scripts/parser.py"].replace(REQUIRED_HEADER + "\n", "")
        text, file_map = _aggregate_files(files)
        result = run_from_text(text, file_map, "zip-reviewer", file_map, list(file_map))
        ranks = [_issue_rank(issue) for issue in result["issues"]]

        self.assertEqual(sorted(ranks), ranks)
        self.assertTrue(result["issues"][0]["blocking"])
        self.assertEqual("P0", result["issues"][0]["priority"])

    def test_suggestions_follow_issue_order(self):
        files = _valid_skill_files("zip-reviewer")
        files.pop("LICENSE.txt")
        files["scripts/parser.py"] = files["scripts/parser.py"].replace(REQUIRED_HEADER + "\n", "")
        text, file_map = _aggregate_files(files)
        result = run_from_text(text, file_map, "zip-reviewer", file_map, list(file_map))
        expected = []
        seen = set()

        for issue in result["issues"]:
            suggestion = f"[{issue['file']}] {issue['fix']}"
            if suggestion not in seen:
                seen.add(suggestion)
                expected.append(suggestion)

        self.assertEqual(expected, result["suggestions"])

    def test_ready_is_preserved_when_only_advisory_issues_exist(self):
        file_map = analyze(OVERLOADED_SKILL)["file_text"]
        result = run_from_text(OVERLOADED_SKILL, file_map, "useful-reviewer")

        self.assertEqual(result["readiness"], "READY")
        self.assertTrue(result["issues"])
        self.assertTrue(all(not issue["blocking"] for issue in result["issues"]))


def _valid_skill_files(skill_name):
    return {
        "SKILL.md": f"""---
name: {skill_name}
description: Reviews complete skill packages for readiness and actionable improvements
---
{REQUIRED_HEADER}

## Inputs
- ZIP skill package
- Text-based skill definition
- Individual files such as README.md, SKILL.md, YAML, and Python scripts

## Outputs
- Summary
- Score (0-100)
- File-level issues with why and fix guidance
- Security findings
- Generated prompts
- Readiness (READY / NOT_READY)

## Workflow
1. Detect the input type
2. Safely extract files when a ZIP package is provided
3. Read README.md, SKILL.md, YAML, and supporting scripts
4. Analyze inputs, outputs, prompts, workflow, examples, and metadata
5. Identify file-level gaps
6. Generate suggestions, prompts, security findings, and readiness output

## Prompts
- "Review this skill"
- "Improve this skill"
- "Validate workflow completeness"
- "Is this ready for submission?"
- "What blocks approval?"
- "Re-review after changes"
""",
        "README.md": f"""{REQUIRED_HEADER}
# ZIP Reviewer

## Quick Start

Copy and run:
"Review this ZIP skill package for submission readiness"

```bash
python3 scripts/run_review.py .
```

Usable in 30 seconds.

## Workflow
Upload, review, fix, re-review, and submit.

## Real Example

### Input
A ZIP skill package with README.md and SKILL.md.

### Output
Score: 95
Issues:
- [README.md] Missing Quick Start
Why: Users need a first step.
Fix: Add a copyable prompt.
Suggestions:
- Improve prompt clarity
Readiness: READY

## Sample Output
Score: 95
Readiness: READY
""",
        "agents/openai.yaml": f"""{REQUIRED_HEADER}
interface:
  display_name: ZIP Reviewer
  short_description: Reviews skill packages
""",
        "LICENSE.txt": f"""{REQUIRED_HEADER}
This package is licensed under the Universal Permissive License v 1.0.
""",
        "scripts/run_review.py": f"""{REQUIRED_HEADER}
import argparse


def main():
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
        "scripts/parser.py": f"""{REQUIRED_HEADER}
def analyze(text):
    return {{}}
""",
        "scripts/engine.py": f"""{REQUIRED_HEADER}
def calculate_score(ctx):
    return 100, []
""",
    }


def _aggregate_files(files):
    text = ""
    for path, content in files.items():
        text += f"\n\n### FILE: {path}\n{content}"
    return text, dict(files)


def _header_requirements():
    return {
        "required_files": ["SKILL.md", "README.md", "LICENSE.txt"],
        "required_text_rules": [
            {
                "name": "test copyright and license header",
                "scope": "all_text_files",
                "required_text": REQUIRED_HEADER.splitlines(),
            },
        ],
    }


def _license_requirements():
    return {
        "required_files": ["SKILL.md", "README.md", "LICENSE.txt"],
        "required_text_rules": [
            {
                "name": "approved license text",
                "scope": "file",
                "path": "LICENSE.txt",
                "required_text": ["This package is licensed under the Universal Permissive License v 1.0."],
            },
        ],
    }


def _first_issue(result, issue_text):
    for issue in result["issues"]:
        if issue["issue"] == issue_text:
            return issue
    raise AssertionError(f"Expected issue not found: {issue_text}")


def _issue_rank(issue):
    return (
        0 if issue["blocking"] else 1,
        PRIORITY_ORDER[issue["priority"]],
        issue["file"],
        issue["issue"],
    )
