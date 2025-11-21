# AD040: Firmware Version Checking for Peer Devices

**Date:** November 19, 2025
**Phase:** 2 (Post-Time Sync)
**Status:** ⏳ **APPROVED** - Implementation pending

---

## Context

Phase 2 implements time synchronization and bilateral control protocols between peer devices. If devices run different firmware versions with incompatible protocols or message formats, the result could be:
- Silent failures (commands ignored due to format mismatch)
- Incorrect motor timing (different frequency calculations)
- BLE protocol incompatibility (characteristic UUID mismatches)
- Safety violations (emergency shutdown messages not recognized)

**User Request:**
> "Can we add some sort of firmware version signature check to ensure emdr pulser devices must be on the same build? Even if there's just some way to get a random value that is always the same within a build but any change to the code base would result in this random value being seeded differently."

**Hybrid Architecture Request:**
> "We might decide that a minor update should still support connecting to some lower versions, can we go with this architecture hybrid of your plan? A way to disable this might be useful, even if it's just a different build environment, xiao_esp32c6_allow_firmware_mismatch would probably work."

---

## Decision

Implement **Git Commit Hash Versioning with Configurable Strictness** for firmware version checking:

1. **Automatic Versioning:** Embed git commit hash at build time (no manual maintenance)
2. **Three Strictness Levels:** STRICT, COMPATIBLE, DISABLED (configurable via build environment)
3. **Bidirectional Negotiation:** Both devices exchange versions AND compatibility results
4. **Motor Task Coordination:** Wait for version check and warning patterns before starting motors
5. **Integration Point:** Version exchange during peer discovery (pre-connection or post-connection)

---

## Architecture

### Version Structure

**File:** `src/ble_manager.h` (planned)

```c
/**
 * @brief Version check strictness modes
 */
typedef enum {
    VERSION_CHECK_DISABLED = 0,   // No version checking (development)
    VERSION_CHECK_COMPATIBLE = 1, // Major.minor must match, patch can differ
    VERSION_CHECK_STRICT = 2      // Exact git hash match required (production)
} version_check_mode_t;

/**
 * @brief Firmware version structure
 *
 * 8-byte structure for BLE transmission efficiency
 */
typedef struct __attribute__((packed)) {
    uint32_t git_hash;      // 4 bytes: First 8 hex chars of git commit hash
    uint8_t  major;         // Major version (breaking changes)
    uint8_t  minor;         // Minor version (feature additions)
    uint8_t  patch;         // Patch version (bug fixes)
    uint8_t  check_mode;    // Strictness level (0=DISABLED, 1=COMPATIBLE, 2=STRICT)
} firmware_version_t;

/**
 * @brief Version compatibility status
 *
 * Result of version comparison between local and peer devices
 */
typedef enum {
    COMPAT_UNKNOWN = 0,       // No version check performed yet
    COMPAT_EXACT_MATCH = 1,   // Perfect match (same git hash)
    COMPAT_PATCH_DIFF = 2,    // Patch version differs (WARNING - yellow blink)
    COMPAT_MINOR_DIFF = 3,    // Minor version differs (WARNING - orange blink)
    COMPAT_MAJOR_DIFF = 4,    // Major version differs (REJECT - red blink)
    COMPAT_DEV_MODE = 5       // One device has check disabled (ALLOW - blue blink)
} compatibility_status_t;
```

### Build-Time Version Embedding

**File:** `platformio.ini` (planned)

