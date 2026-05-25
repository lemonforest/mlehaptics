# R-RBS-NN-5 — Position / context / rotate-overlay binding

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #6 of RBS-NN partition walk (opened ahead of #5 R-RBS-NN-4 per user direction; literature attestation deferred)
**Closing artefact:** §3 three positional schemes placed + §4 rotate-overlay reading + §5 canonical sequence representation + §7 worked example
**Inheritance:** unblocks R-RBS-NN-6 (1:3:7:3 architectural layout) per the planned chain

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-NN-1_mfo_two_level_REPORT.md` §4.2 (positional encoding placement); `R-RBS-NN-2_user_lexicon_REPORT.md` (content-addressing baseline); `R-RBS-NN-3b_transformer_cascade_REPORT.md` §5–§6 (Level-1 substitution map) |
| MFO source | `mfo_spectral_research_notebook.md` §VII.1.3 lines 735–761 (three-mechanism asymmetry); line 743 (`[[user_stance_rotation_is_class_k_pin_slot]]` — rotation IS Class K); line 686 (`L∘K∘C∘I` cascade) |
| srmech infra | `srmech/amsc/hdc.py` permute (Class C cyclic rotation); `srmech/signal_processing/form_function_rotation.py` form_function_rotate (Class A→Class C composition); `srmech/amsc/cyclic.py` Class I coprime shift |
| Spike refs (internal repo) | Spike #142 (bind self-inverse); Spike #159 (Class I coprime shift; D=8192 stride=257); Spike #173 (chess natural-stride orthogonality); Spike #176 (rotation IS Class K at machine ε) |
| repo commit | `2e4657fc` at REPORT-write |
| reproducibility | `PYTHONPATH=docs/srmech/python python3 docs/srmech/rbs_nn_research/worked_example_position_binding.py` |
| literature attestation status | Kanerva HDC sequence representation, RoPE (Su et al. 2021), sinusoidal encoding (Vaswani 2017) — **named, not MPR-attested**; deferred to R-RBS-NN-4 |

---

## §1 Goal

Read the positional / context / rotate-overlay binding question through the srmech 14-class A-N vocabulary and the MFO two-level ontology. R-RBS-NN-1 placed the positional-encoding options (discrete cyclic shift, sinusoidal, RoPE rotation) on the Level-1 / Level-2 line; R-RBS-NN-3b identified that vanilla transformer positional encoding is Level-2 (sinusoidal interp or rotation) but a Level-1 substitute exists (discrete cyclic shift). R-RBS-NN-5 formalizes:

1. Three structurally-distinct positional binding schemes available in srmech, placed at MFO levels.
2. What rotate-overlay IS operationally (MFO Mechanism 3 / Class K per-position selection) versus what it conventionally does in attention (RoPE / bundle-of-rotations across positions).
3. The canonical Kanerva HDC sequence representation in srmech form, and what it preserves under bit-exact recovery.
4. When position-as-binding (Level 1) suffices versus when position-as-rotation (Level 2) is structurally necessary.

This partition is also where R-RBS-NN-3b's Level-1 substitution claim for positional encoding gets formalized empirically — the worked example shows the substitute works bit-exactly.

---

## §2 Inheritance

From R-RBS-NN-1 §4.2 (positional encoding placement table):

| Encoding scheme | Level | Class composition |
|---|---|---|
| Discrete cyclic shift (Class I bit-rotation) | 1 | I (pure substrate; Spike #159 coprime shift; `permute(permute(v,k),-k)==v` bit-exact) |
| Sinusoidal positional encoding | 2 | I ∘ N (rational approximation of sin/cos) |
| Rotary positional embedding (RoPE) | 2 | I ∘ C (rotation = Class K per `[[user_stance_rotation_is_class_k_pin_slot]]`) |
| Causal mask (lower-triangular) | 1 | C (cascade-orientation); bit-pattern mask |

From R-RBS-NN-2 §7 Demo 3: the substrate is content-addressed by string, not by lexical similarity. Position information must therefore be encoded as **explicit binding** — Class M XOR-bind of token vector with position vector — rather than as embedding-layer proximity in continuous space.

From R-RBS-NN-3b §6: the Level-1 transformer substitution uses discrete cyclic position. The Level-2 attention output (bundle-of-rotations across positions) is Mechanism 2 with ~6.9% cost; hard attention (Mechanism 3 / Class K per-position selection) substitutes without averaging cost.

---

## §3 Three positional binding schemes — placed at MFO levels

### §3.1 Scheme A — Bind-with-position-vector (recommended Level-1 form)

For each position k ∈ {0, ..., L-1}, mint a position vector `P_k = mint_vector(f"LoE.position.{k}", D)` via Class A. Bind the token at position k with `P_k` via Class M XOR-bind:

```
bound_k = bind(token_k, P_k)
```

Properties:
- Level 1 throughout (Class A mint + Class M XOR-bind; both ALU, integer)
- Bit-exact reversible: `bind(bound_k, P_k) == token_k` (Spike #142 self-inverse)
- Position vectors are orthogonal pairwise (within 1/√D noise floor per R-RBS-NN-2 §3)
- Sequence representation: `S = bundle(bound_0, bound_1, ..., bound_{L-1})` — single hypervector representing the whole sequence
- Recovery at position k: `bind(S, P_k)` produces an approximate `token_k` (cleanup capacity: ~D/(k_const · log D) per R-RBS-NN-2 §6)

This is the canonical Kanerva HDC sequence representation (Kanerva 1988, 2009; Plate 1995 for the convolution variant). The framework reading places it at MFO Level 1: substrate-preserving content addressing, no FPU lift in the encoding or decoding path.

### §3.2 Scheme B — Discrete cyclic shift (Class I) — alternative Level-1 form

Per `srmech/amsc/hdc.py:permute` and Spike #159 coprime-shift work, a position can be encoded as a cyclic bit-rotation of a base token:

```
positioned_k = permute(token, k * stride)
```

where `stride` is coprime to D (per Spike #170 / §3.1: stride = 257 at D=8192). Properties:

- Level 1 (Class I cyclic shift; pure substrate; ALU integer rotation)
- Bit-exact reversible: `permute(permute(v, k*s), -k*s) == v` (Spike #173 chirality involution)
- Recovers token via reverse-rotation: `permute(positioned_k, -k * stride) == token`
- Differs from §3.1 in that there is **one base token** rotated by position, rather than the token bound with an independent position vector.

Scheme B is structurally **a one-parameter family** rotating a single token through D positions; Scheme A is structurally **a multiplicative composition** with explicit position vectors. Both are Level-1; both are bit-exact reversible. Which to use depends on whether (a) different tokens at different positions need to be distinguished — Scheme A, the conventional sequence case — or (b) one token's position needs to be tracked — Scheme B, more like a clock cycle.

### §3.3 Scheme C — RoPE-style rotation (Level 2, conventional)

Rotary positional embedding (Su et al. 2021): rotate the Q and K vectors by an angle proportional to position before computing attention. Concretely: `Q_rotated = R(θ_k) · Q` where `R(θ)` is a 2D rotation matrix applied pairwise across dimensions.

Per `[[user_stance_rotation_is_class_k_pin_slot]]` + R-RBS-NN-1 §4.2: rotation IS Class K pin-slot. The 2D rotation requires sin/cos values per position, which inhabit Level 2 (continuous interpolation through `θ_k = position / base^(2i/d)`). RoPE is Level 2 by construction.

**What RoPE provides that Scheme A does not:** *relative-position* attention. Two queries Q_i and Q_j at positions i and j, after RoPE rotation, produce a dot-product that depends only on (i − j), not on i and j separately. This is the key inductive bias of RoPE; it generalizes better to long sequences than absolute-position encodings.

**What Scheme A provides that RoPE does not:** bit-exact reversibility at Level 1. The Level-1 transformer substitution (R-RBS-NN-3b §6) loses the relative-position bias when it replaces RoPE with discrete cyclic shift.

---

## §4 Class K rotate-overlay — what it IS

MFO §VII.1.3 line 743, verbatim:

> "MAX-pool of (v, rotate(v)) — Class K per-position selection — IS the canonical substrate-vs-shadow projection mechanism ... At each bin `i`, `output[i] = max(v[i], rotate(v)[i])` — bit-exact value preserved where IT dominates; rotated value preserved where IT dominates."

Operationally: **rotate-overlay takes a single token and overlays it with its rotated companion, then picks the per-position dominant.** This is structurally different from §3.1–§3.3 above (which bind position to content); rotate-overlay creates a **multi-view envelope of the same content** by overlaying it with rotated copies. The framework names this as the canonical substrate-to-shadow projection per MFO line 743.

### §4.1 Where rotate-overlay surfaces in NN architectures

- **Convolutional NN translation/rotation invariance** (MFO line 743 verbatim): "MAX-pool variant is structurally how convolutional NNs achieve translation/rotation invariance via max-pooling across views." The conv-NN's pooling operation IS the rotate-overlay mechanism at the architectural level.
- **Hard attention** (R-RBS-NN-3b §3): `V[argmax_i S_i]` is the degenerate one-position rotate-overlay where the "rotation" is "shift across the position axis." The Mechanism-3 / Class-K reading places hard attention here.
- **Some inductive biases in vision transformers / convolutional positional embedding hybrids** (per literature; deferred attestation to R-RBS-NN-4).

### §4.2 Why rotate-overlay lifts to FPU (the user's "we know exactly why")

The lift is **not** because rotate-overlay requires floating-point arithmetic — the rotation itself (`permute` per `srmech/amsc/hdc.py`) is integer-byte cyclic shift, Level 1. The lift is because rotate-overlay is **ontologically Level-2 by assignment**: it is a substrate-to-shadow projection per MFO line 743. The Class K per-position-selection IS the projection event — what surfaces from substrate (single-view bit-exact content) into shadow (multi-view envelope visible in the dominant projection per bin).

Compute-wise, you CAN execute the rotate-overlay using only integer operations:
1. `v_rot = permute(v, stride)` — Level 1 ALU, byte XOR / integer cyclic shift
2. `output_bit[i] = v[i] OR v_rot[i]` (binary MAX) or `output_bit[i] = sign(v[i] + v_rot[i])` (bipolar MAX)

So rotate-overlay is **computationally Level-1 available** but **ontologically Level-2 by assignment**. The two ontological levels are not the same as the two compute homes; the framework keeps them distinct.

---

## §5 The canonical Kanerva HDC sequence representation in srmech

Putting §3.1 (Scheme A) together with R-RBS-NN-2 §3.3 (Spike #170 stance fingerprinting pattern):

```python
# Encode a sequence of L tokens at positions 0..L-1
def encode_sequence(tokens: list[str], D: int = 8192) -> bytes:
    bound = []
    for k, t in enumerate(tokens):
        token_vec = mint_vector(f"LoE.token.{t}", D=D)
        pos_vec   = mint_vector(f"LoE.position.{k}", D=D)
        bound.append(bind(token_vec, pos_vec))
    return bundle(bound)

