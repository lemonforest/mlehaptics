# ULP-Coordinated H-Bridge Test

## Overview

This test demonstrates battery-efficient bilateral motor control using the ESP32-C6's dual-core architecture:

- **LP Core (ULP)**: Low-power RISC-V core running at ~17MHz (~100µA)
- **HP Core**: High-performance core with light sleep capability (~1-2mA idle, ~50mA active)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ LP Core (ULP RISC-V @ 17MHz)                       │
│  • Runs continuously (~100µA power)                 │
│  • Manages bilateral timing (500ms half-cycles)     │
│  • Generates motor commands                         │
│  • Wakes HP core when needed                        │
│  • Never sleeps (always monitoring)                 │
└────────────────┬────────────────────────────────────┘
                 │ Wake signal
                 ▼
┌─────────────────────────────────────────────────────┐
│ HP Core (RISC-V @ 160MHz)                          │
│  • Light sleep most of time (~1-2mA)                │
│  • Wakes on ULP command                             │
│  • Executes PWM motor control (~50mA)               │
│  • Returns to light sleep                           │
│  • Active ~5-10% of time                            │
└─────────────────────────────────────────────────────┘
```

## Power Consumption

| Mode | Current | % of Time |
|------|---------|-----------|
| LP core timing | 100µA | 100% |
| HP core light sleep | 1-2mA | 90-95% |
| HP core PWM active | 50mA | 5-10% |
| **Average Total** | **~5-10mA** | **100%** |

Compare to continuous HP core operation: ~50mA (5-10x higher!)

## How It Works

### 1. ULP Program (`ulp/ulp_motor_control.c`)

```c
// Runs on LP core continuously
while (true) {
    if (time_for_next_phase) {
        toggle_motor_direction();
        ulp_motor_command = current_phase;
        ulp_riscv_wakeup_main_processor();  // Wake HP core
        next_wake_time = now + 500ms;
    }
    ulp_riscv_delay_cycles(10ms);  // Check every 10ms
}
```

### 2. HP Program (`test/ulp_hbridge_test.c`)

```c
// Runs on HP core
while (true) {
    if (ulp_motor_command != CMD_NONE) {
        execute_motor_command();     // PWM control
        ulp_motor_command = CMD_NONE;
    }
    esp_light_sleep_start();  // Sleep until ULP wakes us
}
```

## Expected Serial Output

```
✓ ULP binary loaded (256 bytes)
✓ ULP core running (LP @ ~17MHz, <100µA)
✓ Light sleep configured (HP core: ~1-2mA when idle)
═══════════════════════════════════════════════════════════
✓ System Ready - ULP controlling bilateral timing
  HP core will sleep and wake automatically
  Monitor: Wake count, cycle count, power consumption
═══════════════════════════════════════════════════════════

