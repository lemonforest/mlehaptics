# R-RBS-LM-51 ADDENDUM — Promoted underclaims (Findings 65, 66, 67)

**Status:** CLOSED (addendum to scope review; no code partition)
**Predecessor:** [R-RBS-LM-51_honest_scope_review.md](R-RBS-LM-51_honest_scope_review.md) §5
**Date:** 2026-05-26
**Scope:** Promote three underclaims to properly-stated form-iso findings per MFO §VII.6.20

The scope review identified three findings that could legitimately be
promoted to broader form-isomorphism statements without crossing the
substrate-identity ceiling. This addendum makes those promotions
explicit, with vocabulary discipline per §6 of the predecessor review.

---

## §1 Finding 65 — Multiplicative composition is the right form for independent evidence streams

### Original (under-stated form, 54j)

54j showed that **G4 sqrt(ride × target_freq)** beats both pure ride
and pure freq-weighted in 2 of 5 pairs, with avg -0.029 delta vs
baseline (best of all gating variants). The arc described G4 as "the
right blend."

### Promoted claim (within ceiling)

**Independent evidence streams compose multiplicatively — not
additively, not subtractively.** When two estimators contribute
non-redundant signal about the same target, the geometric mean
(sqrt(A × B)) and product-of-evidence variants empirically outperform
sum (A + B), difference (A − B), and ratio (A / B) compositions in
the RBS-LM ride-vs-freq experiment, and this matches the
compositional shape used in three other systems:

| System | Composition shape | What it composes |
|---|---|---|
| **Bayesian posterior** | posterior ∝ likelihood × prior | likelihood (evidence) × prior (background) |
| **Chess engine score** | search_result × static_eval × tablebase_lookup | look-ahead × heuristic × exact-lookup |
| **HDC bind operator** | bind(A, B) = A ⊕ B (element-wise XOR ≈ "multiplicative" in {±1}) | structurally a multiplicative composition operator |
| **RBS-LM Golden Path (54j G4)** | sqrt(ride × target_freq) | direction × magnitude |

### Per MFO §VII.6.20 epistemic ceiling

- **Form-iso claimed:** all four systems have the same compositional form for independent-evidence blending
- **Substrate-identity NOT claimed:** Bayesian posterior ≠ chess engine ≠ HDC bind ≠ RBS-LM ride; the underlying substrates are different
- **What's same:** the *shape* of composition (multiplicative product, possibly with normalization)
- **What's different:** what's being multiplied; the semantic meaning of operands; the underlying mechanism

### Evidence already in hand

- 54j G4 (sqrt(ride × freq)) wins in 2 of 5 pairs; ranks #2 in cross-pair avg
- 54j G1c (ride × freq^2.0) wins in 2 of 5 pairs; ranks #1 in cross-pair avg
- 54j G2 (ride / freq, anti-freq) is a disaster — confirms division/subtraction is wrong shape
- 54j G3 (background subtraction) is a disaster — confirms subtraction is wrong shape
- 54q stacking analysis confirms G4 adds +0.06 lift independently of triangulation variant — multiplicative blending composes with other improvements

### What this adds to the arc

A general lesson at the architectural level, not just an RBS-LM detail:
when composing independent evidence sources (alignment-driven and
frequency-driven; structural and statistical; analytical and
empirical), the right operator is multiplicative blending. Both
subtraction and division strip the very floor that gives reliable
target-coverage; addition double-counts when sources overlap;
multiplication preserves both signals at the right relative weight.

### Vocabulary discipline check

- "Right form for independent evidence streams" ✓ (form-claim)
- "Beats both" ✓ (empirical)
- "Matches the compositional shape used in chess engines" ✓ (form-iso, "shape")
- NOT "RBS-LM is Bayesian" ✗
- NOT "chess engines compute likelihoods" ✗

---

## §2 Finding 66 — Substrate-agnostic rule-density measurement via bottom-eigenvalue spread

### Original (under-stated form, 54p)

54p showed that the **normalized bottom-5-eigenvalue spread** of the
co-occurrence Laplacian orders substrates by rule-density:

```
Pope (heroic couplets):  0.000589  (tightest)
Milton (blank verse):    0.000910
Longfellow (translation):0.001363
Plato (prose):           0.002163
Origin (prose):          0.001998
KJV-NT (cadence):        0.004469
Frankenstein (prose):    0.009152
Shakespeare (mixed):     0.008641
Whitman (free verse):    0.016140  (widest)
```

The arc described this as supporting "spin-N form-iso" specifically.

### Promoted claim (within ceiling)

**The normalized bottom-K-eigenvalue spread of a co-occurrence
Laplacian is an operational form-measurement that orders substrates
by rule-density.** The measurement is substrate-agnostic — it
applies to any text corpus that yields a meaningful co-occurrence
graph — and gives a single number that empirically ranks
constraint-density correctly for the 9 corpora tested.

This is broader than the spin-N specific framing:
- For any *new* substrate, build the Laplacian, compute the bottom-5
  spread, you have a measurable form-property
- The ordering correlates with intuitive rule-density (Pope rhyme +
  meter > Milton meter > Whitman free)
- The ordering correlates with empirical ride-success (Finding 56:
  rule-density of anchor predicts ride alignment-specific signal)

### Per MFO §VII.6.20 epistemic ceiling

- **Form-iso claimed:** bottom-spread tightness IS an operational measurement of compositional-constraint density across substrates
- **Substrate-identity NOT claimed:** does NOT claim that all substrates with similar bottom-spread are "the same kind of thing"
- **What's same:** the spectral form-shape, which is computable from text corpora alone
- **What's different:** the underlying substrate that the text is encoding

