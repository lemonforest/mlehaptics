# Phase 1: Message Queue Architecture - Quick Start

**File:** `single_device_battery_bemf_queued_test.c`  
**Purpose:** JPL-compliant task isolation via FreeRTOS message queues

## What Changed

### Removed (Shared Global State):
```c
static mode_t current_mode;              // ❌ Shared between tasks
static volatile bool session_active;     // ❌ Shared
static uint32_t led_indication_start_ms; // ❌ Shared
static bool led_indication_active;       // ❌ Shared
```

### Added (Message Queues):
```c
static QueueHandle_t button_to_motor_queue;
static QueueHandle_t battery_to_motor_queue;

typedef struct {
    message_type_t type;
    union {
        mode_t new_mode;              // For mode changes
        struct {
            float voltage;
            int percentage;
        } battery;                     // For battery warnings
    } data;
} task_message_t;
```

### Message Flow:
- **Button → Motor:** Mode changes, emergency shutdown
- **Battery → Motor:** Low voltage warnings, critical shutdown

## Build & Run

```bash
pio run -e single_device_battery_bemf_queued_test -t upload && pio device monitor
```

## Expected Behavior

Identical to baseline test, but with proper task isolation:
- Motor patterns unchanged
- LED indication same
- Button response same
- Battery monitoring same
- Back-EMF sampling same

## Console Output

You'll see new log messages:
- `"Button task started"`
- `"Battery task started"`
- `"Motor task started: 1Hz@50%"`
- `"Mode change: 1Hz@25%"` (when button pressed)
- `"Emergency shutdown"` (when button held 5s)

## Testing Checklist

- [ ] Verify motor patterns match baseline
- [ ] Test mode changes (button press)
- [ ] Test emergency shutdown (button hold 5s)
- [ ] Monitor battery readings every 10s
- [ ] Verify back-EMF sampling during first 10s
- [ ] Confirm 20-minute session timeout

## JPL Compliance Achieved

✓ No shared state between tasks  
✓ All inter-task communication via queues  
✓ Error checking on queue operations  
✓ Clear data ownership  

## Next Steps

After validating Phase 1:
- **Phase 2:** Add tickless idle (config only, no code changes)
- **Phase 3:** Add explicit light sleep during coast periods

## Troubleshooting

**Issue:** Build fails with "undefined reference to xQueueCreate"  
**Fix:** Queue API is part of FreeRTOS, should work automatically

**Issue:** Device doesn't respond to button  
**Fix:** Check that messages are being sent (add ESP_LOGI before xQueueSend)

**Issue:** Behavior different from baseline  
**Fix:** This indicates a logic error - report for debugging
