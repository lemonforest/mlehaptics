# Documentation Prompt: Deep Sleep Wake State Machine Pattern

**Use this prompt in a new Claude chat to document the deep sleep/wake pattern in planning docs.**

---

## Context

I need to document a critical implementation pattern for deep sleep and wake-from-sleep functionality in my EMDR Pulser project. This pattern was developed through hardware testing and addresses ESP32-C6 ext1 wake limitations.

**Project Location:** `\AI_PROJECTS\EMDR_PULSER_SONNET4`

**Review These Files First:**
- `docs/architecture_decisions.md` - Format for new AD entries
- `docs/ai_context.md` - Project DNA and API contracts
- `test/button_deepsleep_test.c` - Working implementation reference
- `test/BUTTON_DEEPSLEEP_TEST_GUIDE.md` - Implementation details

---

## What Needs Documentation

### Problem We Solved

ESP32-C6 ext1 wake is **level-triggered**, not edge-triggered. This creates a challenge:

**Initial Problem:**
- User holds button through countdown to trigger deep sleep
- Device enters sleep while button is LOW (pressed)
- ext1 configured to wake on LOW
- Device wakes immediately because button is still LOW
- Can't distinguish "still held from countdown" vs "new button press"

**Failed Approaches Tried:**
1. **Wake immediately, check state, re-sleep if held**
   - Problem: After button released (goes HIGH), ext1 still waiting for LOW
   - Device stuck sleeping, can't detect new press
   - Fundamental misunderstanding of level-triggered wake

2. **State machine with wake-on-HIGH support**
   - Read button before sleep: if LOW, configure wake on HIGH (release)
   - On wake from HIGH, reconfigure to LOW and re-sleep
   - Problem: ESP32-C6 ext1 might not support wake on HIGH reliably
   - Too complex for hardware limitations

### Solution Implemented

**Wait-for-Release with LED Blink Feedback:**

```c
void enter_deep_sleep(void) {
    // If button held after countdown, wait for release
    if (gpio_get_level(GPIO_BUTTON) == 0) {
        ESP_LOGI("Waiting for button release...");
        
        // Blink LED while waiting (visual feedback without serial)
        while (gpio_get_level(GPIO_BUTTON) == 0) {
            blink_led_fast();
            vTaskDelay(pdMS_TO_TICKS(200));
        }
        
        ESP_LOGI("Button released!");
    }
    
    // Always configure ext1 to wake on LOW (button press)
    configure_ext1_wake_on_LOW();
    
    // Enter deep sleep (button guaranteed HIGH at this point)
    esp_deep_sleep_start();
}
```

**Key Features:**
- LED blinks rapidly while waiting for release (no serial monitor needed)
- Guarantees button is HIGH before sleep entry
- ext1 always configured for wake-on-LOW (next press)
- Next wake is guaranteed to be NEW button press
- Simple, bulletproof, user-friendly

**User Experience:**
1. Hold button 6 seconds → Countdown
2. LED blinks fast → Visual cue to release
3. Release button → Device sleeps
4. Press button → Device wakes (guaranteed new press)

---

## Deliverables Needed

### 1. New Architecture Decision

Create **AD023: Deep Sleep Wake State Machine for ESP32-C6 ext1**

Include in `docs/architecture_decisions.md`:

**Structure:**
```markdown
### AD023: Deep Sleep Wake State Machine for ESP32-C6 ext1

**Decision**: Use wait-for-release with LED blink feedback before deep sleep entry

**Problem Statement:**
ESP32-C6 ext1 wake is level-triggered, not edge-triggered...
[Full problem description]

**Alternatives Considered:**
1. **Immediate re-sleep with state checking**: ❌ Rejected - device stuck after release
2. **State machine with wake-on-HIGH**: ❌ Rejected - ESP32-C6 ext1 limitations
3. **Wait-for-release with LED blink**: ✅ Chosen - simple and bulletproof

**Solution Architecture:**
[Implementation details]

**Rationale:**
- Works within ESP32-C6 hardware limitations
- Visual feedback without serial monitor
- Guarantees wake-on-new-press
- Simple and maintainable

**Implementation Pattern:**
[Code pattern to replicate]

**JPL Compliance:**
- All delays use vTaskDelay() (no busy-wait)
- Bounded loop (only runs while button held)
- Predictable behavior

**Verification:**
[How to verify this pattern works]
```

