# UTLP C64 HAL - Time Lords on the Breadbin

**Universal Time Lord Protocol** running on a Commodore 64.

> *"If UTLP can synchronize a 1MHz 6502 from 1982, it truly deserves the title Universal."*

## The Magic

The same `utlp_skeleton.c` that runs on ESP32-C6 compiles for C64 with **automatic C99→C89 transformation**:

```
┌─────────────────────────────────────────────────────────────────┐
│              utlp_skeleton.c  (C99 - kept clean!)               │
│                              ↓                                   │
│              c89_transform.py  (automatic at build time)        │
│                              ↓                                   │
│              utlp_skeleton.c  (C89 - for cc65)                  │
│                                                                  │
│    Boot as Genesis → Blink border → Adopt better stratum        │
├─────────────────────────────────────────────────────────────────┤
│              utlp_hal.h  (Same contract as ESP32)               │
├─────────────────────────────────────────────────────────────────┤
│           utlp_hal_c64.c  (C64-Specific Implementation)         │
│                                                                  │
│   ┌─────────┬─────────┬─────────┬─────────┐                     │
│   │  CIA    │  VIC-II │  User   │  Screen │                     │
│   │ Timers  │ Border  │  Port   │  Printf │                     │
│   │ (1MHz)  │ (sync)  │ (radio) │  (log)  │                     │
│   └─────────┴─────────┴─────────┴─────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### C99→C89 Transformation

cc65 is a C89 compiler. The build script automatically transforms C99 code:

| C99 Feature | C89 Transformation |
|-------------|-------------------|
| `for (int i = 0; ...)` | `int i; for (i = 0; ...)` |
| `#pragma once` | Traditional include guards |
| `inline` keyword | Removed (not supported) |

The transformation is done by `c89_transform.py` at build time, so:
- **The main codebase stays clean C99** (ESP32, MG24, etc.)
- **C64 gets automatically transformed** (no manual maintenance)
- **Future platforms with C99+ support work out of the box**

## Quick Start

### Prerequisites

1. **cc65 toolchain** - C compiler for 6502/6510
   - Download: https://cc65.github.io/
   - Linux: `apt install cc65`
   - macOS: `brew install cc65`
   - Windows: Download binary release

2. **VICE emulator** - For testing without real hardware
   - Download: https://vice-emu.sourceforge.io/
   - Linux: `apt install vice`
   - macOS: `brew install vice`

### Build

```bash
cd examples/utlp_c64
make
```

This will:
1. Copy `utlp_skeleton.c` from the main project (unchanged!)
2. Compile with cc65 targeting C64
3. Produce `utlp_c64.prg`

### Run in VICE

```bash
make run
```

Or manually:
```bash
x64sc utlp_c64.prg
```

### Expected Output

```
UTLP HAL C64 INITIALIZING...

========================================
UTLP GENESIS NODE
"TIME IS BORN OF ONE."
========================================
MAC: C6:40:19:82:00:01
STRATUM: 1 (GENESIS)
BEACON: SEISMIC CHIRP (3-BURST)
INTERVAL: GENESIS PULSE
BLINK PERIOD: 1000 MS
========================================

[LED] ON  @ ATOMIC=500000 US (STRATUM 1)
[LED] OFF @ ATOMIC=1000000 US (STRATUM 1)
```

The **border color** blinks at 1Hz (BLACK → WHITE → BLACK → ...).

## Hardware Mapping

| UTLP Abstraction | ESP32-C6 | C64 |
|------------------|----------|-----|
| `utlp_hal_get_micros()` | esp_timer | CIA Timer A (1MHz) |
| `utlp_hal_set_actuator_phase()` | GPIO15 LED | Border color ($D020) |
| `utlp_hal_tx_packet()` | ESP-NOW | User Port serial (Phase 2) |
| `utlp_hal_log_info()` | esp_log | Screen cprintf |

### CIA Timers - Perfect for UTLP!

The C64's CIA chips have 16-bit timers running at **985,248 Hz** (PAL) or **1,022,727 Hz** (NTSC).

This is essentially **1 MHz = 1 microsecond resolution** - exactly what UTLP needs!

```
CIA Timer A: 16-bit counter @ 1MHz (counts DOWN)
Overflow every: 65,536 µs (~65ms)
32-bit extended: ~71 minutes before wrap
```

### Border Color as "LED"

Instead of a physical LED, we use the VIC-II border color register:

| Duty Cycle | Border Color |
|------------|--------------|
| 0% (off) | BLACK |
| 100% (on) | WHITE |

Visual sync is obvious - synchronized C64s will have borders that blink in unison.

## Phase 1: Standalone (Current)

**Status:** ✅ Implemented

- Genesis Node boots immediately (no peer needed)
- Border blinks at 1Hz
- Logs to screen
- No network communication

