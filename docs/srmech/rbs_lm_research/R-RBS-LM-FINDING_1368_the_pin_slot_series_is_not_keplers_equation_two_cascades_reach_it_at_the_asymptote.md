# F1368 — **the single pin-slot series ε^k/k is not Kepler's equation beyond low order; Kepler's E(M) is reached by an iterated one-pin cyclic cascade and by a harmonic epicycle cascade with radii (2/k)J_k(ke), both exact only at the asymptote**

Session research, 2026-09-14, landed from the session scratchpad. The three scripts sit beside this finding verbatim; they were re-run for this landing and their outputs are committed beside them. Every figure below is **MEASURED** from those re-runs unless labelled otherwise.

**Instrument.** srmech 0.9.0rc472, imported from `D:/GitHub/mlehaptics/docs/srmech/python` (the main checkout, hard-coded in each script), pure cell (`HAS_NATIVE False` printed by each script). srmech ops: `math.kepler.kepler_solve` (E for M = E − e sin E), `math.kepler.pin_slot` (the rocker angle `atan2(ε sin θ, 1 + ε cos θ)`), `math.kepler._rsin` (Class-N sine), `music.bessel_j_fixed` (exact rational at a **declared** 2^-256 scale, not a claim that J_k is rational). Hand-rolled and disclosed in each docstring: the Fourier sine projection (plain N-point quadrature, N = 256 or 128), the sup-norm, and `math.sin` on the reconstruction side. No numpy is imported.

## 1 — one pin-slot series against Kepler's harmonics (`F1368_kepler_form_coeffs.py`)

Sine coefficients of Kepler's E(M) − M, of `pin_slot(θ, e, 1)`, and the series ε^k/k:

| e | k | Kepler E(M)−M | pin_slot | ε^k/k | Kepler / (ε^k/k) |
|---|---|---|---|---|---|
| 0.1 | 1 | 0.099875052072484 | +0.100000000000000 | 0.100000000000000 | 0.998751 |
| 0.1 | 2 | 0.004983354152784 | −0.005000000000000 | 0.005000000000000 | 0.996671 |
| 0.1 | 3 | 0.000372895365166 | +0.000333333333333 | 0.000333333333333 | 1.118686 |
| 0.1 | 4 | 0.000033067553865 | −0.000025000000000 | 0.000025000000000 | 1.322702 |
| 0.1 | 5 | 0.000003221450897 | +0.000002000000000 | 0.000002000000000 | 1.610725 |
| 0.3 | 1 | 0.296637632546208 | +0.300000000000000 | 0.300000000000000 | 0.988792 |
| 0.3 | 2 | 0.043665096715842 | −0.045000000000000 | 0.045000000000000 | 0.970335 |
| 0.3 | 3 | 0.009622685650577 | +0.009000000000000 | 0.009000000000000 | 1.069187 |
| 0.3 | 4 | 0.002511333138656 | −0.002025000000000 | 0.002025000000000 | 1.240165 |
| 0.3 | 5 | 0.000719768706944 | +0.000486000000000 | 0.000486000000000 | 1.481006 |

The pin-slot's magnitudes are exactly ε^k/k, with alternating sign. Against Kepler the ratio is within 1–3% at k = 1, 2 and departs from k = 3 on, further at each higher k and at larger e.

## 2 — Kepler as an iterated cascade of one-pin stages (`F1368_kepler_form_cascade_iter.py`)

`E_{n+1} = M + e·sin(E_n)`, `E_0 = M`; each stage is one gear at M carrying one pin of radius e whose phase is the previous stage's output. Sup-norm error against `kepler_solve` on a 128-point grid:

| depth | e = 0.1 | e = 0.3 | e = 0.7 |
|---|---|---|---|
| 1 | 5.179e-03 | 4.997e-02 | 3.096e-01 |
| 2 | 3.929e-04 | 1.119e-02 | 1.648e-01 |
| 3 | 3.297e-05 | 2.782e-03 | 9.488e-02 |
| 5 | 2.612e-07 | 1.952e-04 | 3.553e-02 |
| 10 | 1.875e-12 | 3.340e-07 | 4.055e-03 |
| 20 | 8.882e-16 | 1.410e-12 | 7.323e-05 |
| 40 | 8.882e-16 | 8.882e-16 | 4.355e-08 |

