import os

## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

REQUIRED_SECTIONS = [
    "Quick Start",
    "Workflow",
    "Real Example",
    "Sample Output",
    "Prompts"
]

def validate_integrity():
    issues=[]

    if not os.path.exists("README.md"):
        issues.append("Missing README")

    else:
        content=open("README.md").read().lower()
        for s in REQUIRED_SECTIONS:
            if s.lower() not in content:
                issues.append(f"Missing section: {s}")

    return "PASS" if not issues else issues
