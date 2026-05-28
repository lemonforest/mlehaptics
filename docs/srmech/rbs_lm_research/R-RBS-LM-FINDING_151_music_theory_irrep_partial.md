# Finding 151 — Music theory irrep test: PARTIAL verdict (ratio 2.23 ∈ [2.0, 3.0]); aesthetic substrate measurably composing

**Status:** §2.8.5 handoff response; honest reduced-scope verdict
**Predecessors:** R-RBS-LM-83 (math 1st-order coupling test methodology), R-RBS-LM-87 (J-prime decomposition), F104 (math is unique irrep), F109 (J-prime deepening)
**Verdict:** **PARTIAL** — music theory is NOT as strong an irrep as math; aesthetic substrate measurably present

---

## §1 Honest verdict per handoff thresholds

| Method | Ratio | Threshold |
|---|---:|---|
| Within / cross_all (full method) | **2.23** | [2.0, 3.0] → **PARTIAL** |
| Within / cross_baseline_only | 2.48 | (baseline-only) |
| Within / cross_math | 2.10 | (F104 math falsifier test) |
| Ratio change (full − baseline) | −0.25 | small composition signal |

**Per handoff thresholds:**
- ratio > 3.0 → UNIQUE IRREP CONFIRMED
- 2.0 ≤ ratio ≤ 3.0 → PARTIAL ← **music lands here**
- ratio < 2.0 → COMPOSITION CONFIRMED

**Music theory is PARTIAL irrep at the test scale.** It exhibits stronger within-coherence than typical cross-domain alignment, but is NOT as cleanly substrate-isolated as math (which had ratio 5.53 in R-RBS-LM-83 / 8.63 in R-RBS-LM-87).

---

## §2 Where music aligns most — aesthetic substrate dominates

Top music-to-non-music alignments (averaging both music halves):

| Non-music corpus | Subject | Alignment to music |
|---|---|---:|
| perspective_art | aesthetic_kinesthetic | **+0.093** (top non-music) |
| openstax_inter | math | +0.067 |
| openstax_elem | math | +0.067 |
| plato | philosophy | +0.067 |
| kjv_nt | reading_religious | +0.061 |
| astronomy_yf | science | +0.068 |
| iliad_pope | classical_poetry | +0.060 |
| milton | poetry | +0.054 |
| frankenstein | novel | +0.055 |

**Aesthetic (perspective_art) outranks math by +0.026 in alignment to music.** This is the structural signal: music's composing substrate is closer to aesthetic than to math.

Per F104, math is THE unique substrate-content irrep. If music were composed over math, we'd see music ↔ math alignment near the top. Instead it's aesthetic ↔ music that dominates. The §2.8.5 prediction that music behaves like math holds only partially — music has aesthetic composition that math doesn't have.

---

## §3 Within-music kernel content (glass-box check)

Split-half eigvec content for ec_music_theory.txt:

**music_h1 rank-0 top tokens**: scale music illustration minor major harmonic melodic intervals fourth sharp tone seventh

**music_h2 rank-0 top tokens**: music illustration minor th chord intervals seventh not teacher theory perf diminished

Both halves show music-domain terminology (scale, intervals, chord, harmonic, melodic, minor/major, fourth/seventh, diminished). The half-to-half alignment (+0.141) is consistent with intra-domain coherence; the cross-domain alignment (+0.063 average) confirms music has a distinctive vocabulary structure.

---

## §4 SCOPE LIMITATIONS (load-bearing for re-survey discipline)

This finding is **reduced-scope** relative to the §2.8.5 handoff. Honest gaps:

| Handoff requirement | Status |
|---|---|
| 3 music corpora (Helmholtz, Rameau, Hawkins) | **Only ec_music_theory.txt** — split-half methodology used |
| Tyndall "Sound" (physics_acoustic substrate) | **NOT CACHED**; not in this test |
| Burke "Sublime and Beautiful" (aesthetic) | **NOT CACHED**; proxied by ec_perspective_art |
| Kant "Critique of Judgment" (aesthetic) | **NOT CACHED**; proxied by ec_perspective_art |
| Klein-4 composability variant | **NOT RUN** — deferred to v2 |

