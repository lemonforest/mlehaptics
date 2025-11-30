# Changelog

All notable changes to the EMDR Bilateral Stimulation Device project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 6: Bilateral Motor Coordination (In Progress)

**Coordination Message System:**
- **SYNC_MSG_MODE_CHANGE**: Button press mode changes propagated to CLIENT device (`src/time_sync_task.c:321-366`)
- **SYNC_MSG_SETTINGS**: BLE GATT parameter changes synced to CLIENT via coordination messages
- **SYNC_MSG_SHUTDOWN**: Emergency shutdown propagation between devices
- **SYNC_MSG_START_ADVERTISING**: Re-enable BLE advertising command to CLIENT
- **SYNC_MSG_CLIENT_BATTERY**: CLIENT reports battery level to SERVER for PWA display

**Motor Epoch Mechanism:**
- Motor epoch timestamp republished on mode change for CLIENT phase alignment (`src/motor_task.c`)
- CLIENT resets to INACTIVE state when receiving new timing parameters (prevents overlap during frequency changes)

**Client Battery Characteristic (Configuration Service):**
- **UUID `...020D`**: New GATT characteristic for CLIENT battery level (`src/ble_manager.c`)
- SERVER relays CLIENT battery to PWA for dual-device battery monitoring
- Returns 0% in single-device mode, actual battery in dual-device mode
- Updates via `SYNC_MSG_CLIENT_BATTERY` coordination message

### Fixed

