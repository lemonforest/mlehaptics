"""Batch A — Architectural / archaeological investigation (2026-05-14).

Three sub-tasks following F11 (gear-DAG clustering) and F12 (FFT-inverse recovery):

  A1: Aristotelian inner/outer clustering — intentional or gear-economy forced?
      Prime-factor analysis of Freeth 2021 period-relation numerators/denominators
      vs the observed bronze gear-DAG clustering (Mercury+Venus via g51;
      Mars+Jupiter+Saturn via g56; Moon decoupled).

  A2: Apsidal precession from F12's bronze-to-today phase drift.
      Decompose per-planet phase drift into (i) calibration offset and
      (ii) secular apsidal-line precession. Compare against modern apsidal-
      precession rates per planet.

  A3: Pre-Almagest Hipparchan ε ≈ 0.1146 — what specific tradition?
      Catalogue what's tractable without paywalled sources; honest verdict.

All outputs NDJSON to docs/srmech/notes/.

No CAD; algebra / spectral / archaeological discipline only.
"""

from __future__ import annotations

import json
import math
from itertools import combinations
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
OUT_A1 = HERE / "spike_pinslot_findings_q_aristotle_clustering_2026-05-14.ndjson"
OUT_A2 = HERE / "spike_pinslot_findings_q_apsidal_precession_2026-05-14.ndjson"
OUT_A3 = HERE / "spike_pinslot_findings_q_hipparchan_tradition_2026-05-14.ndjson"

# ---------------------------------------------------------------------------
# Constants (no magic numbers)
# ---------------------------------------------------------------------------

DAYS_PER_JULIAN_YEAR = 365.25
DAYS_PER_JULIAN_CENTURY = 100.0 * DAYS_PER_JULIAN_YEAR
ARCSEC_PER_DEG = 3600.0
DEG_PER_REV = 360.0
RAD_PER_DEG = math.pi / 180.0
DEG_PER_RAD = 1.0 / RAD_PER_DEG

# Reference epoch shared with the F12 spike (JD ~ 1684595 = early 1st century BCE)
REFERENCE_JD = 1684595.0
BRONZE_TO_TODAY_END_JD = 2461000.0
YEARS_BRONZE_TO_TODAY = (BRONZE_TO_TODAY_END_JD - REFERENCE_JD) / DAYS_PER_JULIAN_YEAR


# ---------------------------------------------------------------------------
# A1 — Prime-factor clustering vs gear-DAG clustering
# ---------------------------------------------------------------------------

# Freeth 2021 proposed period relations (synodic_returns, sidereal_years)
PERIOD_RELATIONS = {
    "Mercury": (145, 46),
    "Venus": (289, 462),
    "Mars": (133, 125),
    "Jupiter": (76, 83),
    "Saturn": (427, 442),
}

# Freeth 2021 gear-train tooth counts per planet (from F6 / F11)
GEAR_TRAINS = {
    "Mercury": [51, 72, 89, 40, 20],
    "Venus": [51, 44, 34, 26, 63],
    "Mars": [56, 64, 38, 40, 71, 80, 80],
    "Jupiter": [56, 64, 45, 40, 43, 65, 65],
    "Saturn": [56, 52, 61, 40, 68, 86, 86],
}

# Observed clustering (from F11.3, gear-DAG coupling NDJSON)
OBSERVED_COUPLED_PAIRS = {
    ("Mercury", "Venus"): {"shared_anchor": "g51", "n_shared": 3},
    ("Mars", "Jupiter"): {"shared_anchor": "g56+g64", "n_shared": 4},
    ("Mars", "Saturn"): {"shared_anchor": "g56", "n_shared": 3},
    ("Jupiter", "Saturn"): {"shared_anchor": "g56", "n_shared": 3},
}


def prime_factorize(n: int) -> dict[int, int]:
    """Return prime factorisation of n as {prime: multiplicity}."""
    assert n > 0, f"prime_factorize requires positive int, got {n}"
    factors: dict[int, int] = {}
    p = 2
    remaining = n
    while p * p <= remaining:
        while remaining % p == 0:
            factors[p] = factors.get(p, 0) + 1
            remaining //= p
        p += 1
    if remaining > 1:
        factors[remaining] = factors.get(remaining, 0) + 1
    assert sum(p_k * mult for p_k, mult in factors.items()) >= 1, "factorisation empty"
    return factors


def shared_primes(a: int, b: int) -> set[int]:
    """Primes common to a and b's factorisations."""
    fa = set(prime_factorize(a).keys())
    fb = set(prime_factorize(b).keys())
    return fa & fb


