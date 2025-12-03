# Dual-Device Boot Analysis - Detailed Timeline Tables

## BOOT 1: Initial Pairing & Motor Start Delay

### Phase 1: Pairing & Connection (ms 5500-6200)

| Time | Device | Component | Event | Details |
|------|--------|-----------|-------|---------|
| 5884 | SERVER | BLE_TASK | Pairing complete | GPIO15 turned OFF |
| 5884 | CLIENT | BLE_TASK | Pairing complete | GPIO15 turned OFF |
| 5884 | SERVER | MOTOR_TASK | Pairing message received | Session timer initialized |
| 5884 | CLIENT | MOTOR_TASK | Pairing message received | Session timer initialized |
| 5884 | SERVER | LED_CTRL | WS2812B ownership | MOTOR_TASK now controls |
| 5884 | CLIENT | LED_CTRL | WS2812B ownership | MOTOR_TASK now controls |
| 5884 | SERVER | TIME_SYNC_TASK | Initialization started | role=SERVER |
| 5884 | CLIENT | TIME_SYNC_TASK | Initialization started | role=CLIENT |
| 5969 | SERVER | TIME_SYNC | Server ready | Waiting for CLIENT request |
| 5974 | CLIENT | TIME_SYNC | Handshake initiated | T1=5614306 µs |
| 6074 | TIME_SYNC_TASK | Coordination | Received TIME_REQUEST | Processing NTP |
| 6074 | SERVER | TIME_SYNC | Response sent | T2=9403804, T3=9403815 |
| 6074 | CLIENT | TIME_SYNC | Handshake complete | offset=3740381 µs, RTT=98234 µs |
| 6084 | CLIENT | TIME_SYNC | Motor epoch set | 11660766 µs, cycle=2000 ms |
| 6144 | CLIENT | MOTOR_TASK | Coordinated start check | target=11660766, now=2041488, wait=9619 ms |

### Phase 2: SERVER Preparation & Motor Start (ms 8900-12100)

| Time | Device | Component | Event | Details |
|------|--------|-----------|-------|---------|
| 8989 | SERVER | MOTOR_TASK | Coordinated start scheduled | 3000 ms from now (target=11660766 µs) |
| 9019 | SERVER | BLE_MANAGER | Beacon sent (seq=1) | 28 bytes, SERVER ready |
| 9099 | SERVER | MOTOR_TASK | Waiting for CLIENT_READY | Paused at coordination |
| 9769 | SERVER | TIME_SYNC_TASK | CLIENT_READY received | Both devices synchronized |
| 9899 | SERVER | MOTOR_TASK | CLIENT_READY processed | Proceeding to coordinated start |
| 9999 | SERVER | MOTOR_TASK | Coordinated start check | target=11660766, now=9531128, offset=0 |
| 10099 | SERVER | MOTOR_TASK | Waiting 2129 ms | For motors to start |

### Phase 3: Critical Moment - SERVER Starts, CLIENT Waits (ms 12000-15800)

| Time | Device | Motor State | Details | Notes |
|------|--------|-------------|---------|-------|
| **12029** | **SERVER** | **ACTIVE (FWD)** | **MOTOR_STARTED sent** | **CLIENT NOT YET NOTIFIED** |
| 12039 | SERVER | ACTIVE (FWD) | Motor forward: 80% duty | BEMF logging triggered |
| 12229 | SERVER | COASTING | Motor coasting | FWD cycle complete |
| 12299 | SERVER | COASTING | Back-EMF reading | 876mV→-1548mV |
| **13039** | **SERVER** | **INACTIVE** | **Cycle #2 starts** | **CLIENT still waiting** |
| **14039** | **SERVER** | **ACTIVE (REV)** | **Cycle #3 starts** | **CLIENT still waiting** |
| 14229 | SERVER | COASTING | Motor coasting | REV cycle complete |
| 14299 | SERVER | COASTING | Back-EMF reading | 969mV→-1362mV |
| **15039** | **SERVER** | **INACTIVE** | **Cycle #4 starts** | **CLIENT still waiting** |
| **15774** | **CLIENT** | **[NOTIFICATION RECEIVED]** | **MOTOR_STARTED finally arrives** | **3745 ms delay!** |
| **15774** | **CLIENT** | **INACTIVE** | **CLIENT starts motors** | **7.5 cycles behind** |

