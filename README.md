# Fusion AI Skills

This repository contains reusable Oracle Fusion AI agent skills. Skills package domain-specific instructions, reference material, examples, assets, and optional automation to help architects and delivery teams design and implement Oracle Fusion solutions consistently.

The collection covers business processes, data definition and integration, extensibility, release adoption, reporting, security, and integration architecture. Each skill is self-contained and documented in its own directory.

## Installation

Clone the repository and select the skill that matches your use case:

```bash
git clone https://github.com/oracle-samples/fusion-ai-skills.git
cd fusion-ai-skills
```

Open the selected skill directory and follow its `README.md` and `SKILL.md` instructions. Most skills include the core instructions in `SKILL.md`, with supporting references, examples, and scripts in adjacent folders. Requirements for optional scripts and tooling are documented by the individual skill.

## Documentation

Developer-oriented documentation is maintained in this repository:

- The [repository structure](#repository-structure) describes the skill domains.
- Each skill package contains its own `README.md` and `SKILL.md`.
- Supporting implementation material is available in each package's `references/`, `examples/`, `assets/`, and `scripts/` directories where applicable.

Oracle product documentation is published at [docs.oracle.com](https://docs.oracle.com).

## Examples

Many skill packages include examples that show expected inputs and outputs, along with reusable templates and helper scripts. For example, the `business-process/`, `data-integration/`, and `integration/` domains contain skills for supplier onboarding, data extraction and mapping, schema-drift analysis, and Fusion integration design.

Refer to the `examples/` directory and package-level README for a specific skill.

## Help

For questions about a skill, open an issue in this repository with the skill name, your intended use case, and any relevant non-sensitive error details. For Oracle product support, use your organization's standard Oracle Support channels.

## Contributing

This project welcomes contributions from the community. Before submitting a pull request, please [review our contribution guide](https://github.com/oracle-samples/fusion-ai-skills/blob/main/CONTRIBUTING.md). If a skill has additional contribution requirements, its package-level documentation identifies them.

## Distribution

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Security

Please consult the [security guide](https://github.com/oracle-samples/fusion-ai-skills/blob/main/SECURITY.md) for the responsible security vulnerability disclosure process. Do not report security vulnerabilities through public issues.

## Repository structure

```text
fusion-ai-skills/
├── business-process/       # Process-centric skills
├── common/                 # Shared skills and utilities
├── data-definition/        # Fusion metadata and data-definition skills
├── data-integration/       # Extraction, mapping, pipeline, and drift skills
├── extensibility/          # Fusion extensibility skills
├── integration/            # Integration architecture and design skills
├── release-management/     # Release-adoption skills
├── reporting/              # Reporting and SQL optimization skills
└── security/               # Security-focused skills
```

Most skill packages follow this layout:

- `SKILL.md` — core instructions.
- `README.md` — package overview and usage notes.
- `references/` — source and domain material.
- `examples/` — sample inputs and outputs.
- `assets/` and `scripts/` — reusable assets and optional automation.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at [https://oss.oracle.com/licenses/upl/](https://oss.oracle.com/licenses/upl/).
