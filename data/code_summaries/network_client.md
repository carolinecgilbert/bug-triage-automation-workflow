# Network Client

## Purpose

Provides resilient HTTP and DNS behavior for service API calls, artifact downloads, telemetry upload, and startup discovery.

## Responsibilities

- Resolve service hostnames and establish TLS connections.
- Apply retry, timeout, circuit breaker, and backoff policy.
- Attach authentication headers and request correlation identifiers.
- Detect proxy, captive portal, and network reachability failures.
- Emit structured diagnostics for connectivity issues.

## Common Failure Modes

- DNS `ENOTFOUND` or stale resolver cache during service migration.
- TLS handshake failure due to certificate chain or client trust store mismatch.
- Retry storms from overly aggressive backoff settings.
- Proxy interception causing unexpected certificate or HTTP status errors.
- IPv6 preference causing unreachable endpoint selection.

## Related Components

networking, auth, firmware_update

## Owning Team

networking-team
