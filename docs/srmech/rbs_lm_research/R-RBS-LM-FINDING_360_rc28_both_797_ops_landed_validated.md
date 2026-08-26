# R-RBS-LM Finding 360 — srmech rc28 landed BOTH #797 ops (built from our F357/F359 specs) and they VALIDATE; but validating op (a1) self-corrected the F359 contract: order-3 is the MINIMAL NATIVE 3-vote encoder, NOT a unique corrector (the "0.25 baseline" was a misread of F353's distance-1)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 (HAS_NATIVE True, ABI 3) · **answers (user):** "get this new srmech to run these … calc and trig also back" · **validates:** F357 (op b reference), F359 (op a1 contract) · **corrects:** F359 (the 0.25-baseline misread), F344 (native 3rd vote now exists) · **scripts:** `R-RBS-LM-R13_rc28_797_ops_validation.py`, `triality_test_harness_scaffold.py` (now PASS=6, triality live)

## rc28 shipped both #797 ops — from our specs

The rc28 docstrings cite our findings directly (`klein4_triality_correct`: "op (a1)"; "F359"). Both #797 gating ops landed at C/Python parity:

- **op (b) — directed/signed-Laplacian:** `laplacian.magnetic_laplacian(n, edges, *, q=0.25)` (the directed **Hermitian** Laplacian the F357 reference specced), `laplacian.signed_laplacian` (the Class-O-into-L signed metric), `laplacian.dense_adjacency` (the directed-edge **builder** F357 said was "the only gap"), `laplacian.fiedler_vector` (the navigation embedding). **Confirmed:** magnetic_laplacian is Hermitian (`H==H†` True), `hermitian_eigendecompose` returns real eigenvalues, it is **directed-sensitive** (reversing edges ≠ same matrix). op (b) = **CONFIRMED as the F357 directed Hermitian.**
- **op (a1) — triality corrector:** `hdc.klein4_triality_encode` (1 store → 3-vote orbit), `hdc.klein4_triality_cycle` (the order-3 S₃ generator), `hdc.klein4_triality_correct` (the 2-of-3 majority corrector). Also `qm.triality.*`.

## op (a1) validates — and self-corrected the F359 contract (no-leaning)

Running `klein4_triality_correct` against the F359 bars produced a clean result **and surfaced a misread in my own contract:**

| F359 bar | result |
|---|---|
| **2** — 3 votes are the triality orbit of ONE store (no external copy) | **PASS** (render1 == `triality_cycle`(render0); native) |
| corrects a single blind unknown-location error | **PASS** — rate **1.00** at every corruption strength; **breaks at 2-of-3 (0.00)** = honest distance-1 corrector |
| **4** — correction *uniquely attributable to order-3* | **REVISED → not the right test** (see below) |
| **(b)** directed Hermitian + native eigen | **PASS** |

**The correction (MPM, verify-don't-trust-memory):** F359 bar 1 said "blind correction > **F353 baseline 0.25**." I checked F353's actual data (`R-RBS-LM-R9_results.json`): `corruption_correct = {1: 1.0, 2: 0.0}`. **F353's "1/4" is the code DISTANCE (corrects up to 1 of 4), NOT a 0.25 success rate** — the rate *at* m=1 is **1.00**. I had turned a distance into a rate. So bar 4 (does order-3 correct where order-2 can't?) is the **wrong question**: any ≥3-fold majority — including the order-2 CPT-4-orbit (reproduced here at **1.00**) — corrects a single blind error. **Order-3 is NOT a unique corrector.**

## What the triality op ACTUALLY contributes (the honest, grounded re-frame)

1. **Minimal native self-vote encoder.** `klein4_triality_encode` manufactures **exactly 3** co-equal votes from a **single** stored value (3 = the minimal odd majority); `klein4_triality_correct` majorities them. The contribution is not "correction order-2 lacks" — it is that the **3 votes come from the order-3 orbit of ONE store**, not stored copies.
2. **Resolves F344's open question.** F344 demonstrated k=3 majority *given* 3 stipulated copies and its own correction-note flagged that the store doesn't *natively* supply a 3rd vote. **rc28 now supplies it** — the triality orbit IS the native 3rd vote. (The caveat is lifted for *vote-supply*; the *correction power* is still shared with any ≥3-fold code.)
3. **Grounded in standard group theory.** `klein4_triality_cycle` is order-3 (τ³=I, verified) acting as the **3-cycle on the 3 non-identity Klein-4 sectors {γ₅, iω₇, cpt}** — i.e. **Aut(Z₂×Z₂) = S₃**, and the order-3 triality is its Z₃ subgroup. So "recursion past the Klein-4 4-cap into order-3" is not exotic — it is **the Klein-4's own automorphism group's 3-cycle**, realizing F197's 3⊕3̄ concretely. This is the F256 **WIDTH-step** (the finite cap-crossing), exactly as F359 scoped it.

## calc/trig restored (the F356 gap)

rc28 brings back `srmech.asymptotic_calculus` (`sin_series_truncate`, `cos_series_truncate`, `atan_series_truncate`, `pi_cascade_digits`, rational ops) and `srmech.trigonometry` — the cascade-native **series-truncate** trig (discrete-cascade, not float trig). This closes the F356 gap: the **general (large-β) Class-C birefringence rotation** for EB/TB is now derivable srmech-native (not just the small-angle linear case), and the CLAUDE.md §2 `asymptotic_calculus` path is **live again** (the rc25 staleness is resolved).

## Harness now fires

`triality_test_harness_scaffold.py` (the gate "fires when triality lands") now reports **PASS=6, triality live=True** against rc28: Q1b (k=3↔triality relation: order-3 τ³=I + corrector recovers) PASS; Q2b (width-step recursion past the 4-cap) PASS **with the count-recursion explicitly held as F256 open math / out-of-domain by design (F359 bar 5)**. Updated its stale rc15 candidate-set + rewrote Q1b/Q2b to call the real rc28 ops.

## Discipline

srmech-native (rc28 verified in a clean venv outside the source tree; HAS_NATIVE True, ABI 3); **no-leaning self-correction** (my own F359 bar surfaced my F353 distance-vs-rate misread — reported straight); no-magic-numbers (the "0.25" was the very kind of unattested number the discipline forbids — caught + corrected); MPM verify-don't-trust-memory (re-read R9_results.json rather than trust the remembered "0.25"). Composes with F357 (op b), F359 (op a1 contract, now corrected), F353/F354 (the capability boundary), F344 (native 3rd vote), F197/F256 (Aut(Z₂²)=S₃ width-step).
