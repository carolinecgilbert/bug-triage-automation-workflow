# Firmware Update Fails With Hash Mismatch on v4.12.7

## Labels

bug, firmware_update, ota, sev2, device

## Description

Devices in the 15 percent rollout cohort for firmware version `4.12.7` downloaded the update package but failed before install. The device UI reported "update package failed validation." The fleet dashboard showed a spike in `failed_integrity_check` results for hardware revision `hw-b2`.

## Investigation

The OTA service returned manifest entry `fw-hw-b2-4.12.7.bin` with SHA-256 `57d8c9...a91b`. Device logs showed the downloaded binary hash as `ea40f1...32bc`. The artifact registry contained two uploads with the same logical version and filename. The second upload occurred 11 minutes after manifest generation, during a manual rebuild to include a minor bootloader flag.

## Root Cause

The firmware artifact was republished after the release manifest was generated. The manifest retained the original hash, while the CDN and artifact registry served the rebuilt binary. A missing immutability check allowed overwrite of an already-promoted versioned artifact.

## Resolution

The rollout was paused, a corrected manifest was generated for `4.12.7-r1`, and CDN cache was purged for the affected path. The release pipeline now blocks overwrites for promoted firmware artifacts and requires a new revision suffix for rebuilt binaries.

## Owner Team

firmware-update-team
