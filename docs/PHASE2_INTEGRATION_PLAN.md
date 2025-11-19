# Phase 2 Time Synchronization - Integration Plan

**Created:** 2025-11-19
**Status:** Planning Complete - Ready for Implementation
**Branch:** `phase2-time-sync`
**Goal:** Integrate hybrid time sync module with existing BLE and motor systems

---

## Executive Summary

Phase 2 core time sync module is **complete and committed**. This document provides a step-by-step integration plan for connecting the time sync module to the BLE manager, motor task, and creating validation tests.

**Current Status:**
- ✅ `src/time_sync.h` - API complete (14 functions)
- ✅ `src/time_sync.c` - Implementation complete (JPL compliant)
- ✅ `docs/PHASE2_TIER1_REVIEW.md` - Documentation checklist created
- ⏳ BLE integration - **Next step**
- ⏳ Motor task integration - After BLE
- ⏳ Test environment - After motor task

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BLE Manager (ble_manager.c)              │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │ Bilateral Control Service (Peer-to-Peer)          │    │
│  │                                                     │    │
│  │  • Battery Level (existing)                        │    │
│  │  • MAC Address (existing)                          │    │
│  │  • Device Role (existing)                          │    │
│  │  • Time Sync Beacon (NEW - Phase 2) ◄──────────┐  │    │
│  └─────────────────────────────────────────────────┼──┘    │
│                                                     │       │
└─────────────────────────────────────────────────────┼───────┘
                                                      │
                                    ┌─────────────────▼───────────────────┐
                                    │   Time Sync Module (time_sync.c)    │
                                    │                                      │
                                    │  • Generate beacons (SERVER)         │
                                    │  • Process beacons (CLIENT)          │
                                    │  • Track quality metrics             │
                                    │  • Adaptive interval adjustment      │
                                    │  • Drift detection                   │
                                    └─────────────────┬───────────────────┘
                                                      │
┌─────────────────────────────────────────────────────┼───────┐
│                    Motor Task (motor_task.c)                │
│                                                     │       │
│  • Get synchronized time ◄──────────────────────────┘       │
│  • Calculate cycle position                                 │
│  • Coordinate bilateral activation                          │
│  • Send sync beacons (if SERVER)                            │
│  • Log sync quality                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: BLE Manager Integration

### 1.1 Add Time Sync UUID

**File:** `src/ble_manager.c`
**Location:** After line 82 (after `uuid_bilateral_role`)

```c
// Phase 2: Time synchronization (AD036)
static const ble_uuid128_t uuid_bilateral_time_sync = BLE_UUID128_INIT(
    0x04, 0x01, 0xe7, 0xe5, 0x7d, 0x26, 0x88, 0x9e,
    0x0a, 0x4f, 0x29, 0x98, 0xbe, 0xe9, 0xca, 0x4b);
// UUID: 4BCAE9BE-9829-4F0A-9E88-267DE5E70104
```

**Rationale:**
- Follows existing UUID pattern (Bilateral Service = 0x01 0xNN)
- 0x04 = fourth characteristic in Bilateral service
- Maintains AD032 namespace consistency

### 1.2 Add Time Sync Beacon Storage

**File:** `src/ble_manager.c`
**Location:** Add to state variables section (after line 220)

```c
// Phase 2: Time sync beacon (16 bytes, statically allocated per JPL Rule 1)
static time_sync_beacon_t g_time_sync_beacon = {0};
static SemaphoreHandle_t time_sync_beacon_mutex = NULL;
```

**JPL Compliance:**
- ✅ Rule 1: Static allocation (no malloc)
- ✅ Rule 6: Mutex protection for thread safety

### 1.3 Add Time Sync Read Handler

**File:** `src/ble_manager.c`
**Location:** Add after bilateral role handlers (after line 950)

```c
// Time Sync Beacon - Read (Phase 2)
static int gatt_bilateral_time_sync_read(uint16_t conn_handle, uint16_t attr_handle,
                                          struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // Only readable by peer devices (not mobile app)
    if (!ble_is_peer_connected()) {
        ESP_LOGW(TAG, "Time sync read attempted by non-peer");
        return BLE_ATT_ERR_READ_NOT_PERMITTED;
    }

    // JPL Rule 6: Bounded mutex wait
    if (xSemaphoreTake(time_sync_beacon_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in time sync read");
        return BLE_ATT_ERR_UNLIKELY;
    }

    time_sync_beacon_t beacon;
    memcpy(&beacon, &g_time_sync_beacon, sizeof(time_sync_beacon_t));
    xSemaphoreGive(time_sync_beacon_mutex);

    ESP_LOGD(TAG, "GATT Read: Time sync beacon (seq: %u, quality: %u%%)",
             beacon.sequence, beacon.quality_score);

    int rc = os_mbuf_append(ctxt->om, &beacon, sizeof(beacon));
    return (rc == 0) ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
}
```

