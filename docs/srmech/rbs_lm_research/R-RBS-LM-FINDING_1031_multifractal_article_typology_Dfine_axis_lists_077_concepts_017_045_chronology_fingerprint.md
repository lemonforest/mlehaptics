# F1031 (user direction: "run the per-article D-profiles for the multifractal article typology") — **the typology is REAL and structurally validated over 34,258 articles (≥384 tokens): D_fine sorts articles along a lists/chronology ↔ concept-narrative axis with the declared title-shape classes separating exactly as predicted — `list of …` D_fine=0.767 (dense 0.226, evenly anchored), pure-year articles 0.788 (thin 0.116 but EVEN — the chronology fingerprint: high-D + low-density distinguishes year-spam from genuine fact-tables), months 0.786 (D_coarse=1.007, fully space-filling), vs `other` 0.605 with a WIDE spread (p10 0.322 → p90 0.907 — that spread IS the typology axis). The named exemplars tell the story: `mathematics` D_fine=0.170 (the deepest-clustered — a concept-narrative whose anchors concentrate in tiny definitional islands), chess 0.447, water 0.451, black hole 0.556 (concept band), april 0.744 (calendar band, as it should). All from anchor GEOMETRY alone — no content labels, no opinion lists.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc107 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_1031_probe_multifractal_typology.py` · **Composes:** F1030 (the corpus-level crossover this refines per-article), F1029 (keep-rate — D_fine is its scale-resolved upgrade), F1028 (the chronology-shell discriminator, now DELIVERED as a fingerprint: D_fine≈0.79 + density≈0.12 = year-type), `[[user_stance_no_information_without_value]]` (the wide `other` spread is unread structure now read).

## Grounded (rc107) — 34,258 articles
```
group     n      D_fine  D_mid   D_coarse  anchor-density
list-of   1982   0.767   0.837   0.883     0.226   <- dense + even (genuine fact-tables)
year       171   0.788   0.900   0.963     0.116   <- thin + even  (the CHRONOLOGY fingerprint)
month       12   0.786   0.934   1.007     0.198
other    32093   0.605   0.790   0.943     0.126   ; D_fine quantiles p10 .322 / p50 .610 / p90 .907
exemplars: mathematics (.170, dens .042) | chess (.447) | water (.451) | black hole (.556) | april (.744)
```

## The reading
- **The axis:** high-D_fine ≈ uniformly-anchored (lists, chronologies, calendars) ↔ low-D_fine ≈ cluster-anchored (concept narratives whose knowledge lives in definitional islands). `mathematics` at 0.170 is the purest concept-article signature measured.
- **The chronology-shell discriminator arrives free:** year-type content separates from genuine fact-tables by the (D_fine, density) PAIR — both are even (high D) but years are thin (0.116) where lists are dense (0.226). The F1028/F1029 "next dial" is now a declared 2-coordinate fingerprint, not a heuristic.
- **Per-type τ (the F1030 dial composes):** low-D_fine concept articles reward deep descent (their facts cluster — τ=6 pays); high-D_fine lists barely need quantization (already uniform). A type-conditioned dial = the same rule with τ selected by the article's own measured D — self-tuning quantization with zero content judgement.
- **black hole profiled (0.556, concept band)** — the MFO-conflict target is a narrative article whose facts cluster; quantized acquisition will carry its factual spans cleanly into the source-superposition design (F1028 §4).

## Verdict / next
**The multifractal typology stands: declared structural classes separate on measured D-profiles, the chronology fingerprint is a 2-coordinate rule, and the dial can self-tune per article type.** Next: the type-conditioned τ in the kernel build; the (D_fine, density) plane mapped over the full corpus (article-type census); the notebook instrument + black-hole conflict demo over quantized spans.