```ini
# Production build with strict version checking
[env:xiao_esp32c6]
platform = espressif32
framework = espidf
board = seeed_xiao_esp32c6
build_flags =
    ${env:base_esp32c6.build_flags}
    -DFIRMWARE_VERSION_MAJOR=0
    -DFIRMWARE_VERSION_MINOR=3
    -DFIRMWARE_VERSION_PATCH=0
    -DFIRMWARE_VERSION_CHECK=VERSION_CHECK_STRICT
    '-DFIRMWARE_GIT_HASH=0x'!git rev-parse --short=8 HEAD''

# Development build with version checking disabled
[env:xiao_esp32c6_allow_mismatch]
extends = env:xiao_esp32c6
build_flags =
    ${env:xiao_esp32c6.build_flags}
    -DFIRMWARE_VERSION_CHECK=VERSION_CHECK_DISABLED

# Field update build with compatible version checking
[env:xiao_esp32c6_compatible]
extends = env:xiao_esp32c6
build_flags =
    ${env:xiao_esp32c6.build_flags}
    -DFIRMWARE_VERSION_CHECK=VERSION_CHECK_COMPATIBLE
```

**Git Hash Extraction:**
```bash
# PlatformIO executes this command at build time:
git rev-parse --short=8 HEAD
# Output example: a1b2c3d4

# Converted to hex for C code:
0xa1b2c3d4
```

**Benefits:**
- ✅ Automatic versioning (zero maintenance)
- ✅ Deterministic (same source = same hash)
- ✅ Traceable (hash maps to exact git commit)
- ✅ No manual version bumping errors

### Bidirectional Version Negotiation Protocol

**Problem:** Older firmware doesn't know newer git hashes → cannot identify mismatch

**Solution:** Both devices exchange versions AND compatibility evaluation

```
Device A (Git Hash: a1b2c3d4)        Device B (Git Hash: a1b2c3d4)
────────────────────────────          ────────────────────────────
Step 1: Send version
  → version_message_t {
      git_hash: 0xa1b2c3d4
      major: 0, minor: 3, patch: 0
      check_mode: STRICT
  }

Step 2: Receive peer version          Step 2: Receive peer version
  ← version_message_t {                 ← version_message_t {
      git_hash: 0xa1b2c3d4                  git_hash: 0xa1b2c3d4
      major: 0, minor: 3, patch: 0          major: 0, minor: 3, patch: 0
      check_mode: STRICT                    check_mode: STRICT
  }                                    }

Step 3: Evaluate compatibility        Step 3: Evaluate compatibility
  Local:  0xa1b2c3d4                   Local:  0xa1b2c3d4
  Peer:   0xa1b2c3d4                   Peer:   0xa1b2c3d4
  Result: COMPAT_EXACT_MATCH           Result: COMPAT_EXACT_MATCH

Step 4: Send compatibility result     Step 4: Send compatibility result
  → compat_status: EXACT_MATCH          → compat_status: EXACT_MATCH

Step 5: Receive peer result           Step 5: Receive peer result
  ← compat_status: EXACT_MATCH          ← compat_status: EXACT_MATCH

Step 6: Consensus check               Step 6: Consensus check
  Both agree: EXACT_MATCH              Both agree: EXACT_MATCH
  → Proceed to pairing                 → Proceed to pairing
```

**Conflict Scenario (Device A has newer firmware):**

```
Device A (Git Hash: b2c3d4e5)        Device B (Git Hash: a1b2c3d4)
────────────────────────────          ────────────────────────────
Step 3A: Evaluate compatibility      Step 3B: Evaluate compatibility
  Local:  0xb2c3d4e5                   Local:  0xa1b2c3d4
  Peer:   0xa1b2c3d4                   Peer:   0xb2c3d4e5
  Result: COMPAT_MAJOR_DIFF (reject)   Result: COMPAT_MAJOR_DIFF (reject)

Step 4: Send compatibility result     Step 4: Send compatibility result
  → compat_status: MAJOR_DIFF           → compat_status: MAJOR_DIFF

Step 5: Receive peer result           Step 5: Receive peer result
  ← compat_status: MAJOR_DIFF           ← compat_status: MAJOR_DIFF

Step 6: Consensus check               Step 6: Consensus check
  Both agree: MAJOR_DIFF               Both agree: MAJOR_DIFF
  → Display red blink (5×)             → Display red blink (5×)
  → Disconnect and retry               → Disconnect and retry
```

