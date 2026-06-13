# OTA Update Service

## Purpose

Coordinates over-the-air firmware update availability, manifest delivery, staged rollouts, artifact download metadata, and device update status reporting.

## Responsibilities

- Select update manifests based on device model, hardware revision, region, and rollout cohort.
- Return signed firmware artifact URLs and expected integrity metadata.
- Track device update states including download, validation, install, and rollback.
- Enforce rollout gates, pause controls, and minimum supported firmware versions.
- Record update failures for fleet health reporting.

## Common Failure Modes

- Hash mismatch between release manifest and served artifact.
- Missing manifest after incomplete release promotion.
- Incorrect hardware revision mapping causing wrong binary selection.
- CDN cache serving stale artifacts after rebuild.
- Partial download or interrupted transfer marked as complete by client.

## Related Components

firmware_update, release_pipeline, networking

## Owning Team

firmware-update-team
