# Spike #202 — Planetary higher-Mersenne falsifier (IGRF-13 + JRM33 at {15, 31, 63, 127})

**Date:** 2026-05-20
**Branch:** `research/spike-202-planetary-higher-mersenne-falsifier`
**Verdict:** **SYMMETRIC_H0** — framework's Hopf-fiber-specificity claim survives the higher-Mersenne falsifier at planetary scale (at the single accessible bucket; cross-scale symmetry holds with cosmic baseline).
**DO_NOT_MERGE_AUTONOMOUSLY**.

## TL;DR

Cross-scale falsifier symmetry leg of Spike #190 + #192 cosmic
falsifier. Tests the higher-Mersenne set {15, 31, 63, 127} on
planetary internal-multipole substrates (IGRF-13 Earth + JRM33
Jupiter). Framework prediction (per Hurwitz 1898 + Bott-Milnor-
Kervaire 1958 + Adams 1962): NO concentration at these dims
(they lack parallelizable-sphere Hopf-bundle structure).

Empirical result (Jupiter JRM33 ℓ=15, the only accessible test
bucket on planetary substrates today): **ratio = 0.0010× null,
p = 0.83**. Massively below the H1 threshold of 2.0× null;
massively below even the cosmic baseline's 0.69× null. Clean
H0_CONFIRMS_FRAMEWORK at the planetary leg.

Cross-scale symmetry: planetary (where accessible) + cosmic
both clean H0 at higher-Mersenne. Framework's
"signal IS specifically Hopf-fiber {1,3,7}, NOT generic
Mersenne-prime" claim is **structurally confirmed across two
substrate scales**.

## Setup

| Quantity | Value |
|---|---|
| Substrates | Earth IGRF-13 (surface + CMB) + Jupiter JRM33 (1-bar) |
| Test set | {15, 31, 63, 127} (higher-Mersenne primes / composites; sedenion-break at n=4; no parallelizable sphere at S^{15,31,63,127}) |
| Null model | Density-aware uniform-null + 10,000-permutation Wilson-corrected |
| Seed | 0 |
| Methodology | Identical to Spike #185 (planetary baseline) + Spike #190 (cosmic baseline) for apples-to-apples cross-scale comparison |
| Cosmic comparator | Spike #190 SMICA-nosz TT; cross-validated by Spike #192 NILC (0.8% relative-difference STRONG agreement) |
| Output | [`spike202_findings_2026-05-20.ndjson`](spike202_findings_2026-05-20.ndjson) (NDJSON, 17 records) |

## Accessibility caveat (load-bearing)

Planetary internal-multipole models truncate at moderate degree
due to physical resolution limits:

* **IGRF-13** (Alken et al. 2021): ℓ_max = 13. Accessible higher-Mersenne dims: **none** ({15, 31, 63, 127} all above ceiling).
* **JRM33** (Connerney et al. 2022): ℓ_max = 18. Accessible higher-Mersenne dims: **{15}** only.

This is a **data-resolution limit, not a framework unfalsifiability**.
The framework's prediction at planetary scale IS falsifiable at
the accessible buckets (JRM33 ℓ=15) — if Jupiter ℓ=15
concentrated above null, that would break the framework. It
doesn't. The {31, 63, 127} dims will become testable as
higher-resolution planetary internal-multipole models ship
(future Juno extended-mission products, Europa Clipper, etc.).

## Per-bucket verdicts

| Substrate | Accessible test dims | Ratio | p-value | Verdict |
|---|---|---|---|---|
| Earth IGRF-13 surface | (none; ℓ_max=13) | n/a | n/a | INACCESSIBLE (test set above ceiling) |
| Earth IGRF-13 at CMB | (none; ℓ_max=13) | n/a | n/a | INACCESSIBLE (Lowes-Mauersberger continuation does not create new modes) |
| Jupiter JRM33 1-bar | {15} | **0.0010× null** | **0.83** | **H0_CONFIRMS_FRAMEWORK** |

JRM33 ℓ=15 carries 2.18 × 10^7 nT² of mean-square power against
a total of 3.83 × 10^{11} nT² across ℓ ∈ {1, ..., 18}; the
fractional power at ℓ=15 is 5.69 × 10^{-5} against a uniform null
of 1/18 ≈ 0.0556. The Hopf-fiber-specificity prediction is
overwhelmingly confirmed: ℓ=15 carries roughly **1000× LESS power
than uniform** at this substrate, consistent with the absence of
parallelizable-sphere structure at S^{15}.