**Key Benefit:** Both devices show same warning pattern even if one has older firmware

### Compatibility Evaluation Logic

**File:** `src/ble_manager.c` (planned)

```c
/**
 * @brief Evaluate firmware compatibility between local and peer devices
 *
 * @param local Local device firmware version
 * @param peer  Peer device firmware version
 * @return Compatibility status
 *
 * Logic:
 * - DISABLED mode: Always compatible (dev builds)
 * - STRICT mode: Exact git hash match required
 * - COMPATIBLE mode: Major.minor must match, patch can differ
 */
compatibility_status_t evaluate_firmware_compatibility(
    firmware_version_t local,
    firmware_version_t peer)
{
    // Check if either device has version checking disabled
    if (local.check_mode == VERSION_CHECK_DISABLED ||
        peer.check_mode == VERSION_CHECK_DISABLED) {
        ESP_LOGW(TAG, "Version check DISABLED (dev mode)");
        return COMPAT_DEV_MODE;  // Blue blink, allow connection
    }

    // STRICT mode: Exact git hash match required
    if (local.check_mode == VERSION_CHECK_STRICT ||
        peer.check_mode == VERSION_CHECK_STRICT) {
        if (local.git_hash != peer.git_hash) {
            ESP_LOGE(TAG, "Git hash mismatch: local=0x%08X peer=0x%08X",
                     local.git_hash, peer.git_hash);
            return COMPAT_MAJOR_DIFF;  // Red blink, reject
        }
        return COMPAT_EXACT_MATCH;  // Green blink, allow
    }

    // COMPATIBLE mode: Major.minor must match, patch can differ
    if (local.check_mode == VERSION_CHECK_COMPATIBLE ||
        peer.check_mode == VERSION_CHECK_COMPATIBLE) {
        if (local.major != peer.major) {
            ESP_LOGW(TAG, "Major version mismatch: local=%d peer=%d",
                     local.major, peer.major);
            return COMPAT_MAJOR_DIFF;  // Red blink, reject
        }

        if (local.minor != peer.minor) {
            ESP_LOGW(TAG, "Minor version mismatch: local=%d peer=%d",
                     local.minor, peer.minor);
            return COMPAT_MINOR_DIFF;  // Orange blink, warn but allow
        }

        if (local.patch != peer.patch) {
            ESP_LOGW(TAG, "Patch version differs: local=%d peer=%d",
                     local.patch, peer.patch);
            return COMPAT_PATCH_DIFF;  // Yellow blink, warn but allow
        }

        return COMPAT_EXACT_MATCH;  // Green blink, allow
    }

    // Should never reach here
    return COMPAT_UNKNOWN;
}
```

### Integration with Motor Task

**Problem:** Motor task must not start bilateral stimulation until version check completes

**Solution:** New motor task states for version checking and warning patterns

**File:** `src/motor_task.c` (planned)

```c
typedef enum {
    MOTOR_STATE_INIT = 0,
    MOTOR_STATE_WAIT_CONNECTION,
    MOTOR_STATE_VERSION_CHECK,      // NEW - Wait for version exchange
    MOTOR_STATE_VERSION_BLINK,      // NEW - Display warning pattern
    MOTOR_STATE_WAIT_PAIRING,
    MOTOR_STATE_PAIRING_COMPLETE,
    MOTOR_STATE_RUNNING,
    MOTOR_STATE_SHUTDOWN
} motor_state_t;
```

**State Machine Flow:**