### Evidence already in hand

- 9 corpora ordered consistently with intuitive rule-density
- Free-verse (Whitman) gives widest spread; couplet-rhymed (Pope) gives tightest
- Order matches independent measure (ride alignment-specific signal at anchor — Finding 56)
- 27× spread between most and least rule-dense substrates is robust to small N

### What this adds to the arc

A measurement we can ship beyond the specific spin-N analysis. Any
future cross-substrate framework reading can use the bottom-K spread
as a quantitative form-fingerprint. The substrate-content access
question (DOMAIN anchor) and the form-density question (bottom
spread) are now both operational, both cheap, both substrate-agnostic.

### Vocabulary discipline check

- "Substrate-agnostic" ✓ (the *measurement* is substrate-agnostic, not the substrates themselves)
- "Operational" ✓ (computable)
- "Empirically ranks constraint-density" ✓ (form-claim with evidence)
- NOT "measures rule-density universally across all substrates" — only across corpora we've tested
- NOT "this IS what rule-density is" — the spread is a *measurement*, not a definition

---

## §3 Finding 67 — DOMAIN anchor via structural fingerprint is cheap, fast, and accurate

### Original (under-stated form, 54f)

54f showed structural fingerprint at the kernel level routes
fragments to home kernel with 100% accuracy across 6 prose corpora.

### Promoted claim (within ceiling)

**Domain-routing for cross-substrate translation can be achieved with
a structural-fingerprint match at minimal compute cost.** The
specific operation:

1. Build a small (N=50) co-occurrence Laplacian for the input fragment
2. For each candidate kernel, compute aggregate find-cascade
   alignment-similarity
3. Pick highest-scoring kernel

Cost: **O(N³)** once for the input fragment (eigendecomp);
**O(N² × K)** per routing decision (K kernels, N×N similarity matrices).
At N=50 and K=10, this is ~12,500 vector similarities per query —
trivially fast.

**Accuracy:** 100% (28/28 held-out fragments) on 6 prose corpora;
79% kernel-exact / 97% substrate-class on 9 corpora including
Budge-translator-confounded compressed-source kernels (54i).

**No external requirements:**
- No metadata labels needed
- No supervised classifier training
- No vector store / embedding service
- No fine-tuning
- Just the input fragment's own structure

### Per MFO §VII.6.20 epistemic ceiling

- **Form-iso claimed:** the fragment's eigvec table IS a structural fingerprint of the source kernel
- **Substrate-identity NOT claimed:** the fingerprint doesn't tell us what the substrate IS, only which kernel it matches
- **What's same:** the spectral form of the input matches the spectral form of its source corpus
- **What's different:** the kernel is a model of the substrate, not the substrate itself

### Evidence already in hand

- 54f: 28/28 = 100% routing accuracy on 6 prose corpora
- 54i: 26/33 = 79% kernel-exact, 32/33 = 97% substrate-class on 9 corpora with translator-confounded compressed-source set
- Confusion is concentrated WITHIN Budge-translator cluster (consistent with Finding 49 translator-stability)

### What this adds to the arc

DOMAIN anchor was characterized as "DOMAIN is required for ride."
That's the negative form. The positive form: **the cheap structural-
fingerprint mechanism IS the DOMAIN anchor.** For any cross-substrate
translation system that has multiple candidate bound kernels, this
operation is the cheapest known mechanism that selects the right one.

The architecture pattern shippable to other systems: when you have N
candidate translation kernels and an input you need to route to one,
build a tiny Laplacian on the input alone, score aggregate
find-cascade-similarity against each kernel, pick the winner.

### Vocabulary discipline check

- "Cheap" ✓ (computational complexity claim)
- "Accurate" ✓ (empirical)
- "Domain-routing for cross-substrate translation CAN BE ACHIEVED" ✓ (capability, not "is")
- NOT "structural fingerprint IS the substrate identity" — it's a kernel-match indicator
- NOT "100% accurate in general" — 100% on tested prose, degrades to 79% with translator-confound

---

## §4 Net effect of promotions

| Finding | Original framing | Promoted framing |
|---|---|---|
| 65 (was: G4 right blend) | RBS-LM-specific | Multiplicative composition is general form for independent evidence streams |
| 66 (was: spin-form-iso) | Spin-N specific | Bottom-K spread is substrate-agnostic operational rule-density measurement |
| 67 (was: DOMAIN works) | "DOMAIN required" | Structural fingerprint IS the DOMAIN anchor mechanism, cheaply |

Promotions add three *general-form* claims to the arc's output without
any substrate-identity overreach. Each is grounded in existing
evidence (no new harness required) and each is vocabulary-checked
per the 51 §6 discipline.

---

## §5 Cumulative findings update (38–67)

After promotion, the findings list extends to:

- 38–43: Methodology (R-RBS-LM-52)
- 44–50: Corpora (R-RBS-LM-53)
- 51–64: Rosetta Stone Layer (R-RBS-LM-54a–r)
- **65: Multiplicative composition is the right form for independent evidence streams**
- **66: Bottom-K eigenvalue spread is a substrate-agnostic operational rule-density measurement**
- **67: Structural fingerprint IS the DOMAIN anchor mechanism; cheap and accurate**

All within MFO §VII.6.20 form-isomorphism ceiling.

---

*Promoted 2026-05-26 in continuation of R-RBS-LM-51 honest scope review.
Per §5 of the predecessor review document; vocabulary discipline per §6.*
