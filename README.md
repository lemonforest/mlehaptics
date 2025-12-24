# EMDR Bilateral Stimulation Device

**Version:** v0.7.x (Phase 7 Development)
**Last Updated:** 2025-12-23
**Status:** Phase 7 In Progress (P7.3 PWA Pattern Designer next) | P7.0-P7.2 Complete | Phase 6 Complete
**Project Phase:** Phase 7 (Patterns) | Phase 6 Complete | Phase 2 Complete (Time Sync) | Phase 1c Complete (Pairing)

**A dual-device EMDR therapy system with automatic pairing and coordinated bilateral stimulation**

> **Architecture Note:** This system uses a **hybrid BLE + ESP-NOW architecture**. BLE handles device discovery, pairing, and mobile app communication. ESP-NOW handles all peer-to-peer coordination with ±100μs timing precision. See [Connectionless Distributed Timing](docs/Connectionless_Distributed_Timing_Prior_Art.md) for the foundational techniques.

![EMDR Device in Hand](images/device-in-hand.jpg)

Generated with assistance from **Claude Opus 4.5 (Anthropic)**

## 🤖 Development Methodology

This firmware was developed through guided AI iteration (Claude, Gemini, Grok), moving non-linearly between models and context windows. Cross-checking between sessions often surfaced insights that single-context iteration missed. The human role was direction, validation criteria, and "does this feel right" intuition—not code correction or complete domain expertise. AI contributed both implementation and domain research (protocol analysis, academic literature, patent landscape, algorithm selection).

What you see is what the AI produced through iterative guidance.

**Timing validation:** 240fps slow-motion capture on a consumer phone.

## 🎯 Project Overview

This project implements a two-device bilateral stimulation system for EMDR (Eye Movement Desensitization and Reprocessing) therapy. Two identical ESP32-C6 devices automatically discover and pair with each other, then provide synchronized alternating stimulation patterns with safety-critical non-overlapping timing. The system uses professional ERM (Eccentric Rotating Mass) motors for tactile stimulation with H-bridge bidirectional control, and includes a WS2812B RGB LED for dual-modality stimulation.

**Current Development Status:**
- ✅ Phase 0.4 JPL-compliant firmware complete (single-device testing)
- ✅ Phase 1c complete: Peer discovery with battery-based role assignment
- ✅ Phase 2 complete: NTP-style time synchronization (±30 μs over 90 minutes)
- ✅ Phase 6 complete: Bilateral motor coordination with PTP-inspired sync protocol
- ✅ GPIO remapping complete: H-bridge IN1 moved from GPIO20 to GPIO18 (eliminates crosstalk)
- ✅ Phase 7 P7.0-P7.2 complete: Pattern Engine, Scheduled Playback, Catalog Export (AD047)
- ⏳ Phase 7 next: P7.3 PWA Pattern Designer, P7.4 Legacy Mode Migration

**Key Features:**
- **Hybrid BLE + ESP-NOW**: BLE for discovery/pairing, ESP-NOW for sub-millisecond peer coordination
- **Configurable bilateral frequency**: 0.25-2 Hz (500-4000ms total cycle time)
- **Precise half-cycle allocation**: Each device gets exactly 50% of total cycle
- **Connectionless execution**: Devices sync once, then execute independently without coordination traffic
- **JPL-compliant timing**: All delays use FreeRTOS vTaskDelay() (no busy-wait loops)
- **Adaptive watchdog feeding**: Short cycles feed at end, long cycles feed mid-cycle + end (4-8x safety margin)
- **Open-source hardware**: Complete PCB designs, schematics, 3D-printable cases

### 🚀 Architecture Evolution (v0.7)

**v0.6 and earlier:** BLE maintained for peer-to-peer coordination throughout session. Time sync beacons sent via BLE GATT notifications. BLE connection required for bilateral motor coordination.

