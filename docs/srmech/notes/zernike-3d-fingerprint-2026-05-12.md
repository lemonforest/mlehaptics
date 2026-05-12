# 3D Zernike moment fingerprint — FALSIFIED for discrimination at practical n_max (2026-05-12)

**Origin**: PR #337 documented the tradeoff between SO(3) invariance and cross-protein discrimination. 3D Zernike moments were flagged as the "next natural primitive" — theoretically combining radial polynomial basis with spherical harmonics for more invariants than SH power alone. User asked to test it as PR A of a three-PR sequence.

**Verdict**: **Falsified at practical n_max.** 3D Zernike fingerprints with n_max=10 collapse all discrimination — every protein looks identical (cosine 0.99999). Higher n_max hits factorial numerical issues. The SH per-shell approach from PR #337 stands as the better SO(3)-invariant geometric fingerprint.

Reproduce: `python -X utf8 docs/srmech/notes/zernike_3d_fingerprint_script.py`. Runtime ~30s.

---

## 3D Zernike construction

3D Zernike polynomial basis on the unit ball:

$$Z_{nlm}(r, \theta, \phi) = R_{nl}(r) \cdot Y_{lm}(\theta, \phi)$$

with constraint `n ≥ l` and `(n - l)` even. Moment:

$$\Omega_{nlm} = \int_{\text{ball}} f(r, \theta, \phi) \, Z^*_{nlm} \, dV$$

SO(3)-invariant fingerprint (Wigner-D mixes m-modes within fixed l):

$$F_{nl} = \sum_m |\Omega_{nlm}|^2$$

## Results

| Test | Z3D cosine |
|---|---:|
| Self | 1.000000 |
| Rotation 30° z | 1.000000 |
| Rotation 90° z | 1.000000 |
| Rotation 180° z | 1.000000 |
| Rotation 90° x | 1.000000 |
| Rotation 90° y | 1.000000 |
| Translation 10Å | 1.000000 |
| Thermal noise 0.5Å | 1.000000 |
| Thermal noise 2.0Å | 0.999993 |
| Thermal noise 5.0Å | 0.999992 |
| **1UBQ vs 1BPI** | **0.999991** |

**Headline**: rotation invariance works (1.0 everywhere) but **cross-protein discrimination is destroyed** — 1UBQ and 1BPI look essentially identical.

## Comparison across the three geometric fingerprints

| Test | Voxel HDC (PR #333) | SH power (PR #337) | 3D Zernike (this PR) |
|---|---:|---:|---:|
| Self | 1.000 | 1.000 | 1.000 |
| Rotation 90° z | **0.138** | **1.000** | **1.000** |
| Translation | 1.000 | 1.000 | 1.000 |
| **1UBQ vs 1BPI** | **−0.343** | **+0.929** | **+0.99999** |

The tradeoff curve I theorized in PR #337 turned out to be **monotonic-bad** for Zernike at this parameter regime:

- Voxel HDC: max discrimination (-0.34), no rotation invariance
- SH power: moderate discrimination (0.93), full rotation invariance
- **3D Zernike: zero discrimination (1.00), full rotation invariance** ← *worse than SH power*

## Diagnosis — why Zernike collapses

With n_max=10, only **36 valid (n, l) pairs** exist (n ≥ l, n - l even). The (0, 0) mode is the volume-integral of the field — approximately conserved across proteins because Fiedler eigenvectors are normalized. This single mode dominates the inner product:

$$\text{cosine}(F_A, F_B) \approx \frac{F_A^{(0,0)} F_B^{(0,0)}}{\|F_A\| \|F_B\|}$$

When the (0,0) mode dominates and is similar across proteins, the cosine collapses to 1.

The SH per-shell approach in PR #337 avoids this because it computes power spectra **independently per shell** (8 shells × 21 l-modes = 168 dimensions). Each shell captures different radial structure; you can't trivially dominate with one mode.

## Why higher n_max doesn't trivially fix it

To get discrimination back, n_max would need to grow until the higher-order modes outweigh (0,0). But:

- n_max = 15 → 64 pairs (~2× more)
- n_max = 20 → 121 pairs (~3× more)
- Radial polynomials use factorials of size `factorial(2n+1)` — at n=20, `factorial(41) ≈ 3.3e49` — exceeds float64 precision
- Numerically-stable Zernike polynomial evaluation requires recurrence relations or stable orthonormalization, neither implemented here

The Canterakis 1999 paper gives a stable recurrence; Novotni & Klein 2003 give an alternative formulation. Implementing these would take a real software project, not a 30-minute spike.

## Architectural lesson

**Theoretical "more invariants" ≠ better empirical fingerprint.** The reason matters:

| Approach | Information content | Empirical discrimination |
|---|---|---|
| SH per-shell (PR #337) | 8 × 21 = 168 dims, radial structure as **independent samples** | **0.93 cross-protein** (some signal) |
| 3D Zernike (this PR) | 36 dims, radial structure as **polynomial weights** | **0.99999 cross-protein** (no signal) |

**Same conceptual mathematical content; very different empirical behavior.** The compression scheme matters.

This is the same lesson as PR #333's encoding-must-match-data-type finding: the **representation** of an invariant carries empirical consequences beyond its theoretical properties. Zernike's polynomial radial basis compresses too aggressively for our protein-bipartition data.

## What this DOES confirm

- Rotation invariance theory works (Zernike SO(3) invariance holds at machine precision) ✓
- The PR #337 SH per-shell approach is a genuinely good design point on the tradeoff curve ✓
- The "geometric fingerprint" tier of the three-tier hierarchy is real but parameter-sensitive ✓

## What this falsifies

- The "naive 3D Zernike has more discrimination than SH power" claim
- The hope that low-dimensional rotation-invariant fingerprints would recover voxel-HDC-level discrimination
- The idea that the three-fingerprint comparison would form a smooth tradeoff curve (it's discrete: voxel HDC vs SH per-shell are useful; 3D Zernike at this n_max is not)

## What's NOT falsified (open paths for future)

- **Numerically-stable high-order Zernike** (Canterakis recurrence) — could test at n_max=20-30
- **3D Zernike on different data** (not bipartitions) — may work where (0,0) mode is more informative
- **SO(3) bispectrum** — different higher-order invariant, captures m-correlations
- **Augmented SH** — keep SH per-shell BUT also include cross-shell correlations as additional dims

## Recommendation for the catalog

**Stay with SH per-shell power spectrum** (PR #337) as the SO(3)-invariant geometric fingerprint. Don't add 3D Zernike at this implementation depth — it's worse, not better.

The geometric-fingerprint tier of the three-tier hierarchy currently has:

| Fingerprint | Status |
|---|---|
| Voxel HDC | active in catalog (PR #333) |
| SH per-shell power | active in catalog (PR #337) |
| **3D Zernike (n_max=10)** | **rejected by this spike** |

## Files

- `zernike_3d_fingerprint_script.py` — reproducible spike (~30s)
- `zernike-3d-fingerprint-per-test-2026-05-12.ndjson` — per-test results
- `zernike-3d-fingerprint-comparison-2026-05-12.png` — bar chart vs voxel HDC + SH power
- `zernike-3d-fingerprint-2026-05-12.md` — these findings

---

## Citations

- Canterakis 1999: "3D Zernike moments and Zernike affine invariants" — original
- Novotni & Klein 2003: "Shape retrieval using 3D Zernike descriptors"
- Both papers describe numerically-stable recurrence relations not implemented here
