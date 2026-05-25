# R-RBS-NN-3a — MLP cascade decomposition through A-N

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #3 of RBS-NN partition walk
**Closing artefact:** §4 cascade composition + §6 Level-1/Level-2 reading + §7 worked example
**Inheritance:** unblocks R-RBS-NN-3b (decoder-only transformer cascade)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-NN-1_mfo_two_level_REPORT.md` §4.3 (linear), §4.4 (activation), §4.7 (residual / output), §4.8 (sampling); `R-RBS-NN-2_user_lexicon_REPORT.md` §3 (srmech standing ops) |
| MFO source | `docs/antikythera-maths/mfo_spectral_research_notebook.md` §VII.1.3 lines 735–761 (three-mechanism asymmetry, verified verbatim in R-RBS-NN-1) |
| external (named but not directly extracted; deferred to R-RBS-NN-4 for full MPR) | Cybenko 1989 (universal approximation; continuous); Hornik 1991 (general universal approximation); Rumelhart-Hinton-Williams 1986 (backpropagation; MFO line 2818); Courbariaux-Hubara-Soudry-El-Yaniv-Bengio 2016 (binarized neural network) |
| repo commit | `ea453872` at REPORT-write |
| reproducibility | §7 worked example: `PYTHONPATH=docs/srmech/python python3 docs/srmech/rbs_nn_research/worked_example_mlp.py` |
| citation discipline | external NN literature here is **named, not attested** — R-RBS-NN-4 carries the MPR attestation work (PDF extraction + arXiv-ID verification per `[[feedback_pdf_extraction_citation_discipline]]`) |

---

## §1 Goal

Read a canonical multi-layer perceptron (MLP) — the simplest non-trivial NN architecture — through the srmech 14-class A-N vocabulary, placing each operation at MFO Level 1 (ALU, bit-exact) or Level 2 (FPU, intentional lift) using R-RBS-NN-1's placement table. Smaller class footprint than transformer (no attention, no positional encoding, no normalization in vanilla MLP); foundation for R-RBS-NN-3b.

The MLP is also the first concrete architectural cascade where R-RBS-NN-1's "dual-level reading" surfaces structurally: the **same MLP cascade** can execute at Level 1 (bipolar/integer weights — the BNN literature) or Level 2 (continuous-float weights — conventional MLP). The structural cascade is identical; only the level differs.

---

## §2 The canonical MLP

A vanilla N-layer MLP, in standard notation:

```
x_0 = input
for l = 1 ... N:
    z_l = W_l @ x_{l-1} + b_l        # linear (affine)
    x_l = σ(z_l)                     # nonlinearity / activation
