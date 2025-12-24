# ADR 0049: CSI Phase-Based Motion Detection Exploration

**Status:** Proposed (Exploratory)
**Date:** 2025-12-23
**Authors:** Steve (mlehaptics), Claude Code (Opus 4.5)
**Related:** AD048 (ESP-NOW Transport), RFIP Addendum (ranging)

## Context

Our time synchronization architecture successfully corrects for path asymmetry using statistical methods: EMA filtering, Kalman prediction, outlier rejection, and drift rate estimation. The same mathematical framework could potentially apply to **phase-based RF measurements** from WiFi Channel State Information (CSI).

802.11mc FTM provides meter-level ranging via Time-of-Flight. Phase-based interferometry could theoretically achieve sub-centimeter precision—the physics is sound (2.4 GHz → 12.5cm wavelength). The challenge is that raw phase measurements are corrupted by:

| Corruption Source | Signature | Analogous Timing Problem |
|-------------------|-----------|-------------------------|
| Carrier Frequency Offset (CFO) | Linear phase rotation vs time | Clock drift rate |
| Sampling Time Offset (STO) | Linear phase slope vs subcarrier | RTT asymmetry |
| PLL jitter | High-frequency phase noise | BLE jitter |
| Packet sync reset | Random phase jump per packet | Connection event timing |

These corruptions have **predictable signatures** that can be modeled and subtracted—exactly as we model and subtract timing asymmetry.

## Decision

Establish a **phased exploration** to evaluate whether CSI phase sanitization is practical on ESP32-C6 hardware, with the ultimate goal of enhancing RFIP ranging precision or enabling new capabilities (relative motion detection, proximity sensing).

### Phase 1: Data Collection (Current Priority)

**Goal:** Capture raw CSI data and build intuition.

**Implementation:**
1. Enable CSI collection in ESP-IDF via `esp_wifi_set_csi_rx_cb()`
2. Log amplitude + phase for all subcarriers during ESP-NOW exchanges
3. Visualize data while moving devices (serial plotter or CSV export)
4. Document observed patterns: noise floor, CFO rotation rate, STO slope

**Deliverable:** Raw CSI logging integrated into ESP-NOW transport layer with optional enable flag.

**No runtime processing in Phase 1** - just data collection for offline analysis.

### Phase 2: Offline Analysis

**Goal:** Characterize corruption signatures and evaluate correctability.

- Measure CFO rate (phase rotation vs time) and stability
- Measure STO slope (phase vs subcarrier) and consistency
- Quantify noise floor after subtracting CFO/STO
- Determine if residual phase correlates with device distance/motion

**Deliverable:** Analysis report with go/no-go recommendation for Phase 3.

### Phase 3: Runtime Prediction Model

**Goal:** Implement real-time phase sanitization analogous to timing asymmetry correction.

- CFO tracker: Kalman filter on phase rotation rate
- STO estimator: Linear regression across subcarriers
- Motion detector: Track sanitized phase derivative
- Optional: Fuse with FTM ToF for integer ambiguity resolution

**Deliverable:** `csi_phase_tracker_t` module with runtime correction.

### Phase 4: Integration

**Goal:** Determine practical applications.

Possible outcomes:
- **Enhanced RFIP:** Sub-centimeter relative positioning between paired devices
- **Motion detection:** Detect approaching/departing motion for proximity features
- **Gesture sensing:** Evaluate feasibility for therapy device interaction
- **Negative result:** Document why phase-based methods aren't practical for this hardware/environment

## Rationale

### Why Explore This

1. **Mathematical parallel:** Our asymmetry correction proves we can build runtime statistical models for systematic RF errors. Phase corruption is the same class of problem.

2. **Hardware capability:** ESP32 exposes CSI data. The capability exists; we're just not using it.

3. **Potential payoff:** Sub-centimeter ranging would enable applications impossible with meter-level FTM (precise formation control, collision avoidance, docking).

4. **Low-risk exploration:** Phase 1 is just data logging. If the data looks unpromising, we stop.

### Why Phase 1 is Data-Only

- Current development is in a critical work phase (P7.1 pattern playback)
- Exploration should not destabilize production code
- Offline analysis avoids runtime overhead during evaluation
- "Measure twice, cut once" - understand the data before writing algorithms

## Technical Notes

### ESP-IDF CSI API

```c
wifi_csi_config_t csi_config = {
    .lltf_en = true,           // Long Training Field - most stable for phase
    .htltf_en = true,          // HT Long Training Field
    .stbc_htltf2_en = true,    // STBC HT-LTF
    .ltf_merge_en = true,      // Merge multiple LTF
    .channel_filter_en = false,// Raw data preferred
    .manu_scale = false,       // Automatic scaling
};
esp_wifi_set_csi_config(&csi_config);
esp_wifi_set_csi_rx_cb(csi_rx_callback, NULL);
```

### CSI Data Format

Each callback provides:
- RSSI and noise floor
- ~52 complex values (amplitude + phase) for OFDM subcarriers
- Timestamp
- Source MAC (identifies which peer)

### Phase Representation

