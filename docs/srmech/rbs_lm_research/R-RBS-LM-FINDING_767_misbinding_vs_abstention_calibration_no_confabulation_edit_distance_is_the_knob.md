# F767 — "no hallucination" measured, not asserted: no confabulation; misbinding gated to ZERO by edit-distance abstention (the floor is the wrong knob)

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F765 (the confabulation-vs-misbinding distinction + the Pass-1 edit-distance guard this probe characterizes), F762 (the abstract-layer form-resolver under test), F119/F529 (retrieval-only/attested = the no-confabulation construction), the project epistemic-honesty discipline (the deliverable is an honest measured claim handed to the expert, not a marketing absolute) · **User next-question (2026-06-15):** "maybe we can't claim no hallucination if it's inherent in synaptic neural net inference. would be good to discover." · **Provenance:** `R-RBS-LM-HALLUPROBE_misbinding_vs_abstention_calibration.py` (committed; the generating code).

## The question, made falsifiable
Two failure modes (F765): **confabulation** (fabricate content not held — eliminated by construction: Siona returns only stored, attested strings) vs **misbinding** (retrieve REAL attested content, bind it to the WRONG query — the nearest-neighbour failure mode, since NN always returns a *nearest* item unless an abstention threshold says "none"). So "no hallucination" is really *"(retrieval-only content) + (calibrated abstention)."* The probe **measures** the abstention calibration: it sweeps the two Pass-1 knobs — the similarity **FLOOR** and the **edit-distance RATIO** (`edit ≤ RATIO·len`) — over three input classes (known / near-miss typo / genuinely-unknown) and tabulates near-miss CORRECT, near-miss MISBIND, and unknown MISBIND per cell.

## What the grid showed (known=15, near-miss=13, unknown=8, verified vs the live genome)
| knob | finding |
|---|---|
| **unknown MISBIND** | **0 in every cell** — even at the loosest RATIO. Genuinely-unknown words (flibbertigibbet, borborygmus, …) are orthographically FAR from any store word (edit/len **0.58–0.85**), so the edit gate excludes them at any RATIO ≤ 0.50. |
| **similarity FLOOR** | **the WRONG knob.** Raising it 0.40→0.70 never zeroes misbinding — the wrong resolutions have HIGH sim (tomatto→tomatillo **0.89**, anmal→annual 0.78, earht→earthrise 0.73). It only collapses near-miss CORRECT (0.65+ kills good comprehensions like islnd→island 0.67, computre→computer 0.64). |
| **edit-distance RATIO** | **the EFFECTIVE knob.** At RATIO ≤ 0.35, near-miss MISBIND → 0 too (the wrong picks are edit-3-to-5; the correct ones are edit-1-to-2). |

**Clean cell exists:** RATIO ≈ 0.25–0.35, any floor → **near-miss misbind 0, unknown misbind 0**, near-miss correct ~46%. The **live F765 gate** (FLOOR 0.45, `edit ≤ max(2, len//3)` ≈ RATIO 0.33) sits squarely in this clean zone — the guard is well-calibrated.

## Verdict (the honest, measured claim)
- **Confabulation: eliminated by construction** (retrieval-only/attested — Siona never fabricates content).
- **Misbinding: gated to ZERO by edit-distance abstention** — and the live gate is calibrated into the clean zone. So the refined claim **"no confabulation; misbinding gated to zero by calibrated abstention"** HOLDS, and is now *measured*, not asserted. The blanket "no hallucination" was imprecise; this is the honest replacement.
- **The cost (an honest precision/coverage frontier):** zero misbinding caps near-miss recall at **~46%** — the other ~54% of typos **abstain** (honest asking-state) rather than risk a confident wrong answer. We deliberately sit at the precision-favoring end (better to ask than to misbind), consistent with the can't-hallucinate intent.
- **Misbinding is NOT inherent here** (the user's worry): because genuine unknowns are edit-far, the abstention cleanly separates them. Misbinding would only be *inherent* if unknowns sat as close (orthographically) as typos — they don't. The residual misbinds the gate declines are **glyph mis-RANKS** (tomatto's top glyph match is tomatillo, not tomato), not a fundamental NN limit.

## The lever this exposes (next inch)
The ~46% typo-recall ceiling is set by the *resolver's ranking*, not the gate: tomatto→tomatillo (edit 3) is the glyph-TOP, but tomato (edit 1) is right there. An **edit-distance-RANKED resolver** (pick the edit-closest among glyph-plausible candidates, not the glyph-top) would convert several declined typos into correct comprehensions WITHOUT raising misbinding (it only re-ranks within the already-gated set). That lifts recall along the precision-preserving direction — the concrete improvement F765 flagged, now quantified.

## Honest scope
- Small probe (13 near-miss, 8 unknown, one genome). The *shape* (floor weak, edit strong, unknowns edit-far) is clear; exact percentages are this-corpus. A larger near-miss/unknown set would tighten the recall number.
- Tests the **comprehension (Pass-1) misbinding** vector specifically — the routing/topic-walk could mis-bind by other means (a real word that IS a store key but the wrong sense); that's a separate probe (sense-misbinding), not covered here.
- "Genuinely-unknown" = not routable in THIS genome + force-comprehensible; a broader genome would reclassify some.
- srmech-native (Klein-4 similarity); edit distance pure-Python (no `abs()`); generating code committed (computational-provenance discipline).
