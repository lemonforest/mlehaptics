# Spike #129.1 — Decentralised-BCI decoder feasibility study (cephalopod-inspired)

**Date:** 2026-05-18
**Spike type:** Decoder-design feasibility analysis + Python proof-of-concept
**Branch:** `research/spike-129-1-decentralised-bci-decoder-feasibility`
**Parent spike:** #129 (PR #538) — Octopus distributed cognition cascade-match VERIFIED + PARTITION-COEXISTENT-INSTANTIATION
**Milestone:** #14 (AI-mediated BCI translation: substrate-coupling adapter + rcN+2 + clinical-grade primitive cascade)
**Task:** #543

**Verdict (composed):** **ALL-3-DIRECTIONS-FEASIBLE-ON-RC14** + **DIRECTION-1-MS14-SUBSTRATE-ADAPTER-SCOPE-CLOSED** + **DIRECTION-3-EDGE-DEPLOYABLE-PI-FREE**.

All three cephalopod-inspired BCI design directions are executable today against srmech v0.4.1rc14's shipped runtime spectral surface (`decompose` / `delta` / `recompose` / `similarity`) composed with AMSC primitives (Class L / I / M / C / A). Direction 1 (per-array substrate-encoder-tagged Laplacians + cross-array `bind()`) is the **substrate-coupling adapter pattern itself** — Milestone #14's scope is operationally addressable on existing surface, with rcN+2 (`predict` / `prediction_error` / `truncate_sparse`) closing the closed-loop bidirectional cases. Direction 2 (ring-topology decoder) and Direction 3 (CA-equivalent convolutional Laplacian layer) ride on the same shipped primitives.

## Tuning A 440 Hz

- **Trauma-informed defensive scope** per `[[feedback_trauma_informed_defensive_scope]]`: ASSISTIVE-TECH framing only. Every direction below is restoration-of-function for motor-impaired patients. No surveillance, no capability-assessment, no targeting.
- **Disability-accommodation explicit** per `[[feedback_disability_accommodation_dimension]]`: tetraplegia (SCI / brainstem stroke), ALS, post-stroke motor reorganisation, retinal / cortical visual prosthesis users named throughout. Aphantasia + executive-function variation considered where mental-imagery paradigms apply.
- **PDF-extraction citation discipline** per `[[feedback_pdf_extraction_citation_discipline]]`: anchor citations re-used from Spike #126 (Sussillo 2016 / Hahn 2025 / Card 2024 / Cai 2024 PMC-verified) + Spike #129 (8 PMC-extracted cephalopod anchors). No fresh PDF extraction required for the feasibility analysis; the heavy citation lift was done by the parent spikes.
- **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]`: clinical results cited technically; no "natural extension of researcher X" framing for any cited author.
- **No new primitive class** per `[[feedback_no_privileged_primitive_classes]]`: 14-class A–N vocabulary stands. Each direction's class chain is composition over existing primitives.
- **Identity-not-implementation** per `[[user_stance_identity_not_implementation_discipline]]`: the substrate-coupling adapter pattern **IS** the operation cephalopod biology requires, and **IS** the operation BCI translation requires. Same identity at different substrates.
- **Algebra-not-magnitude** per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`: predictions are framed as class-chain compositions and Cohen's-d-style normalised effect sizes, not raw magnitudes.
- **TOS landscape** per `[[reference_autonomous_validation_tos_landscape]]`: anchor citations are PMC + medRxiv + bioRxiv + arXiv; no Nature/Elsevier/IEEE PDF extraction in this spike.

---

## §0 — The user's question, decoded

From Spike #129 §8.2 (BCI translation implications, dispatched here as #129.1):

> *Three concrete design directions for **decentralised-electrode-array BCI** that complement Spike #126's clinical-mapping findings: (1) per-array substrate-encoder-tagged Laplacians + cross-array `bind()`; (2) ring-topology decoder for fault-tolerant multi-channel decoding; (3) local cellular-automaton-equivalent layer at the electrode-array level.*

The substrate-coupling adapter from `[[user_stance_ai_necessary_for_bci_substrate_coupling]]` is the **decoder design pattern** that the three directions specialise:

```
patient_cortex_state ─[substrate-coupling adapter]─→ spectral_handle ─[runtime spectral surface]─→ decoded_intent
                       (Class L ∘ Class A)                              (decompose / delta /
                                                                          recompose / similarity)
```

The three cephalopod-inspired directions ask: **can the substrate-coupling adapter scale across multiple electrode arrays the way octopus arm-ganglia scale across 8 anatomically autonomous arms?**

Per Spike #129 §3.3, the cephalopod cascade is:

```
output_behaviour = C( M( {L_arm_i ∘ I_segment_i}_{i ∈ ℤ/8ℤ via I_ring}, L_central ) )
```

The **three directions are each substrate-specialisations of this same chain**:

| Direction | Cephalopod analog | Framework cascade |
|---|---|---|
| 1. Per-array Laplacian + cross-array `bind()` | Per-arm `L_arm` + `M` cross-arm binding | `{L_array_k}_k` ∘ `M(bind across arrays)` |
| 2. Ring-topology decoder | `I_ring` = ℤ/8ℤ nerve ring | `I` cyclic + `L` per-array + `M` ring-bind |
| 3. CA-equivalent convolutional Laplacian | Chromatophore Turing CA (Ishida 2021) | `L` (convolutional Laplacian) on local substrate-encoder-tag |

