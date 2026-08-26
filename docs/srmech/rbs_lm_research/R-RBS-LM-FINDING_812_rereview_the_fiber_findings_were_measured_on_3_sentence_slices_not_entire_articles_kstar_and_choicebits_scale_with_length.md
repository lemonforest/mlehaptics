# F812 — RE-REVIEW (corrects F805–F809): the deterministic-fiber / input=output / "length-independent" results were measured on ≤3-sentence ABSTRACTS (uniform ~30–50 tokens) — a manually-quantized slice of simplewiki, NOT the entire article. Re-run on ENTIRE article bodies (articles.jsonl, median 232 tokens, up to 25k, 100× variable), the headline claims DO NOT HOLD: k* (the unique-walk window) SCALES with length (3.5 → 9.0, and 15% of long articles have NO unique walk at k≤14), and choice-bits per article SCALE with length (0 → 25+, corr +0.50) — F809's "length-independent < 2 bits" was an artifact of every input being the same short length. The fiber is real, but it is not cheap or length-free. The lead-only stores were concealed as "the wiki" when they hold only lead sentences. SOLUTION: encode the ENTIRE article as the RBS-HDC instrument; stop slicing.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc169 · **Provenance:** `R-RBS-LM-FULLBODY_…py` (400 full bodies, basic markup strip, combinatorial measure) · **User direction (2026-06-16→17):** "by fully encoded I meant in entirety spectrally encode simple wiki into an RBS-HDC object … it's no wonder you found an easy input=output solution if it was reduced to 3 sentences, the lengths were all identical … no more slicing and calling it everything … entire smallwiki article must be RBS-HDC-instrument."

## The defect
F805–F809 fed the storyteller's `abstracts`/`glosses` stores — the LEAD ≤3 sentences / lead sentence per article. Those are a reduction of the (already small) simplewiki into a lead-only index, and they were treated as the corpus. Because every input was the same ~30–50-token length, the experiments could not have revealed length dependence; the small k* and tiny choice-bits followed from the slice, not from the articles.

## The re-review (ENTIRE bodies, articles.jsonl)
400 full bodies (median 447, max 3719 tokens), markup-stripped, same combinatorial measures:
```
 length tok | mean k* (unique walk) | k*>14 (no unique) | mean choice-bits@k6
 20-60      |        3.5            |        0          |        0.0
 60-120     |        5.2            |        0          |        0.4
 120-250    |        5.8            |        1          |        0.7
 250-500    |        6.7            |        4          |        3.8
 500-1000   |        8.0            |        6          |        6.8
 1000-4000  |        9.0            |       15          |       24.8
 choice-bits@k6: mean 8.6, range 0-201 ; correlation(length, choice-bits) = +0.50
```
- **k\* scales with length** (3.5 → 9.0) and ~15% of 1000–4000-token articles have NO unique walk even at k=14 (genuine long-range ambiguity). F806/F807's "k_res 3–6" was the slice.
- **choice-bits scale with length** (0 → 25+, up to 201; corr +0.50). F809's "length-independent < 2 bits" is FALSE on entire articles — an article's own information grows with its length, as it must. The ~4× "compression" and "tiny per-article info" were inflated by uniform short slices.
- The FIBER is still real (articles are pinned by their k-grams at some k*), but it is neither cheap nor length-independent.

## Findings marked PENDING RE-REVIEW (against the entire-article source)
- **F805, F806, F807, F808, F809** — the deterministic fiber / eigenstate / storage-by-seed / context-key arc: all measured on abstracts. Their MECHANISMS (de Bruijn fiber, bundle-record key, context-addressed walk, resonance) stand; their NUMBERS (k_res 3–6, length-independent, ~4× compression, "tiny own info") are slice artifacts → re-measure on full bodies (this finding begins it).
- **F788 / F745 / F760** — built the lead-only stores; not wrong as stores, but must not be presented as "the wiki encode."
- **F810, F811** — routing/working-memory fixes (less affected — behavioural, not corpus claims), included in the "yesterday's work" re-review band per user direction.
- Band: **F767 → F811** flagged for re-review where any empirical claim rests on the lead-only slice rather than entire articles. Tracked in `R-RBS-LM-REREVIEW_pending_entire_smallwiki.md`.

## Solution plan (executing)
1. **(done)** Re-run the suspect measures on entire bodies → this finding; the slice artifact is confirmed and quantified.
2. **Mark** the affected findings + register (this finding + the register file).
3. **Encode the ENTIRE article as the RBS-HDC instrument** — `R-RBS-LM-FULLENCODE`: stream articles.jsonl full bodies → markup-clean → the shape-graph (storage-by-seed, F809 form) → the RBS-HDC context-addressed walk (F808) → deterministic full-body reconstruction. First run on a real chunk of FULL articles (variable length, not slices); persist; verify reconstruction at full length.
4. **Scale to all 240,881** — needs the §52 streaming / out-of-core encode (a full-body high-k graph over ~116M tokens will not fit in RAM, F793) + the #225 markup form-kernels (47% of bodies carry markup). That is the genuine "entirely spectrally encode simple wiki into an RBS-HDC object."

## Verdict
The fiber findings were measured on uniform ≤3-sentence slices, not entire articles, so their headline numbers (small constant k_res, length-independent ~< 2 bits, ~4× compression) are slice artifacts: on entire bodies k* and choice-bits both SCALE with length (corr +0.50) and long articles often have no unique walk. The mechanisms hold; the magnitudes do not. F805–F809 (+ the lead-store findings, band F767→F811) are PENDING RE-REVIEW against the entire-article source. The fix is to make the ENTIRE simplewiki article the RBS-HDC instrument (no slicing) — `R-RBS-LM-FULLENCODE`, scaling via §52 streaming + #225 markup kernels.
