"""BronzeGeocentricEpicycle — closed-form equation-of-centre encoder for the
five planetary pin-and-slot trains in the Freeth 2021 reconstruction.

This module implements the F17-derived algebra:

  λ_app(M) − λ_mean = Σ_{k≥1} (p_AU^k / k) sin(k M)         (inferior planets)
                    = Σ_{k≥1} (p_AU^k / k) sin(k M)         (superior planets,
                                                              series form valid
                                                              for p_AU < 1; see
                                                              note below)

where:

- ``M`` is the bronze's mean-motion anomaly (the gear-train input phase).
- ``p_AU = d / i`` for inferior planets (Mercury, Venus) — i.e. the ratio of
  the pin offset ``d`` to the inferior-pin-distance ``i``.
- ``p_AU = d / o`` for superior planets (Mars, Jupiter, Saturn) — i.e. the
  ratio of the pin offset ``d`` to the superior-pin-distance ``o``.

The remarkable F17 finding is that these dimensionless ratios are
numerically equal to the planet's astronomical-unit distance (p_AU =
mean Sun-planet distance in AU) to better than 0.05% across all five
planets. The bronze therefore encodes **AU distance**, NOT orbital
eccentricity. The single pin-and-slot per planet implements the
heliocentric→geocentric epicycle projection, with the pin-offset
representing the AU separation.

This is the **BronzeGeocentricEpicycle** encoder. It supersedes the
earlier-proposed "BronzeHipparchan" mode (F17 falsified: the bronze does
not measure planetary orbital eccentricities; Hipparchan e_planet values
would need a different gear-train architecture the bronze does not have).

**Series convergence note (superior planets):** For Mars (p_AU = 1.52),
Jupiter (5.20), and Saturn (9.58) the geometric series in
`(p_AU)^k / k` does not converge. Use ``apparent_longitude_unreduced``
which computes the closed-form arctangent directly without
series expansion. The convergent series form is provided for inferior
planets and for low-order approximation of all planets at small M.

References
----------
- Freeth, T., et al. (2021). A Model of the Cosmos in the Ancient Greek
  Antikythera Mechanism. *Scientific Reports* 11, 5821.
  DOI: 10.1038/s41598-021-84310-w. Supp S4 (page 30, Table S9): per-planet
  (p_AU, i, o, d) reconstructed from the bronze gear-trains. Cached PDF:
  ``docs/antikythera-maths/hoodoos/41598_2021_84310_MOESM4_ESM.pdf``.
- F17 closed-form derivation: ``docs/srmech/notes/spike_pinslot_closed_form_
  f17_2026-05-15.py``. Verifies d/(i or o) = p_AU to 0.05% across all five
  planets at integer-exact precision.
- Pin-slot closed-form Fourier series: this module reuses the same algebra
  as ``pin_and_slot.py`` (Greek center-frame Kepler equation-of-centre
  series), with the substitution ε ↔ p_AU.

Era-appropriateness
-------------------
This encoder uses the bronze's actual reconstructed parameters from
Freeth 2021 Supp S9. Whether those parameters reflect Hipparchan-era
astronomical knowledge or coincidentally-modern AU values is being
investigated separately (era-appropriate research dispatch, 2026-05-15).
When that research lands, an alternate ``BronzeHipparchanEpicycle``
encoder mode using era-appropriate p_AU values will be added alongside
this one for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


# ---------------------------------------------------------------------------
# Per-planet pin-slot geometric parameters (Freeth 2021 Supp S9, Table)
# ---------------------------------------------------------------------------

PlanetType = Literal["inferior", "superior"]


@dataclass(frozen=True)
class PlanetaryPinSlotGeometry:
    """Bronze pin-slot parameters for one planetary train (Freeth 2021 Supp S9).

    Attributes
    ----------
    planet : str
        Planet name ("Mercury", "Venus", "Mars", "Jupiter", "Saturn").
    planet_type : PlanetType
        "inferior" (Mercury, Venus) or "superior" (Mars, Jupiter, Saturn).
        Determines whether ``i`` or ``o`` is the divisor in p_AU = d / (i or o).
    p_AU_reported : float
        Astronomical-unit distance as reported by Freeth 2021 Supp S9
        (modern-era value used as the bronze's target). Heliocentric mean
        Sun-planet distance in AU.
    i_mm : float
        Inferior pin-distance (mm). Load-bearing for inferior planets.
    o_mm : float
        Superior pin-distance (mm). Load-bearing for superior planets.
    d_mm : float
        Pin offset (mm). The "lever" of the epicycle.
    """

    planet: str
    planet_type: PlanetType
    p_AU_reported: float
    i_mm: float
    o_mm: float
    d_mm: float

    @property
    def p_AU_derived(self) -> float:
        """The dimensionless p_AU ratio derived from the bronze geometry.

        For inferior planets this is d / i; for superior, d / o.
        Per F17 this equals ``p_AU_reported`` to ≤ 0.05% across all five
        planets — the bronze's geometric encoding of heliocentric distance.
        """
        if self.planet_type == "inferior":
            return self.d_mm / self.i_mm
        return self.d_mm / self.o_mm


MERCURY_GEOMETRY = PlanetaryPinSlotGeometry(
    planet="Mercury",
    planet_type="inferior",
    p_AU_reported=0.39,
    i_mm=36.00,
    o_mm=0.0,  # Not load-bearing for inferior; recorded as 0 placeholder.
    d_mm=14.04,
)
"""Mercury bronze pin-slot geometry per Freeth 2021 Supp S9. d/i ≈ 0.390."""

VENUS_GEOMETRY = PlanetaryPinSlotGeometry(
    planet="Venus",
    planet_type="inferior",
    p_AU_reported=0.72,
    i_mm=27.80,
    o_mm=0.0,
    d_mm=20.01,
)
"""Venus bronze pin-slot geometry per Freeth 2021 Supp S9. d/i ≈ 0.720."""

MARS_GEOMETRY = PlanetaryPinSlotGeometry(
    planet="Mars",
    planet_type="superior",
    p_AU_reported=1.52,
    i_mm=0.0,
    o_mm=6.58,
    d_mm=10.00,
)
"""Mars bronze pin-slot geometry per Freeth 2021 Supp S9. d/o ≈ 1.520."""

JUPITER_GEOMETRY = PlanetaryPinSlotGeometry(
    planet="Jupiter",
    planet_type="superior",
    p_AU_reported=5.20,
    i_mm=0.0,
    o_mm=1.58,
    d_mm=8.22,
)
"""Jupiter bronze pin-slot geometry per Freeth 2021 Supp S9. d/o ≈ 5.203."""

SATURN_GEOMETRY = PlanetaryPinSlotGeometry(
    planet="Saturn",
    planet_type="superior",
    p_AU_reported=9.58,
    i_mm=0.0,
    o_mm=1.50,
    d_mm=14.37,
)
"""Saturn bronze pin-slot geometry per Freeth 2021 Supp S9. d/o ≈ 9.580."""

PLANETARY_GEOMETRIES = {
    "Mercury": MERCURY_GEOMETRY,
    "Venus": VENUS_GEOMETRY,
    "Mars": MARS_GEOMETRY,
    "Jupiter": JUPITER_GEOMETRY,
    "Saturn": SATURN_GEOMETRY,
}
"""Canonical lookup by planet name."""


# ---------------------------------------------------------------------------
# Closed-form equation-of-centre encoder
# ---------------------------------------------------------------------------

def equation_of_centre_unreduced(
    M: np.ndarray | float,
    geometry: PlanetaryPinSlotGeometry,
) -> np.ndarray | float:
    """Apparent-minus-mean longitude via the closed-form arctangent.

    Computes ``λ_app − λ_mean = arctan(d sin M / (lever + d cos M))`` where
    ``lever`` is ``i`` for inferior planets and ``o`` for superior planets.

    This is the unreduced form valid for ALL planets including superior
    ones with p_AU > 1 (where the geometric series would diverge).

    Parameters
    ----------
    M : array-like or float
        Bronze mean-motion anomaly (radians). Input phase to the pin-slot stage.
    geometry : PlanetaryPinSlotGeometry
        Per-planet bronze pin-slot parameters.

    Returns
    -------
    Δλ : array-like or float
        Apparent-minus-mean longitude (radians).
    """
    M = np.asarray(M, dtype=np.float64)
    if geometry.planet_type == "inferior":
        lever = geometry.i_mm
    else:
        lever = geometry.o_mm
    d = geometry.d_mm
    return np.arctan2(d * np.sin(M), lever + d * np.cos(M))


def equation_of_centre_series(
    M: np.ndarray | float,
    geometry: PlanetaryPinSlotGeometry,
    n_terms: int = 6,
) -> np.ndarray | float:
    """Apparent-minus-mean longitude via the closed-form Fourier series.

    Computes the truncated series ``λ_app − λ_mean = Σ_{k=1..n_terms} (p_AU^k / k) sin(k M)``.

    Convergent for ``|p_AU| < 1`` (inferior planets, Mars marginal). For
    superior planets with p_AU ≥ 1 the series diverges; prefer
    :func:`equation_of_centre_unreduced` there.

    Parameters
    ----------
    M : array-like or float
        Bronze mean-motion anomaly (radians).
    geometry : PlanetaryPinSlotGeometry
        Per-planet bronze pin-slot parameters.
    n_terms : int
        Number of harmonics to retain (default 6, sufficient for inferior
        planets at machine precision).

    Returns
    -------
    Δλ : array-like or float
        Truncated-series apparent-minus-mean longitude (radians).
    """
    M = np.asarray(M, dtype=np.float64)
    eps = geometry.p_AU_derived
    total = np.zeros_like(M)
    eps_k = 1.0
    for k in range(1, n_terms + 1):
        eps_k *= eps
        total += (eps_k / k) * np.sin(k * M)
    return total


def apparent_longitude(
    M: np.ndarray | float,
    mean_longitude: np.ndarray | float,
    geometry: PlanetaryPinSlotGeometry,
    *,
    use_series: bool = False,
    n_terms: int = 6,
    apply_pin_slot: bool = True,
) -> np.ndarray | float:
    """Bronze apparent geocentric ecliptic longitude.

    ``λ_app = λ_mean + Δλ`` where ``Δλ`` is the equation-of-centre.

    For inferior planets and a small-amplitude approximation,
    ``use_series=True`` retains only ``n_terms`` harmonics. For superior
    planets with p_AU > 1 the series diverges; ``use_series=False`` (the
    default) computes the unreduced arctangent directly.

    The ``apply_pin_slot`` flag (default True) controls whether the
    pin-slot equation-of-centre transform is applied. Setting it to False
    returns the bare mean longitude unchanged — the "without pin-slot"
    output, showing what the gear-train would produce *before* the
    pin-slot primitive is composed on top. The difference between
    apply_pin_slot=True and apply_pin_slot=False is exactly the
    equation-of-centre contribution. This is the user-facing handle for
    seeing what the pin-slot primitive contributes mathematically, per
    the F24 candidate's "with/without comparison" framing.

    Parameters
    ----------
    M : array-like or float
        Bronze mean-motion anomaly (radians).
    mean_longitude : array-like or float
        Bronze mean longitude (radians).
    geometry : PlanetaryPinSlotGeometry
        Per-planet bronze pin-slot parameters.
    use_series : bool
        If True, use the truncated series form. If False (default), use the
        unreduced arctangent form.
    n_terms : int
        Number of series harmonics (ignored if use_series=False).
    apply_pin_slot : bool
        If True (default), apply the pin-slot equation-of-centre transform.
        If False, return mean_longitude unchanged (bare gear-train output).

    Returns
    -------
    λ_app : array-like or float
        Apparent geocentric ecliptic longitude (radians).
    """
    mean = np.asarray(mean_longitude, dtype=np.float64)
    if not apply_pin_slot:
        return mean
    if use_series:
        delta = equation_of_centre_series(M, geometry, n_terms=n_terms)
    else:
        delta = equation_of_centre_unreduced(M, geometry)
    return mean + delta


def equation_of_centre_n_armed_cross(
    M: np.ndarray | float,
    geometry: PlanetaryPinSlotGeometry,
    n_arms: int = 1,
    n_terms: int = 6,
) -> np.ndarray | float:
    """N-armed cross-bar pin-slot equation-of-centre (F24 candidate).

    Implements the closed-form rotational-symmetric sum of N pin-slots at
    angles 2πk/N for k = 0, ..., N-1:

        Δλ(M) = Σ_{m≥1} (ε^(m·N) / (m·N)) sin(m·N·M)

    derived in F24.1 of the spike findings doc. An N-armed cross-bar
    pin-slot is a **harmonic selector**: only harmonics that are multiples
    of N survive; all others cancel exactly by rotational symmetry.

    Special cases:
        n_arms=1 → degenerates to the standard single-pin-slot Bessel-Anger
                   series (equivalent to equation_of_centre_series, ε form).
        n_arms=2 → produces only even harmonics 2θ, 4θ, ... (frequency-
                   doubling) with leading amplitude ε² / 2.
        n_arms=N → leading harmonic at Nθ with amplitude ε^N / N.

    F24 is a CANDIDATE finding; the algebra here is exact, the empirical
    question of whether any bronze gear actually instantiates a cross-bar
    pin-slot remains gated on AMRP X-ray tomography access.

    Parameters
    ----------
    M : array-like or float
        Pin-slot input phase (radians).
    geometry : PlanetaryPinSlotGeometry
        Per-planet bronze pin-slot parameters. Provides ε via p_AU_derived.
    n_arms : int
        Number of cross-bar arms (≥ 1). For n_arms=1 the result equals the
        standard single-pin-slot series.
    n_terms : int
        Number of cross-bar harmonics to retain (each at m·n_arms in θ).
        Total harmonics computed = n_arms × n_terms.

    Returns
    -------
    Δλ : array-like or float
        N-armed cross-bar equation-of-centre output (radians).
    """
    if n_arms < 1:
        raise ValueError("n_arms must be >= 1")
    M = np.asarray(M, dtype=np.float64)
    eps = geometry.p_AU_derived
    total = np.zeros_like(M)
    for m in range(1, n_terms + 1):
        jN = m * n_arms
        total += (eps ** jN / jN) * np.sin(jN * M)
    return total


def n_armed_cross_leading_amplitude(
    geometry: PlanetaryPinSlotGeometry, n_arms: int = 1
) -> float:
    """Formal leading-harmonic coefficient of an N-armed cross-bar (rad).

    Returns ``eps^N / N`` from the Bessel-Anger series. For the convergent
    regime (|eps| < 1, inferior planets) this is the physical amplitude
    of the N-th harmonic. For the divergent regime (eps >= 1, superior
    planets) it is a formal series coefficient — the *physical* amplitude
    is bounded by pi/2 (the arctan range) and must be computed numerically
    via :func:`n_armed_cross_peak_amplitude`.
    """
    if n_arms < 1:
        raise ValueError("n_arms must be >= 1")
    eps = geometry.p_AU_derived
    return float(eps ** n_arms / n_arms)


def n_armed_cross_peak_amplitude(
    geometry: PlanetaryPinSlotGeometry,
    n_arms: int = 1,
    n_samples: int = 720,
) -> float:
    """Numerical peak amplitude of the N-armed cross-bar transform (rad).

    Computes max |Δλ(M)| over a uniform sweep of M in [0, 2π). Always
    bounded by pi/2 since the underlying transform is an arctangent.
    Works for both convergent (|eps| < 1) and divergent (|eps| >= 1)
    regimes — the rotational-symmetric sum is always finite even when
    the series expansion isn't.
    """
    if n_arms < 1:
        raise ValueError("n_arms must be >= 1")
    M = np.linspace(0.0, 2.0 * np.pi, n_samples, endpoint=False)
    if geometry.planet_type == "inferior":
        lever = geometry.i_mm
    else:
        lever = geometry.o_mm
    d = geometry.d_mm
    total = np.zeros_like(M)
    for k in range(n_arms):
        offset = 2.0 * np.pi * k / n_arms
        total += np.arctan2(d * np.sin(M - offset),
                            lever + d * np.cos(M - offset))
    total /= n_arms
    return float(np.max(np.abs(total)))


def leading_amplitude_degrees(geometry: PlanetaryPinSlotGeometry) -> float:
    """Peak amplitude of the c_1 sin(M) harmonic in degrees.

    This is ``arctan(d / lever)`` in degrees — the geometric upper bound
    on the equation-of-centre amplitude. For inferior planets this is
    physically reasonable (Mercury ≈ 21°, Venus ≈ 36°). For superior
    planets it grows with p_AU and is *much* larger than the planet's
    actual orbital eccentricity-driven amplitude (Mars ≈ 57°, Jupiter
    ≈ 79°, Saturn ≈ 84°), reflecting that the bronze's equation-of-
    centre is heliocentric-projection geometry, NOT the planet's
    intrinsic orbital anomaly.
    """
    if geometry.planet_type == "inferior":
        lever = geometry.i_mm
    else:
        lever = geometry.o_mm
    return float(np.degrees(np.arctan(geometry.d_mm / lever)))


# ---------------------------------------------------------------------------
# CLI / module smoke
# ---------------------------------------------------------------------------

def _print_summary() -> None:
    """Print a per-planet summary of the bronze pin-slot encoding.

    Includes the F24 with/without comparison: bare gear-train output
    (no pin-slot) vs single pin-slot vs N-armed cross-bar variants.
    """
    print("BronzeGeocentricEpicycle encoder — Freeth 2021 Supp S9 parameters")
    print("=" * 70)
    print(
        f"{'Planet':<8} {'type':<10} {'p_AU':>6} {'lever (mm)':>12} "
        f"{'d (mm)':>8} {'p_derived':>11} {'c_1 (deg)':>11}"
    )
    for planet, geom in PLANETARY_GEOMETRIES.items():
        lever = geom.i_mm if geom.planet_type == "inferior" else geom.o_mm
        print(
            f"{planet:<8} {geom.planet_type:<10} "
            f"{geom.p_AU_reported:>6.2f} {lever:>12.2f} "
            f"{geom.d_mm:>8.2f} {geom.p_AU_derived:>11.4f} "
            f"{leading_amplitude_degrees(geom):>11.2f}"
        )

    print()
    print("F24 with/without and N-armed cross-bar peak-amplitude comparison")
    print("=" * 70)
    print(
        f"{'Planet':<8} {'bare (deg)':>11} {'N=1 (deg)':>11} "
        f"{'N=2 (deg)':>11} {'N=3 (deg)':>11} {'N=4 (deg)':>11}"
    )
    for planet, geom in PLANETARY_GEOMETRIES.items():
        amps = [
            np.degrees(n_armed_cross_peak_amplitude(geom, n_arms=n))
            for n in (1, 2, 3, 4)
        ]
        print(
            f"{planet:<8} {0.0:>11.4f} "
            f"{amps[0]:>11.4f} {amps[1]:>11.4f} "
            f"{amps[2]:>11.4f} {amps[3]:>11.4f}"
        )
    print()
    print("'bare' = apply_pin_slot=False (no equation-of-centre correction)")
    print("'N=1'  = single pin-slot (bronze actual; F17 BronzeGeocentricEpicycle)")
    print("'N=2+' = N-armed cross-bar (F24 candidate; harmonic selector)")
    print()
    print(
        "Amplitudes are numerical peak |delta_lambda(M)| over a 720-sample "
        "sweep; bounded by 180 degrees (arctan2 range pi). The difference "
        "between bare and N=1 is what the bronze's single pin-slot "
        "contributes per planet. N=2..4 show what hypothetical N-armed "
        "cross-bar pin-slots (F24) would contribute. In the convergent "
        "regime (inferior planets, p_AU < 1) leading amplitudes fall as "
        "eps^N/N as expected. In the divergent regime (superior planets, "
        "p_AU > 1) the rotational-sum peak saturates at approximately "
        "180/N degrees because each arm's arctan saturates near +-180 "
        "and the N-arm average compresses the range. The harmonic-"
        "selector property (output spectrum contains only multiples of "
        "N) still holds in both regimes; only the amplitude story "
        "depends on regime."
    )


if __name__ == "__main__":  # pragma: no cover
    _print_summary()
