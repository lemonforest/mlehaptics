# Engineering Documentation Verification Guide

**Agent:** `engineering-verification`
**Model:** Sonnet 4.5 (fast, cost-effective)
**Purpose:** Verify technical accuracy of documentation after component changes

---

## What It Does

The engineering verification agent checks your documentation for:

1. **Circuit Equations**
   - RC time constants (τ = R × C)
   - Voltage dividers (Vout = Vin × R2/(R1+R2))
   - Filter cutoff frequencies (fc = 1/(2πRC))
   - ADC conversion formulas
   - Current limiting calculations

2. **Power Calculations**
   - Battery life estimates
   - Current consumption totals
   - Duty cycle mathematics
   - Efficiency calculations

3. **Signal Timing**
   - PWM frequencies and LEDC constraints
   - Motor timing cycles
   - BEMF sampling windows
   - Watchdog timeout margins

4. **Cross-References**
   - Component values mentioned in multiple files
   - GPIO pin assignments
   - Mode descriptions across docs

---

## How to Use It

### Method 1: Automatic Trigger (Pre-Commit Hook)

When you commit changes to technical files, the pre-commit hook will remind you:

```bash
git commit -m "[Hardware] Update BEMF capacitor to 22nF"

# Output:
🔍 Engineering verification triggered by: test/single_device_ble_gatt_test.c

═══════════════════════════════════════════════════════════════
  Engineering Verification Recommended
═══════════════════════════════════════════════════════════════

Technical files modified. Consider running verification agent:

  Ask Claude Code: "Run engineering-verification agent"
```

Then in Claude Code:
```
Run engineering-verification agent
```

### Method 2: Manual Invocation (Slash Command)

For on-demand audits:

```
/verify-docs
```

### Method 3: Direct Agent Call

For specific file checks:

```
Use the engineering-verification subagent to check if the BEMF filter
calculations in docs/architecture_decisions.md match the new 22nF capacitor
value in test/single_device_ble_gatt_test.c
```

---

## What the Agent Reports

The agent returns a structured report like this:

```markdown
# Engineering Documentation Verification Report

## Executive Summary
- ✅ Verified correct: 12 items
- ⚠️  Warnings: 1 item
- ❌ Issues requiring correction: 2 items

## 🔴 CRITICAL ISSUES

### Issue #1: BEMF Time Constant Calculation Outdated

**Locations:**
- CLAUDE.md:142
- docs/architecture_decisions.md:89

**Problem:**
Documentation claims τ = 0.33ms but current values yield τ = 0.484ms

**Evidence:**
Code (source of truth):
- test/single_device_ble_gatt_test.c:85: C = 22nF
- test/single_device_ble_gatt_test.c:84: R = 22kΩ

Calculation:
τ = 22kΩ × 22nF = 484µs = 0.484ms

**Suggested Correction:**
[Specific file:line edits provided]
```

**Important:** The agent never modifies files itself. It reports findings to you, and you decide what to change.

---

## Source of Truth Hierarchy

When the agent finds conflicting values, it uses this priority:

