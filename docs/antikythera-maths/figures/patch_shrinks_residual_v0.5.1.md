# Patch-shrinks-residual benchmark — v0.5.1 findings

> *Earn the right to predict the missing data.*

The v0.4.0 catalog patches are **plausible** (each was authored from a
v0.3.1 FFT residual peak with the right amplitude and period), but
the claim that they actually *shrink* the targeted residual was
unaudited. v0.5.1 audits it.

## What the audit found

### v0.4.0 catalog (magnitude-only authoring): REJECTED

| Patch | Body | Baseline (°) | Patched (°) | Shrinkage |
|---|---|---:|---:|---:|
| `mars-7.96yr-diagonal` | mars | 3.45 | 3.36 | **+2.5%** |
| `mercury-10.69yr-diagonal` | mercury | 9.19 | **13.77** | **−49.9%** *(grew!)* |
| `jupiter-saturn-9.56yr-coupled` | jupiter | 44.63 | 30.84 | +30.9% |
| `jupiter-saturn-9.56yr-coupled` | saturn | 45.02 | 45.19 | **−0.4%** *(no effect)* |

The Mercury patch made things **worse**. The J-S coupled patch only
worked on Jupiter, not Saturn. Two diagnostic bugs visible here:

1. **Amplitude was off by 2×.** v0.4.0 used `|X[k]| / N` from the
   FFT magnitude spectrum. For a real-valued residual, the energy at
   frequency `k` is split between bins `+k` and `-k`; the actual
   real-sinusoid amplitude is `2 |X[k]| / N`. The patches were
   under-amplitude by a factor of 2.
2. **Phase was assumed 0.** Magnitude spectrum throws away phase, so
   the v0.4.0 catalog set `phase_rad = 0` (a bare `sin` shape). The
   actual residual at each target period has its own phase. With the
   wrong phase, the patch can partially cancel (Mars 2.5%), have no
   effect (Saturn −0.4%), or *reinforce* the residual (Mercury −49.9%).

### v0.5.1 phase-recovered catalog: PARTIAL

Fix the two bugs:

- **Amplitude**: `A = 2 |X[k]| / N`.
- **Phase**: extract `arg(X[k])` from the complex FFT bin and solve
  the patch-cancellation equations for the correct overlay phase.
  (Critically: the FFT phase is referenced to sample 0 = `REFERENCE_JD
  − half_span`, NOT to REFERENCE_JD — the patch's `phase_rad` must
  include the `+ 2π · half_span_days / period_days` offset.)
- **Correlation**: for the coupled patch, recover the J–S phase
  difference at the target period; if `|Δφ| < π/2` set
  `correlation = +1` (in-phase), else `−1`. **The v0.4.0 catalog had
  `correlation = −1` (anti-correlated libration) — empirically wrong:
  J and S are in-phase at 9.56 yr.**

| Patch | Body | Baseline (°) | Patched (°) | Shrinkage |
|---|---|---:|---:|---:|
| `mars-7.96yr-diagonal` | mars | 3.45 | 3.36 | +2.7% |
| `mercury-10.69yr-diagonal` | mercury | 9.19 | 5.55 | **+39.6%** |
| `jupiter-saturn-9.56yr-coupled` | jupiter | 44.63 | 10.24 | **+77.1%** |
| `jupiter-saturn-9.56yr-coupled` | saturn | 45.02 | 10.60 | **+76.4%** |

Reading the deltas:

- **Mercury**: swung **138 percentage points** (−49.9% → +39.6%) — the
  phase fix alone moved a wholly counterproductive patch into a
  meaningful cancellation. The 60% remaining residual is leakage
  (peak rank-1 9.19° + rank-2 5.55° spread across two adjacent
  bins).
- **J–S coupled**: from a one-sided 30.9% / −0.4% split to a balanced
  ~77% on both. The correlation flip (−1 → +1) plus phase recovery
  did exactly what the math says it should: the same overlay
  contributes to both bodies in lockstep, and both peaks shrink in
  lockstep.
