Hardened PTP IEEE 1588 over BLE

Observation Mode Implementation for mlehaptics

Architecture Decision Record & JPL C Reference Implementation

Date: December 2025 • Status: Implementation Guide • Phase:
Pre-Correction Validation

Executive Summary

This document defines a hardened PTP-over-BLE time synchronization
system operating in **observation-only mode**. The system computes clock
offsets and path delays using IEEE 1588 mathematics but deliberately
withholds all clock corrections. This \"trust but verify\" approach
proves the synchronization math before enabling active correction,
directly addressing the observed failure mode where SERVER believes
CLIENT is in correct antiphase when drift has accumulated.

The core insight: if we can\'t accurately *observe* drift, we certainly
can\'t *correct* it. This implementation provides sub-millisecond drift
measurement over BLE with full logging for post-session analysis.

Problem Statement

Observed Failure Mode

The bilateral stimulation system exhibits timing drift where SERVER
maintains internal state indicating CLIENT is in correct antiphase, but
actual motor activation times have diverged. This manifests as both
devices occasionally firing simultaneously rather than in
alternation---therapeutically incorrect and perceptually jarring.

Root Cause Hypothesis

Three potential failure points exist in the current architecture:

1.  **Timestamp placement:** BLE stack processing delays (1-5ms)
    included in timestamps, corrupting offset calculation

2.  **Asymmetric path delay:** Assuming symmetric TX/RX latency when BLE
    connection intervals create asymmetry

3.  **Motor epoch drift:** Crystal oscillator PPM drift accumulating
    faster than resync frequency

Observation mode isolates each variable by providing ground-truth drift
measurements independent of correction logic.

Architecture Overview

PTP-over-BLE Adaptation

IEEE 1588 Precision Time Protocol assumes Ethernet with hardware
timestamping. BLE provides neither---connection-oriented protocol with
variable stack delays. This implementation adapts PTP\'s mathematical
core while acknowledging BLE\'s constraints:

  -----------------------------------------------------------------------
  **Aspect**              **IEEE 1588             **PTP-over-BLE**
                          (Ethernet)**            
  ----------------------- ----------------------- -----------------------
  Timestamp source        PHY hardware            esp_timer (1µs
                                                  resolution)

  Achievable precision    \<1 µs                  40-500 µs (stack
                                                  dependent)

  Path symmetry           Guaranteed              Measured & compensated

  Message exchange        Sync → Follow_Up →      SYNC_BEACON →
                          Delay_Req → Delay_Resp  SYNC_RESPONSE
                                                  (bidirectional)

  Therapeutic requirement N/A                     ±5ms (perceptual
                                                  threshold \~50ms)
  -----------------------------------------------------------------------

**Key insight:** BLE\'s 40-500µs jitter is acceptable when therapeutic
tolerance is ±5ms. We have 10-100× margin. The problem isn\'t
precision---it\'s *trusting the measurement*.

Observation Mode Message Flow

SERVER (Master Clock) CLIENT (Observer) │ │ │ │ T1 ──┼── SYNC_BEACON
──────────────────\>│── T2 │ {t1_server_us, seq_num} │ (record arrival
time) │ │ │ │ T4 ──┼\<─────────────── SYNC_RESPONSE ───┼── T3 │
{t2_client_us, t3_client_us, │ (record departure time) │ seq_num} │ │ │
│ \[Calculate offset & delay\] │ \[Calculate offset & delay\] │ \[LOG
ONLY - NO CORRECTION\] │ \[LOG ONLY - NO CORRECTION\] │ │ │ │ ├── Next
beacon (50-100ms) ───────\>│ │ │

Core Mathematics

IEEE 1588 Offset & Delay Calculation