**v0.7 (Current):** **BLE Bootstrap Model** - BLE used only for initial discovery, pairing, and key exchange (~10 seconds). After bootstrap:
- Peer BLE connection **released** (frees radio for PWA)
- ESP-NOW handles all ongoing coordination (beacons, mode changes, shutdown)
- PWA can connect to SERVER device for real-time session control
- ±100μs timing precision (vs ±10-50ms with BLE)

This architectural shift improves timing precision by 100-500x and frees BLE radio resources for more responsive PWA communication.

## 🔌 Hardware Overview

### Physical Device

The device features a compact, ergonomic design with a 3D-printed enclosure housing a custom PCB based on the Seeed XIAO ESP32-C6 module.

<table>
<tr>
<td width="50%">

![Device Top View](images/device-top-view.jpg)
**Top View:** USB-C charging port, button, and status LED openings visible in the smooth enclosure surface.

</td>
<td width="50%">

![Device Bottom View](images/device-bottom-view.jpg)
**Bottom View:** Battery compartment access panel and mounting holes for internal components.

</td>
</tr>
</table>

**Size Reference:**

![Device Size Comparison](images/device-aa_battery-mouse-size-comparison.jpg)

The device is significantly smaller than a standard computer mouse - approximately the length of an AA battery and comfortably fits in the palm of your hand. The compact form factor makes it ideal for discreet bilateral handheld therapy sessions.

### Key Hardware Components

- **MCU:** Seeed XIAO ESP32-C6 (RISC-V @ 160 MHz)
- **Motor:** ERM vibration motor with discrete MOSFET H-bridge control
- **LED:** WS2812B RGB LED for status feedback
- **Power:** Dual 320mAh LiPo batteries (640mAh total) with USB-C charging
- **Enclosure:** 3D-printed Nylon 12 SLS case (files in [hardware/enclosure/](hardware/enclosure/))
- **PCB:** Custom design (KiCad files in [hardware/pcb/](hardware/pcb/))

For complete hardware documentation, assembly instructions, and manufacturing files, see [hardware/README.md](hardware/README.md).

## 🛡️ Safety-Critical Development Standards

### ESP-IDF Framework Requirements
- **Mandatory Version**: ESP-IDF v5.5.0 (latest stable, enhanced ESP32-C6 support)
- **Platform**: PlatformIO espressif32 v6.12.0 with official Seeed XIAO ESP32-C6 support
- **Framework**: ESP-IDF (not Arduino) for real-time guarantees
- **Rationale**: Enhanced ULP support, BR/EDR + Wi-Fi coexistence, MQTT 5.0, proven stability

### JPL Institutional Coding Standard Compliance
This project follows **JPL Coding Standard for C Programming Language** for safety-critical medical device software:

**Memory Management:**
- ✅ No dynamic memory allocation (malloc/free) during runtime
- ✅ Static allocation only for all data structures
- ✅ Stack usage analysis with defined limits

**Control Flow:**
- ✅ No recursion - all algorithms use iterative approaches
- ✅ **No busy-wait loops** - all timing uses vTaskDelay() or hardware timers
- ✅ Limited function complexity (cyclomatic complexity ≤ 10)
- ✅ Single entry/exit points for all functions
- ✅ No goto statements except error cleanup

**Safety Requirements:**
- ✅ Comprehensive error checking for all function calls
- ✅ Bilateral timing precision ±10ms maximum deviation from configured cycle time
- ✅ Emergency shutdown within 50ms of button press
- ✅ Non-overlapping stimulation patterns (devices never stimulate simultaneously)
- ✅ 1ms dead time at end of each half-cycle (included within timing budget)

## ⚡ Quick Start

### Prerequisites
- **ESP-IDF v5.5.0**: Automatically managed by PlatformIO via `platformio.ini`
- **PlatformIO**: Install via VS Code extension or standalone
- **Two Seeed Xiao ESP32-C6 boards**: Hardware platform requirement (dual-device mode)
- **Hardware files**: See [hardware/README.md](hardware/README.md) for PCB manufacturing and case printing

### Build and Deploy

1. **Clone repository**:
   ```bash
   git clone https://github.com/lemonforest/mlehaptics.git
   cd mlehaptics
   ```

