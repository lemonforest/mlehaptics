# API Analysis: Potential Redundancies with NimBLE/ESP-IDF

**Date:** 2025-11-20
**Goal:** Identify areas where we're reimplementing functionality that exists in NimBLE or ESP-IDF APIs

---

## 1. State Tracking vs NimBLE APIs

### Current Approach: Manual State Flags
We maintain our own state variables:
```c
// Our manual tracking (ble_manager.c:230-242)
static ble_advertising_state_t adv_state = {
    .advertising_active = false,        // ← Manual flag
    .client_connected = false,          // ← Manual flag
    .conn_handle = BLE_HS_CONN_HANDLE_NONE,
    // ...
};

static bool scanning_active = false;    // ← Manual flag
```

**Usage Count:**
- `advertising_active`: ~30+ references
- `scanning_active`: ~10+ references
- `client_connected`: ~15+ references

### NimBLE Provides:
```c
// Check if advertising is currently active
bool ble_gap_adv_active(void);

// Check if discovery (scanning) is currently active
bool ble_gap_disc_active(void);

// Find connection by handle (returns 0 if exists, error if not)
int ble_gap_conn_find(uint16_t handle, struct ble_gap_conn_desc *out_desc);

// Find connection by address
int ble_gap_conn_find_by_addr(const ble_addr_t *addr, struct ble_gap_conn_desc *out_desc);
```

### Analysis:
✅ **GOOD:** We just added `ble_gap_conn_find()` verification in disconnect handler (lines 1729-1746)

⚠️ **OPPORTUNITY:** We could eliminate most of `advertising_active` and `scanning_active` by querying NimBLE directly

**Concern (from line 2843 comment):**
> "NimBLE's ble_gap_adv_active() can return false transiently during state transitions"

**Recommendation:** Test if this transient behavior actually affects our use cases, or if it's an overoptimization

---

## 2. Connection Management

### Current Approach: Manual Tracking
```c
// Track peer connection
peer_state.peer_connected = true;
peer_state.peer_conn_handle = handle;

// Track app connection
adv_state.client_connected = true;
adv_state.conn_handle = handle;
```

### NimBLE Provides:
```c
// Get descriptor for any active connection
int ble_gap_conn_find(uint16_t handle, struct ble_gap_conn_desc *out_desc);

// The descriptor contains rich metadata:
struct ble_gap_conn_desc {
    ble_addr_t peer_id_addr;    // Peer address
    ble_addr_t peer_ota_addr;   // Over-the-air address
    uint16_t conn_handle;       // Connection handle
    uint8_t role;               // MASTER or SLAVE
    bool bonded;                // Is bonded?
    // ... interval, latency, timeout, etc.
};
```

### Analysis:
✅ **IMPROVEMENT MADE:** Disconnect handler now uses `ble_gap_conn_find()` to verify state (lines 1729-1746)

⚠️ **OPPORTUNITY:** Could we eliminate `peer_connected`/`client_connected` flags entirely?
- Instead of checking flags, just call `ble_gap_conn_find(handle)` when needed
- Would eliminate state sync issues

**Trade-off:** Performance (API call) vs Correctness (no state drift)

---

## 3. Connection Identification (Peer vs App)

### Current Approach: Complex UUID-Based Logic
```c
// Identify connection type by which UUID we're advertising (lines 1530-1551)
const ble_uuid128_t *current_uuid = ble_get_advertised_uuid();

if (current_uuid == &uuid_bilateral_service) {
    is_peer = true;  // Bilateral UUID window
} else {
    // Check cached peer address vs this connection's address
    if (memcmp(addr, cached_addr) == 0 && peer_discovered) {
        is_peer = true;  // Bonded peer reconnecting
    } else {
        is_peer = false;  // Mobile app
    }
}
```

**Complexity:** ~150 lines of connection identification + security logic

### NimBLE Provides:
The connection descriptor already tells us:
```c
struct ble_gap_conn_desc desc;
ble_gap_conn_find(handle, &desc);

// We can check:
desc.bonded          // Is this a bonded device?
desc.peer_id_addr    // Who are they?
desc.role            // MASTER (we connected) or SLAVE (they connected)?
```

### Analysis:
⚠️ **COMPLEX AREA:** Our UUID-switching approach serves multiple purposes:
1. Connection type identification (peer vs app)
2. Pairing window enforcement (first 30 seconds)
3. Security (prevent unwanted connections)

**Question:** Could we simplify by:
- Always advertising Config UUID
- Use bonding status to identify peer (bonded = peer, unbonded = app)?
- Would eliminate UUID-switching complexity

**Trade-off:** Current approach prevents accidental app connections during peer discovery window

