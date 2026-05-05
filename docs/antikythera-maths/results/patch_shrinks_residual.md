# Patch-shrinks-residual benchmark

Earn the right to predict the missing data.

**Hypothesis**: each v0.4.0 catalog patch shrinks the targeted FFT residual peak by ~the patch's authored amplitude. If true across all three patches, the spectral-FFT-diagnose-then-overlay methodology is *vindicated* and we can author future patches (for the new moons, multi-millennium horizons, missing physics) the same way with quantified confidence.

- **Overall verdict:** **REJECTED**
- Vindication threshold: ≥80% shrinkage of the targeted peak amplitude.
- Sample grid: 1024 samples @ 900.0 d cadence.
- Native encoder used: True.
- Baseline FFT time: 86.5 s.

## `mars-7.96yr-diagonal` — verdict: **REJECTED**

- Kind: `sinusoid`
- Patch amplitude: **3.45°**
- Patch period: **2907.3 d** (7.96 yr)
- Average shrinkage of baseline peak: **2.5%**

| body | baseline peak (deg) | patched peak (deg) | Δ (deg) | shrinkage % of baseline | shrinkage % of patch amp |
| --- | ---: | ---: | ---: | ---: | ---: |
| mars | 3.4488 | 3.3636 | +0.0852 | 2.5% | 2.5% |

## `mercury-10.69yr-diagonal` — verdict: **REJECTED**

- Kind: `sinusoid`
- Patch amplitude: **9.19°**
- Patch period: **3905.1 d** (10.69 yr)
- Average shrinkage of baseline peak: **-49.9%**

| body | baseline peak (deg) | patched peak (deg) | Δ (deg) | shrinkage % of baseline | shrinkage % of patch amp |
| --- | ---: | ---: | ---: | ---: | ---: |
| mercury | 9.1912 | 13.7738 | -4.5827 | -49.9% | -49.9% |

## `jupiter-saturn-9.56yr-coupled` — verdict: **REJECTED**

- Kind: `coupled-sinusoid`
- Patch amplitude: **45.00°**
- Patch period: **3490.9 d** (9.56 yr)
- Average shrinkage of baseline peak: **15.3%**

| body | baseline peak (deg) | patched peak (deg) | Δ (deg) | shrinkage % of baseline | shrinkage % of patch amp |
| --- | ---: | ---: | ---: | ---: | ---: |
| jupiter | 44.6333 | 30.8383 | +13.7949 | 30.9% | 30.7% |
| saturn | 45.0169 | 45.1855 | -0.1686 | -0.4% | -0.4% |

## Interpretation

At least one catalog patch fails to shrink its targeted peak meaningfully. The spectral-FFT-diagnose-then-overlay methodology is **rejected as a forecasting tool** for the currently-authored catalog. Either the patch parameters (amplitude / period / phase) are wrong, the residual peaks aren't sinusoidal at the FFT cadence, or the patches are interacting with each other in unexpected ways. Drop back to first-principles α derivation.
