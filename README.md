# EMDR Bilateral Stimulation Device

**A dual-device EMDR therapy system with automatic pairing and coordinated bilateral stimulation**

Generated with assistance from **Claude Sonnet 4 (Anthropic)** - Last Updated: 2025-10-20

## 🎯 Project Overview

This project implements a two-device bilateral stimulation system for EMDR (Eye Movement Desensitization and Reprocessing) therapy. Two identical ESP32-C6 devices automatically discover and pair with each other, then provide synchronized alternating stimulation patterns with safety-critical non-overlapping timing. The system uses professional ERM (Eccentric Rotating Mass) motors for tactile stimulation with H-bridge bidirectional control, and includes LED testing capabilities during development.

**Key Features:**
- **Configurable bilateral frequency**: 0.5-2 Hz (500-2000ms total cycle time)
- **Precise half-cycle allocation**: Each device gets exactly 50% of total cycle
- **JPL-compliant timing**: All delays use FreeRTOS vTaskDelay() (no busy-wait loops)
- **Adaptive watchdog feeding**: Short cycles feed at end, long cycles feed mid-cycle + end (4-8x safety margin)
- **Haptic effects support**: Short vibration pulses within half-cycle windows

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
- **Two Seeed Xiao ESP32-C6 boards**: Hardware platform requirement

### Build and Deploy

1. **Clone repository**: 
   ```bash
   git clone <repository-url>
   cd emdr-bilateral-device
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

5. **Upload to both devices**: PlatformIO → Upload (Ctrl+Alt+U)

### First Power-On

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

## 🔧 Bilateral Timing Architecture

### Configurable Cycle Times

**Total cycle time** is the primary configuration parameter:
- **Range**: 500-2000ms (displayed to therapists as 0.5-2 Hz)
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
├── AI_GENERATED_DISCLAIMER.md  # Important safety notice
├── Doxyfile                    # Documentation generation
├── docs/
│   ├── ai_context.md           # Complete rebuild instructions & API contracts
│   ├── requirements_spec.md    # Business requirements with dev standards
│   └── architecture_decisions.md # Technical rationale (PDR)
├── include/
│   ├── config.h               # System constants, JPL compliance macros
│   ├── ble_manager.h          # BLE services and connection management
│   ├── led_controller.h       # PWM patterns and bilateral control
│   ├── nvs_manager.h          # Non-volatile storage interface
│   ├── button_handler.h       # ISR-based button timing
│   └── power_manager.h        # Deep sleep and session management
└── src/
    ├── main.c                 # FreeRTOS tasks and state machine
    ├── ble_manager.c          # NimBLE implementation
    ├── led_controller.c       # LEDC PWM and pattern generation
    ├── nvs_manager.c          # Configuration persistence
    ├── button_handler.c       # Button ISR and timing logic
    └── power_manager.c        # Power management and timers
```

## 🎮 User Operation

### Normal Operation
- **Power on**: Devices auto-pair and start bilateral stimulation
- **Default session**: 20 minutes with automatic shutdown
- **Cycle time**: Configurable via mobile app (500-2000ms, displayed as Hz)
- **Status feedback**: Status LED shows connection and system state
- **Safety-critical timing**: Alternating half-cycles with NO overlap

### Button Controls
- **2-second hold**: Wake from deep sleep
- **5-second hold**: Emergency shutdown (both devices stop immediately)
- **10-second hold** (first 30s only): Factory reset

### LED Status Indicators

| Status | Pattern | Description |
|--------|---------|-------------|
| 🔄 **Boot** | 3 quick flashes | Boot sequence complete |
| 🔍 **Searching** | Fast blink (200ms) | Searching for server device |
| ⏳ **Waiting** | Slow blink (1000ms) | Waiting for client connection |
| ✅ **Connected** | Solid on | Connected, bilateral stimulation active |
| ❌ **Disconnected** | Double blink | Connection lost |
| 💓 **Single Mode** | Heartbeat (100ms on, 1900ms off) | Single mode fallback |
| 🔽 **Shutdown** | Fade out | Shutting down |
| 🚨 **Error** | SOS pattern | Critical error |

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
2. Wait 30 seconds for fallback to single mode
3. Verify heartbeat status LED and alternating forward/reverse motor
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

