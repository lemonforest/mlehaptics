# R-RBS-LM Finding 341 — #855 R1 / #812: non-associativity costs ≥96× store capacity — Klein-4 IS the store, loop-bind is the fiber op (the Klein-4-native instrument, measured)

**Date:** 2026-06-03 · **srmech:** 0.7.0rc25 (verified, UPSTREAM §18) · **#855 block:** R1 (Klein-4-native instrument) · **closes:** #812 (loop-bind capacity vs Klein-4) · **script:** `R-RBS-LM-R1_klein4_vs_loopbind_capacity.py` · **data:** `R-RBS-LM-R1_capacity_results.json`

## The load-bearing question

#855 R1 rests on the claim that the RBS-HDC store must be **Klein-4-native** (order-2 Z₂×Z₂, four sectors) — grounded by F200 (Klein-4 beats triality on sector-tagging contrast) and F158 (4× capacity from the four sectors). #812 asks the complementary question at the **bind** level: does the **non-associative octonionic loop-bind** cost capacity relative to the **associative+commutative Klein-4 XOR bind**, and does loop-bind need cleanup memory? This is the measurement that decides whether the store is Klein-4 or octonionic-loop.

## Method (srmech-native, rc25, D=8192, 5 trials, closed-set associative memory)

Store `S = bundle/superpose({bind(keyᵢ, valᵢ)})` of K pairs; recover each `v̂ᵢ = unbind(keyᵢ, S)`; **RAW** fidelity = `similarity(v̂ᵢ, valᵢ)`, **CLEANUP** accuracy = nearest of the K stored values == valᵢ. Sweep K; capacity = max K with cleanup-acc ≥ 0.90.

- **Klein-4:** `klein4_random` / `klein4_bind` / `klein4_bundle` / `klein4_unbind` / `klein4_similarity` (Z₂×Z₂, exact involutive bind).
- **Loop:** unit-octonion-block float vectors / `loop_bind_hd` / **real-vector superposition** (`np.sum` — *srmech ships no loop bundle*) / `loop_unbind_hd(key,S)` / `hdc.similarity` (octonionic Moufang, non-associative).
- Recovery conventions verified by 1-pair smoke: klein4 unbind **exact (1.000)**; loop unbind **already lossy at K=1 (0.9468)**.

## Result — non-associativity is catastrophic for the store

| K | Klein-4 cleanup-acc | Klein-4 raw-sim | Loop cleanup-acc | Loop raw-sim |
|---|---|---|---|---|
| 2 | **1.000** | 0.561 | 1.000 | 0.138 |
| 4 | **1.000** | 0.472 | 0.600 | 0.135 |
| 8 | **1.000** | 0.406 | 0.475 | 0.124 |
| 16 | **1.000** | 0.359 | 0.188 | 0.093 |
| 32 | **1.000** | 0.325 | 0.075 | 0.050 |
| 64 | **1.000** | 0.302 | 0.041 | 0.008 |
| 128 | **1.000** | 0.287 | 0.009 | −0.028 |
| 192 | **1.000** | 0.280 | 0.020 | −0.047 |

- **Klein-4 store capacity ≥ 192** (perfect cleanup retrieval at every K; **did not degrade at the sweep ceiling** — its true ceiling is the `klein4_bundle` majority-vote cap ~257, not the bind). Graceful raw-sim decay (0.56→0.28) that cleanup fully absorbs.
- **Loop-bind store capacity = 2.** Cleanup-acc collapses 1.0→0.475 by K=8 and to chance by K=32; raw-sim is already **0.138 at K=2** (vs the 0.9468 single-pair) — the non-associative crosstalk destroys the superposition almost immediately.
- **Ratio ≥ 96×** (≥192 vs 2), and the Klein-4 side is censored from above (didn't break).

## Verdict — CONFIRMED: Klein-4 IS the store; loop-bind is the fiber op

**Non-associativity costs ≥96× store capacity.** The associative+commutative Klein-4 XOR bind is a clean superposition store; the octonionic Moufang loop-bind is not — its non-associativity means `unbind(key, Σᵢ bind(keyᵢ,valᵢ))` does not cleanly isolate one term, so retrieval fails past K=2 even with cleanup. This is the bind-level confirmation of #855 R1 / F200: **the RBS-HDC store must be Klein-4-native.**

**Honest scoping (no-leaning — this is NOT "loop-bind is bad"):** loop-bind is the wrong tool for a *bulk associative store*, but it is the right tool for its actual role — the **order-aware sequence / Moufang fiber** op (F281/F290: the `loop_runbind_hd` prefix-peel, the un-flatten catalog's directed-bind fiber). The two ops partition by job, and that partition is **exactly the (4+3) bundle of R2**: the order-2 **Klein-4 is the base/store** (high-capacity, associative); the octonionic **loop-bind lives in the fiber** (the 7=4+3 sequence/gauge structure, low multiplicity, order-sensitive). So R1 doesn't reject loop-bind — it *locates* it: store ⇒ Klein-4, fiber ⇒ loop. This is the cleanest possible hand-off into R2.

## srmech gap (logged)

srmech ships `klein4_bundle` but **no loop bundle** — the loop leg fell back to a raw `np.sum` real-vector superposition. If loop-bind is to be used as a fiber-store at all, a native `loop_bundle` (and the question of what "bundle" means for non-associative octonion blocks) is the missing primitive. Recording for UPSTREAM (not a blocker for R1; loop is the fiber op, not the store).

## Discipline

srmech-native (`klein4_*` Class-M + `loop_bind_hd`/`loop_unbind_hd` + `hdc.similarity`); no hand-rolled similarity, no `abs()`, no `Counter`. Closed-set capacity is the standard associative-memory measurement; result reported straight (Klein-4 ceiling censored — stated, not hidden). Constants attested (D=8192 = 1024 octonion blocks; K-sweep dyadic; threshold 0.90; 5 trials, fixed seeds). Complements F200 (sector-tagging contrast) on the orthogonal bind-capacity axis — same conclusion: order-2 Klein-4 is the store structure.
