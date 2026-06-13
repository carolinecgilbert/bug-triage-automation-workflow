# Auth Service

## Purpose

Provides user authentication, session lifecycle management, OAuth integration, token refresh, and authorization context for downstream services.

## Responsibilities

- Initiate OAuth authorization code flow and validate callback state.
- Exchange authorization codes for access and refresh tokens.
- Issue, validate, refresh, and revoke user sessions.
- Enforce cookie, CSRF, nonce, and redirect URI controls.
- Publish authenticated user identity and scopes to API middleware.

## Common Failure Modes

- Redirect loop caused by cookie attributes or callback URI mismatch.
- Refresh token invalidation after token rotation or retry reuse.
- Session validation failure from inconsistent signing keys across instances.
- Premature token expiry caused by clock skew.
- Identity provider outage or malformed provider metadata.

## Related Components

auth, networking, release_pipeline

## Owning Team

platform-team
