# Firmware Update Troubleshooting

## Component

firmware_update

## Symptoms

- Device downloads firmware but refuses to install it.
- Update job transitions from `downloading` to `failed_integrity_check`.
- Logs show expected and actual SHA-256 values do not match.
- Update succeeds for one hardware revision but fails for another.
- Devices repeatedly retry the same update bundle.

## Common Root Causes

- Release manifest references an outdated artifact hash after a binary was republished.
- CDN edge cache serves an older firmware image than the manifest expects.
- Device selects the wrong hardware-specific artifact because capability metadata is incomplete.
- Partial download is incorrectly marked complete after a transient network interruption.
- Compression or signing step changed the binary after the hash was calculated.

## Recommended Next Steps

- Compare manifest hash, artifact registry hash, and device-computed hash.
- Check whether the firmware artifact was rebuilt or overwritten after manifest generation.
- Purge CDN cache for the affected firmware path and retry from a test device.
- Verify hardware revision mapping in the rollout rule and manifest entry.
- Inspect update service logs for retries, byte counts, and integrity check failures.

## Related Keywords

firmware, OTA, manifest, hash mismatch, SHA-256, integrity check, artifact, CDN, rollout, hardware revision