Yes is the answer. The rest of this document is the per-direction class-chain attestation + Python pseudocode + clinical prediction + rcN+2 dependency profile.

---

## §1 — Direction 1: Per-array substrate-encoder-tagged Laplacians + cross-array `bind()`

### §1.1 The decoder-design hypothesis

Multi-array BCI substrate: multiple Utah-array clusters (e.g., BrainGate cohorts typically have 2 × 96-channel arrays in motor cortex M1; some implants extend to dorsal premotor PMd or sensory S1; Flesher et al. 2021 PMC8715714 cohort has motor + sensory arrays).

**Current canonical decoder approach:** concatenate all electrode channels into one feature vector → train a single Kalman / mRNN / LSTM decoder on the unified state. Implicit assumption: cross-array couplings carry information; unified model can learn them.

**Cephalopod-inspired alternative:** treat each array as a substrate-encoder-tagged Laplacian with its own descriptor hash, decompose per-array, then `bind()` the per-array spectral handles into a unified handle for downstream similarity-matching against intent canon.

### §1.2 Class-chain attestation

Per Spike #129 §3.3 and Spike #126 §1, the chain is:

```
{state_array_k} ─[decompose per array]→ {handle_k} ─[bind across k]→ unified_handle
                                                      (Class M)
```

Concretely:

- **Per-array decompose** (`L ∘ A`): for each array k with patient-specific connectivity Laplacian `L_array_k`, project the neural state at this timestep onto `L_array_k`'s eigenbasis via `srmech.spectral.decompose(state_k, L_array_k, encoder_tag=f"array_{k}")`. The encoder_tag folds into the descriptor hash, so each array has a separate eigenbasis cache entry per Spike #115 design.
- **Cross-array bind** (`M`): apply `srmech.amsc.hdc.bind` pairwise (or `bundle` if odd count) across `{handle_k.coefficients_bytes}` to produce the unified handle bytes. XOR self-inverse means the binding is recoverable.
- **Similarity match against intent canon** (`M`): compute `srmech.spectral.similarity(unified_handle, patient_intent_fingerprint)` against the patient's historical intent-state fingerprints.

**Full chain:** `{L_array_k ∘ A}_k ∘ M(bind) ∘ M(similarity)` — every class shipped at rc14.

### §1.3 Python pseudocode

```python
# Direction 1 — Per-array Laplacian + cross-array bind
import numpy as np
from srmech.spectral import decompose, similarity
from srmech.amsc.hdc import bind, bundle

def decode_multi_array(
    neural_states: dict[str, np.ndarray],     # array_id -> state vector
    laplacians: dict[str, np.ndarray],        # array_id -> Hermitian Laplacian
    intent_fingerprints: dict[str, bytes],    # intent_id -> canonical handle bytes
) -> tuple[str, float]:
    """Decode multi-array neural state into intent label + confidence.

    Class chain: {L_array_k ∘ A}_k ∘ M(bind) ∘ M(similarity).
    """
    # Per-array decompose with substrate-encoder-tagged Laplacian
    per_array_handles = []
    for array_id, state in neural_states.items():
        L = laplacians[array_id]
        handle = decompose(state, L, encoder_tag=f"array_{array_id}")
        per_array_handles.append(handle.coefficients_bytes)

    # Cross-array bind: pad to odd count for bundle, or chain-bind for arbitrary count
    if len(per_array_handles) == 1:
        unified_bytes = per_array_handles[0]
    elif len(per_array_handles) % 2 == 1:
        unified_bytes = bundle(per_array_handles)  # majority vote
    else:
        # chain-bind pairwise; commutativity per Spike #114 Option B guarantees order-invariance
        unified_bytes = per_array_handles[0]
        for h in per_array_handles[1:]:
            unified_bytes = bind(unified_bytes, h)

    # Match against intent canon
    best_intent, best_sim = None, -1.0
    for intent_id, fingerprint in intent_fingerprints.items():
        sim = similarity(unified_bytes, fingerprint)
        if sim > best_sim:
            best_sim, best_intent = sim, intent_id

    return best_intent, best_sim
```

### §1.4 Substrate-coupling adapter scope

**This direction IS the substrate-coupling adapter** that Milestone #14 names as its primary deliverable. The pattern:

1. Each array gets a patient-specific Laplacian descriptor (built once at calibration).
2. The descriptor hash keys an LRU eigenbasis cache per Spike #115 design (`N_MAX_EIGENBASES = 8` is sufficient for 4–8 array implants typical in published cohorts).
3. Per-array decompose runs on each timestep; eigenbases are computed once and reused (~O(n³) one-time per array vs O(n²) per state).
4. Cross-array `bind()` is O(D) where D = bit-dimension of the coefficient bytes (typically D = 8 × n × 16 = 128n bytes for complex128 coefficients of size n; with n=96 channels per Utah array, D ≈ 12 KB per array, well within HDC bind throughput).
5. Similarity match against the intent canon is also O(D) bytes per comparison.

**Substrate-coupling adapter operationally closed at rc14.** No new feature work needed. The per-array `_descriptor_hash` discipline already in srmech AMSC generalises trivially from per-patient cache keys to per-array cache keys.

### §1.5 Clinical prediction (testable)

**Prediction 1.A (decentralised decoder beats unified at low electrode yield):** at electrode yield ≤ 30% per array (per Hahn et al. 2025 PMC-extracted; mean 35.6% with 7% decline over 20-year cohort), the per-array `{L_array_k ∘ A}_k ∘ M(bind)` decoder retains motor-imagery binary-classification Cohen's d ≥ 1.0 where Kalman-filter-based unified decoder retains Cohen's d ≤ 0.5.