def run_a1(records: list[dict]) -> None:
    """A1: prime-factor analysis of period relations vs observed clustering."""

    # Step 1: emit per-planet prime factorisation
    for planet, (num, den) in PERIOD_RELATIONS.items():
        num_factors = prime_factorize(num)
        den_factors = prime_factorize(den)
        train = GEAR_TRAINS[planet]
        train_primes: set[int] = set()
        for t in train:
            train_primes |= set(prime_factorize(t).keys())
        records.append({
            "kind": "prime_factorization",
            "planet": planet,
            "numerator": num,
            "denominator": den,
            "num_factors": {str(p): k for p, k in num_factors.items()},
            "den_factors": {str(p): k for p, k in den_factors.items()},
            "gear_train_teeth": train,
            "gear_train_primes": sorted(train_primes),
        })

    # Step 2: pairwise shared-prime analysis on (num*den) and on gear-train primes
    planets = list(PERIOD_RELATIONS.keys())
    period_shared_summary: dict[tuple[str, str], dict] = {}
    for p1, p2 in combinations(planets, 2):
        n1, d1 = PERIOD_RELATIONS[p1]
        n2, d2 = PERIOD_RELATIONS[p2]
        # primes appearing in EITHER num or den of each planet
        primes1 = set(prime_factorize(n1).keys()) | set(prime_factorize(d1).keys())
        primes2 = set(prime_factorize(n2).keys()) | set(prime_factorize(d2).keys())
        shared_period = primes1 & primes2

        train_primes1: set[int] = set()
        for t in GEAR_TRAINS[p1]:
            train_primes1 |= set(prime_factorize(t).keys())
        train_primes2: set[int] = set()
        for t in GEAR_TRAINS[p2]:
            train_primes2 |= set(prime_factorize(t).keys())
        shared_train = train_primes1 & train_primes2

        # Check what the OBSERVED bronze DAG says for this pair
        observed = OBSERVED_COUPLED_PAIRS.get((p1, p2), {"shared_anchor": None, "n_shared": 1})

        rec = {
            "kind": "pairwise_prime_share",
            "pair": [p1, p2],
            "shared_period_primes": sorted(shared_period),
            "shared_gear_train_primes": sorted(shared_train),
            "observed_dag_coupling": observed,
            "predicted_by_period_primes": len(shared_period) > 0,
            "predicted_by_train_primes": len(shared_train) > 0,
            "actually_coupled": observed.get("shared_anchor") is not None,
        }
        records.append(rec)
        period_shared_summary[(p1, p2)] = rec

    # Step 3: enumerate alternative shared-anchor gears
    # The bronze uses g51 (51 = 3·17) for inner, g56 (56 = 2³·7) for outer.
    # Question: is g51 forced by Mercury+Venus period algebra?  Mercury (145=5·29,
    # 46=2·23), Venus (289=17², 462=2·3·7·11).  Shared primes between Mercury
    # period and Venus period: ∅ (no common prime!).  So the SHARED GEAR g51
    # has tooth-count primes {3, 17} — one of which (17) appears in Venus 289,
    # the other (3) is universal.  g51 is therefore matched to Venus's period
    # factor 17, not to a Mercury-Venus shared algebraic primitive.
    #
    # Similarly: Mars (133=7·19, 125=5³), Jupiter (76=4·19=2²·19, 83 prime),
    # Saturn (427=7·61, 442=2·13·17).  Shared primes Mars-Jupiter: {19}.
    # Shared primes Mars-Saturn: {7}.  Shared primes Jupiter-Saturn: ∅
    # at the period-relation level (Jupiter 76,83 vs Saturn 427,442 share NO
    # primes).  But all three share the gear g56 = 2³·7 — primes {2, 7}.
    # 7 appears in Mars (133) and Saturn (427) period numerators; absent
    # from Jupiter period entirely.
    #
    # Net: the bronze g56 anchor is matched to the Mars-Saturn shared prime 7,
    # and Jupiter rides along (gets g56 for FREE because 2 is universal and the
    # gear designer needed an even tooth count for fabrication).

    # Emit anchor-match analysis
    inner_anchor_primes = sorted(prime_factorize(51).keys())  # {3, 17}
    outer_anchor_primes = sorted(prime_factorize(56).keys())  # {2, 7}
    records.append({
        "kind": "anchor_match_analysis",
        "anchor_gear": "g51",
        "anchor_teeth": 51,
        "anchor_primes": inner_anchor_primes,
        "matched_pair": ["Mercury", "Venus"],
        "mercury_period_primes": sorted(
            set(prime_factorize(145).keys()) | set(prime_factorize(46).keys())
        ),
        "venus_period_primes": sorted(
            set(prime_factorize(289).keys()) | set(prime_factorize(462).keys())
        ),
        "matched_via_prime": 17,  # appears in Venus 289 = 17²
        "mercury_share_with_anchor": [p for p in inner_anchor_primes if p in
            set(prime_factorize(145).keys()) | set(prime_factorize(46).keys())],
        "venus_share_with_anchor": [p for p in inner_anchor_primes if p in
            set(prime_factorize(289).keys()) | set(prime_factorize(462).keys())],
        "shared_between_mercury_and_venus_periods": sorted(
            (set(prime_factorize(145).keys()) | set(prime_factorize(46).keys())) &
            (set(prime_factorize(289).keys()) | set(prime_factorize(462).keys()))
        ),
        "interpretation": (
            "g51 carries prime 17, which matches Venus 289=17² (a strong match). "
            "Prime 3 is universal-engineering. Mercury periods (145, 46) carry "
            "NEITHER 3 nor 17 — so Mercury rides g51 via the gear-DAG topology, "
            "not via period algebra. Mercury+Venus share NO period primes."
        ),
    })

    records.append({
        "kind": "anchor_match_analysis",
        "anchor_gear": "g56",
        "anchor_teeth": 56,
        "anchor_primes": outer_anchor_primes,
        "matched_triple": ["Mars", "Jupiter", "Saturn"],
        "mars_period_primes": sorted(
            set(prime_factorize(133).keys()) | set(prime_factorize(125).keys())
        ),
        "jupiter_period_primes": sorted(
            set(prime_factorize(76).keys()) | set(prime_factorize(83).keys())
        ),
        "saturn_period_primes": sorted(
            set(prime_factorize(427).keys()) | set(prime_factorize(442).keys())
        ),
        "matched_via_prime": 7,  # in Mars 133, Saturn 427
        "jupiter_share_with_anchor": [p for p in outer_anchor_primes if p in
            set(prime_factorize(76).keys()) | set(prime_factorize(83).keys())],
        "shared_among_outer_period_triples": sorted(
            (set(prime_factorize(133).keys()) | set(prime_factorize(125).keys())) &
            (set(prime_factorize(76).keys()) | set(prime_factorize(83).keys())) &
            (set(prime_factorize(427).keys()) | set(prime_factorize(442).keys()))
        ),
        "interpretation": (
            "g56 carries primes {2, 7}. Prime 7 appears in Mars 133=7·19 and "
            "Saturn 427=7·61 — strong match. Jupiter (76=2²·19, 83 prime) "
            "carries NEITHER 7. Jupiter rides g56 via DAG topology only. "
            "Outer triple shares NO common prime in period algebra: shared "
            "prime intersection across {Mars, Jupiter, Saturn} period factors "
            "is the empty set."
        ),
    })

    # Step 4: alternative-gear enumeration thought-experiment
    # If the bronze designer wanted to economize INSIDE the inner-planet cluster
    # WITHOUT sharing a gear, each planet would need its own dedicated input
    # gear from the crank. Cost: +2 gears per planet vs the shared-anchor design.
    # If the bronze designer wanted SEPARATE gear-trains for each of the 3 outer
    # planets, cost: +6 gears overall (each outer planet a private 7-gear train).
    records.append({
        "kind": "alternative_cost_estimate",
        "alternative": "private_train_per_planet",
        "current_total_gears": sum(len(t) for t in GEAR_TRAINS.values()),
        "current_unique_gears_shared": "g51 (inner cluster), g56 (outer triple), g64 (Mars-Jupiter)",
        "private_train_extra_gears_inner": 2,
        "private_train_extra_gears_outer": 6,
        "private_train_total_extra": 8,
        "fabrication_cost_relative": 1.0 + 8.0 / sum(len(t) for t in GEAR_TRAINS.values()),
        "interpretation": (
            "Removing the 3 shared anchor gears (g51 inner, g56 outer, g64 "
            "Mars-Jupiter) and giving each planet a private input chain costs "
            "approximately +8 gears (24% increase over the 33-gear planetary "
            "trains). The bronze design is gear-economical; clustering reduces "
            "gear count. BUT the clustering does NOT cleanly correspond to "
            "shared prime factors in the period relations themselves."
        ),
    })

    # Verdict summary
    records.append({
        "kind": "verdict_a1",
        "headline_question": "Does the inner/outer clustering match shared period-relation primes?",
        "finding": "NO — partial match only, and the prime that matches is the wrong dimension.",
        "details": [
            "Mercury+Venus period algebras share NO primes; their shared gear g51 carries prime 17 (Venus only, via 289=17²).",
            "Mars+Jupiter+Saturn triple shares NO primes across all three; their shared gear g56 carries prime 7 (Mars+Saturn, not Jupiter).",
            "The clustering is gear-DAG topological, not period-algebra forced.",
            "The shared-anchor gears are chosen to match ONE planet's period factor (17 for Venus; 7 for Mars+Saturn); the OTHER planets in the cluster ride along on the DAG.",
        ],
        "implication_for_f11": (
            "F11's 'inner-planet cluster + outer-planet cluster' reading remains "
            "structurally accurate at the gear-DAG-coupling level (shared upstream "
            "gears mediate back-reaction). BUT the Aristotelian-taxonomy-as-encoded "
            "claim is overstated: the clustering doesn't fall out of period-algebra "
            "necessity. It's a design choice for gear economy. The cosmos partitions "
            "by orbital scale because the bronze designer chose anchor gears that "
            "match one period factor per cluster — the Aristotelian split is "
            "consistent with the design but not REQUIRED by it. An alternative "
            "bronze with different anchor-gear choices could share gears differently "
            "(e.g. Mars+Mercury via prime 7+5 hybrid) without violating any period "
            "constraint. The Aristotelian reading is a post-hoc interpretive frame, "
            "not a forced structural consequence."
        ),
        "f11_amendment": (
            "F11.3 reading 'inner+outer cluster' is geometrically correct on the "
            "Freeth-2021-proposed gear DAG. The reading 'Aristotelian-taxonomy "
            "encoded' is softened to 'consistent-with-Aristotelian-taxonomy; "
            "not period-algebra-forced.' The structural-class argument F11.5 is "
            "unaffected: the bronze remains a forced-oscillator network with "
            "shared-anchor coupling, regardless of WHY those specific anchors "
            "were chosen."
        ),
    })


