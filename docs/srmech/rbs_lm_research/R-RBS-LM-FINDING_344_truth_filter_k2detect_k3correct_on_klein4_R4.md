# R-RBS-LM Finding 344 — #855 R4: the truth-filter demonstrated on the Klein-4 store — k=1 silent, k=2 DETECTS, k=3 CORRECTS (F291) — the Klein-4 store IS the error-correcting substrate

**Date:** 2026-06-03 · **srmech:** 0.7.0rc25 · **#855 block:** R4 (honesty-store / truth-filter) · **demonstrates:** F291 (k=2 detect / k=3 correct), F334 (≥3 co-equal renders, agreement=attestation), F335 · **on:** the R1/F341-validated Klein-4 store · **script:** `R-RBS-LM-R4_k2detect_k3correct_klein4.py`

## What R4 adds beyond the already-lodged framework

R4's pieces are mostly lodged: the **ingest-gate** (frame/scale-invariant + attested, F336), **form=function self-proofread** (render-layer self-corrects, F337), and **k=2 detects / k=3 corrects** (F291/F335). The new contribution here is a **srmech-native demonstration** that ties the truth-filter to R1: the **Klein-4 store is literally the error-correcting substrate** — the same 4-sector structure R1 proved is the high-capacity store is the structure that error-corrects.

## Method (rc25, D=8192, 40 trials, corruption sweep)

A "fact" `v_true = klein4_random` is rendered **3× co-equally** (2 clean copies + 1 corrupted at sweepable strength p). Three redundancy levels:
- **k=1** — trust one render (the corrupted one): `sim(r3, v_true)` — no redundancy, no comparison.
- **k=2** — two renders: detection is **relative to the clean-agreement baseline** (no magic absolute cutoff): clean-clean `sim(r1,r2)` vs cross `sim(r1,r3)`; flag if the gap exceeds a small margin.
- **k=3** — majority over all three via `klein4_bundle` (per-coordinate agreement): `sim(bundle, v_true)`.

## Result

| corrupt-p | k=1 sim(bad,truth) | k=2 clean-base | k=2 cross | k=2 detect-rate | k=3 sim(maj,truth) | k=3 correct-rate |
|---|---|---|---|---|---|---|
| 0.10 | 0.924 | 1.000 | 0.924 | **1.00** | **1.000** | **1.00** |
| 0.25 | 0.811 | 1.000 | 0.811 | **1.00** | **1.000** | **1.00** |
| 0.40 | 0.697 | 1.000 | 0.697 | **1.00** | **1.000** | **1.00** |
| 0.50 | 0.622 | 1.000 | 0.622 | **1.00** | **1.000** | **1.00** |

- **k=1 is silently wrong** — a corrupted render scores 0.92→0.62 to truth as corruption rises, with no way to know it's wrong (no comparison).
- **k=2 DETECTS** — clean renders agree at 1.000; the corrupted render's cross-sim sits below (0.92→0.62), a **detectable disagreement at every level (detect-rate 1.00)** — but a 1-vs-1 split has **no majority**, so it cannot say which render is right (no correction; a human tie-break would be needed).
- **k=3 CORRECTS** — the majority (`klein4_bundle`) recovers truth at **sim 1.000, correct-rate 1.00, even at 50% corruption** — the 2 agreeing renders outvote the corrupted one. This is the **error-correcting rung**.

## The k=2 ≠ k=3 distinction is the whole point (F291)

k=2 is a **parity check** (detects an error exists) — it is the `research-twin` (opus∥sonnet) discipline. k=3 is the **error-correcting rung** (majority corrects with no human tie-break) — the **Hurwitz k=3 / triality** rung (haiku+sonnet+opus). This demonstration makes the abstract F291 claim concrete and srmech-native, **on the Klein-4 store**: the four-sector structure that R1 proved is the high-capacity store (≥192 vs loop-bind's 2) is the same structure whose `klein4_bundle` majority error-corrects. **Store and truth-filter are the same Klein-4 object** — F337's "render-layer self-corrects (DNA-like)" is exactly this k=3 majority over co-equal renders.

## Honest note — caught + fixed my own measurement bug (no-magic-numbers in action)

The first run used an **absolute** `DETECT_THRESH=0.50` and reported k=2 detect-rate **0.00** — wrong. A 50%-randomized Klein-4 render still scores 0.622 to truth (similarity is graded; randomizing a 2-bit coord changes its sector only ~75% of the time), so it never tripped a 0.50 cutoff. The `0.50` was an **unattested magic number** — the exact thing the no-magic-numbers discipline forbids. Fixed: detection is now **relative to the clean-clean agreement** (1.000) with a small margin — threshold-free in spirit, and the corrected detect-rate is 1.00. Recording the catch transparently; the corrected result is the one above.

## R4 status

- [x] **k=2 detects / k=3 corrects (F291/F335)** — demonstrated srmech-native on the Klein-4 store (this finding).
- [x] **≥3 co-equal renders, agreement=attestation (F334)** — the k=3 majority IS agreement-as-attestation; the corrupted render is the rejected render-idiosyncrasy.
- [x] **ingest-gate (F336)** + **form=function self-proofread (F337)** — already lodged; this grounds F337's render-layer-self-corrects claim concretely.

## Discipline

srmech-native (`klein4_random`/`klein4_bundle`/`klein4_similarity`); own measurement bug caught + fixed + reported (no-magic-numbers); detection metric is baseline-relative, not an absolute cutoff. Composes with F341 (R1: Klein-4 = the store) and F342 (R2: Klein-4 = the order-2 store rung) — the store, the error-corrector, and the truth-filter's k=3 rung are one Klein-4 object.