### Phase 4: Bilateral Operation Begins (ms 15800+)

| Time | SERVER State | CLIENT State | Status | Notes |
|------|--------------|--------------|--------|-------|
| 15774 | INACTIVE | INACTIVE | SYNCHRONIZED START | Both now in phase |
| 16764 | ACTIVE (REV) | ACTIVE (REV) | IN PHASE | Motors aligned |
| 16874 | COASTING | COASTING | SYNCHRONIZED | Good bilateral operation |
| 17774 | INACTIVE | INACTIVE | IN PHASE | Continuing synchronized |
| 18443 | ACTIVE (FWD) | ACTIVE (FWD) | IN PHASE | Bilateral continues |

**Boot 1 Summary:**
- Unilateral duration: 3745 ms (3.7 seconds)
- SERVER cycles before CLIENT starts: 3 complete + 1 partial
- MOTOR_STARTED notification latency: 3745 ms (74× expected)
- Time to bilateral operation: 15774 ms (15.7 seconds)

---

## BOOT 2: Offset Inversion During RTT Update

### Phase 1: Fresh Connection & Handshake (ms 5800-6200)

| Time | Device | Component | Event | Offset | Notes |
|------|--------|-----------|-------|--------|-------|
| 5884 | CLIENT | MOTOR_TASK | Pairing complete | - | Fresh session start |
| 5884 | SERVER | MOTOR_TASK | Pairing complete | - | Already paired from Boot 1 |
| 5924 | CLIENT | TIME_SYNC | Handshake initiated | - | T1=5564350 µs sent |
| 6064 | SERVER | TIME_SYNC | Response processed | - | T2=5987982, T3=5987993 |
| 6064 | CLIENT | TIME_SYNC | Handshake complete | **+353346 µs** | **CORRECT: CLIENT ahead** |
| 6084 | CLIENT | TIME_SYNC | Motor epoch set | +353346 µs | Ready for coordinated start |
| 6144 | CLIENT | MOTOR_TASK | Coordinated start check | +353346 µs | target=8730767, wait=3310 ms |

### Phase 2: Motor Start - Still Using Correct Offset (ms 8700-10400)

| Time | Device | Motor State | Offset | Details |
|------|--------|-------------|--------|---------|
| **8714** | **CLIENT** | **[READY]** | **+353346 µs** | **MOTOR_STARTED received** |
| 9464 | CLIENT | INACTIVE | +353346 µs | Coordinated start reached |
| 9474 | CLIENT | INACTIVE | +353346 µs | INITIAL ALIGN: wait=971 ms |
| 10444 | CLIENT | ACTIVE (REV) | +353346 µs | ✓ Correct phase still |

### Phase 3: Critical Moment - RTT Update Inverts Offset (ms 16200-16500)

| Time | Component | Event | Old Offset | New Offset | Delta | Status |
|------|-----------|-------|-----------|-----------|--------|--------|
| 16214 | TIME_SYNC_TASK | Beacon seq=2 received | +353346 µs | +353346 µs | 0 | ✓ Confirmed |
| 16314 | TIME_SYNC | **RTT offset updated** | **+353346 µs** | **-394378 µs** | **-747724 µs** | **✗ INVERTED!** |
| 16324 | TIME_SYNC | Quality assessment | - | 95% | - | (Quality still high!) |
| 16454 | CLIENT | Switch ACTIVE (FWD) | -394378 µs | -394378 µs | - | Using WRONG offset |

