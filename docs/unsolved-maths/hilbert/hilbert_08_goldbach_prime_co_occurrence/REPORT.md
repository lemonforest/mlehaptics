# Hilbert 8 / Goldbach — Prime Co-Occurrence Cascade (Redirect 1 of 3)

**Parent**: [hilbert_08_goldbach_conjecture/REPORT.md](../hilbert_08_goldbach_conjecture/REPORT.md)
**Status**: cascade dispatched 2026-05-23; results recorded
**Class cascade**: A ∘ J ∘ I ∘ L (degree-sequence path graph)
**Source**: srmech catalog `hilbert_08_goldbach_prime_co_occurrence` (46 rows)

## Cascade design

Per prime p ≤ N_MAX=200, count `goldbach_degree(p)` = # of even n ∈ [4, 400] where p appears in SOME partition pair. Class L is applied to the sorted-degree-sequence path graph (edges weighted by degree-diff between consecutive ranks).

## Findings (2026-05-23)

| Stat | Value |
|------|-------|
| Primes ≤ 200 | 46 |
| Even n in scope | 199 (n ∈ [4, 400]) |
| Min degree | 1 (prime 2) = 0.5% of n |
| Max degree | 45 (prime 199) = 22.6% of n |
| Mean degree | 44.0 of 199 |
| Std degree | 6.4 |
| Class L Fiedler | 0.0047 |
| Class L spectral radius | 90.51 |
| Spectral gap (fiedler/max) | 0.000052 |

**Structural observation**: prime 2 is uniquely an outlier (degree 1, only used in n=4=2+2). Other primes cluster tightly around mean degree 44 with std 6.4 — a narrow distribution. The framework reading: **most primes participate in roughly equal numbers of Goldbach partitions**, suggesting a near-uniform sampling of the prime substrate by the Goldbach partition operation.

The large spectral gap (multiplicative ratio ~19000) on the sorted-degree-difference-weighted path graph indicates the degree sequence has a few outlier-induced jumps but is otherwise smooth. Per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`: open fermata — is the std/mean ratio (~0.145) related to the framework's 3:7 Hurwitz ratio or some other Hopf-bundle prediction?

## Run

```bash
python docs/unsolved-maths/hilbert/hilbert_08_goldbach_prime_co_occurrence/generate_catalog.py
```
