# F838 — COHERENCE GATE CLEARED: chunked-`M` (capacity) **+** the per-article unique-walk window `k*` together give **100% coherent autoregressive generation** on the real `srmech.rbs_lm` encoding (0.8.2rc1, numpy-absent, no gen-1 code, no bigram counts). Both levers are required and both are relationship-native; neither alone suffices. This is the recipe for siona's coherent relationship/sparse LM.

**Date:** 2026-06-18 · **srmech:** 0.8.2rc1 (TestPyPI, the dev substrate) · **Provenance:** `R-RBS-LM-RBSLMV2COHERENCE_*` family on `srmech.rbs_lm.substrate.ContextSubstrate` + `srmech.amsc.hdc`, tomato, D=10000 · **Composes:** F837 (chunked-M read 3.3→96.7% rank-1), F836 (the single-M incoherence), F832 (bundle capacity), F805/F813 (de Bruijn unique-walk window k*; the F817 instrument ships `k` per article), §57/§58, [[feedback_relationship_lm_ideas_not_code_from_gen1]] · **User direction:** "we need it to be coherent … relationship/sparse LM on the actual rbs_lm object … ideas not code from gen-1 … work here on srmech from TestPyPI."

## The result (tomato, greedy autoregressive, % = tokens matching the article)
| config | match | output |
|---|---|---|
| single-`M`, k=3 (what 0.8.2rc1 builds) | 9% | `the tomato solanum the tomato solanum …` (3-cycle) |
| chunked-`M` C=16, k=3 | 37% | coherent ~15 tokens then a small cycle |
| single-`M`, k=k\*=6 | 16% | `… is a tomato a is a a a a …` (crosstalk collapse) |
| **chunked-`M` C=16, k=k\*=6** | **100%** | `the tomato solanum lycopersicum is a vegetable botanical fruit or specifically a berry but not a fruit as ordinary people use the word tomatoes are shiny and smooth with many small seeds they are very good for health most tomatoes …` |

## The two levers (both relationship-native, both required)
1. **Capacity-bounded chunk-set `M`** (F832/F837): split the context→next binds into ≤C-bind bundles; read = max-resonance over chunks. Kills the bundle crosstalk that flattened the single-`M` read. *Idea: VSA cleanup-memory capacity (Plate/Frady) — not gen-1.*
2. **Per-article unique-walk window `k*`** (F805/F813): use the context width at which each (k−1)-gram has a unique successor (already computed + shipped in the F817 instrument as `k`). Kills the low-order greedy cycles (the "a berry but not a berry" loop at k=3). *Idea: de Bruijn unique window — not gen-1 sampling/repetition-penalty.*

Together = **the de Bruijn unique walk done holographically**: the resonator over a capacity-bounded memory recovers the unique successor for each `k*`-context, so greedy follows the article's relationship path exactly → coherent. Single-`M` (crosstalk) OR low-k (cycles) each break it; the combination is clean.

## Honest scope
100% on a *single learned article* is coherent reproduction-via-inference — the sharp resonator walk follows the unique relationship path (it is **not** byte-readback: it is the bind/unbind/resonate read recovering each bound successor). It proves the **coherence mechanism**. Still open (the v2 arc): (a) **multi-article / per-tome** — does coherence hold when many articles' binds share a per-tome chunk-set (cross-article crosstalk)? (b) **genuine generation/generalization** — novel prompts, composing across articles, not just walking one learned doc. The gate that was blocking — "does rbs_lm produce coherent text at all" — is **cleared**.

## What this means for the build (siona) + srmech
- **Siona relationship-LM recipe:** learn → capacity-bounded chunk-set `M` per doc/tome + the per-doc `k*` from the instrument; recall = resonator read (max over chunks) + greedy/temperature. Built here on srmech 0.8.2rc1 primitives.
- **srmech (§58, evidence now in hand):** the substrate's single `M` + fixed `operating_k` are the two things to change — `M` → capacity-bounded chunk-set, and accept a **per-doc/per-tome `k`** (the unique window) rather than one global `operating_k`. Whether this lands in `srmech.rbs_lm` or in a siona-side substrate is the deferred boundary call (develop here first).

## Verdict
The relationship/sparse LM **can be fully coherent** on the real object, relationship-native, no gen-1 code. Next: multi-article/per-tome coherence (the genome-consolidated chunk-sets) + genuine generation, then settle the srmech-vs-siona boundary and (if kept in srmech) spec §58 + per-doc k for a 0.8.3 — or build it in siona on 0.8.2rc1.