### 1.4 Add Time Sync Write Handler

**File:** `src/ble_manager.c`
**Location:** After time sync read handler

```c
// Time Sync Beacon - Write (Phase 2 - CLIENT receives from SERVER)
static int gatt_bilateral_time_sync_write(uint16_t conn_handle, uint16_t attr_handle,
                                           struct ble_gatt_access_ctxt *ctxt, void *arg) {
    // Only writable by peer devices (not mobile app)
    if (!ble_is_peer_connected()) {
        ESP_LOGW(TAG, "Time sync write attempted by non-peer");
        return BLE_ATT_ERR_WRITE_NOT_PERMITTED;
    }

    time_sync_beacon_t beacon;
    int rc = ble_hs_mbuf_to_flat(ctxt->om, &beacon, sizeof(beacon), NULL);
    if (rc != 0) {
        ESP_LOGE(TAG, "Time sync write: Invalid length");
        return BLE_ATT_ERR_INVALID_ATTR_VALUE_LEN;
    }

    // Get receive timestamp ASAP for accuracy
    uint64_t receive_time_us = esp_timer_get_time();

    // Process beacon via time sync module
    esp_err_t err = time_sync_process_beacon(&beacon, receive_time_us);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to process time sync beacon: %s", esp_err_to_name(err));
        return BLE_ATT_ERR_UNLIKELY;
    }

    ESP_LOGI(TAG, "Time sync beacon received (seq: %u, offset: calculated)",
             beacon.sequence);

    return 0;
}
```

### 1.5 Add Time Sync to Access Router

**File:** `src/ble_manager.c`
**Location:** Add to `gatt_svr_chr_access()` function (after line 1050)

```c
    // Phase 2: Time synchronization
    if (ble_uuid_cmp(uuid, &uuid_bilateral_time_sync.u) == 0) {
        return (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR) ?
               gatt_bilateral_time_sync_read(conn_handle, attr_handle, ctxt, arg) :
               gatt_bilateral_time_sync_write(conn_handle, attr_handle, ctxt, arg);
    }
```

### 1.6 Add Characteristic to Service Definition

**File:** `src/ble_manager.c`
**Location:** Bilateral Control Service definition (line 1081, before terminator)

```c
            {
                .uuid = &uuid_bilateral_time_sync.u,
                .access_cb = gatt_svr_chr_access,
                .flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_NOTIFY,
            },
```

**Flags Rationale:**
- `READ`: Allows peer to query current beacon
- `WRITE`: Allows SERVER to send beacon to CLIENT
- `NOTIFY`: Enables SERVER to push beacons without polling

### 1.7 Add Public API for Motor Task

**File:** `src/ble_manager.h`
**Location:** Add to public API section

```c
/**
 * @brief Update time sync beacon for peer notification (SERVER only)
 *
 * Called by motor_task when sync interval elapsed.
 * Generates new beacon and sends to connected peer.
 *
 * @return ESP_OK on success
 * @return ESP_ERR_INVALID_STATE if not SERVER or no peer connected
 */
esp_err_t ble_send_time_sync_beacon(void);
```

**File:** `src/ble_manager.c`
**Location:** Add implementation in public API section

```c
esp_err_t ble_send_time_sync_beacon(void) {
    if (time_sync_get_role() != TIME_SYNC_ROLE_SERVER) {
        return ESP_ERR_INVALID_STATE;
    }

    if (!ble_is_peer_connected()) {
        return ESP_ERR_INVALID_STATE;
    }

    // Generate beacon via time sync module
    time_sync_beacon_t beacon;
    esp_err_t err = time_sync_generate_beacon(&beacon);
    if (err != ESP_OK) {
        return err;
    }

    // Store for read access
    if (xSemaphoreTake(time_sync_beacon_mutex, pdMS_TO_TICKS(MUTEX_TIMEOUT_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "Mutex timeout in beacon send");
        return ESP_FAIL;
    }
    memcpy(&g_time_sync_beacon, &beacon, sizeof(beacon));
    xSemaphoreGive(time_sync_beacon_mutex);

    // Send via BLE notify
    // TODO: Get attribute handle for time sync characteristic
    // ble_gatts_notify(conn_handle, attr_handle);

    ESP_LOGI(TAG, "Time sync beacon sent (seq: %u, quality: %u%%)",
             beacon.sequence, beacon.quality_score);

    return ESP_OK;
}
```

