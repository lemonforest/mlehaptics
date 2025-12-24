# Single Device Demo Test - Fresh Start Tracker
**Date:** November 2, 2025  
**Purpose:** Track all files and documentation that reference single_device_demo_test for clean restart

---

## Status: READY TO START FRESH
We're removing the existing WDT-compliant implementation and starting over with a simpler approach (no WDT requirements for now).

---

## Files to Delete/Archive

### 1. Test Implementation (ARCHIVE FIRST)
```
test/single_device_demo_test.c              → Archive to: test/archive/single_device_demo_test_v1_wdt.c
test/single_device_demo_test_original.c     → Can delete (already archived)
```

**Action:** Rename current test to archive, keeping it for reference if needed.

### 2. Build Artifacts (SAFE TO DELETE)
```
.pio/build/single_device_demo_test/         → Delete (will rebuild)
sdkconfig.single_device_demo_test           → Delete (will regenerate)
```

**Action:** Clean build system will handle these automatically.

---

## Files to Update

### 1. platformio.ini
**Location:** `C:\AI_PROJECTS\EMDR_PULSER_SONNET4\platformio.ini`  
**Lines:** ~410-425 (approximately)

**Current entry:**
```ini
[env:single_device_demo_test]
extends = env:xiao_esp32c6

build_flags = 
    ${env:xiao_esp32c6.build_flags}
    -DHARDWARE_TEST=1            ; Flag to indicate hardware test mode
    -DDEBUG_LEVEL=3              ; Verbose logging for test observation

; Note: Source file selection handled by extra_scripts in base environment
```

**Action:** KEEP AS-IS (environment definition stays the same)

---

### 2. scripts/select_source.py
**Location:** `C:\AI_PROJECTS\EMDR_PULSER_SONNET4\scripts\select_source.py`  
**Lines:** ~13-25 (approximately)

**Current mapping:**
```python
source_map = {
    "xiao_esp32c6": "main.c",
    "xiao_esp32c6_production": "main.c",
    "xiao_esp32c6_testing": "main.c",
    "hbridge_test": "../test/hbridge_test.c",
    "hbridge_pwm_test": "../test/hbridge_pwm_test.c",
    "ledc_blink_test": "../test/ledc_blink_test.c",
    "button_deepsleep_test": "../test/button_deepsleep_test.c",
    "ws2812b_test": "../test/ws2812b_test.c",
    "single_device_demo_test": "../test/single_device_demo_test.c",  # ← This line
    "battery_voltage_test": "../test/battery_voltage_test.c",
}
```

**Action:** KEEP AS-IS (will point to new implementation)

---

## Documentation to Update

### 1. test/SINGLE_DEVICE_DEMO_TEST_GUIDE.md
**Location:** `C:\AI_PROJECTS\EMDR_PULSER_SONNET4\test\SINGLE_DEVICE_DEMO_TEST_GUIDE.md`  
**Status:** **ARCHIVE AND REWRITE**

**Action:**
```bash
# Archive old guide
mv test/SINGLE_DEVICE_DEMO_TEST_GUIDE.md test/archive/SINGLE_DEVICE_DEMO_TEST_GUIDE_v1_wdt.md

# Create new simplified guide after new implementation
```

**New guide should cover:**
- Simplified architecture (no WDT complexity)
- Basic 4-mode operation
- Button cycling
- LED indication
- Deep sleep (simple version)

---

### 2. docs/SINGLE_DEVICE_DEMO_RESEARCH_SPEC.md
**Location:** `C:\AI_PROJECTS\EMDR_PULSER_SONNET4\docs\SINGLE_DEVICE_DEMO_RESEARCH_SPEC.md`  
**Status:** **UPDATE SECTIONS**

**Sections to update:**
1. **JPL Compliance Requirements** → Mark as "Deferred to Phase 2"
2. **Watchdog Feeding Strategy** → Remove or mark as "Not implemented in v2"
3. **Implementation complexity** → Simplify descriptions
4. **Code Structure Template** → Simplify to basic structure

**Action:** Update after new implementation is working

---

