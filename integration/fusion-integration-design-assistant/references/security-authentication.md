# Security and Authentication References

Use this file when choosing OAuth flows, Fusion authentication, cross-domain IAM setup, SOAP JWT authentication, TLS, secrets, least privilege, or certificate/key management.

## Use first

### Simplifying OAuth for OIC to Fusion Integrations - Authorization Code vs Client Credentials Across IAM Domains
- URL: https://www.ateam-oracle.com/simplifying-oauth-for-oic-to-fusion-integrations-authorization-code-vs-client-credentials-across-iam-domains
- Type: a-team blog
- Category: security and authentication
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: comparing authorization code and client credentials for OIC to Fusion integrations, especially across IAM domains.
- Do not use for: non-Fusion authentication patterns without confirming product support.

### Enabling OAuth 2.0 JWT Authentication for Oracle SOAP Services in OIC Gen3
- URL: https://www.ateam-oracle.com/enabling-oauth-20-jwt-authentication-for-oracle-soap-services-in-oic-gen3
- Type: a-team blog
- Category: security and authentication
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: SOAP services require OAuth 2.0 JWT authentication from OIC Gen3.
- Do not use for: REST-only integrations that do not use SOAP or JWT authentication.

## Design cues

- Prefer client credentials for system-to-system integrations when end-user context is not required.
- Use authorization code or identity propagation where user context and consent/audit are required.
- For SOAP services, evaluate JWT authentication support and certificate/key management.
- Always include credential storage, least privilege, TLS, audit, and secrets rotation considerations.
