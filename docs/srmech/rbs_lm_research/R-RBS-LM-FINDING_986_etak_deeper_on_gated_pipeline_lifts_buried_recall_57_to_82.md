# F986 — **etak-deeper added to the gated pipeline lifts buried-target recall 57% → 82%** (+25pp). The two axes compose: the doc-freq gate (F985) routes to the right community-tome; **etak-deeper (F978–F981) reaches the buried target *within* it**. On doc-freq-gated tomes (max_tome 90), for content targets with ≥3 in-tome contexts (the multi-cue set): FAST-gated single-cue = **57%** (23/40); FAST-gated **+ etak-deeper** multi-cue escalation = **82%** (33/40) — **10 buried targets recovered that FAST missed**.

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_986_*.py` · **Assembles:** F985 (gated community-tome pipeline), F978–F981 (etak-deeper self-escalation), F984 (aboutness-gate), F976 (√k multi-cue) · **User direction (2026-07-02):** "add etak-deeper to the gated pipeline for buried targets." · **Scope:** framework/tool; sparse Klein-4 + `recursive_cut`; no dense/numpy/abs.

## Grounded (rc97, 39 gated tomes, 40 multi-context buried content targets)
```
FAST-gated (single cue)           : 57%  (23/40)
FAST-gated + ETAK-DEEPER (multi)  : 82%  (33/40)   <- +25pp; 10 buried targets recovered that FAST missed
```

## The reading (the axes compose)
- **Gate = the right tome (F985).** De-lensing the partition puts the content target in a coherent community-tome (routing). Necessary but not sufficient — inside a larger tome (max_tome 90), a target can still be *buried* (many pairs, the F896/F975 within-tome recession).
- **Etak-deeper = reach within the tome (F978–F981).** For a buried multi-context target, FAST single-cue fails (57%); escalating to multi-cue superposition (√k, F976) recovers it (82%) — 10 targets that were in the right tome but below the single-cue floor come back. The collapse-margin is the trigger; the multi-cue superposition is the reach.
- **Together:** gate (capacity/routing axis) + etak-deeper (recall-effort axis) = the full recall mechanism, both wired and measured on real corpus. The gate can't reach a buried target (it's the wrong axis); etak-deeper can't help if the target is in the wrong tome (routing failed). Each fixes what the other can't.

## Honest scope
Grounded: 57%→82% on multi-context buried content targets, real gated tomes, sparse Klein-4. The set is *multi-context* targets (≥3 in-tome contexts) — the natural etak-deeper set (single-context targets have no multi-cue to superpose). max_tome 90 (larger tomes → more within-tome burial → room for etak-deeper; at F985's ~93 the emission-gate was redundant, here the *escalation* is the lever). +25pp is the honest lift; not a fluency claim. Composes F985/F978–F981/F984/F976.

## Verdict / next
**Etak-deeper on the gated pipeline lifts buried recall 57%→82%** — the gate routes to the right tome, etak-deeper reaches the buried target within it; the two axes compose on real corpus. The full recall mechanism (full memory + doc-freq-gated de-lensed community-tomes + coherence + effort-adaptive etak-deeper + honest-STOP) is now assembled and validated. **Next:** tome-size sweep with both on (find the F896/F975 sweet spot); wire the FAST→etak-deeper escalation natively via `next_token_coherence` verdict + §80 gate.
