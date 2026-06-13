# Bluetooth Pairing Troubleshooting

## Component

bluetooth

## Symptoms

- Device appears in scan results but pairing times out.
- Mobile app shows "pairing failed" after the PIN or confirmation step.
- Previously paired devices fail to reconnect after firmware update.
- Pairing succeeds on Android but fails on iOS, or the reverse.
- Logs show repeated GATT service discovery failures.

## Common Root Causes

- Device remains bonded to an old mobile identity and rejects new pairing attempts.
- BLE advertising payload omits required service UUID or capability flags.
- GATT service discovery timeout is too aggressive for older hardware.
- Firmware update changed pairing mode behavior without updating mobile client expectations.
- Bluetooth permissions or background restrictions prevent the mobile client from completing discovery.

## Recommended Next Steps

- Confirm the device is in pairing mode and clear stale bonds on both device and phone.
- Capture BLE scan and GATT discovery logs from the mobile client.
- Verify advertising payload includes the expected service UUID and firmware capability flags.
- Test with current and previous firmware versions to identify regressions.
- Check platform-specific permission prompts and OS Bluetooth diagnostics.

## Related Keywords

bluetooth, BLE, pairing timeout, GATT, bond, advertising, service UUID, reconnect, device discovery