### 2. Update API Contracts in ai_context.md

Add/update the button handler API to include deep sleep pattern:

```c
/**
 * @brief Enter deep sleep with guaranteed wake-on-new-press
 * @return Does not return (device sleeps)
 * 
 * ESP32-C6 ext1 wake pattern:
 * 1. Check button state
 * 2. If LOW (held): Blink LED while waiting for release
 * 3. Once HIGH: Configure ext1 wake on LOW
 * 4. Enter deep sleep (button guaranteed released)
 * 5. Next wake guaranteed to be NEW button press
 * 
 * Visual feedback: LED blinks at 5Hz while waiting for release
 * No serial monitor required for user to know when to release
 * 
 * JPL Compliant: Uses vTaskDelay() for all timing
 */
esp_err_t enter_deep_sleep_with_wake_guarantee(void);
```

### 3. Create Quick Reference Section

Add to `docs/ai_context.md` under a new section:

```markdown
## Deep Sleep and Wake Patterns

### ESP32-C6 ext1 Wake Limitation

ext1 wake is **level-triggered**, not edge-triggered:
- Wake condition: GPIO is LOW (button pressed)
- Not an edge detection (no press "event")
- If GPIO is LOW when sleeping → wakes immediately

### Guaranteed Wake-on-New-Press Pattern

**Always use this pattern for button-triggered deep sleep:**

1. Wait for button release before sleep
2. Provide visual feedback (LED blink) while waiting
3. Configure ext1 to wake on LOW only when button is HIGH
4. Next wake is guaranteed to be NEW press

**Reference Implementation:** `test/button_deepsleep_test.c`
```

---

## Instructions for AI

1. **Read the existing documentation patterns** from:
   - `docs/architecture_decisions.md` (AD format)
   - `docs/ai_context.md` (API contracts format)

2. **Create AD023** following the exact format of other ADs:
   - Problem Statement
   - Alternatives Considered (with ❌ rejections)
   - Solution Architecture
   - Rationale (bullet points)
   - Implementation Requirements
   - JPL Compliance notes
   - Verification strategy

3. **Update `docs/ai_context.md`**:
   - Add new API function documentation
   - Add Deep Sleep Patterns section
   - Reference the working test implementation

4. **Ensure replicability**:
   - Code patterns should be complete enough to copy
   - All edge cases documented
   - Visual feedback pattern (LED blink) documented
   - JPL compliance explicitly stated

5. **Cross-reference**:
   - Link AD023 to test implementation
   - Link ai_context.md to AD023
   - Ensure future AI can find this pattern

---

## Success Criteria

After documentation is complete:

✅ AD023 exists in architecture_decisions.md
✅ API contract in ai_context.md includes deep sleep pattern
✅ Deep Sleep Patterns section exists in ai_context.md
✅ All code patterns are copy-paste ready
✅ LED blink feedback pattern documented
✅ JPL compliance explicitly noted
✅ Future AI can replicate this exact pattern

---

## Why This Matters

This pattern solves a **hardware limitation** of ESP32-C6 ext1 wake that isn't obvious from the documentation. Without this pattern:

- Device may appear stuck sleeping
- User has no feedback on when to release button
- Wake events may be unreliable
- Implementation becomes complex and fragile

With proper documentation:

- Future code generation will use this pattern
- Other developers understand the rationale
- Pattern is preserved across refactoring
- Hardware limitations are clearly explained

---

**Generate the documentation now, ensuring all future AI code generation will replicate this exact deep sleep/wake pattern.**
