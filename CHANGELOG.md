# Changelog

All notable changes to the EMDR Bilateral Stimulation Device project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Phase 1c: Battery-based role assignment logic
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

### Known Issues
- **Advertising Timer Loop** (Cosmetic): Rapid IDLE→ADVERTISING→timeout loop after disconnect (devices reconnect successfully despite noisy logging)
- **Status LED 5× Blink Not Visible**: Function called on peer connection but LED doesn't blink (hardware confirmed functional)
- **Mobile App Cannot Connect When Peer-Paired** (BLOCKING): nRF Connect cannot connect when devices are peer-paired; workaround: restart device before mobile app connection

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