2. **Open in PlatformIO**: File → Open Folder → select project directory

3. **Verify ESP-IDF version configuration**: 
   - The `platformio.ini` file at the project root uses ESP-IDF v5.5.0
   - PlatformIO will automatically download and use the correct version
   - Build output will confirm "ESP-IDF v5.5.0" is being used
   
   **Working configuration in `platformio.ini`:**
   ```ini
   platform = espressif32 @ 6.12.0  ; Official Seeed XIAO ESP32-C6 support
   framework = espidf               ; Platform auto-selects ESP-IDF v5.5.0
   board = seeed_xiao_esp32c6       ; Official board definition
   ```

4. **Build project**: PlatformIO → Build (Ctrl+Alt+B)
   - First build will download ESP-IDF v5.5.0 (~1GB, takes ~10 minutes)
   - Verify build output shows "framework-espidf @ 3.50500.0 (5.5.0)"
   - Subsequent builds: ~1 minute incremental

5. **Upload to device(s)**: PlatformIO → Upload (Ctrl+Alt+U)

### First Power-On

**Single-Device Mode (Current Testing):**
1. **Power device** - use nRF Connect app to configure parameters
2. **5 operational modes**: Four presets + custom BLE-controlled mode
3. **Hold button 5 seconds** to shutdown

**Dual-Device Mode (Current Implementation):**
1. **Power both devices** - they will automatically pair within 30 seconds
2. **Status LED patterns**:
   - Fast blink = searching for server
   - Slow blink = waiting for client
   - Solid on = connected and bilateral active
3. **Test bilateral stimulation** - Motors alternate based on configured cycle time:
   - Default 1000ms cycle: Each motor active for 499ms (with 1ms dead time)
   - Fast 500ms cycle: Each motor active for 249ms (2 Hz bilateral rate)
   - Slow 2000ms cycle: Each motor active for 999ms (0.5 Hz bilateral rate)
   - **NO overlap** at any cycle time setting
4. **Hold button 5 seconds** on either device to shutdown both

## 🎬 Typical Bilateral Operation Flow

### Starting a Therapy Session

**Step 1: Power On Both Devices**
- Remove both devices from cases or turn on simultaneously
- Devices boot within 2-3 seconds
- Purple LED + status LED ON = waiting for peer

**Step 2: Automatic Pairing (< 10 seconds)**
- Both devices scan for Bilateral Control Service UUID
- Higher battery device initiates connection (becomes SERVER/MASTER)
- Lower battery device accepts connection (becomes CLIENT/SLAVE)
- **Pairing success**: 3× green synchronized flash on both devices
- **Pairing failure** (rare): 3× red flash, power cycle to retry

**Step 3: Session Starts Automatically**
- Default mode: 0.5Hz @ 25% duty (Mode 0)
- SERVER motors activate while CLIENT motors coast
- After 1 second: CLIENT motors activate while SERVER motors coast
- Bilateral alternation continues automatically
- **Session continuity**: If BLE briefly disconnects (<2 min), motors continue using frozen drift rate

**Step 4: Mode Switching During Session** (Optional)
- **Button tap** on either device: Cycle through modes (0→1→2→3→0...)
- Mode change propagates to peer device automatically
- Both devices synchronize to new frequency within 1 cycle
- Single quick blink confirms mode change
- **Available modes**: 0.5Hz, 1.0Hz, 1.5Hz, 2.0Hz @ 25% motor duty

**Step 5: Session Termination**
- **Normal end**: Session stops after configured duration (default 20 minutes)
- **Emergency shutdown**: 5-second button hold on **either** device
  - Purple LED ON during hold = release to shutdown
  - Both devices stop motors within 50ms
  - Both devices enter deep sleep simultaneously
- **Automatic shutdown**: Low battery warning → graceful stop

### Reconnection After Brief Disconnect

