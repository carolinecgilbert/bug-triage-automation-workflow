# Login Redirect Loop After Session Middleware Change

## Labels

bug, auth, regression, sev2, web

## Description

After the 2026.04.18 web deployment, users authenticating through the production identity provider were redirected between `/login`, `/oauth/callback`, and the provider authorization URL until the browser stopped the redirect chain. The issue affected Chrome and Safari users with existing sessions. New private browsing sessions were less likely to reproduce the loop.

## Investigation

Auth service logs showed successful authorization code exchange followed by immediate session validation failure. The callback handler wrote a session cookie with `SameSite=Strict`, while the identity provider returned users through a cross-site redirect. Browser dev tools confirmed that the cookie was not attached to the first request after callback. Identity provider logs did not show credential failures or invalid client configuration.

## Root Cause

The session middleware default changed from `SameSite=Lax` to `SameSite=Strict` during a dependency upgrade. This prevented the newly-created session cookie from being sent after the OAuth callback redirect, causing the application to believe the user was unauthenticated and restart login.

## Resolution

The auth service explicitly set `SameSite=Lax` for the web session cookie and added an integration test that validates cookie behavior during the OAuth callback flow. Production sessions were allowed to expire naturally because no token data was corrupted.

## Owner Team

platform-team