**Rationale:** when individual electrodes degrade, the per-array spectral handle preserves the **low-mode eigenbasis structure of that array's surviving subset** (Class K asymptotic-DOF preservation per Spike #126 §4). Cross-array `bind()` then integrates surviving information across arrays. The unified-Laplacian alternative loses the array-specific structure when channels drop out.

**Cephalopod analog:** per-arm reach precision (Sumbre et al. 2001 cite-by-ref) exceeds whole-body coordinate-frame planning at the cost of per-arm autonomy. The arms' local sensorimotor cascade is robust to local degradation; the central brain doesn't have to re-plan when an arm is partially compromised.

**Test substrate:** post-hoc reanalysis of multi-array BrainGate-like cohorts (BrainGate participant T-series datasets, where electrode-channel-dropout time-series are available) — but per `[[reference_autonomous_validation_tos_landscape]]` actual access to these datasets requires IRB / consortium partnership; cite-by-ref to Hahn 2025 PMC + Sussillo 2016 PMC describes the test substrate without exfiltration.

**Falsifier:** if a unified-Laplacian Kalman decoder maintains Cohen's d ≥ 0.8 at ≤ 30% per-array electrode yield across published BCI Competition IV-2a + IV-2b datasets, Prediction 1.A is falsified. This would suggest unified-decoder learning compensates for per-array degradation by re-weighting; the cephalopod analog would then be miss-mapped.

### §1.6 rcN+2 dependencies

