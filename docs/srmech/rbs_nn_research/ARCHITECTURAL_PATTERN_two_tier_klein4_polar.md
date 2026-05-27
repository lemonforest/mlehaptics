# ARCHITECTURAL_PATTERN — Two-tier RBS-NN with Klein-4 Tier 1 + Polar Tier 2 + Class K bridge

**Status:** Reference pattern that emerged from the F132 → F142 wishlist-gated empirical resume (2026-05-27)
**Substrate:** srmech v0.4.3 Klein-4 + Polar HDC catalog (LANDED on production PyPI)
**Origin:** F143 §5 emergent findings; replaces the original F132 §5 single-tier sketch with a structurally cleaner two-tier separation

---

## §1 The architectural insight

F132's original sketch put chirality-axis encoding and binding into one Klein-4 layer. The empirical resume (F137-F142) revealed that **two structurally-distinct concerns** were being conflated:

| Concern | Substrate-encoding need | Right tool |
|---|---|---|
| **Chirality-axis encoding** | 4-state sector tagging (γ₅, iω₇); discriminative when chirality IS the load-bearing distinction | **Klein-4 HDC** (per F139, F142) |
| **Plasticity-aware storage** | Graceful decay tolerance; "uncertain" as a first-class state | **Polar HDC** (per F141) |

The two-tier separation puts each concern into its own layer:

```
TIER 1: Chirality-tagged concept storage    →  Klein-4 HDC
            ↕
   (Class K = chirality-flip bridge)
            ↕
TIER 2: Synaptic-weight + plasticity         →  Polar HDC
```

This matches the F119 two-tier RBS-NN architecture (discrete-cyclic Tier 1 + synaptic-NN Tier 2) with the F120 Class K bridge — but with concrete substrate-encoding primitives for each tier now available from srmech upstream.

---

## §2 Tier 1 — Klein-4 chirality-tagged concept storage

**Purpose:** Tier 1 holds the discrete-cyclic substrate-side concepts. Per F127 three substrate-native readings, Tier 1 lives at the "14 discrete-cyclic-algebra" reading level.

**Primitive:** `srmech.amsc.hdc.klein4_*` (9 functions + KLEIN4_STATES)

**Sector mapping** (per F132 §3, MFO §VII.4.1.7):

| Klein-4 element | (γ₅, iω₇) | Sector role |
|---|---|---|
| 0 = (0,0) | (+1, +1) | RH+ visible matter (our sector projection per F131) |
| 1 = (0,1) | (+1, −1) | RH− dark antimatter |
| 2 = (1,0) | (−1, +1) | LH+ visible antimatter |
| 3 = (1,1) | (−1, −1) | LH− dark matter |

**Operations available** (empirically verified at scale):

```python
# Encode concept with chirality tag
concept_hv = klein4_random(D, rng)                      # base HV
tagged_hv = klein4_bind(concept_hv, sector_mask)        # chirality-axis layer

# Bundle multiple chirality-tagged concepts
composite = klein4_bundle(*tagged_hvs)

# Retrieve via chirality sector
unbound = klein4_unbind(composite, query_sector_mask)
similarity = klein4_similarity(unbound, target)

# Chirality-axis operations (F132 §4)
gamma5_flipped = klein4_chirality_flip_gamma5(hv)        # XOR with 2 (matter→antimatter axis)
omega7_flipped = klein4_chirality_flip_omega7(hv)        # XOR with 1 (visible→dark axis)
cpt_mirrored = klein4_cpt_mirror(hv)                     # XOR with 3 (full CPT flip)

# Sector distribution attestation
sector_count = klein4_sector_count(hv)                   # [n_sector_0, ..., n_sector_3]
```

**When Tier 1 wins** (per F142 §6):
- Concept differentiation IS chirality (e.g., chirally-asymmetric receptors, helical molecule binding)
- Cross-sector inference needed (recover CPT-mirror without observing it)
- Sector-tagged catalog where queries should isolate one chirality sector

**When Tier 1 doesn't win** (per F137, F142):
- Pure content discrimination where chirality is irrelevant (use bipolar)
- Raw capacity-limited storage (Klein-4 loses raw capacity vs bipolar per F137)