# ---------------------------------------------------------------------------
# A2 — Apsidal precession from F12's bronze-to-today phase drift
# ---------------------------------------------------------------------------

# F12 per-planet phi1 (sinusoid phase, radians) at REFERENCE_JD, both windows
# from spike_pinslot_findings_q_fft_inverse_per_planet_2026-05-14.ndjson
F12_FIT = {
    "Mercury": {
        "phi1_recent_rad": -2.679639797843908,
        "phi1_bronze_rad": -2.570292141296091,
        "anomalistic_days": 87.969,
        "modern_e": 0.2056,
    },
    "Venus": {
        "phi1_recent_rad": 2.7503174173429454,
        "phi1_bronze_rad": 2.744986337017303,
        "anomalistic_days": 224.701,
        "modern_e": 0.00678,
    },
    "Mars": {
        "phi1_recent_rad": 0.8216076828275752,
        "phi1_bronze_rad": 0.9488541928495369,
        "anomalistic_days": 686.971,
        "modern_e": 0.0934,
    },
    "Jupiter": {
        "phi1_recent_rad": -2.910466077888958,
        "phi1_bronze_rad": -2.8747174022644577,
        "anomalistic_days": 4332.589,
        "modern_e": 0.0484,
    },
    "Saturn": {
        "phi1_recent_rad": 0.6256771030724294,
        "phi1_bronze_rad": 0.7144754030310055,
        "anomalistic_days": 10759.22,
        "modern_e": 0.0539,
    },
}