```
MOTOR_STATE_INIT
    ↓
MOTOR_STATE_WAIT_CONNECTION
    ↓
MOTOR_STATE_VERSION_CHECK  ← Wait for MSG_VERSION_CHECK_RESULT from BLE task
    ↓
    ├─ COMPAT_EXACT_MATCH → Skip blink, proceed to WAIT_PAIRING
    ├─ COMPAT_PATCH_DIFF → Yellow blink (2×), proceed to WAIT_PAIRING
    ├─ COMPAT_MINOR_DIFF → Orange blink (3×), proceed to WAIT_PAIRING
    ├─ COMPAT_MAJOR_DIFF → Red blink (5×), SHUTDOWN (reject)
    └─ COMPAT_DEV_MODE → Blue blink (1×), proceed to WAIT_PAIRING
    ↓
MOTOR_STATE_VERSION_BLINK  ← Wait for pattern completion
    ↓
MOTOR_STATE_WAIT_PAIRING
    ↓
MOTOR_STATE_PAIRING_COMPLETE
    ↓
MOTOR_STATE_RUNNING
```

**Blink Pattern Timing:**

| Compatibility Status | LED Pattern | Duration | Motor State After |
|----------------------|-------------|----------|-------------------|
| COMPAT_EXACT_MATCH   | No blink    | 0ms      | WAIT_PAIRING (immediate) |
| COMPAT_DEV_MODE      | Blue (1×)   | 500ms    | WAIT_PAIRING (allow) |
| COMPAT_PATCH_DIFF    | Yellow (2×) | 1000ms   | WAIT_PAIRING (allow) |
| COMPAT_MINOR_DIFF    | Orange (3×) | 1500ms   | WAIT_PAIRING (allow) |
| COMPAT_MAJOR_DIFF    | Red (5×)    | 2500ms   | SHUTDOWN (reject) |

**Implementation:**

```c
case MOTOR_STATE_VERSION_CHECK:
    // Wait for version check result from BLE task (5 second timeout)
    if (xQueueReceive(ble_to_motor_queue, &msg, pdMS_TO_TICKS(5000))) {
        if (msg.type == MSG_VERSION_CHECK_RESULT) {
            compatibility_status_t compat = msg.data.version_compat;

            switch(compat) {
                case COMPAT_EXACT_MATCH:
                    ESP_LOGI(TAG, "Version match - proceeding to pairing");
                    state = MOTOR_STATE_WAIT_PAIRING;
                    break;

                case COMPAT_PATCH_DIFF:
                    ESP_LOGW(TAG, "Patch version differs - yellow blink warning");
                    status_led_pattern(LED_PATTERN_YELLOW, 2);
                    blink_delay_ms = 1000;  // 2 × 500ms
                    state = MOTOR_STATE_VERSION_BLINK;
                    break;

                case COMPAT_MINOR_DIFF:
                    ESP_LOGW(TAG, "Minor version differs - orange blink warning");
                    status_led_pattern(LED_PATTERN_ORANGE, 3);
                    blink_delay_ms = 1500;  // 3 × 500ms
                    state = MOTOR_STATE_VERSION_BLINK;
                    break;

                case COMPAT_MAJOR_DIFF:
                    ESP_LOGE(TAG, "Major version mismatch - REJECTING connection");
                    status_led_pattern(LED_PATTERN_RED, 5);
                    blink_delay_ms = 2500;  // 5 × 500ms
                    state = MOTOR_STATE_VERSION_BLINK;
                    shutdown_after_blink = true;  // Flag for shutdown
                    break;

                case COMPAT_DEV_MODE:
                    ESP_LOGW(TAG, "Dev mode - version check disabled (blue blink)");
                    status_led_pattern(LED_PATTERN_BLUE, 1);
                    blink_delay_ms = 500;
                    state = MOTOR_STATE_VERSION_BLINK;
                    break;

                default:
                    ESP_LOGE(TAG, "Unknown compatibility status: %d", compat);
                    state = MOTOR_STATE_SHUTDOWN;
                    break;
            }
        }
    } else {
        // Timeout - version check failed
        ESP_LOGE(TAG, "Version check timeout - aborting pairing");
        status_led_pattern(LED_PATTERN_RED, 5);
        state = MOTOR_STATE_SHUTDOWN;
    }
    break;

case MOTOR_STATE_VERSION_BLINK:
    // Wait for blink pattern to complete
    vTaskDelay(pdMS_TO_TICKS(blink_delay_ms));

    if (shutdown_after_blink) {
        ESP_LOGE(TAG, "Incompatible firmware - entering shutdown");
        state = MOTOR_STATE_SHUTDOWN;
    } else {
        ESP_LOGI(TAG, "Version check complete - proceeding to pairing");
        state = MOTOR_STATE_WAIT_PAIRING;
    }
    break;
```

