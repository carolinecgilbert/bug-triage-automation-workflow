# Bluetooth Manager

## Purpose

Manages Bluetooth Low Energy discovery, pairing, connection state, GATT service discovery, and reconnect behavior between the mobile app and devices.

## Responsibilities

- Scan for devices advertising supported service UUIDs.
- Coordinate pairing, bonding, and trust establishment.
- Discover GATT services and subscribe to characteristic updates.
- Handle reconnects, disconnect reasons, and connection health metrics.
- Surface platform-specific Bluetooth permission and capability errors.

## Common Failure Modes

- Pairing timeout from stale bonds or identity mismatch.
- Missing service UUID in advertising payload.
- GATT discovery timeout on older firmware or low signal strength.
- OS permission denial preventing scan or connection.
- Reconnect loop after firmware changes pairing mode behavior.

## Related Components

bluetooth, firmware_update

## Owning Team

device-connectivity-team