### 3. Project file (your uploaded document)
**Location:** `/mnt/project/purple_blink_logic_analysis.md`  
**Status:** **OBSOLETE** (was analyzing the WDT-compliant version)

**Action:** This document becomes historical reference only. We'll create new analysis docs for the simplified version if needed.

---

### 4. test/README.md
**Location:** `C:\AI_PROJECTS\EMDR_PULSER_SONNET4\test\README.md`

**Find section about single_device_demo_test and update:**

**Old description (probably says something about WDT, JPL compliance, etc.)**

**New description should be:**
```markdown
### 6. Single Device Demo Test (`single_device_demo_test.c`)

**Purpose:** Simple 4-mode EMDR research study (no WDT complexity)

**Test Sequence:**
- 4 modes: frequency (0.5Hz, 1Hz) × duty cycle (50%, 25%)
- 20-minute session with button mode cycling
- LED visual indication for mode
- Simplified deep sleep (no watchdog requirements)

**Build & Run:**
```bash
pio run -e single_device_demo_test -t upload && pio device monitor
```
```

---

### 5. BUILD_COMMANDS.md
**Location:** `C:\AI_PROJECTS\EMDR_PULSER_SONNET4\BUILD_COMMANDS.md`

**Find the single_device_demo_test row in the table:**

**Current (probably says something about 20min, 4 modes, WDT, etc.)**

**Update to:**
```markdown
| `single_device_demo_test` | Simple 4-mode test (0.5/1Hz, 25/50% duty), 20min, no WDT | `pio run -e single_device_demo_test -t upload && pio device monitor` |
```

---

## Documents That DON'T Need Updates

These files either don't mention single_device_demo_test or only reference it in passing:

✅ `docs/ai_context.md` - May mention it, but as historical context (OK to leave)  
✅ `docs/architecture_decisions.md` - ADxxx decisions remain valid  
✅ `docs/GPIO_UPDATE_2025-10-17.md` - Hardware docs unchanged  
✅ `docs/requirements_spec.md` - High-level requirements unchanged  
✅ `src/CMakeLists.txt` - Auto-updated by select_source.py  

---

## New Implementation Strategy

### Simplified Requirements (v2 - No WDT)

**Core functionality:**
1. ✅ 4 modes with different frequencies and duty cycles
2. ✅ Button press to cycle modes
3. ✅ LED indication showing current mode
4. ✅ 20-minute session timer
5. ✅ Deep sleep after session

**Removed complexity:**
1. ❌ No task watchdog requirements
2. ❌ No JPL compliance strictness (for now)
3. ❌ No complex task synchronization
4. ❌ No FreeRTOS advanced features

**Simple architecture:**
```c
void app_main(void) {
    init_hardware();
    
    while (session_active) {
        check_button();          // Simple polling
        run_motor_cycle();       // Simple delays
        update_led();            // Simple on/off
        check_time();            // Simple timer
    }
    
    enter_deep_sleep();          // Simple sleep entry
}
```

---

## Step-by-Step Fresh Start Process

### Phase 1: Clean Slate
```bash
# 1. Archive existing implementation
cd test
mkdir -p archive
mv single_device_demo_test.c archive/single_device_demo_test_v1_wdt.c
mv SINGLE_DEVICE_DEMO_TEST_GUIDE.md archive/SINGLE_DEVICE_DEMO_TEST_GUIDE_v1_wdt.md

# 2. Clean build artifacts
cd ..
pio run -e single_device_demo_test -t clean
rm -f sdkconfig.single_device_demo_test
rm -rf .pio/build/single_device_demo_test
```

### Phase 2: Create New Implementation
```bash
# 3. Create new simple test file
touch test/single_device_demo_test.c
# (Implement simplified version)
```

### Phase 3: Test and Validate
```bash
# 4. Build and test
pio run -e single_device_demo_test -t upload && pio device monitor

# 5. Verify basic functionality
# - Does it compile?
# - Does it run?
# - Do modes work?
# - Does button work?
# - Does sleep work?
```

### Phase 4: Update Documentation
```bash
# 6. Create new guide
# Write simplified guide based on actual behavior

# 7. Update reference docs
# Update test/README.md, BUILD_COMMANDS.md, etc.
```

