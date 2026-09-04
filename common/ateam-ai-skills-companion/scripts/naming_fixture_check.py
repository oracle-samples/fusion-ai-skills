## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import json

from naming_validator import is_valid_skill_name, validate_skill_name


def main():
    cases = [
        {
            "name": "valid",
            "skill_name": "ai-skills-companion",
            "package_name": "ai-skills-companion",
            "valid": True,
        },
        {
            "name": "invalid_characters",
            "skill_name": "Bad_Skill Name",
            "package_name": "Bad_Skill Name",
            "valid": False,
        },
        {
            "name": "package_mismatch",
            "skill_name": "skill-reviewer",
            "package_name": "other-reviewer",
            "valid": False,
        },
    ]

    results = []
    for case in cases:
        issues = validate_skill_name(case["skill_name"], case["package_name"])
        actual_valid = is_valid_skill_name(case["skill_name"], case["package_name"])
        assert actual_valid is case["valid"], f"Unexpected validity for {case['name']}"

        if not case["valid"]:
            assert issues, f"Expected naming issues for {case['name']}"

        results.append({
            "name": case["name"],
            "valid": actual_valid,
            "issues": issues,
        })

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
