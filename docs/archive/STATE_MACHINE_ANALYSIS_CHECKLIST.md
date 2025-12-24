# State Machine Analysis Checklist

**Purpose:** Systematic analysis to perform after any state machine refactoring to catch logic errors before hardware testing.

**When to use:** After modifying state machine logic, adding new states, or changing state transition conditions.

---

## Analysis Process

### 1. Identify State Machine Components

- [ ] **State enum:** Find the `typedef enum` defining all states
- [ ] **State variable:** Identify the variable holding current state (e.g., `state`)
- [ ] **Loop condition:** Find the while/for loop that drives the state machine
- [ ] **Switch statement:** Locate the main state dispatcher
- [ ] **Message queues:** Identify all queues used for inter-task communication

**Example:**
```c
typedef enum { STATE_IDLE, STATE_ACTIVE, STATE_SHUTDOWN } state_t;
state_t state = STATE_IDLE;
while (state != STATE_SHUTDOWN) {
    switch (state) { ... }
}
```

---

### 2. Verify Loop Exit Conditions

For each shutdown/exit path:

- [ ] **Check loop condition:** Does the while condition properly exit when shutdown state is set?
- [ ] **Verify state assignment:** Is the shutdown state assigned correctly?
- [ ] **Look for overwrites:** Does any code path overwrite the shutdown state before loop exit?

**Common Bug Pattern:**
```c
// BAD: Shutdown state gets overwritten
if (msg.type == MSG_SHUTDOWN) {
    state = STATE_SHUTDOWN;
    break;  // Only breaks inner loop!
}
// ... more code ...
state = STATE_ACTIVE;  // ❌ Overwrites shutdown state!
```

**Fix:**
```c
if (state == STATE_SHUTDOWN) {
    break;  // Don't transition to active
}
state = STATE_ACTIVE;  // ✅ Only if not shutting down
```

---

### 3. Trace All State Transitions

For each state case:

- [ ] **Entry point:** How does execution enter this state?
- [ ] **Exit points:** What are ALL ways to exit this state?
- [ ] **Cleanup calls:** Is cleanup (motor_coast, led_clear, etc.) called in ALL exit paths?
- [ ] **State overwrites:** Could another code path overwrite the state variable?

**Verification Table Template:**
| State | Entry From | Exit To | Cleanup Called? | Notes |
|-------|-----------|---------|-----------------|-------|
| CHECK_MESSAGES | All states | FORWARD, SHUTDOWN | N/A | ❌ Check for state overwrites! |
| FORWARD_ACTIVE | CHECK_MESSAGES | BEMF, COAST, CHECK_MESSAGES | ✅ motor_coast/led_clear | Verify both sampling paths |
| SHUTDOWN | Any state | Loop exit | ✅ In cleanup section | Should just break |

---

### 4. Analyze Queue Message Handling

For each message queue:

- [ ] **Message types:** List all message types that can be received
- [ ] **Handler location:** Where is each message type processed?
- [ ] **Unhandled messages:** Are there message types that aren't handled?
- [ ] **Queue overflow:** Could rapid messages fill the queue?
- [ ] **Queue purging:** Is there logic to drain duplicate messages?

**Common Issues:**
- Shutdown message handled but state gets overwritten later
- Mode change messages queue up instead of purging duplicates
- Critical messages (shutdown, battery critical) not prioritized

---

### 5. Check Break/Continue Logic

For nested loops and switch statements:

- [ ] **Break scope:** Does `break` exit the right loop/switch?
- [ ] **Continue usage:** Does `continue` affect the correct loop?
- [ ] **Fallthrough:** Are there intentional switch case fallthroughs? (Should be commented!)

**Common Bug Pattern:**
```c
while (xQueueReceive(queue, &msg, 0) == pdPASS) {
    if (msg.type == MSG_SHUTDOWN) {
        state = STATE_SHUTDOWN;
        break;  // ❌ Only breaks inner while, NOT switch case!
    }
}
// Execution continues in same switch case!
state = STATE_SOMETHING_ELSE;  // ❌ Overwrites shutdown
```

