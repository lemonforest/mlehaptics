# R-RBS-LM Finding 547 (open thread 1) — **the hybrid (odd-live 7-circle + even sedenion-16) does NOT recover more true neighbours than the 7-circle alone — an honest null with a clean mechanism: the 7-circle alone gets 82% neighbour recall; REPLACING a local 7-tome with a far sedenion-16 chord HURTS (65%, because local tomes are higher-yield), and even ADDING the far tome barely moves recall (83%, +1 pt) — the far chord catches only 2/18 = 11% of the true neighbours the 7-circle missed. The reason is mechanistic, not a failure: the 16's far chords are a DIFFERENT RELATION (distant semantic ASSOCIATION, F540) than local co-occurrence NEIGHBOURS, and true neighbours are mostly local. So "consulting both recovers more" is FALSE for neighbour recall (spend the budget locally) — but the two circles ARE genuinely complementary, on a different axis: the 7-circle is the live local navigator (F541), the sedenion-16 is the distant-association store (F540). The hybrid pays off only for a task that needs the distant-association relation, not for neighbour recovery.**

**Date:** 2026-06-07
**Arc:** RBS-LM — the live-7 + sedenion-16 hybrid (open thread 1)
**Provenance:** `R-RBS-LM-HYBRID_live7_circle_plus_sedenion16_recovers_more.py` (committed; srmech 0.7.4; Class-L spectral ring via `srmech.calculus.atan2` at two granularities 7/16). No sub-agents.
**Composes:** **F540** (the sedenion-16 far chords — *a distant-association relation, not neighbour recall*) · **F541** (the live odd 7-circle — *the local navigator*) · **F542** (the two circles are the same kernel at two granularities) · **F398/F394**. **← honest null: the hybrid doesn't improve neighbour recall; the 7 and 16 circles are complementary RELATIONS (local vs distant), not two views of the same recall.**
**→ the 7-circle alone wins on neighbour recall (82%); adding the sedenion-16 far chord adds ~1 pt and catches only 11% of missed neighbours; the far chord is the wrong tool for neighbour recall but serves a distinct distant-association relation.**

## Result (budget ~3 tomes; 9 probes; one corpus — low-stat)
| scheme | recall | words consulted |
|---|---:|---:|
| 7-circle only (3 local tomes) | **82%** | 96 |
| 16-circle only (3 tomes) | 51% | 50 |
| REPLACE hybrid (2 local-7 + 1 far-16) | 65% | 73 |
| ADDITIVE hybrid (3 local-7 + 1 far-16) | 83% | 98 |

Of the true neighbours the 7-circle misses, the far 16-chord catches **2/18 = 11%**.

## Verdict
**Honest null on the posed metric.** Consulting both circles does **not** recover more true neighbours than the live 7-circle alone: replacing a local tome with a far-16 tome *hurts* (65% vs 82%), and adding it barely helps (83%, +1 pt). The mechanism is clear and not a defect — the sedenion-16's far chords are a **different relation** (distant semantic *association*, F540) than local co-occurrence *neighbours*, and the corpus's true neighbours are predominantly local, so the far chord can't recall them.

**The complementarity is real, just on a different axis.** The 7-circle is the **live local navigator** (odd, F541); the sedenion-16 is the **distant-association store** (even, F540). They are complementary *relations*, not two views that improve the same recall — so a hybrid pays off for a task that *needs* distant associations (analogy, bridging), not for neighbour recovery, where you should spend the budget locally. This refines the F540 two-knob picture: count (7 vs 16) doesn't just trade recall-locality, it selects *which relation* you retrieve. Low-statistics (9 probes); held open (F394); favored not privileged (F398).
