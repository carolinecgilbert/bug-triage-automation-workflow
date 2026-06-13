# Firmware update 4.13.2 fails validation on HW-B2 devices

## Labels

bug, firmware_update, device, needs-triage

## Description

Several customers in the beta rollout reported that firmware `4.13.2` downloads successfully but fails before installation. The device remains on `4.12.9` and the app shows "Update package could not be verified." The issue appears limited to hardware revision `hw-b2`; `hw-c1` devices in the same account updated successfully.

Device diagnostics include:

- update job id: `ota-2026-06-12-4-13-2-beta`
- update state: `failed_integrity_check`
- expected bytes: `18423172`
- downloaded bytes: `18423172`
- computed hash differs from manifest hash

## Current Status

Unresolved. Rollout is still active for the beta cohort pending triage.