**If BLE connection drops during session:**
- ✅ **Motors continue** using frozen drift rate (CLIENT only)
- ✅ **Bilateral alternation maintained** (±2.4ms drift over 20 min)
- ✅ **Therapeutic continuity** preserved during BLE glitches
- ⏱️ **Safety timeout**: After 2 minutes, motors stop gracefully
- 🔄 **Reconnection**: Devices automatically reconnect, motors resume coordination

**Note:** Roles are preserved on reconnection (Phase 6n). If roles somehow swap, device logs warning (indicates bug).

## 🔧 Bilateral Timing Architecture

### Configurable Cycle Times

**Total cycle time** is the primary configuration parameter:
- **Range**: 500-4000ms (displayed to therapists as 0.25-2 Hz)
- **Default**: 1000ms (1 Hz, traditional EMDR bilateral rate)
- **Half-cycle allocation**: Each device gets exactly total_cycle / 2

### Timing Budget Examples

**1000ms Total Cycle (1 Hz):**
```
Server: [===499ms motor===][1ms dead][---499ms off---][1ms dead]
Client: [---499ms off---][1ms dead][===499ms motor===][1ms dead]
```

**500ms Total Cycle (2 Hz):**
```
Server: [===249ms motor===][1ms dead][---249ms off---][1ms dead]
Client: [---249ms off---][1ms dead][===249ms motor===][1ms dead]
```

**2000ms Total Cycle (0.5 Hz):**
```
Server: [===999ms motor===][1ms dead][---999ms off---][1ms dead]
Client: [---999ms off---][1ms dead][===999ms motor===][1ms dead]
```

### Dead Time Implementation

**1ms FreeRTOS delay at end of each half-cycle:**
- **JPL compliant**: Uses vTaskDelay(), no busy-wait loops
- **Watchdog feeding**: esp_task_wdt_reset() called during 1ms delay
- **Hardware protection**: GPIO write latency (~50ns) provides natural MOSFET dead time
- **Minimal overhead**: 1ms = 0.1-0.4% of half-cycle time
- **Included in budget**: Motor active time = (half_cycle_ms - 1)

## 📁 Project Structure

```
├── platformio.ini              # Build configuration (ESP-IDF v5.5.0)
├── README.md                   # This file
├── LICENSE                     # GPL v3 (software/firmware)
├── AI_GENERATED_DISCLAIMER.md  # Important safety notice
├── hardware/
│   ├── LICENSE                 # CERN-OHL-S v2 (hardware designs)
│   ├── README.md               # Hardware documentation
│   ├── pcb/                    # KiCad PCB project files
│   ├── enclosure/              # FreeCAD case designs
│   └── datasheets/             # Component specifications
├── docs/
│   ├── ai_context.md           # Complete rebuild instructions & API contracts
│   ├── requirements_spec.md    # Business requirements with dev standards
│   └── architecture_decisions.md # Technical rationale (PDR)
├── test/
│   ├── single_device_ble_gatt_test.c  # Phase 4 current implementation
│   └── *.md                    # Test-specific guides
├── include/
│   ├── config.h               # System constants, JPL compliance macros
│   ├── ble_manager.h          # BLE services and connection management
│   ├── led_controller.h       # PWM patterns and bilateral control
│   ├── nvs_manager.h          # Non-volatile storage interface
│   ├── button_handler.h       # ISR-based button timing
│   └── power_manager.h        # Deep sleep and session management
└── src/
    ├── main.c                 # FreeRTOS tasks and state machine (placeholder)
    └── ...                    # (actual code in test/ during development)
```

## 🎮 User Operation

### Normal Operation
- **Power on**: Devices auto-pair and start bilateral stimulation (dual-device mode)
- **Default session**: 20 minutes with automatic shutdown
- **Cycle time**: Configurable via mobile app (500-2000ms, displayed as Hz)
- **Status feedback**: Status LED shows connection and system state
- **Safety-critical timing**: Alternating half-cycles with NO overlap

### Button Controls
- **Button press**: Wake from deep sleep
- **1-2 second hold**: Re-enable BLE advertising for mobile app connection (SERVER role only)
- **5-second hold**: Emergency shutdown (both devices stop immediately)
- **15-second hold** (within 30s of boot): Factory reset (NVS clear)

