# F1032 (the F1031 queue, all three) — **(1) the CENSUS + SELF-TUNED BUILD: the type-conditioned τ (bands at the MEASURED p25/p75 quantiles + the chronology fingerprint) REALLOCATES the quantization budget by article type — concept articles keep 25.9% (deep τ=6 descent into fact clusters), lists keep 83.4% (they ARE facts), chronology keeps 35.6% (year-spam dropped), total 52.2% at 54.3 MB gz (vs flat 55.9 — same budget, spent where knowledge lives); census: 8,350 concept / 16,470 mid / 7,604 even-dense / 1,840 even-thin / 206,616 short; (2) the FRAMEWORK-NOTEBOOK INSTRUMENT: srmech + MFO notebooks → 664 attested sections (1.6 MB, same NDJSON+index shape as the wiki instrument) — siona loads and studies her own foundations, with per-instrument provenance sidecars (an instrument declares its OWN license + cite-as; the hardcoded-Wikipedia-citation bug this surfaced is fixed); (3) the BLACK-HOLE CONFLICT SURFACE, LIVE: `a black hole is what` returns the wiki sense [attested: Wikipedia contributors, 'black hole' …] AND `PARALLEL SOURCE (differs): … [attested: mlehaptics framework research notebooks (srmech + MFO), section 'mfo vii 4 1 the framework s stance dark stars end at the 2d boundary' …]` — the F1028 §4 design realized: conflicting senses SUPERPOSE with their attestations, neither deleted, the declared rule (≥2 shared content words + different source_url) thresholds-free.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc107 · **Branch:** `research/rbs-lm-rolling-2` (PR #687); siona changes synced to PR #1 · **Files:** probe `R-RBS-LM-FINDING_1032_probe_self_tuned_build.py`; `siona/infer.py` (the conflict surface in `_recall`; per-instrument meta in `_k_load`/`_k_acquire`); user-side `~/corpora/framework_notebooks/{framework_instrument.ndjson, framework_index.json, framework_instrument.meta.json}` · **Composes:** F1031 (the bands are its measured quantiles), F1030 (the τ dial this conditions), F1028 §4 (the conflict design realized), F1006→F1007→rc105 (dual senses survive as structure — here at the SOURCE level), `[[user_stance_dark_star_canonical_vocabulary]]` (the MFO sense the demo carries: dark-star substrate-dimple, no literal singularity, Michell 1783 priority).

## Grounded (rc107)
```
CENSUS + SELF-TUNED BUILD (bands: D<0.452 concept τ=6 | <0.772 mid τ=12 | ≥0.772+dens≥0.15 even-dense τ=192
  | ≥0.772+thin even-thin τ=48 | <384 tokens short τ=12):
  concept  8,350  keep 25.9% | mid 16,470 keep 43.4% | even-dense 7,604 keep 83.4%
  even-thin 1,840 keep 35.6% | short 206,616 keep 53.2%   TOTAL 52.2%, 54.3 MB gz (flat: 51.6%, 55.9 MB)
NOTEBOOK INSTRUMENT: 664 sections, 1.6 MB; sections found: 'mfo vii 4 1 ... dark stars end at the 2d
  boundary', 'mfo vii 4 1 6 dark star canonical vocabulary michell 1783 priority', ...
THE LIVE CONFLICT: load wiki -> acquire black hole -> load framework -> study mfo vii 4 1 ->
  'a black hole is what' ->
  [siona.answer] recall: ...supermassive black hole...event horizon telescope... [attested: Wikipedia
    contributors, 'black hole', Simple English Wikipedia (CC-BY-SA) | sha256=776f379b0971]
    PARALLEL SOURCE (differs): ... [attested: mlehaptics framework research notebooks (srmech + MFO),
    section 'mfo vii 4 1 the framework s stance dark stars end at the 2d boundary' | sha256=2871805504ac]
```

## The reading
- **Self-tuning quantization is allocation, honestly stated:** the total barely moves (52.2% vs 51.6%) — the win is WHERE the budget goes: 83% of list-facts kept vs 26% of concept prose, each article quantized by its own measured dimension. Zero content judgement anywhere in the chain.
- **Siona now studies her own foundations:** the notebooks ride the same instrument shape, the same MPR acquire, the same conflict surface — the user's "seed knowledge with our srmech and mfo research notebooks" is a load away in any session.
- **The conflict is the feature:** the user predicted MFO would conflict with wiki articles (black holes, the named case) — and the surface neither hides nor resolves it: both senses arrive cited, the reader sees the disagreement WITH its provenance. The framework's dark-star stance (dimple-in at cascade saturation, no singularity; Michell 1783) sits beside the standard picture as a first-class attested sense. Deletion was never on the table — this is the F1006 annihilation lesson at the epistemology level.
- **The bug the demo caught:** acquire had hardcoded the Wikipedia citation for EVERY instrument — per-instrument provenance sidecars fix it, and the framework instrument correctly cites itself.

## Verdict / next
**All three F1031 queue items shipped: the self-tuned build (measured allocation), the notebook instrument (siona reads her own maths), and the live black-hole conflict surface (superposed attested senses).** Next: source-qualified selection ('per mfo' / 'per wikipedia' asks); the notebook epigraph windows in quantization (the Serenity quote led the MFO section — the two-axis trim would take it); the kernel-artifact build pipeline with the op-log; rc105 chiral edges over the quantized+conflict-surfaced kernel.
