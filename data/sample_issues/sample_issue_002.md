# Users are logged out immediately after refreshing dashboard

## Labels

bug, auth, web, needs-triage

## Description

Production users report that refreshing the dashboard causes an immediate logout. The login flow succeeds, but after the page reloads, API calls to `/v1/me` return `401`. The browser still has an `app_session` cookie. Reports started after the June 12 deployment and are concentrated among users with older existing sessions.

Observed behavior:

- login callback returns `302` to `/dashboard`
- `/v1/me` returns `401 session_signature_invalid`
- clearing cookies and logging in again fixes the issue for some users
- issue reproduces across Chrome and Safari

## Current Status

Unresolved. Support has linked nine customer tickets and requested owner recommendation.