1. **Code `#define` values** → Runtime truth (what's executing)
2. **Code comments** → Developer intent
3. **Documentation equations** → Derived calculations
4. **Hardware files (KiCAD)** → Design intent (may lag)

**Special case:** If docs say "PCB v0.X uses [old], prototype uses [new]", both are considered valid.

---

## Tolerance for Approximations

The agent knows documentation uses rounded values for readability:

| Type | Tolerance | Example |
|------|-----------|---------|
| Battery life | ±10% | "~20 minutes" OK if 18-22 min |
| Improvement ratios | ±2% | "4× improvement" OK if 3.92×-4.08× |
| Time constants | ±1-5% | Depends on criticality |
| Percentages | ±0.5% | Duty cycle calculations |
| Frequencies | ±1% | PWM, oscillator specs |

---

## Files Automatically Scanned

**Code files (source of truth):**
- `test/*.c` - All test implementations
- `src/*.c` - Main source files

**Documentation:**
- `CLAUDE.md` - Project reference
- `docs/*.md` - Technical documentation
- `test/*.md` - Test-specific guides
- `SESSION_SUMMARY_*.md` - Development logs
- `README.md` - Project overview

**Hardware:**
- `hardware/pcb/*BOM*` - Bill of materials
- `platformio.ini` - Build configs with timing constants
- `sdkconfig.*` - ESP-IDF peripheral settings

---

## Triggers for Verification

**Automatic pre-commit triggers:**
- ✅ Component value changes (`#define CAPACITOR_VALUE`)
- ✅ Timing constant changes (delays, frequencies)
- ✅ GPIO pin reassignments
- ✅ Equation edits in documentation
- ✅ Power calculation updates

**Manual triggers:**
- ✅ After PCB revision (BOM changes)
- ✅ Before releasing documentation
- ✅ Periodic audits (monthly/quarterly)
- ✅ When cross-file consistency is suspect

---

## What the Agent Skips

The agent **does not** verify:

- ❌ External datasheet claims (trusted unless contradicted by empirical evidence)
- ❌ ESP-IDF documentation references (assumed correct)
- ❌ EMDRIA therapeutic standards (domain expertise required)
- ❌ Code syntax or compilation (that's the compiler's job)
- ❌ Hardware feasibility (assumes you know your design works)

The agent only checks **internal consistency** within your project documentation.

---

## Workflow Example

### Scenario: You change BEMF capacitor from 15nF to 22nF

**Step 1:** Update code
```c
// test/single_device_ble_gatt_test.c:85
#define BEMF_CAPACITOR_NF 22  // Changed from 15nF
```

**Step 2:** Commit change
```bash
git add test/single_device_ble_gatt_test.c
git commit -m "[Hardware] Update BEMF capacitor to 22nF for production BOM"

# Pre-commit hook reminds you to verify docs
```

**Step 3:** Run verification
```
/verify-docs
```

**Step 4:** Review agent findings
```
Issue #1: BEMF time constant in CLAUDE.md:142 still shows 0.33ms (old value)
Suggested fix: Update to τ = 22kΩ × 22nF = 0.484ms
```

**Step 5:** Make corrections
```
Claude, please update CLAUDE.md:142 to reflect the new time constant of 0.484ms
```

**Step 6:** Verify corrections
```
/verify-docs
# Should now show: ✅ All verified correct
```

**Step 7:** Commit doc updates
```bash
git add CLAUDE.md
git commit -m "[Docs] Update BEMF time constant for 22nF capacitor"
git push
```

---

## Tips for Best Results

### Be Explicit About Changes

When you modify component values, update the code comment:

```c
// GOOD:
#define BEMF_FILTER_CAPACITOR_NF 22  // Production BOM: 22nF, Old prototype: 15nF

// BAD:
#define BEMF_FILTER_CAPACITOR_NF 22  // Just a number, no context
```

This helps the agent understand when both values are intentionally documented.

### Use Descriptive #defines

```c
// GOOD:
#define MOTOR_DUTY_CYCLE_MS 125
#define MOTOR_PERIOD_MS 500

// LESS GOOD:
#define DELAY_1 125
#define DELAY_2 500
```

The agent searches for component names in documentation. Clear names improve matching.

### Keep Calculations Visible

In documentation, show your work:

```markdown
# GOOD:
Battery life estimate:
- Capacity: 2 × 320mAh = 640mAh
- Average current: 102.5mA (see breakdown below)
- Runtime: 640mAh / 102.5mA = 6.24 hours

# LESS GOOD:
Battery life: ~6 hours
```

The agent can verify shown calculations but can only flag unexplained claims.

---

## Future Enhancements (Not Yet Implemented)

Ideas for future versions:

1. **Deep audit agent (Opus):** Create `engineering-verification-deep.md` using Opus 4.1 for more complex interdependency analysis
2. **Automatic correction mode:** Agent proposes edits, main agent applies them with user approval
3. **Continuous monitoring:** Watch mode that checks docs in background during development
4. **Unit test generation:** Generate test cases for equations to catch regressions
5. **Hardware-in-loop validation:** Cross-check claims against actual measurements from devices

---

## Troubleshooting

### "Agent finds false positives"

**Cause:** Documentation uses intentional approximations
**Fix:** Agent applies tolerances (±10% for battery life, etc.). If too strict, update tolerances in agent prompt.

### "Agent misses an error I can see"

**Cause:** Component not following naming conventions or agent search patterns incomplete
**Fix:** Report the miss. Update agent's search patterns to catch similar cases in future.

### "Pre-commit hook doesn't trigger"

**Cause:** Modified file doesn't match trigger patterns
**Fix:** Check `.git/hooks/pre-commit` patterns. Add your file pattern if it should trigger.

**Example:**
```bash
# Add to TRIGGER_PATTERNS array:
"custom_configs/.*\\.h$"    # Custom header files
```

### "Agent report is too verbose"

**Cause:** Full audit scans many files
**Fix:** Use targeted queries instead:
```
Use engineering-verification agent to check only the BEMF filter equations
in docs/architecture_decisions.md against code values
```

---

## Related Documentation

- **Agent Definition:** `.claude/agents/engineering-verification.md` (see agent prompt and methodology)
- **State Machine Analyzer:** `.claude/agents/state-machine-analyzer.md` (complementary code analysis)
- **Build Commands:** `BUILD_COMMANDS.md` (essential build references)
- **Architecture Decisions:** `docs/architecture_decisions.md` (design rationale with equations)

---

## Questions?

The agent is designed to be helpful but non-intrusive. If you find it too aggressive or too lenient, you can adjust:

- **Tolerances:** Edit `.claude/agents/engineering-verification.md` Phase 3 tolerance thresholds
- **Triggers:** Edit `.git/hooks/pre-commit` TRIGGER_PATTERNS array
- **Scope:** Modify agent prompt to focus on specific areas (e.g., skip power calcs, focus on circuits)

The agent learns from your feedback. If it consistently misses something or flags false positives, that's useful information to refine the prompts.
