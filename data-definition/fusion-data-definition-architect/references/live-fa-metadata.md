# Live FA Metadata Retrieval

Read this file only when the user explicitly asks to retrieve metadata from their Fusion Applications environment.

## Script

Run:

```bash
python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py
```

Generated files are written to:

```text
fusion-data-definition-architect/scripts/output/
```

## Required Inputs

- Fusion Applications base URL
- OAuth bearer token
- One or many Fusion REST object names

Never store bearer tokens. The script prompts for a token on each live run, can read from the macOS clipboard or an environment variable for the current process, and retries once with a fresh token after `401/403`.

## Field Modes

- `minimal`: business fields only, and only when required or present in the sample row
- `standard`: business and qualifying flexfields; this is the default
- `full`: all fields except relationship fields

Use `standard` unless the user's wording clearly asks for lightweight/essential fields or exhaustive/all fields.

## Behavior

- Validates FA connection before prompting for object names.
- Discovers FA REST resources and suggests corrected object names.
- Retrieves describe metadata from common Fusion/CX REST endpoints.
- Retrieves one sample row from the collection endpoint when available.
- Runs `Raw Fields -> Classification -> Scoring -> Filtering -> Output`.
- Classifies fields into `BUSINESS`, `SYSTEM`, `FLEXFIELD`, `RELATIONSHIP`, `TECHNICAL`, and `UNKNOWN`.
- Separates standard fields and flexfields in Excel outputs.
- Supports optional JSON/YAML filter configs and mapping-template enrichment.
- Writes normalized JSON and Excel workbooks.
- Writes only endpoint paths, not environment hosts, in `Source API`.

## Examples

```bash
python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py \
  --base-url 'https://<env-host>/' \
  --objects Accounts \
  --service auto \
  --field-mode standard
```

```bash
python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py \
  --input-json fusion-data-definition-architect/scripts/output/accounts_live_metadata.json \
  --field-mode minimal \
  --filter-config my_filter_rules.yaml
```

```bash
python3 fusion-data-definition-architect/scripts/fusion_object_metadata.py \
  --base-url 'https://<env-host>/' \
  --objects Accounts Opportunities \
  --token-from-clipboard
```