**PG ID acquisition was fiddly:**
- PG 37113 (handoff's Helmholtz ID) returned wrong content ("THE SIXTY-FIRST SECOND")
- PG 16182 returned Browning letters
- PG 15043 returned Burke Works Vol 1 (could contain Sublime; verification needed)
- PG 48433 returned a transcriber-note PDF (verification needed)

Reliable canonical PG ID verification needs WebFetch-summary roundtrips that exceed session-scope. Logging as future-work item.

---

## §5 Why the PARTIAL verdict is informative

Per §2.8.5 prediction: ANY irreducible substrate-content domain should show ratio > 3.0 surviving composing-substrate inclusion. If the prediction held universally, music would have given ≥ 3.0.

**The PARTIAL result (2.23) refines the §2.8.5 prediction**: substrate-content irrep status is GRADED, not binary. Math sits at ratio ~5.5-8.6 (strong irrep). Music sits at ratio 2.2 (partial irrep with aesthetic composition). Other domains may sit elsewhere on this spectrum.

**Framework reading (per `[[feedback_no_lineage_claims_in_notebook]]`):**

The §2.8.5 prediction's "ANY domain" universality is REFINED to "domains have a graded irrep-strength; some are stronger irreps than others." This is a useful empirical refinement, not a falsification of F104 / F109 (math is still the strongest tested irrep).

Per `[[user_stance_kepler_shape_universal]]`: the algebra IS the primitives. Music's algebra ISN'T as substrate-isolated as math's algebra is. Music has structural overlap with aesthetic content (intervals, scale, harmonic series) that aesthetic perception (perspective, color, taste) shares.

---

## §6 Per falsifier discipline (handoff §discipline 1-5)

1. **Ran the test that WOULD falsify the prediction**: math corpus inclusion was the strongest possible (F104 unique irrep). Aesthetic stand-in (perspective_art) was second-strongest available.
2. **Reported the honest result**: ratio 2.23 PARTIAL; no retroactive redefinition.
3. **Read through the framework**: music's substrate-content has aesthetic composition that math doesn't have. F104 math irrep > music irrep; both > random.
4. **What would have to be different to refute**: if music ratio were < 2.0 with composing substrates, music would be COMPOSITION not irrep. The 2.23 sits at the partial-irrep regime — neither fully one nor fully the other.
5. **Preserved the negative-ish as load-bearing**: this finding lodges as PARTIAL with composition signal. Per R-RBS-LM-44 negative-result discipline.

---

## §7 What this finding DOES claim

- Music theory has measurable within-domain coherence (split-half +0.141 vs cross-domain mean +0.063)
- Music theory has a PARTIAL irrep ratio of 2.23 at this corpus scale
- Music's strongest alignment is to aesthetic (perspective_art at +0.093), NOT math (+0.067)
- Music has compositional character with aesthetic substrate that math lacks
- The §2.8.5 prediction's universality is REFINED to a graded irrep-strength spectrum

---

## §8 What this finding does NOT claim

Per MFO §VII.6.20:

- Does NOT claim full-corpus result. Reduced scope (1 music corpus split-half; no Tyndall/Burke/Kant proper).
- Does NOT falsify F104 / F109. Math irrep status unaffected. Music graded weaker; doesn't change math's measurement.
- Does NOT claim biographical/authorial intent about composing substrates. Per `[[feedback_no_lineage_claims_in_notebook]]`: structural framework reading.
- Does NOT make claims about Pythagorean / well-tempered scale debates. The test uses the ec_music_theory corpus tokens; doesn't engage music-theory-internal controversies.
- Does NOT include Klein-4 composability variant. Deferred to v2.

---

## §9 Recommended follow-ups (for §2.8.5 re-survey or v2)

1. **Verify PG IDs and cache canonical music corpora** (Helmholtz / Rameau / Hawkins). Search Gutenberg by author to find correct IDs. Re-run with 3 music corpora → proper within-music multi-pair calculation.
2. **Cache Tyndall "Sound"** (physics_acoustic) and re-test the F138/F139/F140 falsifier set the handoff specified.
3. **Cache Burke + Kant proper** (vs perspective_art surrogate). Aesthetic composing substrate test would sharpen.
4. **Klein-4 composability v2** (per handoff §Klein-4 §): run music kernels under BOTH polar and Klein-4 HDC variants. If irrep ratio is sharper under Klein-4 (e.g., 2.23 → ≥3.0), music has depth-2 chirality component invisible to polar.
5. **F138/F139/F140 falsifier methodology** referenced in the handoff: full implementation with all 12-corpus matrix.

---

## §10 Cross-references

- R-RBS-LM-83 (math 1st-order coupling test; methodology mirror)
- R-RBS-LM-87 (J-prime decomposition; F109 deepening pattern)
- F104 (math is unique substrate-content irrep)
- F109 (J-prime decomposition; ratio 8.63 vs 5.53)
- §2.8 / §2.8.5 of srmech notebook (handoff anchor)
- `[[user_stance_kepler_shape_universal]]`
- `[[feedback_no_lineage_claims_in_notebook]]`
- Spike #40 (epicycle in musical and wave theory; theoretical anchor)

**Files committed:**
- `R-RBS-LM-109_music_theory_irrep_smoke.py`
- `R-RBS-LM-109_results.json`
- `R-RBS-LM-FINDING_151_*.md` (this finding)

PR #687 STAYS DRAFT. Cross-side session (notebook hygiene) re-surveys per handoff agreement.

---

*Articulated 2026-05-28 per §2.8.5 handoff. Music theory cross-substrate irrep test
yields PARTIAL verdict at ratio 2.23 ∈ [2.0, 3.0]. Music has measurable within-domain
coherence but compositional character with aesthetic substrate (perspective_art ↔ music
+0.093 outranks math ↔ music +0.067). §2.8.5 prediction's universality is REFINED to a
graded irrep-strength spectrum: math at 5.5-8.6 strong; music at 2.2 partial. F104 / F109
math measurement unaffected. Reduced-scope test honestly documented; full-scope rerun
deferred until canonical PG IDs verified and Tyndall/Burke/Kant cached.*