## Phase 2: VICE Cluster (Planned)

For multi-C64 synchronization in emulation:

```
                    ┌─────────────────────────┐
                    │    UTLP Bridge Daemon   │
                    │    (tools/utlp_bridge.py)│
                    └───────────┬─────────────┘
              ┌─────────────────┼─────────────────┐
              │                 │                 │
        ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
        │  VICE #1  │     │  VICE #2  │     │  VICE #3  │
        │  Genesis  │     │  Follower │     │  Follower │
        │  :6502    │     │  :6503    │     │  :6504    │
        └───────────┘     └───────────┘     └───────────┘
```

Each VICE instance connects its User Port to the bridge daemon via TCP.
The bridge simulates ESP-NOW's broadcast behavior.

## Phase 3: Real Hardware (Stretch)

- Two real C64s with User Port serial cables
- Central hub (Raspberry Pi or ESP32) running bridge
- Border colors sync across physical machines

## Files

| File | Description |
|------|-------------|
| `utlp_hal_c64.c` | C64 HAL implementation (CIA, VIC-II, User Port) |
| `utlp_main_c64.c` | Platform entry point (`main()`) |
| `c89_transform.py` | Automatic C99→C89 transformation script |
| `build.bat` | Windows build script (auto-detects cc65/VICE) |
| `Makefile` | Linux/macOS build system |
| `README.md` | This documentation |
| **Generated at build time:** | |
| `utlp_skeleton.c` | Transformed C89 version of main project skeleton |
| `utlp_hal.h` | Transformed C89 version of HAL header |

## Technical Notes

### Memory Usage

```
Code:    ~12 KB (fits in BASIC area $0800-$9FFF)
Data:    ~2 KB (zero page + stack)
Screen:  1 KB ($0400-$07FF)
```

Total: ~15 KB of 64 KB available - plenty of headroom.

### Floating Point

cc65 has **NO floating-point support**. This is handled via compile-time abstraction:

```c
// In utlp_hal.h:
#ifdef __CC65__
    typedef uint16_t utlp_float_t;  // Fixed-point: 5000 = 50.00%
    #define UTLP_NO_FLOAT 1
#else
    typedef float utlp_float_t;     // Native float on modern platforms
#endif

// In utlp_hal_c64.c:
#if UTLP_NO_FLOAT
    if (duty_pct > 5000) {          // 5000 = 50.00% in fixed-point
        POKE(VIC_BORDER, COLOR_WHITE);
    } else {
        POKE(VIC_BORDER, COLOR_BLACK);
    }
#else
    if (duty_pct > 50.0f) { ... }   // Float on ESP32
#endif
```

Drift statistics (polynomial fitting) are disabled on C64 - sync still works, just no drift analysis.

### 64-bit Integers

`uint64_t` operations are emulated by cc65 (slow but correct).
For performance, the HAL internally uses 32-bit timestamps where possible.

32-bit microseconds wraps after ~71 minutes - acceptable for UTLP sessions.

### No Preemptive Multitasking

C64 has no OS scheduler. The main loop is cooperative:

1. Check for received packets (Phase 2)
2. Update physics (LED state from atomic time)
3. Send beacons if due
4. Yield (short delay)

## Makefile Targets

```bash
make          # Build utlp_c64.prg
make run      # Build and run in VICE
make clean    # Remove build artifacts
make disk     # Create D64 disk image for real hardware
make debug    # Build with debug symbols
make info     # Show build configuration
```

## Troubleshooting

### "cc65 not found"

Install the cc65 toolchain:
- Linux: `sudo apt install cc65`
- macOS: `brew install cc65`
- Windows: Download from https://cc65.github.io/

### "x64sc not found"

VICE emulator not installed or not in PATH:
- Linux: `sudo apt install vice`
- macOS: `brew install vice`
- Or run manually: `/path/to/vice/x64sc utlp_c64.prg`

### Build errors in utlp_skeleton.c

If `utlp_skeleton.c` fails to compile:
1. Ensure HAL purification is complete (no ESP-IDF includes)
2. Check that `utlp_hal.h` declares all required functions
3. Verify cc65 compatibility (no GNU extensions)

### Border doesn't blink

Check the VICE Monitor (Alt+H in VICE):
```
> m d020 d020
```
Should show value changing between $00 (black) and $01 (white).

## Cultural Context

> *The Commodore 64 was released in August 1982.*
>
> *If UTLP can synchronize a network of 40-year-old 8-bit computers,*
> *the protocol truly deserves the title "Universal Time Lord."*
>
> *"Time is born of one." — Even on a breadbin.*

## License

This example is part of the EMDR Bilateral Stimulation Device project.
- Software: GPL v3
- Hardware: CERN-OHL-S v2
