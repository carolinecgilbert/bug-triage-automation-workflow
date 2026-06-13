# Production Release Missing Firmware Manifest

## Labels

bug, release_pipeline, firmware_update, sev1, deployment

## Description

The production OTA endpoint returned `404 manifest not found` for firmware channel `stable` immediately after release promotion. Devices checking for updates failed to receive a manifest, and the fleet dashboard reported elevated update check errors across all hardware revisions.

## Investigation

The release promotion workflow completed successfully, but artifact storage lacked `stable/manifest.json`. CI logs showed manifest generation was skipped because the `GENERATE_OTA_MANIFEST` environment variable was unset in the production promotion job. The staging job had the variable configured at the repository level, but production used an environment-scoped configuration.

## Root Cause

The production release environment was missing a required manifest generation variable. The pipeline did not fail when the manifest artifact was absent, so the promotion job marked the release successful despite publishing incomplete OTA metadata.

## Resolution

The missing environment variable was added to production. The release pipeline now validates required artifacts before promotion and fails the deployment if `manifest.json` is absent or empty.

## Owner Team

build-systems-team
