# Hilbert 8 / Goldbach — Chebyshev ψ Spectral Cascade (Redirect 2 of 3)

**Parent**: [hilbert_08_goldbach_conjecture/REPORT.md](../hilbert_08_goldbach_conjecture/REPORT.md)
**Status**: cascade dispatched 2026-05-23
**Class cascade**: A ∘ J ∘ L ∘ K
**Source**: srmech catalog `hilbert_08_goldbach_chebyshev_psi` (100 rows)

## Cascade design

Compute ψ(N) = Σ_{p^k ≤ N} log(p) for N ∈ {20, 40, …, 2000}. Residual = ψ(N) − N (the prime-number-theorem error term, RH-bounded by O(√N · log² N)). Class L applied to residual time-series path graph weighted by |Δresidual|.

## Findings (2026-05-23)

| Stat | Value |
|------|-------|
| Sample range | N ∈ [20, 2000] |
| Primes ≤ 2000 | 303 |
| ψ(2000) | 1994.45 |
| Residual at N_max | −5.55 |
| rel_residual at N_max (in units of √N) | **−0.1241** |
| Mean \|rel_residual\| | 0.1853 |
| RH bound O(log² N) at N=2000 | ~57.8 |
| Margin to RH bound | **~466×** (rel_residual ≪ bound) |
| Class L Fiedler | 0.0034 |
| Class L spectral radius | 67.68 |
| Spectral gap | 5e-5 |

**Structural observation**: ψ(N) − N is **well within the RH-predicted O(√N · log² N) bound** at N=2000 — the cascade confirms the residual is bounded in the predicted way. Per Class K asymptotic-DoF reading: the residual is the **line-projection of the prime-distribution loop**; its bounded oscillation is exactly what the framework predicts for a substrate-asymptotic-wave whose loop is asymptotically projected to a line.

The high spectral-gap-ratio (max/fiedler ≈ 20000) of the residual time-series path Laplacian indicates the residual's variation is concentrated at specific scales (high-frequency oscillation around the asymptotic), consistent with the explicit-formula picture where ψ(N) − N is a sum over zeta zeros.

## Run

```bash
python docs/unsolved-maths/hilbert/hilbert_08_goldbach_chebyshev_psi/generate_catalog.py
```
