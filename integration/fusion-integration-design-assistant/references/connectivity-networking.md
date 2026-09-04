# Connectivity, Private Endpoints, and Network Paths

Use this file when the integration reaches private/on-premises endpoints, private Fusion endpoints, private OCI resources, cross-tenancy OCI services, or endpoints not exposed publicly.

## Use first

### Configuring OIC Gen3 Private Endpoint Outbound Connection
- URL: https://www.ateam-oracle.com/configuring-oic-gen3-private-endpoint-outbound-connection
- Type: a-team blog
- Category: connectivity and private endpoint
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: designing outbound connectivity from OIC Gen3 to private endpoints or private OCI resources.
- Do not use for: generic public REST integrations that do not need private networking.

### OIC Network Flows
- URL: https://www.ateam-oracle.com/oic-network-flows
- Type: a-team blog
- Category: connectivity and private endpoint
- Relevance: high
- Authority: design guidance
- Freshness: version-sensitive
- Use when: explaining public internet, private endpoint, service gateway, DRG, and connectivity agent traffic paths.
- Do not use for: application mapping, business logic, or payload design.

## Design cues

- Distinguish public internet, private endpoint, service gateway, dynamic routing gateway, and connectivity agent paths.
- Capture firewall, DNS, TLS, certificate, route table, and ownership prerequisites.
- State whether traffic originates from OIC public egress, OIC private endpoint, or the connectivity agent.
- Include failover and operational responsibility implications for private connectivity.
