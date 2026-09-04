---
name: ai-skills-companion
description: Reviews Codex skill ZIP packages for safe extraction, file analysis, score, issues, security findings, fixes, prompts, and readiness.
---
## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# AI Skills Companion

Upload a skill ZIP, or run:

```bash
python3 scripts/run_review.py path/to/skill.zip
```

Expected result: JSON that tells the user `READY` or `NOT_READY`, the score, what blocks approval, and what to fix next.

## If You Are Confused, Start Here

Use this one command:

```bash
python3 scripts/run_review.py path/to/skill.zip
```

Expected result: a JSON review with `readiness`, `score`, `issues`, `suggestions`, `security`, `prompts`, and `score_reasons`.

Fix the listed issues, then run the same command again.

## Inputs

- Skill ZIP package.
- Skill package directory, using `python3 scripts/run_review.py .`.
- Single skill file such as `SKILL.md` or `README.md`.
- Pasted text or aggregated file text with markers such as `### FILE: SKILL.md`.

## Internal Publishing Compliance

Check mandatory content that may block external publishing approval:

- Required files: `SKILL.md`, `README.md`, and `LICENSE.txt`.
- Required text rules are a placeholder for now.

The exact required header text and required `LICENSE.txt` body may change, so do not hardcode final compliance wording in the validator. Add approved content later in `scripts/mandatory_requirements.json` by adding `required_text_rules` entries for all text files, `LICENSE.txt`, or another specific file.

## Outputs

Return JSON. Explain the result in this order:

1. `readiness`: `READY` or `NOT_READY`.
2. `score`: overall score from 0 to 100.
3. `issues`: sorted file-level problems, with approval blockers first.
4. `suggestions`: top fixes generated from the issues.
5. `security`: secrets, unsafe operations, or suspicious content.
6. `prompts` and `prompt_groups`: supporting prompt suggestions.
7. `score_reasons`: detailed scoring breakdown for deeper review.

The JSON can include these top-level fields:

- `summary`
- `score`
- `issues`
- `suggestions`
- `security`
- `score_reasons`
- `prompt_groups`
- `prompts`
- `readiness`

Every issue must include `file`, `issue`, `why`, `fix`, `priority`, and `blocking`. Priority values are `P0` for external publishing blockers, `P1` for high-impact readiness issues, `P2` for medium improvements, and `P3` for advisory non-blocking guidance. Sort blocking issues before advisory issues. Security findings may include `file`, `line`, `type`, `severity`, `value`, `why`, and `fix`; redact secret-like values.

## Workflow

1. Detect whether the input is a ZIP, directory, file, or raw text.
2. For ZIP input, safely extract the archive and reject path traversal, absolute paths, excessive file counts, oversized files, symlinks, or packages that escape the extraction root.
3. Read relevant files such as `SKILL.md`, `README.md`, `agents/openai.yaml`, Markdown, YAML, text files, and Python scripts.
4. Analyze metadata, skill naming, inputs, outputs, prompts, workflow, Quick Start, examples, supporting scripts, and security findings.
5. Return readiness, score, blocking issues, top fixes, security findings, prompt suggestions, and detailed score reasons.

## CLI Usage

Review a packaged skill ZIP:

```bash
python3 scripts/run_review.py path/to/skill.zip
```

Review the current package directory:

```bash
python3 scripts/run_review.py .
```

The CLI emits JSON by default.

## Prompts (Primary Interface)

Use prompts when the user is not running the CLI:

- "Review this skill"
- "Review this ZIP skill package for submission readiness"
- "Improve this skill"
- "Is this ready for submission?"
- "What blocks approval?"
- "Re-review after changes"

Generated prompts are supporting guidance, not the main product. The main product is the skill ZIP readiness review.

## Real Example

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
    }
  ],
  "suggestions": [
    "[README.md] Add a concise Quick Start with one copyable prompt or CLI command."
  ],
  "security": [],
  "score_reasons": [
    {
      "category": "quick_start",
      "points": 0,
      "max_points": 10,
      "status": "fail",
      "detail": "Quick Start scoring checks for a visible heading, copyable invocation, and fast onboarding language.",
      "file": "README.md",
      "issue": "Quick Start is not clear enough",
      "why": "A first-time user should know what to run within seconds.",
      "fix": "Add a Quick Start with one copyable prompt or CLI command and a short expected result."
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
    ]
  },
  "prompts": [
    "Review this skill",
    "Review this ZIP skill package for submission readiness",
    "Improve this skill",
    "What are the top 3 improvements?"
  ],
  "readiness": "NOT_READY"
}
```

## What This Skill Does Not Do

- It is not a general-purpose code auditor.
- It is not a broad app reviewer.
- It focuses on AI skill package readiness.

If functionality appears overloaded, tell the developer which parts are outside the core ZIP skill-review mission and suggest simplifying, splitting, or documenting those responsibilities. Treat functionality overload as advisory; do not make an otherwise strong package `NOT_READY` only because it is broad.

## Advanced Maintenance

Move these concepts below the first-time workflow. Use them only when validating the package itself:

- `baseline_hashes.json` and `scripts/version_compare.py` track package file hashes.
- `scripts/merge_validator.py` checks required files, placeholders, importability, and naming.
- Fixture checks and `python3 -m unittest` cover scoring, security, naming, ZIP safety, and scope overload.

## Success Criteria

A skill is `READY` when:

- Score is at least 90.
- No blocking issues remain.
- The package has clear inputs, outputs, prompts, workflow, Quick Start, realistic examples, valid naming, and clean security findings.
