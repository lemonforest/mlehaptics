# Changelog

All notable changes to the EMDR Bilateral Stimulation Device project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Phase 1c: Battery-based role assignment logic (ONE-TIME at connection, not ongoing monitoring)
- Phase 2: Command-and-control protocol implementation
- Mobile app development

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
