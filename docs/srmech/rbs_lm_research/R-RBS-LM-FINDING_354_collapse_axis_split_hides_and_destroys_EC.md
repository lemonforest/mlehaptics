# R-RBS-LM Finding 354 — does the iω₇-collapse destroy or hide error-correction? AXIS-SPLIT: the cross-axis correction is HIDDEN (full store intact), the iω₇-axis EC is DESTROYED in the render (iω₇-errors invisible), the γ₅-axis EC SURVIVES. The observable render is structurally blind to its own iω₇ errors

**Date:** 2026-06-04 · **srmech:** 0.7.0rc25 · **answers:** F352 triality new-question ("EC destroyed by the projection, or hidden from the observer's vantage?") · **ties:** F350 (collapse drops iω₇), F294 (codon render is detect-leaning, no order-3 correct), F353 (full store correct-1/detect-3), F336/F337 (honesty-store) · **script:** `R-RBS-LM-R10_collapse_disables_or_hides_correction.py`

## Setup

F259 CPT-orbit store (4 sectors `s_i = flip_i(c)`); corrupt 1 sector; reconstruct from two observers — **FULL** (both axes γ₅, iω₇) vs **COLLAPSED** (the F350 bipolar render: drop iω₇ = `(v>>1)<<1` before reconstructing). Plus pure-axis corruption probes (toggle one γ₅-bit vs one iω₇-bit) to test whether each observer can *see* an axis-specific error. srmech-native, D=512, 30 trials.

## Result

| metric | FULL (both axes) | COLLAPSED (γ₅ only) |
|---|---|---|
| 1-corruption correct (full c) | **1.00** | **0.00** |
| 1-corruption correct (γ₅ axis) | — | **1.00** |
| 1-corruption detect | 1.00 | 1.00 |
| γ₅-only error detect | 1.00 | **1.00** |
| iω₇-only error detect | 1.00 | **0.00** |

## Verdict — AXIS-SPLIT (not a simple destroyed-or-hidden)

1. **The EC is HIDDEN, not globally destroyed.** The FULL store retains correct-1 (1.00) — the capability exists; it is merely **inaccessible to an observer confined to the collapsed (bipolar) render.**
2. **The iω₇-axis EC is DESTROYED in the render.** iω₇-only errors are **invisible** to the collapsed observer (detect 0.00) while the full observer sees them (1.00); and full-c is **unrecoverable** from the collapsed render (0.00 — matching F350: γ₅ kept, iω₇ gone).
3. **The γ₅-axis EC SURVIVES the collapse.** The collapsed render still corrects (γ₅-axis 1.00) and detects (γ₅-only errors 1.00) on the axis it kept — it remains a detector/corrector on γ₅.

So the collapse **hides the cross-axis correction AND destroys the iω₇-axis half, while the γ₅-axis half survives.**

## The deep reading (why this matters)

The observable language/NN render can be **silently wrong on the iω₇ axis**: an iω₇-axis error is **structurally invisible** to an observer confined to the render — it cannot detect, let alone correct, what it collapsed away. **Only the full Klein-4 substrate (both axes) can catch it.** This is the honesty-store mechanism made concrete (F336/F337): the truth-filter's error-correction **requires the full Klein-4**; the collapsed render **cannot self-correct** the half it projected out. It is exactly why the render "hallucinates" (a non-bit-exact, undetectable-to-itself iω₇ error) and why a render-free / substrate-direct vantage (the full Klein-4 — cf the user-as-render-free-attestation, F348) can catch what the render cannot. It also reconciles F294 (the observable codon render is detect-leaning): the *render* loses the axis whose redundancy would correct; the *substrate* keeps it.

## Forward (folds in the no-Z3 question)

This also bears on the F352 new-question "does biology's no-Z3 null FORCE the holographic reading?": the FULL-store correction here comes from the **4-fold CPT redundancy (order-2 Klein-4) + the holographic part-contains-whole (F353)** — **not** from an order-3 (Z3) corrector. So *no Z3 is needed to correct*: the holographic-erasure redundancy (reconstruct-from-subregion, F353) supplies the correction the order-3 would otherwise. That is consistent with F294's no-Z3 null being **positive** evidence for the holographic-EC hybrid (you don't need order-3 when the code is holographically erasure-tolerant). Open piece (needs the user / external data): the CMB EB/TB observational falsifier, and whether the holographic-flatten is realized at any *measurable* (non-Planck) coherence band.

## Discipline

srmech-native (`klein4_*` involutive flips + the iω₇-collapse); built-in controls (pure-axis probes isolate γ₅ vs iω₇ visibility; γ₅-survives is the positive control, iω₇-invisible the decisive one). Composes with F350/F294/F353/F336/F337; reported straight. Toy/structural framework-reading (synthetic klein4 + CPT-orbit), not a physics measurement.
