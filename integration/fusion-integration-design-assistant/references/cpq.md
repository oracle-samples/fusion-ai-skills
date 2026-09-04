# CPQ Integration References

Use this file when Oracle CPQ participates in quote, pricing, configuration, order capture, approval, order handoff, or Fusion orchestration flows.

## Use first

### Oracle CPQ Integration Patterns
- URL: https://www.ateam-oracle.com/oracle-cpq-integration-patterns
- Type: a-team blog
- Category: CPQ integration
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: CPQ is a source, target, or orchestration participant in the integration design.
- Do not use for: integrations that do not involve CPQ quote/configuration/pricing/order handoff behavior.

## Design cues

- Identify CPQ as source, target, or orchestration participant.
- Capture quote lifecycle state, pricing/configuration dependencies, synchronous versus asynchronous handoff, and compensation behavior.
- Include recovery behavior for failed downstream handoff after quote/order state has changed.