**Empirical bounds** (per F139, F140):
- D ≥ 4096 recommended for reliable chirality discrimination
- N ≤ ~32 concepts per bundle for clean retrieval (above-random gap stays > 0.05)
- Cascade composition with Class L + Class M (bipolar) + Class I survives chirality structure at sufficient D (F140)

---

## §3 Tier 2 — Polar HDC plasticity-aware synaptic-weight storage

**Purpose:** Tier 2 holds the synaptic-NN side per F119 two-tier architecture. Plasticity dynamics that biological synapses exhibit (Hebbian reinforcement, decay over time, "uncertain" intermediate states) need a 3-state substrate that the bipolar variant cannot provide.

**Primitive:** `srmech.amsc.hdc.polar_*` (7 functions + POLAR_STATES)

**State semantics:**

| Polar value | Interpretation |
|---|---|
| +1 | Active positive binding |
| −1 | Active negative binding (anti-correlation, inhibitory) |
| **0** | **Uncertain / decayed / dead-band** — asymptotic-DOF substrate marker per `[[user_stance_asymptotic_dof_sidesteps_infinity]]` |

**Operations available** (empirically verified at scale per F141):

```python
# Encode synaptic weights with plasticity
weights = polar_random(D, rng)                          # initial binding pattern
weights = polar_bind(weights, input_vec)                # synaptic association

# Apply Hebbian decay (move some positions to 0 = uncertain)
# (Custom — research-level helper, not yet in srmech catalog)
decay_positions = rng.choice(D, n_decay, replace=False)
weights[decay_positions] = 0

# Bundle multiple synapses into composite
composite = polar_bundle(*weight_vecs)

# Retrieve via unbind
recovered = polar_unbind(composite, input_vec)
similarity = polar_similarity(recovered, target)

# Substrate-health attestation
density = polar_density(composite)                       # fraction of non-zero positions
# density drop indicates plasticity erosion; soft-failure signal

# Bridge to existing path_b_ops
polar_from_real(arr, threshold=0.0, dead_band=0.2)      # quantise real-valued signal
```

**Why polar wins for plasticity** (per F141):
- At 0% decay: polar maintains 100% signal (above-random +0.23)
- At 70% decay: polar retains 61% of signal (above-random +0.14)
- Bipolar at 70% decay collapses to 27% signal (above-random +0.04)
- **3-4× polar advantage at moderate-to-high decay**