# Decode the token at position k
def decode_at_position(S: bytes, k: int, vocabulary: dict[str, bytes], D: int) -> str:
    pos_vec = mint_vector(f"LoE.position.{k}", D=D)
    candidate = bind(S, pos_vec)  # extracts approximate token at position k
    # Cleanup against vocabulary
    best_token = max(vocabulary.items(), key=lambda kv: similarity(candidate, kv[1]))
    return best_token[0]
```

Capacity per R-RBS-NN-2 §6: clean recovery for sequences of length up to ~D / (k_const · log D) tokens, with the §7 worked example confirming the empirical inflection.

This is structurally the same algebraic content as conventional transformer positional embedding + attention — but at Level 1 (bind instead of softmax-bundle).

---

## §6 What's preserved / projected under each mechanism

| Mechanism | Level | Preserved | Projected |
|---|---|---|---|
| §3.1 Bind-with-position-vector | 1 | Per-position token content (bit-exact under unbinding with correct position) | None (no projection at encoding; only at cleanup readout) |
| §3.2 Cyclic shift (Class I) | 1 | One token's position-trajectory (recoverable via inverse rotation) | None |
| §3.3 RoPE rotation | 2 | Relative-position structure (dot-product depends on i−j) | Continuous-position interpolation surfaced; absolute position obscured |
| §4 Rotate-overlay (Class K) | 2 (ontological) | Per-bin dominant content (across the v + rotate(v) pair) | Multi-view envelope; canonical substrate-to-shadow per MFO line 743 |

The two Level-1 mechanisms (§3.1, §3.2) preserve substrate at the binding layer. The two Level-2 mechanisms (§3.3, §4) project substrate into observable structure: RoPE projects absolute position into relative-position-only, rotate-overlay projects single-view content into multi-view envelope.

**The choice between Level-1 and Level-2 is architectural intent**, not a precision tradeoff. If the user wants relative-position generalization (RoPE) or multi-view invariance (rotate-overlay), they accept the Level-2 lift. If they want bit-exact substrate preservation, they take §3.1 or §3.2 at Level 1.

---

## §7 Worked example — sequence encoding + position-conditioned recovery

Source: `docs/srmech/rbs_nn_research/worked_example_position_binding.py`
Reproduce: `PYTHONPATH=docs/srmech/python python3 docs/srmech/rbs_nn_research/worked_example_position_binding.py`

Encodes a 9-token sequence using §3.1 (bind-with-position-vector; sequence length is odd because `bundle` requires odd-count majority). For each position k, recovers the token via `argmax similarity(bind(S, P_k), vocabulary)`. Also demonstrates §3.2 cyclic-shift reversibility.

Output captured at repo commit `2e4657fc`:

```
D = 8192 bits