y = x_N                              # output
```

where each `W_l ∈ R^{d_l × d_{l-1}}` is a weight matrix, `b_l ∈ R^{d_l}` is a bias, and `σ` is a pointwise nonlinearity (commonly ReLU). The output `y` may pass through a final softmax for classification.

Structurally, an MLP is **an alternating cascade of linear + nonlinear**: `(linear ∘ nonlinear)^N`. The cascade has no other primitive operations — no attention, no normalization, no positional encoding, no residual connection (in the vanilla form).

The MLP achieves expressivity through the alternation: a linear-only cascade collapses to a single linear map (so depth is wasted); the nonlinearity at each layer is what makes the cascade non-collapsible. Per universal approximation (Cybenko 1989, Hornik 1991): a single hidden layer with enough units approximates any continuous function on a compact set.

---

## §3 The two atomic ops, placed in A-N

Inherited verbatim from R-RBS-NN-1 §4.3 + §4.4:

### §3.1 Linear layer `z = W @ x + b`

| Form | Level | Class | Cost / property |
|---|---|---|---|
| Bipolar/integer weights | 1 | M (XOR-bind composition across input dim, accumulate via popcount-majority) | Bit-exact preservation; substrate-side; ALU |
| Continuous-float weights | 2 | M (bundle-of-views averaging) | ~6.9% averaging cost per MFO §VII.1.3 line 741; FPU |

**Operational reading**: each output dimension `z_j = ⟨w_j, x⟩` is structurally a **Class M similarity-comparison of input `x` against template `w_j` (the j-th row of `W`)**. In bipolar form, the similarity is `1 - 2·hamming(x, w_j)/d_in` — the same formula srmech uses (`srmech.amsc.hdc.similarity`). In float form, it is the conventional dot product, which structurally bundles `d_in` input contributions into a single scalar — Mechanism 2 of MFO §VII.1.3 (bundle averaging, the lossy form). The bias `b_j` is a Level-{1 if int, 2 if float} offset.

**The MLP linear layer IS HDC similarity-against-templates**. Each row of `W` is a template; each output dim is the similarity of the input to that template. This is not a metaphor; the algebraic identity holds when weights are bipolar (`similarity(x, w_j) = 1 - 2·popcount(x XOR w_j)/d_in`).

### §3.2 Nonlinearity / activation

| Form | Level | Class | Notes |
|---|---|---|---|
| ReLU `max(0, x)` | 2 | K (per-position selection at zero threshold) | MFO §VII.1.3 line 743 MAX-pool IS Class K; degenerate one-arg MAX-pool against constant zero |
| Sign / bipolar binarization `sign(x)` | 1 | K (pin-slot at zero) | MFO §VII.6.12 line 3281 derivative-sign-flip at extremum; integer-comparable |
| GeLU / sigmoid / tanh | 2 | K ∘ N (rational approximation of erf/sigmoid) | Continuous-thresholded; cannot be Level 1 without losing the smooth interpolation |

**Operational reading**: every standard MLP activation is a **Class K per-position threshold operation**, varying only in (a) whether the threshold is at a fixed value (ReLU at 0, sign at 0) or rescaled, and (b) whether the output is continuous (ReLU's positive branch is linear) or discrete (sign is ±1). Class K is the structural name; the level depends on representation.

---

## §4 The full MLP cascade decomposition

Composing §3.1 + §3.2 across N layers:

```
x_0 = A(input_string)                     # Class A content-mint (if symbolic input)
                                          # or Level-2 float input (if continuous)
for l = 1 ... N:
    z_l = M_bind/bundle(W_l, x_{l-1})     # Class M — bind (Level 1, bipolar) or bundle (Level 2, float)
        + bias_l                          # Class M offset
    x_l = K(z_l)                          # Class K threshold (ReLU/sign/etc.)