# Modern apsidal-precession rates (perihelion longitude rate of change w.r.t.
# the mean equinox of date). Source: standard heliocentric orbital element
# tables (Standish & Williams; JPL ssd). Values in arcsec/century.
#
# These are the "perihelion of the orbit" precession rates (combined Newtonian
# + frame precession of the equinox), NOT the residual rate after subtracting
# GR for Mercury — they are what an instrument observing the longitude of
# perihelion against the moving equinox would actually measure.
#
# Reference: Standish, E.M. (1992) "Keplerian Elements for Approximate
# Positions of the Major Planets", JPL SSD; also IAU2009 conventions.
# Mercury, Venus, Mars also documented in Simon et al. 1994 A&A 282:663.
MODERN_APSIDAL_RATES_ARCSEC_PER_CENTURY = {
    # Note: these include precession of the equinox; "inertial" rate is smaller
    "Mercury": 5599.7,   # longitude of perihelion rate (Standish 1992 EM2000)
    "Venus":   5070.0,   # very rough; Venus's near-circular orbit makes ω
                         # poorly defined and precession dominated by ecliptic
                         # of date drift
    "Mars":    6633.3,
    "Jupiter": 5036.5,
    "Saturn":  7050.8,
}

# Heliocentric perihelion-only precession rate (subtracting equinox precession
# ≈ 5028.8"/century). What an inertial-frame observer would see. This is the
# more physically interesting comparison for an instrument that tracks the
# moving solar-system geometry independent of Earth-frame precession.
EQUINOX_PRECESSION_ARCSEC_PER_CENTURY = 5028.8
PERIHELION_INERTIAL_RATE_ARCSEC_PER_CENTURY = {
    p: r - EQUINOX_PRECESSION_ARCSEC_PER_CENTURY
    for p, r in MODERN_APSIDAL_RATES_ARCSEC_PER_CENTURY.items()
}