**Critical Safety:** Motor task MUST wait for blink patterns before starting motors
- Ensures users see version warnings
- Prevents bilateral stimulation with incompatible devices
- Provides clear visual feedback for debugging

---

## BLE Integration Point

**Option 1: Post-Connection Version Exchange (RECOMMENDED)**

**Rationale:**
- Simpler implementation (no advertising packet size constraints)
- Can use BLE write/notify for bidirectional exchange
- Better error handling (connection already established)
- Clearer failure logging (connection handle available)

**Implementation:**

```c
// In ble_manager.c gap_event_handler (BLE_GAP_EVENT_CONNECT)

// Step 1: Connection established
ESP_LOGI(TAG, "Peer connection established; conn_handle=%d", event->connect.conn_handle);

// Step 2: Exchange firmware versions
firmware_version_t local_version = {
    .git_hash = FIRMWARE_GIT_HASH,
    .major = FIRMWARE_VERSION_MAJOR,
    .minor = FIRMWARE_VERSION_MINOR,
    .patch = FIRMWARE_VERSION_PATCH,
    .check_mode = FIRMWARE_VERSION_CHECK
};

esp_err_t err = ble_send_firmware_version(&local_version);
if (err != ESP_OK) {
    ESP_LOGE(TAG, "Failed to send firmware version: %s", esp_err_to_name(err));
    ble_gap_terminate(event->connect.conn_handle, BLE_ERR_REM_USER_CONN_TERM);
    return 0;
}

// Wait for peer version (handled in BLE characteristic write callback)
```

**Option 2: Pre-Connection Advertising (Alternative)**

**Rationale:**
- Fails faster (incompatibility detected before connection)
- Saves BLE resources (no connection attempt to incompatible peer)

**Challenges:**
- Limited advertising packet size (31 bytes total)
- Must fit alongside Bilateral UUID, device name, battery level
- More complex (requires scan response parsing)

**Verdict:** Use Option 1 (post-connection) for simplicity and reliability

---

## Compatibility Matrix

| Local Version | Peer Version | Check Mode | Result | LED Pattern | Action |
|---------------|--------------|------------|--------|-------------|--------|
| 0.3.0 (a1b2c3d4) | 0.3.0 (a1b2c3d4) | STRICT | EXACT_MATCH | None | Proceed |
| 0.3.0 (a1b2c3d4) | 0.3.1 (b2c3d4e5) | STRICT | MAJOR_DIFF | Red (5×) | Reject |
| 0.3.0 (a1b2c3d4) | 0.3.1 (b2c3d4e5) | COMPATIBLE | PATCH_DIFF | Yellow (2×) | Allow |
| 0.3.0 (a1b2c3d4) | 0.4.0 (c3d4e5f6) | COMPATIBLE | MINOR_DIFF | Orange (3×) | Allow |
| 0.3.0 (a1b2c3d4) | 1.0.0 (d4e5f6a7) | COMPATIBLE | MAJOR_DIFF | Red (5×) | Reject |
| 0.3.0 (a1b2c3d4) | 0.3.0 (any) | DISABLED | DEV_MODE | Blue (1×) | Allow |

**Decision Logic:**