Depth 1 carries only the first harmonic (0.300000 at e = 0.3, the k = 2..4 coefficients 0). From depth 2 every printed harmonic is non-zero, and the harmonics converge on Kepler's own (at e = 0.3, depth 10 prints 0.296638, 0.043665, 0.009623, 0.002511).

## 3 — Kepler as a harmonic epicycle cascade (`F1368_kepler_form_cascade_harmonic.py`)

`E(M) = M + Σ_k (2/k) J_k(k e) sin(kM)`; each mode is one gear at integer ratio k (Class I) carrying a pin of radius (2/k)J_k(ke). The radii agree with the harmonics measured from `kepler_solve` to the six printed digits (the script's "measured" column is hard-coded from the §1/§2 runs): e = 0.3 gives 0.296638, 0.043665, 0.009623, 0.002511, and e = 0.7 gives 0.657991, 0.207356, 0.096851, 0.053334. Sup-norm error of the K-mode reconstruction:

| modes K | e = 0.3 | e = 0.7 |
|---|---|---|
| 1 | 5.198e-02 | 3.257e-01 |
| 2 | 1.246e-02 | 1.928e-01 |
| 4 | 1.012e-03 | 8.433e-02 |
| 8 | 1.129e-05 | 2.171e-02 |
| 16 | 2.908e-09 | 2.262e-03 |
| 32 | 8.882e-16 | 5.879e-05 |
| 60 | 8.882e-16 | 4.336e-08 |

## 4 — "exact only at the asymptote": what is measured and what comes from elsewhere

- **MEASURED here:** in every row the error falls with depth and with mode count, and at e = 0.1 and 0.3 it reaches 8.882e-16, the float resolution of this sup-norm instrument. At e = 0.7 neither construction reaches that floor by depth 40 or 60 modes (4.355e-08 and 4.336e-08). A floor is where this instrument stops seeing, so these runs do **not** measure exactness at any finite depth.
- **The exact statement is measured in F1369's supporting reports**, not here. The Opus report's S1, in exact `Fraction` arithmetic to e⁹, finds that depth n reproduces every Kapteyn lattice cell with e-order p ≤ n and none reliably at p = n + 1, while the K-mode truncation holds exactly the cells with k ≤ K. The Fable report's F1/F2 find that depth-n error scales with order n + 1 in every harmonic and that the depth frame has infinite harmonic support from depth 2. On both readings each finite truncation differs from E(M); they coincide only in the limit.
- **Not claimed:** that ε^k/k is wrong for the pin-slot. It is the pin-slot's own series (§1, and F1369). The finding concerns the Kepler label only.

## Honest scope

- Three eccentricities for the cascades (0.1, 0.3, 0.7), two for §1 (0.1, 0.3), k ≤ 5 in §1 and k ≤ 4 printed in §2–§3.
- The Fourier projection and the error norm are float instruments.
- The scripts hard-code the main-checkout import path at srmech 0.9.0rc472; this branch vendors an older srmech, so a re-run from this branch needs that path or an equivalent install.

## Companion files (all copied, none over 1 MB)

`F1368_kepler_form_coeffs.py` · `F1368_kepler_form_cascade_iter.py` · `F1368_kepler_form_cascade_harmonic.py` (verbatim copies of the scratch scripts `coeffs.py`, `cascade_iter.py`, `cascade_harmonic.py`), and their 2026-09-14 re-run outputs `F1368_kepler_form_coeffs.out.txt`, `F1368_kepler_form_cascade_iter.out.txt`, `F1368_kepler_form_cascade_harmonic.out.txt`.

**Composes:** F1369 (the May-record recheck that measured this lattice exactly), F1370 (the lattice factorisation and the fourth convergence radius).
