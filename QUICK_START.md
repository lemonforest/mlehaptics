# EMDR Bilateral Stimulation Device - Quick Start Guide

**Version:** v0.1.0
**Last Updated:** 2025-11-13
**Status:** Production-Ready
**Project Phase:** Phase 4 Complete (JPL-Compliant)

---

## Prerequisites

- **Hardware**: Seeed XIAO ESP32-C6 with motor/LED assembly
- **Software**: PlatformIO IDE or PlatformIO CLI
- **Framework**: ESP-IDF v5.5.0 (auto-selected by PlatformIO)

---

## Quick Start (3 Steps)

### Step 1: Build the Firmware

**Current Build (Modular Architecture with BLE):**
```bash
pio run -e xiao_esp32c6
```

This builds the modular architecture with:
- ✅ Full BLE GATT server (12 characteristics)
- ✅ 8-state motor machine with instant mode switching
- ✅ JPL-compliant message queues and error handling
- ✅ NVS persistence for user settings
- ✅ Battery monitoring with low-voltage protection
- ✅ Back-EMF sensing for research

### Step 2: Upload to Device

```bash
pio run -e xiao_esp32c6 -t upload
```

**Or combine build + upload:**
```bash
pio run -e xiao_esp32c6 -t upload && pio device monitor
```

### Step 3: Monitor Serial Output

```bash
pio device monitor
```

Expected output:
```
========================================================
=== EMDR Bilateral Stimulation Device ===
=== v0.1.0 - Production Ready ===
========================================================

Initializing hardware...
✓ GPIO initialized
✓ Battery monitor initialized (4.15V, 95%)
✓ Motor control initialized
✓ LED control initialized
✓ Status LED initialized
✓ BLE manager initialized
✓ NVS manager initialized
✓ Power manager initialized

Starting tasks...
✓ Motor task started
✓ BLE task started
✓ Button task started

=== Device Ready ===
BLE Advertising: "EMDR_Pulser_XXXXXX"
```

---

## Hardware Controls

### Button Operations

| Action | Function |
|--------|----------|
| **Single Press** | Cycle through modes (1→2→3→4→1) |
| **Hold 1-2s** | Re-enable BLE advertising (resets 5-minute timeout) |
| **Hold 5s** | Emergency shutdown → deep sleep |

### Status LED (GPIO15)

| Pattern | Meaning |
|---------|---------|
| 1× quick blink | Mode changed |
| 3× blink | BLE advertising restarted |
| 5× blink | BLE client connected |
| Solid ON | Shutdown countdown (release button to cancel) |
| Purple blink | Ready for deep sleep (release to sleep) |

---

## Motor Modes

| Mode | Frequency | Duty Cycle | Motor ON | Coast Time |
|------|-----------|------------|----------|------------|
| **1** | 1.0 Hz | 50% | 250ms | 250ms |
| **2** | 1.0 Hz | 25% | 125ms | 375ms |
| **3** | 0.5 Hz | 50% | 500ms | 500ms |
| **4** | 0.5 Hz | 25% | 250ms | 750ms |

---

## BLE Mobile App Control

### Connection

1. Open nRF Connect (or similar BLE scanner app)
2. Scan for device: **"EMDR_Pulser_XXXXXX"**
3. Connect to device
4. Service UUID: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`

### GATT Characteristics (12 total)

**Motor Control:**
- Mode (0-4): Read/Write
- Custom Frequency (Hz × 100): Read/Write (25-200 = 0.25-2.0 Hz)
- Custom Duty Cycle (10-50%): Read/Write
- PWM Intensity (0-80%): Read/Write

**LED Control:**
- LED Enable: Read/Write
- Color Mode (0=palette, 1=RGB): Read/Write
- Palette Index (0-15): Read/Write
- Custom RGB (R,G,B): Read/Write
- Brightness (10-30%): Read/Write

**Status/Monitoring:**
- Session Duration (1200-5400s): Read/Write
- Session Time (0-5400s): Read/Notify
- Battery Level (0-100%): Read/Notify

**For detailed BLE reference**, see: [test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md](test/SINGLE_DEVICE_BLE_GATT_TEST_GUIDE.md)

---

## Testing Checklist

### Functional Tests
- [ ] Button press cycles modes (LED blinks indicate mode change)
- [ ] Motor vibrates with correct timing for each mode
- [ ] LEDs illuminate during motor operation (first 10s after mode change)
- [ ] Button hold 1-2s restarts BLE advertising (3× blink)
- [ ] Button hold 5s triggers shutdown countdown → purple blink → deep sleep
- [ ] 20-minute session timeout triggers automatic shutdown
- [ ] Wake from deep sleep works (power on or button press)

### BLE Tests
- [ ] Device appears in BLE scanner with correct name
- [ ] Connection establishes successfully
- [ ] Mode changes via BLE write work correctly
- [ ] Battery level notification received immediately on subscription
- [ ] Session time notification received immediately on subscription
- [ ] BLE re-enable from button works (advertising restarts)

### Safety Tests
- [ ] Low battery warning (< 10%) logged and device shuts down gracefully
- [ ] Emergency shutdown completes successfully
- [ ] Watchdog never triggers (no unexpected resets)

---

## Common Issues & Solutions

### "Port not found" or "Upload failed"

**Check COM port:**
- **Windows**: Device Manager → Ports (COM & LPT)
- **Linux/Mac**: `ls /dev/ttyACM* /dev/ttyUSB*`

**Update platformio.ini if needed:**
```ini
[env:xiao_esp32c6]
upload_port = COM7  ; Change to your port
monitor_port = COM7
```

### "No serial output"

1. Check baud rate: `pio device monitor -b 115200`
2. Try pressing reset button on ESP32-C6
3. Check USB cable (must support data, not just charging)

### BLE not advertising

1. Check logs for "BLE manager initialized"
2. BLE advertising times out after 5 minutes (press button 1-2s to restart)
3. Verify BLE is enabled in sdkconfig (CONFIG_BT_ENABLED=y)

### Motor not vibrating

1. Check logs for "Motor task started"
2. Verify battery voltage > 3.2V (low-voltage cutoff)
3. Check motor connections to H-bridge
4. Try different mode (some modes have longer coast periods)

---

## Build System Notes

### Modular Architecture

The current build uses a modular architecture with separate source files:

**Task Modules:**
- `motor_task.c` - 8-state motor control with instant mode switching
- `ble_task.c` - BLE advertising lifecycle management
- `button_task.c` - Button debouncing and event handling

**Hardware Control:**
- `battery_monitor.c` - LiPo voltage sensing
- `motor_control.c` - H-bridge PWM control
- `led_control.c` - WS2812B RGB LED control
- `status_led.c` - GPIO15 status indication

**System Modules:**
- `ble_manager.c` - NimBLE GATT server with 12 characteristics
- `nvs_manager.c` - Non-volatile storage for user settings
- `power_manager.c` - Power management and deep sleep

**For build system details**, see: [BUILD_COMMANDS.md](BUILD_COMMANDS.md)

### Test Environments

For development and testing, individual test programs are available:

```bash
# BLE GATT test (single-file implementation)
pio run -e single_device_ble_gatt_test -t upload