```
if (DISABLED mode on either device):
    return COMPAT_DEV_MODE (blue blink, allow)

if (STRICT mode on either device):
    if (git_hash mismatch):
        return COMPAT_MAJOR_DIFF (red blink, reject)
    return COMPAT_EXACT_MATCH (no blink, allow)

if (COMPATIBLE mode):
    if (major version mismatch):
        return COMPAT_MAJOR_DIFF (red blink, reject)
    if (minor version mismatch):
        return COMPAT_MINOR_DIFF (orange blink, allow)
    if (patch version mismatch):
        return COMPAT_PATCH_DIFF (yellow blink, allow)
    return COMPAT_EXACT_MATCH (no blink, allow)
```

---

## Backward Compatibility

**Problem:** What happens when newer firmware connects to older firmware without version checking?

**Solution:** Timeout-based fallback

```c
// In ble_manager.c version exchange logic

// Try to read peer firmware version characteristic
esp_err_t err = ble_read_peer_firmware_version(&peer_version, 2000);  // 2s timeout

if (err == ESP_ERR_TIMEOUT || err == ESP_ERR_NOT_FOUND) {
    // Peer doesn't have version checking (older firmware)
    ESP_LOGW(TAG, "Peer firmware version unknown (older build without version checking)");

    if (FIRMWARE_VERSION_CHECK == VERSION_CHECK_DISABLED) {
        // Dev mode - allow connection to any firmware
        ESP_LOGI(TAG, "Dev mode - allowing connection to unknown firmware version");
        return COMPAT_DEV_MODE;
    } else {
        // Production mode - reject unknown firmware for safety
        ESP_LOGE(TAG, "Production mode - rejecting connection to unknown firmware version");
        return COMPAT_MAJOR_DIFF;  // Red blink, reject
    }
}
```

**Behavior:**

| Local Build | Peer Build | Result |
|-------------|------------|--------|
| v0.3.0 with version check | v0.2.0 without version check | Dev mode: Allow (blue blink), Production: Reject (red blink) |
| v0.3.0 without version check | v0.2.0 without version check | Allow (no version check on either side) |

---

## Testing Strategy

### Unit Tests

1. **Git Hash Embedding Test:**
   - Verify FIRMWARE_GIT_HASH defined at compile time
   - Confirm hash matches `git rev-parse HEAD`
   - Validate hash is 8 hex characters (32-bit)

2. **Compatibility Evaluation Test:**
   - Test all compatibility matrix combinations
   - Verify correct LED pattern selection
   - Confirm STRICT/COMPATIBLE/DISABLED behavior

3. **Bidirectional Negotiation Test:**
   - Simulate version exchange between devices
   - Verify both devices reach same conclusion
   - Test conflict scenarios (different hashes)

### Integration Tests

1. **Same Firmware Version:**
   - Build same firmware for both devices
   - Power on and pair
   - Verify: No LED blink, immediate pairing

2. **Patch Version Difference:**
   - Build v0.3.0 for Device A
   - Build v0.3.1 for Device B (COMPATIBLE mode)
   - Verify: Yellow blink (2×), pairing allowed

3. **Major Version Difference:**
   - Build v0.3.0 for Device A
   - Build v1.0.0 for Device B
   - Verify: Red blink (5×), pairing rejected

4. **Dev Mode Test:**
   - Build with VERSION_CHECK_DISABLED
   - Connect to any firmware version
   - Verify: Blue blink (1×), pairing allowed

5. **Backward Compatibility Test:**
   - Build v0.3.0 with version check (Device A)
   - Use v0.2.0 without version check (Device B)
   - Dev mode: Allow, Production mode: Reject

### Hardware Validation

1. **Blink Timing Test:**
   - Verify blink patterns don't interfere with motor task
   - Confirm motor waits for pattern completion
   - Test rapid version check cycles (reconnect stress test)

2. **BLE Protocol Test:**
   - Monitor BLE packet captures
   - Verify version exchange happens before pairing
   - Confirm disconnect on major version mismatch

---

## JPL Compliance

