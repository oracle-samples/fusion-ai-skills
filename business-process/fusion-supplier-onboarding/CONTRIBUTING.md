## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Contributing

Thank you for improving the Supplier Onboarding skill package. Keep contributions focused on reusable Oracle EBS to Oracle Fusion Supplier Onboarding work.

## Contribution Guidelines

- Preserve the skill layout: root `SKILL.md`, detailed guidance in `references/`, reusable files in `assets/`, and filled samples in `examples/`.
- Keep `SKILL.md` concise and procedural. Put detailed domain content in reference files so Codex can load it only when needed.
- Update `README.md` whenever files are moved, renamed, added, or removed.
- Add or update examples when changing output formats, acceptance criteria, or workstream behavior.
- Keep business-facing deliverables clear about assumptions, owners, unresolved decisions, Oracle setup anchors, risks, dependencies, and evidence requirements.
- Treat bank, tax, supplier master, supplier portal access, and cutover handling as controlled-risk topics.
- Do not add customer confidential data, credentials, personal data, or real supplier banking/tax details.

## Review Checklist

- `SKILL.md` has valid YAML frontmatter with only `name` and `description`.
- Links and file paths in `README.md` resolve.
- Markdown tables render cleanly.
- Workbook changes preserve compatibility and the 13 core template sheets unless intentionally versioned.
- License headers remain consistent with the Universal Permissive License.