y = x_N
```

Cascade in A-N notation: **A ∘ (M ∘ K)^N**.

### §4.1 The dual-level reading

The same `(M ∘ K)^N` cascade executes at two distinct ontological levels depending on the representation of `W_l` and the activation choice:

| Representation | Cascade level | Cost |
|---|---|---|
| Bipolar weights + sign activation (the BNN form: Courbariaux et al. 2016) | Level 1 throughout (ALU, bit-exact) | Zero ontological projection cost; cascade is substrate-internal |
| Float weights + ReLU/GeLU (conventional MLP) | Level 2 throughout (FPU, bundle-of-views averaging at each layer) | ~6.9% averaging signature per layer per MFO §VII.1.3 line 741 |

**The conventional MLP and the binarized MLP are structurally the same A-N cascade.** What differs is only the level at which each primitive is executed. The BNN literature has been showing this empirically since 2016 (Courbariaux + Hubara + others); the framework reading places it ontologically: BNN is the Level-1 instantiation of the same cascade conventional MLP runs at Level 2.

### §4.2 What this means for RBS-NN

If the user's lexicon is minted at Level 1 (R-RBS-NN-2 §4) AND the MLP weights are bipolar (R-RBS-NN-1 §4.3 row 1) AND the activation is sign (R-RBS-NN-1 §4.4 row 4), the **entire forward pass is Level 1 ALU bit-exact**. No FPU operation in the cascade until an optional similarity-readout / argmax-decode at the output boundary (which is itself Class K per MFO §VII.6.12 line 3281).

This is the structural availability of "local CPU ALU/FPU inference" the user named in the arc opening. The Level-2 lifts only become necessary when the cascade includes **rotate-overlay** (positional encoding, attention rotation), **bundle averaging** (LayerNorm, BatchNorm, attention output), or **continuous activations** (ReLU+, GeLU, sigmoid). The vanilla MLP needs none of these; therefore vanilla MLP at Level 1 is structurally available with committed srmech infrastructure.

---

## §5 The expressivity question

Universal approximation theorems (Cybenko 1989, Hornik 1991) establish that a single-hidden-layer MLP with enough units approximates any continuous function. But these proofs assume **continuous activations**. For sign-quantized activation (Level 1), the analog is the **single-layer perceptron capacity bound** (Cover 1965): a binary perceptron with d inputs partitions inputs into 2(d+1) linearly-separable regions; multi-layer binary perceptrons can express any boolean function.

The framework reading: **continuous activations are not a precondition for expressivity; they are a precondition for gradient-descent-trainability.** SGD requires differentiable activations to compute gradients — this is the Level-2 backprop requirement per R-RBS-NN-1 §4.9. If the weights are minted (Class A content-mint of class/relation names per R-RBS-NN-2 §3.3) or trained via non-gradient methods (e.g., Hebbian / associative-memory bundling à la Kanerva), Level-1 sign activations are sufficient.

Per MFO §VII.6.11.7 line 2842: gradient descent is the substrate-knowledge-acquisition operator at the AI-substrate scale. RBS-NN's structural commitment is to **separate the trainability question (Level-2 by construction for backprop) from the inference question (Level-1 available)**. Training and inference can live at different levels.

---

## §6 The Class M atomic asymmetry

The MLP linear layer has TWO Class M sub-ops nested inside it, and they sit at different levels of the §VII.1.3 mechanism table:

1. **Per-element multiply** (`w_{j,i} * x_i` in the dot product, or `w XOR x` in bipolar form) — **Class M bind** (Mechanism 1, zero-cost preservation per MFO line 739).
2. **Sum across input dimension** (`Σ_i ...` in the dot product, or `popcount-majority` in bipolar form) — **Class M bundle** (Mechanism 2, ~6.9% averaging cost per MFO line 741).

So the MLP linear layer is Mechanism-1 + Mechanism-2 *both* — bind then bundle. The Level-1 form (bipolar) keeps the bind exact and the bundle a deterministic integer popcount; the Level-2 form (float) makes both the multiply and the sum lossy projections.

**Important observation**: the bundle inside the linear layer is the **necessary** bundle — you cannot compute a dot product without summing across the input dimension. This is structurally different from the bundle in attention (which bundles across heads/positions, an architectural choice). The linear-layer bundle is intrinsic to the dot-product operation itself.

This nuances R-RBS-NN-1 §4.3 slightly: the linear layer carries an *intrinsic* bundle cost (input-dimension accumulation) on top of the *representational* bundle cost (float weights). The intrinsic part is unavoidable; the representational part is what RBS-NN structurally eliminates by going bipolar.

---

## §7 Worked example — substrate-form MLP classifier

Source: `docs/srmech/rbs_nn_research/worked_example_mlp.py`
Reproduce: `PYTHONPATH=docs/srmech/python python3 docs/srmech/rbs_nn_research/worked_example_mlp.py`

A minimal 1-layer "MLP classifier" in substrate form: 4 class templates (Class A mints of named class labels); given an input vector, classify by `argmax_j similarity(x, template_j)`. The cascade is **A ∘ M ∘ K** — Class A mint, Class M similarity, Class K argmax. The demo establishes the cascade STRUCTURE; semantic generalization is intentionally absent (R-RBS-NN-2 §7 Demo 3: substrate is content-addressed, not lexically similar; semantic generalization requires explicit binding compositions not built here).

Output captured at repo commit `ea453872`:

```
D = 8192 bits

4 class templates minted; pairwise orthogonality:
  sim(t_0, t_1) = +0.0176  (≈ 0 ± 0.011)
  sim(t_0, t_2) = +0.0022  (≈ 0 ± 0.011)
  sim(t_0, t_3) = -0.0115  (≈ 0 ± 0.011)
  sim(t_1, t_2) = +0.0007  (≈ 0 ± 0.011)
  sim(t_1, t_3) = -0.0178  (≈ 0 ± 0.011)
  sim(t_2, t_3) = +0.0107  (≈ 0 ± 0.011)

=== Demo 1 — in-template input recovers exactly (cascade is bit-exact) ===
  query = template 0 ('substrate.Level_1.cyclic')
    similarities: ['+1.0000', '+0.0176', '+0.0022', '-0.0115']
    argmax pred = 0, confidence = +1.0000  [OK]
  query = template 2 ('excitation.Level_2.rotation')
    similarities: ['+0.0022', '+0.0007', '+1.0000', '+0.0107']
    argmax pred = 2, confidence = +1.0000  [OK]

