## Copyright (c) 2026, Oracle and/or its affiliates.
## Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl

# fusion-data-extraction-advisor

## Description
advise customers on which oracle fusion applications data extraction or reporting option to choose based on use case. use when a user asks how to extract data from fusion, or wants a recommendation across otbi, bi publisher, hcm extracts, export management, item publication, bicc, rest api, soap services, fusion analytics warehouse, or desktop export. trigger for decisions involving data volume, batch vs real-time, incremental extract, pillar fit across cx hcm erp scm, output format, analytics vs integration, external warehouse replication, and performance or security tradeoffs.

## Quick Start
Use this starter prompt:
- "Given this use case, should we use BICC, REST, or OTBI and why?"

## Inputs:
- Business use case, consumers, and decision objective (analytics vs integration)
- Volume/timeliness profile (batch, near-real-time, incremental, one-time)
- Functional scope across ERP/SCM/HCM/CX and object-level requirements
- Constraints on tooling, security, and downstream warehouse targets

## Outputs:
- Recommended extraction/reporting option with rationale and tradeoffs
- Alternative options with risk/cost/performance comparison
- Implementation checklist aligned to selected method
- Decision summary suitable for architecture review

## Workflow:
1. Capture use-case constraints and classify decision dimensions
2. Evaluate candidate methods (OTBI, BIP, BICC, REST, SOAP, FAW, exports)
3. Score options by volume, latency, governance, and maintainability fit
4. Recommend primary approach plus fallback path
5. Produce execution checklist and validation criteria

## Prompts:
- "Given this use case, should we use BICC, REST, or OTBI and why?"
- "Create a decision matrix for extraction options across ERP and SCM domains."
- "Recommend a low-risk path for incremental warehouse replication from Fusion."
- "What tradeoffs should I expect if I choose BI Publisher instead of BICC?"

## References
- `SKILL.md`