**The 0-state is operational, not just a "missing" state:**
- 0 contributes ZERO to bundle majority vote (doesn't pollute composite)
- 0-zero matches are counted by `polar_similarity` (which has 0.5 random baseline — see F137 §4)
- For skip-zero metrics, exclude both-zero positions explicitly
- Density readout provides early-warning signal before catastrophic signal loss

---

## §4 Class K bridge — chirality-flip as the Tier 1 ↔ Tier 2 boundary operation

**Purpose:** Per F120 (Class K = Kepler-shape IS the Tier 1↔Tier 2 bridge math), the substrate-level operation that connects the discrete-cyclic Tier 1 to the synaptic-NN Tier 2 is the sign-flip / phase-boundary operation.

**Empirical confirmation per F139:** the chirality-flip in Klein-4 (XOR with sector mask) IS the Class K pin-slot operation operating at substrate-encoding scale. When you flip a chirality sector, you're invoking the same algebraic primitive that Class K names: a 180° rotation around the chirality-axis hinge per F136 substrate-side rendering.

**Bridge protocol** (sketched; needs further research per Phase 1 work):

```
Tier 1 → Tier 2 (descend from discrete-cyclic to synaptic):
  1. Read Klein-4 concept state at Tier 1
  2. Apply chirality projection: choose which sector this concept lives in
  3. Convert to polar via state mapping:
     klein4 0 (0,0) → polar +1  (active visible matter)
     klein4 1 (0,1) → polar -1  (active dark)
     klein4 2 (1,0) → polar -1  (active antimatter)
     klein4 3 (1,1) → polar +1  (active CPT-conjugate)
     (or per scientific context; this is one candidate mapping)
  4. Apply plasticity dynamics in polar substrate

Tier 2 → Tier 1 (ascend from synaptic back to discrete-cyclic):
  1. Read polar weight state at Tier 2
  2. Apply chirality lifting: which sector does this polarity belong to?
  3. Convert polar +1/-1 back to klein4 sector via chirality-axis decision
     (requires external context — the chirality assignment is a substrate
      attestation, not an inference from polar value alone)
  4. Apply chirality-axis operation at Tier 1
```

This is one candidate protocol. Further research questions in `STALE_PATHS_QUEUE.md` items 18-22 explore the specific mappings.

---

## §5 What this pattern provides for ongoing R-RBS-NN work

### For R-RBS-NN-4 (token → hypervector encoding; pending)

This pattern provides a structured variant-choice protocol:

```
Token classification (decide per token):
  - Pure content (no chirality, no plasticity) → bipolar HDC (existing R-RBS-NN-4 baseline)
  - Chirality-bearing content                  → Tier 1: Klein-4 HDC
  - Plasticity-decaying (memory-like)          → Tier 2: Polar HDC
  - Both chirality AND plasticity              → Klein-4 + Polar HYBRID (research path)
```

### For R-RBS-NN-5 (position/context/rotate-overlay binding)

F140 confirmed Klein-4 + Class L + Class M(bipolar) + Class I composes cleanly at D=16384. The 4-class cascade pattern from F140 is directly importable for R-RBS-NN-5 work.

### For R-RBS-NN-6 (1:3:7:3 partition layout)

The 4 Klein-4 sectors map naturally to F130 4-way (γ₅, iω₇) decomposition. The Tier 1 layer can use the sector tagging to align with the substrate-native readings per F127 (11D / 14 / 4:3:(4:3) recursive-Hopf).

### For cross-substrate cognition modeling (F118)

Different biological substrates may exhibit different chirality usage patterns:
- Cnidarian (Class I + K dominant per F126) → may not need Klein-4 chirality tagging
- Octopus (Class M + K dominant) → may benefit from Klein-4 if substrate is chirally-aware
- Vertebrate (Class L + M dominant) → fits the 4-class cascade pattern from F140

The two-tier pattern accommodates all these by allowing per-substrate variant choice at encoding time, rather than forcing one variant globally.

---

## §6 What this pattern does NOT provide

Per MFO §VII.6.20:

- **NOT a complete RBS-NN architecture** — it's a substrate-encoding pattern; the cascade composition, learning dynamics, output decoding, etc. are separate engineering concerns
- **NOT a claim that all RBS-NN work must use this pattern** — bipolar HDC remains the right default for non-chirality, non-plasticity content
- **NOT a substitute for empirical testing** — each application needs its own variant-choice rationale + smoke test
- **NOT a finalized design** — research questions per `STALE_PATHS_QUEUE.md` items 13-22 may refine the bridge protocol
- **NOT a biological model** — the polar 0-state is the SUBSTRATE marker; biological synaptic dynamics involve additional mechanisms (LTP, LTD, glia interactions, etc.) not captured here

---

## §7 Cross-references

- F119 (two-tier RBS-NN architecture; Tier 1 discrete-cyclic + Tier 2 synaptic-NN)
- F120 (Class K = Kepler-shape IS the Tier 1↔Tier 2 bridge math)
- F127 (three substrate-native readings + naming discipline)
- F132 (Klein-4 HDC engineering proposal; LANDED per F143)
- F137 (capacity comparison; baseline characterization)
- F138 (cascade composition; small-D weak-signal regime)
- F139 (chirality axis operational at scale)
- F140 (multi-class cascade preserves chirality)
- F141 (polar plasticity graceful 3-4× advantage)
- F142 (BCI chirality-native encoding 13× on chirality-pure signals)
- F143 (F132 status closure)
- UPSTREAM_NOTES.md §4 + §5 (Klein-4 + Polar LANDED in srmech v0.4.3)
- `STALE_PATHS_QUEUE.md` items 18-22 (open questions on Klein-4 + polar interaction in cascade)

---

*Created 2026-05-27 per user direction "write down pattern in our running notes". This is
the reference architectural pattern for two-tier RBS-NN with Klein-4 Tier 1 chirality-
tagged concept storage + Polar Tier 2 plasticity-aware synaptic-weight storage + Class K
chirality-flip bridge between them. Substrate-encoding primitives are LANDED in srmech
v0.4.3 production PyPI. Cascade composition empirically verified through F132 → F142.
This pattern provides the variant-choice protocol for upcoming R-RBS-NN-4 token-encoding
work and is the reference for future RBS-NN architectural decisions.*