### LED Status Indicators

| Status | Pattern | Description |
|--------|---------|-------------|
| 🔌 **BLE Connected** | 5× blink (100ms) | Mobile app or peer connected |
| 📡 **BLE Re-enabled** | 3× blink (100ms) | Advertising restarted (1-2s button hold) |
| 🪫 **Low Battery** | 3× blink (200ms) | Battery low warning |
| 🔧 **Factory Reset** | 3× blink (100ms) | NVS cleared successfully |
| 🎯 **Mode Change** | Single quick blink (50ms) | Mode switched |
| ⏸️ **Button Hold** | Continuous ON | Hold detected (1s+), waiting for action |
| ⏳ **Pairing Wait** | Solid ON + Purple LED | Waiting for peer (30s window) |
| 🔄 **Pairing Progress** | Pulsing 1Hz + Purple LED | Peer connection in progress |
| ✅ **Pairing Success** | 3× green synchronized | Peer paired successfully |
| ❌ **Pairing Failed** | 3× red synchronized | Peer pairing failed |

## 🔬 Development Configuration

### ⚠️ Critical Build System Constraint

**ESP-IDF uses CMake - PlatformIO's `build_src_filter` DOES NOT WORK!**

ESP-IDF framework delegates all compilation to CMake, which reads `src/CMakeLists.txt` directly. PlatformIO's `build_src_filter` option has **NO EFFECT** with ESP-IDF.

**Required approach**: Python pre-build scripts modify `src/CMakeLists.txt` for source file selection.

**📚 See for complete details:**
- **`docs/ESP_IDF_BUILD_CONSTRAINTS.md`** - Full explanation, examples, and common mistakes
- **`docs/architecture_decisions.md`** - AD022: Build System Architecture

### Build Standards and Quality Assurance

#### Code Quality Requirements
- **C language only**: No C++ features (JPL standard compliance)
- **No busy-wait loops**: All timing uses vTaskDelay() or hardware timers
- **Static analysis**: Code must pass JPL-compliant static analysis tools
- **Function complexity**: Maximum cyclomatic complexity of 10
- **Stack analysis**: All functions must have bounded stack usage
- **Error handling**: All functions return esp_err_t for operations that can fail

#### Build Flags (config.h)
```c
// Development mode configuration
#define ENABLE_FACTORY_RESET    1   // 0 = disable for production
#define TESTING_MODE           1   // 0 = production build
#define DEBUG_LEVEL            3   // 0 = no logging, 4 = full debug

// JPL Coding Standard compliance
#define JPL_COMPLIANT_BUILD    1   // Enable JPL standard checks
#define ESP_IDF_TARGET_VERSION "v5.5.0"  // Verified ESP-IDF version

// Bilateral timing configuration
#define BILATERAL_CYCLE_TOTAL_MIN_MS    500     // 2 Hz max
#define BILATERAL_CYCLE_TOTAL_MAX_MS    2000    // 0.5 Hz min
#define BILATERAL_CYCLE_TOTAL_DEFAULT   1000    // 1 Hz default
#define MOTOR_DEAD_TIME_MS              1       // FreeRTOS delay
```

#### Validation Requirements
- **Unit testing**: Minimum 90% code coverage for safety-critical functions
- **Integration testing**: Full two-device bilateral coordination validation at multiple cycle times
- **Timing precision**: Automated testing of ±10ms bilateral timing requirements
- **JPL compliance**: Static analysis verification of coding standard adherence
- **ESP-IDF compatibility**: Build verified against v5.5.0 (October 20, 2025)

### Testing Protocol

#### Bilateral Coordination Testing
1. Power both devices simultaneously
2. Verify automatic pairing within 30 seconds
3. Test at multiple cycle times (500ms, 1000ms, 2000ms)
4. Confirm non-overlapping stimulation patterns with oscilloscope
5. Test coordinated shutdown from either device

