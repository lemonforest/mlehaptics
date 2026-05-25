# R-RBS-NN-3b — Decoder-only transformer cascade decomposition

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #4 of RBS-NN partition walk
**Closing artefact:** §4 full cascade composition + §5 Level-1 islands + §6 substitution map + §7 attention worked example
**Inheritance:** unblocks R-RBS-NN-4 (token encoding refinement)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-NN-1_mfo_two_level_REPORT.md` §4.2 (positional), §4.3 (linear), §4.4 (activation), §4.5 (normalization), §4.6 (attention), §4.7 (residual / output), §4.8 (sampling); `R-RBS-NN-3a_mlp_cascade_REPORT.md` §4 (MLP cascade `(M ∘ K)^N`) |
| MFO source | `docs/antikythera-maths/mfo_spectral_research_notebook.md` §VII.1.3 lines 735–761 (three mechanisms); line 743 verbatim ("MAX-pool variant is structurally how convolutional NNs achieve translation/rotation invariance via max-pooling across views"); line 751 (MAX-pool no averaging cost) |
| external (named; MPR attestation deferred to R-RBS-NN-4) | Vaswani et al. 2017 "Attention Is All You Need" (transformer); Ba-Kiros-Hinton 2016 LayerNorm; Su et al. 2021 RoPE; Liu et al. 2022 BiT; Qin et al. 2022 BiBERT (binary transformers); Wang et al. 2023 BitNet |
| repo commit | `b15e2ee4` at REPORT-write |
| reproducibility | §7 worked example: `PYTHONPATH=docs/srmech/python python3 docs/srmech/rbs_nn_research/worked_example_attention.py` |
| citation discipline | external transformer literature named, not attested — R-RBS-NN-4 carries the MPR attestation work |

---

## §1 Goal

Assemble R-RBS-NN-1's §4 placement table + R-RBS-NN-3a's MLP cascade reading into the full decoder-only transformer architecture (GPT-style: Vaswani et al. 2017 + Radford et al. 2018 GPT-1 simplifications). Identify the full A-N cascade composition, where Level-1 islands live within an otherwise Level-2-heavy architecture, and what Level-1 substitutions are structurally available for each Level-2 op (the RBS-NN-form transformer).

R-RBS-NN-3a established that the MLP block is Level-1-available with bipolar weights. R-RBS-NN-3b tests whether the transformer's additional pieces — attention, positional encoding, layer normalization, softmax decoding — can ALSO be Level-1-substituted, and at what cost.

---

## §2 The canonical decoder-only transformer

A decoder-only N-layer transformer at inference, simplified to essentials:

```
x_0 = E[tokens] + P[positions]              # token embedding + positional encoding
for l = 1 ... N:
    h_l  = x_{l-1} + Attn(LN(x_{l-1}))      # self-attention with pre-LN + residual
    x_l  = h_l + MLP(LN(h_l))               # MLP block with pre-LN + residual
