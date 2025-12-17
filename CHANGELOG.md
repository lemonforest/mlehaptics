# Changelog

All notable changes to the EMDR Bilateral Stimulation Device project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation

**Doxygen Quality Improvements for Arduino Developer Accessibility**:
- **Purpose**: Make ESP-IDF codebase approachable for developers transitioning from Arduino
- **Files Updated**:
  - `src/time_sync.h` - Added `@defgroup`, Arduino comparison table (`millis()` vs `esp_timer_get_time()`), protocol architecture, `@warning`/`@pre`/`@post` tags, example code
  - `src/motor_task.h` - Added `@defgroup`, Arduino pattern comparison (`loop()` vs FreeRTOS queues), state machine ASCII diagram, queue code examples
  - `src/ble_manager.h` - Added `@defgroup`, Arduino BLE library comparison, GATT service tree structure, callback threading `@warning` tags
  - `src/firmware_version.h` - Added `@defgroup`, "Why This Matters" section explaining dual-device versioning requirements
- **Consistent Pattern Applied**:
  - `@defgroup` with opening `@{` and closing `@}`
  - "Arduino Developers" sections with side-by-side comparison tables
  - `@warning` tags for safety-critical constraints
  - `@pre`/`@post` conditions on init functions
  - `@see` cross-references to ADR documentation
  - `@par Example Usage` with `@code` blocks
  - Updated version (0.6.122), date (2025-12-14), author credit (Sonnet 4, Sonnet 4.5, Opus 4.5)

**README.md Updates**:
- Added Phase 6 "Bilateral Motor Coordination (Complete)" milestone section
- Added Phase 7 "Scheduled Pattern Playback (Next - AD047)" preview section
- Added link to MLE Haptics PWA: https://lemonforest.github.io/mlehaptics-pwa/
- Added link to Bilateral Time Sync Protocol Technical Report

**ADR README.md Updates**:
- Phase 2 now shows "(Complete)" status
- Added Phase 6 section with key achievements (PTP-inspired sync, EMA filter, ±30 μs precision)
- Added Phase 7 section (Lightbar Mode, half-cycle boundaries)
- Updated Last Updated date to 2025-12-14

### Added

**AD040: Peer Firmware Version Exchange (v0.6.124)**:
- **Purpose**: Ensure both peer devices run identical firmware builds for reliable bilateral coordination
- **Core Feature**: One-time firmware version exchange after GATT discovery completes
  - Both SERVER and CLIENT send their version via SYNC_MSG_FIRMWARE_VERSION (0x10)
  - Compares major.minor.patch AND build timestamps for exact match
  - Soft enforcement: mismatch logs WARNING but connection allowed, motors run normally
- **LED Feedback**:
  - Green 3× blink on version match (reuses PAIRING_SUCCESS pattern)
  - Yellow/amber 3× blink on mismatch (new STATUS_PATTERN_VERSION_MISMATCH, RGB 255,180,0)
- **BLE Integration**: Peer firmware version exposed via characteristic (AD032: ...0213)
- **Bug Fixes During Implementation**:
  - Fixed infinite loop: Removed response send from handler (each side sends once)
  - Fixed timing: Moved send from MTU event to GATT discovery completion
- **Files Modified**:
  - `src/ble_manager.h` - Add message type, payload, and API declarations
  - `src/ble_manager.c` - Implement send/set/match functions, discovery trigger
  - `src/status_led.h` - Add STATUS_PATTERN_VERSION_MISMATCH enum
  - `src/status_led.c` - Implement yellow RGB(255,180,0) blink pattern
  - `src/time_sync_task.c` - Handle SYNC_MSG_FIRMWARE_VERSION message
  - `src/firmware_version.h` - Bump to v0.6.124

**AD047: Scheduled Pattern Playback Architecture (Phase 7 - Proposed)**:
- **Purpose**: Future "Lightbar Mode" enabling GPS-quality bilateral sync with complex visual patterns
- **Core Concept**: Scheduled playback with half-cycle boundary execution
  - All parameter changes take effect at clean half-cycle boundaries
  - Neither device is mid-motor-pulse at boundary → safe to apply new parameters
  - 250-1000ms latency (half-cycle) vs reactive architecture (immediate but glitchy)
- **Key Benefits**:
  - Eliminates Bug #81-#84 class of timing issues (mid-cycle changes impossible)
  - Enables lightbar-style patterns with scheduled frequency changes
  - RF disruption resilient (continues executing from local buffer)
- **Pattern Buffer Design**: Pre-computed segments with boundary_time, frequency, duty, intensity, LED color
- **Related**: Builds on AD041, AD044, AD045, AD046 timing infrastructure
- **Files Added**: `docs/adr/0047-scheduled-pattern-playback.md`
- **ADR Index Updated**: `docs/adr/README.md` (47 total decisions, 3 proposed)

**AD043 Enhancement: Paired Timestamps for Bias-Corrected Offset (v0.6.72)**:
- **Problem Solved**: One-way delay bias in beacon-based time sync
  - Original AD043 EMA filter smooths variance but cannot correct systematic bias
  - Every beacon has ~20-40ms one-way delay → EMA converges to wrong offset
  - Explains observed ~40ms phase offset despite excellent filter stability
- **Solution**: NTP-style paired timestamps in SYNC_FB (activation report)
  - CLIENT includes beacon timestamps (T1, T2) and report send time (T3)
  - SERVER records receive time (T4) and calculates: `offset = ((T2-T1) + (T3-T4)) / 2`
  - NTP formula cancels symmetric delays, giving bias-corrected offset
- **Why This Works Now**: Pattern-broadcast architecture (AD045) changed the problem
  - OLD: RTT spikes → stale timestamp → bad motor correction → jitter
  - NEW: RTT spikes → EMA filter rejects outlier → motor timing unaffected
  - Paired timestamps feed EMA filter, not motor corrections directly
- **Expected Improvement**: ~40ms offset → <5ms target
- **Files Modified**:
  - `src/ble_manager.h` - Extended `activation_report_t` with T1/T2/T3 timestamps
  - `src/time_sync.h` - Added `time_sync_get_last_beacon_timestamps()` and `time_sync_update_from_paired_timestamps()` APIs
  - `src/time_sync.c` - Store T2 in process_beacon(), implement paired offset calculation
  - `src/motor_task.c` - Populate paired timestamps when sending SYNC_FB
  - `src/time_sync_task.c` - Call paired timestamp update on SYNC_FB receive
  - `docs/adr/0043-filtered-time-synchronization.md` - Updated with v0.6.72 enhancement section

**AD045: Pattern-Broadcast Architecture (Emergency Vehicle Adaptation)**:
- **Beacon Enhancement**: Added `duty_percent` and `mode_id` fields to time_sync beacon (25 bytes, was 23)
  - Both devices now have complete pattern info: epoch, period, duty, mode
  - CLIENT can validate mode matches SERVER (warns if mismatch detected)
- **Feniex-style Boundary Resync**: CLIENT detects epoch changes and resets cycle counter
  - When SERVER changes mode, new epoch propagates via beacon
  - CLIENT resets `client_inactive_cycle_count` to 0 on epoch change
  - Eliminates cycle counter divergence in SYNC_FB diagnostics
- **Enhanced SYNC_FB Diagnostics**:
  - CLIENT logs: `SYNC_FB sent cycle=N err=Xms offset=Yms` (shows offset being applied)
  - SERVER logs: `[SYNC_FB] cycle=N/M err=Xms elapsed=Yms` (shows elapsed time since epoch)
  - Warns on cycle divergence > 5 (indicates stale epoch or time domain issue)
- **Files Modified**:
  - `src/time_sync.h` - Beacon struct expanded with duty_percent, mode_id
  - `src/time_sync.c` - Beacon generation includes pattern fields, mode validation
  - `src/motor_task.c` - Epoch change detection, cycle counter reset
  - `src/motor_task.h` - Added `motor_get_duty_percent()` API
  - `src/time_sync_task.c` - Enhanced SYNC_FB handler with elapsed time

### Infrastructure

**Code Cleanup: Emergency Vehicle Light Sync Architecture Alignment**:
- **Motivation**: Align with proven "pattern-broadcast + independent execution" architecture from emergency vehicle lighting systems (Whelen, Federal Signal, SoundOff, Feniex)
- **Research**: [docs/Emergency_Vehicle_Light_Sync_Proven_Architectures_for_ESP32_Adaptation.md](docs/Emergency_Vehicle_Light_Sync_Proven_Architectures_for_ESP32_Adaptation.md)
- **Phase 1**: Removed Bug #26 disabled coast correction block (~68 lines)
  - Code was inside `#if 0` block, permanently disabled
  - Attempted drift corrections during COAST state that made overlap WORSE
- **Phase 2**: Removed unused hardware timer infrastructure (~91 lines)
  - `MSG_TIMER_MOTOR_TRANSITION` message type removed from motor_task.h
  - Timer declaration, callback, creation, and arming code removed
  - Timer was never controlling transitions - polling-based `delay_until_target_ms()` did actual work
  - Phase 2 time sync already provides ±30 μs accuracy (200× better than ±10ms spec)
- **Phase 3**: Simplified CLIENT motor cycle monitoring (~26 lines)
  - Removed verbose SERVER cycle logging (reduced log spam)
  - Simplified quality monitoring (removed unused edge case detection)
  - Preserved essential calculation, Bug #54a activation report, and direction alternation
- **Phase 4-5**: Skipped (mode change protocol and startup handshaking)
  - These would require behavioral changes, not just dead code removal
  - Deferred for future refactoring with hardware testing
- **Total Removed**: 195 lines (-185 net deletions)
- **Flash Reduction**: ~1,152 bytes saved (896,409 → 895,257)
- **Files Modified**:
  - `src/motor_task.c` - 194 lines removed
  - `src/motor_task.h` - 1 line removed (MSG_TIMER_MOTOR_TRANSITION enum)

### Fixed

**Bug #95: Mode 4 Frequency Changes Need Coordinated Sync (v0.6.117)**:
- **Symptom**: When PWA user drags frequency slider in Mode 4, devices desync
  - Each slider position change sends BLE write immediately
  - Without coordination, only frequency VALUE is synced (via Phase 3a settings sync)
  - Motor patterns continue at old timing until manual mode cycle
- **Root Cause**: Mode 4 frequency changes weren't triggering AD045 coordinated mode change
  - Bug #84 fixed CLIENT desync AFTER mode change
  - But frequency changes weren't triggering mode change protocol at all
  - Settings sync updates VALUE; mode change updates TIMING
- **Solution**: Debounced frequency change triggers coordinated mode change (AD047 stepping stone)
  - 300ms debounce window handles rapid slider drag gracefully
  - After debounce settles, SERVER triggers MSG_MODE_CHANGE to motor_task
  - Motor task executes AD045 two-phase commit to resync both devices
- **Implementation**:
  - Added `freq_change_pending` flag and `freq_change_timestamp_ms` in ble_manager.c
  - Added `ble_check_and_clear_freq_change_pending()` API in ble_manager.h
  - time_sync_task checks debounce periodically (SERVER only)
  - On debounce expiry, sends MSG_MODE_CHANGE with MODE_CUSTOM to motor_task
- **Note**: Duty cycle changes don't need this - duty only affects motor ON time within fixed cycle
- **Files Modified**: `src/ble_manager.c`, `src/ble_manager.h`, `src/time_sync_task.c`

**Bug #97: CLIENT LED Shows Old Mode Color at Mode Change Boundary (v0.6.119)**:
- **Symptom**: CLIENT LED activates too soon at mode change, showing OLD mode color for last pulse
  - LED turns on when mode change is REQUESTED (arming phase)
  - But mode change doesn't EXECUTE until ~2 seconds later (synchronized epoch)
  - CLIENT continues OLD pattern with LED active → shows OLD mode color
- **Root Cause**: `led_indication_active = true` set at mode change REQUEST (line 1160)
  - Should only activate when mode change EXECUTES (line 1328)
  - Two-phase commit means 2s delay between REQUEST and EXECUTE
  - During delay, CLIENT still running OLD mode but LED is on
- **Fix**: Only set `led_indication_active` at REQUEST time when NOT synchronized
  - Added `if (!TIME_SYNC_IS_ACTIVE())` guard around immediate LED activation
  - When synchronized, LED indication activates at EXECUTE time (existing line 1328)
  - Standalone mode still gets immediate LED feedback
- **Files Modified**: `src/motor_task.c` (lines 1161-1170)

**Bug #98: CLIENT First ACTIVE Cycle Truncated After Mode Change (v0.6.120)**:
- **Symptom**: After rapid mode changes, CLIENT's first ACTIVE cycle is only ~10ms instead of full duration
  - Motor starts then immediately coasts
  - Observable as very brief pulse that doesn't match SERVER's timing
- **Root Cause**: Stale `client_epoch_cycle_start_ms` from interrupted INACTIVE state
  - CLIENT is in INACTIVE state, calculates target time for next cycle
  - Rapid mode changes get armed and CLIENT stays in wait loop
  - Mode change finally executes, sets `client_skip_inactive_wait = true`
  - CHECK_MESSAGES goes directly to ACTIVE (skips INACTIVE)
  - ACTIVE finds stale `client_epoch_cycle_start_ms > 0` from before mode change armed
  - Uses stale value (which is now in the past) for `motor_off_target_ms`
  - `delay_until_target_ms()` returns immediately → motor coasts after ~10ms
- **Fix**: Clear epoch cycle start values when CLIENT executes mode change
  - `client_epoch_cycle_start_ms = 0` clears stale INACTIVE target
  - `notify_epoch_cycle_start_ms = 0` clears frequency change path too
  - ACTIVE falls through to fresh `esp_timer_get_time()` for first cycle
- **Files Modified**: `src/motor_task.c` (mode change execution, lines 1317-1324)

**Bug #99: Misleading Beacon Warning for CLIENT During Mode Change (v0.6.120)**:
- **Symptom**: CLIENT logs `W: Beacon trigger only valid for SERVER role` on every mode change
  - Creates unnecessary alarm in logs
  - Makes it look like something is wrong when it's expected behavior
- **Root Cause**: `time_sync_trigger_forced_beacons()` called unconditionally on mode change
  - `SYNC_MSG_MODE_CHANGE` handler calls this function for both SERVER and CLIENT
  - Comment at line 558 says "This is expected on CLIENT (not an error)"
  - But function itself uses `ESP_LOGW` (warning level) instead of `ESP_LOGD` (debug)
- **Fix**: Change log level from WARNING to DEBUG
  - CLIENT calling this is expected and harmless (function returns early)
  - DEBUG level won't clutter logs at default verbosity
- **Files Modified**: `src/time_sync.c` (line 1411-1413)

**Bug #96: Short Motor Activations After Mode Change (v0.6.118)**:
- **Symptom**: After mode change, cycles 2-4 have very short motor activations (~0-10ms instead of 63-84ms)
  - SERVER's second activation is nearly instant (motor coasts immediately)
  - Observable as brief motor pulses that don't provide proper tactile feedback
- **Root Cause**: Motor epoch mismatch between proposed and actual execution time
  - Mode change sets `motor_epoch` to PROPOSED time (500ms before execution)
  - Bug #94b correctly uses fresh `esp_timer_get_time()` for first cycle
  - INACTIVE calculates next cycle target: `motor_epoch + (cycle_count * cycle_period)`
  - Since motor_epoch is ~500ms in the past, calculated target is already past
  - `delay_until_target_ms()` returns immediately → motor coasts instantly
- **Example Trace**:
  - `motor_epoch = 25941170` (proposed from 500ms ago)
  - First ACTIVE actually started at ~26388ms (fresh time)
  - INACTIVE calculates: `25941170 + 667000 = 26608170` → target = 26608ms
  - Second ACTIVE enters at 27058ms → target is 450ms in the PAST!
- **Fix**: Update motor_epoch when SERVER's first cycle actually starts
  - In ACTIVE state, when `server_cycle_count == 0`, update motor_epoch to actual `cycle_start_ms`
  - INACTIVE calculations now anchor to correct starting point
  - Subsequent cycles have valid future targets
- **Files Modified**: `src/motor_task.c` (ACTIVE state, lines 1527-1539)

**Bug #84: Mode 4 Frequency Changes Cause CLIENT Desync (v0.6.104)**:
- **Symptom**: When changing frequency within Mode 4 (via PWA), CLIENT gets severely out of sync
  - Desync persists until mode switch away and back to Mode 4
  - Bug #83 fix only covered mode changes, not intra-mode frequency changes
- **Root Cause**: MOTOR_STARTED message handler didn't set `client_skip_inactive_wait` flag
  - Mode 4 frequency changes send MOTOR_STARTED (not full mode change protocol)
  - CLIENT receives MOTOR_STARTED, updates epoch from beacon
  - CLIENT then enters INACTIVE state and recalculates antiphase
  - Recalculation misses first target, advances to NEXT cycle (1 cycle behind)
- **Fix**: `motor_task_notify_motor_started()` now sets BOTH flags
  - `motor_started_received = true` (existing - for coordinated start)
  - `client_skip_inactive_wait = true` (new - for frequency change scenario)
  - Same skip pattern as Bug #81/#83 - antiphase already correct, don't recalculate
- **Files Modified**: `src/motor_task.c` (motor_task_notify_motor_started function)

**Bug #83: CLIENT Mode Change Adds Extra Cycle Delay (v0.6.103)**:
- **Symptom**: After mode change, SERVER runs 1 cycle ahead of CLIENT
  - CLIENT LED activates late with motor already active
  - Regression from v0.6.99 Bug #82 fix
- **Root Cause**: CLIENT INACTIVE state recalculates antiphase after mode change execution
  - CLIENT executes mode change at correct time (two-phase commit)
  - CLIENT then transitions to INACTIVE state per normal flow
  - INACTIVE calls `time_sync_get_motor_epoch()` and recalculates antiphase target
  - By recalculation time, first antiphase target has passed
  - `advance_past_target_cycles()` jumps to NEXT cycle → CLIENT 1 cycle behind