**Fix:**
```c
while (xQueueReceive(queue, &msg, 0) == pdPASS) {
    if (msg.type == MSG_SHUTDOWN) {
        state = STATE_SHUTDOWN;
        break;
    }
}
if (state == STATE_SHUTDOWN) {
    break;  // Exit the switch case
}
state = STATE_SOMETHING_ELSE;  // ✅ Won't execute if shutting down
```

---

### 6. Verify Cleanup Paths

For each resource (motor, LED, GPIO, etc.):

- [ ] **Normal path:** Is cleanup called when operation completes normally?
- [ ] **Early exit path:** Is cleanup called when mode change interrupts?
- [ ] **Shutdown path:** Is cleanup called during emergency shutdown?
- [ ] **Error path:** Is cleanup called if an error occurs?

**Cleanup Verification Matrix:**
| Resource | Normal | Mode Change | Shutdown | Error | Notes |
|----------|--------|-------------|----------|-------|-------|
| Motor (coast) | ✅ | ✅ | ✅ | ✅ | Must ALWAYS coast before state change |
| LED (clear) | ✅ | ✅ | ✅ | ✅ | Should match motor state |
| GPIO | ✅ | ✅ | ✅ | ? | Check enable pins |

---

### 7. Look for Race Conditions

- [ ] **Shared variables:** Are any variables accessed by multiple tasks?
- [ ] **Queue access:** Are queues accessed from multiple tasks safely?
- [ ] **State variable:** Is state only modified by the state machine task?
- [ ] **Flag variables:** Are boolean flags updated atomically?

**FreeRTOS Safety:**
- Message queues are thread-safe (xQueueSend/Receive)
- Global variables need protection (mutex or atomic operations)
- Task-local state variables are safe

---

### 8. Check Timing and Delays

For each delay operation:

- [ ] **Watchdog feeding:** Is watchdog fed during long delays?
- [ ] **Message checking:** Can delays be interrupted by mode changes?
- [ ] **Overflow protection:** Are timing calculations protected from uint32_t overflow?

**Good Pattern:**
```c
// Delay that checks for messages every 50ms
bool delay_with_mode_check(uint32_t delay_ms) {
    const uint32_t CHECK_INTERVAL_MS = 50;
    uint32_t remaining_ms = delay_ms;

    while (remaining_ms > 0) {
        uint32_t this_delay = (remaining_ms < CHECK_INTERVAL_MS)
            ? remaining_ms : CHECK_INTERVAL_MS;
        vTaskDelay(pdMS_TO_TICKS(this_delay));
        remaining_ms -= this_delay;

        // Check for messages
        if (message_pending()) return true;
    }
    return false;
}
```

---

### 9. Verify State Machine Completeness

- [ ] **All states handled:** Does switch statement have cases for ALL enum values?
- [ ] **Default case:** Is there a default case to catch unexpected states?
- [ ] **Compiler warnings:** Does compiler warn about unhandled enum values?

**Best Practice:**
```c
switch (state) {
    case STATE_IDLE: ... break;
    case STATE_ACTIVE: ... break;
    case STATE_SHUTDOWN: ... break;
    // default: should NOT be needed if all states handled
}
```

Enable compiler warnings to catch missing cases:
```c
// In platformio.ini or sdkconfig
-Wswitch-enum  // Warn about unhandled enum cases
```

---

### 10. Test Edge Cases

For each state transition:

- [ ] **Rapid messages:** What if multiple messages arrive before processing?
- [ ] **Timeout during transition:** What if session timeout occurs mid-transition?
- [ ] **Battery critical during active:** What if battery fails during motor active?
- [ ] **Button release timing:** What if button released during countdown?

**Edge Case Testing Checklist:**
- Shutdown during each state (not just during CHECK_MESSAGES)
- Mode change during back-EMF sampling
- Multiple rapid button presses
- Battery critical while motor is active
- Session timeout during sleep preparation

---

## Real-World Example: Emergency Shutdown Bug

### The Bug (Found in EMDR Pulser)