→ FORWARD @ 60% (ULP wake #1)
💤 HP core → light sleep (ULP continues)
⏰ HP core ← woken by ULP
← REVERSE @ 60% (ULP wake #2)
💤 HP core → light sleep (ULP continues)
⏰ HP core ← woken by ULP
→ FORWARD @ 60% (ULP wake #3)
📊 Stats: Wakes=10, ULP_Cycles=5000
```

## Measuring Power Consumption

### Method 1: Multimeter in Series with Battery

1. Disconnect USB power
2. Connect battery through multimeter (µA/mA range)
3. Observe average current draw
4. Expected: ~5-10mA average

### Method 2: ESP32-C6 Built-in Current Monitor

```c
// Future enhancement - add to test
float current_ma = esp_current_monitor_get_average_ma();
ESP_LOGI(TAG, "Average current: %.2f mA", current_ma);
```

## Troubleshooting

### ULP binary load failed

**Error**: `ULP binary load failed: ESP_ERR_INVALID_SIZE`

**Solution**: Check that `ulp/ulp_motor_control.c` is being compiled. The ULP CMakeLists.txt should create the binary automatically.

### HP core never wakes

**Error**: No motor activity, only "HP core → light sleep" messages

**Solutions**:
1. Check ULP program is running: `ulp_cycle_count` should increase
2. Verify wake source enabled: `esp_sleep_enable_ulp_wakeup()`
3. Check ULP program logic: Is `ulp_riscv_wakeup_main_processor()` being called?

### Motor runs but no power savings

**Error**: Current consumption still ~50mA

**Solutions**:
1. Verify light sleep is configured: Check `configure_light_sleep()` was called
2. Check for busy-wait loops preventing sleep
3. Verify HP core is entering sleep: Add debug logging in sleep/wake cycle
4. Check LEDC PWM continues during sleep (should be automatic)

### ULP cycles not incrementing

**Error**: `ULP_Cycles=0` stays at zero

**Solutions**:
1. ULP program may have crashed - check ULP program logic
2. Verify ULP was started: `ulp_riscv_run()` should return `ESP_OK`
3. Check ULP program infinite loop structure

## Build and Run

```bash
# Build and upload
pio run -e ulp_hbridge_test -t upload

# Monitor serial output
pio device monitor

# Or combined
pio run -e ulp_hbridge_test -t upload && pio device monitor
```

## Development Notes

### Modifying ULP Program

1. Edit `ulp/ulp_motor_control.c`
2. Rebuild (CMake automatically compiles ULP binary)
3. Upload to device (ULP binary embedded in main firmware)

### Changing Bilateral Timing

```c
// In ulp_hbridge_test.c initialization
ulp_half_cycle_ms = 250;  // 250ms half-cycle = 500ms total (2 Hz)
ulp_half_cycle_ms = 500;  // 500ms half-cycle = 1000ms total (1 Hz)
ulp_half_cycle_ms = 1000; // 1000ms half-cycle = 2000ms total (0.5 Hz)
```

### Adding More Commands

```c
// In both ULP and HP code
typedef enum {
    CMD_NONE = 0,
    CMD_FORWARD,
    CMD_REVERSE,
    CMD_COAST,
    CMD_BRAKE,       // New: active braking
    CMD_HAPTIC_PULSE // New: short pulse
} motor_command_t;
```

## Design Decisions

### Why ULP for Timing?

1. **Power efficiency**: 100µA vs 50mA continuous HP core
2. **Real-time guarantee**: LP core never interrupted by other tasks
3. **Battery life**: Enables 20+ minute therapeutic sessions
4. **Scalability**: Foundation for production bilateral device

### Why Not Pure HP Core?

| Approach | Power | Pros | Cons |
|----------|-------|------|------|
| Pure HP | 50mA | Simple | High power, short battery life |
| HP + Light Sleep | 5-10mA | Moderate power | Complex wake logic |
| **ULP + HP Sleep** | **5-10mA** | **Best power** | **Slightly complex** |

### Why 500ms Half-Cycles?

- Standard EMDR therapeutic rate: 1 Hz bilateral
- Total cycle: 1000ms (500ms per device)
- Configurable: 250ms to 1000ms half-cycles (0.5-2 Hz)

## Future Enhancements

1. **Dynamic cycle adjustment**: BLE commands to change ulp_half_cycle_ms
2. **Wake-only mode**: HP core wakes only when button pressed
3. **Power monitoring**: Real-time current measurement via ADC
4. **Haptic effects**: Short pulses within half-cycle windows
5. **Deep sleep**: HP + LP both sleep between sessions (button wake)

## Related Files

- `ulp/ulp_motor_control.c` - LP core program
- `test/ulp_hbridge_test.c` - HP core test program
- `ulp/CMakeLists.txt` - ULP build configuration
- `platformio.ini` - Build environment (ulp_hbridge_test)
- `BUILD_COMMANDS.md` - Quick reference commands

## References

- [ESP32-C6 ULP RISC-V Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/system/ulp_riscv.html)
- [ESP32-C6 Low Power Management](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/system/sleep_modes.html)
- Architecture Decisions: `docs/architecture_decisions.md` (AD020)
- Requirements Spec: `docs/requirements_spec.md` (PF004)