### For Developers
- **docs/ai_context.md**: Complete API contracts and rebuild instructions with JPL compliance
- **docs/architecture_decisions.md**: Technical decision rationale (PDR) including timing architecture
- **docs/requirements_spec.md**: Business requirements with development standards
- **Doxygen docs**: Run `doxygen Doxyfile` for comprehensive API documentation

### For Users
- **This README**: Setup and operation instructions with safety requirements
- **AI_GENERATED_DISCLAIMER.md**: Critical safety validation requirements

## 🤝 Contributing

### API-Compatible Development
Use the complete API contracts in `docs/ai_context.md` to generate compatible code additions without sharing the full source code. All generated code automatically follows ESP-IDF v5.5.0 and JPL coding standards.

### Adding Features
1. **Reference API contracts** for function signatures and safety requirements
2. **Maintain JPL compliance** - no dynamic allocation, no busy-wait loops, comprehensive error checking
3. **Use vTaskDelay() exclusively** for all timing operations (no esp_rom_delay_us or ets_delay_us)
4. **Use ESP-IDF v5.5.0 APIs** exclusively - no deprecated function calls
5. **Include comprehensive Doxygen documentation** with safety annotations
6. **Add appropriate logging** with conditional compilation for production builds
7. **Update architecture decisions** document with rationale for changes

### Code Standards Enforcement
- **C language**: Strictly C (no C++ features)
- **JPL coding standard**: All safety-critical rules must be followed
- **No busy-wait loops**: All delays use vTaskDelay() or hardware timers
- **Doxygen-style comments**: Required for all public functions
- **ESP-IDF v5.5.x conventions**: Follow latest framework best practices
- **Hierarchical error handling**: Proper esp_err_t propagation
- **Conditional compilation**: Support for testing, debug, and production builds

### Quality Gates
- **Static analysis**: Must pass JPL-compliant analysis tools
- **Unit testing**: Minimum 90% coverage for safety-critical functions
- **Integration testing**: Two-device coordination verification at multiple cycle times
- **Timing validation**: Bilateral precision within ±10ms specification
- **Code review**: Peer review required for all safety-critical changes

## 📄 License & Attribution

- **AI Assistant**: Claude Sonnet 4 (Anthropic) - Code generation assistance
- **Development Standards**: JPL Institutional Coding Standard for C Programming Language
- **Framework**: ESP-IDF v5.5.0 (Espressif Systems) - Verified October 20, 2025
- **Human Engineering**: Requirements specification and safety validation
- **Generated**: 2025-09-18, Updated: 2025-10-20

Please maintain attribution when using or modifying this code.

## 🔗 Related Projects and Future Development

### Current Phase: Motor Control with Configurable Timing
- **GPIO19/20 H-bridge control**: Variable intensity ERM motor bilateral stimulation
- **Configurable cycle times**: 500-2000ms (0.5-2 Hz therapeutic range)
- **Safety-critical timing**: Non-overlapping half-cycles with 1ms FreeRTOS dead time
- **Mobile app integration**: BLE Configuration Service for therapist control

### Phase 2: Advanced Features
- **Dedicated H-bridge IC**: Hardware-based stall detection and thermal protection
- **Pattern library**: Multiple stimulation waveforms and haptic effects
- **Biofeedback integration**: Heart rate and stress level monitoring
- **OTA updates**: BLE-based firmware updates with dual partition safety

### Development Tools and Standards
- **ESP-IDF v5.5.0**: [Official ESP-IDF Documentation](https://docs.espressif.com/projects/esp-idf/en/v5.5.0/)
- **JPL Coding Standard**: [JPL Institutional Coding Standard for C](https://web.archive.org/web/20200914031549/https://lars-lab.jpl.nasa.gov/JPL_Coding_Standard_C.pdf)
- **Medical Device Standards**: IEC 62304 Software Development Lifecycle
- **PlatformIO ESP32**: [ESP32 Platform Documentation](https://docs.platformio.org/en/latest/platforms/espressif32.html)

---

**Ready to build the future of EMDR therapy devices with safety-critical reliability! 🚀**

*Ensuring therapeutic effectiveness through precise engineering, rigorous safety standards, and JPL-compliant code quality.*
