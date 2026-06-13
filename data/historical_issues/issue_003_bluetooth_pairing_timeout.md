# BLE Pairing Timeout After Device Reset

## Labels

bug, bluetooth, mobile, sev3, pairing

## Description

Customers reported that devices appeared in the mobile app scan list but timed out during pairing after a factory reset. The issue was most common on devices previously paired to the same phone before the reset. Android reports were more frequent than iOS reports.

## Investigation

Mobile logs showed the device advertising normally and accepting the initial connection. Pairing failed during GATT service discovery after the app attempted to reuse a cached bond. Device logs showed `bond_identity_mismatch` followed by disconnect. Clearing Bluetooth storage on the phone allowed pairing to complete.

## Root Cause

The factory reset flow cleared the device bond table but did not rotate the BLE identity address. Some Android versions reused the old bond metadata for the same address, causing the mobile app to skip the fresh pairing path and attempt service discovery with stale credentials.

## Resolution

Firmware was updated to rotate the BLE identity address after factory reset. The mobile app also added a fallback path that detects `bond_identity_mismatch`, clears the stale bond, and prompts the user to retry pairing.

## Owner Team

device-connectivity-team