---

## Quick Reference: What Stays vs What Goes

### ✅ KEEP (Still Valid)
- Hardware configuration (GPIO pins, motor control, LED control)
- 4-mode research design (frequencies and duty cycles)
- 20-minute session duration
- Button cycling behavior
- Deep sleep wake-on-button
- Overall project structure and build system

### ❌ REMOVE (Too Complex for Now)
- Watchdog timer requirements
- FreeRTOS task coordination complexity
- Purple blink wait-to-sleep logic with WDT feeding
- Task synchronization with notifications
- JPL compliance enforcement
- Complex error handling

### 🔄 SIMPLIFY (Keep Concept, Reduce Complexity)
- Motor control: Direct GPIO control instead of tasks
- LED indication: Simple on/off instead of task-based blinking
- Button handling: Simple polling instead of task with state machine
- Sleep entry: Direct call instead of task coordination
- Timing: Simple delays instead of task delays with watchdog considerations

---

## Testing Checklist for New Implementation

### Basic Functionality
- [ ] Compiles without errors
- [ ] Uploads to board successfully
- [ ] Boots and initializes hardware
- [ ] Mode 1 runs (1Hz @ 50%)
- [ ] Mode 2 runs (1Hz @ 25%)
- [ ] Mode 3 runs (0.5Hz @ 50%)
- [ ] Mode 4 runs (0.5Hz @ 25%)

### Button Functionality
- [ ] Button press cycles modes (1→2→3→4→1)
- [ ] No double-triggers or bouncing issues
- [ ] Console shows mode change messages

### LED Indication
- [ ] LED shows which mode is active
- [ ] LED brightness appropriate (20%)
- [ ] LED turns off after indication period

### Session Management
- [ ] Session runs for 20 minutes
- [ ] Session auto-sleeps at end
- [ ] Timer accurate (check with stopwatch)

### Deep Sleep
- [ ] Device enters sleep after session
- [ ] Button press wakes device
- [ ] New session starts correctly

### Reliability
- [ ] No crashes or resets during session
- [ ] Stable operation over full 20 minutes
- [ ] Consistent behavior across power cycles

---

## Communication Plan

When asking Claude for help with the new implementation:

### ✅ DO Say:
- "Let's create a simple single_device_demo_test without WDT complexity"
- "I want basic 4-mode operation with simple delays"
- "Just get it working first, we'll add sophistication later"
- "Reference the working tests: hbridge_pwm_test, ws2812b_test, button_deepsleep_test"

### ❌ DON'T Say:
- "Make it JPL compliant"
- "Add watchdog timer feeding"
- "Implement task synchronization"
- "Follow the architecture from the old version"

---

## Archive Locations

When we archive the old implementation:

```
test/archive/
├── single_device_demo_test_v1_wdt.c              # Old WDT-compliant code
├── SINGLE_DEVICE_DEMO_TEST_GUIDE_v1_wdt.md       # Old comprehensive guide
└── purple_blink_logic_analysis.md                # Your uploaded analysis doc
```

**Reason for archiving:** Good reference material, but represents a complexity level we're stepping back from temporarily.

---

## Success Criteria for Fresh Start

The new implementation is successful when:

1. ✅ Compiles and runs without WDT or task complexity
2. ✅ All 4 modes work reliably
3. ✅ Button cycling works consistently
4. ✅ LED indication is clear
5. ✅ Full 20-minute session completes
6. ✅ Deep sleep and wake work reliably
7. ✅ Code is simple enough to understand and modify easily

**Target:** Working prototype in 1-2 implementation sessions, not weeks of debugging.

---

## Next Steps

1. **Archive** existing implementation (if you want to keep it)
2. **Clean** build artifacts
3. **Create** new simple test file
4. **Reference** working tests (hbridge_pwm, ws2812b, button_deepsleep)
5. **Build** incrementally: first mode only, then add others
6. **Test** thoroughly at each step
7. **Document** actual behavior (not planned complexity)

---

**Ready to start fresh!** 🚀

Let me know when you want to begin the new simplified implementation.