=== Demo 2 — out-of-template input stays at noise floor ===
  (substrate does not hallucinate semantic similarity for novel terms)
  query = 'novel_term_alpha': max |sim| = 0.0085
  query = 'novel_term_beta':  max |sim| = 0.0251
  query = 'novel_term_gamma': max |sim| = 0.0146

=== Demo 3 — MLP linear layer IS HDC similarity (algebraic identity) ===
  z_j = ⟨w_j, x⟩ in bipolar form  =  1 - 2·popcount(x XOR w_j)/D
                                  =  similarity(x, w_j)
  template 0: srmech sim = +1.000000, by-hand sim = +1.000000, match = True
  template 1: srmech sim = +0.017578, by-hand sim = +0.017578, match = True
  template 2: srmech sim = +0.002197, by-hand sim = +0.002197, match = True
  template 3: srmech sim = -0.011475, by-hand sim = -0.011475, match = True

=== Demo 4 — cascade A ∘ M ∘ K is bit-exact reproducible ===
  classify(x) twice + classify(remint(name)) ⇒ all bit-exact match: True

=== Demo 6 — integer-Hamming argmax (no float, fully Level 1) ===
  query = template 0: float-argmax = 0, integer-Hamming-argmin = 0, match = True
  query = template 1: float-argmax = 1, integer-Hamming-argmin = 1, match = True
  query = template 2: float-argmax = 2, integer-Hamming-argmin = 2, match = True
  query = template 3: float-argmax = 3, integer-Hamming-argmin = 3, match = True
