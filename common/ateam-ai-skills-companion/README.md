## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# AI Skills Companion

Upload a skill ZIP, or run:

```bash
python3 scripts/run_review.py path/to/skill.zip
```

Expected result: JSON that tells you `READY` or `NOT_READY`, the score, what blocks approval, and what to fix next.

## If You Are Confused, Start Here

Use this one command:

```bash
python3 scripts/run_review.py path/to/skill.zip
```

Expected result:

```json
{
  "readiness": "NOT_READY",
  "score": 82,
  "issues": [
    {
      "file": "README.md",
      "issue": "Missing Quick Start section",
      "why": "First-time users need to know the first prompt or command to run.",
      "fix": "Add a concise Quick Start with one copyable prompt or CLI command.",
      "priority": "P1",
      "blocking": true
    }
  ]
}
```

Fix the listed issues, then run the same command again.

## What To Provide

Best input:

- A skill `.zip` package.

Also supported:

- A skill package directory: `python3 scripts/run_review.py .`
- A single skill file such as `SKILL.md`.
- Pasted or aggregated text.

## Internal Publishing Compliance

This reviewer also checks internal mandatory content that may block external publishing approval.

Current mandatory rules:

- Required files: `SKILL.md`, `README.md`, and `LICENSE.txt`.
- Required text rules: placeholder only for now.

The specific required header text and required `LICENSE.txt` body are intentionally not hardcoded yet because the approved content may change. Add approved compliance text later in `scripts/mandatory_requirements.json` without rewriting the reviewer.

Example future text rule:

```json
{
  "name": "approved copyright and license header",
  "scope": "all_text_files",
  "required_text": [
    "approved header line 1",
    "approved header line 2"
  ]
}
```

## How To Read The Result

Read the JSON in this order:

1. `readiness`: `READY` or `NOT_READY`.
2. `score`: overall score from 0 to 100.
3. `issues`: sorted file-level problems, with approval blockers first.
4. `suggestions`: top fixes generated from the issues.
5. `security`: secrets, unsafe operations, or suspicious content.
6. `prompts` and `prompt_groups`: supporting prompt suggestions.
7. `score_reasons`: detailed scoring breakdown for deeper review.

Generated prompts are supporting guidance. The main product is the ZIP package readiness review.

## Workflow

1. Accept a skill ZIP.
2. Safely unzip it and reject unsafe archives.
3. Inspect relevant files such as `SKILL.md`, `README.md`, `agents/openai.yaml`, Markdown, YAML, text, and Python scripts.
4. Analyze package readiness, documentation, prompts, workflow, metadata, naming, scripts, and security signals.
5. Return readiness, score, blocking issues, fixes, security findings, prompt suggestions, and detailed score reasons.

## Output Fields

The full JSON response can include:

- `summary`: short review summary.
- `score`: numeric readiness score from 0 to 100.
- `issues`: file-level issues with `file`, `issue`, `why`, `fix`, `priority`, and `blocking`.
- `suggestions`: deduplicated fixes.
- `security`: security findings with file-aware details when available.
- `score_reasons`: weighted scoring details by category.
- `prompt_groups`: curated prompts grouped by intent.
- `prompts`: flat prompt list.
- `readiness`: `READY` or `NOT_READY`.

Security findings may include `file`, `line`, `type`, `severity`, `value`, `why`, and `fix`. Sensitive values are redacted.

Issue priorities are:

- `P0`: external publishing blocker.
- `P1`: high-impact readiness issue.
- `P2`: medium improvement.
- `P3`: advisory / non-blocking guidance.

## Real Example

This sample uses the current schema for a package that needs fixes:

```json
{
  "summary": "Skill reviewed with file-level diagnostics",
  "score": 82,
  "issues": [
    {
      "file": "README.md",
      "issue": "Missing Quick Start section",
      "why": "First-time users need to know the first prompt or command to run.",
      "fix": "Add a concise Quick Start with one copyable prompt or CLI command.",
      "priority": "P1",
      "blocking": true
    },
    {
      "file": "SKILL.md",
      "issue": "Workflow is incomplete",
      "why": "A clear workflow helps Codex produce consistent reviews instead of ad hoc feedback.",
      "fix": "Document a step-by-step workflow from input detection through extraction, analysis, issue mapping, suggestions, and readiness output.",
      "priority": "P1",
      "blocking": true
    }
  ],
  "suggestions": [
    "[README.md] Add a concise Quick Start with one copyable prompt or CLI command.",
    "[SKILL.md] Document a step-by-step workflow from input detection through extraction, analysis, issue mapping, suggestions, and readiness output."
  ],
  "security": [],
  "score_reasons": [
    {
      "category": "workflow",
      "points": 5,
      "max_points": 15,
      "status": "warning",
      "detail": "Workflow scoring checks step count and whether the procedure covers intake, analysis, and output.",
      "file": "SKILL.md",
      "issue": "Workflow is incomplete",
      "why": "A clear workflow helps Codex produce consistent reviews instead of ad hoc feedback.",
      "fix": "Document a step-by-step workflow from input detection through extraction, analysis, issue mapping, suggestions, and readiness output."
    }
  ],
  "prompt_groups": {
    "Review": [
      "Review this skill",
      "Review this ZIP skill package for submission readiness"
    ],
    "Improve": [
      "Improve this skill",
      "What are the top 3 improvements?"
    ],
    "Packaging/submission": [
      "Is this ready for submission?",
      "What blocks approval?"
    ]
  },
  "prompts": [
    "Review this skill",
    "Review this ZIP skill package for submission readiness",
    "Improve this skill",
    "What are the top 3 improvements?",
    "Is this ready for submission?",
    "What blocks approval?"
  ],
  "readiness": "NOT_READY"
}
```

## What This Skill Does Not Do

- It is not a general-purpose code auditor.
- It is not a broad app reviewer.
- It focuses on AI skill package readiness.

If a package appears overloaded, the review should explain which parts are outside the core ZIP skill-review mission and suggest simplifying or splitting them. Functionality overload is advisory; it should not make an otherwise strong package `NOT_READY` by itself.

## Advanced Maintenance

These checks are useful after normal review, but they are not the first-time path:

```bash
python3 scripts/merge_validator.py .
python3 scripts/version_compare.py .
python3 -m unittest
```

- `merge_validator.py` checks required files, placeholders, importability, and naming.
- `version_compare.py` compares package files with `baseline_hashes.json`.
- `python3 -m unittest` runs fixture coverage for scoring, security, naming, ZIP safety, and scope overload.

## Ready Criteria

A package is `READY` when it scores at least 90 and has no blocking issues. Strong packages usually have a clear Quick Start, concrete inputs and outputs, useful prompts, complete workflow, realistic examples, valid naming, clean security findings, and reliable supporting scripts.