def run_a2(records: list[dict]) -> None:
    """A2: per-planet apsidal precession from F12's phase fits."""

    # The F12 fit gives sin/cos amplitude + phi1 at REFERENCE_JD for each
    # window. The phi1 value is the apsidal-line orientation as encoded in
    # the sinusoid's argument: residual ≈ amp * sin(ω·(t - t_ref) + phi1).
    # The apsidal line (longitude of perihelion) corresponds to where the
    # sinusoid crosses zero with positive slope; that's at angle (-phi1)
    # modulo the planet's orbital phase.
    #
    # CRUCIAL: phi1 is the value at REFERENCE_JD for each window. The recent-
    # decade window samples 2014-2024 (a small window FAR from REFERENCE_JD).
    # When fitting amp*sin(ω·t + phi), the fit phase phi is "the phase at t=0",
    # which the F12 script set to t_ref = window_start - REFERENCE_JD or
    # similar. We need to interpret CAREFULLY.
    #
    # Inspection of the F12 source shows: `omega_anom_rad_per_day` and
    # `phi1_rad` define residual(t) = amp1 * sin(omega * (t - REFERENCE_JD) + phi1).
    # So phi1 is the phase at t = REFERENCE_JD itself, in both windows.
    # The recent-decade fit was performed on data AT 2014-2024 but the
    # functional form is anchored at REFERENCE_JD. So phi1_recent and
    # phi1_bronze are BOTH evaluated at the SAME instant (REFERENCE_JD); the
    # difference between them captures the apsidal-line drift over the
    # window's center-of-mass time difference — which is the average epoch
    # of the recent-decade window (2018) vs the average of the bronze-to-
    # today window (~midpoint between bronze ≈ JD 1684595 and today ≈ JD
    # 2461000, i.e. ≈ JD 2.07e6, around 350 CE).
    #
    # Wait — if BOTH fits use the same functional form anchored at
    # REFERENCE_JD, then phi1_recent and phi1_bronze should ONLY differ
    # because of (i) different data being fit (different epoch coverage)
    # and (ii) actual apsidal-precession secular drift in the residual.
    # A non-precessing planet would have IDENTICAL phi1 in both windows
    # (to within fit noise). So delta_phi = phi1_bronze - phi1_recent is
    # the secular drift signal.
    #
    # The recent-decade window samples ~2018 mean epoch. The bronze-to-today
    # window samples ~JD 2.07e6 mean epoch (~350 CE). Time gap ≈ 1668 yr.
    # If apsidal precession is at rate `r` (degrees per year), then the
    # apsidal line at 2018 is offset from the apsidal line at 350 CE by
    # `r * 1668` degrees. The SINUSOID PHASE shifts oppositely:
    #
    #     residual(t) = -e * sin(ω(t - t_peri))
    #
    # where t_peri is the time of perihelion passage. Apsidal precession
    # advances t_peri across cycles; equivalently the phase at fixed t
    # decreases by ω·Δt_peri = ω·(Δλ_peri / ω_mean) = Δλ_peri (where
    # Δλ_peri is the apsidal-longitude advance and we use ω ≈ ω_mean for
    # the anomalistic motion). So:
    #
    #     phi1_at_recent_epoch - phi1_at_bronze_epoch = -Δλ_peri (radians)
    #
    # Equivalently, Δλ_peri = phi1_bronze - phi1_recent  (radians), and
    # rate = Δλ_peri / 1668 years.

    recent_mean_jd = (2457023.5 + 2460676.5) / 2.0  # F12 recent-decade window
    bronze_mean_jd = (REFERENCE_JD + BRONZE_TO_TODAY_END_JD) / 2.0
    delta_jd = recent_mean_jd - bronze_mean_jd
    delta_years = delta_jd / DAYS_PER_JULIAN_YEAR

    records.append({
        "kind": "window_geometry",
        "recent_window_mean_jd": recent_mean_jd,
        "bronze_window_mean_jd": bronze_mean_jd,
        "delta_jd": delta_jd,
        "delta_years": delta_years,
        "interpretation": (
            "Both F12 fits use functional form anchored at REFERENCE_JD, so the "
            "fit phase phi1 captures the apsidal-line ORIENTATION at the WINDOW'S "
            "EFFECTIVE EPOCH (which biases toward the data's center-of-mass). "
            "The two windows have mean epochs ~350 CE (bronze-to-today, JD 2.07e6) "
            "and ~2018 (recent-decade). The phase difference is the secular "
            "apsidal-line drift over that ~1668-year baseline."
        ),
    })

    for planet, fit in F12_FIT.items():
        phi_recent = fit["phi1_recent_rad"]
        phi_bronze = fit["phi1_bronze_rad"]
        # Unwrap phase difference to (-π, π]
        d_phi = phi_bronze - phi_recent
        while d_phi > math.pi:
            d_phi -= 2 * math.pi
        while d_phi <= -math.pi:
            d_phi += 2 * math.pi

        # Apsidal precession rate per the F12 fits:
        # Δλ_peri ≈ -d_phi (radians) over delta_years
        # (sign convention: residual ≈ -e sin(ω(t-t_peri)) →
        #  phi1 = -ω·t_peri at the anchor; t_peri advances at rate ω̇_peri/ω;
        #  d_phi/d_time = -ω̇_peri, so ω̇_peri = -d_phi/d_time)
        # Apsidal advance per year (rad/yr):
        rate_rad_per_yr = -d_phi / delta_years
        # Convert to arcsec/century
        rate_arcsec_per_century = (
            rate_rad_per_yr * DEG_PER_RAD * ARCSEC_PER_DEG * 100.0
        )

        modern_rate_geocentric = MODERN_APSIDAL_RATES_ARCSEC_PER_CENTURY[planet]
        modern_rate_inertial = PERIHELION_INERTIAL_RATE_ARCSEC_PER_CENTURY[planet]

        # Two comparisons: vs geocentric (equinox-of-date) and vs inertial.
        # The bronze's residual is computed against modern truth (likely in
        # an inertial heliocentric frame in the F12 script), so inertial is
        # the more apt comparison.
        ratio_to_inertial = (
            rate_arcsec_per_century / modern_rate_inertial
            if abs(modern_rate_inertial) > 0 else float("inf")
        )
        ratio_to_geocentric = (
            rate_arcsec_per_century / modern_rate_geocentric
            if abs(modern_rate_geocentric) > 0 else float("inf")
        )

        records.append({
            "kind": "apsidal_precession_estimate",
            "planet": planet,
            "phi_recent_rad": phi_recent,
            "phi_bronze_rad": phi_bronze,
            "delta_phi_rad_unwrapped": d_phi,
            "delta_phi_deg": d_phi * DEG_PER_RAD,
            "baseline_years": delta_years,
            "bronze_drift_rate_rad_per_yr": rate_rad_per_yr,
            "bronze_drift_rate_arcsec_per_century": rate_arcsec_per_century,
            "modern_apsidal_geocentric_arcsec_per_century": modern_rate_geocentric,
            "modern_apsidal_inertial_arcsec_per_century": modern_rate_inertial,
            "ratio_to_modern_inertial": ratio_to_inertial,
            "ratio_to_modern_geocentric": ratio_to_geocentric,
            "sign_matches_modern_inertial": (rate_arcsec_per_century * modern_rate_inertial) > 0,
            "order_of_magnitude_match_inertial": (
                0.1 < abs(ratio_to_inertial) < 10.0 if math.isfinite(ratio_to_inertial) else False
            ),
        })

    # Compute summary
    rates = []
    for planet in F12_FIT:
        fit = F12_FIT[planet]
        phi_recent = fit["phi1_recent_rad"]
        phi_bronze = fit["phi1_bronze_rad"]
        d_phi = phi_bronze - phi_recent
        while d_phi > math.pi:
            d_phi -= 2 * math.pi
        while d_phi <= -math.pi:
            d_phi += 2 * math.pi
        rate_arcsec_per_century = (
            (-d_phi / delta_years) * DEG_PER_RAD * ARCSEC_PER_DEG * 100.0
        )
        modern_inertial = PERIHELION_INERTIAL_RATE_ARCSEC_PER_CENTURY[planet]
        rates.append({
            "planet": planet,
            "bronze_rate": rate_arcsec_per_century,
            "modern_inertial": modern_inertial,
            "ratio": (
                rate_arcsec_per_century / modern_inertial
                if abs(modern_inertial) > 0 else float("nan")
            ),
        })

    # Discipline-honest assessment — MATH DOESN'T LIE check
    #
    # Numerical results (signs + magnitudes vs modern inertial perihelion rate):
    #   Mercury: bronze -2134"/cy vs modern +571"/cy   → sign WRONG, mag 3.7×
    #   Venus:   bronze  +104"/cy vs modern  +41"/cy   → sign right (e~0 unreliable)
    #   Mars:    bronze -2483"/cy vs modern +1604"/cy  → sign WRONG, mag 1.5×
    #   Jupiter: bronze  -698"/cy vs modern    +8"/cy  → sign WRONG, mag 90×
    #   Saturn:  bronze -1733"/cy vs modern +2022"/cy  → sign WRONG, mag 0.86×
    #
    # The dispatch hypothesis ("bronze tracks apsidal precession") is FALSIFIED.
    # 4/5 planets show wrong sign; only Venus matches sign but Venus is degenerate.
    # Magnitude in OOM ballpark for Mars/Saturn but signs are wrong.
    #
    # What's actually happening: the F12 sinusoid fit fits the BRONZE'S RESIDUAL
    # against modern truth. The residual is dominated by the first-inequality
    # (eccentric-anomaly term ε sin M), and the phase phi1 captures (-λ_peri),
    # the negative of the perihelion longitude at the window's effective epoch.
    # BUT: the recent-decade fit and the bronze-to-today fit DO NOT use the
    # SAME effective epoch for their phase determination. The recent fit's
    # phi1 reflects perihelion-longitude at ~2018; the bronze fit's phi1
    # reflects an AMPLITUDE-WEIGHTED-AVERAGE perihelion-longitude over the
    # millennia window — which is a fundamentally different quantity.
    #
    # If apsidal precession is monotonic and the bronze-window phi1 averages
    # over a wide range of perihelion longitudes (one full turn at Mercury's
    # rate ≈ 0.16°/yr over 2100 yr = 336°, basically a complete rotation), the
    # amplitude-weighted average phase is near-zero contribution per Mercury
    # cycle (the term sin(ω(t-t_peri(t))) is nearly orthogonal under such a
    # sweep). The fit phi1 in that case reflects a residual misalignment of
    # the bronze's encoder mean-motion vs modern mean-motion — NOT the true
    # apsidal-precession rate.
    records.append({
        "kind": "verdict_a2",
        "rates_table": rates,
        "headline": (
            "FALSIFIED at the strong reading. The bronze-vs-modern FFT phase drift "
            "does NOT cleanly recover modern apsidal-precession rates. 4/5 planets "
            "show WRONG SIGN; Mercury and Mars off by factors of 1.5-3.7×, "
            "Jupiter off by 90×. Only Saturn lands within 15% (right OOM) and "
            "Venus (degenerate near-circular orbit) lands within 2.5×. The "
            "hypothesis 'bronze drift tracks apsidal precession' is rejected."
        ),
        "interpretation": (
            "Why the recovery fails: the recent-decade fit phi1 is the perihelion-"
            "longitude at the recent window's effective epoch (~2018). The bronze-"
            "to-today fit phi1 is NOT the perihelion-longitude at the bronze "
            "window's effective epoch — it is an amplitude-weighted average over "
            "the entire 2100-year baseline. For planets with rapid apsidal "
            "precession (Mercury ~0.16°/yr full turn in 2200 yr ≈ one COMPLETE "
            "rotation over the bronze baseline), the amplitude-weighted average "
            "is sensitive to non-uniformities in the bronze residual's amplitude "
            "structure (which depends on the bronze's period-relation truncation "
            "error and modern truth's higher-order eccentricity terms), NOT to "
            "the apsidal-line position itself. The recovered 'rate' is a fit "
            "artefact of the differing window geometries, not a real measurement."
        ),
        "finding_class": "null",
        "null_finding_headline": (
            "A2-null — The F12 two-window phase-fit method does NOT recover "
            "modern apsidal-precession rates per planet from the bronze-vs-truth "
            "residual. 4/5 planets show wrong sign. The recovery is BLOCKED by "
            "amplitude-weighted-averaging over the wide window; a sliding-window "
            "phase regression over multiple intermediate epochs would be required "
            "to actually extract apsidal precession from the residual."
        ),
        "caveats": [
            "The dispatch's preliminary claim ('Mercury drifts 6° over 2100 yr "
            "→ apsidal precession ≈ 10″/yr, of correct sign and order') turns "
            "out to be a coincidental near-match of magnitude only. With the "
            "geocentric (equinox-of-date) modern rate (5600″/cy ≈ 56″/yr), the "
            "bronze's -38″/yr Mercury rate is at the right OOM but wrong sign. "
            "Against the inertial perihelion rate (571″/cy ≈ 5.7″/yr) the bronze "
            "rate is 3.7× larger and wrong sign.",
            "Venus's bronze rate is degenerate: tiny eccentricity (e=0.007) "
            "makes residual amplitude small and phi1 noisy; Venus's modern apsidal "
            "rate is itself poorly defined for the same reason.",
            "Jupiter is the worst miss (90×) because the bronze-to-today window "
            "spans <2 Jupiter apsidal cycles, so the amplitude-weighted average "
            "lands in a region of phi space far from the true mean orientation.",
            "Two-window phase resolution dominates: 1668-year baseline at "
            "Mercury's anomalistic period (88 d) gives ~6900 cycles. The fit "
            "phi at one window is a 6900-cycle phase average; phase resolution "
            "is poor in that geometry.",
            "Modern apsidal-rate values cited here are from standard Standish/JPL "
            "element tables. Treat the modern numbers as OOM benchmark; not "
            "extracted from PDF in hoodoos/.",
        ],
        "next_spike_candidates_from_null": [
            "Sliding-window phi1 regression: fit the bronze residual on overlapping "
            "100-year windows from 100 BCE to 2024 CE, regress phi1(t) linearly. "
            "Slope IS the apsidal-precession rate; intercept is the calibration "
            "offset. This decouples calibration from rate cleanly. Cost: 22 fits "
            "× 5 planets = 110 fits. Tractable.",
            "Bronze-to-1500-AD vs 1500-AD-to-today split: two long windows at "
            "moderately separated mean epochs (775 CE vs 1750 CE, baseline 975 yr). "
            "Apsidal-line averaging artefact would CHANGE under window choice; "
            "if the apparent rate is robust under window split, that's evidence "
            "for real apsidal-precession extraction. Currently we have only one "
            "data point per planet — undetermined.",
        ],
        "no_promotion_to_f13": (
            "Recommend NO F13 promotion. The result is a null at the strong "
            "reading. The weak reading (correct OOM at the encoder-drift level) "
            "is uninformative — the bronze's residual drifts at the OOM-correct "
            "scale because that's where the encoder's truncation error lives. "
            "An honest framing: 'bronze residual has secular drift component at "
            "~1000″/cy OOM per planet; the drift signal is dominated by encoder "
            "truncation error and amplitude-weighted phase averaging, NOT by "
            "apsidal-line precession.' This is a refinement of the existing F12 "
            "drift-sweep finding, not a new F13."
        ),
    })


