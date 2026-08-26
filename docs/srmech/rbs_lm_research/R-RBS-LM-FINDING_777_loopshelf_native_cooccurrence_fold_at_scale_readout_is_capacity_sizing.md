# F777 — the §50.1 holographic co-occurrence loopshelf builds NATIVE at corpus scale (rc165); read-out quality is purely a CAPACITY-SIZING question (the lossy-correction principle, verified)

**Date:** 2026-06-15 · **srmech:** 0.7.5rc165 · **Composes:** F758 (the holographic-fold thesis + the over-capacity caveat + "loss is ONLY over-capacity superposition, sized around"), §50/§50.1 (the native fold, delivered rc165), F768 (the top-K=16 truncation discarded the spread — the fold keeps it), F119/F529 (the two-tier: exact payload + holographic associative tail), F774/F776 (the reasoner whose intersections this deepens) · **Queue:** task #218 · **Provenance:** `R-RBS-LM-LOOPSHELF_holographic_cooccurrence_tomes_native_fold.py` + a capacity-sweep probe.

## Built + measured (20k-article slice, the rc165 native fold)
- **5,497,275 tokens → 244,197 word-bundles in 28.2 s** (native `hdc.cooccurrence_fold`), store = **vocab × D/4 = 3.9 MB at D=64**. **BOUNDED fixed-width** (grows with VOCAB not EDGES — Heaps-sublinear), every co-occurrence SUPERPOSED (the full spread, not the top-K=16 the old assoc store kept — F768). **Deterministic** (fold×2 → similarity 1.0). → **F758's bounded-storage thesis is confirmed NATIVE at corpus scale.**
- API note (caught a self-misread): `cooccurrence_fold` returns `{"bundles":{tok:HV}, "codes":{tok:HV}, "vocab":[…], "n_tokens":int}`; read out a co-occurrence with `klein4_similarity(bundles[w], codes[c])` (bundle-vs-CODE, not bundle-vs-bundle).

## The read-out is a CAPACITY-SIZING question (F758, verified)
The naive read-out at **D=64 + no-IDF** is **over-capacity** — ~44M co-occurrences (stopwords included) folded into 64-symbol bundles → crosstalk + stopword domination: `tomato → beans, trying, gripped, fort…` (noise). This is exactly the F758 Result-2 caveat at scale, NOT a bug.

**Sizing around capacity recovers it** (stopword-filter + bigger D), measured on a 3k-article / 1.34M-token slice:
| D | tomato → | computer → | water → |
|---|---|---|---|
| 64 (under-capacity) | beans, trying, gripped, fort | science, ibm, climbing, age | turks, france, broad, carbon |
| 2048 (capacity-sized) | **color, beans, botany, fruit, fruits** | **science, programs, program, software** | **air, hydrogen, ice, earth** |

D=2048 gives **topical** read-out; D=64 is noise. Cost: D=2048 fold 201 s (vs 9.7 s) / store 24.5 MB (vs 0.8 MB) for the slice. So read-out quality = **"loss is ONLY over-capacity superposition, sized around" (F758)** — the very lossy-correction principle from earlier this session, now empirically confirmed: size D + IDF to capacity → lossless-enough read-out; under-size → crosstalk.

## What this settles vs leaves open
- **Settled:** the native fold makes the §50.1 loopshelf tractable at corpus scale (the python-only remnant is closed, rc165); the storage is bounded; the full spread is kept (F768's truncation undone); read-out is governed by capacity-sizing (D + IDF), verified.
- **The honest two-tier (F119/F529):** this is the **associative tier only**. The exact gloss text + relation edges stay LOSSLESS (the genome/chromosome payload, F758) — they are NOT folded away. The holographic store is the "what's near what" associative surface, sized to capacity.
- **Open (the integration, follow-on #223):** persist a **capacity-sized (D≥2048 + IDF) full-corpus** store, then wire it into Siona's assoc tier (replacing the top-K=16 store) + the F776 reasoner's intersection + the #221 spectral-aboutness read. The mechanism + operating point are now known; the production fold (D≥2048 over 240k articles) is an offline run (hours at D=2048 — or a smaller D with IDF; a capacity/cost sweep picks the point).

## Honest scope
- The slice (20k/3k articles) demonstrates the mechanism + the capacity law; the full-corpus build is the follow-on. Not yet wired into Siona (she still serves the exact stores — correct, lossless).
- D=2048 is illustrative of "capacity-sized," not tuned; the right D×IDF is a sweep (more capacity = better read-out, more compute/storage) — a Pareto choice, not a magic number.
- srmech-native fold (no `abs()`, no `Counter`); store HV-native; data outside the repo; CC-BY-SA.

## Verdict
The §50.1 holographic co-occurrence **loopshelf builds NATIVE at corpus scale** (rc165): bounded fixed-width, full spread, deterministic — F758's storage thesis confirmed. **Read-out is purely a capacity-sizing question** — over-capacity at D=64, topical at D≥2048 + IDF — the "loss is only over-capacity, sized around" principle verified end-to-end. The associative tier; exact payload stays lossless. Task #218's mechanism + operating point are delivered; the production capacity-sized full store + Siona-wiring is the follow-on (#223), which also unblocks #221 (spectral aboutness) and deepens #217 (the reasoner's intersections).