**Inversion Analysis:**
```
Ratio: new / old = -394378 / 353346 = -1.116

This is NOT a small refinement:
- Expected: ±50 µs change (RTT precision improvement)
- Actual: -747724 µs change (complete sign reversal + amplification)
- Indicates: new_offset = -2.11 × old_offset formula (or similar)
```

### Phase 4: Antiphase Operation & Convergence (ms 16400-37000)

| Time | CLIENT Motor | SERVER Motor | CLIENT Offset | Status | Drift |
|------|--------------|--------------|---------------|--------|-------|
| 16454 | ACTIVE (FWD) | ACTIVE (REV) | -394378 µs | **ANTIPHASE!** | -747 ms |
| 17464 | INACTIVE | INACTIVE | -394378 µs | Opposite directions | -756 ms |
| 17464 | | | | **CATCH-UP #1** | **-50 ms** |
| 18414 | ACTIVE (REV) | ACTIVE (FWD) | -394378 µs | Still inverted | -700 ms |
| 19414 | INACTIVE | INACTIVE | -394378 µs | | -714 ms |
| 19424 | | | | **CATCH-UP #2** | **-50 ms** |
| 20374 | ACTIVE (FWD) | ACTIVE (REV) | | Correction slow | |
| 21384 | | | | **CATCH-UP #3** | **-50 ms** |
| ... | ... | ... | | ... | ... |
| 26244 | ACTIVE (FWD) | ACTIVE (REV) | | Still opposite | -500+ ms |
| 27254 | | | | **CATCH-UP #6** | **-50 ms** |
| 30174 | ACTIVE (FWD) | ACTIVE (REV) | | Slowly improving | -400 ms |
| 37044 | ACTIVE (FWD) | ACTIVE (REV) | | **CATCH-UP STOPS** | **-337 ms** |

**Convergence Pattern:**
- Catch-up applies -50 ms correction per cycle (every 1000 ms)
- Initial drift: -756 ms → Final residual: -337 ms
- Total correction applied: 419 ms
- Cycles to partial convergence: 12+ cycles
- Success: Partial (still -337 ms error)

### Phase 5: End State (ms 37000+)

| Time | CLIENT Motor | SERVER Motor | Offset Status | Notes |
|------|--------------|--------------|----------------|-------|
| 37044 | ACTIVE (FWD) | ACTIVE (REV) | -337 µs residual | **Still antiphase!** |
| 37044+ | [continues] | [continues] | | Catch-up stops |
| | | | | Residual 337 µs error persists |
| | | | | Device operates in degraded mode |

**Boot 2 Summary:**
- Initial offset (correct): +353346 µs
- RTT offset (inverted): -394378 µs
- Inversion magnitude: -747724 µs (2.11× magnification with sign flip)
- Antiphase duration: 12+ seconds (entire observation period)
- Residual error: 337 µs (never reaches zero)
- Root cause: Sign error in RTT offset calculation formula

---

## Comparative Analysis

### Boot 1 vs Boot 2 Issues

| Aspect | Boot 1 | Boot 2 | Type |
|--------|--------|--------|------|
| **Initial sync** | Good | Good | ✓ Both correct |
| **Offset sign** | + (correct) | + (correct) | ✓ Both correct |
| **Problem onset** | t=12029 ms | t=16314 ms | Different |
| **Problem type** | BLE notification latency | RTT calculation error | Different root cause |
| **Duration** | 3745 ms (one-time) | 12+ seconds (continuous) | Boot 2 worse |
| **Motor phase** | Unilateral | Antiphase | Different consequences |
| **Recovery** | Automatic (after notification) | Catch-up correction | Boot 2 slower |
| **Final outcome** | Synchronized | Residual -337 µs error | Boot 2 worse |

### Impact on 20-Minute Session