### 1.8 Initialize Time Sync Mutex

**File:** `src/ble_manager.c`
**Location:** Add to `ble_init()` function

```c
    // Create time sync beacon mutex (Phase 2)
    time_sync_beacon_mutex = xSemaphoreCreateMutex();
    if (time_sync_beacon_mutex == NULL) {
        ESP_LOGE(TAG, "Failed to create time sync mutex");
        return ESP_FAIL;
    }
```

---

## Step 2: Motor Task Integration

### 2.1 Initialize Time Sync Module

**File:** `src/motor_task.c`
**Location:** In `motor_task()` after role assignment

```c
    // Phase 2: Initialize time synchronization
    time_sync_role_t sync_role = (assigned_role == ROLE_SERVER) ?
                                  TIME_SYNC_ROLE_SERVER : TIME_SYNC_ROLE_CLIENT;

    esp_err_t err = time_sync_init(sync_role);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize time sync: %s", esp_err_to_name(err));
        // Continue without time sync (fallback to independent operation)
    } else {
        ESP_LOGI(TAG, "Time sync initialized as %s",
                 (sync_role == TIME_SYNC_ROLE_SERVER) ? "SERVER" : "CLIENT");
    }
```

### 2.2 Establish Connection Sync

**File:** `src/motor_task.c`
**Location:** After peer connection detected

```c
    // Establish initial time sync on peer connection
    if (ble_is_peer_connected()) {
        uint64_t connection_time_us = esp_timer_get_time();
        err = time_sync_on_connection(connection_time_us);
        if (err != ESP_OK) {
            ESP_LOGW(TAG, "Failed to establish connection sync: %s", esp_err_to_name(err));
        }
    }
```

### 2.3 Periodic Sync Update (Main Loop)

**File:** `src/motor_task.c`
**Location:** In main motor loop (every cycle)

```c
    // Phase 2: Update time synchronization
    if (TIME_SYNC_IS_INITIALIZED()) {
        esp_err_t sync_err = time_sync_update();
        if (sync_err != ESP_OK) {
            ESP_LOGD(TAG, "Time sync update failed: %s", esp_err_to_name(sync_err));
        }

        // SERVER: Send beacon if interval elapsed
        if (TIME_SYNC_IS_SERVER() && should_send_sync_beacon()) {
            ble_send_time_sync_beacon();
        }
    }
```

### 2.4 Use Synchronized Time for Motor Timing

**File:** `src/motor_task.c`
**Location:** Replace `esp_timer_get_time()` calls with synchronized time

```c
    // Get synchronized time for bilateral coordination
    uint64_t sync_time_us = 0;
    if (TIME_SYNC_IS_ACTIVE()) {
        err = time_sync_get_time(&sync_time_us);
        if (err != ESP_OK) {
            // Fallback to local time
            sync_time_us = esp_timer_get_time();
            ESP_LOGW(TAG, "Using local time (sync unavailable)");
        }
    } else {
        sync_time_us = esp_timer_get_time();
    }

    // Calculate cycle position for bilateral coordination
    uint32_t cycle_ms = (uint32_t)((sync_time_us / 1000) % motor_cycle_period_ms);
```

### 2.5 Handle Disconnection

**File:** `src/motor_task.c`
**Location:** In peer disconnect handler

```c
    // Handle time sync disconnection
    if (TIME_SYNC_IS_ACTIVE()) {
        err = time_sync_on_disconnection();
        if (err != ESP_OK) {
            ESP_LOGW(TAG, "Time sync disconnect handling failed: %s", esp_err_to_name(err));
        }
    }
```

### 2.6 Log Sync Quality

**File:** `src/motor_task.c`
**Location:** In battery status logging (every 60 seconds)

```c
    // Log time sync quality alongside battery status
    if (TIME_SYNC_IS_ACTIVE()) {
        time_sync_quality_t quality;
        if (time_sync_get_quality(&quality) == ESP_OK) {
            ESP_LOGI(TAG, "Time Sync: offset=%ld μs, drift=%lu μs, quality=%u%%",
                     quality.avg_offset_us,
                     quality.max_drift_us,
                     quality.quality_score);
        }
    }
```

