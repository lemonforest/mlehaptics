# Chaos Ratio vs Game Length

Corpus: 26 games across 3 sweeps (sweep_chain_lichess_drnykterstein_2026-04-14_N10, sweep_hf_2026-04-14_N10_seed42, sweep_lichess_drnykterstein_2026-04-14_N10).

## Formula

```
L2_fiber[t] = sqrt(||FA||² + ||FD||²)
L2_irrep[t] = sqrt(||A1||² + ||A2||² + ||B1||² + ||B2||²
                  + ||E||² + ||F1||² + ||F2||² + ||F3||²)
chaos_ratio = mean_t(L2_fiber) / mean_t(L2_irrep)
```
Source: `chess_spectral/corpus.py:201-207`. Note the dashboard's
'fiber view' (F1+F2+F3) is *not* what `chaos_ratio` measures —
`chaos_ratio` is the antisymmetric-breaking ratio (FA+FD vs all)
and treats F1/F2/F3 as part of the irrep denominator.

## Spearman ρ (game length vs each variant)

| Variant | ρ | p | Interpretation |
|---|---:|---:|---|
| `cr_mean_of_means` | +0.252 | 0.213 | |
| `cr_mean_per_ply` | +0.153 | 0.456 | |
| `cr_median` | **+0.449** | 0.0215 | |
| `cr_max` | +0.266 | 0.188 | |
| `cr_p90` | +0.167 | 0.415 | |
| `cr_sqrtnorm` | +0.088 | 0.669 | |

## Per-game table

| sweep | idx | plies | cr_csv | mean_per_ply | median | max | p90 | sqrt-norm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sweep_hf_2026-04-14_N10_seed42 | 4 | 129 | 4.901 | 7.380 | 1.816 | 146.198 | 12.460 | 0.431 |
| sweep_chain_lichess_drnykterstei | 10 | 108 | 14.268 | 27.296 | 32.295 | 133.674 | 44.338 | 1.373 |
| sweep_hf_2026-04-14_N10_seed42 | 6 | 116 | 4.885 | 10.662 | 4.588 | 116.520 | 24.064 | 0.454 |
| sweep_lichess_drnykterstein_2026 | 5 | 126 | 1.545 | 2.315 | 0.789 | 112.164 | 2.395 | 0.138 |
| sweep_chain_lichess_drnykterstei | 4 | 89 | 7.884 | 16.578 | 3.812 | 96.484 | 77.371 | 0.836 |
| sweep_hf_2026-04-14_N10_seed42 | 7 | 163 | 15.648 | 24.669 | 25.828 | 83.238 | 39.130 | 1.226 |
| sweep_chain_lichess_drnykterstei | 2 | 55 | 3.736 | 7.069 | 2.114 | 80.627 | 7.574 | 0.504 |
| sweep_chain_lichess_drnykterstei | 3 | 59 | 2.289 | 3.528 | 0.103 | 80.559 | 13.771 | 0.298 |
| sweep_lichess_drnykterstein_2026 | 3 | 61 | 1.648 | 2.992 | 0.119 | 78.347 | 1.689 | 0.211 |
| sweep_hf_2026-04-14_N10_seed42 | 1 | 89 | 3.630 | 6.253 | 4.516 | 75.606 | 11.487 | 0.385 |
| sweep_hf_2026-04-14_N10_seed42 | 2 | 80 | 0.882 | 1.376 | 0.147 | 68.284 | 1.190 | 0.099 |
| sweep_chain_lichess_drnykterstei | 7 | 57 | 1.700 | 2.727 | 0.094 | 64.352 | 4.786 | 0.225 |
| sweep_chain_lichess_drnykterstei | 1 | 137 | 2.123 | 2.258 | 1.215 | 61.711 | 2.763 | 0.181 |
| sweep_lichess_drnykterstein_2026 | 1 | 137 | 2.123 | 2.258 | 1.215 | 61.711 | 2.763 | 0.181 |
| sweep_lichess_drnykterstein_2026 | 4 | 100 | 3.157 | 5.223 | 3.544 | 61.169 | 10.815 | 0.316 |
| sweep_hf_2026-04-14_N10_seed42 | 5 | 101 | 6.296 | 8.484 | 3.500 | 60.603 | 24.508 | 0.626 |
| sweep_hf_2026-04-14_N10_seed42 | 10 | 114 | 4.937 | 6.139 | 4.035 | 55.612 | 12.165 | 0.462 |
| sweep_chain_lichess_drnykterstei | 5 | 91 | 5.695 | 9.242 | 3.369 | 53.449 | 24.652 | 0.597 |
| sweep_hf_2026-04-14_N10_seed42 | 3 | 98 | 1.319 | 1.717 | 0.306 | 50.725 | 1.508 | 0.133 |
| sweep_lichess_drnykterstein_2026 | 6 | 99 | 10.214 | 17.068 | 9.396 | 50.657 | 48.466 | 1.027 |
| sweep_hf_2026-04-14_N10_seed42 | 8 | 81 | 1.416 | 1.730 | 0.282 | 48.748 | 1.854 | 0.157 |
| sweep_lichess_drnykterstein_2026 | 2 | 97 | 2.504 | 3.582 | 0.514 | 46.609 | 13.728 | 0.254 |
| sweep_chain_lichess_drnykterstei | 6 | 88 | 4.008 | 6.831 | 0.122 | 36.428 | 26.310 | 0.427 |
| sweep_hf_2026-04-14_N10_seed42 | 9 | 122 | 1.289 | 1.726 | 0.654 | 31.060 | 5.629 | 0.117 |
| sweep_chain_lichess_drnykterstei | 8 | 48 | 2.688 | 3.666 | 2.653 | 28.780 | 7.272 | 0.388 |
| sweep_chain_lichess_drnykterstei | 9 | 64 | 1.845 | 2.298 | 0.853 | 5.860 | 5.588 | 0.231 |

## Focus game: sweep_hf_2026-04-14_N10_seed42 #7 (163 plies, csv cr=15.65)

Per-ply chaos ratio: median=25.828, max=83.238 at ply 58, plies above 3×median (77.48): 1 of 163 (0.6%).

If spikes ≪ 10% of plies → spikes are localised events.
If spikes ≫ 10% → ratio is uniformly elevated.

Per-ply ratio time series (first 60 plies, 5-ply chunks):

| ply | ratio |
|---:|---:|
| 0 | 0.086 |
| 5 | 0.317 |
| 10 | 0.082 |
| 15 | 0.418 |
| 20 | 0.072 |
| 25 | 14.447 |
| 30 | 12.856 |
| 35 | 13.743 |
| 40 | 16.016 |
| 45 | 14.745 |
| 50 | 10.077 |
| 55 | 14.491 |
| ... | ... |

Top-10 spike plies:

| ply | ratio |
|---:|---:|
| 58 | 83.238 |
| 115 | 41.874 |
| 143 | 40.640 |
| 144 | 40.568 |
| 132 | 40.309 |
| 108 | 40.060 |
| 114 | 39.906 |
| 145 | 39.904 |
| 117 | 39.759 |
| 113 | 39.718 |