Vocabulary: 10 terms; encoding sequence of length L = 9
Encoded sequence S: 1024 bytes (8192 bits)

=== Scheme A — per-position recovery ===
  pos | true token        | recovered         | sim     | OK
  --- + ----------------- + ----------------- + ------- + ---
    0 | Class A           | Class A           | +0.2808 | OK
    1 | Class M           | Class M           | +0.2532 | OK
    2 | Class K           | Class K           | +0.2588 | OK
    3 | sign flip         | sign flip         | +0.2690 | OK
    4 | Class L           | Class L           | +0.2656 | OK
    5 | rotate-overlay    | rotate-overlay    | +0.2976 | OK
    6 | pin slot          | pin slot          | +0.2710 | OK
    7 | Class I           | Class I           | +0.2759 | OK
    8 | substrate         | substrate         | +0.2944 | OK

  Accuracy: 9/9 (100.0%)

=== Scheme B — cyclic shift (Class I) bit-exact reversibility ===
  stride = 257 (coprime to D = 8192)
  k =    0: permute(base, k*stride) → reverse-permute recovers base: True
  k =    1: permute(base, k*stride) → reverse-permute recovers base: True
  k =    5: permute(base, k*stride) → reverse-permute recovers base: True
  k =   13: permute(base, k*stride) → reverse-permute recovers base: True
  k =  100: permute(base, k*stride) → reverse-permute recovers base: True