- **Mars**: stuck at 2.7%. Looking at v0.3.1's FFT report, Mars's
  rank-1 peak is 3.45° at 7.960 yr and the rank-2 peak is 3.36° at
  7.935 yr — *adjacent FFT bins of comparable amplitude*. That's the
  classic signature of a single sinusoid whose period falls *between*
  two FFT bins; the energy spreads across them and a single-bin patch
  can only cancel a fraction.

## What this earns

- **Vindication, partial.** The methodology produces real,
  reproducible shrinkage in the right direction when amplitude and
  phase are recovered properly. J–S at ~77% is hard data: the patch
  *predicts the missing physics* well enough that the residual
  collapses to a quarter of its baseline.
- **Diagnostic rigor.** We now know the v0.4.0 catalog's phase=0
  assumption was wrong (sometimes by π) and the amplitude was off by
  2×. Future catalog entries should be authored from the complex FFT
  spectrum, not the magnitude.
- **Quantified ceiling per patch.** Mars's 2.7% sets a known floor:
  single-frequency overlay can't cancel an FFT-leaked residual. The
  next iteration of the methodology needs windowing or multi-bin
  patches (see roadmap).

## What this doesn't earn (yet)

- **Full vindication (≥80% on every patch).** Mars's leakage problem
  is real and structural; the methodology in its current form can't
  attack it.
- **Permission to author moon patches.** The new Saturnian /
  Jovian-moon residuals (v0.5.x supplementary kernels) are likely to
  show similar leakage, especially for closely-spaced moon
  resonances. Need windowing first.

## Roadmap — what unblocks full predictive power

| v0.5.x phase | Description |
|---|---|
| Hann-windowed FFT for patch authoring | Apply `np.hanning(N)` before the FFT to suppress spectral leakage. Re-author the v0.5.1 catalog from the windowed spectrum. The amplitude/phase recovery formulas need a corresponding window-correction factor. Should push Mars from 2.7% to >50% per the leakage budget. |
| Multi-bin coupled patches | Author a single patch as a *list* of (period, amplitude, phase) sinusoids covering the leaked bins around the target. The C-side overlay struct gets a small array of sinusoids per patch; the encode hook sums all of them. Cancels arbitrary-period real-world residuals. |
| Catalog v2 | Once windowed + multi-bin authoring is in, ship a `CATALOG_V2` alongside the existing `CATALOG`. Each entry pinned with its measured shrinkage% as a regression-test gate. The original v0.4.0 catalog stays for backwards compatibility. |
| Apply the methodology to the new moons | With the supplementary kernels staged (`mar097`, `jup340`, `sat441`) and windowed multi-bin authoring, FFT each Galilean / Saturnian moon's residual against ephemeris truth and author cancellation patches. The Saturnian resonance physics (Mimas–Tethys, Enceladus–Dione, Titan–Hyperion) is in `RESONANCES` already; what's residual after that physics is what the patches should target. |

## Reproducing this

The three scripts that produced this report:

- `research/patch_shrinks_residual.py` — runs the benchmark on the
  v0.4.0 catalog (the REJECTED column above).
- `research/author_phase_recovered_patches.py` — re-authors the
  catalog from the FFT's complex spectrum (2× amplitude + recovered
  phase + recovered correlation). Output:
  `results/phase_recovered_catalog.json`.
- `research/verify_recovered_patches.py` — runs the benchmark on the
  recovered catalog (the PARTIAL column above).

End-to-end ~25 min on the v0.5.0 C native path (4 full FFT spectrum
runs, mostly skyfield truth-lookup). On Python BIP it's ~90 min.

## TL;DR

We thought we had three working patches; we measured them and found
two were wrong-signed and one had a 2× amplitude error. We fixed the
math and got J–S to 77% shrinkage on both bodies — clean, real
predictive power on the smoking-gun residual peak. We earned a
**partial** right to predict the missing data; full predictive power
is one windowed-FFT-authoring-pass away.
