# API Client Startup Fails Due to DNS Resolution Error

## Labels

bug, networking, dns, sev2, client

## Description

After migrating the API gateway to a new regional endpoint, a subset of desktop clients failed during startup with `ENOTFOUND api.prod.example.internal`. The failures were concentrated among users on networks with custom DNS forwarders. Restarting the client sometimes resolved the issue.

## Investigation

Client logs showed a single DNS lookup attempt during startup and no retry before the initialization process failed. Infrastructure confirmed the DNS record had been updated with a low TTL, but several resolvers cached the old negative response from a pre-migration validation window. The network client treated `ENOTFOUND` as non-retryable.

## Root Cause

The client startup path performed a required API discovery call before retry policy initialization. Transient DNS resolution failures were surfaced as fatal errors, so clients behind stale resolvers could not recover without manual restart.

## Resolution

The networking library now retries DNS lookup failures with exponential backoff during startup. API gateway DNS migration runbooks were updated to avoid publishing validation windows that can create negative cache entries.

## Owner Team

networking-team