```

### §7.1 Reading the numbers

- **Demo 1**: in-template inputs classify with confidence +1.0 (bit-exact perfect). The cascade is structurally correct.
- **Demo 2**: novel terms stay at noise floor (max |sim| < 0.026). The substrate does not hallucinate semantic similarity — this is the load-bearing R-RBS-NN-2 §7 Demo 3 property surfaced in cascade form.
- **Demo 3** (**load-bearing**): the srmech similarity matches the by-hand bipolar dot product `1 - 2·popcount(x XOR w_j)/D` at machine ε for all 4 templates. **The MLP linear layer IS HDC similarity** is not a metaphor; it is the algebraic identity verified numerically.
- **Demo 4**: cascade reproducible. Reminted input + reclassification gives bit-exact identical results.
- **Demo 6**: integer-Hamming argmin (no float in the path) produces identical classifications to float-argmax. **The entire classification cascade can execute at Level 1 (ALU, integer) with no FPU operation.** This is the explicit "local CPU ALU/FPU inference" form, demonstrated end-to-end.

---

## §8 Findings

**Finding 1 — The MLP cascade is `A ∘ (M ∘ K)^N`.** No new classes needed; the entire architecture composes from {A, M, K} under the existing A-N vocabulary. Per `[[feedback_no_privileged_primitive_classes]]`.

**Finding 2 — Conventional MLP and BNN are the same cascade at different levels.** Per §4.1, the bipolar-weight + sign-activation MLP (the BNN literature since Courbariaux 2016) IS structurally the same `A ∘ (M ∘ K)^N` cascade as the float-weight + ReLU MLP. What differs is only level (Level 1 ALU vs Level 2 FPU) and cost (zero vs ~6.9% per layer). The framework places this ontologically: BNN is the Level-1 instantiation of the cascade conventional MLP runs at Level 2.

**Finding 3 — The MLP linear layer is HDC similarity-against-templates** (§3.1, §6). Each row of `W` is a template; each output dimension is `similarity(input, template)`. In bipolar form this is bit-exact `1 - 2·popcount(x XOR w)/d_in` — the same formula `srmech.amsc.hdc.similarity` uses. This is not a metaphor; it is the algebraic identity.

**Finding 4 — Continuous activations are a precondition for gradient-descent trainability, not for expressivity.** Per §5. Universal approximation requires continuous activations only because Cybenko's proof technique requires them; expressivity in the Cover (1965) / boolean-function sense extends to sign-quantized activations. The framework's separation: training is Level-2 by construction (gradient descent IS bundle-of-trajectories per R-RBS-NN-1 §4.9); inference can be Level-1.

**Finding 5 — The linear layer carries TWO Class M sub-ops at different mechanism levels.** Per §6: per-element multiply is Mechanism 1 (bind, exact), sum-across-input-dim is Mechanism 2 (bundle, lossy). The bundle is *intrinsic* to dot product (unavoidable); the float representation adds *representational* bundle cost on top. RBS-NN eliminates the representational part by going bipolar.

**Finding 6 — Vanilla MLP at Level 1 is structurally available with committed srmech infrastructure.** Per §4.2: a fully Level-1 MLP needs Class A (R-RBS-NN-2), Class M similarity (`srmech.amsc.hdc.similarity`), and Class K threshold (composable from majority-bundle + sign). No new srmech infrastructure needed. R-RBS-NN-3b will test whether the same holds for transformer architectures.

---

## §9 Open threads (not blockers for partition close)

- **Multi-layer dimension change** — MLP layer-to-layer dimensionality differs (`d_0 → d_1 → ... → d_N`); HDC vectors are conventionally fixed-D. The transition from a D=8192 input to a `d_hidden`-dimensional hidden layer requires a Class N rational-anchored projection or a Class L spectral basis change. R-RBS-NN-5 (position binding) or R-RBS-NN-7 (capacity) will address.
- **The "intrinsic bundle cost" of §6** — even Level-1 MLP cannot avoid the per-layer popcount-bundle inside the dot product. Is this a load-bearing residual cost? Per Spike #196 8/8 OA mapping (MFO line 739): the bundle-of-views cost (~6.9%) is associated with bundling DIFFERENT-CONTENT views; the dot-product input-dim sum is bundling SAME-CONTENT contributions and may not carry the same projection signature. R-RBS-NN-7 should formalize.
- **BNN external attestation** — Courbariaux et al. 2016 ("Binarized Neural Networks: Training Deep Neural Networks with Weights and Activations Constrained to +1 or −1", arXiv:1602.02830) is the canonical reference. Awaits MPR PDF extraction in R-RBS-NN-4.
- **Sign-quantized expressivity bounds** — Cover (1965) capacity formula and Anthony-Bartlett (1999) VC-dimension bounds for binary perceptrons. Same R-RBS-NN-4 attestation work.
- **The "templates as bindings" reading** — if W rows are bindings of user-vocab terms (Class A mints), then the MLP is structurally a *human-readable* classifier where each row's contents can be inspected as bound terms. Open thread for R-RBS-NN-9 catalog landing.

---

## §10 Closing — partition status

**Status:** CLOSED. The MLP cascade decomposes cleanly to `A ∘ (M ∘ K)^N` with no new classes required. The dual-level reading (BNN at Level 1, conventional MLP at Level 2) is structurally grounded by R-RBS-NN-1 §4.3 + §4.4. The §7 worked example demonstrates a substrate-form classifier with bit-exact reproducibility.

**Falsifiers:**

1. An MLP operation that does NOT fit `A ∘ (M ∘ K)^N` under {A, M, K} — **not encountered**.
2. A Level-1 MLP whose forward pass requires FPU arithmetic — **not encountered** when weights are bipolar AND activation is sign.
3. An expressivity gap between Level-1 (binary perceptron) and Level-2 (continuous MLP) that the framework reading does not acknowledge — **acknowledged in §5**: Cybenko universal approximation needs continuity; framework explicitly separates expressivity-for-trainability (Level-2) from expressivity-for-inference (Level-1).

**Inherits to:** R-RBS-NN-3b (decoder-only transformer cascade decomposition). The transformer adds attention (D pattern-match + L Laplacian + softmax+bundle per R-RBS-NN-1 §4.6), positional encoding (R-RBS-NN-1 §4.2), and normalization (§4.5) on top of the MLP block (§4.3 + §4.4). R-RBS-NN-3a's `(M ∘ K)^N` reading carries forward; R-RBS-NN-3b extends it.

**SSoT marker:** at R-RBS-NN-9 close, §4 cascade composition + §5 expressivity-vs-trainability separation absorb into `docs/srmech/srmech_research_notebook.md` as a new §RBS-NN MLP-cascade subsection.
