## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import json

from engine import calculate_score
from parser import analyze
from security_validator import detect_security_issues


FILE_MARKER = "### " + "FILE:"
REQUIRED_HEADER = "\n".join([
    "## Copyright (c) 2026, Oracle and/or its affiliates.",
    "## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl",
])


STRONG_SKILL = f"""
{FILE_MARKER} SKILL.md
---
name: useful-reviewer
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
2. Extract files when a ZIP package is provided
3. Read README.md, SKILL.md, YAML, and supporting scripts
4. Analyze inputs, outputs, prompts, workflow, examples, and metadata
5. Identify file-level gaps
6. Generate suggestions and readiness output

## Prompts
- "Review this skill"
- "Improve this skill"
- "Validate workflow completeness"
- "Is this ready for submission?"
- "What blocks approval?"
- "Re-review after changes"

{FILE_MARKER} README.md
{REQUIRED_HEADER}
# Useful Reviewer

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

{FILE_MARKER} agents/openai.yaml
{REQUIRED_HEADER}
interface:
  display_name: Useful Reviewer
  short_description: Reviews skill packages

{FILE_MARKER} LICENSE.txt
{REQUIRED_HEADER}
This package is licensed under the Universal Permissive License v 1.0.

{FILE_MARKER} scripts/run_review.py
{REQUIRED_HEADER}
import argparse

def main():
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

{FILE_MARKER} scripts/parser.py
{REQUIRED_HEADER}
def analyze(text):
    return {{}}

{FILE_MARKER} scripts/engine.py
{REQUIRED_HEADER}
def calculate_score(ctx):
    return 100, []
"""


SHALLOW_SKILL = f"""
{FILE_MARKER} SKILL.md
---
name: shallow
description: Reviews things
---
{REQUIRED_HEADER}

## Inputs
- files

## Outputs
- results

## Workflow
- step

## Prompts
- "Review"

{FILE_MARKER} README.md
{REQUIRED_HEADER}
# Shallow

## Quick Start
Start.

## Real Example
Example.

## Sample Output
Output.
"""


MISSING_WORKFLOW_SKILL = f"""
{FILE_MARKER} SKILL.md
---
name: missing-workflow
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

## Prompts
- "Review this skill"
- "Improve this skill"
- "Validate workflow completeness"
- "Is this ready for submission?"

{FILE_MARKER} README.md
{REQUIRED_HEADER}
# Missing Workflow

## Quick Start
"Review this ZIP skill package for submission readiness"

```bash
python3 scripts/run_review.py .
```

Usable in 30 seconds.

## Real Example

### Input
A ZIP skill package.

### Output
Score: 85
Issues:
- [SKILL.md] Missing workflow
Why: Reviews need a sequence.
Fix: Add workflow steps.
Readiness: NOT_READY

## Sample Output
Score: 85
Readiness: NOT_READY

{FILE_MARKER} agents/openai.yaml
{REQUIRED_HEADER}
interface:
  display_name: Missing Workflow
  short_description: Reviews skill packages

{FILE_MARKER} LICENSE.txt
{REQUIRED_HEADER}
This package is licensed under the Universal Permissive License v 1.0.
"""


INVALID_NAME_SKILL = STRONG_SKILL.replace("name: useful-reviewer", "name: Useful_Reviewer")


def score_fixture(name, text, package_name=None):
    ctx = analyze(text)
    if package_name:
        ctx["package_name"] = package_name
    security = detect_security_issues(text)
    score, reasons = calculate_score(ctx, security)
    return {
        "name": name,
        "score": score,
        "reasons": reasons,
    }


def main():
    results = [
        score_fixture("strong", STRONG_SKILL),
        score_fixture("shallow", SHALLOW_SKILL),
        score_fixture("missing_workflow", MISSING_WORKFLOW_SKILL),
        score_fixture("invalid_name", INVALID_NAME_SKILL, "Useful_Reviewer"),
    ]

    by_name = {result["name"]: result for result in results}

    assert by_name["strong"]["score"] >= 90, "strong fixture should score 90+"
    assert by_name["shallow"]["score"] < by_name["strong"]["score"], "shallow fixture should score lower"
    assert by_name["shallow"]["score"] < 80, "shallow fixture should not pass as strong"
    assert by_name["missing_workflow"]["score"] < by_name["strong"]["score"], "missing workflow should be penalized"
    assert by_name["missing_workflow"]["score"] < 90, "missing workflow should fall below readiness threshold"
    assert by_name["invalid_name"]["score"] < by_name["strong"]["score"], "invalid name should reduce the score"
    assert any(
        reason.get("issue") == "Skill name does not follow naming convention"
        for reason in by_name["invalid_name"]["reasons"]
    ), "invalid name should produce a naming reason"

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
