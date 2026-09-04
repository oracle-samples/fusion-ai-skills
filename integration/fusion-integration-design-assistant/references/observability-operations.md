# Observability and Operations References

Use this file when defining monitoring, dashboards, alerting, operational analytics, log forwarding, support diagnostics, and production runbooks.

## Use first

### Leveraging Logging Analytics for Oracle Integration Cloud Logging and Monitoring
- URL: https://www.ateam-oracle.com/leveraging-logging-analytics-for-oracle-integration-cloud-logging-and-monitoring
- Type: a-team blog
- Category: observability and operations
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: defining OIC logging, monitoring, dashboards, alerts, and support diagnostics.
- Do not use for: application error handling design without pairing with error-handling guidance.

### Leveraging Logging Analytics for Oracle Integration Cloud Logging and Monitoring - Part 2
- URL: https://www.ateam-oracle.com/leveraging-logging-analytics-for-oracle-integration-cloud-logging-and-monitoring-part-2
- Type: a-team blog
- Category: observability and operations
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: extending Logging Analytics guidance with dashboards, operational analytics, or advanced monitoring examples.
- Do not use for: basic designs where simple OIC tracking fields and alerts are sufficient.

## Design cues

- Include correlation identifiers, OIC tracking fields, structured log fields, dashboards, alert thresholds, retention, and operational runbooks.
- Separate build-time troubleshooting from production observability.
- Define ownership, escalation path, and support handoff artifacts.