**Symptom:** Emergency shutdown never stops motor, no purple blink LED

**Root Cause Analysis:**

1. ✅ Button task sends shutdown message correctly
2. ✅ Motor task CHECK_MESSAGES receives message (line 1716)
3. ✅ Sets `state = MOTOR_STATE_SHUTDOWN` (line 1718)
4. ✅ Breaks from inner while loop (line 1719)
5. ❌ **Execution continues in CHECK_MESSAGES case!**
6. ❌ Line 1784 unconditionally sets `state = MOTOR_STATE_FORWARD_ACTIVE`
7. ❌ Shutdown state was overwritten, while loop never exits

**The Fix:**
```c
// At end of CHECK_MESSAGES case, before transitioning to FORWARD:
if (state == MOTOR_STATE_SHUTDOWN) {
    break;  // Don't overwrite shutdown state
}
state = MOTOR_STATE_FORWARD_ACTIVE;
```

**Lesson:** Break statements only exit the immediate loop/switch, not outer structures!

---

## Automated Analysis Template

Use this prompt with `Task` tool for automated analysis:

```
Perform systematic state machine analysis on [FILE_PATH]:

1. Identify state machine components:
   - State enum: [ENUM_NAME]
   - State variable: [VAR_NAME]
   - Loop condition: [WHILE_CONDITION]
   - Message queues: [QUEUE_NAMES]

2. Verify all state transitions:
   - Trace entry and exit for each state
   - Check for state variable overwrites
   - Verify cleanup in all paths

3. Check break/continue scope:
   - Look for breaks that only exit inner loops
   - Find state assignments followed by unconditional overwrites

4. Analyze message handling:
   - Verify all message types handled
   - Check for queue overflow conditions
   - Look for race conditions

5. Verify shutdown paths:
   - Emergency shutdown
   - Battery critical
   - Session timeout
   - User-initiated

6. Report findings:
   - List potential issues with line numbers
   - Categorize by severity (critical, warning, info)
   - Suggest fixes for each issue

Focus on finding bugs like:
- State overwrites after shutdown
- Missing cleanup calls
- Break scope errors
- Unhandled edge cases
```

---

## Prevention Strategies

### During Development:

1. **One state change per code path:** Avoid conditional state changes
2. **Guard state transitions:** Check current state before overwriting
3. **Explicit cleanup:** Call cleanup functions in ALL exit paths
4. **Comment break scope:** Note what loop/switch a break exits
5. **Unit test state transitions:** Test each transition independently

### Code Review Checklist:

- [ ] All states have documented entry/exit conditions
- [ ] Cleanup called in all code paths (normal, interrupt, error, shutdown)
- [ ] Break statements clearly scoped (add comments if nested)
- [ ] State variable only modified in one place per case
- [ ] Shutdown messages cannot be ignored or overwritten
- [ ] Edge cases documented and tested

### Tools:

- Static analysis: cppcheck, clang-tidy
- Compiler warnings: `-Wall -Wextra -Wswitch-enum`
- State diagram: Draw before implementing complex state machines
- Logging: Add ESP_LOGI at every state transition during development

---

## Summary

**Most Common State Machine Bugs:**

1. **State Overwrite** - Shutdown state overwritten before loop exit
2. **Missing Cleanup** - Resources not released in all exit paths
3. **Break Scope Error** - Break exits inner loop, not intended scope
4. **Unhandled Messages** - Critical messages ignored in some states
5. **Race Conditions** - Shared state modified without synchronization

**Golden Rules:**

✅ **Always check if shutting down before changing state**
✅ **Call cleanup in ALL exit paths (normal, interrupt, error, shutdown)**
✅ **Comment break statements in nested structures**
✅ **Test edge cases: rapid messages, timeouts during transitions**
✅ **Use compiler warnings to catch missing enum cases**

**Remember:** State machines are deterministic - if a bug exists, it will happen. Take the time to trace all paths!

---

**Last Updated:** November 8, 2025
**Based on:** EMDR Pulser BLE GATT test refactoring experience