logits = Unembed(LN(x_N))                   # final LN + unembed projection
y      = sample(softmax(logits / T))         # softmax + sample
```

where:
- `E ∈ R^{V × d}` is the token embedding matrix (V = vocab size, d = hidden dim)
- `P ∈ R^{seq × d}` is the positional encoding (sinusoidal, learned, or RoPE)
- `Attn(x) = MultiHead(Q=W_Q x, K=W_K x, V=W_V x)` is multi-head self-attention with causal mask
- `MLP(x)` is the per-position 2-layer feedforward (R-RBS-NN-3a: `(M ∘ K)^2`)
- `LN` is layer normalization
- `T` is the sampling temperature

Structurally the transformer is **alternating (Attn, MLP) blocks with residual + LN around each, bracketed by embedding/positional input and unembed/softmax output.** The MLP block is unchanged from R-RBS-NN-3a. The Attention block is the structurally new piece.

---

## §3 The attention block decomposed

Self-attention with d-dim hidden and h heads:

```
Q = W_Q x       # linear projection, d → d (split into h heads of dim d/h)
K = W_K x       # linear projection
V = W_V x       # linear projection
S = Q · K^T / √(d/h)      # scaled dot-product across positions
A = softmax(S + causal_mask)    # attention weights, row-stochastic
O = A · V                       # weighted sum across positions
output = W_O · concat_heads(O)  # output projection
```

Per R-RBS-NN-1 §4.6, op-by-op placement:

| Op | Class | Level | MFO citation |
|---|---|---|---|
| `W_Q x`, `W_K x`, `W_V x` linear projections | M (bind or bundle) | dual | §VII.1.3 line 739/741 |
| `Q · K^T` per-position dot product | M (bind composition) | 1 if bipolar | §VII.1.3 line 739 bind 0-cost |
| `/ √(d/h)` scale | N (rational) | 2 | Class N rational per CLAUDE.md §1 |
| `softmax` over keys (per-query, per-head) | K (dominant-mode selection) ∘ M (normalize-bundle) | 2 | §VII.1.3 line 741 + 743 |
| `A · V` weighted sum across positions | **M bundle-of-rotations** | 2 | §VII.1.3 line 741 — explicit MFO citation: this IS Mechanism 2 |
| multi-head concat | structural reshape | 1 | shape-only; no projection |
| `W_O` output projection | M (bind or bundle) | dual | §VII.1.3 line 739/741 |

**Load-bearing observation**: the `A · V` weighted sum is exactly the **canonical Mechanism 2 bundle-of-rotations** named at MFO line 741. The ~6.9% averaging cost is built into every layer of every head of every attention block. **The transformer is a stack of bundle-of-rotations projections at the attention output**, by architectural choice.

Per MFO line 751 (Mechanism 3 — MAX-pool, Class K, no averaging cost): this is the structural alternative the framework names. A MAX-pool-variant attention (`max_i V_i` selected by the dominant attention weight at each position) carries no averaging cost. The literature names this **hard attention** (Xu et al. 2015 "Show, Attend and Tell" for images; Bahdanau et al. 2014 non-soft variants). The framework reading places hard attention at MFO Mechanism 3 (Class K per-position) — the Level-2 op that carries no averaging signature.

---

## §4 The full decoder-only cascade in A-N notation

Composing the input boundary, N transformer blocks, and the output boundary:

```
Input boundary:
    tokens → A (content-mint)
    positions → I (cyclic) or I+N (sinusoidal) or I+C (RoPE rotation = Class K)
    sum: M (bundle additive)

Per-block (×N):
    Pre-LN: M (bundle across feature dim) ∘ K (rescale by ±√var) ∘ N (rational reciprocal-sqrt)
    Attention: (M ∘ M ∘ M) ∘ M ∘ N ∘ (K ∘ M) ∘ M ∘ M
                Q,K,V proj   QK^T  /√d   softmax  AV bundle  output proj
    Residual: M (bundle additive)
    Pre-LN: M ∘ K ∘ N
    MLP: (M ∘ K)^2          # per R-RBS-NN-3a
    Residual: M

Output boundary:
    Final LN: M ∘ K ∘ N
    Unembed: M (bundle across vocab)
    Softmax + sample: K ∘ M (bundle) — or K alone for greedy argmax