---

## Step 3: Build System Integration

### 3.1 Update CMakeLists.txt

**File:** `src/CMakeLists.txt`
**Action:** Add `time_sync.c` to source list

```cmake
idf_component_register(
    SRCS
        "main.c"
        "motor_task.c"
        "ble_task.c"
        "button_task.c"
        "motor_control.c"
        "ble_manager.c"
        "role_manager.c"
        "time_sync.c"  # NEW - Phase 2
    INCLUDE_DIRS "."
    REQUIRES
        nvs_flash
        driver
        esp_timer
        led_strip
        bt
        esp_adc
)
```

### 3.2 Verify sdkconfig Settings

**File:** `sdkconfig.xiao_esp32c6`
**Verify:** Ensure sufficient task stack sizes

```ini
# Time sync requires accurate timing
CONFIG_FREERTOS_HZ=1000

# Ensure NimBLE has sufficient resources for notifications
CONFIG_BT_NIMBLE_MAX_CONNECTIONS=2
CONFIG_BT_NIMBLE_ATT_PREFERRED_MTU=256
```

---

## Step 4: Test Environment Creation

### 4.1 Create Test Program

**File:** `test/time_sync_validation_test.c`
**Purpose:** Standalone test for time sync accuracy

**Test Cases:**
1. **Connection Sync Test**
   - Both devices record connection timestamp
   - Verify initial offset < 1ms

2. **Beacon Exchange Test**
   - SERVER generates beacon every 10s
   - CLIENT processes and calculates offset
   - Verify offset remains < 50ms over 5 minutes

3. **Drift Compensation Test**
   - Simulate 2-minute disconnect
   - Calculate expected drift (±10 PPM)
   - Verify actual drift within specification

4. **Quality Metrics Test**
   - Track quality score over time
   - Verify exponential backoff (10s→60s)
   - Test resync on quality degradation

5. **Disconnection Handling Test**
   - Force disconnect during operation
   - Verify continued sync using frozen state
   - Measure actual drift vs expected

### 4.2 Hardware Validation Plan

**Equipment Required:**
- 2× XIAO ESP32-C6 devices
- 2× USB cables for monitoring
- 1× Oscilloscope (optional, for precise timing)
- 1× Mobile phone with nRF Connect (BLE monitoring)

**Test Procedure:**
1. Flash both devices with Phase 2 firmware
2. Power on within 30s (pairing window)
3. Monitor serial logs for:
   - "Peer discovered"
   - "Time sync established"
   - Sync quality logs every 60s
4. Verify bilateral motor coordination:
   - Motors alternate correctly
   - No overlap observed
   - Timing accuracy within ±100ms
5. Test disconnect/reconnect:
   - Power cycle one device
   - Verify automatic reconnection
   - Check sync re-establishment

---

## Step 5: Documentation Updates

### 5.1 Update CLAUDE.md

**Sections to Update:**
- Version → v0.3.0
- Project Phase → Phase 2 Complete
- Add "Time Synchronization" section
- Document hybrid sync approach
- Add build commands for Phase 2

### 5.2 Update docs/architecture_decisions.md

**New Architecture Decision:**

```markdown
## AD036: Hybrid Time Synchronization Architecture

**Status:** Implemented (Phase 2)
**Date:** 2025-11-19
**Context:** Bilateral motor coordination requires sub-second timing accuracy

**Decision:** Implement hybrid time sync combining:
1. Initial connection sync (< 1ms accuracy)
2. Periodic sync beacons (10-60s adaptive intervals)
3. Quality-based interval adjustment

**Consequences:**
- ✅ Achieves ±100ms accuracy (AD029)
- ✅ Battery efficient (< 0.5% overhead)
- ✅ Graceful degradation on disconnect
- ✅ JPL compliant implementation
```

**Update Existing:**
- AD028: Revise command-and-control with hybrid sync details
- AD029: Document achieved timing accuracy

### 5.3 Update docs/requirements_spec.md

**Add Functional Requirement:**

```markdown
### FR0XX: Time Synchronization

**Priority:** P1 (Critical for bilateral operation)
**Status:** Implemented (Phase 2)

The system shall synchronize time between peer devices with:
- Initial connection accuracy: < 1ms
- Sustained accuracy: ±100ms over 20-minute session
- Sync interval: Adaptive 10-60s based on quality
- Graceful degradation: Continue operation using last sync on disconnect

**Rationale:** Ensures non-overlapping bilateral stimulation (FR002)
```

