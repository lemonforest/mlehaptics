# Known Issues

This document tracks known bugs and limitations that are documented for future resolution.

---

## Bug #105: NVS Peer Exclusivity Not Enforced

**Status:** Open
**Severity:** Medium
**Environment:** `xiao_esp32c6` (NVS bonding enabled)
**Discovered:** 2025-12-18

### Description

When using the production environment with NVS bonding enabled, a device that already has a paired peer saved in NVS will still connect to a **different** unpaired device if both are powered on during the pairing window.

### Expected Behavior

Once a peer MAC address is saved to NVS:
1. Device should ONLY scan for and connect to that specific peer
2. Connections from/to other devices should be rejected during peer discovery
3. NVS peer MAC should be the **source of truth** for finding a "friend"
4. Only clearing NVS (or explicit unpair action) should allow pairing with a different device

### Actual Behavior

- Device accepts connection from any peer during the discovery window
- Previously bonded peer is ignored if a new device connects first
- Results in unpredictable pairing behavior in multi-device environments

### Root Cause (Suspected)

The peer discovery logic doesn't check NVS for an existing bonded peer MAC before accepting new connections. The scan callback accepts any device advertising the bilateral service UUID.

### Proposed Fix

1. On startup, check NVS for saved peer MAC address
2. If peer MAC exists in NVS:
   - Only scan for that specific MAC address
   - Reject advertising/connections from other peers
   - After timeout (e.g., 30s), optionally fall back to open discovery
3. If no peer MAC in NVS:
   - Proceed with normal battery-based discovery and bonding
   - Save new peer MAC to NVS after successful pairing

### Files Likely Affected

- `src/ble_manager.c` - Scan callback, connection handling
- `src/nvs_manager.c` - Peer MAC storage/retrieval

### Workaround

Use `xiao_esp32c6_ble_no_nvs` environment during development/testing to avoid stale bond confusion.

---

## Bug #106: Firmware Version Timestamp Not Enforced

**Status:** Open (Deferred)
**Severity:** Low
**Discovered:** 2025-12-18

### Description

The firmware version checking system (AD040) was designed to compare both semantic version AND build timestamp, but:

1. The version mismatch was never actually preventing pairing
2. No orange LED blink pattern was shown on version mismatch
3. The `firmware_versions_match()` function was called but its return value may not have been used to reject connections

### Current State (v0.6.129)

The timestamp matching has been intentionally relaxed - only `major.minor.patch` is now enforced, with timestamp differences logged as warnings. This is the correct behavior for practical use since PlatformIO rebuilds make identical timestamps impractical.

### Remaining Issue

The original design called for visual feedback (orange blink) when firmware versions don't match. This was never implemented or tested.

### Proposed Resolution

1. Verify `firmware_versions_match()` is called during peer connection
2. Add orange LED blink pattern for version mismatch (warning, not rejection)
3. Log version mismatch clearly in serial output
4. Consider adding version info to PWA status display

### Priority

Low - Current behavior (semantic version matching) is sufficient for production use. Visual feedback is nice-to-have for debugging.

---

## Issue Tracking Format

```markdown
## Bug #NNN: Brief Title

**Status:** Open | In Progress | Resolved | Deferred
**Severity:** Critical | High | Medium | Low
**Environment:** Affected build environment(s)
**Discovered:** YYYY-MM-DD

### Description
What the bug is.

### Expected Behavior
What should happen.

### Actual Behavior
What actually happens.

### Root Cause
Why it happens (if known).

### Proposed Fix
How to fix it.

### Files Affected
Which files need changes.

### Workaround
Temporary solution if available.
```

---

**Last Updated:** 2025-12-18