| Boot | Time Lost | Percentage | Impact |
|------|-----------|-----------|--------|
| **Boot 1** | 3.7 seconds (unilateral) | 0.31% | Patient feels one-sided for first 3.7s |
| **Boot 2** | 12+ seconds (antiphase) | 1.0% | Patient feels reversed/inverted motion |
| **Combined** | 15.7 seconds | 1.3% | **Not EMDRIA compliant** |

---

## Key Timing Markers

### Boot 1 Critical Times

```
5884 ms  = Connection complete
6074 ms  = Time sync handshake complete (+3740381 µs offset)
12029 ms = SERVER motors start ACTIVE
15774 ms = CLIENT receives MOTOR_STARTED (3745 ms delay!)
15774 ms = CLIENT motors finally start

Time to bilateral: 15774 - 12029 = 3745 ms delay
```

### Boot 2 Critical Times

```
5884 ms  = Connection complete
6064 ms  = Time sync handshake complete (+353346 µs offset, CORRECT)
8714 ms  = CLIENT receives MOTOR_STARTED
9464 ms  = CLIENT motors start INACTIVE (8s to start, normal)
16314 ms = RTT update INVERTS offset to -394378 µs (WRONG!)
16454 ms = CLIENT cycles ACTIVE using wrong offset
17464 ms = First CATCH-UP correction triggered (-756 ms drift)
26244 ms = Still in catch-up phase (-500+ ms drift)
37044 ms = Catch-up stops, residual error -337 µs remains
```

---

## BLE Notification Timeline (Issue #1)

### Expected vs Actual Delivery

| Stage | Expected | Actual | Latency |
|-------|----------|--------|---------|
| SERVER sends MOTOR_STARTED | 12029 ms | 12029 ms | 0 ms (start) |
| BLE stack processes | +10-50 ms | +? ms | ? |
| Notification enqueued | +20-100 ms | +? ms | ? |
| CLIENT receives | ~12079-12129 ms | 15774 ms | **3745 ms** |
| **Total BLE latency** | **50-100 ms** | **3745 ms** | **37.5-75× slower** |

The 3745 ms latency suggests:
- Notification queued behind other BLE operations
- Task context switch delays
- Possible mutex contention
- OR: Notification not being sent until later in SERVER task cycle

---

## RTT Offset Inversion Pattern (Issue #2)

### Mathematical Analysis

```
Initial Offset (Handshake):     +353346 µs
RTT Calculated Offset:          -394378 µs
Difference (drift):             -747724 µs

Ratio Analysis:
  -394378 / 353346 = -1.1159

  This suggests: new_offset ≈ -1.116 × old_offset

  More likely:  new_offset = -(old_offset × 2) + error

  Check: -2 × 353346 = -706692
         Actual:       -394378
         Error:        +312314

This doesn't match simple formulas, indicating:
1. Complex calculation with multiple steps
2. Possible overflow/underflow
3. Type casting error (signed/unsigned)
4. Or: Accumulation of multiple sign errors
```

### Why Catch-Up Doesn't Fix It

Catch-up logic applies fixed -50 ms correction per cycle:
- Initial drift: -747724 µs ≈ -747.7 ms
- Correction per cycle: -50 ms
- Cycles needed to reach zero: 747.7 / 50 ≈ 15 cycles
- Actual observation: Stops at 12 cycles with -337 µs remaining

**Why it stops:**
- Logic likely has condition: `if (|drift| < threshold) break;`
- -337 µs is close to zero, trigger stops
- But offset is still WRONG (should be +353, not -394)
- Catch-up fixes timing drift, but not offset sign

---

## Conclusion

**Boot 1 Issue:** BLE notification delivery delay causes 3.7-second unilateral vibration before bilateral starts.

**Boot 2 Issue:** RTT offset calculation inverts the sign, causing 12+ seconds of antiphase operation with incomplete recovery.

**Combined Impact:** Device fails to meet EMDRIA bilateral alternation requirement for first 15+ seconds of therapy session.