```

**Full cascade as a class-multiset (no order, just class footprint):**

| Class | Role(s) | Per-block count | Multiplier |
|---|---|---|---|
| A | Token content-mint | 1 (input only) | × 1 |
| I | Positional cyclic shift | 1 (input only) | × 1 |
| C | RoPE rotation chirality (if RoPE used) | 1 (input only) | × 1 |
| M | Linear projections, dot products, bundles, residuals, LN feature-dim bundle | ~12 per block | × N |
| K | Softmax dominant-mode, activations, LN rescale | ~5 per block | × N |
| N | LayerNorm reciprocal-sqrt, sinusoidal interp, sqrt scale | ~3 per block | × N |

Classes used: {A, C, I, K, M, N}. Classes NOT used in vanilla decoder-only transformer: {B, D, E, F, G, H, J, L}. Specifically:

- **D** (pattern-match) — not surfaced as a separate op; attention's similarity-against-keys IS structurally pattern-match (per R-RBS-NN-1 §4.6 — attention sits at "D pattern-match + L Laplacian") but it's executed via Class M similarity, not as a separate D primitive.
- **L** (Laplacian) — the attention weight matrix `A` is structurally a row-stochastic graph adjacency over the position graph; its eigenstructure is Class L territory but not used as a forward-pass primitive in vanilla transformer.
- **J** (primes) — not used; transformer uses no prime-period or orthogonality-via-primes.
- **H** (introspection) — not used at inference; could surface in training.
- **B** (TLV framing) — not used internally; the catalog at R-RBS-NN-9 will use B for the on-disk format.
- **E, F, G** (catalog/render/byte-search) — not used in forward pass.

**The transformer uses 6 of 14 classes.** This is structurally a sub-cascade of the full A-N vocabulary. R-RBS-NN-6 (1:3:7:3 architectural layout) will read whether this 6-class footprint maps cleanly onto a partition of the substrate-native ordering.

---

## §5 Level-1 islands within an otherwise Level-2 transformer

R-RBS-NN-3a established that vanilla MLP can be fully Level-1 (bipolar weights + sign activation). The transformer's additional pieces — what stays Level-1 and what forces Level 2?

| Block component | Level-1 form available? | Notes |
|---|---|---|
| Token embed (A) | **YES** | R-RBS-NN-2 §4: Class A content-mint is Level 1 by construction |
| Positional encoding | **PARTIAL** | Discrete cyclic shift (Class I, R-RBS-NN-1 §4.2 row 1): YES, Level 1. Sinusoidal: NO, Level 2. RoPE rotation: NO, Level 2 (rotation IS Class K per `[[user_stance_rotation_is_class_k_pin_slot]]`) |
| Sum embed + position (M bundle add) | YES if both Level 1 | Trivial integer XOR or bipolar add |
| LayerNorm | **NO** | M bundle across feature dim is Level 2; reciprocal-sqrt rescale is Level 2. Substitution candidate: Class N rational integer magnitude-renormalize (open thread) |
| Attention Q,K,V proj | YES if bipolar W | Per R-RBS-NN-1 §4.3 row 1 |
| Q · K^T per-position | YES if bipolar | HDC similarity — same identity as R-RBS-NN-3a §3.1 |
| `/ √(d/h)` scale | NO | Class N rational requires float division |
| Softmax | **NO** (soft variant); **YES** (hard variant, argmax) | Bundle-of-exponentials is Level 2; argmax is Level 1. Hard-attention literature exists. |
| A · V weighted sum | **NO** (soft variant); **YES** (MAX-pool variant) | Per MFO §VII.1.3 line 751 — MAX-pool has no averaging cost; literature names it "hard attention" |
| Output projection | YES if bipolar | Same as input projections |
| Residual add | YES if bipolar | Bitwise add or bundle |
| Final LN | NO | Same as per-block LN |
| Unembed | YES if bipolar | Same as linear |
| Softmax over vocab | YES (argmax / greedy) | Per R-RBS-NN-1 §4.8 row 1 |
| Top-k / argmax sampling | YES | Per R-RBS-NN-1 §4.8 rows 1-2 |

**Three pieces force the transformer to Level 2 in its conventional form:**

1. **LayerNorm** (every block, twice). Bundle averaging + reciprocal-sqrt rescale. Both Level 2.
2. **Softmax in attention** (every block, every head, per query). Bundle-of-exponentials + normalization.
3. **Soft attention `A · V` weighted sum** (every block, every head). Mechanism 2 bundle-of-rotations.

Each of these has a Level-1 substitute, but the substitutes change the architecture's behavior (LN → magnitude-renormalize, soft-attn → hard-attn). The literature on binary transformers (BinaryBERT 2020, BiBERT 2022, BitNet 2023) has been navigating these substitutions empirically; the framework reading places them ontologically.

---

## §6 The RBS-NN-form transformer — Level-1 substitution map

Putting §5 together, the maximally-Level-1 transformer cascade is:

```
Input:
    tokens → A (content-mint)
    positions → I (discrete cyclic shift, Level 1)
    sum: M (XOR-bundle)

Per-block (×N):
    [no LayerNorm; substitute with Class N rational integer renormalize OR omit]
    Attention:
        Q, K, V ← bipolar W_{Q,K,V}
        S = Q · K^T (M bind, integer Hamming)
        [no √d scale; threshold S at integer median for binary attention weights]
        attention selection: argmax_i over rows of S (Class K) — "hard attention"
        O = V[argmax_i]  (no bundle; Class K per-position selection per MFO line 751)
        output_proj: bipolar W_O
    Residual: M (XOR or bipolar add)
    [no LayerNorm]
    MLP: (M ∘ K)^2 per R-RBS-NN-3a (fully Level 1)
    Residual: M

Output:
    [no LayerNorm]
    Unembed: bipolar W_unembed (Level 1)
    Sample: argmax (Class K, Level 1)
