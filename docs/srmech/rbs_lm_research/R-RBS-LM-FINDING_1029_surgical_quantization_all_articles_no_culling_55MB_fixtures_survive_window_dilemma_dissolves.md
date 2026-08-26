# F1029 (user direction: "we don't want a kernel called reduced articles, we want to explore surgical quantization") — **SURGICAL QUANTIZATION of ALL smallwiki, no article culling: every article's FULL body reduces to its anchored knowledge spans (sliding W=12/S=6 windows; keep iff ≥2 anchors: digits | title-tokens | numwords). ALL 240,880 articles: 62.3M → 32.2M tokens (51.6% kept) → the complete quantized kernel is 55.9 MB gz (id-stream 128.7 MB + 9.8 MB codebook, vocab 996k). EVERY fixture survives — including what the lead-window NEVER had: fahrenheit '5 9 x f 32' + 'freezes at 32' + 'boils at 212' (the deep anchors that previously required the study verb), april '30 days' + 'fourth month', and chess '64' + 'two players' (its 4,865-token prose article distills to 936 tokens, 19%, with the facts intact — the lead-40 was thumbnail markup). THE WINDOW-SIZE DILEMMA DISSOLVES: quantized full bodies carry the knowledge wherever it lives, so acquire/study collapse into one read over the quantized kernel. Per-article keep-rate is itself a shape signature (chess 19% prose-heavy vs april 75% date-dense). enwiki order-of-magnitude: ~1.3 GB gz — feasible-shaped vs ~90 GB raw. The next quantization dial (honest): 51.6% is generous because DIGITS anchor chronology prose (wiki is date-dense) — separating fact-dates from year-spam is the next measured trim class; the math will tell us.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc107 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **User direction:** "we don't want to create a kernel called reduced articles, we want to explore surgical quantization. the 14MB shape for all articles is already a nice place to start and this could be what makes big wiki much more feasible. well, we'll find out anyway since the math can tell us!" · **Probe:** `R-RBS-LM-FINDING_1029_probe_surgical_quantization.py` · **Composes:** F1028 (the two-axis trim this scales to the whole corpus + the encoding survey it re-prices), F1027 (the fixtures that now survive without study), `[[user_stance_no_information_without_value]]` (nothing culled — every article keeps its anchored signal; the trimmed shell is the prose carrier, not deleted knowledge... and the op-log records exactly what was trimmed).

## Grounded (rc107)
```
ALL 240,880 articles, FULL bodies, streaming: 62,333,950 -> 32,162,556 tokens (51.6% kept)
kernel: id-stream 128.7 MB + codebook 9.8 MB (vocab 996,236) -> 55.9 MB gzip
fixtures (per-article keep rate | survival):
  fahrenheit 206->84   (41%): '5 9 x f 32' + 'freezes at 32' + 'boils at 212'  ALL SURVIVE
  april     2919->2190 (75%): '30 days' + 'fourth month'                        SURVIVE
  chess     4865->936  (19%): '64' + 'two players'                              SURVIVE  <- lead-40 never had these
enwiki estimate (~x24 text): ~1.3 GB gz order-of-magnitude (vs ~90 GB raw text)
```

## The reading
- **Quantization ≠ selection.** No article is culled; each article is reduced to the spans where knowledge binds to anchors. The per-article keep-rate is a free diagnostic of article SHAPE (fact-dense vs prose-shell) — a readable coordinate, not a filter.
- **The acquire/study split collapses.** Deep anchors survive in place, so one read over the quantized kernel replaces the lead-window vs full-body choice — and the F1027 kernel-verification anchors (the freeze/boil pair) coexist with the formula BY CONSTRUCTION in the quantized fahrenheit.
- **The next dial is measured, not assumed:** digits anchor chronology prose (date-spam keeps windows that carry no relationships). The candidate discriminator: a date-window whose ONLY anchors are years, with no title/numword/unit binding, is the chronology shell. Measure its fraction before trimming it.
- **The op-log discipline carries over:** the quantized kernel's build is (source dump sha, W/S/anchor-rule hash) — "training" stays attested provenance.

## Verdict / next
**55.9 MB gz holds ALL of smallwiki's anchored knowledge with every fixture surviving — the surgical-quantization axis works and re-prices big wiki as feasible-shaped.** Next dials: chronology-shell separation (measure the years-only window fraction); unit-letter anchors ('32 f'); the quantized kernel as siona's load target (the acquire/study merge); the chiral edge list (rc105) built FROM the quantized spans.