#### Single-Device Testing  
1. Power single device
2. Use nRF Connect app for BLE configuration
3. Test all 5 operational modes
4. Test button wake/shutdown functionality

#### Timing Validation
1. **Oscilloscope verification**: Measure actual bilateral timing precision at all cycle times
2. **Stress testing**: 24-hour continuous operation validation
3. **Emergency response**: Verify <50ms shutdown response time
4. **Connection loss**: Test graceful degradation when devices disconnect
5. **Watchdog testing**: Verify TWDT feeding during 1ms dead time periods

## ⚠️ Important Safety Notice

**This code was generated with AI assistance and implements safety-critical medical device functionality. Please read `AI_GENERATED_DISCLAIMER.md` for critical safety information before use.**

### Required Validation for Medical Use
- **Complete code review** by qualified embedded systems engineer
- **JPL coding standard verification** using certified static analysis tools
- **ESP-IDF v5.5.0 compatibility** verified on target hardware (October 20, 2025)
- **Safety validation** for therapeutic applications following IEC 62304
- **Timing precision validation** with laboratory-grade measurement equipment
- **EMC compliance testing** for medical device environments
- **Battery safety validation** for portable medical equipment

### Development Environment Requirements
- **ESP-IDF v5.5.0**: Required version for enhanced ESP32-C6 support and BLE stability
- **Static analysis tools**: PC-Lint, Coverity, or equivalent for JPL compliance
- **Timing measurement**: Oscilloscope or logic analyzer for bilateral precision testing
- **Multi-device testing**: Minimum two ESP32-C6 boards for integration testing

## 📚 Documentation

