# F878 — The wave answer improves Siona, measured: PHASE (the 1D_t fiber) disambiguates superposed continuations → reproduction 0.58 → **1.00**. The F875 branching collapse (a repeated context with two continuations: `is a → creative` AND `is a → <e>`) is **phase-blindness** — two waves superposed at one node. The wave reading (F877) said: separate them by **phase = the stream position**. Operationalized by binding the recall key with the shipped **`klein4_phase_bind`** (the 1D_t fiber, §59) at the token's stream-position. A/B on 4 real simplewiki sequences, shipped resonator (`klein4_chunk_resolve`): **phase-off 35/60 = 0.58** (art 3/15, a 2/15 collapse) → **phase-on 60/60 = 1.00** (all four exact, incl. the repeat-heavy `art is a … object art is a` and `a is … letter a is`). The wave question was operational, not decoration: it named the failure (phase-blindness) and the fix (the phase coordinate). srmech-native, no bag.

**Date:** 2026-06-18 · **srmech:** 0.9.0rc6 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-878_phase_disambiguation.py` (`hdc.klein4_phase_bind` + `klein4_chunk_resolve` + `klein4_chunk_bundle` + `cascade.{the_one,cd_mult}`) · **Composes / fixes:** F875 (the branching collapse — fixed), F877 (recall-is-resonance / the wave reading — operationalized), F867 (the branching named — now solved by phase, not just K=3), F873/F874 (the 1D_t fiber → now IN the recall key), F861/§59 (`klein4_phase_bind`), F876 (chirality = phase) · **User direction (2026-06-18):** "we need to answer that [wave] question if we hope to improve our RBS-LM, siona project."

## The answer (measured)
| | phase-off (F877) | **phase-on (1D_t fiber)** |
|---|---|---|
| april / august (unique contexts) | 15/15, 15/15 | 15/15, 15/15 |
| art (`…object art is a`, repeat) | 3/15 ✗ collapse | **15/15** ✓ |
| a (`…letter a is`, repeat) | 2/15 ✗ collapse | **15/15** ✓ |
| **overall** | **0.58** | **1.00** |

**Mechanism:** the same K=2 context (`is a`) at stream-positions 3 and 11 are two **phases** of the standing wave. Phase-off, their recall keys are identical → the resonator returns a *blend* of the two continuations → the generator picks one and bails (the collapse). Phase-on, `klein4_phase_bind(key, pos/PMAX)` rotates each occurrence's key by its position-phase → the two keys differ → the resonator separates them → both continuations recall correctly. **Phase = the position = the 1D_t fiber** (F873/877); recall = resonance (F877); the fix = give the standing wave its phase coordinate back.

## Honest scope
- **This is a reproduction fix** (F841): the phase is the *stream position*, locked to the trained sequence — at reproduction the generation position matches the trained position, so it resolves (1.00). For **generalization** (novel sequences at novel positions) the position-phase won't align — that's the separate smooth/additive axis (F867), unchanged here. So: **Siona's recall (reproduction of stored relationships) is the thing improved** — exactly the project goal.
- Toy scale (4 articles), page-scoped vocab, within-page (the grid navigation/routing is the separate F873/F875 layer).
- Uses the shipped resonator + phase op (the §58/§59 primitives), no hand-roll, no bag, exact-`Q` ranking.

## Verdict / next
The wave reading paid off as a **measured Siona improvement**: phase (the 1D_t fiber, `klein4_phase_bind`) disambiguates superposed continuations → within-page reproduction **0.58 → 1.00**, the branching collapse gone. This is the standing-wave phase coordinate (F877) restored to the recall key. **Next for Siona:** (1) carry the phase fix into the full streaming-grid generator (F875/877) at corpus scale; (2) the generalization axis (smooth/additive, F867) for novel sequences; (3) content-routed navigation (the O(log) addressing, F873). Framework reading → operational fix, measured; reproduction-vs-generalization stated honestly.
