# F1182 (#243) (the fractal advantage on a REAL fragmentary text — honest weak-positive, bounded by the text's recurrence-scale ceiling: reconstructing a burst LACUNA in Gilgameš by finding its parallel passage at increasing context scales, the **stanza scale (C=4) beats the line scale (C=1)** at every burst size (0.378/0.362/0.274/0.265 vs 0.356/0.351/0.268/0.241, +~0.02) — a genuine multi-scale benefit — but the **episode scale (C=12) OVERSHOOTS and does worse** (0.284/0.288/0.253/0.217), because Gilgameš has verbatim recurrence at the *formula/stanza* scale but NOT at the 12-line episode scale, so over-large context matches find spurious parallels; so F1181's idealized exponential fractal advantage is **capped on real text at the text's actual recurrence ceiling** — the multi-scale benefit is real but small and peaks at the scale where the text genuinely repeats) — **user: "test on a real fragmentary text: line+stanza+episode reconstruction." DONE — multi-scale helps up to the recurrence ceiling (stanza here), overshoots beyond it.**

**Date:** 2026-07-09 · **srmech:** 0.7.5rc135 · **User direction:** test line+stanza+episode reconstruction on a real fragmentary text. · **Corpus:** the 5 ETCSL Gilgameš tablets concatenated (1516 lines; oral-formulaic — verbatim repeated speeches), glyph→concept via `siona.anchor`. numpy-free; no magnitude-builtin. · **Composes:** F1181 (the idealized fractal advantage this bounds on real data), F1171 (multi-scale recurrence comb), F1175–F1178 (the reconstruction arc). **Refines F1181: the advantage is real but capped by the text's recurrence-scale ceiling.**

## Method

Excise a contiguous **lacuna** (burst) of L lines. Reconstruct it by finding the best **parallel passage** — the position elsewhere in the text whose surrounding context best matches the lines *bracketing* the lacuna (C lines before + C after, skipping the burst's own neighbourhood). The parallel's middle IS the reconstruction. The **context width C is the recurrence SCALE** used to find the parallel: C=1 = line-scale, C=4 = stanza-scale, C=12 = episode-scale. Recall = mean line-wise Jaccard(reconstructed, true).

## Result

| burst L | line (C=1) | **stanza (C=4)** | episode (C=12) |
|---|---|---|---|
| 2 | 0.356 | **0.378** | 0.284 |
| 3 | 0.351 | **0.362** | 0.288 |
| 5 | 0.268 | **0.274** | 0.253 |
| 8 | 0.241 | **0.265** | 0.217 |

**Stanza (C=4) > line (C=1) at every burst size** — a genuine multi-scale advantage: using a larger-than-line context to find the parallel reconstructs the lacuna better, exactly F1181's direction. **But episode (C=12) < line** — it overshoots. The reason is the honest boundary: Gilgameš's oral-formulaic repetition lives at the **line/formula/stanza scale** (a few lines — a repeated speech, an epithet-string), not at the **12-line episode scale**, so a 12-line context rarely recurs verbatim and the match latches onto spurious distant passages. The multi-scale benefit peaks at the scale where the text *actually* repeats and degrades beyond it.

## What it refines

F1181 showed the fractal comb's advantage grows *exponentially* with the number of scales — but that assumed the signal has genuine recurrence at *every* scale. **Real narrative does not.** It has self-similar recurrence up to a **ceiling** (here the stanza/formula scale) and above that its content is effectively unique. So on real fragmentary text:
- the multi-scale advantage is **real but small** (stanza beats line by ~0.02), and
- it **peaks at the recurrence ceiling** and **overshoots** above it (episode < line).

This is the honest, expected bound: the fractal advantage is only as deep as the text's actual self-similarity. A text with deeper verbatim recurrence (a litany, a heavily-formulaic funerary corpus, a genealogy) should show the sweet-spot at a *larger* scale; a unique-content text shows none. (Absolute recall is low, ~0.24–0.38, because most lacuna content is only partly recurrent — the operand problem again: the formula frame recurs, the unique slot does not, F1175.)

## Verdict / next
**HONEST weak-positive, bounded: on real Gilgameš the multi-scale reconstruction advantage is real (stanza C=4 beats line C=1 by ~0.02 at every burst size) but SMALL and CAPPED at the text's recurrence ceiling — the episode scale (C=12) overshoots and underperforms because Gilgameš lacks verbatim 12-line recurrence. So F1181's idealized exponential fractal advantage is, on real text, only as deep as the text's actual self-similarity: multi-scale helps up to the recurrence ceiling, hurts beyond it. NEXT: repeat on a deeper-recurrence corpus (Book of the Dead litanies / a genealogy) to find where the sweet-spot scale lands; combine with the operand-EC (F1177) — reconstruct the recurring frame at the stanza scale, the unique slot from a parallel version. Read-independent-verified (scale sweep + burst sweep); composes F1181/F1171/F1175-78.**