### Web App
- **[MLE Haptics PWA](https://lemonforest.github.io/mlehaptics-pwa/)**: Web Bluetooth control app for device configuration and monitoring

### Research & Prior Art

This project developed foundational techniques for **connectionless distributed timing**—a class of systems that achieve synchronized actuation across wireless nodes *without* real-time coordination traffic during operation. While we built an EMDR device, the architecture enables countless applications from emergency vehicle light bars to drone swarms.

- **[Connectionless Distributed Timing: A Prior Art Publication](docs/Connectionless_Distributed_Timing_Prior_Art.md)**: Defensive publication establishing open-source prior art for synchronized wireless actuation. Documents the journey from BLE stack timing jitter to recognizing the constraint was artificial. Validated with SAE J845 Quad Flash at 240fps (zero-frame overlap). Published to ensure these techniques remain freely available.

### Technical Reports
- **[Bilateral Time Sync Protocol Technical Report](docs/Bilateral_Time_Sync_Protocol_Technical_Report.md)**: Comprehensive documentation of the PTP-inspired BLE synchronization protocol achieving +/-30us over 90 minutes

### Protocol Specifications (UTLP/RFIP)
- **[UTLP Specification](docs/UTLP_Specification.md)**: Universal Time Layer Protocol - peer-to-peer time synchronization for embedded swarms
- **[UTLP Technical Report v2](docs/UTLP_Technical_Report_v2.md)**: Detailed protocol analysis with stratum hierarchy and passive opportunistic adoption
- **[RFIP Addendum](docs/UTLP_Addendum_Reference_Frame_Independent_Positioning.md)**: Reference-Frame Independent Positioning - spatial awareness without external reference frames
- **[802.11mc FTM Reconnaissance](docs/802.11mc_FTM_Reconnaissance_Report.md)**: Fine Time Measurement research for ±1-2m ranging capability

### For Builders
- **[hardware/README.md](hardware/README.md)**: PCB manufacturing, case printing, assembly instructions
- **[test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md](test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md)**: BLE GATT testing with nRF Connect

### For Developers
- **[docs/ai_context.md](docs/ai_context.md)**: Complete API contracts and rebuild instructions with JPL compliance
- **[docs/adr/README.md](docs/adr/README.md)**: Architecture Decision Records (48 ADRs documenting design rationale)
- **[docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md)**: Known bugs and limitations being tracked for resolution
- **[docs/requirements_spec.md](docs/requirements_spec.md)**: Business requirements with development standards
- **[CLAUDE.md](CLAUDE.md)**: Developer reference for AI-assisted workflow
- **Doxygen docs**: Run `doxygen Doxyfile` for comprehensive API documentation

### For Users
- **This README**: Setup and operation instructions with safety requirements
- **AI_GENERATED_DISCLAIMER.md**: Critical safety validation requirements

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

**In brief:** This is a personal research project. Bug reports and suggestions via GitHub issues are welcome! I prefer to implement changes myself to ensure hands-on hardware testing and consistency with the AI-assisted development workflow. Forks are encouraged if you want to take the project in your own direction.

### Code Standards Reference

If you're forking or studying the code, these are the standards followed:

- **C language**: Strictly C (no C++ features)
- **JPL coding standard**: All safety-critical rules must be followed
- **No busy-wait loops**: All delays use vTaskDelay() or hardware timers
- **Doxygen-style comments**: Required for all public functions
- **ESP-IDF v5.5.x conventions**: Follow latest framework best practices
- **Hierarchical error handling**: Proper esp_err_t propagation

## 📄 License

This project uses **dual licensing** to separate software and hardware:

### Software License: GPL v3

All firmware, software, and code in this repository is licensed under the **GNU General Public License v3.0**.

- **Applies to:** All `.c`, `.h`, Python scripts, and other software files
- **Location:** [LICENSE](LICENSE)
- **Summary:** Copyleft license - modifications must be shared under same license
- **Compatibility:** Can be integrated into GPL-compatible projects

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

### Hardware License: CERN-OHL-S v2

All hardware designs (PCB schematics, layouts, enclosures) are licensed under the **CERN Open Hardware License Version 2 - Strongly Reciprocal**.

- **Applies to:** KiCad files, gerbers, FreeCAD models, STL/STEP files in `/hardware`
- **Location:** [hardware/LICENSE](hardware/LICENSE)
- **Summary:** Copyleft for hardware - derivative designs must be shared under same license
- **Compatibility:** Reciprocal like GPL but for physical designs

[![License: CERN-OHL-S-2.0](https://img.shields.io/badge/Hardware-CERN--OHL--S--2.0-green.svg)](https://ohwr.org/cern_ohl_s_v2.txt)

### Why Dual Licensing?

- **Software copyleft (GPL v3):** Ensures firmware improvements benefit the community
- **Hardware copyleft (CERN-OHL-S v2):** Ensures PCB/case improvements benefit the community
- **Strong reciprocal:** Both licenses require sharing modifications under the same terms
- **Patent protection:** Both provide protection against patent claims
- **Medical device safety:** Copyleft ensures safety improvements are shared publicly

### Attribution Requirements

When using or modifying this project:
- **Retain all license notices** in source files and documentation
- **Document modifications** with dates and descriptions
- **Share modified source** if distributing devices or derivatives
- **Credit original project:** Link to this repository

## 📄 Attribution

- **License:** Dual - [GPL v3](LICENSE) (software) + [CERN-OHL-S v2](hardware/LICENSE) (hardware)
- **AI Assistant**: Claude Sonnet 4 (Anthropic) - Code generation assistance
- **Development Standards**: JPL Institutional Coding Standard for C Programming Language
- **Framework**: ESP-IDF v5.5.0 (Espressif Systems) - Verified October 20, 2025
- **Human Engineering**: Requirements specification, safety validation, hardware design
- **Project**: MLE Haptics - mlehaptics.org
- **Generated**: 2025-09-18, Updated: 2025-12-23

Please maintain attribution when using or modifying this code or hardware designs.

## 🔗 Related Projects and Future Development

### Phase 0.4: Single-Device Testing & Hardware Validation (Complete)
- **Phase 0.4 firmware**: JPL-compliant single-device operation with BLE GATT control
- **5 operational modes**: Four presets + custom BLE-configured mode
- **Hardware v0.663399ADS**: GPIO crosstalk fixes implemented, ready for production
- **Mobile app integration**: BLE GATT Configuration via nRF Connect

### Phase 1b/1c: Dual-Device Peer Discovery and Role Assignment (Complete)
- ✅ **Phase 1b Complete**: Peer discovery with UUID switching (Bilateral UUID 0-30s, Config UUID 30s+)
- ✅ **Phase 1b.1 Complete**: Multiple connection support (peer + mobile app simultaneously)
- ✅ **Phase 1b.2 Complete**: Role-aware advertising (SERVER continues, CLIENT stops)
- ✅ **Phase 1b.3 Complete**: Exclusive pairing (once bonded, only that peer can connect until NVS erase)
- ✅ **Phase 1c Complete**: Battery-based role assignment via BLE Service Data (higher battery initiates as SERVER)

### Phase 2: NTP-Style Time Synchronization (Complete)
- ✅ **Time Sync Protocol**: NTP-style beacon exchange via ESP-NOW achieving ±30 μs over 90 minutes
- ✅ **Dual-Clock Architecture**: System clock untouched, synchronized time via API
- ✅ **Quality Metrics**: 0-100% sync quality with automatic recovery from anomalies
- ✅ **90-Minute Stress Test**: 271 ESP-NOW beacons exchanged, 95% quality sustained

### Phase 6: Bilateral Motor Coordination (Complete)
- ✅ **ESP-NOW Coordination**: Sub-millisecond peer sync (±100μs jitter vs BLE's ±10-50ms)
- ✅ **PTP-Inspired Sync**: Pattern broadcast architecture (like emergency vehicle light bars)
- ✅ **Motor Epoch**: Shared timing reference for independent device operation
- ✅ **Non-overlapping Half-Cycles**: Each device gets exactly 50% of total cycle time
- ✅ **Emergency Shutdown**: Coordinated stop from either device within 50ms

### Phase 7: Scheduled Pattern Playback (P7.0-P7.2 Complete - AD047)

**Milestones:**
- ✅ **P7.0 Pattern Engine Foundation**: Core pattern scheduling infrastructure
- ✅ **P7.1 Scheduled Pattern Playback**: Pattern catalog as SSOT, CLIENT interpolation, "Lightbar Mode"
- ✅ **P7.2 Pattern Catalog Export**: JSON generation from SSOT catalog (`pattern_generate_json()`)
- ⏳ **P7.3 PWA Pattern Designer**: Custom pattern creation from web app
- 📋 **P7.4 Legacy Mode Migration**: Replace reactive 0.5/1.0/1.5/2.0 Hz modes with pattern-based execution

**Features:**
- **Pre-buffered execution**: GPS-quality sync from local pattern buffer
- **Step-boundary transitions**: Pattern changes occur at pattern step boundaries (inherently safe)
- **RF disruption resilient**: Continues from local buffer during ESP-NOW gaps

### Phase 8: Advanced Haptic Research (Future)
- **Dedicated haptic driver ICs**: DRV2605L family evaluation
- **ERM vs LRA comparison**: Comparative therapeutic efficacy research
- **Pattern library**: Multiple stimulation waveforms and haptic effects
- **Enhanced power management**: Extended battery life optimization

### Development Tools and Standards
- **ESP-IDF v5.5.0**: [Official ESP-IDF Documentation](https://docs.espressif.com/projects/esp-idf/en/v5.5.0/)
- **JPL Coding Standard**: [JPL Institutional Coding Standard for C](https://web.archive.org/web/20200914031549/https://lars-lab.jpl.nasa.gov/JPL_Coding_Standard_C.pdf)
- **Medical Device Standards**: IEC 62304 Software Development Lifecycle
- **PlatformIO ESP32**: [ESP32 Platform Documentation](https://docs.platformio.org/en/latest/platforms/espressif32.html)
- **CERN-OHL**: [Open Hardware License](https://ohwr.org/project/cernohl/wikis/home)

---

**Building open-source EMDR therapy devices with safety-critical reliability! 🚀**

*Combining precise engineering, rigorous safety standards, and open-source accessibility for the therapeutic community.*
