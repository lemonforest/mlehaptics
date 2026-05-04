# Architecture Decision Records (ADR)

This directory contains all Architecture Decision Records for the EMDR Bilateral Stimulation Device project.

**Format:** [MADR 4.0.0](https://adr.github.io/madr/) (Markdown Architectural Decision Records)
**Migration Date:** 2025-11-21
**Status:** ✅ Migrated from monolithic `docs/architecture_decisions.md`

---

## Quick Navigation

| ID | Title | Status | Phase | Date |
|----|-------|--------|-------|------|
| [AD001](0001-esp-idf-v5-5-0-framework-selection.md) | ESP-IDF v5.5.0 Framework Selection | ✅ Accepted | Phase 1a | 2025-10-28 |
| [AD002](0002-jpl-coding-standard-adoption.md) | JPL Power of Ten Rules Adoption | ✅ Accepted | Phase 1a | 2025-10-28 |
| [AD003](0003-c-language-selection.md) | C Language Selection (C17 Standard) | ✅ Accepted | Phase 1a | 2025-10-28 |
| [AD004](0004-seeed-xiao-esp32c6-platform-selection.md) | Seeed XIAO ESP32C6 Platform Selection | ✅ Accepted | Phase 1a | 2025-10-28 |
| [AD005](0005-gpio-assignment-strategy.md) | GPIO Assignment Strategy | ✅ Accepted | Phase 1a | 2025-10-28 |
| [AD006](0006-bilateral-cycle-time-architecture.md) | Bilateral Cycle Time Architecture | ✅ Accepted | Phase 1a | 2025-10-28 |
| [AD007](0007-freertos-task-architecture.md) | FreeRTOS Task Architecture | ✅ Accepted | Phase 1a | 2025-10-28 |
| [AD008](0008-ble-protocol-architecture.md) | BLE Protocol Architecture | 🔄 Superseded | Phase 1b | 2025-10-29 |
| [AD009](0009-bilateral-timing-implementation.md) | Bilateral Timing Implementation | ✅ Accepted | Phase 1a | 2025-10-29 |
| [AD010](0010-race-condition-prevention-strategy.md) | Race Condition Prevention Strategy | ✅ Accepted | Phase 1b | 2025-10-29 |
| [AD011](0011-emergency-shutdown-protocol.md) | Emergency Shutdown Protocol | ✅ Accepted | Phase 1a | 2025-10-29 |
| [AD012](0012-dead-time-implementation-strategy.md) | Dead Time Implementation Strategy | ✅ Accepted | Phase 1a | 2025-10-29 |
| [AD013](0013-factory-reset-security-window.md) | Factory Reset Security Window | ✅ Accepted | Phase 1a | 2025-10-30 |
| [AD014](0014-deep-sleep-strategy.md) | Deep Sleep Strategy | ✅ Accepted | Phase 3 | 2025-10-30 |
| [AD015](0015-nvs-storage-strategy.md) | NVS Storage Strategy | ✅ Accepted | Phase 1a | 2025-10-30 |
| [AD016](0016-no-session-state-persistence.md) | No Session State Persistence | ✅ Accepted | Phase 1a | 2025-10-30 |
| [AD017](0017-conditional-compilation-strategy.md) | Conditional Compilation Strategy | ✅ Accepted | Phase 1a | 2025-10-30 |
| [AD018](0018-technical-risk-mitigation.md) | Technical Risk Mitigation | ✅ Accepted | Phase 4 | 2025-10-31 |
| [AD019](0019-task-watchdog-timer-adaptive-feeding.md) | Task Watchdog Timer Adaptive Feeding | ✅ Accepted | Phase 4 | 2025-10-31 |
| [AD020](0020-power-management-strategy-phased.md) | Power Management Strategy (Phased) | ✅ Accepted | Phase 3 | 2025-11-01 |
| [AD021](0021-motor-stall-detection-back-emf.md) | Motor Stall Detection (Back-EMF) | ✅ Accepted | Phase 3 | 2025-11-04 |
| [AD022](0022-esp-idf-build-system-test-architecture.md) | ESP-IDF Build System and Test Architecture | ✅ Accepted | Phase 1a | 2025-11-05 |
| [AD023](0023-deep-sleep-wake-state-machine.md) | Deep Sleep Wake State Machine | ✅ Accepted | Phase 3 | 2025-11-06 |
| [AD024](0024-led-strip-component-version.md) | LED Strip Component Version Lock | ✅ Accepted | Phase 4 | 2025-11-07 |
| [AD025](0025-dual-device-wake-pattern-ux.md) | Dual-Device Wake Pattern UX | ✅ Accepted | Phase 3 | 2025-11-08 |
| [AD026](0026-ble-automatic-role-recovery.md) | BLE Automatic Role Recovery | 🔄 Superseded | Phase 1b | 2025-11-09 |
| [AD027](0027-modular-source-file-architecture.md) | Modular Source File Architecture | ✅ Accepted | Phase 1b | 2025-11-10 |
| [AD028](0028-command-control-synchronized-fallback.md) | Command-and-Control Architecture with Synchronized Fallback | ✅ Accepted | Phase 2 | 2025-11-11 |
| [AD029](0029-relaxed-timing-specification.md) | Relaxed Timing Specification (±100ms) | ✅ Accepted | Phase 2 | 2025-11-11 |
| [AD030](0030-ble-bilateral-control-service.md) | BLE Bilateral Control Service | ✅ Accepted | Phase 1b | 2025-11-12 |
| [AD031](0031-research-platform-extensions.md) | Research Platform Extensions | ✅ Accepted | Phase 4+ | 2025-11-12 |
| [AD032](0032-ble-configuration-service-architecture.md) | BLE Configuration Service Architecture | ✅ Accepted | Phase 1b | 2025-11-12 |
| [AD033](0033-led-color-palette-standard.md) | LED Color Palette Standard | ⏳ Approved | Phase 1b | 2025-11-13 |
| [AD034](0034-documentation-versioning-and-release-management.md) | Documentation Versioning and Release Management | ⏳ Approved | Phase 1b | 2025-11-13 |
| [AD035](0035-battery-based-initial-role-assignment.md) | Battery-Based Initial Role Assignment (Phase 1c) | ✅ Implemented | Phase 1c | 2025-11-14 |
| [AD036](0036-ble-bonding-and-pairing-security.md) | BLE Bonding and Pairing Security (Phase 1b.3) | ⏳ Approved | Phase 1b.3 | 2025-11-15 |
| [AD037](0037-state-based-connection-type-identification.md) | State-Based BLE Connection Type Identification | 🔄 Superseded | Phase 1b.3 | 2025-11-18 |
| [AD038](0038-uuid-switching-strategy.md) | UUID-Switching Strategy for Connection Type Identification | ✅ Implemented | Phase 1b.3 | 2025-11-18 |
| [AD039](0039-time-synchronization-protocol.md) | Time Synchronization Protocol | 🔄 Superseded | Phase 2 | 2025-11-19 |
| [AD040](0040-firmware-version-checking.md) | Firmware Version Checking for Peer Devices | ⏳ Approved | Phase 2 | 2025-11-19 |
| [AD041](0041-predictive-bilateral-synchronization.md) | Predictive Bilateral Synchronization Protocol | 🔄 Superseded | Phase 6v | 2025-12-12 |
| [AD042](0042-remove-mac-delay-battery-based-symmetry-breaking.md) | Remove MAC-Based Scan Delay (Battery-Based Symmetry Breaking) | ✅ Implemented | Phase 6q | 2025-11-29 |
| [AD043](0043-filtered-time-synchronization.md) | Filtered Time Synchronization Protocol | ✅ Approved | Phase 6r | 2025-12-02 |
| [AD044](0044-non-blocking-motor-timing.md) | CLIENT Hardware Timer Synchronization | ✅ Accepted | Phase 6 | 2025-12-03 |
| [AD045](0045-synchronized-independent-bilateral-operation.md) | Synchronized Independent Bilateral Operation | ⏳ Proposed | Phase 6u | 2025-12-08 |
| [AD046](0046-ptp-observation-mode-integration.md) | PTP Observation Mode Integration | ⏳ Proposed | Phase 6v | 2025-12-12 |
| [AD047](0047-scheduled-pattern-playback.md) | Scheduled Pattern Playback Architecture | ✅ Implemented | Phase 7 | 2025-12-13 |
| [AD048](0048-espnow-adaptive-transport-hardware-acceleration.md) | ESP-NOW Adaptive Transport and Hardware Acceleration | 🔬 Research | Phase 7+ | 2025-12-17 |
| [AD049](0049-csi-phase-motion-detection-exploration.md) | CSI Phase-Based Motion Detection Exploration | 🔬 Exploratory | Phase 8+ | 2025-12-23 |
| [AD050](0050-utlp-module-extraction.md) | UTLP Module Extraction | ⏳ Proposed | Phase 8 | 2025-12-24 |

---

## Navigation by Phase

### Phase 0.1: Foundation (Framework & Standards)
- Development platform selection
- Coding standards
- Build system

### Phase 0.4: JPL Compliance (Single-Device)
- Message queue architecture
- Error handling patterns
- Watchdog management

### Phase 1: Dual-Device Foundation
- Peer discovery
- Connection management
- Battery monitoring

### Phase 1b: BLE Bonding & Pairing
- Pairing security
- NVS storage
- Connection identification

### Phase 1b.3: UUID Switching
- Peer vs app identification
- Time-based advertising

### Phase 1c: Role Assignment
- Battery-based roles
- SERVER/CLIENT assignment

### Phase 2: Time Synchronization (Complete)
- NTP-style beacon exchange
- Clock drift compensation
- Quality metrics

### Phase 6: Bilateral Motor Coordination (Complete)
- PTP-inspired pattern broadcast architecture
- EMA filter with dual-alpha design
- Motor epoch for independent operation
- ±30 μs precision over 90 minutes

### Phase 6k: Predictive Bilateral Synchronization
- Drift-rate prediction
- Motor epoch broadcasting
- CLIENT antiphase calculation
- Validates AD028 Option A with drift compensation

### Phase 6q: Discovery Race Condition Fix
- Remove MAC-based scan delay
- Fix error 523 handler bug
- Battery-based symmetry breaking
- Eliminates advertising-only race window

### Phase 6r: Filtered Time Synchronization
- One-way SERVER timestamps (replaces 4-way RTT)
- Exponential moving average filter
- Eliminates RTT spike sensitivity
- ±15ms accuracy improvement

### Phase 6u: Synchronized Independent Operation
- Both devices calculate from synced clocks
- Eliminates correction death spiral
- Passive monitoring for edge cases
- ±6 μs precision over 20 minutes

### Phase 7: Scheduled Pattern Playback (P7.0-P7.2 Complete - AD047)
- ✅ P7.0 Pattern Engine Foundation
- ✅ P7.1 Scheduled Pattern Playback (catalog, interpolation, "Lightbar Mode")
- ✅ P7.2 Pattern Catalog Export (`pattern_generate_json()`)
- ⏳ P7.3 PWA Pattern Designer
- 📋 P7.4 Legacy Mode Migration

### Phase 7+: ESP-NOW and Hardware Acceleration (Research - AD048)
- ESP-NOW as adaptive BLE fallback for extended range
- 802.11mc FTM coexistence for ranging
- AES/SHA/ECC hardware accelerator utilization
- Transport abstraction layer design

### Phase 8: Architecture Refinement
- AD049: CSI Phase-Based Motion Detection (Exploratory)
- AD050: UTLP Module Extraction (Proposed)
  - Clean separation: Time = unencrypted (public), Application = encrypted
  - Transport-agnostic API for portability
  - Reference implementation for prior art documentation

---

## Navigation by Status

### ✅ Accepted
Decisions that have been implemented and are in active use.

### 🔄 Superseded
Decisions that have been replaced by newer decisions.

**Supersession Chain:**
- AD008 (BLE Protocol Architecture) → 🔄 Superseded in Phase 1b (replaced by AD030, AD032)
- AD010 (Race Condition Prevention - MAC Delay) → 🔄 Partially Superseded by AD042 (MAC delay component removed; error 523 handling retained)
- AD026 (BLE Automatic Role Recovery) → 🔄 Superseded by AD028 (Command-and-Control Architecture)
- AD028 (Command-and-Control - Motor Control) → 🔄 Partially Superseded by AD041 (Predictive Sync for motor control, command-and-control retained for emergency features)
- AD037 (State-Based Connection ID) → 🔄 Superseded by AD038 (UUID-Switching Strategy)
- AD039 (Time Synchronization Protocol) → 🔄 Superseded by AD043 (Filtered Time Sync replaces 4-way RTT with one-way timestamps + EMA filter)

### ⏳ Approved
Decisions that have been accepted but not yet fully implemented.

### 🔬 Research
Decisions under active investigation/research before implementation planning.

### ❌ Deprecated
Decisions that are no longer valid or relevant.

---

## Navigation by Type

### Architecture
Core system design decisions affecting multiple components.

### Build System
Compilation, linking, and environment configuration decisions.

### Security
Authentication, authorization, encryption, and pairing decisions.

### Testing
Test strategy, verification methods, and validation approaches.

### Documentation
Documentation format, structure, and maintenance decisions.

---

## How to Create a New ADR

1. **Copy the template:**
   ```bash
   cp docs/adr/_template.md docs/adr/NNNN-your-decision-title.md
   ```

2. **Fill in all sections:**
   - Date, Phase, Status, Type
   - Summary (Y-Statement)
   - Problem Statement, Context, Decision
   - Consequences (Benefits & Drawbacks)
   - Options Considered (with pros/cons)
   - Related Decisions
   - Implementation Notes

3. **Update this index:**
   - Add row to Quick Navigation table
   - Add to appropriate Phase section
   - Add to Status section
   - Add to Type section

4. **Reference in code:**
   ```c
   // Per AD040, we check firmware version compatibility
   // See docs/adr/0040-firmware-version-checking.md
   ```

5. **Commit with clear message:**
   ```bash
   git add docs/adr/NNNN-*.md docs/adr/README.md
   git commit -m "[ADR] Add ADNNN: Title"
   ```

---

## ADR Migration Notes

**Original Location:** `docs/architecture_decisions.md` (4,354 lines, 186 KB)
**Reason for Migration:** Exceeded Claude Code read tool token limit (25,000 tokens)
**Migration Date:** 2025-11-21
**Commit Hash:** _[to be added]_

**Benefits of File-Per-AD Structure:**
- ✅ Individual ADs readable by AI tools (500-1000 tokens each)
- ✅ Fast grep/search for specific decisions
- ✅ Automated cross-reference validation
- ✅ Clear template for future decisions
- ✅ Parallel development (no merge conflicts)
- ✅ Granular git history per decision

**Backward Compatibility:**
- Original file archived at `docs/archive/architecture_decisions.md`
- "AD0XX" reference format works with both old and new structure
- Links in code/docs can gradually migrate to new location

---

## Cross-Reference Graph

_(To be populated with decision dependency visualization)_

---

## Statistics

- **Total Decisions:** 50
- **Accepted:** 31 (AD001-007, AD009-013, AD015-024, AD027-032, AD044)
- **Implemented:** 5 (AD035, AD038, AD041, AD042, AD047)
- **Approved:** 5 (AD033, AD034, AD036, AD040, AD043)
- **Proposed:** 3 (AD045, AD046, AD050)
- **Research/Exploratory:** 2 (AD048, AD049)
- **Superseded:** 4 (AD008, AD026, AD037, AD039)
- **Partially Superseded:** 2 (AD010 - MAC delay only, AD028 - motor control only)
- **Deprecated:** 0

---

## Maintenance

**Last Updated:** 2025-12-24
**Maintained By:** Project team + Claude Code AI
**Review Frequency:** Quarterly or when adding new decisions
**Template Version:** MADR 4.0.0 (Customized for EMDR Pulser)

---

**Questions about ADRs?**
- See `docs/adr/_template.md` for structure
- Review existing ADs for examples
- Reference MADR 4.0.0 standard: https://adr.github.io/madr/
