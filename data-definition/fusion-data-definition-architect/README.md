## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# Fusion Data Definition Architect

Human-facing overview for the `fusion-data-definition-architect` Codex skill. Codex runtime behavior is defined in `SKILL.md`; this README is for maintainers and users browsing the skill folder.

## Purpose

This skill helps create Oracle Fusion Cloud data definition and migration artifacts:

- Object identification
- Canonical data models
- Source-to-Fusion mappings
- Reference-data standardization
- Data quality and validation rules
- Reconciliation strategy
- Governance guidance
- Live Fusion Applications REST metadata exports when explicitly requested

## Quick Start Prompts

```text
Purchase Orders
Customer Account
Map supplier data from SAP to Fusion SCM
Purchase Orders from my environment
Retrieve Fusion object attributes for Accounts from my environment
```

## Interaction Modes

### Knowledge Mode

Used for generic prompts that do not explicitly ask for the user's Fusion environment.

If the business object is missing, ask only for the business object. Then infer likely source and Fusion target objects and offer exactly these choices:

1. Identify objects from source system for <Business Object>
2. Generate source-to-Fusion mapping for <Business Object>
3. Validate mapping completeness for <Business Object>

### Live FA Mode

Used only when the prompt explicitly asks for live metadata from the user's Fusion Applications environment, such as "from my environment" or "live FA".

Required inputs:

- Fusion Applications URL
- OAuth bearer token
- One or more Fusion REST object names

Bearer tokens are used only in memory for the current run and are not stored.

Default field mode is `standard`. Use `minimal` only for lightweight/essential requests and `full` only for exhaustive/all-fields requests.

## Main Files

| Path | Purpose |
|---|---|
| `SKILL.md` | Runtime skill instructions and trigger metadata |
| `agents/openai.yaml` | UI-facing skill metadata |
| `references/live-fa-metadata.md` | Live metadata retrieval workflow |
| `references/sample-artifacts.md` | Notes for hard-coded example artifact generators |
| `scripts/fusion_object_metadata.py` | Live FA REST metadata retrieval and JSON/Excel export |
| `scripts/guided_intake.py` | Lightweight intake manifest and starter prompt generator |
| `scripts/generate_artifact_bundle.py` | Manifest-driven mapping/validation/reconciliation bundle generator |
| `scripts/object_catalog.py` | Business-object source/target inference catalog |
| `scripts/smoke_validate.py` | Focused smoke validation checks |

## Output Files

All generated files should be written under:

```text
scripts/output/
```

This applies to mapping workbooks, live metadata JSON/Excel exports, guided intake manifests, artifact bundles, and sample artifacts. The folder is intentionally ignored for packaging so generated customer or environment-specific files do not ship with the skill.

## Live Metadata Retrieval

Run interactively:

```bash
python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py
```

Argument-assisted example:

```bash
python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py \
  --base-url 'https://<env-host>/' \
  --objects Accounts \
  --service auto \
  --field-mode standard
```

Generated JSON and Excel files are written under `scripts/output/`.

## Example Artifacts

The sample artifact generators are hard-coded examples, not generic mapping engines:

```bash
python3 fusion-data-definition-architect/scripts/generate_customer_canonical_workbook.py
python3 fusion-data-definition-architect/scripts/generate_migration_strategy_doc.py
```

Use them for demonstrations or workshop scaffolding, then review and adapt the content before treating it as customer-specific output.

## Validation

Run:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/fdda_pycache python3 -m py_compile scripts/*.py
python3 scripts/smoke_validate.py
```

The smoke checks verify:

- `guided_intake.py` does not expose persona input.
- `normalize_field_mode(None)` defaults to `standard`.
- Standard field filtering keeps representative business fields such as `SupplierId`, `CurrencyCode`, and `DocumentTypeCode`.
- Excel metadata exports include a first `Summary` sheet.
- SAP supplier catalog inference resolves `LFA1 -> Supplier`.

## Packaging Notes

The distributable skill should not include generated artifacts or local metadata files. Keep these ignored:

```text
.DS_Store
__pycache__/
*.pyc
scripts/output/
```