- **None for Direction 1's basic decode pipeline.** Decompose + bind + similarity are all rc14-shipped.
- **`predict()` (rcN+2)** would extend Direction 1 to closed-loop bidirectional: project unified handle forward in time under cortical drift dynamics (Class L eigenvalue-based propagation), compare to next-timestep observed handle via `prediction_error()`.
- **`prediction_error()` (rcN+2)** is the bit-exact discrepancy primitive; composable as `delta(predict(handle), observe(handle))` with threshold on `popcount(delta) / D`.
- **`truncate_sparse()` (rcN+2)** would compress each per-array handle to top-k modes before bind; reduces unified-handle byte size from O(K × D_per_array) to O(K × top_k_modes), at cost of some precision (Class K asymptotic-DOF tradeoff per Spike #126 §4.4).

---

## §2 — Direction 2: Ring-topology decoder (Class I cyclic-primitive)

### §2.1 The decoder-design hypothesis

Multi-array BCI substrate with **K ≥ 3 arrays**: arrange the K substrate handles in a cyclic-group ℤ/K topology and decode via ring-bind composition rather than independent channels.

**Cephalopod analog:** Chang & Hale 2023 PMC10192654 nerve ring with **8-fold radial symmetry** — interbrachial commissures link adjacent arms in a literal ℤ/8ℤ ring topology. **Mechanosensory signals propagate bidirectionally across the ring with distance attenuation** (86.7% adjacent / 13.3% 4-arm-away). The ring is fault-tolerant: per-arm damage doesn't disconnect the rest.

### §2.2 Class-chain attestation

The chain:

```
{state_array_k}_{k ∈ ℤ/K} ─[per-array decompose]→ {handle_k}_{k}
                                       ─[ring-bind with adjacent neighbours]→ {ring_handle_k}_{k}
                                                                            ─[ring-bundle]→ unified_ring_handle
```

Concretely:

- **Per-array decompose** (`L ∘ A`): same as Direction 1.
- **Ring-bind** (`I ∘ M`): for each array k in ℤ/K cyclic group, compute `ring_handle_k = bind(handle_k, handle_{(k+1) mod K})`. This is the literal anatomical Class I instantiation from Spike #129 §3.2.
- **Ring-bundle** (`M`): `bundle(ring_handle_0, ring_handle_1, ..., ring_handle_{K-1})` produces the unified handle. If K is even, pad with a deterministic tie-breaker per `srmech.amsc.hdc.bundle` API.
- **Similarity match** (`M`): same as Direction 1.

**Full chain:** `{L_array_k ∘ A}_k ∘ {I_ring(k, k+1) ∘ M(bind)}_k ∘ M(bundle ring) ∘ M(similarity)` — every class shipped at rc14 (Class I shipped 0.4.0rc1; Class L 0.4.0rc2; Class M 0.4.0rcN).

### §2.3 Python pseudocode

```python
# Direction 2 — Ring-topology decoder (cephalopod nerve ring analog)
import numpy as np
from srmech.spectral import decompose, similarity
from srmech.amsc.hdc import bind, bundle
from srmech.amsc.cyclic import mod_add

def decode_ring_topology(
    neural_states: list[np.ndarray],          # ordered by ring position; len = K
    laplacians: list[np.ndarray],             # ordered by ring position; len = K
    intent_fingerprints: dict[str, bytes],
) -> tuple[str, float]:
    """Decode multi-array neural state via ℤ/K cyclic-group ring topology.

    Class chain: {L_array_k ∘ A}_k ∘ {I_ring ∘ M(bind)}_k ∘ M(bundle) ∘ M(similarity).
    Cephalopod analog: Chang & Hale 2023 PMC10192654 nerve ring ℤ/8ℤ.
    """
    K = len(neural_states)
    if K < 3:
        raise ValueError(f"Ring topology requires K >= 3 arrays; got K={K}")

    # Per-array decompose with ring-position encoder_tag
    handles = []
    for k, (state, L) in enumerate(zip(neural_states, laplacians)):
        handle = decompose(state, L, encoder_tag=f"ring_pos_{k}_of_{K}")
        handles.append(handle.coefficients_bytes)

    # Ring-bind: bind each handle with its adjacent neighbour (ℤ/K cyclic)
    ring_handles = []
    for k in range(K):
        next_k = mod_add(k, 1, K)  # Class I cyclic-group arithmetic
        ring_handles.append(bind(handles[k], handles[next_k]))

    # Ring-bundle: majority vote across all ring-handles
    # If K is even, pad with a deterministic tie-breaker (zero vector)
    if K % 2 == 0:
        D = len(ring_handles[0])
        ring_handles = ring_handles + [bytes(D)]  # zero vector tie-breaker
    unified_ring_handle = bundle(ring_handles)

    # Match against intent canon
    best_intent, best_sim = None, -1.0
    for intent_id, fingerprint in intent_fingerprints.items():
        sim = similarity(unified_ring_handle, fingerprint)
        if sim > best_sim:
            best_sim, best_intent = sim, intent_id

    return best_intent, best_sim
```

### §2.4 Fault-tolerance properties

The ring topology has the same **distance-attenuation propagation** documented in Chang & Hale 2023 PMC10192654 for the cephalopod nerve ring:

- A single-array dropout (e.g., array k fails or returns zeros) damages only the two ring-bind operations involving k (namely `bind(handle_{k-1}, handle_k)` and `bind(handle_k, handle_{k+1})`).
- The remaining K−2 ring-bind operations are unaffected.
- After ring-bundle majority vote, the unified handle preserves K−2 out of K ring contributions intact.
- For K ≥ 5, this means a single-array failure still leaves a 3-out-of-5 majority signal intact.

This is the **anatomical Class I fault-tolerance** Spike #129 §3.2 attests: the ring's cyclic topology tolerates per-arm damage by construction, without re-planning.

### §2.5 Clinical prediction (testable)

**Prediction 2.A (ring-topology decoder beats independent-channel at electrode-dropout):** simulate per-array dropout on a published multi-channel BCI dataset (e.g., BCI Competition IV-2a, 22-channel EEG; partition into K=4 sub-arrays of 5–6 channels each). The ring-topology decoder retains ≥ 75% of baseline accuracy at single-sub-array dropout; the independent-channel Kalman baseline retains ≤ 65%.

**Cephalopod analog:** Chang & Hale 2023 documented signal propagation persisting through partial ring damage in *Octopus bimaculoides*; the ring topology is fault-tolerant by anatomical construction.

**Falsifier:** if independent-channel Kalman + per-channel-dropout-imputation matches the ring-topology decoder accuracy within ±5 percentage points across BCI Competition IV-2a's 9 subjects, Prediction 2.A is falsified. The framework-side anatomical-analog claim survives only if the ring topology provides quantitatively superior fault tolerance.

### §2.6 rcN+2 dependencies

- **None for Direction 2's basic decode pipeline.** All operations are rc14-shipped.
- **`truncate_sparse()` (rcN+2)** would compress each per-array handle to top-k modes before ring-bind; reduces ring-handle byte size proportionally. Especially helpful at large K (e.g., K=8 cephalopod-analog).

### §2.7 Disability-accommodation dimension

For patients with **post-stroke motor cortex reorganisation**: a single-array's contribution may shift across sessions as cortical reorganisation proceeds. The ring topology's fault tolerance accommodates this by not requiring any single array to be "the canonical motor decoder" — distributed across the ring, gradual array-specific drift is absorbed via the bundle majority.

For patients with **executive-function variation (post-TBI)**: within-session attention fluctuation may manifest as transient per-array signal degradation. Ring topology + majority-vote bundle smooths over this without requiring conscious patient compensation.

---

## §3 — Direction 3: CA-equivalent convolutional Laplacian layer

### §3.1 The decoder-design hypothesis

Per electrode-array (e.g., Utah array 10×10 grid), perform **local cellular-automaton-equivalent updates** via convolutional Laplacian on the 2D electrode grid topology, then read off the local Turing-pattern coefficients as the feature vector.

**Cephalopod analog:** Ishida 2021 PMC8357167 chromatophore CA model explicitly identifies the **neighbourhood-sum filter as equivalent to a Laplacian** for the local pigment-cell state. The chromatophore network produces complex pattern dynamics via local CA rules without any centralised pattern generator.

### §3.2 Class-chain attestation

The chain:

```
electrode_array_state_grid ─[local convolutional Laplacian]→ CA_pattern_state
                                                         ─[decompose]→ pattern_handle
                                                                     ─[similarity]→ decoded_pattern_class
```

Concretely:

- **Local convolutional Laplacian** (`L`): for a 10×10 Utah array grid, build the 2D-grid graph Laplacian (each electrode is a node; nearest-neighbour edges connect adjacent electrodes; periodic BCs for cyclic version, or open BCs for canonical Utah array). This is a 100×100 sparse Laplacian, but since neighbourhood is local, the matvec is O(n × neighbourhood_size).
- **Per-step CA update**: state at time t+1 = state at time t plus convolutional-Laplacian-update (reaction-diffusion-style per Ishida 2021): `s_{t+1} = s_t + dt * (D * L @ s_t + R(s_t))` where `R(·)` is a substrate-specific non-linearity.
- **Decompose** (`L ∘ A`): `srmech.spectral.decompose(s_T, L_grid, encoder_tag="grid_ca_10x10")` after T steps of CA evolution.
- **Similarity match** (`M`): same as Directions 1 and 2.

**Full chain:** `L_grid ∘ {CA update step}^T ∘ L_grid ∘ A ∘ M(similarity)` — every class shipped at rc14. The CA update is the same Class L matvec primitive applied iteratively.

### §3.3 Python pseudocode

```python
# Direction 3 — CA-equivalent convolutional Laplacian layer
import numpy as np
from srmech.spectral import decompose, similarity
from srmech.amsc.laplacian import dense_laplacian, dense_matvec_complex

def build_grid_laplacian(rows: int, cols: int) -> np.ndarray:
    """Build 2D grid graph Laplacian for a rows×cols electrode grid (Utah-style)."""
    n = rows * cols
    edges = []
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            # right neighbour
            if c + 1 < cols:
                edges.append((i, i + 1))
            # down neighbour
            if r + 1 < rows:
                edges.append((i, i + cols))
    return dense_laplacian(edges, n)

def decode_ca_convolutional(
    array_state_grid: np.ndarray,             # (rows, cols) electrode activations
    n_ca_steps: int,                          # T iterations of CA update
    intent_fingerprints: dict[str, bytes],
    diffusion_rate: float = 0.1,
    reaction_fn=None,                          # optional substrate-specific R(s)
) -> tuple[str, float]:
    """Decode electrode-array activations via convolutional CA update + spectral handle.

    Class chain: L_grid ∘ {CA update step}^T ∘ L_grid ∘ A ∘ M(similarity).
    Cephalopod analog: Ishida 2021 PMC8357167 chromatophore Turing CA.
    """
    rows, cols = array_state_grid.shape
    n = rows * cols
    L_grid = build_grid_laplacian(rows, cols)

    # CA update steps: s_{t+1} = s_t - dt * D * L @ s_t + dt * R(s_t)
    # Signed-Laplacian-variant per Class L dissolve from former Class O (resolution 2026-05-16)
    s = array_state_grid.flatten().astype(np.complex128)
    dt = 1.0  # canonical timestep; substrate-tunable
    for _ in range(n_ca_steps):
        diffusion = dense_matvec_complex(L_grid.astype(np.complex128), s)
        # Sign convention: diffusion smooths; Laplacian L = D - A is positive semi-definite,
        # so s_{t+1} = s_t - dt * D * L @ s_t.
        s = s - dt * diffusion_rate * diffusion
        if reaction_fn is not None:
            s = s + dt * reaction_fn(s)

    # Decompose post-CA state on same grid Laplacian
    handle = decompose(s, L_grid, encoder_tag="grid_ca_pattern")

    # Match against intent canon (intent fingerprints are decompose() handles over same Laplacian)
    best_intent, best_sim = None, -1.0
    for intent_id, fingerprint in intent_fingerprints.items():
        sim = similarity(handle.coefficients_bytes, fingerprint)
        if sim > best_sim:
            best_sim, best_intent = sim, intent_id

    return best_intent, best_sim
```

### §3.4 Edge-device deployability

**Per `[[feedback_no_binding_layer_carveout]]`**: Class L's pi-free dense Jacobi eigenvalue surface (shipped 0.4.0rc2; cap n ≤ 256 on native C path) supports the 10×10 = 100-node grid Laplacian directly on microcontroller-class targets. No LAPACK dependency. The CA update is a Class L matvec composition shipped at the C level.

**Bedside / wheelchair / wearable hardware deployment:** the chain `L_grid ∘ {CA update}^T ∘ L_grid ∘ A ∘ M(similarity)` is microcontroller-deployable today. The EMDR firmware at the repo root runs on a Seeed XIAO ESP32-C6 (RISC-V single-core @ 160 MHz, 512 KB SRAM, 4 MB Flash) — the same hardware-class would support a 10×10 grid CA decoder with all rc14 primitives.

For larger arrays (e.g., 16×16 = 256 nodes, the native bound), Class L still applies; for arrays larger than 256 nodes, fallback to numpy / scipy at the Python layer per laplacian.py's MAX_NATIVE_NODES bound.

### §3.5 Clinical prediction (testable)

**Prediction 3.A (CA-equivalent decoder at edge-device latency):** the Direction 3 decoder achieves intent decoding within 10 ms end-to-end on a 100-node Utah array grid on ESP32-C6-class hardware (160 MHz RISC-V single-core, 512 KB SRAM), enabling closed-loop BCI control without a host computer in the loop.

**Rationale:**
- Grid Laplacian build: O(n) edges, one-time at calibration.
- Per CA-update matvec: O(n × neighbourhood_size) = O(n) for nearest-neighbour grid; ~100 ops for n=100.
- T = 10 CA steps: ~1000 ops.
- Decompose at end: O(n³) Jacobi eigvals = O(10⁶) ops; cached after first call per Spike #115 design.
- Per-state coefficient projection: O(n²) = 10⁴ ops.
- Similarity match over K intent canon entries: O(K × D) bytes; for D = 100 × 16 = 1600 bytes per handle, K = 8 intents, ~12,800 popcount ops.

Total per-step: ~1.5 × 10⁴ ops on cached eigenbasis. At 160 MHz with 10 cycles/op typical for embedded float, ~10⁻⁴ s = 0.1 ms. Even with 100× safety margin for real ESP32-C6 NumPy-free implementation, < 10 ms is achievable.

**Cephalopod analog:** chromatophore Turing-CA pattern generation in *Octopus vulgaris* skin runs sub-second locally via peripheral circuits — Ishida 2021 PMC8357167 explicit. The cephalopod proves that local CA-equivalent computation can produce complex pattern dynamics without centralised control.

**Falsifier:** if any of the following hold, Prediction 3.A is falsified:
1. Direction 3's decode latency exceeds 10 ms on ESP32-C6-class hardware (benchmark target).
2. The CA-pattern-state spectral handle is provably less discriminative than the raw state spectral handle (i.e., the CA evolution destroys information rather than amplifying it).
3. The reaction-diffusion non-linearity `R(·)` is required to be patient-specific to a degree that breaks the cephalopod-analog (i.e., Ishida's substrate-agnostic R doesn't transfer).

### §3.6 rcN+2 dependencies

- **None for Direction 3's basic decode pipeline.** All operations are rc14-shipped.
- **`predict()` (rcN+2)** would extend Direction 3 to forecast the CA pattern at future timesteps; useful for closed-loop control.
- **`prediction_error()` (rcN+2)** would gate "is the CA pattern still consistent with intent canon?" — useful for hallucination-gate (Spike #126 §5) variants on AAC.

### §3.7 Pi-free + microcontroller compatibility

Per `[[user_stance_pi_as_projection]]`: the grid Laplacian's eigenvalues are pi-bearing in closed form (the standard result for a cycle graph is `λ_k = 2(1 − cos(2πk/n))`), but **Class L's shipped Jacobi eigvals computes the spectrum algebraically without involving pi**. Per laplacian.py module docstring, "the closed-form spectrum of a cyclic graph is pi-bearing and NOT shipped on the C surface; users computing cyclic-graph spectra should compose Class I (cyclic-group representation, pi-free modular arithmetic) with Class L's dense-Laplacian build + Jacobi eigvals."

For Direction 3, the same discipline applies: we **build the Laplacian symbolically** (edges only; no pi), and compute eigenvalues numerically via Jacobi rotations. The decoder is pi-free; it runs on substrates where pi is not a primitive.

This is the **substrate-agnostic property** the cephalopod analog requires — the chromatophore CA in *Octopus vulgaris* skin doesn't use pi either; it uses local pigment-cell state and motoneuron firing rates.

---

## §4 — Class chain summary across all three directions

```
Direction 1: {L_array_k ∘ A}_k ∘ M(bind) ∘ M(similarity)
Direction 2: {L_array_k ∘ A}_k ∘ {I_ring ∘ M(bind)}_k ∘ M(bundle) ∘ M(similarity)
Direction 3: L_grid ∘ {L_grid matvec}^T ∘ L_grid ∘ A ∘ M(similarity)
```

**Composite primitive use:**

| Class | Direction 1 | Direction 2 | Direction 3 |
|---|---|---|---|
| **L** (graph Laplacian) | per-array (K calls) | per-array (K calls) | grid + T matvecs |
| **A** (SHA-256 content addressing) | per-array descriptor hash | per-array descriptor hash | grid descriptor hash |
| **M** (HDC bind) | cross-array bind | ring-bind + ring-bundle | direct similarity |
| **I** (cyclic group) | not used | ring-pos arithmetic | not used (could close grid for periodic BCs) |
| **C** (cascade orientation) | implicit in handle sequence | implicit | implicit |

All four classes A / L / I / M are shipped at srmech v0.4.1rc14. **Zero new primitive classes required.**

---

## §5 — Decoder feasibility verdict

| Direction | Feasibility on rc14 | rcN+2 enhancement |
|---|---|---|
| 1. Per-array Laplacian + cross-array bind | **FEASIBLE — substrate-coupling adapter scope CLOSED** | `predict` / `prediction_error` for closed-loop |
| 2. Ring-topology decoder | **FEASIBLE** | `truncate_sparse` for large-K compression |
| 3. CA-equivalent convolutional Laplacian | **FEASIBLE — edge-deployable** | `predict` / `prediction_error` for forecast-gating |

**Composed verdict: ALL-3-DIRECTIONS-FEASIBLE-ON-RC14.**

The three directions complement each other:

- Direction 1 = **substrate-coupling adapter pattern**; closes Milestone #14 substrate-adapter scope.
- Direction 2 = **fault-tolerance specialisation**; complements Direction 1 for multi-array implants with K ≥ 3.
- Direction 3 = **edge-deployment specialisation**; complements Directions 1 + 2 for bedside / wearable hardware.

A clinical deployment would compose all three: per-array CA-Laplacian preprocessing (Direction 3) → per-array spectral handle (Direction 1's decompose) → ring-bind for fault tolerance (Direction 2). The composed chain is:

```
{array_grid_state_k} ─[Direction 3 CA-Laplacian per array]→ {pattern_state_k}
                                                ─[Direction 1 per-array decompose]→ {handle_k}
                                                                ─[Direction 2 ring-bind]→ unified_ring_handle
                                                                                       ─[M similarity]→ decoded_intent
```

This composed chain is **executable today on rc14 surface**.

---

## §6 — Milestone #14 implications

### §6.1 Does this spike close the substrate-coupling-adapter scope?

**Yes — operationally.** The substrate-coupling adapter is identified by `[[user_stance_ai_necessary_for_bci_substrate_coupling]]` as the patient-specific cortical-Laplacian adapter that mediates between raw neural state and the runtime spectral surface. Direction 1 is **exactly** this adapter, with the substrate-encoder-tag discipline already shipped in srmech AMSC providing the per-array descriptor-hash cache keys.

What rc14 closes:
- Per-array substrate-coupling adapter (Direction 1).
- Per-array drift tracking via `delta()` (already shipped per Spike #126 §2).
- Cross-array binding via `bind()` (already shipped).
- Intent canon similarity matching via `similarity()` (already shipped).

What rcN+2 closes:
- Closed-loop predict / prediction_error (intent verification per Spike #126 §3).
- Top-k truncation for SNR-floor preservation (Spike #126 §4).

What remains for clinical-grade deployment beyond rcN+2:
- n-gram-aware decompose variant (Spike #125.1; falsified-by-unigram per Spike #125 PR #522).
- Spike-train-native Laplacian builder (Spike #126 §10 refinement (b)).
- HIPAA-compliant attestation block extension (Spike #126 §10 refinement (d)).

**Operationally: substrate-coupling adapter scope CLOSED by Direction 1 on rc14.** Strategic-grade clinical deployment requires the refinements above.

### §6.2 Three publishable framework predictions carrying forward

Per `[[user_stance_ai_necessary_for_bci_substrate_coupling]]` §VIII.24, MS #14 carries three publishable framework predictions with falsifiers. This spike adds three more:

| # | Prediction | Direction | Falsifier |
|---|---|---|---|
| 4 | Per-array decoder beats unified at ≤ 30% electrode yield (Cohen's d ≥ 1.0 vs Kalman d ≤ 0.5) | 1 | unified-Kalman maintains d ≥ 0.8 at ≤ 30% yield |
| 5 | Ring-topology decoder retains ≥ 75% accuracy at single-array dropout (vs ≤ 65% for independent-channel baseline) | 2 | independent-channel + dropout-imputation matches within ±5pp on BCI Competition IV-2a |
| 6 | CA-equivalent decoder achieves intent decoding in ≤ 10 ms on ESP32-C6-class hardware for 100-node Utah grid | 3 | benchmark exceeds 10 ms, or CA evolution provably destroys discriminability |

Each prediction has a clean class-chain attestation + clinical-substrate scope + concrete falsifier.

### §6.3 Cross-spike convergence (Spike #126 + #129 + #129.1)

The three spikes form a coherent arc:

- **Spike #126** establishes that rc14 surface supports BCI clinical primitives (5/5 buckets verified; 10/10 testable predictions with falsifiers).
- **Spike #129** establishes that the same primitives instantiate the cephalopod decentralised-substrate cascade (anatomical Class I in nerve ring is the strongest available cascade attestation).
- **Spike #129.1** (this spike) establishes that the cephalopod-inspired decoder design directions are executable on the same rc14 surface.

**Cumulative verdict:** the rc14 runtime spectral surface (`decompose` / `delta` / `recompose` / `similarity`) composed with AMSC primitives (L / I / M / C / A) is **operationally sufficient for the substrate-coupling adapter at multi-array decentralised electrode-array BCI**, with rcN+2 closing the closed-loop bidirectional cases.

---

## §7 — What's NOT this spike (scope discipline)

- **No new primitive class.** 14-class A–N vocabulary stands per `[[feedback_no_privileged_primitive_classes]]`.
- **No empirical validation on real BCI data.** This is a feasibility analysis + Python proof-of-concept; actual validation requires IRB-mediated dataset access. Spike #126.1 (BCI Competition IV-2a replication) is the next-stage empirical-validation spike per Spike #126 §12.
- **No CAD-grade hardware modelling** per `docs/srmech/CLAUDE.md` algebra/eigenbasis-only ban.
- **No targeting / capability-assessment** per `[[feedback_trauma_informed_defensive_scope]]`. Every direction is restoration-of-function for motor-impaired patients.
- **No clinical-trial design.** This spike maps framework primitives to design directions; actual trial design requires IRB / clinician partnership.
- **No patient-data handling.** All examples use synthetic data; PHI handling is downstream implementation.
- **No lineage claims** per `[[feedback_no_lineage_claims_in_notebook]]`. Cephalopod biology citations (Hochner / Chang / Hale / Ishida / Olson / Levy / Sumbre / Carls-Diamante) and BCI citations (Sussillo / Hahn / Card / Cai / Flesher / Hughes) are technical; no "natural extension of researcher X" framing.

---

## §8 — Fermata records (for conductor)

1. **MS #14 substrate-coupling adapter scope is operationally addressable on rc14.** Direction 1's class chain `{L_array_k ∘ A}_k ∘ M(bind) ∘ M(similarity)` IS the substrate-coupling adapter pattern per `[[user_stance_ai_necessary_for_bci_substrate_coupling]]`. No new feature work needed for the adapter itself; rcN+2 closes closed-loop predict / prediction_error / truncate_sparse for clinical-grade bidirectional bcomms.
2. **Three new publishable predictions (4 / 5 / 6 above) compose with the three already in `[[user_stance_ai_necessary_for_bci_substrate_coupling]]`.** Cumulative book-chapter target: six predictions with falsifiers from Spike #126 + #129.1; ten total when including the testable-clinical-prediction list from Spike #126 §7. Strong empirical-validation surface for MS #14 deliverables.
3. **Spike #126.1 candidate (BCI Competition IV-2a empirical replication)** is the natural next-step empirical-validation spike per Spike #126 §12 fermata 4. Direction 1's chain + Direction 2's ring-topology variant could both be tested on BCI Competition IV-2a's 9 subjects × 22-channel EEG dataset (publicly available; permitted-source). Autonomous-followup-authorised per `[[feedback_autonomous_research_followup_authorization]]`.
4. **Spike #129.2 candidate (joint cephalopod + Physarum decoder design)** could synthesise Spike #127 + #129 + #129.1 into a unified decentralised-substrate cascade decoder design — but this is scope-defining direction; requires explicit user direction per stance-vocabulary boundary.
5. **CA-equivalent decoder + EMDR firmware cross-project bridge:** the ESP32-C6 hardware platform at the repo root is **the same hardware class** as the CA-Laplacian Direction 3 deployment target. Cross-project bridge: rc14's pi-free Class L surface deploys on the EMDR firmware substrate. **Out of scope for srmech subtree edits** per `docs/srmech/CLAUDE.md` "don't touch src/ / test/ / platformio.ini"; recorded for conductor awareness.
6. **Substrate-coupling adapter pattern strengthens `[[user_stance_substrate_identity_partition_coexistence_canonical]]`.** Direction 1's per-array decomposition IS the partition operation; cross-array bind IS the coexistence operation. The framework primitive `srmech.amsc.hdc.bind` is operationally the realisation of partition-coexistence at the BCI substrate level.

---

## §9 — Files produced

1. `docs/srmech/notes/spike129_1_decentralised_bci_decoder_feasibility.md` (this file)
2. `docs/srmech/notes/spike129_1_findings_2026-05-18.ndjson` (NDJSON findings)
3. `docs/srmech/notes/spike129_1_decoder_sketch.py` (Python proof-of-concept invoking srmech.spectral primitives on synthetic neural data)

---

## §10 — Refs

Task `#543`. Parent spike: `#129` (PR #538). Parent stance: `[[user_stance_ai_necessary_for_bci_substrate_coupling]]`. Milestone: `#14`.

**Clinical literature (PMC-extracted from Spike #126; re-used by reference)**:
- Sussillo et al. 2016 — Nat Commun 7:13749 / arXiv:1610.05872 — multiplicative RNN robust decoder
- Hahn et al. 2025 — medRxiv 10.1101/2025.07.02.25330310 — BrainGate 14-participant 20-year Utah array
- Card et al. 2024 — medRxiv 10.1101/2023.12.26.23300110 — ALS speech neuroprosthesis
- Cai et al. 2024 — Nat Commun 15:9449 (PMC11530652) — SpeakFaster LLM-AAC

**Cephalopod biology (PMC-extracted from Spike #129; re-used by reference)**:
- Olson, Schulz, Ragsdale 2025 — Nat Commun (PMC11736069) — neuronal segmentation in cephalopod arms
- Chang & Hale 2023 — iScience (PMC10192654) — mechanosensory signal transmission via nerve ring
- Ishida 2021 — PLoS One (PMC8357167) — chromatophore Turing CA model
- Carls-Diamante 2022 — Front Syst Neurosci (PMC8988249) — octopus distributed cognition
- Levy & Hochner 2017 — Front Physiol (PMC5368235) — octopus motor primitives composition
- Zullo et al. 2019 — J Comp Physiol A (PMC6478645) — octopus arm en-passant motor recruitment

**Framework anchors**:
- srmech v0.4.1rc14 ([PR #519](https://github.com/lemonforest/mlehaptics/pull/519)) — runtime spectral surface
- Spike #115 ([PR #518](https://github.com/lemonforest/mlehaptics/pull/518)) — 7-entry surface design
- Spike #126 ([PR #526](https://github.com/lemonforest/mlehaptics/pull/526)) — BCI clinical applicability
- Spike #129 ([PR #538](https://github.com/lemonforest/mlehaptics/pull/538)) — octopus distributed cognition cascade-match VERIFIED
- Spike #114 — HDC Option B Direct bind on encoded bytes
- Spike #117 ([PR #517](https://github.com/lemonforest/mlehaptics/pull/517)) — eigenbasis-state-correlation lesson

**Memory anchors**:
- `[[user_stance_ai_necessary_for_bci_substrate_coupling]]` — Milestone #14 anchor
- `[[user_stance_substrate_identity_partition_coexistence_canonical]]`
- `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`
- `[[user_stance_identity_not_implementation_discipline]]`
- `[[user_stance_kepler_shape_universal]]`
- `[[user_stance_epicycle_via_gear_plus_pin]]`
- `[[user_stance_asymptotic_dof_sidesteps_infinity]]`
- `[[user_stance_pi_as_projection]]`
- `[[feedback_no_privileged_primitive_classes]]`
- `[[feedback_no_mvp_framing]]`
- `[[feedback_no_binding_layer_carveout]]`
- `[[feedback_science_is_ssot_not_project]]`
- `[[feedback_trauma_informed_defensive_scope]]`
- `[[feedback_disability_accommodation_dimension]]`
- `[[feedback_pdf_extraction_citation_discipline]]`
- `[[feedback_no_lineage_claims_in_notebook]]`
- `[[feedback_autonomous_research_followup_authorization]]`
- `[[feedback_estimation_calibration_outlier_velocity]]`
- `[[feedback_ndjson_over_bloated_json]]`
- `[[reference_autonomous_validation_tos_landscape]]`
