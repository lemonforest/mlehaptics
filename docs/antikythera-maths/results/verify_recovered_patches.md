# Phase-recovered catalog — patch-shrinks-residual verification

Re-run of the benchmark using the **phase-recovered** catalog (amplitudes scaled 2× and phases extracted from the FFT's complex bin) instead of the v0.4.0 magnitude-only catalog.

- **Overall verdict:** **PARTIAL**
- Vindication threshold: ≥80% shrinkage of the targeted peak amplitude.

## `mars-7.96yr-diagonal` — verdict: **REJECTED**

- Recovered amplitude: **6.8976°**
- Recovered phase: **0.3426 rad** (19.63°)
- Average shrinkage: **2.7%**

| body | baseline (deg) | patched (deg) | Δ | shrinkage % |
| --- | ---: | ---: | ---: | ---: |
| mars | 3.4488 | 3.3557 | +0.0931 | 2.7% |

## `mercury-10.69yr-diagonal` — verdict: **REJECTED**

- Recovered amplitude: **18.3823°**
- Recovered phase: **3.0520 rad** (174.86°)
- Average shrinkage: **39.6%**

| body | baseline (deg) | patched (deg) | Δ | shrinkage % |
| --- | ---: | ---: | ---: | ---: |
| mercury | 9.1912 | 5.5469 | +3.6442 | 39.6% |

## `jupiter-saturn-9.56yr-coupled` — verdict: **PARTIAL**

- Recovered amplitude: **89.6502°**
- Recovered phase: **6.0217 rad** (345.02°)
- Recovered correlation: **+1**
- Average shrinkage: **76.8%**

| body | baseline (deg) | patched (deg) | Δ | shrinkage % |
| --- | ---: | ---: | ---: | ---: |
| jupiter | 44.6333 | 10.2403 | +34.3929 | 77.1% |
| saturn | 45.0169 | 10.6023 | +34.4146 | 76.4% |
