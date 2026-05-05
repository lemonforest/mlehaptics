# Phase-recovered catalog — patch-shrinks-residual verification

Re-run of the benchmark using the **phase-recovered** catalog (amplitudes scaled 2× and phases extracted from the FFT's complex bin) instead of the v0.4.0 magnitude-only catalog.

- **Overall verdict:** **VINDICATED**
- Vindication threshold: ≥80% shrinkage of the targeted peak amplitude.

## `mars-7.96yr-diagonal` — verdict: **VINDICATED**

- Recovered amplitude: **10.6890°**
- Recovered phase: **0.3378 rad** (19.36°)
- Average shrinkage: **99.2%**

| body | baseline (deg) | patched (deg) | Δ | shrinkage % |
| --- | ---: | ---: | ---: | ---: |
| mars | 3.4488 | 0.0272 | +3.4216 | 99.2% |

## `mercury-10.69yr-diagonal` — verdict: **VINDICATED**

- Recovered amplitude: **23.4815°**
- Recovered phase: **3.0538 rad** (174.97°)
- Average shrinkage: **99.9%**

| body | baseline (deg) | patched (deg) | Δ | shrinkage % |
| --- | ---: | ---: | ---: | ---: |
| mercury | 9.1912 | 0.0076 | +9.1836 | 99.9% |

## `jupiter-saturn-9.56yr-coupled` — verdict: **VINDICATED**

- Recovered amplitude: **113.2947°**
- Recovered phase: **6.0191 rad** (344.87°)
- Recovered correlation: **+1**
- Average shrinkage: **96.8%**

| body | baseline (deg) | patched (deg) | Δ | shrinkage % |
| --- | ---: | ---: | ---: | ---: |
| jupiter | 44.6333 | 1.0749 | +43.5584 | 97.6% |
| saturn | 45.0169 | 1.7956 | +43.2213 | 96.0% |
