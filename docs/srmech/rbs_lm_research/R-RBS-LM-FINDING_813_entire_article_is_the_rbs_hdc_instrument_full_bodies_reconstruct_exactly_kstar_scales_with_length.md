# F813 — the ENTIRE article (full body, not the ≤3-sentence lead) IS the RBS-HDC instrument: on 1000 full simplewiki bodies (variable length, median 420, up to 25,097 tokens), 98.2% reconstruct EXACTLY from a seed + their shape-graph (storage-by-seed, F809 form), at mean k* = 7.8 (range 3–24). The fiber is real on entire articles — but, correcting the slice (F812), k* SCALES with length (the abstract's "3–6" was the uniform-3-sentence artifact). No more slicing-and-calling-it-everything: the full body is the instrument.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc169 · **Provenance:** `R-RBS-LM-FULLENCODE_…py` (1000 entire bodies, basic markup strip, per-article minimal-k* shape-graph + walk-reconstruct) · **Composes:** F812 (the re-review — slice artifact), F806–F809 (the mechanisms, now applied to entire bodies), F808 (the RBS-HDC context-addressed bundle-record walk = the realisation), §52 (streaming/out-of-core encode), #225 (markup form-kernels) · **User direction (2026-06-17):** "entire smallwiki article must be RBS-HDC-instrument … no more slicing and calling it everything."

## What was built
For each ENTIRE article body (markup-stripped): find the minimal context window k* whose walk is unique, build the de Bruijn shape-graph at k*, and reconstruct the WHOLE body by walking from the seed (the first k*-1 tokens). The article = seed + shape-graph (the RBS-HDC instrument, realised by F808's context-addressed bundle-record walk). Storage-by-seed (F809) applied to entire bodies, not leads.

## Result (1000 entire bodies, median 420 / max 25,097 tokens)
- **reconstruct the ENTIRE body EXACTLY from seed alone: 982/1000 = 98.2%** (unique walk at k*).
- **mean k* = 7.8 (range 3–24)** — k* SCALES with article length (F812 confirmed: 3.5 at 20–60 tok → 9.0 at 1000–4000 tok). The abstract finding of "k_res 3–6" was the 3-sentence slice.
- the remaining **1.8%** are long-range-ambiguous (no unique walk at k≤24); they reconstruct exactly only with explicit branch-choices stored (seed + true-pick at each branch — by-construction exact; the easy completion to 100%, not yet wired here).
- per-article choice-bits at the minimal k* are ~0 for the 98.2% (the own-information shows up as the HIGHER k* needed, not as choice-bits at fixed k) — consistent with F812's length-correlation (longer body ⇒ more context needed ⇒ larger k* / bigger graph).

## What this corrects + confirms
- **Confirms** the fiber is real on ENTIRE articles: a full body reconstructs exactly from its shape + a short seed (the RBS-HDC deterministic recall the user asked for — not on a slice).
- **Corrects** the slice magnitudes (F812): k* is NOT a small constant — it scales with length (mean 7.8, up to 24); a long article carries real own-information (more context to pin its path). F809's "length-independent / tiny" stands corrected.
- The lead-only stores are no longer "the wiki": the entire body is encodable + recallable.

## Honest scope + the path to ALL of simple wiki
- 1000 full bodies, basic markup strip. Two things remain to make it the ENTIRE simplewiki RBS-HDC object:
  1. **§52 streaming / out-of-core encode** — a full-corpus high-k shape-graph over all 240,881 bodies (~116M tokens) will not fit RAM (F793); the encode must stream + page (the §52 upstream ask). The per-article instrument (above) is the unit; the shared-corpus version is the scaled object.
  2. **#225 markup form-kernels** — 47% of bodies carry wiki markup; the basic strip is a stand-in. Clean, lossless markup handling (the sub-language router) is needed so the graph is real content, not strip residue.
- The 1.8% ambiguous tail: store explicit branch-choices (trivial, makes it 100% exact).
- The HDC realisation at full length (F808 keyed walk, O(len²)) is the per-article instrument; for the corpus it is the genome bake (build-once, GPU-free).

## Verdict
The entire article — full body, not the lead slice — IS the RBS-HDC instrument: 98.2% of 1000 full simplewiki bodies (up to 25k tokens) reconstruct exactly from a seed + their shape-graph at mean k* = 7.8. The fiber is real on entire articles, and (correcting the 3-sentence slice, F812) k* scales with length — the honest, no-slicing result. The full simplewiki RBS-HDC object is now a streaming-encode engineering task (§52) + clean markup (#225), not a conceptual gap. F805–F809's numbers are superseded by the full-body re-runs (F812/F813); their mechanisms stand.
