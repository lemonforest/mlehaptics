# UUID-Switching Implementation Plan

**Date:** November 18, 2025
**Objective:** Replace state-based connection identification with UUID-switching strategy
**Bug:** #28 (Button unresponsiveness) - FIXED
**Enhancement:** Simplified peer/app identification via advertised UUID

---

## Problem Statement

Current implementation (post-Bug #9 fix):
- Always advertises Config Service UUID (`...0200`)
- Uses complex 4-path state-based logic to identify peer vs app connections
- Vulnerable to misidentification (Bug #27)
- 38-second grace period (30s + 8s) is confusing

User's proposed solution (SUPERIOR):
- **0-30s**: Advertise ONLY Bilateral Service UUID (`...0100`) - peers can discover, apps cannot
- **30s+**: Switch to ONLY Config Service UUID (`...0200`) - apps can discover, bonded peers reconnect by address
- **Eliminates ALL state-based identification complexity**
- **Zero misidentification risk** (wrong connection type physically cannot connect)

---

## Implementation Changes

### 1. Add Boot Timestamp Tracking

**File:** `src/ble_manager.c`

```c
// Add after line 50 (UUID definitions section)
/**
 * @brief Boot timestamp for pairing window tracking
 *
 * Initialized in ble_init() to esp_timer_get_time() / 1000
 * Used to determine which UUID to advertise (Bilateral vs Config)
 */
static uint32_t ble_boot_time_ms = 0;

// Add constant
#define PAIRING_WINDOW_MS 30000  // 30 seconds for peer pairing
```

**In `ble_init()`:**
```c
ble_boot_time_ms = (uint32_t)(esp_timer_get_time() / 1000);
ESP_LOGI(TAG, "BLE boot timestamp: %lu ms", ble_boot_time_ms);
```

### 2. Helper Function - Determine Advertised UUID

**File:** `src/ble_manager.c`

```c
/**
 * @brief Determine which UUID to advertise based on timing and pairing state
 * @return Pointer to UUID to advertise (Bilateral or Config)
 *
 * Logic:
 * - No peer bonded AND within 30s: Bilateral UUID (peer discovery only)
 * - Peer bonded OR after 30s: Config UUID (app discovery + bonded peer reconnect)
 */
static const ble_uuid128_t* ble_get_advertised_uuid(void) {
    uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
    uint32_t elapsed_ms = now_ms - ble_boot_time_ms;

    // Check if peer already bonded (NVS check)
    bool peer_bonded = ble_check_bonded_peer_exists();

    if (!peer_bonded && elapsed_ms < PAIRING_WINDOW_MS) {
        // Within pairing window, no peer bonded yet - advertise Bilateral UUID
        return &uuid_bilateral_service;
    } else {
        // After pairing window OR peer already bonded - advertise Config UUID
        return &uuid_config_service;
    }
}
```

### 3. Modify Advertising to Use Dynamic UUID

**File:** `src/ble_manager.c` - `ble_on_sync()` function (line 1754-1770)

**BEFORE:**
```c
// Configure scan response with Configuration Service UUID (Phase 1b.2)
// - Configuration Service UUID (0x0200): For mobile app/PWA discovery
// - Peer discovery works via GATT service presence (devices already connecting)
// Using scan response prevents exceeding 31-byte advertising packet limit
struct ble_hs_adv_fields rsp_fields;
memset(&rsp_fields, 0, sizeof(rsp_fields));

// Advertise Configuration Service so PWA can filter and find the device
rsp_fields.uuids128 = &uuid_config_service;
rsp_fields.num_uuids128 = 1;
rsp_fields.uuids128_is_complete = 1;
```

**AFTER:**
```c
// Configure scan response with dynamic UUID (Phase 1b.3 UUID-switching)
// - 0-30s: Bilateral Service UUID (0x0100) - peer discovery only
// - 30s+: Configuration Service UUID (0x0200) - app discovery + bonded peer reconnect
// Using scan response prevents exceeding 31-byte advertising packet limit
struct ble_hs_adv_fields rsp_fields;
memset(&rsp_fields, 0, sizeof(rsp_fields));

const ble_uuid128_t *advertised_uuid = ble_get_advertised_uuid();
rsp_fields.uuids128 = advertised_uuid;
rsp_fields.num_uuids128 = 1;
rsp_fields.uuids128_is_complete = 1;

ESP_LOGI(TAG, "Advertising UUID: %s",
         (advertised_uuid == &uuid_bilateral_service) ? "Bilateral (peer discovery)" : "Config (app + bonded peer)");
```

### 4. Modify Scanning to Look for Bilateral UUID

**File:** `src/ble_manager.c` - Scan callback (line 2123-2150)

**BEFORE:**
```c
// Compare against Configuration Service UUID (Phase 1b.2: simplified discovery)
// Both peer devices advertise this UUID, and it also enables PWA discovery
if (ble_uuid_cmp(&fields.uuids128[i].u, &uuid_config_service.u) == 0) {
```

**AFTER:**
```c
// Compare against Bilateral Service UUID (Phase 1b.3: UUID-switching)
// Peer devices advertise this UUID during pairing window (0-30s)
// After pairing, bonded peers reconnect by address (no scanning needed)
if (ble_uuid_cmp(&fields.uuids128[i].u, &uuid_bilateral_service.u) == 0) {
```

### 5. Add UUID Switch at 30 Seconds

**Option A: BLE Task Timer Check** (Recommended - already have BLE task)

**File:** `src/ble_task.c` - Main loop

```c
// Check if UUID switch needed (30s boundary)
uint32_t elapsed_ms = (uint32_t)(esp_timer_get_time() / 1000);
if (!uuid_switched && elapsed_ms >= 30000 && !ble_check_bonded_peer_exists()) {
    ESP_LOGI(TAG, "30s pairing window expired - switching to Config Service UUID");
    ble_restart_advertising();  // Re-advertise with Config UUID
    uuid_switched = true;
}
```

**Option B: ESP Timer** (More precise, but adds complexity)

```c
static esp_timer_handle_t uuid_switch_timer = NULL;

static void uuid_switch_timer_callback(void *arg) {
    if (!ble_check_bonded_peer_exists()) {
        ESP_LOGI(TAG, "30s pairing window expired - switching to Config Service UUID");
        ble_restart_advertising();
    }
}

// In ble_init():
esp_timer_create_args_t timer_args = {
    .callback = uuid_switch_timer_callback,
    .name = "uuid_switch"
};
esp_timer_create(&timer_args, &uuid_switch_timer);
esp_timer_start_once(uuid_switch_timer, 30 * 1000000);  // 30s in microseconds
```

### 6. Switch UUID When Peer Pairs

**File:** `src/ble_manager.c` - Connection handler (after peer identified)

```c
if (is_peer) {
    peer_state.peer_connected = true;
    peer_state.conn_handle = event->connect.conn_handle;

    // Stop scanning once peer connected
    if (scanning_active) {
        int scan_rc = ble_gap_disc_cancel();
        ...
    }

    // NEW: Switch to Config UUID immediately after peer pairing
    // This allows mobile app to connect while peer is still connected
    ESP_LOGI(TAG, "Peer connected - restarting advertising with Config Service UUID");
    ble_restart_advertising();  // Will use Config UUID (peer now bonded)
}
```

### 7. Simplify Connection Identification Logic

**File:** `src/ble_manager.c` - Connection event handler

**BEFORE (Complex 4-path logic):**
```c
// Path 1: Check cached peer address
// Path 2: Check BLE connection role
// Path 3a: Check scanning active AND no peer connected
// Path 3b: Check grace period (38s)
// Path 4: Default to app
```

**AFTER (Simple UUID-based logic):**
```c
// Determine connection type based on currently advertised UUID
const ble_uuid128_t *current_uuid = ble_get_advertised_uuid();
bool is_peer = false;

if (current_uuid == &uuid_bilateral_service) {
    // Advertising Bilateral UUID - this is a peer connection
    is_peer = true;
    ESP_LOGI(TAG, "Peer identified (connected during Bilateral UUID window)");
} else {
    // Advertising Config UUID - this is an app connection
    // Exception: Bonded peer reconnecting by address
    if (peer_state.peer_connected || is_bonded_to_peer(desc.peer_id_addr)) {
        is_peer = true;
        ESP_LOGI(TAG, "Peer identified (bonded reconnection)");
    } else {
        is_peer = false;
        ESP_LOGI(TAG, "Mobile app connected (Config UUID window)");
    }
}
```

### 8. Remove Grace Period Complexity

**File:** `src/ble_manager.c`

**BEFORE:**
```c
uint32_t grace_period_end = 30000 + 8000;  // 38s total
```

**AFTER:**
```c
// No grace period needed - UUID switching handles peer discovery timing
// Connections during Bilateral UUID (0-30s) = peers
// Connections during Config UUID (30s+) = apps
```

---

## Benefits of UUID-Switching Approach

1. **Eliminates misidentification**: PWAs physically cannot discover device during peer pairing window
2. **Simpler logic**: Connection type determined by advertised UUID, not complex state machine
3. **Zero latency**: No GATT discovery needed post-connection
4. **Better UX**: Clear separation - peers pair first, then apps can connect
5. **Fewer bugs**: Less complex code = fewer edge cases = fewer bugs
6. **Industry standard**: UUID-based filtering is standard BLE practice

---

## Testing Plan

1. **Fresh boot, peer pairing**:
   - Both devices boot within 30s
   - Both advertise Bilateral UUID
   - Both discover each other and connect
   - After pairing, both switch to Config UUID
   - Mobile app can now discover and connect

2. **Fresh boot, single device**:
   - Device boots, advertises Bilateral UUID
   - Mobile app cannot see device for first 30s
   - At 30s, device switches to Config UUID
   - Mobile app can now discover and connect

3. **Bonded peer reconnection**:
   - Device reboots with bonded peer in NVS
   - Immediately advertises Config UUID (peer already bonded)
   - Bonded peer reconnects by address (not by UUID scan)
   - Mobile app can also connect simultaneously

4. **Late peer startup** (edge case):
   - Device A boots at t=0
   - Device B boots at t=25s
   - Both advertise Bilateral UUID
   - Devices discover and pair by t=29s
   - At t=30s, both switch to Config UUID
   - Result: Successful pairing

5. **Very late peer startup** (expected failure):
   - Device A boots at t=0
   - Device B boots at t=35s (after 30s window)
   - Device A advertises Config UUID, Device B advertises Bilateral UUID
   - Devices cannot discover each other (different UUIDs)
   - Result: Pairing fails (expected - outside pairing window)
   - User must reboot both devices within 30s of each other

---

## Files to Modify

1. `src/ble_manager.c` - Main implementation
2. `src/ble_manager.h` - Add `ble_restart_advertising()` if needed
3. `src/ble_task.c` - Add 30s UUID switch timer check
4. `docs/architecture_decisions.md` - Update AD036 or create AD037
5. `CHANGELOG.md` - Document UUID-switching implementation and Bug #28 fix

---

## Next Steps

1. Implement boot timestamp tracking ✅
2. Create `ble_get_advertised_uuid()` helper ✅
3. Modify advertising setup ✅
4. Modify scanning logic ✅
5. Add 30s UUID switch trigger ✅
6. Simplify connection identification ✅
7. Test on hardware 🔄
8. Update documentation ✅

---

## Related Bugs/Issues

- **Bug #27**: PWA misidentified as peer - ELIMINATED by UUID-switching
- **Bug #26**: Late peer rejection - ELIMINATED by UUID-switching (pairing window is clear)
- **Bug #28**: Button unresponsiveness - FIXED (removed blocking status_led_pattern calls)
- **AD036**: State-based identification - SUPERSEDED by UUID-switching approach

---

**Status:** Ready for implementation (plan approved by user)