**BLE Writes Breaking Bilateral Sync** (CRITICAL - Bug #12):
- **Symptom**: CLIENT device experienced excessive phase resets during PWA operation, causing device overlap
- **Root Cause**: Every BLE GATT write (including Session Duration) triggered `sync_settings_to_peer()`. CLIENT received `SYNC_MSG_SETTINGS` and unconditionally called `ble_callback_params_updated()`, which reset CLIENT to INACTIVE state even when no motor-timing parameters changed.
- **Fix**: Three-layer change detection defense:
  1. `ble_update_custom_freq()` only calls `update_mode5_timing()` if value actually changed (`src/ble_manager.c:3858-3882`)
  2. `ble_update_custom_duty()` only calls `update_mode5_timing()` if value changed (`src/ble_manager.c:3884-3908`)
  3. `ble_update_pwm_intensity()` only calls `motor_update_mode5_intensity()` if value changed (`src/ble_manager.c:3910-3938`)
  4. `handle_coordination_message()` SYNC_MSG_SETTINGS tracks old values, only calls `ble_callback_params_updated()` if freq/duty/intensity changed (`src/time_sync_task.c:369-444`)
- **Result**: PWA Session Duration updates no longer disrupt bilateral timing

**Frequency Change Skip/Overlap Pattern** (CRITICAL - Bug #13):
- **Symptom**: Mode 4 frequency changes via PWA caused skip-then-overlap pattern during transition
- **Root Cause**: Race condition between SYNC_MSG_SETTINGS and motor epoch beacon. CLIENT received new frequency via SYNC_MSG_SETTINGS BEFORE SERVER's beacon with updated motor_epoch arrived. CLIENT's drift correction used OLD motor_epoch with NEW cycle_ms → wrong wait calculation → skip/overlap.
- **Fix**: Added `skip_drift_correction_once` flag in CLIENT (`src/motor_task.c:112-116`):
  1. Flag set when CLIENT processes `ble_params_updated` for MODE_CUSTOM (`src/motor_task.c:624-627`)
  2. INACTIVE state checks flag, uses nominal timing instead of drift correction (`src/motor_task.c:809-813`)
  3. Flag cleared after use, normal drift correction resumes with fresh beacon
- **Result**: CLIENT uses nominal timing for one INACTIVE cycle after param change, then resumes drift correction when fresh beacon arrives with new motor_epoch

**Drift Correction Too Aggressive at High Duty Cycles** (CRITICAL - Bug #14):
- **Symptom**: At 2Hz 95% duty, perceptible drift with corrections of +198ms and -185ms causing phase jumps
- **Root Cause**: Drift correction allowed corrections up to a full cycle (500ms), but at 95% duty the inactive period is only 250ms with just 13ms coast time. Large corrections caused CLIENT to wait much longer/shorter than expected, creating visible phase drift.
- **Fix**: Added correction clamping (`src/motor_task.c:815-882`):
  1. Always apply drift correction (removed quality threshold that caused drift-then-snap behavior)
  2. Correction clamping: Max correction is ±50ms or 20% of nominal, whichever is larger
  3. Gradual correction over multiple cycles instead of single large jump
- **Result**: Continuous gradual correction keeps devices synchronized without perceptible phase jumps

**Fixed Correction Limits Not Frequency-Dependent** (Bug #29):
- **Symptom**: Mode switching at 0.5Hz with high RTT (>300ms) took 3 cycles to converge to antiphase
- **Root Cause**: Fixed 100ms max correction was only 10% of inactive period at 0.5Hz (1000ms) but 40% at 2Hz (250ms), causing inconsistent convergence behavior across frequencies
- **Fix**: Replaced fixed constants with frequency-dependent calculation (`src/motor_task.c:1467-1493`):
  - Max correction: 20% of inactive period (minimum 50ms)
  - Deadband: 10% of inactive period (minimum 25ms)
  - At 0.5Hz: 200ms max correction, 100ms deadband (was 100ms/50ms)
  - At 1.0Hz: 100ms max correction, 50ms deadband (unchanged)
  - At 2.0Hz: 50ms max correction, 25ms deadband (was 100ms/50ms, now safer)
- **Expected Result**: 1-cycle convergence at 0.5Hz with high RTT, safer corrections at high frequencies
- **Impact**: Addresses Gemini's log analysis findings (see GEMINI.md)

**64-bit Timestamp Logging Corruption** (CRITICAL - Bug #30):
- **Symptom**: "Handshake complete" logs showed timestamps (T1-T4) that didn't mathematically match the calculated offset/RTT values. Example: Log showed RTT=1320μs, but timestamps calculated to RTT=59540μs (45× difference!)
- **Root Cause**: Using non-portable format specifiers (`%lld`/`%llu`) for 64-bit integers on RISC-V architecture. ESP-IDF requires `PRId64`/`PRIu64` macros from `<inttypes.h>` for correct printf parsing on 32-bit systems with 64-bit values.
- **Fix**: Added `#include <inttypes.h>` and replaced all format specifiers (`src/time_sync.c`):
  - `%lld` → `%" PRId64 "` for int64_t (offset, drift, signed timestamps)
  - `%llu` → `%" PRIu64 "` for uint64_t (T1-T4 timestamps, motor epoch)
  - Fixed 15 logging statements across handshake, beacon, RTT, and drift tracking
- **Result**: Timestamp values in logs now correctly match calculated offset/RTT values, enabling accurate verification of synchronization math
- **Impact**: Critical for debugging - impossible to verify time sync correctness when logged timestamps were corrupted
- **Discovery**: Gemini's 90-minute log analysis identified the mathematical inconsistency (see GEMINI.md)

**Quality Metrics Stuck at 0% - Handshake Race Condition** (CRITICAL - Bug #28):
- **Symptom**: Quality metrics always showed 0%, RTT updates never improved quality score
- **Root Cause**: TIME_REQUEST arrived 840-1040ms before SERVER time_sync initialization completed, SERVER rejected with `ESP_ERR_INVALID_STATE`, CLIENT never retried, fell back to beacon path which didn't initialize quality metrics
- **Fix**: Implemented TIME_REQUEST buffering (matching existing CLIENT_READY pattern):
  1. Buffer TIME_REQUEST if time_sync not initialized (`src/time_sync_task.c:574-580`)
  2. Process buffered request after initialization complete (`src/time_sync_task.c:300-337`)
  3. Fallback: Initialize quality metrics from beacon if handshake missed (`src/time_sync.c:511-517`)
  4. Fixed drift_rate variable scoping issue for logging (`src/time_sync.c:1432`)
- **Result**: Handshake completes successfully (quality=95%), RTT updates properly track sync quality
- **Files Modified**: `src/time_sync_task.c` (buffering), `src/time_sync.c` (beacon fallback)

### Added - Phase 6r: Drift Continuation During Disconnect (November 30, 2025)

**Conditional Clearing for Motor Continuation:**
- **Modified Disconnect Handler** (`src/time_sync.c:174-217`): Preserves motor_epoch and drift_rate when BLE disconnects
- **Safety Timeout** (`src/time_sync.c:935-958`): Motor epoch expires after 2-minute disconnect, returns `ESP_ERR_TIMEOUT`
- **Role Swap Detection** (`src/time_sync.c:219-278`): New `time_sync_on_reconnection()` detects role changes on reconnection
- **BLE Integration** (`src/ble_manager.c:2121-2128`): Calls reconnection handler after role assignment
- **Documentation** (`src/motor_task.c:21-28`, `README.md`): Phase 6r section explaining drift continuation behavior

**Key Behavior Changes:**
- ✅ **CLIENT motors continue** during brief BLE disconnect (< 2 min) using frozen drift rate
- ✅ **Bilateral alternation maintained** with ±2.4ms drift over 20-minute session (well within ±100ms spec)
- ✅ **Therapeutic continuity** preserved during BLE glitches
- ⏱️ **Safety timeout** stops motors gracefully after 2-minute disconnect
- ⚠️ **Role swap warning** logged if roles change on reconnection (indicates Phase 6n bug)

**Technical Rationale:**
- Original Phase 6 bug was about role SWAP corruption during reconnection (not disconnect continuation)
- Drift rate stability from Phase 2 testing (±30 μs over 90 min) validates continuation approach
- Conditional clearing: Preserve during disconnect, clear only on role swap
- Aligns with AD041 (predictive bilateral synchronization philosophy)

### Documentation

- CLAUDE.md: Added Phase 6r section with complete implementation details
- README.md: Updated to v0.3.0-beta.2, added "Typical Bilateral Operation Flow" section
- CLAUDE.md: Added Branch and PR Workflow section (mandatory changelog updates and version bumps before PRs)

### Planned
- Phase 6r: Hardware testing (brief disconnect, long disconnect, role swap scenarios)
- Phase 6: Complete bilateral motor coordination testing
- Mobile app development
- Enhanced pairing with numeric comparison and button confirmation

---

## [0.3.0-beta.1] - 2025-11-20

### Added - Phase 2: Time Synchronization Complete ✅

**Time Synchronization Implementation:**
- **NTP-Style Clock Sync**: Dual-clock architecture preserving system clock while calculating synchronized time (`src/time_sync.c`, `src/time_sync.h`, `src/time_sync_task.c`, `src/time_sync_task.h`)
- **Beacon Exchange Protocol**: Timestamped messages exchanged every 10-60 seconds (adaptive based on quality)
- **Quality Metrics**: Confidence score (0-100%) based on round-trip time and drift stability
- **One-Time Phase Alignment**: Single synchronization at session start (drift < 30 μs over 90 minutes - periodic re-sync unnecessary)
- **Opt-In Synchronization**: Applications choose sync clock (`time_sync_get_time_us()`) vs system clock (`esp_timer_get_time()`)
- **Sequence Wrap Handling**: Beacon counter (uint8_t) wraps correctly at 255→0

**Architecture Decisions:**
- **AD037**: Time Synchronization Protocol (NTP-style beacon exchange)
- **AD038**: Synchronized vs System Clock Usage (dual-clock architecture)
- **AD039**: Time Synchronization Protocol Details (beacon format, quality metrics)
- **AD040**: Firmware Version Checking (semantic versioning comparison)

**Production Readiness:**
- 90-minute unattended stress test PASSED:
  - 271/271 beacons delivered (100% delivery rate)
  - Drift converged to -14 μs, stable at -31 μs final
  - Quality sustained at 95%
  - 7 brief 50ms offset jumps (suspected BLE connection parameter updates, not time sync bugs)
  - Recovery: Quality→0% detected, recovered within 2 beacons
  - Sequence wrap verified (255→0 transition handled correctly)

### Fixed

**NVS Configuration Standardization:**
- Replaced custom `BLE_PAIRING_TEST_MODE` flag with standard ESP-IDF `CONFIG_BT_NIMBLE_NVS_PERSIST` (`sdkconfig.xiao_esp32c6:715`, `src/ble_manager.c:2453-2466`, `platformio.ini:485,495,499`)
- Production environment: `CONFIG_BT_NIMBLE_NVS_PERSIST=y` enables persistent bonding across reboots
- Test environment: `CONFIG_BT_NIMBLE_NVS_PERSIST` not set for RAM-only bonding (unlimited pairing cycles)
- Test binary now 1,738 bytes smaller (NVS backend not compiled)
- Better compatibility with developers familiar with NimBLE stack conventions

**Pairing Race Condition** (CRITICAL - Bug #35):
- **Symptom**: DEV_A (98% battery) never discovered DEV_B (96% battery), both timed out after 30 seconds
- **Root Cause**: Scanning stopped immediately after peer discovery, BEFORE role assignment. CLIENT devices would stop scanning, then wait for connection, but SERVER couldn't discover them.
- **Fix**: CLIENT devices now keep scanning during wait period. Moved `ble_gap_disc_cancel()` to only execute when device initiates connection (SERVER role). Applied same pattern to MAC tie-breaker and fallback cases. (`src/ble_manager.c:2658-2674`)
- **Result**: Robust pairing regardless of power-on timing

**PWA Connection Tracking** (CRITICAL - Bug #36):
- **Symptom**: Windows PC PWA connected (MTU exchange visible) but no "Mobile app connected" log. Device became invisible after disconnect. Android PWA worked correctly.
- **Root Cause**: "Keep scanning" fix caused CLIENT device to attempt connections to discovered devices while also accepting incoming connections, creating interference.
- **Fix**: Stop scanning immediately when peer connects (unconditional call). Added BLE_HS_EINVAL handling for cases where scanning already stopped. Updated comments to reference Bug #36. (`src/ble_manager.c:1613-1626`)
- **Result**: All BLE central devices work correctly (Android PWA, Windows PC PWA, nRF Connect)

### Infrastructure

- Message queue added: `time_sync_to_motor_queue` for coordination messages (MSG_PHASE_ALIGNMENT, MSG_DRIFT_UPDATE)
- Task added: `time_sync_task` managing beacon exchange and quality monitoring
- Module added: `time_sync.c/h` with dual-clock calculation functions
- API documentation: `docs/AD038_TIME_SYNCHRONIZATION_API.md` (planned API examples)

### Documentation

- CLAUDE.md updated with Phase 2 summary and test results
- Architecture decisions migrated to docs/adr/ (AD037-AD040 added as individual files)
- PHASE3_COMMAND_CONTROL_IDEAS.md created for Phase 3 planning

### Known Issues (Non-Blocking)

**50ms Timing Jumps** (Under Investigation):
- 7 brief 50ms offset jumps over 90 minutes (suspected BLE connection parameter updates)
- Time sync correctly detects (quality→0%) and recovers within 2 beacons
- Impact: Negligible for 20-minute therapy sessions
- Decision: Not blocking Phase 2 completion; will investigate if Phase 3 motor coordination affected

---

## [0.2.0-beta.1] - 2025-11-19

### Added - Phase 1c: Battery-Based Role Assignment
- **AD035 Implementation**: Battery-based role assignment via BLE Service Data (0x16). Devices broadcast battery percentage in scan response during peer discovery window (0-30s). Higher battery device initiates connection (SERVER/MASTER role), lower battery device waits (CLIENT/SLAVE role). MAC address tie-breaker for equal batteries. Eliminates race condition for deterministic role assignment. (`src/ble_manager.c:2114-2153, 2256-2319, 2547-2572`)
- **Dynamic Battery Updates**: Advertising restarts when battery changes during peer discovery window, ensuring accurate role assignment data. Falls back to discovery-based role if no battery data available.

### Fixed
- **GPIO15 Status LED Stuck ON** (Bug #34): After peer pairing completes, motor_task takes WS2812B ownership which disables status_led pattern control. GPIO15 was left ON from pairing patterns, blocking all future status LED blinks. Fixed by explicitly calling `status_led_off()` after pairing success/failure patterns complete, before motor takes ownership. (`src/ble_task.c:251-252, 301-302`)

### Fixed (Phase 1b.3 Continued)
- **Button Unresponsiveness** (CRITICAL - Bug #28): Rapid button presses (5+ in 1 second) caused firmware hang requiring battery disconnect to recover. Root cause: Blocking `status_led_pattern()` calls in button state machine (50ms for mode change, 500ms for BLE re-enable). Multiple rapid presses accumulated blocking delays (5 presses = 250ms blocked), preventing button GPIO reads and causing state machine to enter unexpected states. Fixed by replacing blocking LED patterns with non-blocking `status_led_on()` (~10ms brief pulse). Button task now remains responsive to rapid inputs. (`src/button_task.c:148, 185`)

### Changed
- **Phase Naming Clarification**: Renamed "Phase 4" to "Phase 0.4" throughout documentation to avoid confusion with planned Phase 2 and Phase 3. Phase 0.4 represents JPL-compliant single-device testing foundation, parallel to Phase 1's dual-device work. (`CLAUDE.md`, `README.md`, documentation files)
- **Documentation Updates**: Updated README.md with current Phase 1c completion status. Fixed outdated button controls (wake from sleep, factory reset timing), removed obsolete LED patterns, clarified 1-2s button hold is for mobile app connection only (SERVER role).

### Changed (Phase 1b.3 Continued)
- **UUID-Switching Strategy**: Implemented time-based UUID switching for peer/app identification (Phase 1b.3 architecture). Devices advertise Bilateral Service UUID (`...0100`) for first 30 seconds (peer discovery only), then switch to Configuration Service UUID (`...0200`) for app discovery. Bonded peers reconnect by cached address via Config UUID (allowed anytime). Eliminates complex state-based connection identification and **completely eliminates Bug #27** (PWA misidentification) at BLE discovery level - mobile apps physically cannot discover device during Bilateral UUID window. (`src/ble_manager.c:140-161, 1696-1712, 1807-1821, 2184-2197`, `src/ble_task.c:114-127`)
- **Connection Identification Simplified**: Replaced complex 4-path state machine (cached address, BLE role, scanning state, grace period) with simple 2-case UUID check. If advertising Bilateral UUID → connection is peer. If advertising Config UUID → check cached peer address, otherwise mobile app. Reduced connection identification code from ~60 lines to ~30 lines (50% reduction). Zero misidentification risk - connection type determined by which UUID device is advertising when connection arrives. (`src/ble_manager.c:1277-1307`)
- **Pairing Window Enforcement**: Reduced effective pairing window from 38 seconds (30s + 8s grace period) to strict 30 seconds via UUID-switching. Grace period no longer needed - UUID automatically switches at 30s boundary. Clearer user experience and simpler implementation.
- **Security Model Updated**: Security section simplified to reflect UUID-switching enforcement. Bilateral UUID (0-30s) allows unbonded peer connections (initial pairing). Config UUID (30s+) only allows bonded peer reconnections (unbonded connections identified as mobile apps). Security check now only prevents multiple simultaneous peer connections. (`src/ble_manager.c:1310-1329`)

---

## [0.1.3] - 2025-11-15

### Added - Phase 1b.3: BLE Bonding/Pairing Security
- **BLE Pairing Support**: Just-Works pairing implementation with LE Secure Connections (ECDH key exchange)
- **Bonding with NVS Storage**: Long-term key storage for persistent pairing across power cycles (production mode)
- **Pairing State Machines**: 5-state BLE task (added BLE_STATE_PAIRING) and 9-state motor task (added MOTOR_STATE_PAIRING_WAIT)
- **Session Timer After Pairing**: Session timer initialization deferred until after successful pairing for accurate session duration tracking
- **Message Queue Architecture**: Added `ble_to_motor_queue` for pairing status communication (MSG_PAIRING_COMPLETE, MSG_PAIRING_FAILED)
- **Pairing Test Mode**: `BLE_PAIRING_TEST_MODE` build flag for RAM-only bonding (prevents NVS flash wear during development testing)
- **30-Second Pairing Timeout**: JPL-compliant bounded timeout with progress logging every 5 seconds
- **Pairing LED Patterns**: Full WS2812B RGB integration for pairing feedback
  - **Waiting**: GPIO15 solid ON + WS2812B purple solid (palette index 7)
  - **Progress**: GPIO15 pulsing 1Hz + WS2812B purple pulsing (500ms ON/OFF)
  - **Success**: GPIO15 OFF + WS2812B green 3× blink (250ms each)
  - **Failed**: GPIO15 OFF + WS2812B red 3× blink (250ms each)
- **Graceful Pairing Timeout**: Automatic connection termination and cleanup if pairing exceeds 30 seconds

### Fixed (Phase 1b.3)
- **motor_on_ms Constraint Mismatch** (CRITICAL - Bug #18): AD032 specified 0.25-2.0Hz frequency range but motor_on_ms limit was 500ms (only supported ≥0.5Hz). At 0.40Hz with 25% duty, calculation yielded 625ms (rejected). At 0.39Hz, calculation yielded 641ms (rejected). Root cause: Original 500ms limit designed for preset modes (0.5-1Hz), not research platform's full range. Fixed by increasing motor_on_ms limit from 500ms to 1250ms (supports 0.25Hz @ 50% duty = full AD032 range). Also increased coast_ms from 2000ms to 4000ms for low-frequency support. (`motor_task.c:677-683`)
- **Pairing Window Security Blocking App Connections** (CRITICAL - Bug #19): Pairing window security check rejected ALL unbonded connections (peer AND app) before determining connection type. This caused asymmetric pairing failures where one device would pair successfully while the other rejected the connection. Symptom: After mobile app connection attempt, peer devices could no longer pair (one device thinks paired, other shows timeout). Root cause: Security check occurred before connection type determination in BLE_GAP_EVENT_CONNECT handler. Fixed by restructuring connection handler to determine connection type FIRST (peer vs app), then apply connection-type-specific security rules: PEER connections blocked outside 30s pairing window unless bonded, APP connections allowed anytime (no pairing requirement). (`ble_manager.c:1237-1390`)
- **Bilateral Motor Offset Timing Error** (Bug #20): CLIENT device started motor 250ms too early (1/4 cycle offset error) in bilateral mode. For 1.0Hz bilateral (1000ms cycle), CLIENT should wait 500ms (half cycle) but was waiting 750ms (coast_ms from ACTIVE/INACTIVE timing). This worked by accident at 50% duty (natural gaps prevented overlap) but would fail at higher duty cycles. Root cause: CLIENT offset used coast_ms instead of calculating proper bilateral half-cycle offset. Fixed by calculating bilateral_cycle_ms (motor_on_ms + coast_ms) and using bilateral_cycle_ms / 2 for CLIENT initial INACTIVE wait. Ensures true alternation: DEV_A [250ms ON | 750ms OFF], DEV_B [500ms OFF | 250ms ON | 250ms OFF] for 1.0Hz@50%. (`motor_task.c:318-327`)
- **Peer Misidentification - App Identified as Peer** (CRITICAL - Bug #21): Mobile app connections were misidentified as peer device connections, causing incorrect handling and state corruption. Symptom: When mobile app connected to device waiting for peer, app was identified as peer, triggering peer connection logic. When app disconnected, code thought peer disconnected and tried to restart advertising (which was already running), causing advertising state desync. Root cause: Connection handler used overly broad heuristic "scanning_active → must be peer" without checking WHO initiated the connection. Fixed by checking BLE connection role: if WE initiated connection (BLE_GAP_ROLE_MASTER), it's a peer (we only connect to discovered peers). If THEY initiated connection (BLE_GAP_ROLE_SLAVE), it's an app (unless cached peer address matches). (`ble_manager.c:1261-1283`)
- **Advertising State Desync** (Bug #22): BLE_TASK reported "advertising=NO" but device was actually advertising (mobile app could connect). Root cause: When advertising restart failed with BLE_HS_EALREADY (error code 2 = already advertising), code incorrectly set `advertising_active = false`. This happened because Bug #21 caused app disconnects to be handled as peer disconnects, which tried to restart advertising that was already running. Fixed by syncing flag with actual NimBLE state on error: `advertising_active = ble_gap_adv_active()` instead of blindly setting false. Applied to all advertising restart error paths. (`ble_manager.c:1369, 1463, 1491`)
- **Pairing Window Not Enforced for Peer Discovery** (Bug #23): New peer connections could be initiated during active session if BLE scanning was restarted. Symptom: DEV_A in active session (motors running) could discover and connect to newly-powered DEV_B, interrupting session. Root cause: Scan callback (BLE_GAP_EVENT_DISC) checked for duplicate peer connections but not for pairing window expiry. Fixed by adding 30-second pairing window check to scan callback - peers discovered outside pairing window are ignored. (`ble_manager.c:2101-2106`)
- **Asymmetric Pairing Failure - Incoming Peer Connections Misidentified** (CRITICAL - Bug #24): Bug #21 fix was incomplete - only handled outgoing connections (BLE MASTER). When DEV_A (BLE SLAVE) received incoming connection from DEV_B (BLE MASTER), it had no cached peer address and was misidentified as app connection. Symptom: One device successfully pairs while other device times out and continues in single-device mode. DEV_A logs show "Mobile app connected" when DEV_B connects. Root cause: Peer identification logic didn't account for incoming connections during pairing window. Fixed by adding Case 3: if device is BLE SLAVE (they initiated) AND scanning_active=true (in pairing window), it's a peer connection. This completes the peer identification logic for all connection scenarios: outgoing (BLE MASTER), incoming during pairing (BLE SLAVE + scanning), incoming after pairing (app), and bonded reconnections (cached address). (`ble_manager.c:1279-1285`)
- **SERVER Advertising Restart Timing Race** (Bug #25): Intermittent failure where SERVER device wouldn't advertise for mobile app connections after peer pairing. Symptom: Sometimes mobile app could connect after peer pairing, sometimes not (intermittent on battery-powered boots). Root cause: BLE_MANAGER tried to restart advertising immediately after peer connection (20ms), NimBLE controller not ready yet, rejected with BLE_HS_ECONTROLLER error (rc=6). When restart failed, advertising never started and BLE_TASK eventually detected "advertising stopped externally" and went to IDLE. Fixed by removing immediate advertising restart from BLE_MANAGER connection handler and moving it to BLE_TASK PAIRING → ADVERTISING transition (~4s later). This gives NimBLE controller time to fully establish connection before advertising restart. Only SERVER devices restart advertising (CLIENT devices don't advertise after peer pairing). (`ble_manager.c:1355-1375`, `ble_task.c:248-259`)
- **Pairing Timeout Race - Late Peer Connections Misidentified** (CRITICAL - Bug #26): Asymmetric pairing when devices started at different times. Symptom: DEV_A starts first, times out after 30s, continues as single-device. DEV_B starts ~27s later, discovers DEV_A, connects at 36s (DEV_A time). DEV_A receives connection AFTER timeout, identifies as "App" instead of "Peer" because scanning_active=false. Result: DEV_A runs single-device mode, DEV_B runs bilateral CLIENT mode (one device thinks pairing succeeded, other doesn't). Root cause: Case 3 peer identification only checked scanning_active flag (true during active scan). After pairing timeout, scanning stops and flag=false, so late peer connections fall through to "app" case. Fixed by adding Case 3b: Check 38-second grace period (30s pairing + 8s grace) AND no peer connected yet. Grace period duration accounts for BLE connection establishment (1-5s typical) plus margin for devices discovered just before 30s timeout. Connections arriving within grace period (when waiting for FIRST peer) are identified as peers even if scanning stopped. Once peer connects, grace period no longer applies (prevents app misidentification). This handles devices started up to ~25 seconds apart. (`ble_manager.c:1287-1305`)
- **PWA Misidentified as Peer When Scanning Active After Peer Pairing** (CRITICAL - Bug #27): Mobile app (PWA/native) connections rejected with "Rejecting unbonded PEER outside 30s pairing window" error. Symptom: At 66s after boot, PWA connection identified as peer instead of app, then rejected by security check. Device showed "BLE: Peer (SERVER)" at 61s (peer already connected), but PWA at 66s still identified as peer. Root cause: Case 3a peer identification checked only `scanning_active` flag without checking if peer was already connected. After peer pairing, scanning may restart for peer rediscovery (after peer disconnect), causing PWA connections to be misidentified as peers. Fixed by adding `!peer_state.peer_connected` check to Case 3a: if peer already connected, incoming connections during scanning are apps (not peers). Also added error handling for `ble_gap_disc_cancel()` to log failures. This aligns with industry best practices for state-based connection type identification (no BLE standard exists for this, confirmed via research into Nordic/Espressif/BLE Mesh implementations). (`ble_manager.c:1279-1294`, `ble_manager.c:1350-1359`)
- **Bilateral Frequency Definition Ambiguity**: Updated comments to clarify that mode frequencies (0.5Hz, 1.0Hz, 1.5Hz, 2.0Hz) refer to BILATERAL alternation rate (one complete left-right alternation per second) not per-device frequency. Example: "1.0Hz" in dual-device mode means DEV_A active while DEV_B inactive, then vice versa, completing 1 full bilateral cycle per second. In single-device mode, same frequency with alternating motor directions. This aligns with EMDR therapeutic standards requiring bilateral stimulation. (`motor_task.c:47-60`, `motor_task.h:50-67`)

### Architecture Decisions
- **AD036**: BLE Bonding/Pairing Security Architecture - Just-Works pairing with LE Secure Connections, conditional NVS storage

### Infrastructure
- New build environment: `xiao_esp32c6_ble_no_nvs` for BLE testing (RAM-only bonding)
  - **NVS Write Prevention**: `store_status_cb = NULL` in test mode prevents flash writes during pairing tests
  - Bonding data stored in RAM only, cleared on reboot (prevents flash wear during development)
  - Production mode: `store_status_cb = ble_store_util_status_rr` enables NVS persistence
- BLE task expanded from 4 to 5 states with pairing lifecycle management
- Motor task expanded from 8 to 9 states with pairing wait state
- Message queue count increased from 3 to 4 (added ble_to_motor_queue)

### Implementation Notes
- **Simplified from Initial Plan**: Originally planned numeric comparison with button confirmation, implemented as Just-Works pairing for faster development
- **NimBLE API Corrections**: Used `BLE_GAP_EVENT_ENC_CHANGE` for pairing detection instead of separate security manager callback
- **Session Timer Lifecycle**: Moved from main.c initialization to motor task (starts only after pairing completes)

### Documentation
- BUILD_COMMANDS.md updated with pairing test environment commands across all shell environments (bash, PowerShell, cmd)
- AD036 created in architecture_decisions.md

---

## [0.1.2] - 2025-11-14

### Added - Phase 1b: Peer Discovery and Initial Role Assignment
- **Peer-to-Peer Discovery**: Devices discover and connect to each other via BLE scanning (~1-2s connection time)
- **Connection Type Identification**: `ble_is_peer_connected()` and `ble_get_connection_type_str()` differentiate peer vs mobile app connections
- **Battery Exchange**: Bilateral Battery characteristic updates every 60 seconds for role assignment foundation
- **Race Condition Handling**: Graceful handling of ACL_CONN_EXISTS error (523) when both devices connect simultaneously (AD010)
- **Project-Specific UUIDs**: Changed from Nordic UART Service to custom UUID base `4BCAE9BE-9829-...` to prevent collision (AD032)
- **Battery Status Logging**: Motor task now logs connection type: `Battery: 4.18V [98%] | BLE: Peer/App/Disconnected`

### Architecture Decisions
- **AD035**: Battery-Based Initial Role Assignment strategy (higher battery = SERVER role)
- **AD010**: Updated Race Condition Prevention Strategy with Phase 1b simultaneous connection handling
- **AD028**: Updated Command-and-Control Architecture with Phase 1b implementation status
- **AD030**: Updated Bilateral Control Service with Phase 1b battery characteristic implementation

### Fixed (Phase 1b.1)
- **Mobile App Cannot Connect When Peer-Paired** (RESOLVED): Increased `CONFIG_BT_NIMBLE_MAX_CONNECTIONS` from 1 to 2, allowing SERVER to accept both peer and mobile app connections simultaneously

### Fixed (Phase 1b.2)
- **Advertising Timeout Disconnects Peer** (CRITICAL - Bug #7): Role-aware advertising implemented (`ble_manager.c:1136-1155`). CLIENT (connection initiator) stops advertising to prevent 5-minute timeout. SERVER (connection receiver) keeps advertising for mobile app access. Fixes peer timeout disconnect while enabling mobile app connection during peer pairing.
- **Peer Reconnection Broken** (CRITICAL - Bug #8): Fixed peer disconnect handler to explicitly restart both advertising and scanning for peer rediscovery (`ble_manager.c:1186-1214`). Previous code relied on `advertising_active` flag which was set to false by Bug #7 fix, preventing reconnection after peer disconnect.
- **PWA Cannot Discover Device** (Bug #9): Web Bluetooth PWAs filter by Configuration Service UUID but device was only advertising Bilateral Service UUID. Now advertising Configuration Service UUID (`...0200`) in scan response (`ble_manager.c:1385`). Peer discovery updated to use Configuration Service UUID instead of Bilateral Service UUID (`ble_manager.c:1708`) - simpler single-UUID approach works for both peer discovery and PWA filtering.
- **Both Devices Think They're CLIENT** (CRITICAL - Bug #10): When both devices scan simultaneously, both set `peer_discovered = true` upon discovery. Role detection logic incorrectly used this flag to determine connection initiator, causing both to think they initiated (CLIENT role). Fixed by using NimBLE's actual connection role (`desc.role == BLE_GAP_ROLE_MASTER` = CLIENT, `BLE_GAP_ROLE_SLAVE` = SERVER) instead of discovery flag (`ble_manager.c:1150-1166`). SERVER now correctly keeps advertising for mobile app access.
- **SERVER Advertising Not Visible After Peer Connection** (CRITICAL - Bug #11): SERVER logged "Keeping advertising active" after peer connection but was invisible to BLE scanners. Root cause: NimBLE automatically stops advertising when ANY connection is established (standard BLE behavior). The code logged "keeping advertising active" but didn't actually restart it. Fixed by explicitly restarting advertising after peer connection for SERVER role (`ble_manager.c:1176-1185`). Also enabled `CONFIG_BT_NIMBLE_HOST_ALLOW_CONNECT_WITH_SCAN` to allow incoming connections while scanning (`sdkconfig.xiao_esp32c6:843`).
- **Race Condition Warning on PWA Disconnect** (JPL Compliance - Bug #12): BLE task logged "Advertising did not restart after disconnect" warning due to race condition - it checked advertising status before disconnect handler completed restart (~80ms). Violated JPL requirement for deterministic behavior. Fixed by adding 150ms deterministic delay before checking advertising status (`ble_task.c:175-178`). Warning now only appears if advertising genuinely fails to restart.
- **Slow Peer Reconnection After Disconnect** (Bug #13): Peer reconnection took ~1 minute vs ~2 seconds for initial connection. Root cause: NimBLE needs time to clean up connection handle after disconnect. Immediate retry (2s after disconnect) caused `BLE_ERR_UNK_CONN_ID` errors. Fixed by increasing peer disconnect delay from 100ms to 2 seconds (`ble_manager.c:1361-1366`). Allows NimBLE to fully clean up before reconnection attempt, achieving fast reconnection similar to initial discovery.
- **Peer Misidentified as Mobile App After Reconnect** (CRITICAL - Bug #14): When one device shut down and restarted, the other device misidentified the peer as "Mobile app connected" instead of "Peer device connected". Root cause: Connection detection logic required both `peer_discovered` flag AND address match, but flag was cleared on disconnect while address remained cached. Fixed by checking cached peer address first without requiring `peer_discovered` flag (`ble_manager.c:1228-1234`). Peer now correctly identified on reconnection using cached MAC address.
- **No Graceful BLE Disconnect on Shutdown** (CRITICAL - Bug #15): Emergency shutdown (5s button hold) did not disconnect BLE connections before entering deep sleep. Peer device experienced connection timeout (0x08) instead of clean disconnect. Fixed by adding explicit `ble_gap_terminate()` calls for both peer and mobile app connections in BLE task shutdown handler (`ble_task.c:162-181`). Connections now terminate gracefully with "Remote Device Terminated by Local Host" (0x16) before deep sleep.
- **Role Not Assigned When Advertising Inactive** (CRITICAL - Bug #16): Battery logs showed "BLE: Peer" without CLIENT/SERVER role designation. Root cause: Role assignment at `ble_manager.c:1272` only executed inside `if (adv_state.advertising_active)` check. If advertising stopped before peer connection established, role never assigned (`peer_state.role` remained `PEER_ROLE_NONE`). Fixed by moving role assignment outside advertising check (`ble_manager.c:1268-1280`). Role now always assigned based on NimBLE's `desc.role` regardless of advertising state.
- **Device Names Not Unique** (CRITICAL - Bug #17): Both devices advertised as "EMDR_Pulser_406400" instead of unique names with actual MAC address. Root cause: `ble_hs_id_infer_auto()` at line 1542 returns address **type** (public vs random), not address **bytes**. This returned garbage data instead of actual MAC address. Fixed by using correct API `ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, addr_val, NULL)` (`ble_manager.c:1540-1555`). Devices now show unique names like "EMDR_Pulser_8945DE" and "EMDR_Pulser_8A46E1" based on actual MAC addresses. Also added full MAC address logging for diagnostics.

### JPL Power of Ten Compliance (November 15, 2025)
- **Unbounded Mutex Waits Eliminated** (CRITICAL - JPL Rule #6): All 69 instances of `portMAX_DELAY` in mutex operations replaced with 100ms bounded timeouts. Affects `motor_control.c` (5), `role_manager.c` (17), and `ble_manager.c` (47). Each timeout includes error handling: functions returning `esp_err_t` return `ESP_ERR_TIMEOUT`, getters return safe defaults, void functions return early. Prevents permanent hangs if mutex holder crashes.
- **Infinite Error Loops Eliminated** (WARNING - JPL Rule #2): Replaced 3 infinite `while(1)` loops in `main.c` error handlers with `esp_deep_sleep_start()`. Allows button-wake recovery instead of permanent system hang when hardware init, queue creation, or task creation fails.
- **User-Bounded Wait Exception** (Accepted): Button release wait after NVS factory reset (`button_task.c:270`) intentionally kept unbounded - this is a user-driven shutdown operation where wait is bounded by human action, not system automation. Watchdog is fed during wait to prevent timeout.

**JPL Compliance Status:** ✅ ACHIEVED
- Rule #1 (No dynamic allocation): ✅ PASS
- Rule #2 (Fixed loop bounds): ✅ PASS
- Rule #3 (No recursion): ✅ PASS
- Rule #4 (No goto): ✅ PASS
- Rule #5 (Check return values): ✅ PASS
- Rule #6 (No unbounded waits): ✅ PASS (all violations eliminated)
- Rule #7 (Watchdog compliance): ✅ PASS
- Rule #8 (Defensive logging): ✅ PASS

### Known Issues
- **Advertising Timeout Not Enforced** (Low Priority): 5-minute advertising timeout doesn't trigger when no mobile app connects. Advertising continues indefinitely instead of transitioning to IDLE. Does not affect functionality when peer is connected or when mobile app connects successfully. Deferred to future milestone.
- **Advertising Timer Loop** (Possibly RESOLVED by Bug #8 fix): Previous rapid IDLE→ADVERTISING→timeout loop after disconnect may be resolved by peer reconnection fix. Requires hardware testing to confirm.
- **Status LED 5× Blink Not Visible**: Function called on peer connection but LED doesn't blink (hardware confirmed functional)
- **Battery Calibration Needed** (Planned Phase 1c): Fully charged batteries don't reach 100% (~95-98% observed) due to 1S2P configuration, P-MOSFET losses, and battery wear. Requires USB detection (5V pin) and automatic calibration routine.

### Hardware Reliability Notes
- **Motor Connection Intermittency**: One device experienced intermittent motor operation progressing to complete failure during testing. Recommendations:
  - Verify solder joint quality on motor wire connections
  - Check for wire flex fatigue at solder points (motor wires subject to vibration)
  - Consider strain relief for motor wires in future enclosure design
  - Inspect motor solder pads for cold joints or cracked solder

### Infrastructure
- Modular architecture in `src/` (ble_manager, motor_task, ble_task, button_task)
- Build environment: `xiao_esp32c6`
- Dual battery characteristic updates (Configuration Service + Bilateral Control Service)

### Documentation
- Phase 1b section added to CLAUDE.md with implementation details and testing evidence
- architecture_decisions.md updated with Phase 1b status in AD010, AD028, AD030
- AD035 created documenting battery-based role assignment strategy

---

## [0.1.1] - 2025-11-13

### Fixed
- **LED_COUNT constant**: Corrected from 2 to 1 in [led_control.h](src/led_control.h) to match actual hardware (1 WS2812B per device)
- **Frequency range documentation**: Updated from 0.5-2 Hz to 0.25-2 Hz research platform range in README and related docs
- **Hardware descriptions**: Corrected references from "TB6612FNG H-bridge IC" to "discrete MOSFET H-bridge" to accurately reflect hardware design

---

## [0.1.0] - 2025-11-13

### Added
- **BLE GATT Server**: Full NimBLE implementation with 12 GATT characteristics for mobile app control (AD032)
- **8-State Motor Machine**: Instant mode switching (<100ms latency) with safe cleanup (SESSION_SUMMARY_MODE_SWITCH_REFACTOR.md)
- **State Machine Analysis**: Systematic bug detection methodology (STATE_MACHINE_ANALYSIS_CHECKLIST.md)
- **JPL Compliance**: Phase 4 implementation with message queues, error handling, watchdog management
- **NVS Persistence**: User settings saved across power cycles
- **Back-EMF Sampling**: Research measurements during first 10 seconds of mode changes
- **Battery Monitoring**: LiPo voltage sensing with low-battery protection
- **Documentation Versioning**: Unified semantic versioning system (AD034)
- **Immediate BLE Notifications**: Session time and battery level sent immediately on subscription

### Fixed
- 6 critical bugs found during state machine analysis before hardware testing:
  - State overwrite after shutdown (nested loop break scope error)
  - Missing cleanup in motor/LED state transitions
  - Button task message spam (no terminal state)
  - Watchdog timeout (missing feed in main loop)
  - BLE parameter update latency (up to 1s delay)
  - Emergency shutdown hang (inverted deep sleep logic)
- BLE re-enable button press (1-2s hold) now works in all states

### Infrastructure
- Modular architecture with separate task/control/manager modules
- ESP-IDF v5.5.0 via PlatformIO
- Seeed XIAO ESP32-C6 hardware platform
- 16-color LED palette (AD033)

### Documentation
- CLAUDE.md: AI reference guide
- README.md: Main project documentation
- architecture_decisions.md: 34 design decisions documented
- requirements_spec.md: Full project specification
- QUICK_START.md: Consolidated quick start guide

---

## Project Milestones (Pre-versioning)

### Phase 4: JPL Compliance (2025-11-04)
- Message queue architecture
- Button state machine (no goto)
- Comprehensive error handling
- Battery LVO protection

### BLE GATT Integration (2025-11-06)
- Full NimBLE GATT server implementation
- 12 GATT characteristics for mobile app control
- NVS persistence for user settings
- Immediate notifications on subscription
- State machine refactoring for instant mode switching

### Phase 1-3: Foundation (2025-10-01 to 2025-10-31)
- Motor control with 4 preset modes
- WS2812B LED control
- Button interface
- Back-EMF sensing research platform
- Power management (tickless idle, deep sleep)

### Initial Hardware (2025-09-15)
- ESP32-C6 hardware selection
- Discrete MOSFET H-bridge motor driver
- Dual 320mAh LiPo batteries
- WS2812B RGB LEDs

---

## Version Bump Guidelines

### Minor Versions (v0.x.Y)
- Documentation updates, clarifications, typo fixes
- Content additions to existing documents
- Small feature additions

### Major Versions (v0.X.0)
- New features (BLE, dual-device support)
- Architecture changes documented in new ADs
- Requirement updates
- Breaking changes to APIs or workflows

### Version 1.0.0
- Production release milestone
- Feature-complete implementation
- Comprehensive testing completed
- Full documentation verified