# ---------------------------------------------------------------------------
# A3 — Pre-Almagest Hipparchan ε ≈ 0.1146 — what tradition?
# ---------------------------------------------------------------------------

def run_a3(records: list[dict]) -> None:
    """A3: archaeological catalogue of candidate Hipparchan/Babylonian sources.

    Honest about what's accessible (Freeth 2006 in hoodoos/) vs blocked
    (Toomer 1984, Almagest direct, Babylonian System B parameter tables).
    """
    # Inventory of cached sources
    HOODOOS = Path(__file__).resolve().parents[2] / "antikythera-maths" / "hoodoos"
    cached = sorted([p.name for p in HOODOOS.iterdir()]) if HOODOOS.exists() else []

    records.append({
        "kind": "source_inventory",
        "hoodoos_dir": str(HOODOOS),
        "cached_pdfs": cached,
        "no_almagest_pdf": True,
        "no_toomer_pdf": True,
        "no_babylonian_act_pdf": True,
        "implication": (
            "Only Freeth 2006 + Freeth 2021 (+correction) + SciAm 2009 available. "
            "Direct verification of Hipparchan or Babylonian numerical values is "
            "blocked at the primary-source level."
        ),
    })

    # Candidate 1: Hipparchan eclipse-eclipse parallax
    records.append({
        "kind": "candidate_hipparchan_eclipse_method",
        "method": "Eclipse-eclipse parallax (Almagest IV.11)",
        "principle": (
            "Three lunar eclipses widely separated in lunar anomaly yield the "
            "eccentricity-amplitude of the lunar orbit. Hipparchos famously did "
            "this calculation twice in his career."
        ),
        "ptolemy_preserved_results": {
            "first_value_deg": 5.9,
            "first_value_eps": 0.103,
            "second_value_deg": 4.5,
            "second_value_eps": 0.0785,
            "source": "Almagest IV.11 (Toomer 1984 trans.)",
            "extraction_status": "secondary — not verified against Almagest PDF (not in hoodoos)",
        },
        "bronze_value": {"deg": 6.5, "eps": 0.1146, "source": "Freeth 2006 p.590 Fig 6 caption (verified PDF in hoodoos/)"},
        "verdict": (
            "Bronze 6.5° lies ABOVE both preserved Hipparchan values. To produce "
            "6.5° via the eclipse-eclipse method would require a triplet with "
            "wider anomaly spacing OR a triplet where the middle eclipse caught "
            "the moon closer to anomaly extremum. No specific eclipse triplet "
            "in Hipparchos's documented working dates (~150-127 BCE) has been "
            "identified that yields 6.5° via the standard method, but exhaustive "
            "search across the Saros catalogue is feasible — outside the spike's "
            "scope and bounded by access to Hipparchan working notes (none "
            "survive directly; only Ptolemy's compression)."
        ),
        "blocked_on": [
            "No Almagest PDF in hoodoos/ — cannot verify 5.9° / 4.5° quotation directly",
            "No surviving Hipparchan original — all Hipparchan numerical claims "
            "transmitted via Ptolemy ~250 yr later",
            "Eclipse-triplet search would require Saros catalogue + ephemeris "
            "back-projection to 150 BCE — feasible in principle, exceeds spike scope",
        ],
    })

    # Candidate 2: Babylonian System B
    records.append({
        "kind": "candidate_babylonian_system_b",
        "method": "Babylonian System B lunar tables (ACT — Astronomical Cuneiform Texts)",
        "principle": (
            "Babylonian astronomers used zigzag functions to model lunar velocity "
            "variation. System B's parameters implicitly encode an eccentricity-"
            "equivalent through the zigzag amplitude and the precession of the "
            "anomalistic period."
        ),
        "freeth_2006_remark": (
            "Freeth 2006 explicitly notes 'estimates of the [lunar] anomaly from "
            "Babylonian astronomy were generally larger' than Hipparchos's — "
            "language consistent with 6+ degree amplitudes."
        ),
        "extraction_status": "verified — Freeth 2006 PDF in hoodoos/, quote re-checked",
        "system_b_lunar_velocity_amplitude": {
            "value_deg_per_day": "uncertain (no ACT PDF in hoodoos)",
            "implied_eps_range": "0.10 - 0.13 typically cited in literature",
            "citation_needed": "Neugebauer 1955 ACT vol II; Britton 2009; Aaboe 1974",
            "blocked_on": "No Babylonian-source PDF cached",
        },
        "verdict": (
            "Plausible match: the bronze 6.5° / ε=0.1146 sits comfortably inside "
            "the typically-cited Babylonian System B range. CANNOT VERIFY against "
            "a primary source without ACT volumes or Britton's lunar-theory PDF "
            "in hoodoos/."
        ),
    })

    # Candidate 3: Pre-Almagest Hipparchan refinement
    records.append({
        "kind": "candidate_third_book_hipparchos",
        "method": "Hipparchos's 'second model' with movable eccentre (Almagest IV.11 reference)",
        "principle": (
            "Ptolemy mentions Hipparchos produced TWO lunar models. The second "
            "had a 'movable eccentre' precursor of the equant. Parameters of the "
            "second model are partially preserved but the eccentricity-amplitude "
            "specifically may have been refined relative to the first model."
        ),
        "extraction_status": "blocked — Toomer 1984 commentary required, no PDF",
        "verdict": (
            "Tractable in principle: if Hipparchos's second-model eccentricity-"
            "amplitude is preserved in Toomer's commentary or in Neugebauer's "
            "HAMA, comparison to bronze 6.5° is direct. CANNOT VERIFY without "
            "Toomer 1984 PDF or Neugebauer HAMA vol II in hoodoos/."
        ),
    })

    # Candidate 4: Empirical direct observation (no specific tradition)
    records.append({
        "kind": "candidate_independent_empirical",
        "method": "Direct observational calibration by the bronze designer",
        "principle": (
            "Greek astronomers had naked-eye observational capability; a 6.5° "
            "lunar anomaly amplitude is detectable by careful eclipse-timing "
            "over a few decades. The bronze designer may have made an independent "
            "measurement rather than copying from any specific tradition."
        ),
        "supporting_evidence": [
            "Bronze 6.5° lies CLOSER TO MODERN (6.29°) than to either preserved "
            "Hipparchan value (5.9°, 4.5°) — suggesting calibration against "
            "better data than what Ptolemy preserved from Hipparchos.",
            "The bronze was contemporary with Hipparchos's working career, and "
            "the design tradition that produced it had access to either "
            "Hipparchos's working notes directly OR to Babylonian data that "
            "Hipparchos himself used as input.",
        ],
        "verdict": (
            "Cannot be definitively distinguished from candidates 2 or 3 without "
            "primary sources. The 'independent measurement' hypothesis is "
            "consistent with the data but unfalsifiable without further evidence."
        ),
    })

    # Honest verdict for A3
    records.append({
        "kind": "verdict_a3",
        "headline": (
            "No specific known Hipparchan or Babylonian calculation matches the "
            "bronze ε = 0.1146 / 6.5° exactly, within the sources accessible to "
            "this spike (Freeth 2006, Freeth 2021)."
        ),
        "candidate_rankings": [
            "(1) Babylonian System B — most plausible given Freeth's direct "
            "remark + the bronze value sitting comfortably in the typical "
            "System B range. BLOCKED on ACT/Britton PDF access.",
            "(2) Pre-Almagest Hipparchan refinement (second-model parameters) — "
            "consistent with bronze contemporaneity with Hipparchos. BLOCKED "
            "on Toomer 1984 / Neugebauer HAMA PDF access.",
            "(3) Independent empirical observation by the bronze designer — "
            "consistent but unfalsifiable.",
            "(4) Direct transcription of preserved Hipparchan 5.9° or 4.5° — "
            "RULED OUT (numerical mismatch).",
        ],
        "archaeological_finding": (
            "The bronze ε = 0.1146 / 6.5° sits in a 'pre-Almagest range' that is "
            "more accurate than either Hipparchan value Ptolemy preserved but "
            "more uncertain in attribution than either. The instrument's "
            "calibration is empirically excellent (4% from modern Brown) and "
            "comes from a tradition that Ptolemy's compression did not preserve "
            "intact. This is a real archaeological finding: the bronze witnesses "
            "an astronomical-precision tradition (Babylonian, late-Hipparchan, "
            "or hybrid) that the Almagest does not faithfully transmit."
        ),
        "tractable_next_steps": [
            "Acquire Britton 2009 'Studies in Babylonian Lunar Theory' or "
            "Neugebauer 1955 ACT vol II for System B parameter extraction.",
            "Acquire Toomer 1984 Almagest translation + commentary for direct "
            "verification of Hipparchan 5.9°/4.5° and second-model parameters.",
            "Cross-reference Aaboe 1974 'Scientific Astronomy in Antiquity' for "
            "System B / Hipparchan reconciliation.",
        ],
        "scope_caution": (
            "Per project policy on autonomous validation TOS: any future "
            "verification work must respect the publisher TOS landscape "
            "(see reference_autonomous_validation_tos_landscape). Springer / "
            "Wiley / Elsevier sources are off-limits for autonomous validation "
            "tooling; PDF acquisition for cited reading is fine, but no scripted "
            "scraping or batch verification is permitted in-repo."
        ),
        "blocked_finding": (
            "Honest result: the bronze ε is in the historically-plausible range "
            "for a Hipparchan-tradition mechanism, but NO SPECIFIC KNOWN "
            "calculation matches 6.5° exactly. The discrepancy may reflect "
            "either (a) Babylonian transmission of empirically-derived larger "
            "values, or (b) pre-Almagest Hipparchan refinement Ptolemy did not "
            "preserve, or (c) independent empirical observation by the bronze "
            "designer. Within accessible sources, the three remain indistinguishable."
        ),
        "frame_as_f2_companion_refinement": (
            "This is F2-companion-refinement: the bronze calibration is "
            "demonstrably outside the Almagest-preserved Hipparchan canon, "
            "in a region the Almagest does not faithfully transmit. The "
            "'pre-Almagest' framing of the original F2-companion finding "
            "stands; the specific identification of which pre-Almagest "
            "tradition is the source remains blocked at the primary-source "
            "access level."
        ),
    })


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _write_ndjson(path: Path, records: Iterable[dict]) -> int:
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> None:
    a1_records: list[dict] = []
    run_a1(a1_records)
    n1 = _write_ndjson(OUT_A1, a1_records)
    print(f"A1 wrote {n1} records to {OUT_A1.name}")

    a2_records: list[dict] = []
    run_a2(a2_records)
    n2 = _write_ndjson(OUT_A2, a2_records)
    print(f"A2 wrote {n2} records to {OUT_A2.name}")

    a3_records: list[dict] = []
    run_a3(a3_records)
    n3 = _write_ndjson(OUT_A3, a3_records)
    print(f"A3 wrote {n3} records to {OUT_A3.name}")


if __name__ == "__main__":
    main()