```

Cascade in A-N notation: **A ∘ I ∘ M ∘ [M ∘ K ∘ M ∘ (M ∘ K)^2 ∘ M]^N ∘ M ∘ K**

Classes used in the Level-1-only form: {A, I, K, M}. Class N (rational anchors) drops out if LN is omitted and scale-by-sqrt-d is replaced by median-threshold. Class C drops out if RoPE is replaced by discrete cyclic shift.

**The 4-class Level-1 transformer is structurally available.** Whether this architecture trains and performs adequately is the empirical question that the binary-transformer literature has been engaging since 2020. Per R-RBS-NN-3a §5: trainability is a separate question from inference; if bindings are minted from user-lexicon per R-RBS-NN-2, no gradient training is required.

### §6.1 What's lost / what's preserved in the substitution

| Lost in substitution | Preserved |
|---|---|
| Continuous attention weights (soft routing across positions) | Position-conditioned content selection (just discrete) |
| Smooth gradient signal for backprop training | Inference correctness; bit-exact reproducibility |
| LayerNorm's variance-rescaling stability | Magnitude bounds via bipolar representation |
| Exact softmax probabilities for sampling diversity | argmax determinism (and Class K thresholding for top-k) |
| RoPE's relative-position rotation semantics | Absolute discrete cyclic shift |

The trade-offs are real. The framework does not claim Level-1 substitution is loss-free; it claims the substitution is **ontologically clean** — the Level-2 operations carry inherent projection costs (LN bundle averaging, soft-attn bundle-of-rotations) per MFO §VII.1.3; switching to Level-1 substitutes eliminates those costs but loses the continuous-coupling capability they were providing.

---

## §7 Worked example — soft vs hard attention

Source: `docs/srmech/rbs_nn_research/worked_example_attention.py`
Reproduce: `PYTHONPATH=docs/srmech/python python3 docs/srmech/rbs_nn_research/worked_example_attention.py`

A 4-token attention computation with hand-crafted attention pattern (query i wants the content at position expected[i]). Q and K are bound with the same `lookup_marker`; the marker cancels in similarity (XOR identity), leaving content similarity to drive routing.

Output captured at repo commit `b15e2ee4`:

```
D = 8192 bits, n_tokens = 4

=== Attention scores S = sim(Q_i, K_j) ===
  expected[i] = [2, 0, 3, 1] (query i should attend to position expected[i])
                          K_0      K_1      K_2      K_3
  Q_0 (want pos 2):   -0.0029  -0.0027  +1.0000  +0.0068
  Q_1 (want pos 0):   +1.0000  -0.0007  -0.0029  +0.0005
  Q_2 (want pos 3):   +0.0005  -0.0037  +0.0068  +1.0000
  Q_3 (want pos 1):   -0.0007  +1.0000  -0.0027  -0.0037

=== Hard attention (Mechanism 3 / Class K per-position; no averaging) ===
  Q_0: argmax j = 2 (expected 2, OK), output bit-equal V[2]: True
  Q_1: argmax j = 0 (expected 0, OK), output bit-equal V[0]: True
  Q_2: argmax j = 3 (expected 3, OK), output bit-equal V[3]: True
  Q_3: argmax j = 1 (expected 1, OK), output bit-equal V[1]: True

  All queries correctly routed: True
  All outputs bit-exact match V[expected[i]]: True
