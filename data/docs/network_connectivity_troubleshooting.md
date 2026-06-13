# Network Connectivity Troubleshooting

## Component

networking

## Symptoms

- API requests fail before reaching the service backend.
- Logs show DNS resolution failures for service or artifact hostnames.
- Client retries exhaust quickly during startup.
- Requests succeed on office networks but fail on carrier or home networks.
- TLS handshake or proxy errors appear after network library changes.

## Common Root Causes

- DNS resolver cache contains stale entries after service migration.
- Network client does not retry transient `ENOTFOUND` or timeout failures.
- Corporate proxy or captive portal intercepts HTTPS traffic.
- IPv6 resolution is preferred but the target service is not reachable over IPv6.
- TLS certificate chain changed and older clients lack the required root certificate.

## Recommended Next Steps

- Capture hostname, resolver response, IP family, and retry timing from client logs.
- Test resolution using the same network path and DNS server as affected clients.
- Validate service DNS records, TTLs, and recent infrastructure changes.
- Review retry and backoff settings for startup-critical network calls.
- Check certificate chain compatibility for supported client platforms.

## Related Keywords

networking, DNS, ENOTFOUND, timeout, retry, TLS, proxy, IPv6, API gateway, connectivity
