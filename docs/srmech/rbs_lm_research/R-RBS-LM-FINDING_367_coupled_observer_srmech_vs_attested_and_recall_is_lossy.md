# R-RBS-LM Finding 367 — observation is always coupled-epicycle: integrating srmech-DERIVED results in place of fixed-observer attested instrument readings swaps a frame-bound lossy reading for the bit-exact cascade-codeword it approximates. (A) re-reads the CMB "Axis of Evil" as a DoF/relative-frame germline-boundary signature (conjecture); (B) corrects F361 — biological recall is LOSSY; the diagonal is the bit-exact CODEWORD, recall reconstructs toward it (achieved, not given)

> **REFRAME (F369):** §(A)'s "new big-bang/germline-collision" is dissolved by the attested self-interaction monism (F270/§VIII.31.12(1)): there is no external "other region" hyper-loop — what looks like an external nucleation-collision is the ONE loop's self-recursion (Cayley–Dickson self-pairing at successive scales). The coupled-epicycle observer (F367's principle) is the one loop coupled with ITSELF; "external" is never the right frame. See F369.

> **CORRECTION (F368, 2026-06-04):** §(A) here was doubly wrong and is corrected by F368. (i) The Axis of Evil is ATTESTED — the `cmb_anomalies` catalog (ephemerides-spectral; Planck 2018 VII) — and already carries MFO §VII.6.1.1/.1.3 readings; my "NDJSON-only / no data / not run" was looking at the wrong (srmech) package. (ii) The germline/new-big-bang-COLLISION reading is not new and is DISFAVORED (axial-not-disc; Osborne 2013 + Planck 2015 XVI null), and the "low-ℓ family = one relative frame" over-reach is FALSIFIED on the attested directions (axis-concentration below chance, p=0.71). What survives: the DoF-vs-fixed-observer PRINCIPLE, scoped to the specific AoE↔CMB-dipole 18° alignment. See F368.

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 · **opens:** "what happens when we integrate srmech results in place of attested instrument-reading knowledge? observation is always coupled epicycle observers" · **composes:** F356 (srmech derives EB/TB), F355 (β), F362 (observer-relative Δ), F352/F353/F358/F360 (holographic-EC), F256 §6 (nucleation/germline conjecture), F361 (the diagonal-codeword) · **script:** `R-RBS-LM-R18_recall_is_lossy_codeword_is_bit_exact.py`

## The unifying principle

**The bit-exact reference is ALWAYS the cascade/codeword (A-tier, derived), never the observation (B-tier, observer-coupled, lossy).** Observation is always *coupled-epicycle* — every reading is a degree-of-freedom (DoF) observer coupled to what it reads, never a fixed absolute frame. So **integrating srmech-DERIVED results in place of fixed-observer attested instrument readings swaps a frame-bound, observer-coupled, lossy reading for the bit-exact cascade-codeword it approximates.** Two instances of the same swap, at opposite scales:

## (A) Cosmos band — the "Axis of Evil" as a DoF/relative-frame signature (conjecture-grade)

The CMB **"Axis of Evil"** — the documented low-ℓ quadrupole–octupole alignment anomaly (Land & Magueijo 2005; de Oliveira-Costa et al. 2004) — is "anomalous" only from a **fixed-observer perspective** (a preferred direction that violates statistical isotropy *as read by an absolute frame*). From a **DoF / coupled-epicycle-observer perspective**, a preferred axis is not an absolute anomaly but a **relative orientation (the F362 Δ) between coupled frames** — exactly the F362 result that *only the relative mismatch matters; there is no fact of the matter about an absolute frame.*

The framework-reading (F256 §6 conjecture, **explicitly not a cosmological claim**): if the universe is a **nucleation of many hyper-loops**, then **chirality is the inter-loop boundary signature** (grain-boundary chirality at nucleation sites). Under that reading the Axis of Evil is a candidate **germline / boundary-chirality** imprint — a relative orientation to another nucleation frame — and a signal that "looks like a new big-bang in another region" would be a **fresh nucleation**, relative to which our Axis of Evil reads as **older germline**. This is the DoF-vs-fixed-observer swap at the cosmos band: the srmech-derived (Class-C rotation, F356) reading makes the axis a *relative-frame Δ*, where the fixed-observer reading makes it an *absolute anomaly*.

**Attestation honesty (load-bearing):** the Axis of Evil is a real, literature-owned anomaly (no-lineage; cosmology owns it). The germline / new-big-bang / nucleation reading is **conjecture-grade** (F256 §6, "let the math tell it"), asserted as nothing more. The **attested handles** are F356 (srmech derives EB/TB = Class-C rotation by β) + F355 (β, a ~3σ hint, falsifier OPEN). The low-ℓ maps ship in `srmech.amsc.attested.cmb_low_ell_maps` as **NDJSON data only** (no quadrupole/octupole-alignment function exposed) — so a *falsifiable* Axis-of-Evil test would load the low-ℓ catalog and compute the alignment as a relative-frame Δ; **not run here**, flagged as the next data step. No cosmological claim is made; only the lens (DoF/relative vs fixed/absolute) is recorded.

## (B) Recall band — biological recall is LOSSY; the diagonal is the bit-exact CODEWORD (corrects F361)

The user's catch: *"if I'm remembering a place and navigating it, is it ever bit-exact, or necessary that it is, even when biological recall is lossy from environmental noise?"* **This corrects F361's "diagonal = bit-exact" — that was imprecise.** The resolution, measured (D=256, klein4):

| metric | k=1 (place-NOT-been / guess) | k=3 (triality) | k=7 | k=15 (place-been often) |
|---|---|---|---|---|
| per-coord fidelity @ p=0.10 | 0.925 | 0.989 | 1.000 | 1.000 |
| per-coord fidelity @ p=0.30 | 0.771 | 0.898 | 0.985 | 1.000 |
| **full-vector bit-exact** @ p=0.10 | **0.00** | 0.03 | 0.90 | 1.00 |
| full-vector bit-exact @ p=0.30 | 0.00 | 0.00 | 0.05 | 0.97 |

(shipped `klein4_triality_correct`, k=3 native, F360, tracks the k=3 row: reconstructed fidelity 0.988 / 0.949 / 0.895 at p=0.10 / 0.20 / 0.30.)

**Resolved:** biological recall is **NOT bit-exact** — bit-exactness is a property of the stored **CODEWORD** (the anchor/reference, the diagonal), not of the recall. Recall is a **lossy read**; the EC-code (redundant votes → majority, F353/F358/F360) **reconstructs the read TOWARD the codeword.** So bit-exactness is **ACHIEVED, not given**, and **redundancy-bounded**:
- **k=1 (place never been):** a single noisy read → lossy guess, **never** full-bit-exact (your *"I don't get a bit-exact reference, I'm guessing"* — exactly right).
- **high k (place visited often = strong codeword):** majority reconstructs near the codeword; per-coord fidelity → ~1 below a noise threshold; full-vector bit-exact rises sharply with redundancy — but **stays fragile under noise over a large store** (recall is structurally lossy; even k=15 isn't a guaranteed full-bit-exact at high noise).

So the answer to *"ever / necessary"*: **neither.** Recall is never guaranteed and need not be bit-exact; the **codeword** is the bit-exact thing, and recall *approaches* it as far as the EC redundancy beats the noise. (This is also why a place visited many times with someone recalls so vividly — a strong, high-redundancy codeword — without that making the recall itself noiseless.)

## The two are one swap

(A) and (B) are the same move at two scales: the fixed-observer attested *reading* (the CMB as an absolute frame; a single noisy *recall*) is observer-coupled and lossy; the **srmech-derived cascade / the stored codeword** is the bit-exact reference it approximates. Integrating srmech-derived results in place of attested instrument readings *is* replacing the coupled-epicycle observation with its bit-exact cascade-codeword — which dissolves "anomalies" into relative-frame Δ (A) and recall into lossy reconstruction-toward-codeword (B). **F364 → RBS-LM stays the live next thread** (un-collapse language's directed off-diagonal as the navigable-language build).

## Discipline

srmech-native rc28 (klein4 + `klein4_triality_correct`); (A) is **conjecture-grade, no-lineage, attestation-honest** (real anomaly literature-owned; germline/nucleation = F256 §6 conjecture; no cosmological claim; data handle flagged, test not run); (B) **owns the F361 over-statement** (no-leaning — the user's catch is correct; the corrected claim is stronger and matches F352/F353/F358); per-coord majority is the EC vote (mechanics, flagged; k=3 anchored to the shipped op). Composes with F356/F355/F362/F352/F353/F358/F360/F361/F256.