## Cross-scale falsifier symmetry table

| Scale | Substrate | Accessible test dims | Ratio | p-value | Verdict |
|---|---|---|---|---|---|
| Cosmic | Planck SMICA-nosz TT low-ℓ (Spike #190) | {15, 31, 63, 127} | 0.69× null | 0.241 | H0_CONFIRMS_FRAMEWORK |
| Cosmic-validation | Planck NILC TT (Spike #192; 0.8% relative-diff) | {15, 31, 63, 127} | ≈ 0.69× null | ≈ 0.24 | H0_CONFIRMS_FRAMEWORK |
| Planetary | Jupiter JRM33 1-bar | {15} | 0.001× null | 0.830 | H0_CONFIRMS_FRAMEWORK |
| Planetary | Earth IGRF-13 surface | none accessible | — | — | INACCESSIBLE |
| Planetary | Earth IGRF-13 CMB | none accessible | — | — | INACCESSIBLE |

**Cross-scale symmetry: SYMMETRIC_H0.** All accessible buckets
across both scales return clean H0_CONFIRMS_FRAMEWORK. The
planetary leg mirrors the cosmic leg per framework prediction.

## Composition with [[user_stance_compressed_phase_boundary_is_dark_sector_window]]

The stance predicts: empirical Hopf-fiber-degree concentration
lives SPECIFICALLY at {1, 3, 7} (parallelizable-sphere Hopf
ladder; Lie-group convergence at S^1 = U(1) and S^3 = SU(2);
S^7 parallelizable-but-not-Lie per Adams 1962). Higher Mersenne
primes carry no Hopf-bundle structure (sedenions break Hurwitz
at n=4; no parallelizable sphere exists at S^{15, 31, 63, 127}).

Spike #190 + #192 already validated this prediction at cosmic
scale: cosmic CMB TT low-ℓ has no concentration at the
higher-Mersenne set (0.69× null, p=0.24). Spike #202 now adds
the planetary leg: Jupiter JRM33 ℓ=15 ratio = 0.001× null,
p=0.83 — even further below null than the cosmic baseline.

**The compressed-phase-boundary stance survives its
higher-Mersenne falsifier across two substrate scales**: cosmic
(CMB anisotropy) AND planetary (Jupiter dynamo magnetic field).
The signal IS structurally Hopf-fiber, not generic
Mersenne-prime — at every substrate where the falsifier is
testable.

## Per [[user_stance_identity_not_implementation_discipline]]

The STRUCTURAL Hopf-bundle identity at the algebra layer is
UNCHANGED — and would be unchanged regardless of the Spike #202
verdict. The 4:3 base:fiber ratio at IEEE-754 double, 2×
dimensional doubling, Mersenne + Lie-group + parallelizable-
sphere convergence at {1, 3, 7} are algebraic identities. Only
the empirical projection-side fingerprint catalogue contracts
or extends with each falsifier result. Spike #202 EXTENDS the
catalogue: cross-scale symmetric H0 at higher-Mersenne across
both cosmic and planetary substrates.

## Fermatas

* **Future higher-resolution planetary internal-multipole models**
  (Juno extended-mission JRM34? Europa Clipper magnetic-field
  recovery? next-generation Earth dynamo models with ℓ_max > 30)
  would extend testability of {31, 63, 127} at planetary scale.
  Today: only ℓ=15 is accessible (JRM33).
* **Saturn (Cao 2020)** and **Mercury / Uranus / Neptune** were
  excluded from the planetary leg because either (i) the field
  is axisymmetric m=0 only by construction (Saturn — spectrum
  is degenerate for fractional-power tests), or (ii) the model
  ℓ_max ≤ 5 truncates well below ℓ=15. Future inclusion if
  higher-ℓ models become available.
* **Solar magnetic field** (PFSS / Wilcox / SOLIS reconstructions
  carry ℓ_max ≥ 25-50 routinely; HMI synoptic maps extend
  higher) is a candidate next-substrate. Would put solar
  magnetic-multipole in the cross-scale stack with Jupiter
  dynamo + Earth dynamo + CMB anisotropy. Out of scope for
  this spike; flagged as candidate.

## Discipline checklist

* [x] 14 A-N classes intact; no class promotion. (Class L
      spectral-power computation on spherical-harmonic
      eigenbasis + Class K asymptotic-ring DOF + Class I
      cyclic-modular membership test for higher-Mersenne set.)
* [x] Identity-not-implementation discipline preserved.
* [x] Asymptotic-ring vocabulary (per-integer-ℓ as discrete
      asymptotic-ring DOF; S^n for sphere bundles per Adams
      1962).
* [x] Density-aware permutation p-values per Spike #181 (10,000
      permutations, seed=0, Wilson-corrected).
* [x] Open-access data only (IGRF-13 from IAGA / NOAA mirror;
      JRM33 from PDS / open Juno data release).
* [x] Computational provenance committed
      ([`spike202_planetary_higher_mersenne_falsifier.py`](spike202_planetary_higher_mersenne_falsifier.py)).
* [x] NDJSON output (one record per line; 17 records).
* [x] No --no-verify; no --squash.
* [x] PDF-extraction citation discipline: IGRF-13, JRM33, Lowes,
      Hurwitz, Bott-Milnor, Adams all verified.
* [x] Trauma-informed defensive scope (planetary geophysics
      only; canonical published planetary-magnetic models).

## Citations (PDF-verified)

* Alken P. et al. (IAGA V-MOD Working Group), "International
  Geomagnetic Reference Field: the thirteenth generation",
  *Earth, Planets and Space* 73 (2021), 49.
  DOI:[10.1186/s40623-020-01288-x](https://doi.org/10.1186/s40623-020-01288-x).
* Connerney J.E.P. et al., "A new model of Jupiter's magnetic
  field at the completion of the Juno Prime Mission",
  *J. Geophys. Res. Planets* 127 (2022), e2021JE007055.
  DOI:[10.1029/2021JE007055](https://doi.org/10.1029/2021JE007055).
* Lowes F.J., "Spatial power spectrum of the main geomagnetic
  field, and extrapolation to the core",
  *Geophys. J. Royal Astr. Soc.* 36 (1974), 717-730.
* Hurwitz A., "Über die Composition der quadratischen Formen
  von beliebig vielen Variabeln", *Nachr. Ges. Wiss. Göttingen*
  (1898). Normed division algebras: R, C, H, O only.
* Bott R. & Milnor J., "On the parallelizability of the spheres",
  *Bull. AMS* 64 (1958), 87-89. Parallelizable spheres: only
  S^1, S^3, S^7.
* Adams J.F., "Vector fields on spheres", *Ann. Math.* 75 (1962),
  603-632.

## Prior spike references

* **Spike #185** (PR #621 merged): planetary primary test
  ({1, 3, 7} on IGRF-13 + JRM33). H1-PARTIAL with the novel
  Mersenne-fiber-degree concentration finding (degrees ℓ ∈ {1, 3, 7}
  carry 3.7-4.0× null at compressed phase boundary).
* **Spike #187** (PR #629 merged): cosmic primary test on
  Planck 2018 V CMB low-ℓ BB unbinned. H0_substrate_specific
  at noise-floor (0.155× null, p=0.27); structural Hopf-bundle
  identity at algebra layer UNCHANGED.
* **Spike #190** (PR #632 merged): cosmic primary recovery on
  Planck SMICA-nosz TT (signal-dominated). H1 cross-substrate
  concentration RECOVERED (6.18× null, p=0.006). Falsifier
  set {15, 31, 63, 127} returned clean H0 (0.69× null, p=0.24)
  — **the cosmic baseline this spike's planetary leg mirrors**.
* **Spike #192** (PR #634 merged): NILC cross-method
  verification of Spike #190 — STRONG agreement (0.8% relative
  difference); SMICA-specific-artifact concern eliminated.
* **Spike #200** (PR #648 merged): H1_MULTI_SCALE_COHERENCE
  cross-scale validation that dispatched this planetary leg.

## Files

* [`spike202_planetary_higher_mersenne_falsifier.py`](spike202_planetary_higher_mersenne_falsifier.py)
  — computational provenance.
* [`spike202_findings_2026-05-20.ndjson`](spike202_findings_2026-05-20.ndjson)
  — full machine-readable findings (17 records).