CSI data arrives as `int8_t` pairs (I/Q). Phase = `atan2(Q, I)`. Phase wraps at ±π.

## References

1. ESP-IDF Programming Guide: Wi-Fi CSI
2. Halperin et al., "Tool Release: Gathering 802.11n Traces with Channel State Information," ACM CCR 2011
3. Wang et al., "Understanding and Modeling of WiFi Signal Based Human Activity Recognition," MobiCom 2015
4. GitHub: ESP32-CSI-Tool (StevenMHernandez)
5. AD043: Filtered Time Synchronization (asymmetry correction prior art)

## Success Criteria

- **Phase 1 complete:** CSI data logged, visualized, patterns documented
- **Phase 2 complete:** Corruption signatures characterized, feasibility assessed
- **Phase 3 complete:** Runtime model achieves measurable noise reduction
- **Phase 4 complete:** Practical application demonstrated OR documented infeasibility

## Risks

| Risk | Mitigation |
|------|------------|
| Multipath makes phase unusable indoors | Start with line-of-sight outdoor tests |
| CFO too unstable to track | Evaluate both devices' oscillator stability |
| Effort exceeds benefit | Strict phase gates; stop if data looks bad |
| Scope creep from core therapy device | This is explicitly exploratory, not blocking |
| Serial bottleneck during logging | Use binary logging or decimation (1-in-10 packets) |
| Integer ambiguity unsolvable | Focus on velocity first, not absolute distance |

---

## Cross-Model Review (Gemini)

*The following insights were contributed via cross-model triangulation (2025-12-23).*

### 1. The Math is Valid: "Vernier Caliper" Analogy

Phase is just **Time in a costume**:

| Time Domain | Frequency Domain |
|-------------|------------------|
| Clock drift (10 ppm) | Carrier rotation (3.6°/packet) |
| Propagation delay | Phase slope across subcarriers |

**The Vernier Caliper Strategy:**

- **FTM (ToF):** The "Main Scale" — measures 5m ± 1m
- **CSI (Phase):** The "Sliding Scale" — measures 0.125m (wavelength) ± 0.001m
- **Fusion:** Use FTM to resolve which wavelength (Integer Ambiguity Resolution), CSI to locate within that wavelength

The same Kalman Filter used for UTLP timing will work for phase tracking.

### 2. The Trap: Integer Ambiguity (The Wrap)

`atan2(Q, I)` wraps at ±π. Moving 12.5cm (one wavelength) spins 360° and looks identical to the starting point.

| Problem | Difficulty | Approach |
|---------|------------|----------|
| Relative Motion (Velocity) | **Easy** | Count the spins (Doppler) |
| Absolute Distance | **Hard** | Need FTM fusion or continuous tracking |

**Recommendation for Phase 3:** Don't solve "Absolute Distance" immediately. Focus on **Phase-Coherent Velocity**:

- Phase derivative = 0 → Devices are **relatively static**
- Phase derivative positive → Devices are **closing**
- Phase derivative negative → Devices are **separating**

This is sufficient for collision avoidance and gesture detection without solving the full integer ambiguity problem.

### 3. Killer App: Non-Contact Respiration Monitoring

**The EMDR therapy use case Gemini identified:**

Human chest movement during breathing: ~5mm

At 2.4 GHz (λ = 12.5cm):
- 5mm movement = **~14° phase shift**
- ESP32 CSI noise floor: **~2°** (when filtered)
- **Signal-to-noise: 7:1** — detectable!

**Implication:** The bilateral pulsers could sit on a table and detect patient hyperventilation by analyzing WiFi field perturbation between left and right units.

- No wires
- No cameras
- Just phase perturbation analysis

This fits the "invisible, empathetic sensing" philosophy of the mlehaptics project.

### 4. ESP32-C6 Technical Gotchas

#### A. HE-LTF (WiFi 6 Preamble)

The C6 speaks WiFi 6 (802.11ax). The config struct enables `htltf` (WiFi 4 High Throughput).

- If ESP-NOW uses standard rates (1 Mbps): HT-LTF is fine
- If AX rates are used: Need HE-LTF capture

**Action for Phase 1:** Verify `rx_ctrl` field in callback to confirm which preamble type is being captured.

#### B. Serial Bottleneck

CSI data volume:
```
52 subcarriers × 2 bytes (I/Q) = 104 bytes/packet
At 100 Hz packet rate = ~10 KB/s raw data
```

**Warning:** `printf()` over USB Serial while running the radio stack may crash the ISR.

**Fix for Phase 1:**
- Use binary logging (SLIP or raw bytes), OR
- Decimate: Log 1 of every 10 packets to "build intuition" without choking the CPU

### Gemini Verdict

> **Approve.** This is the correct next step. You have mastered Time (UTLP). Space (RFIP/CSI) is the logical next backbone. Even if you only get "Relative Motion" out of it, the ability for a swarm to know "I am moving towards my neighbor" without GPS is a game changer for the aerial drone application.

---

*This ADR captures an exploration path, not a committed feature. The goal is to not forget a promising direction while remaining focused on current priorities.*
