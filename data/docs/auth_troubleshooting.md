# Authentication Troubleshooting

## Component

auth

## Symptoms

- User is redirected repeatedly between the application and the identity provider.
- Refresh token requests return `401 Unauthorized` or `invalid_grant`.
- Session cookie is present but the API rejects requests as unauthenticated.
- Login succeeds in staging but fails in production after a release.
- Mobile clients report "session expired" immediately after a successful login.

## Common Root Causes

- Redirect URI mismatch between the deployed application and identity provider configuration.
- Session cookie domain, path, `SameSite`, or secure flag changed during deployment.
- Refresh token rotation is enabled but clients are retrying with an already-consumed token.
- Clock skew causes access tokens to be considered expired before validation.
- OAuth state or nonce validation fails because the session store is unavailable or using inconsistent keys across instances.

## Recommended Next Steps

- Compare the configured redirect URI with the callback URL emitted in login logs.
- Inspect recent changes to session middleware, cookie attributes, and auth proxy configuration.
- Check identity provider audit logs for `invalid_redirect_uri`, `invalid_grant`, and failed nonce validation events.
- Confirm all application instances use the same session signing keys and clock synchronization.
- Reproduce using a clean browser session and capture the full redirect chain.

## Related Keywords

oauth, redirect loop, callback, refresh token, invalid_grant, session cookie, SameSite, nonce, state, login
