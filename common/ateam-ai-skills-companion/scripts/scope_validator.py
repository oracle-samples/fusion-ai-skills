## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

import re


OVERLOAD_ISSUE = "Possible functionality overload"

PRIMARY_DOCS = ("SKILL.md", "README.md", "agents/openai.yaml", "openai.yaml")

APP_FEATURE_TERMS = (
    "web app",
    "frontend",
    "react",
    "next.js",
    "three.js",
    "canvas game",
    "game engine",
    "mobile app",
    "payment",
    "ecommerce",
    "e-commerce",
    "crm",
    "chatbot",
    "api server",
)

CODE_AUDIT_TERMS = (
    "general-purpose code auditor",
    "code auditor",
    "full codebase audit",
    "audit any repository",
    "static analyzer",
    "vulnerability scanner",
)

DOMAIN_TERMS = (
    "finance",
    "legal",
    "healthcare",
    "marketing",
    "sales",
    "hr",
    "database migration",
    "cloud deployment",
    "image generation",
    "video editing",
    "spreadsheet",
    "presentation",
)

CORE_WORKFLOW_TERMS = ("skill", "zip", "package", "submission", "readiness", "review")
SCRIPT_SUPPORT_TERMS = (
    "review",
    "parser",
    "engine",
    "security",
    "validator",
    "validate",
    "zip",
    "prompt",
    "version",
    "compare",
    "naming",
    "fixture",
    "test",
    "integrity",
)


def detect_functionality_overload(ctx, file_map=None):
    file_map = file_map or ctx.get("file_text", {})
    doc_text = _primary_doc_text(file_map)
    script_evidence = _unrelated_scripts(file_map)
    evidence = []

    app_matches = _matches(doc_text, APP_FEATURE_TERMS)
    if len(app_matches) >= 2:
        evidence.append(f"unrelated app/game/web features: {', '.join(app_matches[:4])}")

    audit_matches = _matches(doc_text, CODE_AUDIT_TERMS, skip_negated=True)
    if audit_matches:
        evidence.append(f"broad code-auditing language: {', '.join(audit_matches[:3])}")

    domain_matches = _matches(doc_text, DOMAIN_TERMS)
    if len(domain_matches) >= 3:
        evidence.append(f"multiple unrelated domains: {', '.join(domain_matches[:5])}")

    if _workflow_unclear(ctx, doc_text) and (app_matches or audit_matches or len(domain_matches) >= 2):
        evidence.append("unclear primary user workflow")

    if len(script_evidence) >= 4:
        evidence.append(f"excessive unrelated scripts: {', '.join(script_evidence[:4])}")

    strong_signal = len(script_evidence) >= 4 or (audit_matches and _workflow_unclear(ctx, doc_text))
    if len(evidence) < 2 and not strong_signal:
        return []

    overloaded = "; ".join(evidence)
    return [{
        "file": "SKILL.md",
        "issue": OVERLOAD_ISSUE,
        "why": (
            f"The package appears to mix {overloaded}. This may confuse first-time users because the "
            "main path is harder to distinguish from optional or unrelated capabilities."
        ),
        "fix": (
            "Simplify around the core skill-review workflow: accept a skill ZIP, safely unzip it, analyze "
            "the relevant skill files, and return score, issues, security findings, prompts, and readiness. "
            "Move unrelated app, game, broad code-audit, or domain-specific work into separate skills."
        ),
    }]


def _primary_doc_text(file_map):
    chunks = []
    for name in PRIMARY_DOCS:
        if name in file_map:
            chunks.append(str(file_map[name]))
    return "\n".join(chunks).lower()


def _matches(text, terms, skip_negated=False):
    found = []

    for term in terms:
        pattern = re.escape(term.lower())
        for match in re.finditer(pattern, text):
            if skip_negated and _is_negated(text, match.start()):
                continue
            found.append(term)
            break

    return found


def _is_negated(text, index):
    prefix = text[max(0, index - 48):index]
    return any(phrase in prefix for phrase in ("not ", "not a ", "not an ", "isn't ", "is not "))


def _workflow_unclear(ctx, doc_text):
    workflow_text = " ".join(ctx.get("workflow_steps", [])).lower()
    if not workflow_text:
        return True

    core_hits = sum(1 for term in CORE_WORKFLOW_TERMS if term in workflow_text)
    doc_core_hits = sum(1 for term in CORE_WORKFLOW_TERMS if term in doc_text)
    return core_hits < 2 and doc_core_hits < 4


def _unrelated_scripts(file_map):
    unrelated = []

    for path, content in file_map.items():
        if not path.startswith("scripts/") or not path.endswith(".py"):
            continue

        path_text = path.lower()
        text = f"{path_text}\n{str(content).lower()}"
        if any(term in text for term in SCRIPT_SUPPORT_TERMS):
            continue

        unrelated.append(path)

    return sorted(unrelated)
