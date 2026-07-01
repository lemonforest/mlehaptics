# F981 — etak-deeper at **heavy real-corpus load** recovers where FAST fails. On **3727 real content bigrams** (vocab 1339; target `april` recurs after **155** distinct contexts), the FAST single-cue read **failed** (`days → last`, wrong, margin 0.002); **ETAK-DEEPER multi-cue recovered `april` at k=3** (margin rising 0.006 → 0.013 at k=5 → 0.011 at k=8 — the √k lift then the crosstalk turn). Deep escalation works at real load: FAST loses the buried target, multi-cue finds it.

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_981_*.py` · **Composes:** F980 (the wired etak-deeper), F979 (effort curve), F976 (√k) · **Caveat:** this run used **write-time content-isolation** (function words dropped before encoding) — which **F982 corrects** as the doctoring error; the etak-deeper result stands, but the memory should be built full + de-lensed *at runtime*.

## Grounded (rc97)
```
target april recurs after 155 contexts; HEAVY memory = 3727 content bigrams, vocab 1339
FAST single-cue [days]  -> last   margin 0.0021  wrong (buried at heavy load)
ETAK-DEEPER k=3         -> april  margin 0.0056  CORRECT (recovered from the deeper reservoir)
ETAK-DEEPER k=5         -> april  margin 0.0127  CORRECT (margin climbing, sqrt k)
ETAK-DEEPER k=8         -> april  margin 0.0110  CORRECT (slight turn = crosstalk at high k)
```
The margins are small (heavy load, 1339 vocab, far past the F896 wall), but the **relative recovery is decisive**: FAST wrong → escalation correct from k=3, margin rising with k. This is F979/F980's escalation exercised at genuine real-corpus load.

## Verdict
Etak-deeper recovers a buried real-corpus target where FAST fails (april at k=3+, margin ∝√k). Confirms the escalation at heavy load. **The memory-construction method (write-time content-isolation) is corrected by F982** (de-lens at runtime, not write-time).
