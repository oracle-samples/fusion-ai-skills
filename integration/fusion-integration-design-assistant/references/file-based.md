# File-Based and Batch Integration References

Use this file when requirements mention files, CSV/XML payload drops, SFTP, object storage, scheduled batch, bulk import, or large payload handling.

## Use first

### Integration Cloud File Handling Primer
- URL: https://www.ateam-oracle.com/integration-cloud-file-handling-primer
- Type: a-team blog
- Category: file-based integration
- Relevance: high
- Authority: design guidance
- Freshness: stable
- Use when: designing file pickup/drop, SFTP/Object Storage staging, archive/error folders, chunking, schema validation, or duplicate file detection.
- Do not use for: real-time API-only designs unless files are part of an exception or replay mechanism.

## Design cues

- Include file pickup/drop pattern, naming convention, archive/error folders, chunking or staging, schema validation, duplicate file detection, and retention.
- Define batch acknowledgement, partial failure handling, and reprocessing controls.
- Include expected file size, record volume, and schedule window assumptions.