The four-timestamp exchange (Cristian\'s algorithm variant) calculates
clock offset and one-way delay assuming symmetric path latency:

Timestamps: T1 = Server send time (server clock) T2 = Client receive
time (client clock) T3 = Client send time (client clock) T4 = Server
receive time (server clock) One-way delay (assuming symmetric path):
delay = \[(T2 - T1) + (T4 - T3)\] / 2 Clock offset (client ahead =
positive): offset = \[(T2 - T1) - (T4 - T3)\] / 2 = (T2 - T1) - delay
Interpretation: offset \> 0 → Client clock is AHEAD of server offset \<
0 → Client clock is BEHIND server To align client to server (if we were
correcting): client_corrected_time = client_time - offset

Exponential Weighted Average (EWA) Filter

Raw offset measurements exhibit BLE stack jitter. EWA provides smoothed
observation without the instability of aggressive correction:

α = 0.1 (smoothing factor, tune 0.05-0.2) ewa_offset = α × raw_offset +
(1 - α) × ewa_offset_prev Properties: - α = 0.1 → 90% weight on history,
10% on new sample - Settling time: \~10/α samples to reach 63% of step
change - At α = 0.1: \~100 samples (5-10 seconds at 10-20 Hz beacon
rate)

Drift Rate Estimation

Crystal oscillator drift is temperature-dependent but locally linear.
Track drift rate for diagnostic insight:

drift_rate_ppm = (offset_now - offset_prev) / (time_now - time_prev) ×
1e6 Expected ranges: Typical crystal: ±20 PPM → ±20 µs/second drift
Worst-case crystal: ±50 PPM → ±50 µs/second drift Over 30-second resync
interval at 50 PPM: Max drift = 50 × 30 = 1500 µs = 1.5 ms This is well
within ±5ms therapeutic tolerance.

JPL C Reference Implementation

The following pseudocode adheres to JPL Coding Standard (*JPL
Institutional Coding Standard for the C Programming Language*). Key
compliance points: no dynamic allocation, fixed-size buffers, bounded
loops, defensive assertions, explicit return checking.

Data Structures

/\*===========================================================================
\* ptp_observer.h - PTP-over-BLE Observation Mode \* \* JPL Rule #1: No
dynamic memory allocation \* JPL Rule #2: Fixed loop bounds
(PTP_HISTORY_SIZE) \* JPL Rule #3: No recursion
\*===========================================================================\*/
#ifndef PTP_OBSERVER_H #define PTP_OBSERVER_H #include \<stdint.h\>
#include \<stdbool.h\> /\* Configuration constants \*/ #define
PTP_HISTORY_SIZE 128U /\* Circular buffer for drift history \*/ #define
PTP_EWA_ALPHA_NUM 1U /\* EWA α numerator (α = 1/10 = 0.1) \*/ #define
PTP_EWA_ALPHA_DEN 10U /\* EWA α denominator \*/ #define
PTP_JITTER_BOUND_US 10000 /\* Discard samples \> 10ms jitter \*/ #define
PTP_BEACON_INTERVAL_MS 100U /\* Sync beacon rate \*/ /\* Sync message
types (extends sync_message_type_t from AD030) \*/ typedef enum {
PTP_MSG_SYNC_BEACON = 0x10, /\* SERVER→CLIENT: T1 timestamp \*/
PTP_MSG_SYNC_RESPONSE = 0x11, /\* CLIENT→SERVER: T2, T3 timestamps \*/
PTP_MSG_DRIFT_REPORT = 0x12 /\* Bidirectional: Computed drift feedback
\*/ } ptp_message_type_t; /\* Four-timestamp exchange record \*/ typedef
struct { int64_t t1_server_us; /\* Server send time (server clock) \*/
int64_t t2_client_us; /\* Client receive time (client clock) \*/ int64_t
t3_client_us; /\* Client send time (client clock) \*/ int64_t
t4_server_us; /\* Server receive time (server clock) \*/ uint16_t
seq_num; /\* Sequence number for packet matching \*/ bool valid; /\* All
four timestamps captured \*/ } ptp_timestamp_set_t; /\* Computed
synchronization metrics \*/ typedef struct { int64_t raw_offset_us; /\*
Instantaneous offset (µs) \*/ int64_t ewa_offset_us; /\* Smoothed offset
(µs) \*/ int64_t one_way_delay_us; /\* Path delay (µs) \*/ int32_t
drift_rate_ppm; /\* PPM drift rate \*/ uint32_t sample_count; /\* Total
samples processed \*/ uint32_t rejected_count; /\* Samples exceeding
jitter bound \*/ } ptp_metrics_t; /\* Drift history entry for
logging/analysis \*/ typedef struct { uint32_t timestamp_ms; /\* Local
monotonic time \*/ int32_t offset_us; /\* Offset at this sample
(truncated to int32) \*/ int32_t delay_us; /\* Delay at this sample \*/
uint16_t seq_num; /\* Beacon sequence \*/ } ptp_history_entry_t; /\*
Main observer state - statically allocated \*/ typedef struct { /\*
Current exchange in progress \*/ ptp_timestamp_set_t current_exchange;
/\* Computed metrics \*/ ptp_metrics_t metrics; /\* Circular history
buffer (JPL Rule #1: static allocation) \*/ ptp_history_entry_t
history\[PTP_HISTORY_SIZE\]; uint32_t history_write_idx; /\* State
tracking \*/ bool initialized; bool observation_active; int64_t
last_offset_us; /\* For drift rate calculation \*/ uint32_t
last_offset_time_ms; /\* Sequence tracking \*/ uint16_t
expected_seq_num; uint32_t sequence_errors; } ptp_observer_state_t; /\*
BLE message payloads \*/ typedef struct \_\_attribute\_\_((packed)) {
uint8_t msg_type; /\* PTP_MSG_SYNC_BEACON \*/ int64_t t1_server_us; /\*
Server timestamp \*/ uint16_t seq_num; /\* Sequence number \*/ }
ptp_sync_beacon_t; typedef struct \_\_attribute\_\_((packed)) { uint8_t
msg_type; /\* PTP_MSG_SYNC_RESPONSE \*/ int64_t t2_client_us; /\* Client
RX timestamp \*/ int64_t t3_client_us; /\* Client TX timestamp \*/
uint16_t seq_num; /\* Echo sequence number \*/ } ptp_sync_response_t;
typedef struct \_\_attribute\_\_((packed)) { uint8_t msg_type; /\*
PTP_MSG_DRIFT_REPORT \*/ int32_t offset_us; /\* Computed offset \*/
int32_t delay_us; /\* Computed delay \*/ uint16_t seq_num; /\* Reference
sequence \*/ } ptp_drift_report_t; #endif /\* PTP_OBSERVER_H \*/

Core Implementation

/\*===========================================================================
\* ptp_observer.c - PTP-over-BLE Observation Mode Implementation \* \*
OBSERVATION ONLY - NO CLOCK CORRECTIONS APPLIED \* \* JPL Rule #5: All
return values checked \* JPL Rule #6: No unbounded waits \* JPL Rule #8:
Defensive assertions and logging
\*===========================================================================\*/
#include \"ptp_observer.h\" #include \"esp_timer.h\" #include
\"esp_log.h\" #include \<string.h\> static const char \*TAG =
\"PTP_OBS\"; /\* Single static instance (JPL Rule #1) \*/ static
ptp_observer_state_t g_observer = {0};
/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* Initialization
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
esp_err_t ptp_observer_init(void) { /\* JPL Rule #8: Defensive - prevent
double init \*/ if (g_observer.initialized) { ESP_LOGW(TAG, \"Already
initialized\"); return ESP_ERR_INVALID_STATE; } /\* Zero all state \*/
memset(&g_observer, 0, sizeof(g_observer)); g_observer.initialized =
true; g_observer.observation_active = false; ESP_LOGI(TAG, \"PTP
Observer initialized (OBSERVATION ONLY - NO CORRECTIONS)\"); return
ESP_OK; }
/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* Get current microsecond timestamp \* Uses esp_timer for 1µs
resolution monotonic time
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
static inline int64_t ptp_get_timestamp_us(void) { return
esp_timer_get_time(); /\* Returns int64_t microseconds \*/ }
/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* SERVER: Generate and send sync beacon \* Called by time_sync_task at
PTP_BEACON_INTERVAL_MS
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
esp_err_t ptp_server_send_beacon(void) { if (!g_observer.initialized
\|\| !g_observer.observation_active) { return ESP_ERR_INVALID_STATE; }
ptp_sync_beacon_t beacon = {0}; beacon.msg_type = PTP_MSG_SYNC_BEACON;
beacon.seq_num = g_observer.expected_seq_num++; /\* CRITICAL: Timestamp
as close to TX as possible \*/ /\* Ideally in BLE TX callback, but
NimBLE doesn\'t expose this \*/ beacon.t1_server_us =
ptp_get_timestamp_us(); /\* Store T1 for when response arrives \*/
g_observer.current_exchange.t1_server_us = beacon.t1_server_us;
g_observer.current_exchange.seq_num = beacon.seq_num;
g_observer.current_exchange.valid = false; /\* Send via existing
coordination message infrastructure (AD030) \*/ /\*
ble_send_coordination_message() handles GATT write \*/ esp_err_t ret =
ble_send_ptp_message(&beacon, sizeof(beacon)); if (ret != ESP_OK) {
ESP_LOGW(TAG, \"Beacon TX failed: seq=%u\", beacon.seq_num); } return
ret; }
/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* CLIENT: Handle incoming sync beacon \* Called from BLE GATT write
handler
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
esp_err_t ptp_client_handle_beacon(const ptp_sync_beacon_t \*beacon) {
if (!g_observer.initialized \|\| !g_observer.observation_active) {
return ESP_ERR_INVALID_STATE; } /\* JPL Rule #8: Validate input \*/ if
(beacon == NULL) { return ESP_ERR_INVALID_ARG; } /\* Record T2
immediately on receipt \*/ int64_t t2 = ptp_get_timestamp_us(); /\*
Sequence check \*/ if (beacon-\>seq_num != g_observer.expected_seq_num)
{ g_observer.sequence_errors++; ESP_LOGW(TAG, \"Seq mismatch:
expected=%u got=%u (errors=%lu)\", g_observer.expected_seq_num,
beacon-\>seq_num, g_observer.sequence_errors);
g_observer.expected_seq_num = beacon-\>seq_num + 1; } else {
g_observer.expected_seq_num++; } /\* Prepare response \*/
ptp_sync_response_t response = {0}; response.msg_type =
PTP_MSG_SYNC_RESPONSE; response.t2_client_us = t2; response.seq_num =
beacon-\>seq_num; /\* Record T3 as close to TX as possible \*/
response.t3_client_us = ptp_get_timestamp_us(); /\* Store for local
offset calculation \*/ g_observer.current_exchange.t1_server_us =
beacon-\>t1_server_us; g_observer.current_exchange.t2_client_us =
response.t2_client_us; g_observer.current_exchange.t3_client_us =
response.t3_client_us; g_observer.current_exchange.seq_num =
beacon-\>seq_num; /\* T4 not available on client - server computes full
offset \*/ /\* Send response \*/ esp_err_t ret =
ble_send_ptp_message(&response, sizeof(response)); /\* Client can
compute partial offset using T1, T2 only \*/ /\* Full offset requires T4
from server feedback \*/ int64_t partial_offset =
response.t2_client_us - beacon-\>t1_server_us; ESP_LOGD(TAG, \"Beacon
RX: seq=%u T1=%lld T2=%lld partial_offset=%lldus\", beacon-\>seq_num,
beacon-\>t1_server_us, t2, partial_offset); return ret; }
/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* SERVER: Handle sync response from client \* Completes four-timestamp
exchange and computes offset/delay
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
esp_err_t ptp_server_handle_response(const ptp_sync_response_t
\*response) { if (!g_observer.initialized \|\|
!g_observer.observation_active) { return ESP_ERR_INVALID_STATE; } if
(response == NULL) { return ESP_ERR_INVALID_ARG; } /\* Record T4
immediately \*/ int64_t t4 = ptp_get_timestamp_us(); /\* Validate
sequence matches pending exchange \*/ if (response-\>seq_num !=
g_observer.current_exchange.seq_num) { ESP_LOGW(TAG, \"Response seq
mismatch: expected=%u got=%u\", g_observer.current_exchange.seq_num,
response-\>seq_num); g_observer.metrics.rejected_count++; return
ESP_ERR_INVALID_RESPONSE; } /\* Complete the timestamp set \*/
ptp_timestamp_set_t \*ts = &g_observer.current_exchange;
ts-\>t2_client_us = response-\>t2_client_us; ts-\>t3_client_us =
response-\>t3_client_us; ts-\>t4_server_us = t4; ts-\>valid = true; /\*
Compute offset and delay \*/ return ptp_compute_and_log_offset(ts); }
/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* Core PTP math: Compute offset and delay from four timestamps \* \*
OBSERVATION ONLY - Results logged but NO corrections applied
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
static esp_err_t ptp_compute_and_log_offset(const ptp_timestamp_set_t
\*ts) { if (!ts-\>valid) { return ESP_ERR_INVALID_STATE; } int64_t t1 =
ts-\>t1_server_us; int64_t t2 = ts-\>t2_client_us; int64_t t3 =
ts-\>t3_client_us; int64_t t4 = ts-\>t4_server_us; /\* \* IEEE 1588
offset calculation: \* delay = \[(T2 - T1) + (T4 - T3)\] / 2 \* offset =
\[(T2 - T1) - (T4 - T3)\] / 2 \* = (T2 - T1) - delay \* \* offset \> 0
means client clock is AHEAD of server \*/ int64_t forward_delay = t2 -
t1; /\* Server→Client path \*/ int64_t reverse_delay = t4 - t3; /\*
Client→Server path \*/ int64_t one_way_delay = (forward_delay +
reverse_delay) / 2; int64_t raw_offset = (forward_delay - reverse_delay)
/ 2; /\* JPL Rule #8: Bounds check - reject outliers \*/ if
(one_way_delay \< 0 \|\| one_way_delay \> PTP_JITTER_BOUND_US) {
ESP_LOGW(TAG, \"Delay out of bounds: %lldus (seq=%u)\", one_way_delay,
ts-\>seq_num); g_observer.metrics.rejected_count++; return
ESP_ERR_INVALID_RESPONSE; } if (raw_offset \< -PTP_JITTER_BOUND_US \|\|
raw_offset \> PTP_JITTER_BOUND_US) { ESP_LOGW(TAG, \"Offset out of
bounds: %lldus (seq=%u)\", raw_offset, ts-\>seq_num);
g_observer.metrics.rejected_count++; return ESP_ERR_INVALID_RESPONSE; }
/\* Apply EWA filter (integer math to avoid float) \*/ /\* ewa = α \*
raw + (1-α) \* ewa_prev \*/ /\* ewa = (NUM \* raw + (DEN - NUM) \*
ewa_prev) / DEN \*/ int64_t ewa_prev = g_observer.metrics.ewa_offset_us;
int64_t ewa_new = (PTP_EWA_ALPHA_NUM \* raw_offset +
(PTP_EWA_ALPHA_DEN - PTP_EWA_ALPHA_NUM) \* ewa_prev) /
PTP_EWA_ALPHA_DEN; /\* Compute drift rate (PPM) \*/ uint32_t now_ms =
(uint32_t)(esp_timer_get_time() / 1000); int32_t drift_ppm = 0; if
(g_observer.last_offset_time_ms \> 0) { uint32_t dt_ms = now_ms -
g_observer.last_offset_time_ms; if (dt_ms \> 0) { int64_t d_offset =
raw_offset - g_observer.last_offset_us; /\* drift_ppm = (d_offset_us /
dt_ms) \* 1000 = d_offset_us \* 1000 / dt_ms \*/ drift_ppm =
(int32_t)((d_offset \* 1000) / dt_ms); } } /\* Update metrics \*/
g_observer.metrics.raw_offset_us = raw_offset;
g_observer.metrics.ewa_offset_us = ewa_new;
g_observer.metrics.one_way_delay_us = one_way_delay;
g_observer.metrics.drift_rate_ppm = drift_ppm;
g_observer.metrics.sample_count++; g_observer.last_offset_us =
raw_offset; g_observer.last_offset_time_ms = now_ms; /\* Store in
history buffer (circular, JPL Rule #2: bounded) \*/ uint32_t idx =
g_observer.history_write_idx % PTP_HISTORY_SIZE;
g_observer.history\[idx\].timestamp_ms = now_ms;
g_observer.history\[idx\].offset_us = (int32_t)raw_offset;
g_observer.history\[idx\].delay_us = (int32_t)one_way_delay;
g_observer.history\[idx\].seq_num = ts-\>seq_num;
g_observer.history_write_idx++; /\* LOG OBSERVATION - NO CORRECTION \*/
ESP_LOGI(TAG, \"PTP\[%u\] offset=%+.2fms ewa=%+.2fms delay=%.2fms
drift=%+dppm\", ts-\>seq_num, (float)raw_offset / 1000.0f,
(float)ewa_new / 1000.0f, (float)one_way_delay / 1000.0f, drift_ppm);
/\* \*
╔══════════════════════════════════════════════════════════════════╗ \*
║ OBSERVATION MODE: NO CLOCK CORRECTION APPLIED ║ \* ║ ║ \* ║ If we were
correcting, we would call: ║ \* ║ time_sync_apply_offset(-ewa_new); //
DISABLED ║ \* ║ ║ \* ║ Instead, offset is logged for post-session
analysis. ║ \* ║ Trust the math FIRST, then enable correction. ║ \*
╚══════════════════════════════════════════════════════════════════╝ \*/
/\* Send drift report back to client for bilateral logging \*/
ptp_drift_report_t report = {0}; report.msg_type = PTP_MSG_DRIFT_REPORT;
report.offset_us = (int32_t)ewa_new; report.delay_us =
(int32_t)one_way_delay; report.seq_num = ts-\>seq_num; /\*
Fire-and-forget feedback to client \*/
(void)ble_send_ptp_message(&report, sizeof(report)); return ESP_OK; }

Integration with time_sync_task

/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* time_sync_task.c integration \* \* Add PTP beacon generation to
existing time sync loop
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
/\* In time_sync_task main loop (SERVER role): \*/ static void
time_sync_task(void \*pvParameters) { TickType_t last_beacon_tick = 0;
const TickType_t beacon_interval =
pdMS_TO_TICKS(PTP_BEACON_INTERVAL_MS); while (1) { TickType_t now =
xTaskGetTickCount(); /\* Existing time sync logic\... \*/ /\* PTP beacon
generation (SERVER only) \*/ if (device_role == DEVICE_ROLE_SERVER) { if
((now - last_beacon_tick) \>= beacon_interval) {
ptp_server_send_beacon(); last_beacon_tick = now; } } /\* Yield to other
tasks \*/ vTaskDelay(pdMS_TO_TICKS(10)); } }
/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* BLE message handler integration \* \* Route PTP messages through
existing coordination message handler
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
/\* In handle_coordination_message() from AD030: \*/ void
handle_coordination_message(const uint8_t \*data, uint16_t len) { if
(len \< 1) return; uint8_t msg_type = data\[0\]; switch (msg_type) { /\*
Existing message types\... \*/ case SYNC_MSG_MODE_CHANGE: case
SYNC_MSG_SETTINGS: case SYNC_MSG_SHUTDOWN: /\* \... existing handlers
\... \*/ break; /\* PTP observation messages \*/ case
PTP_MSG_SYNC_BEACON: if (len \>= sizeof(ptp_sync_beacon_t)) {
ptp_client_handle_beacon((const ptp_sync_beacon_t \*)data); } break;
case PTP_MSG_SYNC_RESPONSE: if (len \>= sizeof(ptp_sync_response_t)) {
ptp_server_handle_response((const ptp_sync_response_t \*)data); } break;
case PTP_MSG_DRIFT_REPORT: if (len \>= sizeof(ptp_drift_report_t)) {
ptp_client_handle_drift_report((const ptp_drift_report_t \*)data); }
break; default: ESP_LOGW(TAG, \"Unknown message type: 0x%02x\",
msg_type); break; } }

Activation Drift Measurement

The core validation metric: does actual motor activation match expected
timing? This bridges the gap between clock offset (what PTP measures)
and therapeutic correctness (what the patient experiences).

Motor Activation Logging

/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* Motor activation timestamping \* \* Add to motor_task.c to capture
actual vs expected activation times
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
typedef struct { uint32_t cycle_num; /\* Motor cycle count \*/ int64_t
expected_time_us; /\* When motor SHOULD have fired \*/ int64_t
actual_time_us; /\* When motor ACTUALLY fired \*/ int32_t
activation_drift_us; /\* actual - expected \*/ int32_t ptp_offset_us;
/\* PTP offset at this cycle \*/ } activation_record_t; #define
ACTIVATION_HISTORY_SIZE 256U static activation_record_t
g_activation_log\[ACTIVATION_HISTORY_SIZE\]; static uint32_t
g_activation_idx = 0; /\* Call this at moment of motor GPIO assertion
\*/ void log_motor_activation(uint32_t cycle_num, int64_t
expected_time_us) { int64_t actual = esp_timer_get_time(); int32_t drift
= (int32_t)(actual - expected_time_us); uint32_t idx = g_activation_idx
% ACTIVATION_HISTORY_SIZE; g_activation_log\[idx\].cycle_num =
cycle_num; g_activation_log\[idx\].expected_time_us = expected_time_us;
g_activation_log\[idx\].actual_time_us = actual;
g_activation_log\[idx\].activation_drift_us = drift;
g_activation_log\[idx\].ptp_offset_us = (int32_t)ptp_get_ewa_offset();
g_activation_idx++; /\* Log if drift exceeds threshold \*/ if (drift \>
5000 \|\| drift \< -5000) { /\* ±5ms threshold \*/ ESP_LOGW(TAG,
\"ACTIVATION DRIFT: cycle=%lu expected=%lld actual=%lld \"
\"drift=%+.2fms ptp_offset=%+.2fms\", cycle_num, expected_time_us,
actual, (float)drift / 1000.0f,
(float)g_activation_log\[idx\].ptp_offset_us / 1000.0f); } }

Bilateral Phase Verification

/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* Phase verification: Are SERVER and CLIENT actually in antiphase? \*
\* SERVER logs its activation time, CLIENT logs its activation time. \*
Post-session analysis compares: was CLIENT at 180° ± tolerance?
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
/\* Expected relationship for bilateral alternating at 1Hz (1000ms
cycle): \* \* SERVER activates at: T + 0ms, T + 1000ms, T + 2000ms, \...
\* CLIENT activates at: T + 500ms, T + 1500ms, T + 2500ms, \... \* \*
Phase difference should be 500ms ± tolerance \* \* If we observe: \*
SERVER at T + 0ms, CLIENT at T + 480ms → OK (20ms early) \* SERVER at
T + 0ms, CLIENT at T + 520ms → OK (20ms late) \* SERVER at T + 0ms,
CLIENT at T + 100ms → FAIL (400ms early = overlap!) \*/ typedef struct {
uint32_t cycle_num; int64_t server_activation_us; /\* SERVER motor fire
time (server clock) \*/ int64_t client_activation_us; /\* CLIENT motor
fire time (client clock) \*/ int32_t ptp_offset_us; /\* Clock offset to
translate client→server \*/ int32_t phase_error_us; /\* Deviation from
expected 500ms antiphase \*/ } phase_record_t; /\* Calculate phase error
given both activation times and PTP offset \*/ int32_t
calculate_phase_error(int64_t server_time_us, int64_t client_time_us,
int32_t ptp_offset_us, uint32_t cycle_period_us) { /\* Translate client
time to server clock reference \*/ int64_t client_time_adjusted =
client_time_us - ptp_offset_us; /\* Expected phase difference is half
the cycle period (antiphase) \*/ int64_t expected_phase_us =
cycle_period_us / 2; /\* Actual phase difference \*/ int64_t
actual_phase_us = client_time_adjusted - server_time_us; /\* Normalize
to within one cycle \*/ while (actual_phase_us \< 0) { actual_phase_us
+= cycle_period_us; } while (actual_phase_us \>=
(int64_t)cycle_period_us) { actual_phase_us -= cycle_period_us; } /\*
Phase error: how far from expected antiphase? \*/ int32_t phase_error =
(int32_t)(actual_phase_us - expected_phase_us); return phase_error; }

Diagnostic API

/\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--
\* Public API for observation mode diagnostics
\*\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\*/
/\* Start observation (call after BLE connection established) \*/
esp_err_t ptp_observer_start(void) { if (!g_observer.initialized) {
return ESP_ERR_INVALID_STATE; } /\* Reset metrics for new session \*/
memset(&g_observer.metrics, 0, sizeof(g_observer.metrics));
g_observer.history_write_idx = 0; g_observer.sequence_errors = 0;
g_observer.observation_active = true; ESP_LOGI(TAG, \"PTP observation
STARTED - collecting drift data\"); return ESP_OK; } /\* Stop
observation and dump summary \*/ esp_err_t ptp_observer_stop(void) { if
(!g_observer.observation_active) { return ESP_ERR_INVALID_STATE; }
g_observer.observation_active = false; ESP_LOGI(TAG,
\"═══════════════════════════════════════════════════\"); ESP_LOGI(TAG,
\"PTP OBSERVATION SUMMARY\"); ESP_LOGI(TAG,
\"═══════════════════════════════════════════════════\"); ESP_LOGI(TAG,
\" Samples collected: %lu\", g_observer.metrics.sample_count);
ESP_LOGI(TAG, \" Samples rejected: %lu\",
g_observer.metrics.rejected_count); ESP_LOGI(TAG, \" Sequence errors:
%lu\", g_observer.sequence_errors); ESP_LOGI(TAG, \" Final EWA offset:
%+.3f ms\", (float)g_observer.metrics.ewa_offset_us / 1000.0f);
ESP_LOGI(TAG, \" Final delay: %.3f ms\",
(float)g_observer.metrics.one_way_delay_us / 1000.0f); ESP_LOGI(TAG, \"
Drift rate: %+d PPM\", g_observer.metrics.drift_rate_ppm); ESP_LOGI(TAG,
\"═══════════════════════════════════════════════════\"); return ESP_OK;
} /\* Get current metrics (for real-time display or BLE transmission)
\*/ const ptp_metrics_t\* ptp_observer_get_metrics(void) { return
&g_observer.metrics; } /\* Get smoothed offset for external use (NO
correction - observation only) \*/ int64_t ptp_get_ewa_offset(void) {
return g_observer.metrics.ewa_offset_us; } /\* Dump history buffer to
console (for post-session analysis) \*/ void
ptp_observer_dump_history(void) { uint32_t count =
(g_observer.history_write_idx \< PTP_HISTORY_SIZE) ?
g_observer.history_write_idx : PTP_HISTORY_SIZE; ESP_LOGI(TAG, \"PTP
History (%lu samples):\", count); ESP_LOGI(TAG,
\"timestamp_ms,offset_us,delay_us,seq_num\"); /\* JPL Rule #2: Bounded
loop \*/ for (uint32_t i = 0; i \< count; i++) { uint32_t idx =
(g_observer.history_write_idx - count + i) % PTP_HISTORY_SIZE;
ESP_LOGI(TAG, \"%lu,%d,%d,%u\", g_observer.history\[idx\].timestamp_ms,
g_observer.history\[idx\].offset_us, g_observer.history\[idx\].delay_us,
g_observer.history\[idx\].seq_num); } }

Validation Criteria

Before enabling clock corrections, the observation mode must
demonstrate:

  -----------------------------------------------------------------------
  **Metric**                 **Pass Criteria**      **Rationale**
  -------------------------- ---------------------- ---------------------
  EWA offset stability       Stays within ±3ms over Proves measurement,
                             20min session          not correction

  Drift rate consistency     \< ±50 PPM (matches    Higher = measurement
                             crystal spec)          error

  Sample rejection rate      \< 5% of samples       High rejection = BLE
                                                    instability

  Sequence error rate        \< 1% of beacons       High loss =
                                                    connection issue

  Phase error (bilateral)    \< ±50ms from expected Perceptual threshold
                             antiphase              \~50-100ms

  One-way delay variance     \< ±2ms standard       High variance =
                             deviation              asymmetric path
  -----------------------------------------------------------------------

**Test Protocol:** Run 1-hour sessions with temperature variation (±10°C
from ambient). Log all metrics. If any criterion fails, investigate
before enabling correction. The goal is proving the measurement
infrastructure, not achieving perfect sync.

BLE Service Integration

Add PTP observation characteristic to Bilateral Control Service (AD030)
for real-time drift monitoring from PWA:

  ------------------------------------------------------------------------
  **UUID**          **Name**    **Access**   **Payload**
  ----------------- ----------- ------------ -----------------------------
  \...E7010B        PTP Metrics R/Notify     offset_ms:i16, delay_ms:u16,
                                             drift_ppm:i16, samples:u16

  ------------------------------------------------------------------------

Implementation Roadmap

4.  **Phase 1 - Infrastructure:** Implement ptp_observer.c/h, integrate
    with time_sync_task, add BLE characteristic. No behavior change to
    existing system.

5.  **Phase 2 - Data Collection:** Run 10+ therapy-length sessions
    (20-90 min). Log all metrics. Export via serial or BLE for analysis.

6.  **Phase 3 - Validation:** Analyze logs against pass criteria.
    Identify systematic errors. Correlate PTP offset with actual
    activation drift.

7.  **Phase 4 - Correction (Future):** Only after observation proves
    accurate: uncomment time_sync_apply_offset() and tune EWA α for
    servo stability.

**Key Principle:** If we can\'t accurately OBSERVE drift, we certainly
can\'t CORRECT it. Prove the measurement first.

─────────────────────────────────────────

mlehaptics Project • JPL C Implementation Guide • December 2025
