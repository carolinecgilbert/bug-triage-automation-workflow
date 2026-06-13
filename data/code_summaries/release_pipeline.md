# Release Pipeline

## Purpose

Builds, validates, packages, and promotes application and firmware artifacts through staging and production release environments.

## Responsibilities

- Compile and package service, mobile, and firmware artifacts.
- Generate release manifests and artifact integrity metadata.
- Publish artifacts to registry and CDN-backed storage.
- Enforce environment gates, smoke tests, and rollback procedures.
- Track release versions, provenance, and promotion approvals.

## Common Failure Modes

- Manifest generation skipped due to missing environment configuration.
- Artifact overwritten after manifest hash calculation.
- Promotion succeeds despite missing required release artifacts.
- Staging and production environments diverge in secrets or variables.
- Build cache produces stale artifact metadata.

## Related Components

release_pipeline, firmware_update, auth

## Owning Team

build-systems-team