- **Why Bug #81 didn't catch this**: Bug #81 was for coordinated start (epoch from beacon)
  - Mode changes use two-phase commit (epoch from proposal, not beacon)
  - CLIENT sets motor_epoch from proposal correctly (Bug #82 fix)
  - But `client_skip_inactive_wait` flag not set during mode change execution
- **Fix**: Set `client_skip_inactive_wait = true` when CLIENT executes mode change
  - CLIENT's armed_epoch_us is already half-cycle after server_epoch (antiphase)
  - When CLIENT executes at this epoch, it's at perfect antiphase position
  - Skip INACTIVE and go directly to ACTIVE (same pattern as Bug #81)
- **Files Modified**: `src/motor_task.c` (mode change execution for CLIENT)

**Bug #74: Mode Change Latency Coupled to Current Frequency (v0.6.90)**:
- **Symptom**: Mode changes at 0.5Hz took ~4 seconds, at 1.0Hz took ~2 seconds
  - User perceived mode changes as "sluggish" at lower frequencies
- **Root Cause**: Mode change scheduled "2 cycles from now" based on CURRENT frequency
  - At 0.5Hz (2000ms period): 2 cycles = 4000ms wait
  - At 1.0Hz (1000ms period): 2 cycles = 2000ms wait
  - At 2.0Hz (500ms period): 2 cycles = 1000ms wait
- **Fix**: Use fixed 500ms time margin instead of cycle-based margin
  - BLE delivery + processing is ~100ms, so 500ms is plenty
  - Find next cycle boundary after `now + 500ms`
  - Mode change latency now independent of current frequency
- **Expected Latency**: 500ms-1000ms at any frequency (was 1-4 seconds)
- **Files Modified**: `src/motor_task.c` (lines 1138-1161)

**Bug #73: CLIENT Epoch Race Condition on Mode Change (v0.6.89)**:
- **Symptom**: After mode change, CLIENT's first activation uses OLD epoch, causing phase inversion
  - CLIENT activates almost synchronized with SERVER instead of half-cycle offset
  - ~1.4 seconds later, "New epoch detected" triggers recalculation
  - After recalculation, CLIENT phase is inverted (activating half-cycle BEFORE SERVER)
- **Root Cause**: CLIENT knew epoch from proposal but waited for beacon
  - Mode change proposal sends epoch=28871170 to CLIENT
  - CLIENT executes mode change, enters INACTIVE state
  - CLIENT calls `time_sync_get_motor_epoch()` which reads from beacon data
  - Forced beacon sent 28ms after mode change, but CLIENT already calculated
  - First INACTIVE uses OLD epoch → wrong timing
- **Fix**: CLIENT now sets motor_epoch directly from proposal (like SERVER does)
  - Both devices call `time_sync_set_motor_epoch(armed_epoch_us, armed_cycle_ms)`
  - CLIENT no longer waits for beacon - it already knows the epoch
  - SERVER still sends forced beacons for ongoing sync validation
- **Files Modified**: `src/motor_task.c` (lines 1250-1265)

**Bug #72: Double Half-Cycle Offset on Mode Change (v0.6.88)**:
- **Symptom**: ~3 second gap where only SERVER activates after mode change at lower frequencies
- **Root Cause**: Double half-cycle offset calculation
  - SERVER (line 1158): `client_epoch = server_epoch + half_cycle` → adds half-cycle
  - CLIENT INACTIVE (line 1706): `target = server_cycle_start + half_cycle` → adds ANOTHER half-cycle
  - Result: CLIENT activates 1.5 cycles after SERVER instead of 0.5 cycles
- **Example at 0.5Hz (2000ms period)**:
  - Expected: CLIENT activates 1000ms after SERVER (antiphase)
  - Actual: CLIENT activates 3000ms after SERVER (1 full cycle + half)
- **Fix**: SERVER now sends `client_epoch = server_epoch` (same epoch)
  - CLIENT adds the ONE half-cycle offset in INACTIVE state as designed
  - Mode changes now complete within a single cycle
- **Files Modified**: `src/motor_task.c` (line 1160)

**Bug #71: First Cycle After Mode Change Has Shortened Motor ON Time (v0.6.86→v0.6.87)**:
- **Symptom**: First motor cycle after mode change only ran ~160ms instead of 250ms
  - Second cycle onwards was correct (250ms for 0.5Hz@25%)
  - Caused noticeable "short pulse" on first activation after mode change
- **Root Cause**: Epoch calculated for mode change is in the PAST by execution time
  - Mode change arms with epoch = current_epoch + (N * period) (Bug #69)
  - By the time ACTIVE state runs (~500ms later), epoch is 400-500ms in the past
  - `cycle_start_ms = epoch + 0` is in the past
  - `motor_off_target = cycle_start + 250ms` is ALSO in the past
  - `delay_until_target_ms()` returns immediately when target is past
  - Motor ON time shortened to whatever processing time occurred (~160ms)
- **Fix v0.6.86 (WRONG - caused motor to run 2230ms!)**: Skip past cycles to find future boundary
  - While loop advanced `server_cycle_count` until `cycle_start_us >= now_us`
  - **BUG**: Motor turns ON now, but waits until `cycle_start + 250ms` (future) to turn OFF
  - Result: Motor ran for ~2230ms instead of 250ms (even worse!)
- **Fix v0.6.87 (CORRECT)**: Check if motor_on phase already passed BEFORE turning on motor
  - Calculate `motor_off_target_ms` and `active_end_target_ms` before motor_on
  - If past `active_end`: skip entire ACTIVE phase, go to INACTIVE
  - If past `motor_off` but before `active_end`: skip motor_on, still wait for coast period
  - If neither: normal operation (turn on motor, wait until motor_off)
  - Result: Clean phase skip without extending motor duration
- **Files Modified**:
  - `src/motor_task.c:1518-1549` - Bug #71 pre-check before motor_on
  - `src/motor_task.c:1573` - Remove duplicate variable declaration

**Bug #70: Mode 4 Log Spam During Mode Change Armed Wait (v0.6.85)**:
- **Symptom**: ~40 lines of "Mode 4 (Custom): 0.50Hz..." printed every 50ms during mode change wait
  - Log spam lasted 2-4 seconds (entire armed wait period)
  - Cluttered serial output, made debugging difficult
- **Root Cause**: Verbose logging not suppressed during armed wait
  - `calculate_mode_timing()` called with `sample_backemf=true` every poll iteration
  - Mode change triggers `led_indication_active=true` → `mode_change_logging=true`
  - Armed wait loop polls every 50ms, calling calculate_mode_timing each time
- **Fix**: Add `&& !mode_change_armed` to verbose logging condition
  - `sample_backemf = (mode_change_logging || periodic_bemf) && !mode_change_armed`
  - Motors paused during armed wait, no cycles executing → no logging needed
- **Files Modified**:
  - `src/motor_task.c:1368-1372` - Skip verbose logging during armed wait

**Bug #69: Mode Change Transition - Epoch-Relative Scheduling (v0.6.84)**:
- **Symptom**: Mode changes caused one device to activate early/late relative to the other
  - Both devices observed timing mismatch during mode transitions
  - Early activation visible to user despite sync working during steady-state
- **Root Cause**: Mode change epoch calculated as `now + 2s` (non-deterministic)
  - "now" varies between devices due to BLE transmission delay
  - CLIENT couldn't independently verify SERVER's calculation
- **Fix**: Epoch-relative mode change transitions (deterministic)
  - SERVER calculates: `transition_epoch = current_epoch + (N * current_period)`
  - N is typically `current_cycle + 2` (margin for BLE delivery)
  - CLIENT can verify: transition must align with known motor epoch
  - Both devices use same epoch + period → independently verifiable math
- **Architecture**: Extension of Bug #68 epoch-anchored principle to mode changes
- **Files Modified**:
  - `src/motor_task.c:1128-1154` - SERVER epoch-relative transition calculation
  - `src/time_sync_task.c:831-850` - CLIENT epoch-relative verification

**Bug #68: SERVER ADC-Induced Timing Drift - Epoch-Based Cycle Scheduling (v0.6.83)**:
- **Symptom**: SERVER motor cycles drift 10-20ms when BEMF/ADC sampling is active
  - Without BEMF: Perfect 2000ms cycles
  - With BEMF: Cycles drift by +10ms, +20ms, etc. (cumulative)
  - Log evidence: `4153923 → 4155923 → 4157933 → 4159953` (2000, 2010, 2020ms intervals)
- **Root Cause**: SERVER used `esp_timer_get_time()` ("now") for cycle_start_ms each cycle
  - Any processing delay in CHECK_MESSAGES (ADC, logging, queue) accumulated
  - CLIENT already used epoch-based timing (correct), but SERVER did not
- **Fix**: SERVER now calculates cycle_start_ms from motor_epoch + cycle_count
  - `cycle_start_us = motor_epoch + (server_cycle_count * cycle_period * 1000)`
  - Cycles start at fixed intervals regardless of CHECK_MESSAGES processing time
  - Added epoch change detection to reset cycle counter on mode changes
  - Fallback to "now" for standalone mode (no epoch)
- **Architecture**: Both devices now use same epoch-based approach (Emergency Vehicle pattern)
- **Files Modified**:
  - `src/motor_task.c:1437-1479` - Epoch-based cycle start calculation for SERVER

**Bug #67: CLIENT Starts Motor Cycle After Button Press Before Proposal (v0.6.82)**:
- **Symptom**: CLIENT starts a new ACTIVE motor cycle AFTER button press but BEFORE proposal arrives
  - Log evidence: "Mode change armed" at 09:06:49.946, then "Cycle starts ACTIVE" at 09:06:49.988
  - CLIENT runs old mode PWM (90%) during ~100ms gap before proposal arrives
  - Mode change execution latency: 10-43ms late due to 50ms poll interval
- **Root Cause**: Two issues:
  1. CLIENT logged "Mode change armed" but did NOT actually set `mode_change_armed = true`
  2. Real arming only happened when proposal arrived from SERVER (~100ms later)
  3. During this gap, CLIENT continued running motor cycles
  4. After proposal, 50ms poll interval caused additional 0-50ms execution latency
- **Fix**: CLIENT now arms immediately on button press with two changes:
  1. Set `mode_change_armed = true` with placeholder epoch (`UINT64_MAX`) on button press
  2. Motors pause immediately; real epoch is set when proposal arrives
  3. Improved pause loop: calculates precise wait time if <50ms remaining
- **Files Modified**:
  - `src/motor_task.c:1164-1175` - CLIENT arms immediately with placeholder epoch
  - `src/motor_task.c:1374-1394` - Precise wait time calculation in pause loop

**Bug #66: CLIENT Startup Offset - Extra Cycle Before First Activation (v0.6.81)**:
- **Symptom**: CLIENT first activation ~2 seconds after SERVER (should be ~1 second for antiphase)
  - Log evidence: SERVER activates at 08:29:49.334, CLIENT at 08:29:52.323 (~3s later, should be ~1s)
- **Root Cause**: After coordinated start, CLIENT transitions to INACTIVE state instead of ACTIVE
  - Coordinated start waits until antiphase moment (half-cycle after SERVER's epoch)
  - But then CLIENT goes CHECK_MESSAGES → INACTIVE → calculates target
  - By the time INACTIVE runs, antiphase moment has passed (~60ms transit time)
  - INACTIVE adds a full cycle: `client_target_active_us += cycle_us` (line 1580)
  - CLIENT ends up waiting an extra full cycle before first activation
- **Fix**: CLIENT goes directly to ACTIVE after coordinated start (no INACTIVE wait)
  - Added `client_first_cycle_active` flag set after coordinated start
  - CHECK_MESSAGES checks flag: if true, go to ACTIVE instead of INACTIVE
  - Flag cleared after first use (subsequent cycles use normal INACTIVE logic)
- **Files Modified**:
  - `src/motor_task.c:156-159` - Added `client_first_cycle_active` flag
  - `src/motor_task.c:922-924` - Set flag when CLIENT reaches coordinated start
  - `src/motor_task.c:1377-1388` - Use flag to bypass INACTIVE on first cycle

**Bug #65: CLIENT Continues Cycles After Mode Change Armed (v0.6.80)**:
- **Symptom**: 830 unpaired activations over 90-minute session (only 81 properly paired)
  - CLIENT continued 2.0Hz cycles AFTER mode change was armed to 0.5Hz
  - User report: "mode change arming does not always command both devices to stop"
- **Root Cause**: `delay_until_target_ms()` and `delay_until_sync_target_us()` only checked `button_to_motor_queue` for MSG_MODE_CHANGE
  - Did NOT check `mode_change_armed` flag set by `time_sync_task`
  - CLIENT received mode proposal, armed the change, but continued delay loop
- **Fix**: Added `mode_change_armed` check to both delay functions
  - Returns early if mode change is armed, breaking out of wait loop
  - Motor task returns to CHECK_MESSAGES where armed mode change is executed
- **Files Modified**:
  - `src/motor_task.c:290-294` - Added mode_change_armed check to delay_until_target_ms()
  - `src/motor_task.c:355-359` - Added mode_change_armed check to delay_until_sync_target_us()

**Bug #48: Battery-Based Role Assignment Race Condition**:
- **Symptom**: Both devices fell back to discovery-based role assignment (power-on order) instead of using battery level
- **Root Cause**: BLE stack's `ble_on_sync()` callback fired before battery was cached, causing both devices to advertise 0% battery
- **Fix**: Battery now read BEFORE `ble_manager_init()` and passed as parameter
  - Added `g_initial_battery_pct` static variable to store battery before BLE init
  - `ble_on_sync()` initializes `bilateral_data.battery_level` with pre-cached value before first advertising update
  - Ensures battery available for role assignment when peer devices discover each other
- **Impact**: Higher-battery device now correctly becomes SERVER, balancing load and battery life
- **Files Modified**:
  - `src/ble_manager.h:141` - Updated signature: `esp_err_t ble_manager_init(uint8_t initial_battery_pct)`
  - `src/ble_manager.c:258-260` - Static variable declaration
  - `src/ble_manager.c:3523-3530` - Store initial battery in ble_manager_init()
  - `src/ble_manager.c:3292-3299` - Initialize bilateral_data.battery_level in ble_on_sync()
  - `src/main.c:232-258` - Read battery before BLE init, pass to ble_manager_init()

**Bug #49: CLIENT Overwrites Motor Epoch (COMPLETE FIX - Startup + Mode Change)**:
- **Symptom**:
  - 275 motor overlaps (87.1 seconds) over 90-minute session - both devices running ACTIVE simultaneously instead of alternating
  - Startup antiphase error: CLIENT 1009ms offset from SERVER (should be exactly half-cycle = 1000ms at 1 Hz)
  - User reports: "start up motor behavior is not correct", "systematic overlap in client/server activation periods"
- **Root Cause**: CLIENT overwrote SERVER's authoritative motor epoch in TWO locations:
  1. **Mode change handler** (v0.6.59 fix): CLIENT calculated epoch by subtracting half-cycle from its own start time
  2. **Coordinated start handler** (v0.6.60 fix): CLIENT set epoch to its own actual start time during startup
  - In both cases: CLIENT replaced SERVER's precise epoch with CLIENT's local time
  - Result: Antiphase calculation used WRONG reference point → progressive drift → overlap
- **Analysis Evidence**:
  - v0.6.58 logs: 275 overlaps, avg 316.9ms, progressive drift 25ms → 209ms within 10 minutes
  - v0.6.59 logs: Startup antiphase error persists (CLIENT epoch 12170137 μs vs SERVER 11161172 μs = 1009ms offset)
  - CLIENT log showed: "CLIENT: Motor epoch set to actual start time: 12170137 μs" (should NOT set, only read!)
- **Fix** (v0.6.59 + v0.6.60):
  - **v0.6.59**: Removed CLIENT epoch update in mode change handler (motor_task.c:1201-1210)
  - **v0.6.60**: Removed CLIENT epoch update in coordinated start handler (motor_task.c:900-909)
  - Only SERVER calls `time_sync_set_motor_epoch()` (authoritative source of truth per AD045)
  - CLIENT only calls `time_sync_get_motor_epoch()` to READ epoch (never writes)
  - Maintains single source of truth for antiphase calculation
- **Impact**:
  - Eliminates motor overlap during session
  - Fixes startup antiphase error (CLIENT now uses SERVER's exact epoch)
  - Restores proper antiphase alternation (one device ACTIVE while other INACTIVE)
- **Files Modified**:
  - `src/motor_task.c:900-909` - Added SERVER role check before epoch update (coordinated start)
  - `src/motor_task.c:1201-1210` - Added SERVER role check before epoch update (mode change)

**Bug #50: Mode 4 Duty Cycle Display Confusion**:
- **Symptom**: Mode 4 displayed "79% duty" but actual motor duty cycle was 39.5% of total cycle, causing AI model confusion
- **Root Cause**: Cross-domain terminology ambiguity - "duty cycle" means different things in different contexts:
  - Traditional electronics: % of total period with signal HIGH
  - Bilateral alternation: % of ACTIVE period with motor ON (must maintain 50/50 ACTIVE/INACTIVE split)
- **Fix**: Enhanced with "Motor Active Duty Percent" terminology throughout
  - Logging: "39% total duty (79% motor active duty)" clarifies both measurements
  - Comments: Explicitly state "Motor Active Duty Percent: 10-100% of ACTIVE period (not total cycle)"
  - Documentation: Added comprehensive section explaining semantic difference for AI models
  - Example: 100% Motor Active Duty = 50% Total Duty (motor on entire ACTIVE period)
- **Impact**:
  - Users understand actual haptic feedback intensity (39.5% total vs 79% active)
  - AI models can correctly interpret "duty" in bilateral context (not traditional duty cycle)
  - Prevents future confusion about cross-domain terminology
- **Files Modified**:
  - `src/motor_task.c:315-338` - Enhanced function documentation with Motor Active Duty Percent explanation
  - `src/motor_task.c:345` - Comment: "Motor Active Duty Percent: 10-100% of ACTIVE period (not total cycle)"
  - `src/motor_task.c:354` - Comment: "Apply Motor Active Duty Percent within ACTIVE period only"
  - `src/motor_task.c:355-366` - Logging: "motor active duty" terminology, dual display

**Bug #51: Motors Pause During Mode Change Arming (Synchronized Transitions)**:
- **Symptom**:
  - Mode changes left one device running the NEW pattern while the other ran the OLD pattern for ~3.5 seconds
  - User report: "mode change behavior is still leaving one device running the previous pattern"
  - CLIENT changed pattern immediately after button press, SERVER continued OLD pattern until synchronized epoch
  - Log evidence: "CLIENT: Antiphase lock LOST (will re-establish via beacons)" during every mode change
- **Root Cause**: CLIENT executed mode change immediately after arming instead of waiting for synchronized epoch
  - Line 1166 in motor_task.c changed `current_mode = new_mode` for CLIENT after button press
  - Motor state machine immediately started running NEW pattern parameters (frequency, duty cycle)
  - SERVER continued running OLD pattern until its synchronized epoch was reached
  - Result: ~3.5 seconds of pattern chaos with mismatched frequencies and loss of antiphase lock
- **Analysis Evidence**:
  - v0.6.60 logs (first mode change 0.5Hz → 1.0Hz):
    - 17:56:02.365: CLIENT mode change requested
    - 17:56:02.366: CLIENT executes immediately: "Mode: 1.0Hz@25% (standalone)"
    - 17:56:03.364: CLIENT starts NEW pattern: "Motor reverse: 65%" (1.0Hz timing)
    - 17:56:03.864: CLIENT detects problem: "Antiphase lock LOST"
    - Meanwhile SERVER still running 0.5Hz pattern until 17:56:04.025
  - User confirmed observation: "I think that we need to stop active motor patterns during the arming behavior"
- **Fix** (v0.6.61):
  - **Part 1**: CLIENT doesn't execute mode change immediately (motor_task.c:1165-1178)
    - If time sync active (CLIENT role): Don't change `current_mode`, log "Mode change armed"
    - Wait for synchronized execution at agreed epoch
    - Only standalone devices change mode immediately (no peer coordination needed)
  - **Part 2**: Add PAUSED state during arming period (motor_task.c:1339-1346)
    - Check `mode_change_armed` flag in CHECK_MESSAGES state
    - If armed: Motors pause, log "Motors paused (mode change armed)", continue checking
    - Both devices enter PAUSED state, resume together at synchronized epoch
- **Impact**:
  - Eliminates pattern chaos during mode changes (both devices now change together)
  - Prevents antiphase lock loss (motors pause instead of running mismatched patterns)
  - Smooth synchronized transitions with coordinated pause → resume behavior
  - Professional UX: Users see both devices pause briefly, then resume in sync with new pattern
- **Files Modified**:
  - `src/motor_task.c:1165-1178` - CLIENT doesn't execute mode change immediately, waits for synchronized epoch
  - `src/motor_task.c:1339-1346` - Added PAUSED state check to prevent motor activation during arming
  - `src/firmware_version.h:33` - Version bump to v0.6.61
  - `platformio.ini:101` - Version bump to v0.6.61

**Bug #52: [INCORRECT FIX - Superseded by Bug #53]**:
- v0.6.62 moved timing recalculation to BEFORE message handling
- This was wrong - timing calculated from OLD current_mode before mode change executed
- See Bug #53 for correct fix

**Bug #53: Timing Recalculation Must Happen AFTER Mode Change Execution**:
- **Symptom** (v0.6.61 analysis):
  - SERVER stuck at old frequency after mode changes while CLIENT switches correctly
  - Mode Change 1.0Hz → 1.5Hz: SERVER measured at 1.000 Hz (33% error), CLIENT perfect at 1.500 Hz
  - Mode Change 1.5Hz → 2.0Hz: SERVER measured at 1.499 Hz (25% error), CLIENT perfect at 2.001 Hz
  - Pattern: CLIENT immediately switches, SERVER continues running old frequency
- **Symptom** (v0.6.62 - Bug #52 incorrect fix made it worse):
  - BOTH devices stuck at approximately half target frequency
  - Mode 0.5→1.0 Hz: Both measured ~0.5 Hz (50% error)
  - Mode 1.0→1.5 Hz: Both measured ~0.8-0.9 Hz (42-47% error)
  - Mode 1.5→2.0 Hz: SERVER 0.994 Hz (50% error), CLIENT 0.821 Hz (59% error)
- **Root Cause**:
  - Original (v0.6.61): Timing calculated AFTER pause check's `continue` statement
  - Bug #52 fix (v0.6.62): Moved timing to BEFORE message handling - WRONG!
  - Timing was now calculated from OLD current_mode before mode change updated it
  - Correct location: AFTER mode change execution, BEFORE pause check
- **Analysis Evidence**:
  - analyze_mode_change_convergence.py tool created for systematic analysis
  - v0.6.61 logs: SERVER stuck at previous frequency, CLIENT correct
  - v0.6.62 logs: Both devices running at ~50% of target frequency
- **Fix** (v0.6.63):
  - Moved timing recalculation to AFTER mode change execution (line 1305-1326)
  - Correct sequence: 1) Process messages → 2) Execute mode change → 3) Calculate timing
  - Timing now reflects NEW current_mode after mode change updates it
  - Then pause check runs (but mode already changed, so won't pause)
- **Impact**:
  - Both devices calculate timing from correct (new) mode after mode change
  - Eliminates frequency mismatch (SERVER no longer stuck at old frequency)
  - Eliminates halved frequency bug introduced by Bug #52
- **Files Modified**:
  - `src/motor_task.c:1305-1326` - Timing recalculation after mode change execution
  - `src/firmware_version.h:33` - Version bump to v0.6.63
  - `platformio.ini:101` - Version bump to v0.6.63

**Bug #57: Forced Beacons Not Sent Promptly After Mode Change (v0.6.68)**:
- **Symptom**:
  - CLIENT continued running at OLD frequency for 10-60 seconds after mode change
  - Mode Change 0.5Hz → 1.0Hz at 09:26:54: CLIENT continued at 2000ms period (should be 1000ms)
  - SYNC_FB showed server_err=-329ms confirming desync
  - Log evidence: "SERVER: Forced beacons triggered for mode change sync" at 09:26:56.307
  - But NO "Forced beacon 1/5 sent" until 09:27:47 (51 seconds later!)
- **Root Cause**:
  - `time_sync_trigger_forced_beacons()` only SET FLAGS (`forced_beacon_count=5`, `forced_beacon_next_ms=0`)
  - But beacons were only SENT when `perform_periodic_update()` called `time_sync_should_send_beacon()`
  - `perform_periodic_update()` was called based on ADAPTIVE INTERVAL (10-60 seconds)
  - After system stabilized, adaptive interval was 10+ seconds, so forced beacons were delayed!
  - At startup, interval was short (1-2 seconds), so forced beacons worked correctly
  - Result: CLIENT didn't receive new motor_epoch_us/motor_cycle_ms for 10-60 seconds after mode changes
- **Analysis Evidence**:
  - v0.6.67 logs show startup beacons working (1/5 through 5/5 within 5 seconds)
  - Mode change logs show 51-second delay before forced beacon burst
  - CLIENT motor cycle logs confirm 2000ms period after mode change (should be 1000ms)
- **Fix** (v0.6.68):
  - Added new message type `TIME_SYNC_MSG_TRIGGER_BEACONS` to wake up time_sync_task
  - Added API function `time_sync_task_trigger_beacons()` to send this message
  - Modified `time_sync_trigger_forced_beacons()` to call the new API after setting flags
  - Handler in time_sync_task.c sends all 5 forced beacons immediately (with 200ms spacing)
  - Beacons now sent within 1 second of mode change (vs 10-60 seconds before)
- **Impact**:
  - CLIENT receives new motor_epoch_us/motor_cycle_ms within ~1 second of mode change
  - Eliminates extended desync period after mode changes
  - Both devices now transition to new frequency together (professional UX)
- **Files Modified**:
  - `src/time_sync_task.h:57` - Added `TIME_SYNC_MSG_TRIGGER_BEACONS` enum value
  - `src/time_sync_task.h:175-189` - Added `time_sync_task_trigger_beacons()` declaration
  - `src/time_sync_task.c:204-221` - Added API function implementation
  - `src/time_sync_task.c:241-274` - Added message handler with immediate beacon burst
  - `src/time_sync.c:23` - Added include for time_sync_task.h
  - `src/time_sync.c:1394-1407` - Modified to call new API function
  - `src/firmware_version.h:33` - Version bump to v0.6.68

---

## [0.6.57] - 2025-12-03

### Added

**Phase 6t: Fast Lock with Coordinated Motor Start**:
- **Forced Beacon Burst After Handshake**: SERVER triggers 5 beacons at 200ms intervals (vs 3 @ 500ms in Phase 6r)
  - Enables ~1s lock acquisition (vs 5+ seconds in Phase 6s)
  - Research basis: IEEE/Bluetooth SIG papers show 50-100ms lock achievable for biomedical BLE sensors with rapid beacon bursts handling 16-50ppm crystal drift (ESP32-C6 is ~16ppm)
  - **Implementation**: `src/time_sync_task.c:670-682` (trigger after handshake)
  - `src/time_sync.c:975-983` (beacon timing logic)
  - `src/time_sync.c:1378-1394` (forced beacon setup)
- **Early Lock Detection**: Allows lock during fast-attack mode if offset variance < ±2ms
  - Checks last 5 valid beacon samples for low variance
  - Enables lock before reaching steady-state (sample_count 10+)
  - Reduces lock time from 2-3s to ~1s
  - **Implementation**: `src/time_sync.c:1513-1557` (44 lines)
- **Coordinated Motor Start**: Both SERVER and CLIENT wait ~1.5s before starting motors
  - SERVER waits for CLIENT to achieve fast lock
  - Coordinated start delay increased from 500ms to 1500ms
  - Both devices start within ~100ms of each other (vs CLIENT appearing unresponsive for 5s)
  - **Implementation**: `src/motor_task.c:564-573` (coordinated start timing)

### Changed

**Root Cause Analysis - Startup UX Issue**:
- **Problem**: SERVER started motors immediately while CLIENT waited 5s for lock, appearing broken
- **Phase 6s Behavior**: CLIENT timeout at 11.4s after 5s wait, SERVER already buzzing at 10.4s
- **Root Cause**: Phase 6s required 10 beacon samples for steady-state lock, but beacons arrived at 1-2s intervals → 10-20s wait
- **Solution**: Fast lock via rapid beacon burst + early variance-based lock detection

**Protocol Hardening**:
- Increased beacon burst from 3→5 beacons for better convergence
- Reduced interval from 500ms→200ms for faster lock acquisition
- Variance-based early lock (±2ms threshold) inspired by Kalman filter approaches in literature

**Expected Performance**:
- **Startup**: Both devices synchronized within ~1.5s (vs SERVER immediate + CLIENT 5s timeout)
- **Lock Time**: ~1s with fast lock (vs 2-3s in Phase 6s, 5s+ timeout fallback)
- **User Experience**: Both devices responsive, professional synchronized feel
- **Phase Error**: Stable ±10ms from first cycle (maintained from Phase 6s)

### Files Modified
- `src/time_sync_task.c:670-682` - Trigger forced beacon burst after handshake
- `src/time_sync.c:975-983, 1378-1394` - Fast lock beacon burst (5 @ 200ms)
- `src/time_sync.c:1513-1557` - Early lock detection (variance < ±2ms)
- `src/motor_task.c:564-573` - Coordinated start delay (1.5s)
- `src/firmware_version.h:33` - Version v0.6.57

---

## [0.6.56] - 2025-12-03

### Added

**Phase 6s: Two-Stage Antiphase Lock (Eliminates Startup & Mode Switch Jitter)**:
- **Lock Detection Function**: `time_sync_is_antiphase_locked()` determines when time sync has converged to stable state
  - Checks handshake complete (precise NTP-style bootstrap)
  - Verifies minimum 3 beacons received (filter has data)
  - Confirms filter in steady-state mode (sample_count >= 10, alpha = 10%)
  - Validates beacon not stale (within 2× adaptive interval)
  - Expected lock time: 2-3 seconds from connection
  - **Implementation**: `src/time_sync.c:1466-1531` (66 lines)
  - **API Declaration**: `src/time_sync.h:670-692`
- **Pre-Motor-Start Lock Wait**: CLIENT waits for antiphase lock before starting motors
  - Prevents startup jitter from EWMA filter oscillation during fast-attack mode (±1-5ms offset changes)
  - 5-second timeout (fallback to best-effort start if lock not achieved)
  - Logs lock acquisition time for diagnostics
  - **Implementation**: `src/motor_task.c:723-755` (33 lines)
  - **Expected outcome**: Clean bilateral feel from first cycle (no "keep getting closer" convergence)
- **Periodic Lock Monitoring**: Checks lock status every 10 cycles during operation
  - Detects lock loss (stale beacons, connection issues, etc.)
  - Automatically requests forced beacons from SERVER for fast re-convergence
  - Logs lock status changes only (avoids spam)
  - **Implementation**: `src/motor_task.c:993-1033` (41 lines)
  - **Benefits**: Prevents long-term drift or desynchronization during sessions
- **Mode Change Integration**: Automatic re-lock after mode changes
  - Phase 6r forced beacons + filter reset already implemented in `time_sync_task.c:458-470`
  - Periodic lock monitoring detects when re-lock established (~1.5s)
  - No additional blocking wait needed (motors continue during convergence)
- **Files Modified**:
  - `src/time_sync.c:1466-1531` - Added `time_sync_is_antiphase_locked()` implementation
  - `src/time_sync.h:670-692` - Added lock detection API declaration
  - `src/motor_task.c:723-755` - Added pre-motor-start lock wait for CLIENT
  - `src/motor_task.c:993-1033` - Added periodic lock monitoring (every 10 cycles)
  - `src/firmware_version.h:33` - Version v0.6.56

### Changed

**Root Cause Analysis**:
- **Problem**: Startup jitter - devices converge toward in-phase instead of antiphase for 10-20 seconds
- **Root Cause**: Filter offset oscillates ±1-5ms during fast-attack mode (30% alpha, samples 0-9)
  - Phase calculations use this noisy offset
  - Produces incorrect negative drift values (e.g., drift=-997ms when actually +3ms)
  - CLIENT applies SLOW-DOWN corrections, pushing toward in-phase convergence
- **Solution**: Wait for filter to reach steady-state (10% alpha, samples 10+) before starting motors
  - Offset stable within ±0.3-1ms (vs ±1-5ms during fast-attack)
  - Phase calculations use converged offset from first cycle
  - Clean antiphase from motor start

**Design Decision**:
- **Option A rejected**: Disable drift corrections during fast-attack mode (workaround for symptom)
- **Two-stage lock chosen**: Address root cause by waiting for filter convergence
  - More principled approach (similar to IEEE 1588 PTP lock detection)
  - Enables stable phase calculations from motor start
  - Reuses existing forced beacon + filter reset mechanisms from Phase 6r

**Expected Performance**:
- **Startup**: Motors start 2-3 seconds after connection (vs immediate jerky start)
- **Phase Error**: Immediately stable within ±10ms from first cycle (vs 10-20 seconds convergence)
- **Mode Changes**: Brief pause (~1.5s) → smooth restart (vs 10-40 seconds jerky corrections)
- **Lock Maintenance**: Automatic forced beacon request if lock lost during session

---

## [0.6.55] - 2025-12-02

### Added

**Phase 6r: Mode Change Fast-Attack Filter**:
- **Filter Reset on Mode Change**: Automatically resets EWMA filter to fast-attack mode (alpha=30%) when mode changes
  - Triggered by `SYNC_MSG_MODE_CHANGE` coordination message
  - Resets `sample_count=0` to force fast alpha for next 12 samples
  - Preserves current `filtered_offset_us` instead of resetting to zero (avoids large jumps)
  - Reduces outlier threshold from 100ms to 50ms during fast-attack mode
  - **Expected outcome**: ~1.5s to adapt (vs 10-40s jerky corrections previously)
- **Forced Beacon Sequence**: SERVER sends 3 immediate beacons at 500ms intervals after mode change
  - First beacon sent immediately (forced_beacon_next_ms = 0)
  - Subsequent beacons at 500ms intervals
  - Returns to adaptive interval (10-60s) after 3rd beacon
  - Helps CLIENT filter converge quickly after motor epoch reset
  - **Implementation**: `time_sync_trigger_forced_beacons()` API for SERVER role
- **Dynamic Outlier Threshold**: Threshold adapts based on filter mode
  - Fast-attack mode (samples 0-11): 50ms threshold (more aggressive convergence)
  - Steady-state mode (samples 12+): 100ms threshold (same as v0.6.54)
- **Files Modified**:
  - `src/time_sync.h:145-152` - Added fast-attack outlier threshold constant and API declaration
  - `src/time_sync.h:192-194` - Added forced beacon state fields to `time_sync_state_t`
  - `src/time_sync.h:600-611` - Added `time_sync_trigger_forced_beacons()` API declaration
  - `src/time_sync.c:600-616` - Implemented `time_sync_reset_filter_fast_attack()` function
  - `src/time_sync.c:673-674` - Added dynamic outlier threshold based on sample count
  - `src/time_sync.c:816-847` - Modified `time_sync_should_send_beacon()` to support forced beacon mode
  - `src/time_sync.c:1193-1216` - Implemented `time_sync_trigger_forced_beacons()` function
  - `src/time_sync_task.c:486-493` - Added filter reset and forced beacon trigger on mode change
  - `src/firmware_version.h:33` - Version v0.6.55

### Fixed

**Phase 6r: BLE Connection Timing Race Conditions**:
- **Issue**: `time_sync_on_reconnection()` called too early during GAP connection event
  - Caused `BLE_HS_EALREADY` (259) - operation already in progress
  - Caused `BLE_ERR_UNK_CONN_ID` (0x202) - connection handle not valid yet
  - Caused `BLE_HS_EDONE` (547) - previous operation not complete
  - Connection would eventually succeed but logged spurious errors
- **Root Cause**: Called at ~1557ms before service discovery and CCCD write completed
- **Solution**: Moved `time_sync_on_reconnection()` from GAP connect event to CCCD write callback
  - Now called at ~1697ms after services discovered, characteristics found, notifications enabled
  - ~140ms delay ensures connection fully ready before time sync initialization
  - Eliminates all three BLE error codes
- **Files Modified**:
  - `src/ble_manager.c:2466-2474` - Removed early call from GAP connect event (replaced with comment)
  - `src/ble_manager.c:1916-1929` - Added call after CCCD write succeeds in `gattc_on_cccd_write()`

---

## [0.6.54] - 2025-12-02

### Added

**Phase 6r: Immediate Bootstrap Beacon (Option A)**:
- **SERVER sends beacon immediately after TIME_RESPONSE** instead of waiting for first periodic interval
- **First sample timing**: ~2s after BLE connection (down from 4.35s = 54% faster)
- **Then fast interval**: t=3s, t=4s, t=5s... (1s intervals from v0.6.53)
- **Expected convergence**: 3-4 seconds to ±100 μs band (down from 5-8s in v0.6.53)
- **Implementation**: Single 9-line addition after handshake completion
- **Benefits**:
  - Filter gets first sample 2.35s earlier
  - 9 samples by t=10s (vs 7 in v0.6.53, vs 3 in v0.6.52)
  - More robust to unlucky first sample (more data for outlier detection)
  - Negligible overhead (one extra 23-byte packet)
- **Files Modified**:
  - `src/time_sync_task.c:652-661` - Added immediate beacon send after TIME_RESPONSE sent
  - `src/firmware_version.h:33` - Version v0.6.54

---

## [0.6.53] - 2025-12-02

### Changed

**Phase 6r: Fast Convergence Optimization**:
- **Beacon Interval**: Reduced `TIME_SYNC_INTERVAL_MIN_MS` from 10000ms to 1000ms (10× faster startup)
  - **Before**: 3 beacons in first 30 seconds (at t=4.35s, 13.90s, 23.95s)
  - **After**: 10+ beacons in first 10 seconds (expected convergence in 5-8 seconds)
  - Adaptive backoff still works: 1s → 10s → 20s → 60s based on quality
  - **Impact**: Negligible power (23 bytes/s for 10s = 230 bytes total)
- **Dual-Alpha EMA**: Implemented fast-attack filter for startup
  - **First 10 samples**: alpha=30% (fast tracking, 3× faster convergence)
  - **Samples 11+**: alpha=10% (heavy smoothing, same long-term stability as v0.6.52)
  - **Benefit**: Robust to unlucky first sample (±500 μs error recovery in seconds, not minutes)
  - **Tradeoff**: Slightly more sensitive to outliers during startup (30% vs 10%)
- **Expected Performance**:
  - Convergence: 5-8 seconds to ±100 μs band (down from 4.35s with lucky first sample, robust to all conditions)
  - Long-term stability: Same as v0.6.52 (±29 μs jitter over 90 minutes)
  - Outlier rejection: Same 200ms threshold
- **Files Modified**:
  - `src/time_sync.h:49` - Changed `TIME_SYNC_INTERVAL_MIN_MS` from 10000 to 1000
  - `src/time_sync.c:663` - Added dual-alpha logic: `alpha = (sample_count < 10) ? 30 : 10`
  - `src/firmware_version.h:33` - Version v0.6.53

---

## [0.6.52] - 2025-12-02

### Added

**Phase 6r Steps 2-3: EMA Filter + RTT Removal (AD043)**:
- **Step 2: EMA Filter Implementation**:
  - Added exponential moving average filter with outlier rejection for one-way timestamp smoothing
  - Filter constants: alpha=10% (heavy smoothing), ring_size=8, outlier_threshold=200ms
  - Outlier detection: Reject samples >200ms deviation from filtered value
  - Ring buffer stores last 8 samples for debugging and correlation analysis
  - Filter statistics logged every 10 samples to track outlier percentage
  - **Benefits**: Smooths out BLE transmission delay variation (±10-30ms typical, 300ms outliers)
  - **Expected outcome**: <5ms mean error vs ±15ms current with RTT approach
- **Step 3: RTT Logic Removal (COMPLETE)**:
  - Removed RTT message types from `ble_manager.h`: `SYNC_MSG_BEACON_RESPONSE`, `SYNC_MSG_RTT_RESULT`
  - Removed RTT payload structures: `time_sync_beacon_response_t`, `time_sync_rtt_result_t`
  - Removed RTT case handlers from `time_sync_task.c` (Bug #27 beacon response and RTT result processing)
  - Removed Bug #41 RTT-based clamping logic from `motor_task.c` (replaced with simple frequency-dependent clamping)
  - Removed all 4 RTT function implementations from `time_sync.c`:
    - `time_sync_record_beacon_t1()` (117 lines)
    - `time_sync_process_beacon_response()` (90 lines)
    - `time_sync_get_measured_rtt()` (15 lines)
    - `time_sync_update_offset_from_rtt()` (95 lines)
  - Removed RTT state variable references in `time_sync_on_disconnection()`
  - Replaced `last_rtt_update_ms` with `last_beacon_time_us` in `time_sync_get_predicted_offset()`
  - **Total code removed**: ~320 lines of RTT-related logic
  - **Compilation status**: ✅ Clean build (one minor unused function warning)
- **Files Modified (Step 2 - EMA Filter)**:
  - `src/time_sync.h:86-127` - Added filter constants and structures (`TIME_FILTER_*`, `time_sample_t`, `time_filter_t`)
  - `src/time_sync.h:195-196` - Added `time_filter_t filter` to `time_sync_state_t`
  - `src/time_sync.c:65` - Added `update_time_filter()` forward declaration
  - `src/time_sync.c:92-94` - Initialize filter in `time_sync_init()`
  - `src/time_sync.c:445-447` - Apply EMA filter to raw offset in `time_sync_process_beacon()`
  - `src/time_sync.c:598-689` - Implemented `update_time_filter()` function (93 lines)
- **Files Modified (Step 3 - RTT Removal)**:
  - `src/ble_manager.h:355-356` - Removed `SYNC_MSG_BEACON_RESPONSE` and `SYNC_MSG_RTT_RESULT` enum values
  - `src/ble_manager.h:418-444` - Removed RTT payload structures (27 lines)
  - `src/ble_manager.h:475-476` - Removed RTT payload union members
  - `src/time_sync.h:603-665` - Removed RTT API declarations (4 functions, 63 lines)
  - `src/time_sync.h:218-231` - Removed RTT state variables (6 variables)
  - `src/time_sync_task.c:686-738` - Removed RTT case handlers (53 lines)
  - `src/motor_task.c:1614-1665` - Replaced Bug #41 RTT-based logic with simple clamping (52 lines)
  - `src/time_sync.c:208-211` - Removed RTT state clearing in disconnection handler
  - `src/time_sync.c:1246-1248` - Removed "BUG #27 FIX" section header
  - `src/time_sync.c:1250-1488` - Removed 4 RTT function implementations (239 lines)
  - `src/time_sync.c:1281,1285,1294-1295` - Replaced `last_rtt_update_ms` with `last_beacon_time_us`
  - `src/firmware_version.h:33` - Version v0.6.52

---

## [0.6.51] - 2025-12-02

### Changed

**Phase 6r Step 1: Simplified Beacon Structure (AD043)**:
- **Context**: Grok AI analysis identified RTT measurement overhead as root cause of timing instability. 300ms RTT spikes → 150ms stale timestamps → ±15ms jitter despite corrections. Recommend industry-standard filtered one-way timestamp approach.
- **Changes**:
  - Beacon structure reduced from 28 to 23 bytes (removed `session_ref_ms`, `quality_score`, `server_rssi`, `reserved`)
  - Renamed `timestamp_us` → `server_time_us` for clarity (one-way timestamp)
  - CLIENT captures receive time immediately, calculates raw offset: `offset = rx_time - server_time`
  - Removed beacon response (T2/T3) from CLIENT → no more 4-way RTT handshake overhead
  - Removed RSSI measurement code (not needed for filtering approach)
  - Removed `time_sync_record_beacon_t1()` call (no RTT tracking)
- **Benefits**:
  - Simpler protocol: One message instead of two (beacon + response)
  - Lower BLE bandwidth: 23 bytes vs 28 bytes per beacon
  - Eliminates RTT measurement delay (100-300ms round-trip → instant one-way)
  - Prepares for EMA filter in Step 2 (smooth out BLE transmission delay variation)
- **Files Modified**:
  - `src/time_sync.h:45-46` - Updated `TIME_SYNC_MSG_SIZE` constant (28→23)
  - `src/time_sync.h:204-210` - Simplified beacon structure
  - `src/time_sync.c:476-492` - Updated beacon generation (removed quality/RSSI fields)
  - `src/time_sync.c:427-468` - One-way offset calculation (raw, filter pending Step 2)
  - `src/time_sync_task.c:385-416` - Removed beacon response logic
  - `src/ble_manager.c:1417-1418` - Removed quality_score from debug log
  - `src/ble_manager.c:1440-1443` - Removed RSSI measurement code
  - `src/ble_manager.c:3001-3002` - Updated timestamp field name
  - `src/ble_manager.c:4320-4321` - Removed RTT recording call
  - `src/firmware_version.h:33` - Version v0.6.51
- **Next Steps**:
  - Step 2: Implement EMA filter with ring buffer for outlier detection
  - Step 3: Remove legacy RTT measurement functions and state
  - Expected outcome: <5ms mean error vs ±15ms current (3× minimum improvement)

---

## [0.6.50] - 2025-12-02

### Fixed

**Blind Toggle Causes Phase Desynchronization** (CRITICAL - Bug #50):
- **Symptom**: CLIENT state selection used a blind toggle (`client_next_inactive`) that assumed perfect 1000ms cycles forever. Any drift would cause toggle to desynchronize from SERVER's actual phase position.
- **User Observation**: "Could have something to do with a special flag that the client uses to start in inactive by default? It just seems like if you think the logic says this should be antiphase, something outside your scope is maybe changing how the client really starts vs how your logic sees it start."
- **Root Cause**: Toggle-based state selection (lines 1169-1182 in old code):
  ```c
  if (client_next_inactive) {
      state = MOTOR_STATE_INACTIVE;
      client_next_inactive = false;  // Next cycle: ACTIVE
  } else {
      state = MOTOR_STATE_ACTIVE;
      client_next_inactive = true;   // Next cycle: INACTIVE
  }
  ```
  - Toggle flips every cycle based on LOCAL cycle completion
  - No connection to SERVER's actual position in its cycle
  - Any timing drift causes toggle to drift relative to SERVER
  - Assumes perfect 1000ms cycles (no jitter, no corrections)
- **Impact**:
  - CLIENT state can drift out of phase with SERVER over time
  - Toggle can't self-correct - once wrong, stays wrong until reset
  - Especially problematic with drift corrections (Bug #49) that change cycle duration
  - Creates fragile dependency between state selection and timing corrections
- **Fix**: Replace toggle with position-based state calculation (`src/motor_task.c:1167-1196`):
  - Calculate SERVER's position in current cycle every time
  - Determine if SERVER is in first half (ACTIVE) or second half (INACTIVE)
  - Set CLIENT to opposite state (antiphase coordination)
  - Algorithm:
    ```c
    // Calculate SERVER's current position
    uint64_t elapsed_us = sync_time_us - server_epoch_us;
    uint64_t cycles_since_epoch = elapsed_us / cycle_us;
    uint64_t server_cycle_start_us = server_epoch_us + (cycles_since_epoch * cycle_us);
    uint64_t position_in_cycle_us = sync_time_us - server_cycle_start_us;

    // SERVER in first half = ACTIVE, CLIENT should be INACTIVE (antiphase)
    bool server_is_active = (position_in_cycle_us < half_cycle_us);
    state = server_is_active ? MOTOR_STATE_INACTIVE : MOTOR_STATE_ACTIVE;
    ```
- **Benefits**:
  - Deterministic state selection based on SERVER's actual position
  - No state to get out of sync - calculated fresh every cycle
  - Self-correcting - always reflects SERVER's true phase
  - Works correctly even with drift corrections changing cycle duration
  - Simpler mental model - CLIENT always does opposite of SERVER's current position
- **Files Modified**:
  - `src/motor_task.c:410` - Removed `client_next_inactive` variable declaration
  - `src/motor_task.c:598-606` - Removed toggle initialization and logging
  - `src/motor_task.c:1167-1196` - Replaced toggle logic with position-based calculation
- **Expected Outcome**:
  - CLIENT state always correctly antiphase to SERVER
  - No phase drift over time
  - Robust to timing corrections and jitter
  - Logs show: "CLIENT: Position-based state: SERVER ACTIVE (pos=500/1000 ms) → CLIENT INACTIVE"

---

## [0.6.49] - 2025-12-02

### Fixed

**Time Domain Mismatch in Motor Epoch Causes In-Phase Activation Overlap** (CRITICAL - Bug #49):
- **Symptom**: CLIENT starts with correct state (INACTIVE when SERVER ACTIVE), but timing is wrong, causing both devices to activate simultaneously later. CLIENT's first INACTIVE period is 1209ms instead of 1000ms. Both devices ACTIVE together for ~109ms.
- **Activation Overlap Timeline**:
  ```
  11:14:24.295: SERVER ACTIVE starts (cycle 2)
  11:14:24.431: CLIENT ACTIVE starts ← 136ms later, BOTH ACTIVE!
  11:14:24.540: SERVER INACTIVE starts
  11:14:24.676: CLIENT INACTIVE starts

  Overlap: 109ms of simultaneous activation (in-phase, not antiphase!)
  ```
- **Evidence from Logs**:
  ```
  CLIENT: Motor epoch set: 6851136 us (synchronized time)
  CLIENT PHASE CALC: sync_time=11665475 us, epoch=6851136 us (age=4814 ms)
  CLIENT PHASE CALC: cycles_since_epoch=2 ← Should be 0! CLIENT just started!
  CLIENT SLOW-DOWN: drift=-815 ms, correction=+200 ms ← Wrong correction
  Result: First INACTIVE = 1209ms (should be 1000ms) → phase misalignment
  ```
- **Root Cause**: Bug #47 fix set epoch using `esp_timer_get_time()` (LOCAL time domain), but all phase calculations use `time_sync_get_time()` (SYNCHRONIZED time domain)
  - SERVER/CLIENT have ~360ms clock offset (time sync correction)
  - Epoch set in local time: 6851ms local → stored as 6851ms
  - Phase calculation uses synchronized time: 11665ms sync - 6851ms = 4814ms age
  - **Wrong time domain:** 4814ms / 2000ms = 2.4 cycles elapsed (CLIENT thinks it's on cycle #2, but it just started!)
  - CLIENT applies +200ms slow-down correction to first INACTIVE period
  - 1000ms + 200ms = 1200ms → CLIENT ACTIVE delayed into SERVER's next ACTIVE cycle
- **Impact**:
  - Both devices activate simultaneously (in-phase) instead of alternating (antiphase)
  - Defeats entire purpose of bilateral alternation for therapeutic effect
  - User feels synchronized pulses instead of alternating pattern
  - All drift calculations wrong from first cycle onward
- **Fix**: Use synchronized time when setting motor epoch (`src/motor_task.c:819-825`)
  - Changed from `actual_start_us = esp_timer_get_time();` (local time)
  - Changed to `time_sync_get_time(&actual_start_us)` (synchronized time)
  - Fallback to local time only if time_sync_get_time() fails (should never happen)
  - Epoch now in same time domain as phase calculation reference
- **Expected Outcome**:
  - CLIENT phase calculation: age = 0ms on first cycle (correct!)
  - First INACTIVE period: 1000ms (not 1209ms)
  - No phantom drift corrections on early cycles
  - Antiphase timing accurate: SERVER ACTIVE at T=0, CLIENT ACTIVE at T=1000ms ±10ms
  - No activation overlap - devices alternate as designed

---

## [0.6.48] - 2025-12-02

### Fixed

**Watchdog Initialization Error on Deep Sleep Wake** (Bug #48):
- **Symptom**: On wake from deep sleep, watchdog initialization fails with `ESP_ERR_INVALID_STATE`:
  ```
  E (442) task_wdt: esp_task_wdt_init(517): TWDT already initialized
  E (452) MAIN: Watchdog init failed: ESP_ERR_INVALID_STATE
  E (462) MAIN: Watchdog init failed, continuing anyway
  ```
- **Root Cause**: Code unconditionally calls `esp_task_wdt_init()` on every boot. On wake from deep sleep, the watchdog timer is already initialized by the bootloader, causing the error.
- **Impact**: Harmless but noisy error logs on approximately 25% of boots (specifically when waking from deep sleep via button press). System continued to function normally despite the error.
- **Fix**: Check if watchdog is already initialized before attempting to initialize it (`src/main.c:143-164`):
  - Call `esp_task_wdt_status(NULL)` to check initialization state
  - Only call `esp_task_wdt_init()` if status returns `ESP_ERR_INVALID_STATE` (not initialized)
  - Log "Watchdog already initialized (wake from deep sleep)" on wake from sleep
  - Eliminates error messages while maintaining proper initialization on cold boot
- **Expected Outcome**: Clean startup logs on both cold boot and deep sleep wake, no error messages

---

## [0.6.47] - 2025-12-02

### Fixed

**Motor Epoch Set Before Actual Start Causes In-Phase Activation** (CRITICAL - Bug #47):
- **Symptom**: After Bug #46 fix, devices still activate in-phase (within 50ms) instead of antiphase (1000ms offset). Bug #46 fixed CLIENT abort issue, but didn't resolve root timing problem.
- **Evidence from Logs (Post-Bug-#46)**:
  ```
  08:55:36.316 > SERVER: T=9782ms: Set epoch=9857669 μs, beacon sent
  08:55:36.491 > CLIENT: Pre-calculated antiphase: server_pos=1385/2000 ms (69.3%), wait=1614 ms
  08:55:36.804 > SERVER: T=10222ms: Motors actually start (440ms AFTER epoch!)
  08:55:36.810 > SERVER: MOTOR_STARTED notification sent (epoch=9857669)
  08:55:38.398 > CLIENT: Completed full 1587ms wait (no abort - Bug #46 fixed!)
  08:55:38.820 > SERVER ACTIVE (T=10222ms)
  08:55:38.856 > CLIENT ACTIVE (T=10256ms) ← 36ms apart, IN-PHASE!
  ```
- **Root Cause**: SERVER sets motor_epoch to coordinated_start_us (TARGET time) BEFORE waiting
  - Line 566/584: `time_sync_set_motor_epoch(coordinated_start_us, cycle_ms);` called before wait
  - SERVER waits ~440ms, then starts motors at T=10222ms
  - CLIENT receives epoch=9857669 μs (T=9857ms), but SERVER actually started at T=10222ms
  - CLIENT's antiphase calculation: `elapsed_us = sync_time_us - server_epoch_us` uses PAST reference
  - Result: CLIENT calculates position based on time 364ms in the PAST → wrong phase offset
- **Timeline Analysis**:
  ```
  T=9782ms:  SERVER sets epoch = coordinated_start_us = 9857669 μs (target)
  T=9857ms:  (Target time - doesn't match actual start)
  T=10222ms: SERVER actually starts motors (364ms LATER than epoch!)
             SERVER sends MOTOR_STARTED with epoch=9857669 (OLD time)
  T=10256ms: CLIENT receives epoch, calculates antiphase using 9857669 reference
             CLIENT calculation based on PAST time → IN-PHASE result
  ```
- **Impact**:
  - Bug #46 fix worked correctly (no abort during wait)
  - But antiphase calculation still wrong due to incorrect epoch reference
  - Strategy A calculation is correct, but uses wrong input data
  - All Phase 6 testing still shows in-phase activation
- **Fix**: Move motor_epoch setting from target time to ACTUAL motor start time (`src/motor_task.c:566, 584, 813-818`)
  - Removed early epoch setting at lines 566, 584 (before wait)
  - Added epoch setting RIGHT AFTER "Coordinated start time reached" log (line 815-818)
  - Use `esp_timer_get_time()` for actual motor start time (not coordinated_start_us target)
  - Applied to both SERVER and CLIENT roles
  - MOTOR_STARTED notification now contains correct epoch (actual start time)
- **Expected Outcome**:
  - SERVER sets epoch at T=10222ms (actual start) instead of T=9857ms (target)
  - CLIENT receives correct epoch reference
  - CLIENT antiphase calculation: `elapsed_us = sync_time_us - 10222000` uses correct reference
  - Devices activate in antiphase: SERVER at T=0, CLIENT at T=1000ms (±50ms tolerance)
- **Testing Required**: Hardware test with both devices to confirm antiphase timing with corrected epoch

---

## [0.6.46] - 2025-12-02

### Fixed

**In-Phase Motor Activation Instead of Antiphase** (CRITICAL - Bug #46):
- **Symptom**: Both devices activating motors simultaneously (within 50ms) instead of alternating. User reported "feels like the devices are trying to activate in phase instead of bilateral antiphase."
- **Evidence from Logs**:
  ```
  08:42:08.215: Dev B ACTIVE
  08:42:08.243: Dev A ACTIVE (28ms later!) ← IN-PHASE!

  08:42:10.200: Dev A ACTIVE
  08:42:10.215: Dev B ACTIVE (15ms later!) ← IN-PHASE!
  ```
  - Expected: Device A ACTIVE at T=0ms, Device B ACTIVE at T=1000ms (antiphase)
  - Actual: Both devices ACTIVE within 50ms (in-phase)
- **Root Cause**: CLIENT aborted antiphase wait when `MOTOR_STARTED` message arrived
  - CLIENT calculated correct antiphase wait: `server_pos=1561/2000 ms (78.1%), wait=1438 ms`
  - MOTOR_STARTED message arrived during wait
  - Abort logic at `src/motor_task.c:793-796` broke out of wait loop immediately
  - CLIENT started motors ~1400ms early, synchronized with SERVER (in-phase)
- **Impact**:
  - Bilateral stimulation ineffective (requires antiphase for therapeutic effect)
  - All Phase 6 testing has been in-phase, not antiphase
  - Correction algorithms tested on wrong phase relationship
- **Fix**: Disable MOTOR_STARTED abort when Strategy A (antiphase pre-calculation) active (`src/motor_task.c:786-799`)
  - Added `strategy_a_active` flag: `(role == PEER_ROLE_CLIENT && unclamped_correction_cycles == 0)`
  - MOTOR_STARTED abort only happens if NOT using Strategy A
  - When Strategy A active, CLIENT must complete full antiphase wait
  - Preserves fast startup for non-Strategy-A paths (backward compatibility)
- **Expected Outcome**:
  - Device A ACTIVE → Device B ACTIVE exactly 1000ms later (at 0.5 Hz)
  - User should feel distinct alternating pattern, not simultaneous activation
- **Testing Required**: Hardware test with both devices to confirm antiphase timing

---

## [0.6.45] - 2025-12-02

### Fixed

**Peer Connection Accepted After 30s Pairing Window** (CRITICAL - Bug #45):
- **Symptom**: Devices that powered on at different times would pair even after 30s window expired. Also, mobile apps could connect during early peer pairing (e.g., if peer paired at T=5s, app connecting at T=10s would be misidentified as peer).
- **Evidence from Logs**:
  - Dev A: Discovered peer at T=29.781s (within window), initiated connection
  - Dev B: Received connection at T=30.111s (AFTER window), incorrectly accepted as peer
  - Both devices successfully paired despite 30.111s > 30s timeout
- **Root Causes**:
  1. **Time-based check missing**: Connection handler only checked `current_uuid == &uuid_bilateral_service`, didn't verify pairing window still open
  2. **BLE handshake latency**: Peer initiated at T=29.9s, arrived at T=30.1s (after timeout)
  3. **Early pairing vulnerability**: If peer paired at T=5s, mobile app at T=10s would still see Bilateral UUID until `peer_connected` flag updated
  4. **Race condition**: Simultaneous connections could both be identified as peers before flag updated
- **Impact**:
  - Tech spike impossible (both devices always paired)
  - Breaks architectural assumption that peer pairing only happens within 30s window
  - Mobile apps blocked from connecting during 0-30s window even after peer pairing complete
- **Fix**: Flag-based pairing window closure (`src/ble_manager.c:438-441, 2307-2333, 3678-3705` + `src/ble_manager.h:167-180` + `src/ble_task.c:286-288`)
  - Added `peer_pairing_window_closed` static flag
  - Close window when EITHER: (1) First peer identified OR (2) 30s timeout expires
  - Connection handler checks: `current_uuid == &uuid_bilateral_service AND !peer_pairing_window_closed`
  - Flag set IMMEDIATELY when first peer identified (line 2319) - prevents simultaneous connection race
  - Flag set by `ble_close_pairing_window()` called from ble_task timeout handler (line 288)
  - Flag reset by `ble_reset_pairing_window()` to allow re-pairing after disconnect
- **Additional Fix**: Role preservation across temporary disconnects
  - **Issue**: Original `ble_reset_pairing_window()` cleared `peer_state.role`, breaking time sync continuity
  - **Impact**: After temporary disconnect, devices didn't know which was SERVER/CLIENT for reconnection
  - **Fix**: Preserve `peer_state.role` in `ble_reset_pairing_window()` (line 3678-3695)
  - **Rationale**: Roles must persist for time sync relationship (SERVER sends beacons, CLIENT applies corrections)
- **Expected Outcomes**:
  1. Devices powered on >30s apart will NOT pair (timeout → single-device mode)
  2. Mobile apps can connect after early peer pairing (e.g., peer at T=5s, app at T=10s works)
  3. Simultaneous connections handled correctly (second connection rejected)
  4. Temporary disconnects maintain SERVER/CLIENT roles for time sync continuity
- **Use Case**: Enables tech spike - power on devices separately to measure natural oscillator drift

---

## [0.6.44] - 2025-12-02

### Changed - Versioning Scheme

**New Semantic Versioning Convention:**
- **MINOR version tracks PHASE number**: Phase 6 → v0.6.x, Phase 7 → v0.7.x
- **PATCH version tracks BUG number**: Bug #44 → v0.x.44, Bug #45 → v0.x.45
- **Benefits**: Logs instantly show context - "v0.6.44" = Phase 6, Bug 44 fix
- **Example**: v0.6.44 clearly indicates Phase 6 bilateral motor coordination, Bug #44 fix

### Fixed

**Battery Extraction Failure from Scan Response** (CRITICAL - Bug #44):
- **Symptom**: After Bug #43 fix, battery-based role assignment still failing. Logs showed "No peer battery data - falling back to discovery-based role"
- **Root Cause**: Battery Service Data was added to SCAN RESPONSE (via `ble_gap_adv_rsp_set_fields()`), but scanner only parsed ADVERTISING DATA (`event->disc.data`). Even with active scanning enabled, NimBLE stores advertising and scan response data separately. Scanner never saw battery data.
- **Evidence**:
  - Advertising: Battery added to scan response at `src/ble_manager.c:3566-3567`
  - Scanning: Only advertising data parsed at `src/ble_manager.c:3654` via `event->disc.data`
  - Result: `fields.svc_data_uuid16` always NULL, battery extraction failed
- **Fix**: Moved battery Service Data from scan response to ADVERTISING DATA (`src/ble_manager.c:3540-3583`)
  - Created `ble_update_advertising_data()` function (mirrors `ble_update_scan_response()`)
  - Battery now in advertising packet: flags (3B) + TX power (3B) + name (~12B) + battery (3B) = ~21B (fits in 31B limit)
  - UUID remains in scan response (17B) for dynamic switching (Bilateral ↔ Config)
  - Both `ble_update_advertising_data()` and `ble_update_scan_response()` called when starting advertising
- **Expected Outcome**: Scanners will now extract battery from `event->disc.data`, battery-based role assignment will work correctly
- **Files Modified**: `src/ble_manager.c:3540-3612` (new function + updated `ble_start_advertising()` + updated init)

### Added

**Tech Spike: Single-Device Drift Baseline Measurement** (December 2, 2025):
- **Purpose**: Measure natural oscillator drift between two independent devices (no peer connection, no corrections)
- **Compile-Time Flag**: `ENABLE_SINGLE_DEVICE_DRIFT_BASELINE` in `src/motor_task.c:64-69`
- **Behavior When Enabled**:
  - Continuous activation logging even when `role == PEER_ROLE_NONE` (no peer connected)
  - Both devices run as independent SERVERs using nominal timing
  - Logs compatible with existing `analyze_bilateral_phase_detailed.py` script
- **Goal**: Compare isolated device timing vs synchronized timing to determine:
  - What the drift correction algorithm is actually correcting
  - Whether corrections add noise instead of improving timing
  - Optimal correction interval based on actual crystal oscillator drift
- **Files Modified**: `src/motor_task.c:1159-1169, 1393-1403` (conditional logging)

### Infrastructure

- Firmware version: v0.3.1 → v0.6.44 (new versioning scheme)
- Version header updated: `src/firmware_version.h:29-34` (comments added)

---

## Phase 6: Bilateral Motor Coordination (In Progress)

### Added - Phase 6: Bilateral Motor Coordination (In Progress)

**BLE TX Power Boost (+6 dBm improvement):**
- **Maximum TX Power**: Set to +9 dBm for advertising, scanning, and connections
- **Default was +3 dBm**: Resulted in weak RSSI (-98 dBm) with nylon case and body attenuation
- **API**: `esp_ble_tx_power_set_enhanced()` for ESP32-C6 (ESP-IDF recommended approach)
- **Power Types Configured**:
  - `ESP_BLE_ENHANCED_PWR_TYPE_ADV`: Advertising/discoverable mode
  - `ESP_BLE_ENHANCED_PWR_TYPE_SCAN`: Peer discovery scanning
  - `ESP_BLE_ENHANCED_PWR_TYPE_DEFAULT`: Active connections
- **Expected RSSI Improvement**: ~6 dBm stronger signal (2× power increase)
- **Use Case**: Compensates for RF attenuation from nylon enclosure and human body tissue during bilateral therapy sessions
- **Implementation**: `src/ble_manager.c:3120-3142` (ble_on_sync callback)

**Connection RSSI in Sync Beacons (Link Quality Monitoring):**
- **Purpose**: Track BLE link quality during bilateral sessions for debugging and future adaptive algorithms
- **Implementation**: `server_rssi` field added to `time_sync_beacon_t` structure (28 bytes total, was 26 bytes)
- **Measurement**: CLIENT measures SERVER RSSI when receiving sync beacons via `ble_gap_conn_rssi()`
- **Logging**: RSSI logged with every beacon at DEBUG level: "Beacon processed (seq: N, ..., RSSI: -60 dBm)"
- **Use Cases**:
  - Debug device-to-device link quality (currently -88 to -92 dBm estimated with +9 dBm TX power)
  - Future: Adaptive drift correction thresholds based on RSSI (weak signal → wider deadband)
  - Future: Predictive disconnect detection (RSSI < -90 dBm → freeze drift rate proactively)
- **Files Modified**: `src/time_sync.h:209-210`, `src/time_sync.c:484-485`, `src/ble_manager.c:1438-1446`

**Coordination Message System:**
- **SYNC_MSG_MODE_CHANGE**: Button press mode changes propagated to CLIENT device (`src/time_sync_task.c:321-366`)
- **SYNC_MSG_SETTINGS**: BLE GATT parameter changes synced to CLIENT via coordination messages
- **SYNC_MSG_SHUTDOWN**: Emergency shutdown propagation between devices
- **SYNC_MSG_START_ADVERTISING**: Re-enable BLE advertising command to CLIENT
- **SYNC_MSG_CLIENT_BATTERY**: CLIENT reports battery level to SERVER for PWA display

**Motor Epoch Mechanism:**
- Motor epoch timestamp republished on mode change for CLIENT phase alignment (`src/motor_task.c`)
- CLIENT resets to INACTIVE state when receiving new timing parameters (prevents overlap during frequency changes)

**Client Battery Characteristic (Configuration Service):**
- **UUID `...020D`**: New GATT characteristic for CLIENT battery level (`src/ble_manager.c`)
- SERVER relays CLIENT battery to PWA for dual-device battery monitoring
- Returns 0% in single-device mode, actual battery in dual-device mode
- Updates via `SYNC_MSG_CLIENT_BATTERY` coordination message

**Per-Mode PWM Intensity (Configuration Service):**
- **4 new GATT characteristics** for mode-specific motor intensity (`src/ble_manager.c`):
  - **UUID `...020E`**: Mode 0 (0.5Hz) intensity - Range 50-80%, default 65%
  - **UUID `...020F`**: Mode 1 (1.0Hz) intensity - Range 50-80%, default 65%
  - **UUID `...0210`**: Mode 2 (1.5Hz) intensity - Range 70-90%, default 80%
  - **UUID `...0211`**: Mode 3 (2.0Hz) intensity - Range 70-90%, default 80%
- **UUID `...0204`** renamed to Mode 4 (Custom) intensity - Range 30-80%, default 75%
- **Frequency-dependent intensity ranges**: Higher frequencies (1.5Hz, 2Hz) require stronger PWM (70-90%) due to shorter activation periods (83-167ms). Lower frequencies (0.5Hz, 1Hz) work well at 50-80% with longer activation periods (250-1000ms).
- **Motor task integration**: `calculate_mode_timing()` selects appropriate intensity based on current mode (`src/motor_task.c:357-376`)
- **NVS persistence**: All 5 mode intensities saved/loaded across power cycles (`src/ble_manager.c`)
- **Peer synchronization**: All 5 mode intensities synced via `SYNC_MSG_SETTINGS` (`src/time_sync_task.c:504-527`)
- **Benefits**: Each preset mode feels "right" without manual adjustment; 2Hz maintains therapeutic effectiveness despite brief 125ms activation at 25% duty

### Fixed

**Systematic Phase Offset in CLIENT Drift Correction** (CRITICAL - Bug #40):
- **Symptom**: CLIENT motor activation consistently 662ms late relative to ideal antiphase target (should be period/2 after SERVER)
- **Impact**: Over 90-minute Mode 0 baseline, 0% of cycles within acceptable ±50ms timing (100% DRIFT status)
- **Root Cause**: INACTIVE state used relative position calculation (`elapsed_us % cycle_us`) which accumulated errors from:
  - CLIENT ACTIVE duration (500ms) not accounted for in wait calculation
  - CHECK_MESSAGES processing overhead
  - FreeRTOS scheduling delays
- **Fix**: Replaced relative calculation with absolute target time (`src/motor_task.c:1410-1451`):
  1. Calculate `server_current_cycle_start_us = server_epoch_us + (cycles_since_epoch * cycle_us)`
  2. Set `client_target_active_us = server_current_cycle_start_us + half_period_us`
  3. Wait until absolute target: `target_wait_us = client_target_active_us - sync_time_us`
  4. If target in past, advance to next cycle
- **Test Results (90-minute Mode 0 baseline)**:
  - Mean phase error: +662ms → **+9.1ms** (98.6% improvement)
  - Acceptable timing (±50ms): 0% → **74.9%**
  - Excellent timing (±10ms): 0% → **18.7%**
  - DRIFT status (>50ms): 100% → **19.0%**
- **Remaining Issues**:
  - Initial convergence artifacts (first 3-5 cycles show large errors, converge quickly)
  - Periodic drift patterns around T=700-750s (temporary degradation to ±85-105ms, recovers)
  - Large std deviation (156.6ms) suggests room for further improvement
- **Next Steps**: Implement outlier rejection and predictive filtering to achieve 95% within ±10ms target

**Sign Error in Drift Correction After Bug #40** (CRITICAL - Bug #42):
- **Symptom**: Bug #41 testing showed 31× regression from Bug #40: mean phase error +9.1ms → +282.9ms, GOOD timing 18.7% → 0%, DRIFT 25.1% → 100%
- **Root Cause**: After Bug #40 changed target calculation from relative to absolute, drift correction sign interpretation became inverted
  - Bug #40 introduced: `calculated_ms = target_time - current_time` (wait duration until target)
  - Drift calc remained: `diff_ms = calculated_ms - nominal_ms`
  - **Before Bug #40**: Positive diff meant CLIENT ahead of cycle position → slow down ✓
  - **After Bug #40**: Positive diff meant target is LATE → need to catch up, but code still slowed down ✗
- **Evidence**: Phase analysis showed CLIENT +275ms LATE, but motor logs showed drift=-101ms (backwards!), applied -50ms correction (wrong direction!)
- **Fix**: Inverted sign in correction calculation (`src/motor_task.c:1548`):
  - OLD: `correction_ms = (diff_ms * P_GAIN_PCT) / 100`
  - NEW: `correction_ms = -(diff_ms * P_GAIN_PCT) / 100`
  - Also fixed adaptive EWMA sign (line 1581) for fair comparison in logs
  - Updated comments: Positive diff = target LATE = catch up (shorten INACTIVE), Negative diff = target EARLY = slow down (extend INACTIVE)
- **Expected Outcome**: Should restore Bug #40 performance (~+9ms mean, ~19% GOOD timing, ~25% DRIFT), allowing Bug #41 RTT-based clamping to be properly evaluated

**Role Assignment Inverted - No Drift Corrections Applied** (CRITICAL - Bug #43):
- **Symptom**: Bug #42 test showed oscillating phase errors with NO correction logs. Device that should be CLIENT (higher battery, higher MAC) was running as SERVER instead
- **Root Cause**: BLE role to time sync role mapping was backwards in `ble_manager.c:2407-2430`
  - **Intended (per AD010)**: BLE MASTER → SERVER (sends beacons), BLE SLAVE → CLIENT (receives beacons, applies corrections)
  - **Actual Code**: BLE MASTER → CLIENT, BLE SLAVE → SERVER (inverted!)
  - Lower battery device initiated connection (became BLE MASTER) but got CLIENT role
  - Higher battery device accepted connection (became BLE SLAVE) but got SERVER role
  - Result: Device that should apply corrections was running nominal timing instead
- **Evidence from logs**:
  - Dev_a (lower MAC): "lower MAC - initiating as SERVER" → "CLIENT role assigned (BLE MASTER)" → Motor task in CLIENT mode
  - Dev_b (higher MAC): "higher MAC - waiting as CLIENT" → "SERVER role assigned (BLE SLAVE)" → Motor task in SERVER mode (no corrections!)
  - Dev_b motor logs: All "SERVER: Cycle starts ACTIVE/INACTIVE" (nominal timing only)
  - NO "CORRECTION COMPARE" or "CATCH-UP" logs despite oscillating phase errors
- **Fix**: Swapped role assignment in connection callback (`src/ble_manager.c:2409-2432`)
  - BLE_GAP_ROLE_MASTER now assigns PEER_ROLE_SERVER (was CLIENT)
  - BLE_GAP_ROLE_SLAVE now assigns PEER_ROLE_CLIENT (was SERVER)
  - Updated comments to reflect correct AD010 mapping
- **Expected Outcome**: CLIENT device will now actually apply drift corrections, Bug #42 sign fix can be properly evaluated
- **Files Modified**: `src/ble_manager.c:2401-2449`

**Battery Extraction Failure from Scan Response** (CRITICAL - Bug #44):
- **Symptom**: After Bug #43 fix, battery-based role assignment still failing. Logs showed "No peer battery data - falling back to discovery-based role"
- **Root Cause**: Battery Service Data was added to SCAN RESPONSE (via `ble_gap_adv_rsp_set_fields()`), but scanner only parsed ADVERTISING DATA (`event->disc.data`). Even with active scanning enabled, NimBLE stores advertising and scan response data separately. Scanner never saw battery data.
- **Evidence**:
  - Advertising: Battery added to scan response at `src/ble_manager.c:3566-3567`
  - Scanning: Only advertising data parsed at `src/ble_manager.c:3654` via `event->disc.data`
  - Result: `fields.svc_data_uuid16` always NULL, battery extraction failed
- **Fix**: Moved battery Service Data from scan response to ADVERTISING DATA (`src/ble_manager.c:3540-3583`)
  - Created `ble_update_advertising_data()` function (mirrors `ble_update_scan_response()`)
  - Battery now in advertising packet: flags (3B) + TX power (3B) + name (~12B) + battery (3B) = ~21B (fits in 31B limit)
  - UUID remains in scan response (17B) for dynamic switching (Bilateral ↔ Config)
  - Both `ble_update_advertising_data()` and `ble_update_scan_response()` called when starting advertising
- **Expected Outcome**: Scanners will now extract battery from `event->disc.data`, battery-based role assignment will work correctly
- **Files Modified**: `src/ble_manager.c:3540-3612` (new function + updated `ble_start_advertising()` + updated init)

**BLE Writes Breaking Bilateral Sync** (CRITICAL - Bug #12):
- **Symptom**: CLIENT device experienced excessive phase resets during PWA operation, causing device overlap
- **Root Cause**: Every BLE GATT write (including Session Duration) triggered `sync_settings_to_peer()`. CLIENT received `SYNC_MSG_SETTINGS` and unconditionally called `ble_callback_params_updated()`, which reset CLIENT to INACTIVE state even when no motor-timing parameters changed.
- **Fix**: Three-layer change detection defense:
  1. `ble_update_custom_freq()` only calls `update_mode5_timing()` if value actually changed (`src/ble_manager.c:3858-3882`)
  2. `ble_update_custom_duty()` only calls `update_mode5_timing()` if value changed (`src/ble_manager.c:3884-3908`)
  3. `ble_update_pwm_intensity()` only calls `motor_update_mode5_intensity()` if value changed (`src/ble_manager.c:3910-3938`)
  4. `handle_coordination_message()` SYNC_MSG_SETTINGS tracks old values, only calls `ble_callback_params_updated()` if freq/duty/intensity changed (`src/time_sync_task.c:369-444`)
- **Result**: PWA Session Duration updates no longer disrupt bilateral timing

**Frequency Change Skip/Overlap Pattern** (CRITICAL - Bug #13):
- **Symptom**: Mode 4 frequency changes via PWA caused skip-then-overlap pattern during transition
- **Root Cause**: Race condition between SYNC_MSG_SETTINGS and motor epoch beacon. CLIENT received new frequency via SYNC_MSG_SETTINGS BEFORE SERVER's beacon with updated motor_epoch arrived. CLIENT's drift correction used OLD motor_epoch with NEW cycle_ms → wrong wait calculation → skip/overlap.
- **Fix**: Added `skip_drift_correction_once` flag in CLIENT (`src/motor_task.c:112-116`):
  1. Flag set when CLIENT processes `ble_params_updated` for MODE_CUSTOM (`src/motor_task.c:624-627`)
  2. INACTIVE state checks flag, uses nominal timing instead of drift correction (`src/motor_task.c:809-813`)
  3. Flag cleared after use, normal drift correction resumes with fresh beacon
- **Result**: CLIENT uses nominal timing for one INACTIVE cycle after param change, then resumes drift correction when fresh beacon arrives with new motor_epoch

**Drift Correction Too Aggressive at High Duty Cycles** (CRITICAL - Bug #14):
- **Symptom**: At 2Hz 95% duty, perceptible drift with corrections of +198ms and -185ms causing phase jumps
- **Root Cause**: Drift correction allowed corrections up to a full cycle (500ms), but at 95% duty the inactive period is only 250ms with just 13ms coast time. Large corrections caused CLIENT to wait much longer/shorter than expected, creating visible phase drift.
- **Fix**: Added correction clamping (`src/motor_task.c:815-882`):
  1. Always apply drift correction (removed quality threshold that caused drift-then-snap behavior)
  2. Correction clamping: Max correction is ±50ms or 20% of nominal, whichever is larger
  3. Gradual correction over multiple cycles instead of single large jump
- **Result**: Continuous gradual correction keeps devices synchronized without perceptible phase jumps

**Fixed Correction Limits Not Frequency-Dependent** (Bug #29):
- **Symptom**: Mode switching at 0.5Hz with high RTT (>300ms) took 3 cycles to converge to antiphase
- **Root Cause**: Fixed 100ms max correction was only 10% of inactive period at 0.5Hz (1000ms) but 40% at 2Hz (250ms), causing inconsistent convergence behavior across frequencies
- **Fix**: Replaced fixed constants with frequency-dependent calculation (`src/motor_task.c:1467-1493`):
  - Max correction: 20% of inactive period (minimum 50ms)
  - Deadband: 10% of inactive period (minimum 25ms)
  - At 0.5Hz: 200ms max correction, 100ms deadband (was 100ms/50ms)
  - At 1.0Hz: 100ms max correction, 50ms deadband (unchanged)
  - At 2.0Hz: 50ms max correction, 25ms deadband (was 100ms/50ms, now safer)

**Lower-Battery Device Assigned Wrong Role** (CRITICAL - Bug #33):
- **Symptom**: Device with lower battery (96%) incorrectly assigned itself SERVER role instead of CLIENT
- **Root Cause**: CLIENT-waiting devices kept advertising after deciding to wait. Higher-battery device could connect TO lower-battery device, reversing BLE roles (MASTER/SLAVE) and thus reversing device roles (SERVER/CLIENT).
- **Log Evidence**: DEV_B correctly logged "Lower battery (96% < 97%) - waiting as CLIENT", but then logged "SERVER role assigned (BLE SLAVE)" when DEV_A connected to it
- **Fix**: Added `ble_gap_adv_stop()` in three CLIENT-waiting code paths (`src/ble_manager.c`):
  1. Lower battery device waiting for higher battery (line 3713-3719)
  2. Higher MAC device waiting for lower MAC (equal batteries) (line 3755-3761)
  3. Previous CLIENT waiting for previous SERVER reconnection (line 3685-3691)
- **Result**: Only the connection-initiating device (higher battery / lower MAC / previous SERVER) remains discoverable. CLIENT devices stop advertising and wait to receive connection, ensuring correct role assignment.

**Discovery Race Condition (Pairing Timeout)** (CRITICAL - Bug #34):
- **Symptom**: Both devices scanning for 30 seconds but failing to discover each other (pairing timeout)
- **Root Cause**: Both devices used identical scan parameters (10ms interval, 10ms window), causing synchronization where devices scan at exactly the same time and miss each other's advertisements
- **Log Evidence**: DEV_A scanned for full 30s but never discovered DEV_B. DEV_B discovered DEV_A at 4.3s (RSSI: -98 dBm) but DEV_A never reciprocated.
- **Fix**: Added MAC-based jitter to scan interval (`src/ble_manager.c:3892-3919`):
  - Base interval: 16 units (10ms)
  - MAC jitter: 0-15 units (0-9.375ms) based on last byte of MAC address
  - Result: Each device scans at 10-19.375ms intervals
  - Desynchronization is imperceptible to humans but prevents scan timing races
- **Result**: Devices gradually desynchronize over the 30-second pairing window, improving discovery probability. Each device logs its unique scan interval for debugging.

**BLE_HS_EDONE Logged as Error** (Bug #35):
- **Symptom**: Service and characteristic discovery logged "error; status=14" at ERROR level during normal pairing
- **Root Cause**: NimBLE uses BLE_HS_EDONE (status=14) to signal "discovery complete" - this is a normal completion status, not an error
- **Impact**: Error logs appeared during successful pairing, confusing debugging and implying failure when operations succeeded
- **Fix**: Added status check in both GATT client callbacks (`src/ble_manager.c`):
  - `gattc_on_chr_disc()`: Status 14 logged as DEBUG instead of ERROR (line 1963-1964)
  - `gattc_on_svc_disc()`: Status 14 logged as DEBUG instead of ERROR (line 2196-2197)
  - Other non-zero statuses still logged as ERROR (actual errors)
- **Result**: Clean logs during successful discovery, ERROR level reserved for actual failures

**Beacon Interval Stuck at 10 Seconds** (Bug #36):
- **Symptom**: Sync beacon interval stuck at 10s despite 100% quality score (should increase to 20s, 40s, 80s)
- **Root Cause**: SERVER's `samples_collected` initialized to 1 and never incremented. Interval backoff requires `samples_collected >= 3`, so condition always false.
- **Analysis**: Discovered by Gemini analyzing server logs showing "quality=100%" but "next_interval" stuck at 10000ms
- **Fix**: Increment SERVER's `samples_collected` on each beacon send up to `TIME_SYNC_QUALITY_WINDOW` (`src/time_sync.c:303-308`)
- **Expected Behavior After Fix**:
  - 1st beacon: 5s interval (initial)
  - 2nd beacon: 10s interval (samples_collected=2)
  - 3rd beacon: 20s interval (samples_collected=3, backoff begins)
  - 4th beacon: 40s interval
  - 5th beacon: 80s interval (max)
- **Result**: Reduced BLE overhead during long sessions (80s beacons vs 10s), improved battery life

**MAC Comparison Inverted (Equal Battery Tie-Breaker)** (CRITICAL - Bug #37):
- **Symptom**: When both devices have equal battery levels, MAC address tie-breaker made backwards decisions (lower MAC device waited as CLIENT, higher MAC device initiated as SERVER)
- **Root Cause**: BLE MAC addresses stored in reverse byte order (LSB first) in `ble_addr_t.val[]` array. Comparison loop iterated from index 0→5 (LSB to MSB), inverting the result.
- **Log Evidence**:
  - DEV_A (MAC: `b4:3a:45:89:45:de` = 0x45de lower) logged: "higher MAC - waiting as CLIENT" ❌
  - DEV_B (MAC: `b4:3a:45:89:5c:76` = 0x5c76 higher) logged: "lower MAC - initiating as SERVER" ❌
  - Result: Both devices made opposite decisions → DEV_A stopped advertising, DEV_B couldn't connect → pairing failed
- **Fix**: Reversed comparison loop to iterate from index 5→0 (MSB to LSB) (`src/ble_manager.c:3785-3796`)
- **Expected Behavior**: Lower MAC address initiates connection (SERVER/SLAVE), higher MAC address waits (CLIENT/MASTER)
- **Result**: Correct tie-breaker logic when batteries are equal

**Waiting Device Stops Advertising (Bug #33 Fix Was Incorrect)** (CRITICAL - Bug #38):
- **Symptom**: Devices failed to pair in all scenarios (battery comparison, MAC tie-breaker, reconnection). 3 boot attempts, all timed out after 30 seconds.
- **Root Cause**: Bug #33 fix incorrectly stopped advertising on connection-waiting device, preventing connection-initiating device from discovering it.
- **Log Evidence** (December 1, 2025):
  - DEV_B (96% battery, higher MAC) discovered DEV_A (97%) successfully ✅
  - DEV_B correctly identified: "Lower battery (96% < 97%) - waiting as CLIENT" ✅
  - DEV_B stopped advertising (per Bug #33 fix) ✅
  - DEV_A (97%) never discovered DEV_B ❌ (not advertising!)
  - Result: Pairing timeout after 30 seconds (3 attempts)
- **Understanding the Bug #33 Fix Mistake**:
  - Original Bug #33: Both devices calling `ble_gap_connect()` caused race condition
  - Incorrect Fix: Stop advertising on waiting device → prevents discovery ❌
  - Correct Fix: Keep advertising, but don't call `ble_gap_connect()` → discoverable but passive ✅
- **Fix**: Removed `ble_gap_adv_stop()` calls from three code paths (`src/ble_manager.c`):
  1. Lower battery device waiting (lines 3766-3769)
  2. Higher MAC device waiting (equal batteries) (lines 3803-3805)
  3. Previous CLIENT waiting for reconnection (lines 3730-3732)
- **Expected Behavior**:
  - Connection-waiting device: Keeps advertising (discoverable) + keeps scanning (doesn't call `ble_gap_connect()`)
  - Connection-initiating device: Keeps scanning + calls `ble_gap_connect()` when peer discovered
  - Result: Only ONE device calls `ble_gap_connect()`, preventing race condition while maintaining discoverability
- **Result**: Pairing should succeed within 5-10 seconds

**64-bit Timestamp Logging Corruption** (CRITICAL - Bug #30):
- **Symptom**: "Handshake complete" logs showed timestamps (T1-T4) that didn't mathematically match the calculated offset/RTT values. Example: Log showed RTT=1320μs, but timestamps calculated to RTT=59540μs (45× difference!)
- **Root Cause**: Using non-portable format specifiers (`%lld`/`%llu`) for 64-bit integers on RISC-V architecture. ESP-IDF requires `PRId64`/`PRIu64` macros from `<inttypes.h>` for correct printf parsing on 32-bit systems with 64-bit values.
- **Fix**: Added `#include <inttypes.h>` and replaced all format specifiers (`src/time_sync.c`):
  - `%lld` → `%" PRId64 "` for int64_t (offset, drift, signed timestamps)
  - `%llu` → `%" PRIu64 "` for uint64_t (T1-T4 timestamps, motor epoch)
  - Fixed 15 logging statements across handshake, beacon, RTT, and drift tracking
- **Result**: Timestamp values in logs now correctly match calculated offset/RTT values, enabling accurate verification of synchronization math
- **Impact**: Critical for debugging - impossible to verify time sync correctness when logged timestamps were corrupted
- **Discovery**: Gemini's 90-minute log analysis identified the mathematical inconsistency (see GEMINI.md)

**BLE GATT Discovery BUSY Errors** (Bug #31):
- **Symptom**: "Service discovery error; status=14" and "Characteristic discovery error; status=14" during pairing (status 14 = BLE_HS_EBUSY)
- **Root Cause**: CLIENT tried to start Configuration Service characteristic discovery from within the Bilateral Service discovery completion callback. NimBLE stack was still processing the completion event, causing BLE_HS_EBUSY when starting new discovery.
- **Fix**: Deferred Configuration Service discovery using esp_timer (`src/ble_manager.c`):
  - Added `g_deferred_discovery_timer` to defer discovery by 50ms
  - Created `deferred_discovery_timer_cb()` to start Config Service discovery after Bilateral completes
  - Modified `gattc_on_chr_disc()` to schedule timer instead of immediate discovery call
  - Timer and state cleanup in disconnect handler
- **Result**: Eliminates BUSY errors, cleaner logs, potentially 10-50ms faster pairing (avoids retry overhead)
- **Impact**: Non-functional fix (errors were non-fatal), but improves code quality and debugging experience

**Motor Overlap After Mode Changes - Stale Epoch Prediction** (CRITICAL - Bug #32):
- **Symptom**: 91ms-127ms motor activation overlap after multiple mode changes during active session (Gemini analysis: `GEMINI.md`)
- **Timeline**: Device B (CLIENT): 16:18:36.498-36.922 (424ms), Device A (SERVER): 16:18:36.795-37.213 (418ms), overlap 16:18:36.795-36.922 = 127ms
- **Root Cause**: CLIENT only received motor epoch ONCE at session start via `SYNC_MSG_MOTOR_STARTED`. When user changed modes (2000ms → 1000ms → 667ms → 500ms → 1000ms), SERVER set new epoch locally but never sent it to CLIENT. CLIENT continued predicting epoch using stale cycle time, causing 8.13-second drift after ~60 seconds.
- **Evidence**: CLIENT log showed `epoch=57669660` while SERVER actual epoch was `65798967` (8,129,307 μs difference)
- **Fix**: Send `SYNC_MSG_MOTOR_STARTED` to CLIENT after every mode/frequency change (`src/motor_task.c`):
  1. After button-triggered mode change on SERVER (lines 961-976)
  2. After BLE-triggered frequency change in MODE_CUSTOM (lines 1053-1067)
  3. CLIENT already receives and processes `SYNC_MSG_MOTOR_STARTED` correctly (handled since Phase 6)
- **Result**: CLIENT epoch updates immediately on every mode/frequency change, eliminating prediction drift
- **Impact**: Prevents motor overlap during multi-mode therapy sessions (0.5Hz → 1Hz → 1.5Hz → 2Hz sequences)
- **Discovery**: Gemini's bilateral timing overlap analysis (November 30, 2025) - see updated `GEMINI.md`

**Quality Metrics Stuck at 0% - Handshake Race Condition** (CRITICAL - Bug #28):
- **Symptom**: Quality metrics always showed 0%, RTT updates never improved quality score
- **Root Cause**: TIME_REQUEST arrived 840-1040ms before SERVER time_sync initialization completed, SERVER rejected with `ESP_ERR_INVALID_STATE`, CLIENT never retried, fell back to beacon path which didn't initialize quality metrics
- **Fix**: Implemented TIME_REQUEST buffering (matching existing CLIENT_READY pattern):
  1. Buffer TIME_REQUEST if time_sync not initialized (`src/time_sync_task.c:574-580`)
  2. Process buffered request after initialization complete (`src/time_sync_task.c:300-337`)
  3. Fallback: Initialize quality metrics from beacon if handshake missed (`src/time_sync.c:511-517`)
  4. Fixed drift_rate variable scoping issue for logging (`src/time_sync.c:1432`)
- **Result**: Handshake completes successfully (quality=95%), RTT updates properly track sync quality
- **Files Modified**: `src/time_sync_task.c` (buffering), `src/time_sync.c` (beacon fallback)

### Added - Phase 6r: Drift Continuation During Disconnect (November 30, 2025)

**Conditional Clearing for Motor Continuation:**
- **Modified Disconnect Handler** (`src/time_sync.c:174-217`): Preserves motor_epoch and drift_rate when BLE disconnects
- **Safety Timeout** (`src/time_sync.c:935-958`): Motor epoch expires after 2-minute disconnect, returns `ESP_ERR_TIMEOUT`
- **Role Swap Detection** (`src/time_sync.c:219-278`): New `time_sync_on_reconnection()` detects role changes on reconnection
- **BLE Integration** (`src/ble_manager.c:2121-2128`): Calls reconnection handler after role assignment
- **Documentation** (`src/motor_task.c:21-28`, `README.md`): Phase 6r section explaining drift continuation behavior

**Key Behavior Changes:**
- ✅ **CLIENT motors continue** during brief BLE disconnect (< 2 min) using frozen drift rate
- ✅ **Bilateral alternation maintained** with ±2.4ms drift over 20-minute session (well within ±100ms spec)
- ✅ **Therapeutic continuity** preserved during BLE glitches
- ⏱️ **Safety timeout** stops motors gracefully after 2-minute disconnect
- ⚠️ **Role swap warning** logged if roles change on reconnection (indicates Phase 6n bug)

**Technical Rationale:**
- Original Phase 6 bug was about role SWAP corruption during reconnection (not disconnect continuation)
- Drift rate stability from Phase 2 testing (±30 μs over 90 min) validates continuation approach
- Conditional clearing: Preserve during disconnect, clear only on role swap
- Aligns with AD041 (predictive bilateral synchronization philosophy)

### Documentation

- CLAUDE.md: Added Phase 6r section with complete implementation details
- README.md: Updated to v0.3.0-beta.2, added "Typical Bilateral Operation Flow" section
- CLAUDE.md: Added Branch and PR Workflow section (mandatory changelog updates and version bumps before PRs)

### Planned
- Phase 6r: Hardware testing (brief disconnect, long disconnect, role swap scenarios)
- Phase 6: Complete bilateral motor coordination testing
- Mobile app development
- Enhanced pairing with numeric comparison and button confirmation

---

## [0.3.0-beta.1] - 2025-11-20

### Added - Phase 2: Time Synchronization Complete ✅

**Time Synchronization Implementation:**
- **NTP-Style Clock Sync**: Dual-clock architecture preserving system clock while calculating synchronized time (`src/time_sync.c`, `src/time_sync.h`, `src/time_sync_task.c`, `src/time_sync_task.h`)
- **Beacon Exchange Protocol**: Timestamped messages exchanged every 10-60 seconds (adaptive based on quality)
- **Quality Metrics**: Confidence score (0-100%) based on round-trip time and drift stability
- **One-Time Phase Alignment**: Single synchronization at session start (drift < 30 μs over 90 minutes - periodic re-sync unnecessary)
- **Opt-In Synchronization**: Applications choose sync clock (`time_sync_get_time_us()`) vs system clock (`esp_timer_get_time()`)
- **Sequence Wrap Handling**: Beacon counter (uint8_t) wraps correctly at 255→0

**Architecture Decisions:**
- **AD037**: Time Synchronization Protocol (NTP-style beacon exchange)
- **AD038**: Synchronized vs System Clock Usage (dual-clock architecture)
- **AD039**: Time Synchronization Protocol Details (beacon format, quality metrics)
- **AD040**: Firmware Version Checking (semantic versioning comparison)

**Production Readiness:**
- 90-minute unattended stress test PASSED:
  - 271/271 beacons delivered (100% delivery rate)
  - Drift converged to -14 μs, stable at -31 μs final
  - Quality sustained at 95%
  - 7 brief 50ms offset jumps (suspected BLE connection parameter updates, not time sync bugs)
  - Recovery: Quality→0% detected, recovered within 2 beacons
  - Sequence wrap verified (255→0 transition handled correctly)

### Fixed

**NVS Configuration Standardization:**
- Replaced custom `BLE_PAIRING_TEST_MODE` flag with standard ESP-IDF `CONFIG_BT_NIMBLE_NVS_PERSIST` (`sdkconfig.xiao_esp32c6:715`, `src/ble_manager.c:2453-2466`, `platformio.ini:485,495,499`)
- Production environment: `CONFIG_BT_NIMBLE_NVS_PERSIST=y` enables persistent bonding across reboots
- Test environment: `CONFIG_BT_NIMBLE_NVS_PERSIST` not set for RAM-only bonding (unlimited pairing cycles)
- Test binary now 1,738 bytes smaller (NVS backend not compiled)
- Better compatibility with developers familiar with NimBLE stack conventions

**Pairing Race Condition** (CRITICAL - Bug #35):
- **Symptom**: DEV_A (98% battery) never discovered DEV_B (96% battery), both timed out after 30 seconds
- **Root Cause**: Scanning stopped immediately after peer discovery, BEFORE role assignment. CLIENT devices would stop scanning, then wait for connection, but SERVER couldn't discover them.
- **Fix**: CLIENT devices now keep scanning during wait period. Moved `ble_gap_disc_cancel()` to only execute when device initiates connection (SERVER role). Applied same pattern to MAC tie-breaker and fallback cases. (`src/ble_manager.c:2658-2674`)
- **Result**: Robust pairing regardless of power-on timing

**PWA Connection Tracking** (CRITICAL - Bug #36):
- **Symptom**: Windows PC PWA connected (MTU exchange visible) but no "Mobile app connected" log. Device became invisible after disconnect. Android PWA worked correctly.
- **Root Cause**: "Keep scanning" fix caused CLIENT device to attempt connections to discovered devices while also accepting incoming connections, creating interference.
- **Fix**: Stop scanning immediately when peer connects (unconditional call). Added BLE_HS_EINVAL handling for cases where scanning already stopped. Updated comments to reference Bug #36. (`src/ble_manager.c:1613-1626`)
- **Result**: All BLE central devices work correctly (Android PWA, Windows PC PWA, nRF Connect)

### Infrastructure

- Message queue added: `time_sync_to_motor_queue` for coordination messages (MSG_PHASE_ALIGNMENT, MSG_DRIFT_UPDATE)
- Task added: `time_sync_task` managing beacon exchange and quality monitoring
- Module added: `time_sync.c/h` with dual-clock calculation functions
- API documentation: `docs/AD038_TIME_SYNCHRONIZATION_API.md` (planned API examples)

### Documentation

- CLAUDE.md updated with Phase 2 summary and test results
- Architecture decisions migrated to docs/adr/ (AD037-AD040 added as individual files)
- PHASE3_COMMAND_CONTROL_IDEAS.md created for Phase 3 planning

### Known Issues (Non-Blocking)

**50ms Timing Jumps** (Under Investigation):
- 7 brief 50ms offset jumps over 90 minutes (suspected BLE connection parameter updates)
- Time sync correctly detects (quality→0%) and recovers within 2 beacons
- Impact: Negligible for 20-minute therapy sessions
- Decision: Not blocking Phase 2 completion; will investigate if Phase 3 motor coordination affected

---

## [0.2.0-beta.1] - 2025-11-19

### Added - Phase 1c: Battery-Based Role Assignment
- **AD035 Implementation**: Battery-based role assignment via BLE Service Data (0x16). Devices broadcast battery percentage in scan response during peer discovery window (0-30s). Higher battery device initiates connection (SERVER/MASTER role), lower battery device waits (CLIENT/SLAVE role). MAC address tie-breaker for equal batteries. Eliminates race condition for deterministic role assignment. (`src/ble_manager.c:2114-2153, 2256-2319, 2547-2572`)
- **Dynamic Battery Updates**: Advertising restarts when battery changes during peer discovery window, ensuring accurate role assignment data. Falls back to discovery-based role if no battery data available.

### Fixed
- **GPIO15 Status LED Stuck ON** (Bug #34): After peer pairing completes, motor_task takes WS2812B ownership which disables status_led pattern control. GPIO15 was left ON from pairing patterns, blocking all future status LED blinks. Fixed by explicitly calling `status_led_off()` after pairing success/failure patterns complete, before motor takes ownership. (`src/ble_task.c:251-252, 301-302`)

### Fixed (Phase 1b.3 Continued)
- **Button Unresponsiveness** (CRITICAL - Bug #28): Rapid button presses (5+ in 1 second) caused firmware hang requiring battery disconnect to recover. Root cause: Blocking `status_led_pattern()` calls in button state machine (50ms for mode change, 500ms for BLE re-enable). Multiple rapid presses accumulated blocking delays (5 presses = 250ms blocked), preventing button GPIO reads and causing state machine to enter unexpected states. Fixed by replacing blocking LED patterns with non-blocking `status_led_on()` (~10ms brief pulse). Button task now remains responsive to rapid inputs. (`src/button_task.c:148, 185`)

### Changed
- **Phase Naming Clarification**: Renamed "Phase 4" to "Phase 0.4" throughout documentation to avoid confusion with planned Phase 2 and Phase 3. Phase 0.4 represents JPL-compliant single-device testing foundation, parallel to Phase 1's dual-device work. (`CLAUDE.md`, `README.md`, documentation files)
- **Documentation Updates**: Updated README.md with current Phase 1c completion status. Fixed outdated button controls (wake from sleep, factory reset timing), removed obsolete LED patterns, clarified 1-2s button hold is for mobile app connection only (SERVER role).

### Changed (Phase 1b.3 Continued)
- **UUID-Switching Strategy**: Implemented time-based UUID switching for peer/app identification (Phase 1b.3 architecture). Devices advertise Bilateral Service UUID (`...0100`) for first 30 seconds (peer discovery only), then switch to Configuration Service UUID (`...0200`) for app discovery. Bonded peers reconnect by cached address via Config UUID (allowed anytime). Eliminates complex state-based connection identification and **completely eliminates Bug #27** (PWA misidentification) at BLE discovery level - mobile apps physically cannot discover device during Bilateral UUID window. (`src/ble_manager.c:140-161, 1696-1712, 1807-1821, 2184-2197`, `src/ble_task.c:114-127`)
- **Connection Identification Simplified**: Replaced complex 4-path state machine (cached address, BLE role, scanning state, grace period) with simple 2-case UUID check. If advertising Bilateral UUID → connection is peer. If advertising Config UUID → check cached peer address, otherwise mobile app. Reduced connection identification code from ~60 lines to ~30 lines (50% reduction). Zero misidentification risk - connection type determined by which UUID device is advertising when connection arrives. (`src/ble_manager.c:1277-1307`)
- **Pairing Window Enforcement**: Reduced effective pairing window from 38 seconds (30s + 8s grace period) to strict 30 seconds via UUID-switching. Grace period no longer needed - UUID automatically switches at 30s boundary. Clearer user experience and simpler implementation.
- **Security Model Updated**: Security section simplified to reflect UUID-switching enforcement. Bilateral UUID (0-30s) allows unbonded peer connections (initial pairing). Config UUID (30s+) only allows bonded peer reconnections (unbonded connections identified as mobile apps). Security check now only prevents multiple simultaneous peer connections. (`src/ble_manager.c:1310-1329`)

---

## [0.1.3] - 2025-11-15

### Added - Phase 1b.3: BLE Bonding/Pairing Security
- **BLE Pairing Support**: Just-Works pairing implementation with LE Secure Connections (ECDH key exchange)
- **Bonding with NVS Storage**: Long-term key storage for persistent pairing across power cycles (production mode)
- **Pairing State Machines**: 5-state BLE task (added BLE_STATE_PAIRING) and 9-state motor task (added MOTOR_STATE_PAIRING_WAIT)
- **Session Timer After Pairing**: Session timer initialization deferred until after successful pairing for accurate session duration tracking
- **Message Queue Architecture**: Added `ble_to_motor_queue` for pairing status communication (MSG_PAIRING_COMPLETE, MSG_PAIRING_FAILED)
- **Pairing Test Mode**: `BLE_PAIRING_TEST_MODE` build flag for RAM-only bonding (prevents NVS flash wear during development testing)
- **30-Second Pairing Timeout**: JPL-compliant bounded timeout with progress logging every 5 seconds
- **Pairing LED Patterns**: Full WS2812B RGB integration for pairing feedback
  - **Waiting**: GPIO15 solid ON + WS2812B purple solid (palette index 7)
  - **Progress**: GPIO15 pulsing 1Hz + WS2812B purple pulsing (500ms ON/OFF)
  - **Success**: GPIO15 OFF + WS2812B green 3× blink (250ms each)
  - **Failed**: GPIO15 OFF + WS2812B red 3× blink (250ms each)
- **Graceful Pairing Timeout**: Automatic connection termination and cleanup if pairing exceeds 30 seconds

### Fixed (Phase 1b.3)
- **motor_on_ms Constraint Mismatch** (CRITICAL - Bug #18): AD032 specified 0.25-2.0Hz frequency range but motor_on_ms limit was 500ms (only supported ≥0.5Hz). At 0.40Hz with 25% duty, calculation yielded 625ms (rejected). At 0.39Hz, calculation yielded 641ms (rejected). Root cause: Original 500ms limit designed for preset modes (0.5-1Hz), not research platform's full range. Fixed by increasing motor_on_ms limit from 500ms to 1250ms (supports 0.25Hz @ 50% duty = full AD032 range). Also increased coast_ms from 2000ms to 4000ms for low-frequency support. (`motor_task.c:677-683`)
- **Pairing Window Security Blocking App Connections** (CRITICAL - Bug #19): Pairing window security check rejected ALL unbonded connections (peer AND app) before determining connection type. This caused asymmetric pairing failures where one device would pair successfully while the other rejected the connection. Symptom: After mobile app connection attempt, peer devices could no longer pair (one device thinks paired, other shows timeout). Root cause: Security check occurred before connection type determination in BLE_GAP_EVENT_CONNECT handler. Fixed by restructuring connection handler to determine connection type FIRST (peer vs app), then apply connection-type-specific security rules: PEER connections blocked outside 30s pairing window unless bonded, APP connections allowed anytime (no pairing requirement). (`ble_manager.c:1237-1390`)
- **Bilateral Motor Offset Timing Error** (Bug #20): CLIENT device started motor 250ms too early (1/4 cycle offset error) in bilateral mode. For 1.0Hz bilateral (1000ms cycle), CLIENT should wait 500ms (half cycle) but was waiting 750ms (coast_ms from ACTIVE/INACTIVE timing). This worked by accident at 50% duty (natural gaps prevented overlap) but would fail at higher duty cycles. Root cause: CLIENT offset used coast_ms instead of calculating proper bilateral half-cycle offset. Fixed by calculating bilateral_cycle_ms (motor_on_ms + coast_ms) and using bilateral_cycle_ms / 2 for CLIENT initial INACTIVE wait. Ensures true alternation: DEV_A [250ms ON | 750ms OFF], DEV_B [500ms OFF | 250ms ON | 250ms OFF] for 1.0Hz@50%. (`motor_task.c:318-327`)
- **Peer Misidentification - App Identified as Peer** (CRITICAL - Bug #21): Mobile app connections were misidentified as peer device connections, causing incorrect handling and state corruption. Symptom: When mobile app connected to device waiting for peer, app was identified as peer, triggering peer connection logic. When app disconnected, code thought peer disconnected and tried to restart advertising (which was already running), causing advertising state desync. Root cause: Connection handler used overly broad heuristic "scanning_active → must be peer" without checking WHO initiated the connection. Fixed by checking BLE connection role: if WE initiated connection (BLE_GAP_ROLE_MASTER), it's a peer (we only connect to discovered peers). If THEY initiated connection (BLE_GAP_ROLE_SLAVE), it's an app (unless cached peer address matches). (`ble_manager.c:1261-1283`)
- **Advertising State Desync** (Bug #22): BLE_TASK reported "advertising=NO" but device was actually advertising (mobile app could connect). Root cause: When advertising restart failed with BLE_HS_EALREADY (error code 2 = already advertising), code incorrectly set `advertising_active = false`. This happened because Bug #21 caused app disconnects to be handled as peer disconnects, which tried to restart advertising that was already running. Fixed by syncing flag with actual NimBLE state on error: `advertising_active = ble_gap_adv_active()` instead of blindly setting false. Applied to all advertising restart error paths. (`ble_manager.c:1369, 1463, 1491`)
- **Pairing Window Not Enforced for Peer Discovery** (Bug #23): New peer connections could be initiated during active session if BLE scanning was restarted. Symptom: DEV_A in active session (motors running) could discover and connect to newly-powered DEV_B, interrupting session. Root cause: Scan callback (BLE_GAP_EVENT_DISC) checked for duplicate peer connections but not for pairing window expiry. Fixed by adding 30-second pairing window check to scan callback - peers discovered outside pairing window are ignored. (`ble_manager.c:2101-2106`)
- **Asymmetric Pairing Failure - Incoming Peer Connections Misidentified** (CRITICAL - Bug #24): Bug #21 fix was incomplete - only handled outgoing connections (BLE MASTER). When DEV_A (BLE SLAVE) received incoming connection from DEV_B (BLE MASTER), it had no cached peer address and was misidentified as app connection. Symptom: One device successfully pairs while other device times out and continues in single-device mode. DEV_A logs show "Mobile app connected" when DEV_B connects. Root cause: Peer identification logic didn't account for incoming connections during pairing window. Fixed by adding Case 3: if device is BLE SLAVE (they initiated) AND scanning_active=true (in pairing window), it's a peer connection. This completes the peer identification logic for all connection scenarios: outgoing (BLE MASTER), incoming during pairing (BLE SLAVE + scanning), incoming after pairing (app), and bonded reconnections (cached address). (`ble_manager.c:1279-1285`)
- **SERVER Advertising Restart Timing Race** (Bug #25): Intermittent failure where SERVER device wouldn't advertise for mobile app connections after peer pairing. Symptom: Sometimes mobile app could connect after peer pairing, sometimes not (intermittent on battery-powered boots). Root cause: BLE_MANAGER tried to restart advertising immediately after peer connection (20ms), NimBLE controller not ready yet, rejected with BLE_HS_ECONTROLLER error (rc=6). When restart failed, advertising never started and BLE_TASK eventually detected "advertising stopped externally" and went to IDLE. Fixed by removing immediate advertising restart from BLE_MANAGER connection handler and moving it to BLE_TASK PAIRING → ADVERTISING transition (~4s later). This gives NimBLE controller time to fully establish connection before advertising restart. Only SERVER devices restart advertising (CLIENT devices don't advertise after peer pairing). (`ble_manager.c:1355-1375`, `ble_task.c:248-259`)
- **Pairing Timeout Race - Late Peer Connections Misidentified** (CRITICAL - Bug #26): Asymmetric pairing when devices started at different times. Symptom: DEV_A starts first, times out after 30s, continues as single-device. DEV_B starts ~27s later, discovers DEV_A, connects at 36s (DEV_A time). DEV_A receives connection AFTER timeout, identifies as "App" instead of "Peer" because scanning_active=false. Result: DEV_A runs single-device mode, DEV_B runs bilateral CLIENT mode (one device thinks pairing succeeded, other doesn't). Root cause: Case 3 peer identification only checked scanning_active flag (true during active scan). After pairing timeout, scanning stops and flag=false, so late peer connections fall through to "app" case. Fixed by adding Case 3b: Check 38-second grace period (30s pairing + 8s grace) AND no peer connected yet. Grace period duration accounts for BLE connection establishment (1-5s typical) plus margin for devices discovered just before 30s timeout. Connections arriving within grace period (when waiting for FIRST peer) are identified as peers even if scanning stopped. Once peer connects, grace period no longer applies (prevents app misidentification). This handles devices started up to ~25 seconds apart. (`ble_manager.c:1287-1305`)
- **PWA Misidentified as Peer When Scanning Active After Peer Pairing** (CRITICAL - Bug #27): Mobile app (PWA/native) connections rejected with "Rejecting unbonded PEER outside 30s pairing window" error. Symptom: At 66s after boot, PWA connection identified as peer instead of app, then rejected by security check. Device showed "BLE: Peer (SERVER)" at 61s (peer already connected), but PWA at 66s still identified as peer. Root cause: Case 3a peer identification checked only `scanning_active` flag without checking if peer was already connected. After peer pairing, scanning may restart for peer rediscovery (after peer disconnect), causing PWA connections to be misidentified as peers. Fixed by adding `!peer_state.peer_connected` check to Case 3a: if peer already connected, incoming connections during scanning are apps (not peers). Also added error handling for `ble_gap_disc_cancel()` to log failures. This aligns with industry best practices for state-based connection type identification (no BLE standard exists for this, confirmed via research into Nordic/Espressif/BLE Mesh implementations). (`ble_manager.c:1279-1294`, `ble_manager.c:1350-1359`)
- **Bilateral Frequency Definition Ambiguity**: Updated comments to clarify that mode frequencies (0.5Hz, 1.0Hz, 1.5Hz, 2.0Hz) refer to BILATERAL alternation rate (one complete left-right alternation per second) not per-device frequency. Example: "1.0Hz" in dual-device mode means DEV_A active while DEV_B inactive, then vice versa, completing 1 full bilateral cycle per second. In single-device mode, same frequency with alternating motor directions. This aligns with EMDR therapeutic standards requiring bilateral stimulation. (`motor_task.c:47-60`, `motor_task.h:50-67`)

### Architecture Decisions
- **AD036**: BLE Bonding/Pairing Security Architecture - Just-Works pairing with LE Secure Connections, conditional NVS storage

### Infrastructure
- New build environment: `xiao_esp32c6_ble_no_nvs` for BLE testing (RAM-only bonding)
  - **NVS Write Prevention**: `store_status_cb = NULL` in test mode prevents flash writes during pairing tests
  - Bonding data stored in RAM only, cleared on reboot (prevents flash wear during development)
  - Production mode: `store_status_cb = ble_store_util_status_rr` enables NVS persistence
- BLE task expanded from 4 to 5 states with pairing lifecycle management
- Motor task expanded from 8 to 9 states with pairing wait state
- Message queue count increased from 3 to 4 (added ble_to_motor_queue)

### Implementation Notes
- **Simplified from Initial Plan**: Originally planned numeric comparison with button confirmation, implemented as Just-Works pairing for faster development
- **NimBLE API Corrections**: Used `BLE_GAP_EVENT_ENC_CHANGE` for pairing detection instead of separate security manager callback
- **Session Timer Lifecycle**: Moved from main.c initialization to motor task (starts only after pairing completes)

### Documentation
- BUILD_COMMANDS.md updated with pairing test environment commands across all shell environments (bash, PowerShell, cmd)
- AD036 created in architecture_decisions.md

---

## [0.1.2] - 2025-11-14

### Added - Phase 1b: Peer Discovery and Initial Role Assignment
- **Peer-to-Peer Discovery**: Devices discover and connect to each other via BLE scanning (~1-2s connection time)
- **Connection Type Identification**: `ble_is_peer_connected()` and `ble_get_connection_type_str()` differentiate peer vs mobile app connections
- **Battery Exchange**: Bilateral Battery characteristic updates every 60 seconds for role assignment foundation
- **Race Condition Handling**: Graceful handling of ACL_CONN_EXISTS error (523) when both devices connect simultaneously (AD010)
- **Project-Specific UUIDs**: Changed from Nordic UART Service to custom UUID base `4BCAE9BE-9829-...` to prevent collision (AD032)
- **Battery Status Logging**: Motor task now logs connection type: `Battery: 4.18V [98%] | BLE: Peer/App/Disconnected`

### Architecture Decisions
- **AD035**: Battery-Based Initial Role Assignment strategy (higher battery = SERVER role)
- **AD010**: Updated Race Condition Prevention Strategy with Phase 1b simultaneous connection handling
- **AD028**: Updated Command-and-Control Architecture with Phase 1b implementation status
- **AD030**: Updated Bilateral Control Service with Phase 1b battery characteristic implementation

### Fixed (Phase 1b.1)
- **Mobile App Cannot Connect When Peer-Paired** (RESOLVED): Increased `CONFIG_BT_NIMBLE_MAX_CONNECTIONS` from 1 to 2, allowing SERVER to accept both peer and mobile app connections simultaneously

### Fixed (Phase 1b.2)
- **Advertising Timeout Disconnects Peer** (CRITICAL - Bug #7): Role-aware advertising implemented (`ble_manager.c:1136-1155`). CLIENT (connection initiator) stops advertising to prevent 5-minute timeout. SERVER (connection receiver) keeps advertising for mobile app access. Fixes peer timeout disconnect while enabling mobile app connection during peer pairing.
- **Peer Reconnection Broken** (CRITICAL - Bug #8): Fixed peer disconnect handler to explicitly restart both advertising and scanning for peer rediscovery (`ble_manager.c:1186-1214`). Previous code relied on `advertising_active` flag which was set to false by Bug #7 fix, preventing reconnection after peer disconnect.
- **PWA Cannot Discover Device** (Bug #9): Web Bluetooth PWAs filter by Configuration Service UUID but device was only advertising Bilateral Service UUID. Now advertising Configuration Service UUID (`...0200`) in scan response (`ble_manager.c:1385`). Peer discovery updated to use Configuration Service UUID instead of Bilateral Service UUID (`ble_manager.c:1708`) - simpler single-UUID approach works for both peer discovery and PWA filtering.
- **Both Devices Think They're CLIENT** (CRITICAL - Bug #10): When both devices scan simultaneously, both set `peer_discovered = true` upon discovery. Role detection logic incorrectly used this flag to determine connection initiator, causing both to think they initiated (CLIENT role). Fixed by using NimBLE's actual connection role (`desc.role == BLE_GAP_ROLE_MASTER` = CLIENT, `BLE_GAP_ROLE_SLAVE` = SERVER) instead of discovery flag (`ble_manager.c:1150-1166`). SERVER now correctly keeps advertising for mobile app access.
- **SERVER Advertising Not Visible After Peer Connection** (CRITICAL - Bug #11): SERVER logged "Keeping advertising active" after peer connection but was invisible to BLE scanners. Root cause: NimBLE automatically stops advertising when ANY connection is established (standard BLE behavior). The code logged "keeping advertising active" but didn't actually restart it. Fixed by explicitly restarting advertising after peer connection for SERVER role (`ble_manager.c:1176-1185`). Also enabled `CONFIG_BT_NIMBLE_HOST_ALLOW_CONNECT_WITH_SCAN` to allow incoming connections while scanning (`sdkconfig.xiao_esp32c6:843`).
- **Race Condition Warning on PWA Disconnect** (JPL Compliance - Bug #12): BLE task logged "Advertising did not restart after disconnect" warning due to race condition - it checked advertising status before disconnect handler completed restart (~80ms). Violated JPL requirement for deterministic behavior. Fixed by adding 150ms deterministic delay before checking advertising status (`ble_task.c:175-178`). Warning now only appears if advertising genuinely fails to restart.
- **Slow Peer Reconnection After Disconnect** (Bug #13): Peer reconnection took ~1 minute vs ~2 seconds for initial connection. Root cause: NimBLE needs time to clean up connection handle after disconnect. Immediate retry (2s after disconnect) caused `BLE_ERR_UNK_CONN_ID` errors. Fixed by increasing peer disconnect delay from 100ms to 2 seconds (`ble_manager.c:1361-1366`). Allows NimBLE to fully clean up before reconnection attempt, achieving fast reconnection similar to initial discovery.
- **Peer Misidentified as Mobile App After Reconnect** (CRITICAL - Bug #14): When one device shut down and restarted, the other device misidentified the peer as "Mobile app connected" instead of "Peer device connected". Root cause: Connection detection logic required both `peer_discovered` flag AND address match, but flag was cleared on disconnect while address remained cached. Fixed by checking cached peer address first without requiring `peer_discovered` flag (`ble_manager.c:1228-1234`). Peer now correctly identified on reconnection using cached MAC address.
- **No Graceful BLE Disconnect on Shutdown** (CRITICAL - Bug #15): Emergency shutdown (5s button hold) did not disconnect BLE connections before entering deep sleep. Peer device experienced connection timeout (0x08) instead of clean disconnect. Fixed by adding explicit `ble_gap_terminate()` calls for both peer and mobile app connections in BLE task shutdown handler (`ble_task.c:162-181`). Connections now terminate gracefully with "Remote Device Terminated by Local Host" (0x16) before deep sleep.
- **Role Not Assigned When Advertising Inactive** (CRITICAL - Bug #16): Battery logs showed "BLE: Peer" without CLIENT/SERVER role designation. Root cause: Role assignment at `ble_manager.c:1272` only executed inside `if (adv_state.advertising_active)` check. If advertising stopped before peer connection established, role never assigned (`peer_state.role` remained `PEER_ROLE_NONE`). Fixed by moving role assignment outside advertising check (`ble_manager.c:1268-1280`). Role now always assigned based on NimBLE's `desc.role` regardless of advertising state.
- **Device Names Not Unique** (CRITICAL - Bug #17): Both devices advertised as "EMDR_Pulser_406400" instead of unique names with actual MAC address. Root cause: `ble_hs_id_infer_auto()` at line 1542 returns address **type** (public vs random), not address **bytes**. This returned garbage data instead of actual MAC address. Fixed by using correct API `ble_hs_id_copy_addr(BLE_ADDR_PUBLIC, addr_val, NULL)` (`ble_manager.c:1540-1555`). Devices now show unique names like "EMDR_Pulser_8945DE" and "EMDR_Pulser_8A46E1" based on actual MAC addresses. Also added full MAC address logging for diagnostics.

### JPL Power of Ten Compliance (November 15, 2025)
- **Unbounded Mutex Waits Eliminated** (CRITICAL - JPL Rule #6): All 69 instances of `portMAX_DELAY` in mutex operations replaced with 100ms bounded timeouts. Affects `motor_control.c` (5), `role_manager.c` (17), and `ble_manager.c` (47). Each timeout includes error handling: functions returning `esp_err_t` return `ESP_ERR_TIMEOUT`, getters return safe defaults, void functions return early. Prevents permanent hangs if mutex holder crashes.
- **Infinite Error Loops Eliminated** (WARNING - JPL Rule #2): Replaced 3 infinite `while(1)` loops in `main.c` error handlers with `esp_deep_sleep_start()`. Allows button-wake recovery instead of permanent system hang when hardware init, queue creation, or task creation fails.
- **User-Bounded Wait Exception** (Accepted): Button release wait after NVS factory reset (`button_task.c:270`) intentionally kept unbounded - this is a user-driven shutdown operation where wait is bounded by human action, not system automation. Watchdog is fed during wait to prevent timeout.

**JPL Compliance Status:** ✅ ACHIEVED
- Rule #1 (No dynamic allocation): ✅ PASS
- Rule #2 (Fixed loop bounds): ✅ PASS
- Rule #3 (No recursion): ✅ PASS
- Rule #4 (No goto): ✅ PASS
- Rule #5 (Check return values): ✅ PASS
- Rule #6 (No unbounded waits): ✅ PASS (all violations eliminated)
- Rule #7 (Watchdog compliance): ✅ PASS
- Rule #8 (Defensive logging): ✅ PASS

### Known Issues
- **Advertising Timeout Not Enforced** (Low Priority): 5-minute advertising timeout doesn't trigger when no mobile app connects. Advertising continues indefinitely instead of transitioning to IDLE. Does not affect functionality when peer is connected or when mobile app connects successfully. Deferred to future milestone.
- **Advertising Timer Loop** (Possibly RESOLVED by Bug #8 fix): Previous rapid IDLE→ADVERTISING→timeout loop after disconnect may be resolved by peer reconnection fix. Requires hardware testing to confirm.
- **Status LED 5× Blink Not Visible**: Function called on peer connection but LED doesn't blink (hardware confirmed functional)
- **Battery Calibration Needed** (Planned Phase 1c): Fully charged batteries don't reach 100% (~95-98% observed) due to 1S2P configuration, P-MOSFET losses, and battery wear. Requires USB detection (5V pin) and automatic calibration routine.

### Hardware Reliability Notes
- **Motor Connection Intermittency**: One device experienced intermittent motor operation progressing to complete failure during testing. Recommendations:
  - Verify solder joint quality on motor wire connections
  - Check for wire flex fatigue at solder points (motor wires subject to vibration)
  - Consider strain relief for motor wires in future enclosure design
  - Inspect motor solder pads for cold joints or cracked solder

### Infrastructure
- Modular architecture in `src/` (ble_manager, motor_task, ble_task, button_task)
- Build environment: `xiao_esp32c6`
- Dual battery characteristic updates (Configuration Service + Bilateral Control Service)

### Documentation
- Phase 1b section added to CLAUDE.md with implementation details and testing evidence
- architecture_decisions.md updated with Phase 1b status in AD010, AD028, AD030
- AD035 created documenting battery-based role assignment strategy

---

## [0.1.1] - 2025-11-13

### Fixed
- **LED_COUNT constant**: Corrected from 2 to 1 in [led_control.h](src/led_control.h) to match actual hardware (1 WS2812B per device)
- **Frequency range documentation**: Updated from 0.5-2 Hz to 0.25-2 Hz research platform range in README and related docs
- **Hardware descriptions**: Corrected references from "TB6612FNG H-bridge IC" to "discrete MOSFET H-bridge" to accurately reflect hardware design

---

## [0.1.0] - 2025-11-13

### Added
- **BLE GATT Server**: Full NimBLE implementation with 12 GATT characteristics for mobile app control (AD032)
- **8-State Motor Machine**: Instant mode switching (<100ms latency) with safe cleanup (SESSION_SUMMARY_MODE_SWITCH_REFACTOR.md)
- **State Machine Analysis**: Systematic bug detection methodology (STATE_MACHINE_ANALYSIS_CHECKLIST.md)
- **JPL Compliance**: Phase 4 implementation with message queues, error handling, watchdog management
- **NVS Persistence**: User settings saved across power cycles
- **Back-EMF Sampling**: Research measurements during first 10 seconds of mode changes
- **Battery Monitoring**: LiPo voltage sensing with low-battery protection
- **Documentation Versioning**: Unified semantic versioning system (AD034)
- **Immediate BLE Notifications**: Session time and battery level sent immediately on subscription

### Fixed
- 6 critical bugs found during state machine analysis before hardware testing:
  - State overwrite after shutdown (nested loop break scope error)
  - Missing cleanup in motor/LED state transitions
  - Button task message spam (no terminal state)
  - Watchdog timeout (missing feed in main loop)
  - BLE parameter update latency (up to 1s delay)
  - Emergency shutdown hang (inverted deep sleep logic)
- BLE re-enable button press (1-2s hold) now works in all states

### Infrastructure
- Modular architecture with separate task/control/manager modules
- ESP-IDF v5.5.0 via PlatformIO
- Seeed XIAO ESP32-C6 hardware platform
- 16-color LED palette (AD033)

### Documentation
- CLAUDE.md: AI reference guide
- README.md: Main project documentation
- architecture_decisions.md: 34 design decisions documented
- requirements_spec.md: Full project specification
- QUICK_START.md: Consolidated quick start guide

---

## Project Milestones (Pre-versioning)

### Phase 4: JPL Compliance (2025-11-04)
- Message queue architecture
- Button state machine (no goto)
- Comprehensive error handling
- Battery LVO protection

### BLE GATT Integration (2025-11-06)
- Full NimBLE GATT server implementation
- 12 GATT characteristics for mobile app control
- NVS persistence for user settings
- Immediate notifications on subscription
- State machine refactoring for instant mode switching

### Phase 1-3: Foundation (2025-10-01 to 2025-10-31)
- Motor control with 4 preset modes
- WS2812B LED control
- Button interface
- Back-EMF sensing research platform
- Power management (tickless idle, deep sleep)

### Initial Hardware (2025-09-15)
- ESP32-C6 hardware selection
- Discrete MOSFET H-bridge motor driver
- Dual 320mAh LiPo batteries
- WS2812B RGB LEDs

---

## Version Bump Guidelines

### Minor Versions (v0.x.Y)
- Documentation updates, clarifications, typo fixes
- Content additions to existing documents
- Small feature additions

### Major Versions (v0.X.0)
- New features (BLE, dual-device support)
- Architecture changes documented in new ADs
- Requirement updates
- Breaking changes to APIs or workflows

### Version 1.0.0
- Production release milestone
- Feature-complete implementation
- Comprehensive testing completed
- Full documentation verified