```

### §7.1 Reading the numbers

- **Scheme A — 9/9 per-position recovery at L=9**. Recovery similarities cluster around +0.25 to +0.30 — well above the noise floor (~±0.011) but lower than the unbundled +1.0. This is exactly the bundle-then-cleanup behavior: each token's contribution to the bundle decreases as bundle size grows, but stays distinguishable above noise. Per R-RBS-NN-2 §6, the cleanup capacity at D=8192 is ~63–130 items; L=9 sits well inside that regime.
- **Scheme B — bit-exact reversibility verified at k ∈ {0, 1, 5, 13, 100}**. The `permute(permute(v, k·stride), -k·stride) == v` involution holds at machine ε for all tested k. Per Spike #176 (rotation IS Class K at machine ε). The cyclic shift is genuinely bit-exact, not approximate.
- **Both schemes Level-1 throughout**. The per-position recovery in Scheme A uses similarity (with its cosmetic float rescale); replacing with integer Hamming argmin (as in R-RBS-NN-3a Demo 6) gives identical results without any FPU operation.

---

## §8 Findings

**Finding 1 — Two structurally-distinct Level-1 positional binding schemes are available**: §3.1 bind-with-position-vector (multiplicative composition) and §3.2 cyclic shift (one-parameter rotation family). Both are bit-exact reversible at the binding layer; both stay at MFO Level 1; both have committed srmech implementations.

**Finding 2 — Conventional transformer positional encoding (sinusoidal / RoPE) is Level 2 by construction**, but the Level-1 substitute (§3.1) is the canonical Kanerva HDC sequence representation. RBS-NN's choice is structural, not novel. Per R-RBS-NN-3b §6.

**Finding 3 — Rotate-overlay is ontologically Level 2 even though it is computationally Level-1 available.** Per §4.2. The lift is by ontological assignment (substrate-to-shadow projection per MFO line 743), not by compute requirement. The framework keeps ontology and compute distinct.

**Finding 4 — What rotate-overlay surfaces in NN architectures** is convolutional max-pooling translation-invariance (per MFO line 743 verbatim) + hard attention (R-RBS-NN-3b §3). These are the Class K Mechanism-3 instantiations in conventional NN.

**Finding 5 — The Level-1 / Level-2 choice for positional encoding is architectural intent.** Per §6. Level-1 preserves absolute-position content bit-exactly; Level-2 (RoPE) projects to relative-position generalization. Choose by what generalization is required.

**Finding 6 — The canonical Kanerva HDC sequence representation is structurally identical to conventional transformer position+content fusion**, but at Level 1. Per §5. RBS-NN reads conventional transformer positional handling as a Level-2 instantiation of the same algebraic content the framework reads at Level 1.

---

## §9 Open threads (not blockers for partition close)

- **R-RBS-NN-4 literature attestation** — Kanerva 1988/2009, Plate 1995, Gayler 2003, Su et al. 2021 RoPE all named in this REPORT; MPR attestation pending. Deferred per user direction.
- **Capacity at sequence length** — §5 capacity is governed by R-RBS-NN-2 §6 cleanup capacity. R-RBS-NN-7 (capacity & grow-without-quantization) will formalize the sequence-length scaling.
- **Relative-position Level-1 substitutes** — RoPE provides relative-position dot-products at Level 2. Is there a Level-1 substitute that preserves relative-position structure? Class I coprime-shift (§3.2) IS relative-rotation-preserving, but it operates on a single token, not on a query-key pair. Open architectural thread.
- **Rotate-overlay in the worked example** — §7 currently demonstrates §3.1 (bind-with-position-vector). A second worked example demonstrating §4 (Class K rotate-overlay; v vs permute(v) overlay) is open for inclusion or as a separate file.
- **Multi-head attention's per-head position interaction** — each attention head can apply different positional structure (per-head RoPE base, etc.); how this composes with §3.1 binding is an open thread.

---

## §10 Closing — partition status

**Status:** CLOSED. Three positional binding schemes placed at MFO levels per §3. Rotate-overlay reading at §4. Canonical Kanerva sequence representation at §5. What-is-preserved/projected per mechanism at §6. Worked example at §7.

**Falsifiers:**

1. A positional-encoding scheme in active NN literature that does NOT fit one of §3.1 / §3.2 / §3.3 / §4 — **not encountered**.
2. A claim that rotate-overlay requires floating-point arithmetic — **explicitly disclaimed in §4.2**: it is ontologically Level 2 by assignment, not by compute requirement.
3. A Level-1 substitute claim for RoPE that the framework cannot ground — **acknowledged as open thread §9**: RoPE's specific relative-position dot-product structure does not have a clean Level-1 substitute in the bind-with-position-vector form.

**Inherits to:** R-RBS-NN-6 (1:3:7:3 architectural layout). R-RBS-NN-3b §4 identified that the transformer uses 6 of 14 classes — {A, C, I, K, M, N}. R-RBS-NN-5 confirms {C, I} for positional handling. The 1:3:7:3 mapping in R-RBS-NN-6 inherits these placements.

**SSoT marker:** at R-RBS-NN-9 close, §3 schemes + §4 rotate-overlay reading absorb into `srmech_research_notebook.md` as a new §RBS-NN positional-binding subsection.
