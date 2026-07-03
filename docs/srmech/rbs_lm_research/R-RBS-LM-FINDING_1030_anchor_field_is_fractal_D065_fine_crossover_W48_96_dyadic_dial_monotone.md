# F1030 (user direction: "is there a fractal reduction shape … a tuned quantization dial?") — **YES, measured on the real corpus: (1) the ANCHOR FIELD IS FRACTAL AT FINE SCALES with a crossover — per-octave box dimension D = 0.654 (W 12→24, strongly clustered) → 0.812 → 0.953 → 1.057 ≈ 1 (W 96→192, space-filling; 99.3% coarse occupancy). Knowledge clusters ONLY below the W≈48–96 crossover — the fine-scale D≈0.65 is WHY surgical quantization works, and the crossover is the natural TOP of the dial; (2) the DYADIC DIAL WORKS and is MONOTONE — the same scale-invariant density test (ρ ≥ 1/6, integer math) applied in dyadic descent from W=192, with the dial τ = the minimum descent scale: kept% rises 20.9 → 24.5 → 29.5 → 35.7 → 44.0 → 53.9 as τ descends 192→6, and fixture survival rises 0/7 → 7/7 in step. One declared rule at every scale (self-similar), one integer knob, a smooth size↔retention trade: τ=6 recovers ALL F1029 fixtures at 53.9%; τ=12 gives 44% with most; a pyodide deployment picks its point on the measured curve.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc107 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_1030_probe_fractal_quantization_dial.py` (box-counting over 1,841 articles ≥200 tokens; dial curve over a 600-article sample + the F1029 fixtures) · **Composes:** F1029 (the flat W=12 rule this generalizes — the flat rule is the τ=12 slice of the dial family), F1028 (the two-axis trim), RC-1/F963 (the recursive scale-invariant compose arc — this is its first corpus-level instance), F778 (clump-don't-cap: the descent finds clumps, never caps them), `[[feedback_read_independent_structure_check_first]]` (the fractality was MEASURED before the dial was trusted — a D≈1 uniform field would have been the honest null killing the idea).

## Grounded (rc107)
```
BOX-COUNTING (1,841 articles, anchor = digit|title-token|numword):
  W:        12      24      48      96      192
  occupancy 0.608   0.780   0.905   0.969   0.993
  D/octave:     0.654   0.812   0.953   1.057     <- fractal FINE, uniform COARSE; crossover W~48-96
THE DIAL (dyadic descent from W0=192; rho>=1/6 self-similar at every scale; tau = min descent scale):
  tau:      192     96      48      24      12      6
  kept%:    20.9    24.5    29.5    35.7    44.0    53.9
  fixtures: 0/7     0/7     1/7     2/7     6/7     7/7   (fahrenheit formula+anchors / april / chess)
```

## The reading
- **The dial is principled, not arbitrary:** its range is bounded above by the measured crossover (descending past W≈96 is where structure appears; stopping above it drops whole blocks — the coarse-τ fixture wipeout shows exactly that) and below by the token scale. The single knob τ moves along a measured curve — "tuned quantization" in the literal sense.
- **Self-similarity is the discipline win:** ONE declared rule (integer density ≥ 1/6) at every scale — no per-scale tuning surface, no thresholds multiplying. The F1029 flat rule survives as the τ=12 slice; the family costs nothing extra to specify.
- **The scale-dependent dimension is itself a coordinate:** per-article D-profiles (where an article's own crossover sits) extend the F1029 keep-rate diagnostic toward a multifractal article typology — fact-tables, narratives, and lists should have distinguishable D-profiles. Unmeasured yet; named as the follow-on.
- **Big-wiki implication:** the dial makes the enwiki kernel a CHOICE on a curve rather than a fixed cost — ship τ=12 for the browser, τ=6 for the desktop, same rule, same attested build (source sha + W0/ρ/τ in the op-log).

## Verdict / next
**The fractal reduction shape exists, is measured (D 0.65→1.06 with the W≈48–96 crossover), and yields a monotone one-knob dial (τ: 21%→54% kept, 0/7→7/7 fixtures).** Next: per-article D-profiles (the multifractal typology); the chronology-shell discriminator composed INTO the density test; the τ-dial wired into the kernel build pipeline; the rc105 chiral edges built from τ-quantized spans.
