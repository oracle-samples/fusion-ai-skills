# Identity Propagation References

Use this file when the integration must call Fusion SaaS or another target on behalf of the initiating user, preserve user identity for audit, or compare identity propagation with service-account access.

## Use first

### Identity Propagation - OIC and Fusion SaaS
- URL: https://www.ateam-oracle.com/identity-propagation-oic-fusion-saas
- Type: a-team blog
- Category: identity propagation
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: deciding whether to propagate end-user identity between OIC and Fusion SaaS.
- Do not use for: scheduled or background integrations where no initiating user context exists.

### A Test Run of Identity Propagation with OIC REST Adapter
- URL: https://www.ateam-oracle.com/a-test-run-of-identity-propagation-with-oic-rest-adapter
- Type: a-team blog
- Category: identity propagation
- Relevance: medium
- Authority: example-only
- Freshness: version-sensitive
- Use when: a concrete REST Adapter identity propagation example helps explain implementation implications.
- Do not use for: canonical security policy decisions without a higher-authority source.

## Design cues

- State whether OIC uses a service account or propagates end-user identity.
- Capture token exchange, user authorization, audit attribution, and fallback for scheduled/background processing.
- Explain why identity propagation is not appropriate when the integration has no user context.