# JPL compliance test (single-file implementation)
pio run -e single_device_demo_jpl_queued -t upload

# Other test programs (see test/ directory)
```

**For test program reference**, see: [test/README.md](test/README.md)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Application Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐│
│  │ Motor Task  │  │  BLE Task   │  │  Button  ││
│  │  (State     │  │ (Lifecycle) │  │   Task   ││
│  │  Machine)   │  │             │  │          ││
│  └──────┬──────┘  └──────┬──────┘  └────┬─────┘│
│         │                │               │      │
└─────────┼────────────────┼───────────────┼──────┘
          │                │               │
┌─────────┼────────────────┼───────────────┼──────┐
│         │    Manager Layer    │          │      │
│  ┌──────▼──────┐  ┌────▼──────┐  ┌──────▼────┐ │
│  │   Motor     │  │    BLE    │  │   Power   │ │
│  │  Control    │  │  Manager  │  │  Manager  │ │
│  └──────┬──────┘  └────┬──────┘  └──────┬────┘ │
└─────────┼──────────────┼─────────────────┼──────┘
          │              │                 │
┌─────────┼──────────────┼─────────────────┼──────┐
│         │   Hardware Abstraction Layer   │      │
│  ┌──────▼──────┐  ┌───▼───────┐  ┌──────▼────┐ │
│  │   H-Bridge  │  │  NimBLE   │  │    NVS    │ │
│  │   (PWM)     │  │  (GATT)   │  │  (Flash)  │ │
│  └─────────────┘  └───────────┘  └───────────┘ │
└──────────────────────────────────────────────────┘
```

---

## Next Steps

### For Developers

1. **Explore the codebase**: See [CLAUDE.md](CLAUDE.md) for AI reference guide
2. **Understand decisions**: See [docs/architecture_decisions.md](docs/architecture_decisions.md) for design rationale
3. **Review requirements**: See [docs/requirements_spec.md](docs/requirements_spec.md) for full specification

### For Users

1. Build and test on hardware
2. Verify all 4 modes work correctly
3. Test BLE connection with mobile app
4. Conduct therapeutic sessions
5. Report any issues on GitHub

### For Researchers

1. Review back-EMF sampling code (first 10s of mode changes)
2. Analyze motor duty cycle effects on battery life
3. Test custom frequency/duty cycle parameters via BLE
4. Document therapeutic effectiveness findings

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main project overview |
| [CLAUDE.md](CLAUDE.md) | AI reference guide (comprehensive) |
| **QUICK_START.md** | This guide - Get started quickly |
| [BUILD_COMMANDS.md](BUILD_COMMANDS.md) | Essential build commands |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [docs/architecture_decisions.md](docs/architecture_decisions.md) | 34 design decisions (AD format) |
| [docs/requirements_spec.md](docs/requirements_spec.md) | Full requirements specification |
| [test/README.md](test/README.md) | Test program overview |

---

## Success! 🎉

You now have **production-ready, JPL-compliant** embedded software running on your device!

**Key Features:**
- ✅ Professional-grade code quality
- ✅ Full BLE mobile app control
- ✅ Proper software architecture
- ✅ Comprehensive error handling
- ✅ Safety features (LVO, clean shutdown)
- ✅ Ready for therapeutic applications

**Questions or issues?** See [CLAUDE.md](CLAUDE.md) for comprehensive reference or check the documentation index above.

---

**This is deployment-quality code - Ready to help people!** 💜