✅ **Rule #1 (No dynamic allocation):** All version structures statically allocated (8 bytes)
✅ **Rule #2 (Fixed loop bounds):** Version exchange has 5-second timeout
✅ **Rule #5 (Explicit error checking):** All BLE operations return esp_err_t
✅ **Rule #6 (No unbounded waits):** Motor task timeout for version check result
✅ **Rule #8 (Defensive logging):** All version mismatches logged with details

---

## Benefits Summary

✅ **Zero Maintenance:** Git hash automatically embedded at build time
✅ **Traceable:** Hash maps to exact git commit for debugging
✅ **Flexible:** Three strictness levels for different deployment scenarios
✅ **Safe:** Rejects incompatible firmware before bilateral stimulation starts
✅ **User-Friendly:** Clear LED patterns indicate version issues
✅ **Bidirectional:** Both devices show same warning even if one has older firmware
✅ **Backward Compatible:** Graceful handling of older firmware without version checking
✅ **Production Ready:** STRICT mode for field deployment, DISABLED for development

---

## Alternatives Considered

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Git Commit Hash** | Automatic, deterministic, traceable | Requires git during build | ✅ **Selected** |
| **Manual Versioning** | Simple to understand | Error-prone (forget to bump), not traceable | ❌ Rejected |
| **ESP-IDF App Description** | Built-in metadata structure | SHA-256 hash too large for BLE (32 bytes) | ❌ Rejected (alternative) |
| **Random Build Seed** | Meets user request | Not traceable, no semantic versioning | ❌ Rejected |
| **Compilation Timestamp** | Automatic | Non-deterministic (same code = different hash) | ❌ Rejected |
| **Single Strictness Mode** | Simplest | Not flexible for field updates | ❌ Rejected |
| **Pre-Connection Check** | Fails faster | Advertising packet size constraints | ⚠️ Alternative (not recommended) |

---

## Modified Files (Planned)

| File | Changes | Lines |
|------|---------|-------|
| `platformio.ini` | Build flags for git hash and version | ~30 lines |
| `src/ble_manager.h` | Version structures, compatibility enum | ~50 lines |
| `src/ble_manager.c` | Version exchange, compatibility evaluation | ~150 lines |
| `src/motor_task.c` | VERSION_CHECK and VERSION_BLINK states | ~100 lines |
| `src/motor_task.h` | New message type MSG_VERSION_CHECK_RESULT | ~10 lines |
| `test/PHASE_3_COMMAND_CONTROL_IDEAS.md` | Update for version checking | Documentation |

**Total:** ~340 lines of new code across 5 files

---

## Build Environments

```ini
# Production build (strict version checking - default)
pio run -e xiao_esp32c6 -t upload

# Development build (version checking disabled)
pio run -e xiao_esp32c6_allow_mismatch -t upload

# Field update build (compatible version checking - minor patches allowed)
pio run -e xiao_esp32c6_compatible -t upload
```

---

## Status

⏳ **APPROVED** - Design complete, implementation pending
🎯 **Target:** Phase 2 completion (before hardware deployment)
📋 **Dependencies:** AD039 (Time Synchronization) - provides infrastructure for timestamp verification

---

## Next Steps

1. ✅ **AD040 Created** - Architecture documented
2. ⏳ **Implementation:**
   - Add build flags to platformio.ini
   - Implement version structures in ble_manager.h
   - Add compatibility evaluation logic to ble_manager.c
   - Update motor task states for version checking
   - Add BLE characteristic for version exchange
3. ⏳ **Testing:**
   - Unit test compatibility matrix
   - Integration test with mismatched firmware
   - Hardware validation with two devices
4. ⏳ **Documentation:**
   - Update CLAUDE.md with version checking section
   - Add build environment examples to BUILD_COMMANDS.md
   - Create troubleshooting guide for version mismatches

---

**Document prepared with assistance from Claude Sonnet 4 (Anthropic)**