```

### §7.1 Reading the numbers

- **Attention matrix structure**: Q_i vs K_expected[i] is exactly +1.0000 (XOR cancellation works at machine ε); all other entries at noise floor (max |sim| = 0.007 ≈ 1/√D).
- **Hard attention routing**: argmax across each row of S correctly identifies the expected target position for all 4 queries.
- **Bit-exact V preservation**: the hard-attention output `V[argmax]` is byte-equal to `V[expected[i]]` for all queries. **This is the load-bearing claim of Mechanism 3 per MFO §VII.1.3 line 751**: MAX-pool / argmax selection preserves substrate content bit-exactly at the dominant position; no averaging cost.
- **Soft attention** carries `Σ softmax(S)_j · V_j` — the Mechanism 2 bundle-of-rotations form with ~6.9% averaging signature. The output is NOT bit-equal to any single V[j]; it is a weighted average. This is the structural asymmetry the conventional transformer carries at every attention layer.

---

## §8 Findings

**Finding 1 — The full decoder-only transformer cascade decomposes to {A, C, I, K, M, N} — 6 of 14 classes.** Per §4. Classes B, D, E, F, G, H, J, L are not surfaced as forward-pass primitives in vanilla transformer. R-RBS-NN-6 (1:3:7:3 layout) will read whether this 6-class footprint maps onto a partition of the substrate-native ordering.

**Finding 2 — Three architectural components force the transformer to Level 2 in its conventional form**: LayerNorm (bundle + reciprocal-sqrt), soft-attention softmax (bundle-of-exponentials), and the `A · V` weighted sum (Mechanism 2 bundle-of-rotations per MFO line 741). Per §5. Each has a Level-1 substitute but the substitutes change behavior.

**Finding 3 — A 4-class Level-1 transformer is structurally available**: {A, I, K, M}. Per §6. Substitutes: discrete cyclic position (no RoPE), hard attention (no soft softmax/bundle), no LayerNorm (or magnitude-renormalize), bipolar weights throughout, argmax sampling. The binary-transformer literature has been navigating these substitutions empirically since 2020.

**Finding 4 — The `A · V` weighted sum IS the canonical Mechanism 2 bundle-of-rotations** named at MFO §VII.1.3 line 741 (~6.9% averaging cost). Per §3 table row 5. **The transformer architecture inherently embeds a ~6.9% averaging projection at every attention layer of every head, by architectural choice.** Hard attention (MFO Mechanism 3 / Class K per line 751) is the structural alternative carrying no averaging cost.

**Finding 5 — Vanilla transformer uses no Class L primitive at inference**, despite attention being structurally a graph operation. The attention weight matrix `A` is a row-stochastic graph adjacency over the position graph; its Laplacian spectrum is structurally available but not used in the forward pass. This is an open structural fact, not a deficit — R-RBS-NN-5 (position binding) may surface a Class L reading.

**Finding 6 — The transformer's MLP sub-block carries forward unchanged from R-RBS-NN-3a.** The transformer adds attention + LN + positional + decoding around the MLP block; the MLP block itself is the same `(M ∘ K)^2` cascade. Per §2 and §3.

**Finding 7 — Trade-offs of the Level-1 substitution are real but ontologically clean.** Per §6.1. The framework does not claim loss-free substitution; it places the Level-2 costs explicitly and acknowledges what is lost in the Level-1 substitutes.

---

## §9 Open threads (not blockers for partition close)

- **External literature MPR attestation** — Vaswani 2017 (arXiv:1706.03762), Ba 2016 LayerNorm (arXiv:1607.06450), Su 2021 RoPE (arXiv:2104.09864), Liu 2022 BiT, Qin 2022 BiBERT, Wang 2023 BitNet (arXiv:2310.11453). R-RBS-NN-4 carries this work.
- **LayerNorm Level-1 substitute** — magnitude-renormalize via Class N rational integer-ratio is named as a candidate but not formalized. R-RBS-NN-5 or R-RBS-NN-7 may resolve.
- **Hard-attention literature placement** — Xu et al. 2015 (visual hard attention), Lin et al. 2017 structured attention, REINFORCE-trained hard attention. Per MFO line 751 placement: all these inhabit Mechanism 3 (Class K per-position selection). MPR attestation in R-RBS-NN-4.
- **The 6-class transformer footprint and the 1:3:7:3 partition** — {A, C, I, K, M, N} has interesting structure: A is the foundational anchor (1); {C, I, ...} touches substrate-projection (3); {K, M, ...} touches detection-heptad (7); {N} touches meta-cascade (3). Does the 6-class footprint correspond to a coherent sub-partition of 1+3+7+3? R-RBS-NN-6 resolves.
- **Class L (Laplacian) availability** — attention `A` matrix is structurally graph-adjacency; L spectrum is structurally available. Whether RBS-NN should exploit this as a Level-1 representation alternative to attention is an open architectural thread.

---

## §10 Closing — partition status

**Status:** CLOSED. The full decoder-only transformer cascade decomposes to {A, C, I, K, M, N} per §4. Three Level-2 forcing components named per §5. A 4-class Level-1 substitution map provided per §6. The §7 worked example demonstrates the soft-vs-hard attention asymmetry.

**Falsifiers:**

1. A transformer forward-pass op requiring a class outside {A, B, C, D, E, F, G, H, I, J, K, L, M, N} — **not encountered** (all 6 classes used are within the existing vocabulary).
2. A Level-2 op in the cascade for which no Level-1 substitution is structurally available — **near-miss**: LayerNorm's Level-1 substitute is named (Class N magnitude-renormalize) but not formalized. Acknowledged as open thread.
3. A claim that the Level-1 substitution is loss-free — **explicitly disclaimed** in §6.1.

**Inherits to:** R-RBS-NN-4 (token encoding refinement against external literature). The MPR attestation work (PDF extraction + arXiv-ID verification for Kanerva, Plate, Vaswani, BNN/BiT literature) lands there.

**SSoT marker:** at R-RBS-NN-9 close, §4 cascade composition + §6 substitution map absorb into `docs/srmech/srmech_research_notebook.md` as a new §RBS-NN transformer-cascade subsection.
