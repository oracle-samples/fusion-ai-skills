# Event-Driven Integration References

Use this file when the requirement includes business events, near-real-time processing, order status publication, item import/load completion, or event-based decoupling.

## Use first

### Event Driven Integrations Primer
- URL: https://www.ateam-oracle.com/event-driven-integrations-primer
- Type: a-team blog
- Category: event-driven integration
- Relevance: high
- Authority: design guidance
- Freshness: stable
- Use when: explaining producer, event channel, subscriber, filtering, idempotency, replay, and asynchronous decoupling.
- Do not use for: product-specific order management or SCM lifecycle boundaries when a more specific source applies.

### Event-Based Streaming Integration - SCM Item Load
- URL: https://www.ateam-oracle.com/event-based-streaming-integration-scm-item-load
- Type: a-team blog
- Category: event-driven integration
- Relevance: high
- Authority: scenario guidance
- Freshness: version-sensitive
- Use when: designing event-based item load or SCM item import completion processing.
- Do not use for: unrelated event patterns that do not involve item load or SCM import semantics.

### OM Order Status Integration Patterns
- URL: https://www.ateam-oracle.com/om-order-status-integration-patterns
- Type: a-team blog
- Category: event-driven integration
- Relevance: high
- Authority: scenario guidance
- Freshness: version-sensitive
- Use when: designing order status publication, subscription, or downstream order lifecycle integrations.
- Do not use for: generic non-order integrations.

## Design cues

- Identify producer, event channel, subscriber, payload, event filtering, idempotency key, and ordering expectation.
- Include replay/recovery for missed events and duplicate-event handling.
- For order management or SCM load scenarios, include business object lifecycle and completion/status event boundaries.