---

## Implementation Checklist

### Phase 2.1: BLE Integration
- [ ] Add time sync UUID to ble_manager.c
- [ ] Implement read/write handlers
- [ ] Add characteristic to service definition
- [ ] Create `ble_send_time_sync_beacon()` API
- [ ] Initialize time sync mutex
- [ ] Test: Compile without errors
- [ ] Test: GATT service appears in nRF Connect

### Phase 2.2: Motor Task Integration
- [ ] Initialize time sync module based on role
- [ ] Establish connection sync on peer connect
- [ ] Add sync update to main loop
- [ ] Replace timing calls with `time_sync_get_time()`
- [ ] Handle disconnection events
- [ ] Add sync quality logging
- [ ] Test: Compile without errors
- [ ] Test: Serial logs show sync messages

### Phase 2.3: Build System
- [ ] Update CMakeLists.txt
- [ ] Verify sdkconfig settings
- [ ] Test: Clean build succeeds
- [ ] Test: Flash to hardware

### Phase 2.4: Validation
- [ ] Create `time_sync_validation_test.c`
- [ ] Run connection sync test
- [ ] Run beacon exchange test
- [ ] Run drift compensation test
- [ ] Run quality metrics test
- [ ] Run disconnection handling test
- [ ] Document test results

### Phase 2.5: Documentation
- [ ] Update CLAUDE.md
- [ ] Create AD036
- [ ] Update AD028 and AD029
- [ ] Update requirements_spec.md
- [ ] Update PHASE2_TIER1_REVIEW.md checkboxes
- [ ] Create SESSION_SUMMARY_PHASE_2.md

---

## Risk Mitigation

### Risk 1: BLE Notification Latency
**Impact:** Sync beacons delayed > 100ms
**Mitigation:** Use WRITE instead of NOTIFY if latency too high
**Fallback:** Increase sync frequency to compensate

### Risk 2: Crystal Drift Exceeds Spec
**Impact:** Devices drift > ±10 PPM
**Mitigation:** Decrease max sync interval from 60s to 30s
**Fallback:** Force resync if drift exceeds 50ms

### Risk 3: Mutex Deadlock
**Impact:** System hangs waiting for time sync mutex
**Mitigation:** All mutexes have 100ms timeout (JPL Rule 6)
**Fallback:** Log error and continue with stale data

### Risk 4: Memory Constraints
**Impact:** Stack overflow in time sync task
**Mitigation:** All data statically allocated, no recursion
**Validation:** Monitor stack watermarks

---

## Success Criteria

Phase 2 is considered complete when:

1. ✅ **Code Quality:**
   - All code compiles without warnings
   - JPL compliance verified for all new code
   - No static analysis warnings

2. ✅ **Functional:**
   - Two devices successfully pair and sync
   - Bilateral motors coordinate correctly
   - Sync maintained over 20-minute session
   - Graceful handling of disconnects

3. ✅ **Performance:**
   - Timing accuracy: ±100ms verified
   - Sync interval: Adaptive 10-60s observed
   - Battery overhead: < 1% measured

4. ✅ **Documentation:**
   - All Tier 1 docs updated
   - Integration plan complete
   - Test results documented

---

## Next Session Quick Start

When resuming Phase 2 implementation:

1. **Review this document** - Re-familiarize with integration plan
2. **Start at Phase 2.1** - Begin with BLE integration
3. **Follow checklist order** - Complete each section before moving on
4. **Test incrementally** - Verify each integration step compiles
5. **Commit frequently** - Small, focused commits with clear messages

**Estimated Time:**
- Phase 2.1 (BLE): 2-3 hours
- Phase 2.2 (Motor): 1-2 hours
- Phase 2.3 (Build): 30 minutes
- Phase 2.4 (Validation): 3-4 hours
- Phase 2.5 (Docs): 1-2 hours
- **Total: 8-12 hours**

---

## References

- **Time Sync Module:** `src/time_sync.h`, `src/time_sync.c`
- **BLE Manager:** `src/ble_manager.c`, `src/ble_manager.h`
- **Motor Task:** `src/motor_task.c`, `src/motor_task.h`
- **Architecture Decisions:** `docs/architecture_decisions.md`
- **Requirements:** `docs/requirements_spec.md`
- **Tier 1 Review:** `docs/PHASE2_TIER1_REVIEW.md`

---

**Document Version:** 1.0
**Last Updated:** 2025-11-19
**Author:** Claude Code (Phase 2 Planning)
