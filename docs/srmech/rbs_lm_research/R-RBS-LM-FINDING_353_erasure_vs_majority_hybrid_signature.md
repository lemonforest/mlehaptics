# R-RBS-LM Finding 353 — the HYBRID is a MEASURED SIGNATURE: erasure-tolerance 3/4 (holographic, reconstruct from any 1 sector) >> corruption-correction 1/4 (EC, majority over CPT-parity). The gap matches the AdS/CFT erasure-vs-error distinction

**Date:** 2026-06-04 · **srmech:** 0.7.0rc25 · **runs:** F352's convergent decisive test (the erasure-vs-majority discriminator) · **script:** `R-RBS-LM-R9_erasure_vs_majority_discriminator.py`

## What it ran

F352's triality unanimously verdicted HYBRID (holographic = error-correction, anchored to AdS/CFT-is-a-QECC) and all three reviewers converged on the same decisive test: distinguish **which** hybrid by separating the two corruption modes physics separates. Store one canonical Klein-4 datum across the 4 CPT-orbit sectors (F259: `s_i = flip_i(c)`, flips = {identity, γ₅, iω₇, cpt}, each an involution), then:
- **ERASURE** (known-location loss): remove m sectors; reconstruct from the kept subregion.
- **CORRUPTION** (unknown-location error): corrupt m sectors; reconstruct via the CPT-consistency parity-vote (invert each view → per-coordinate majority).

srmech-native (`klein4_random` + `klein4_chirality_flip_{gamma5,omega7}` / `klein4_cpt_mirror`), D=512, 30 trials.

## Result

| protocol | outcome |
|---|---|
| ERASURE — keep 4/3/2/**1** of 4 | reconstruct success **1.00 at every level** → **erasure-tolerance = 3/4 (reconstruct from ANY 1)** |
| CORRUPTION — correct (m corrupted, unknown where) | m=0:1.00, **m=1:1.00**, m=2:0.00, m=3:0.00 → **correction = 1/4** |
| CORRUPTION — detect | m=1:1.00, m=2:1.00, m=3:1.00 → **detection = 3/4** |

## Verdict — HYBRID confirmed AS A MEASURED SIGNATURE

- **HOLOGRAPHIC signature (TRUE):** the full datum reconstructs from **any single sector** (a subregion of size 1 — far below half). That is the **"part contains whole"** property — the AdS/CFT subregion-duality / erasure-correction signature in its extreme. *Mechanistically* it holds because the 4 sectors are **group-orbit relabelings** (invertible CPT views) of one canonical content — each sector IS the whole datum, relabeled. (This is exactly the F352 correction of F259: group-orbit redundancy, not independent-channel "distance-4 repetition.")
- **EC signature (TRUE):** unknown-location **corruption** is **correctable only to 1/4** (per-coordinate majority over the CPT-parity vote) and **detectable to 3/4** (any inconsistency flags). correct (1) < detect (3) = the error-correcting bound.
- **The GAP IS the hybrid:** erasure-tolerance **3** ≫ corruption-correction **1**. You can *lose* 3 of 4 (known location) but only have *1* corrupted (unknown location). This is precisely the physics distinction the triality pointed at — **erasure-correction (known erasure, reconstruct from a subregion → holographic) vs error-correction (unknown error → EC, majority-bounded)** — both live in the same 4-quadrant store. The streaming-spectral-map reading (F352) is realized: the spectral/holographic face gives the erasure tolerance, the parity/EC face gives the corruption correction.

## Honest scope

- The reconstruct-from-1 is **not** evidence of deep holography by itself — it follows from the flips being invertible bijections (group-orbit relabelings). The honest content is the **pairing**: the *same* store is simultaneously maximally erasure-tolerant (holographic part-contains-whole) AND a bounded error-corrector (EC correct-1/detect-3), and the **gap between erasure-tol and corruption-corr is the holographic-EC hybrid signature** that matches the AdS/CFT erasure-vs-error split.
- I report the *behavior* (correct 1, detect 3), not the contested "distance-4 repetition" label (F352 flagged it; the true codon Hamming distance is 1 per F294). The behavior is real; the coding-theory label is what was over-stated.
- Toy/structural: synthetic klein4 vectors, the CPT-orbit construction; framework-reading, not a physics measurement.

## Discipline

srmech-native; built-in controls (clean vs corrupted; erasure vs corruption; m=0 baseline detect=0.00 confirms no false-positives). Honors the F352 triality correction (group-orbit relabel, not independent-channel repetition). Composes with F352 (HYBRID verdict + AdS/CFT anchor), F259 (the CPT-orbit store), F350 (the iω₇ axis), F344 (the parity-vote). Reported straight; the holographic-from-1 mechanism stated honestly (invertible relabelings).