---

## 4. Bonding/Pairing Status

### Current Approach: Manual NVS Queries
```c
// Check if device is bonded (lines 1514-1519)
union ble_store_value bond_value;
union ble_store_key bond_key;
memset(&bond_key, 0, sizeof(bond_key));
bond_key.sec.peer_addr = desc.peer_id_addr;
int bond_rc = ble_store_read(BLE_STORE_OBJ_TYPE_OUR_SEC, &bond_key, &bond_value);
bool is_bonded = (bond_rc == 0);
```

**Repeated:** Every time we need to check bonding status

### NimBLE Provides:
```c
// The connection descriptor already includes this!
struct ble_gap_conn_desc desc;
ble_gap_conn_find(handle, &desc);
bool is_bonded = desc.bonded;  // ← Already computed!
```

### Analysis:
✅ **EASY WIN:** Replace manual NVS queries with `desc.bonded` field

**Locations to fix:** Lines 1514-1519, and anywhere else we check bonding

---

## 5. Advertising/Scanning State Consistency

### Current Issue: State Drift
Our manual flags can get out of sync with NimBLE's actual state:
- Connection race conditions (your bug report)
- Advertising stop/start failures
- Scanning state transitions

### NimBLE's Source of Truth:
```c
// Always accurate, never stale
bool adv_active = ble_gap_adv_active();
bool scan_active = ble_gap_disc_active();
```

### Analysis:
⚠️ **RECOMMENDATION:** Replace manual flags with NimBLE queries

**Before:**
```c
if (adv_state.advertising_active) {
    // Do something
}
```

**After:**
```c
if (ble_gap_adv_active()) {
    // Do something - always accurate
}
```

**Benefit:** Eliminates entire class of state sync bugs

---

## 6. Standard BLE Services

### Battery Service
**Current:** Manual ADC reading + percentage calculation
```c
// src/motor_task.c - custom implementation
float battery_v = read_battery_voltage();
int battery_pct = calculate_battery_percentage(battery_v);
```

**Standard BLE:** Battery Service (0x180F)
- UUID 0x180F (Battery Service)
- UUID 0x2A19 (Battery Level characteristic)
- Standard format: uint8 percentage (0-100%)

**Analysis:**
✅ **GOOD:** We already use standard Battery Service UUID and format in GATT characteristics

⚠️ **OPPORTUNITY:** Could use ESP-IDF's Battery Service implementation if available

---

## 7. Time Synchronization

### Current: Custom NTP-Style Protocol
**Implementation:** ~600 lines in `src/time_sync.c`
- Custom beacon format (16 bytes)
- Manual drift calculation
- Custom quality metrics

### BLE Standard: Current Time Service (CTS)
- UUID 0x1805 (Current Time Service)
- UUID 0x2A2B (Current Time characteristic)
- Standardized time format

### Analysis:
⚠️ **CUSTOM IS JUSTIFIED:**
- CTS is for absolute time (wall clock), not synchronization
- Our use case (bilateral motor coordination) requires offset/drift tracking
- No standard BLE service for microsecond-precision peer sync

**Recommendation:** Keep custom implementation

---

## Summary of Opportunities

### High Priority (Easy Wins)

1. **Use `desc.bonded` instead of manual NVS queries** (lines 1514-1519)
   - Eliminates ~10 lines of code per check
   - More reliable (NimBLE's cached value)

2. **Replace advertising/scanning flags with NimBLE queries**
   - `adv_state.advertising_active` → `ble_gap_adv_active()`
   - `scanning_active` → `ble_gap_disc_active()`
   - Eliminates state drift bugs

3. **Use `ble_gap_conn_find()` more aggressively**
   - Already started with disconnect verification
   - Could eliminate `peer_connected`/`client_connected` flags

### Medium Priority (Moderate Refactor)

4. **Simplify connection identification logic**
   - Consider always advertising Config UUID
   - Use bonding status as primary identifier
   - Would eliminate UUID-switching complexity

### Low Priority (Works Fine)

5. **Time sync implementation** - Keep custom (no standard alternative)
6. **Battery service** - Already using standard format

---

## Action Items

**Immediate:**
- [ ] Test `ble_gap_adv_active()` reliability (address line 2843 concern)
- [ ] Replace `desc.bonded` checks (easy win)
- [ ] Audit all `advertising_active`/`scanning_active` usage

**Short-term:**
- [ ] Refactor to use NimBLE queries as source of truth
- [ ] Remove redundant state tracking variables
- [ ] Add integration tests for state consistency

**Long-term:**
- [ ] Evaluate UUID-switching simplification
- [ ] Document architectural decisions (API choices)
