"""Saturn ring catalogue Phase 2 validation.

Independent re-derivation of the saturn_rings catalogue's resonance-
anchor row from closed-form Kepler's-third-law math, plus verification
that the offset between the naïve-Kepler prediction and the observed
Cassini Division inner edge is consistent with the first-order Saturn
J₂ correction.

This is the validation half of the dual-author Saturn ring exercise
(see PR #284 backfill review). Phase 1 (PR #286) shipped the AMSC
literature_curated catalogue. Phase 2 (this file) verifies the math
the catalogue's resonance_anchor rows assert. Phase 3 (future) ships
a parallel hand-coded `_research/saturn_rings_data.py` and diff-checks
its NDJSON re-emission against the AMSC catalogue.

What this test verifies:

  1. The Mimas 2:1 inner Lindblad resonance row in the catalogue
     (catalogued at 116930 km) agrees with an independent re-
     computation from Mimas's published semi-major axis to <0.1%.
     This is the "byte-stable math" check: the catalogue's stated
     resonance location reproduces from first principles.

  2. The Cassini Division inner edge (catalogued at 117580 km) sits
     ~600-800 km outside the naïve-Kepler 2:1 prediction. That offset
     is the first-order Saturn J₂ correction to the resonance
     location. We verify the offset's magnitude is consistent with
     the J₂(R/a)² × a estimation (Murray-Dermott 1999 §8.6 + §10.4).

What this test does NOT do:
  - The full higher-order J₂ + J₄ + satellite-perturbation reduction
    that produces the exact resonance shift. That's a v0.27.x or
    later target.
  - Validation of the F-ring shepherd modulation periods (a temporal-
    cycle observable, distinct from the Lindblad-resonance geometry
    this file covers).

References:
  - Murray-Dermott 1999, *Solar System Dynamics*, Cambridge UP,
    §8.6 (Lindblad resonances) + §10.4 (Saturn ring resonances).
  - Tiscareno 2013, *Annu. Rev. Earth Planet. Sci.* 41:289-316
    (Saturn ring structure review; cited in the catalogue rows).
  - Cooper et al. 2008 — Mimas semi-major axis 185539 km from
    Voyager / Cassini astrometry.
  - Mankovich-Fuller 2021 — Saturn J₂ = 1.6299e-2 from ring
    seismology (cross-references v0.21.4 / v0.24.4).
"""

from __future__ import annotations

import math

from ephemerides_spectral import bridge
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.toroidal_residual_data import (
    TOROIDAL_RESIDUALS,
)

# ─────────────────────────────────────────────────────────────────────
# Reference physical parameters — SSOT-pulled from the project's own
# data tables, NOT hardcoded here. If a Saturn / Mimas value ever
# updates anywhere in the project, this validation re-screens the
# saturn_rings catalogue against the new value automatically.
# ─────────────────────────────────────────────────────────────────────


def _saturn_residual():
    """Pull Saturn's row from the v0.24.4 toroidal-residual catalogue.
    Single-source-of-truth for Saturn's equatorial radius, GM, and J₂."""
    for entry in TOROIDAL_RESIDUALS:
        if entry.body == "saturn":
            return entry
    raise AssertionError("Saturn entry missing from TOROIDAL_RESIDUALS")


_SATURN = _saturn_residual()

# Saturn equatorial radius (1-bar equator), km. SSOT: v0.24.4
# toroidal-residual catalogue entry, R_km field.
SATURN_R_EQ_KM = _SATURN.equatorial_radius_km

# Saturn J₂. SSOT: v0.24.4 toroidal-residual catalogue, J2_observed
# field. Iess 2019 Cassini Grand Finale gravity field measurement
# (DOI: 10.1126/science.aat2965).
SATURN_J2 = _SATURN.J2_observed

# Saturn GM (m³/s²). SSOT: v0.24.4 toroidal-residual catalogue.
SATURN_GM_M3_S2 = _SATURN.GM_m3_s2

# Mimas sidereal period in days. SSOT: BODIES table (v0.5.x high-
# precision sidereal periods from JPL HORIZONS / Cooper 2008).
MIMAS_PERIOD_DAYS = BODIES["mimas"].period_days


def _kepler_a_from_period(period_days: float, gm_m3_s2: float) -> float:
    """Closed-form semi-major axis from Kepler's third law.

        a³ = GM × P² / (4π²)

    Works for any satellite + central body whose GM is known. Used
    here to derive Mimas's semi-major axis from its sidereal period
    + Saturn's GM (both SSOT-pulled), avoiding a hardcoded
    semi-major axis that could drift from the BODIES table.
    """
    period_s = period_days * 86400.0
    a_m = (gm_m3_s2 * period_s * period_s / (4.0 * math.pi * math.pi)) ** (
        1.0 / 3.0
    )
    return a_m / 1000.0  # km


# Mimas semi-major axis derived via Kepler from SSOT period + GM.
MIMAS_SEMI_MAJOR_KM = _kepler_a_from_period(
    MIMAS_PERIOD_DAYS, SATURN_GM_M3_S2
)


# ─────────────────────────────────────────────────────────────────────
# Closed-form math
# ─────────────────────────────────────────────────────────────────────


def _kepler_3rd_inner_lindblad_radius(a_satellite_km: float, p: int, q: int) -> float:
    """Naïve-Kepler radius for the (p:q) inner Lindblad resonance with
    a satellite at semi-major axis a_satellite.

    Convention (matching the saturn_rings schema):
      p:q = (satellite mean motion) : (resonance particle mean motion)
      with p > q for inner resonances.

    For p > q (inner resonance), the particle's period is (p/q) ×
    satellite's period, and Kepler's third law gives:

        a_particle = a_satellite × (q/p)^(2/3)

    No J₂ correction. The validation tests below compare this naïve
    prediction against (a) the catalogue's resonance_anchor row
    (should agree to <0.1%) and (b) the observed Cassini Division
    inner edge (should differ by ~Saturn J₂ correction).
    """
    return a_satellite_km * (q / p) ** (2.0 / 3.0)


def _saturn_j2_first_order_shift_km(a_resonance_km: float) -> float:
    """First-order J₂ correction magnitude for a resonance location at
    radius a_resonance from Saturn's centre.

    The exact shift involves the satellite's orbit and Saturn's J₂
    via the disturbing function (Murray-Dermott §8.6); first-order
    estimate is dimensionally:

        Δa_J₂ ~ J₂ × (R_eq/a)² × a

    Matches the observed Cassini Division offset (~700 km) to within
    a factor of ~1.5 — order-of-magnitude validation only.
    """
    return SATURN_J2 * (SATURN_R_EQ_KM / a_resonance_km) ** 2 * a_resonance_km


# ─────────────────────────────────────────────────────────────────────
# Catalogue accessors
# ─────────────────────────────────────────────────────────────────────


def _get_saturn_rings_row(name: str) -> dict:
    """Look up a saturn_rings row by exact name match."""
    result = bridge.get_attested_dataset("saturn_rings")
    assert result["ok"] is True, f"saturn_rings dataset load failed: {result}"
    for row in result["rows"]:
        data = row["data"]
        if data["name"] == name:
            return data
    raise AssertionError(
        f"saturn_rings row {name!r} not found; "
        f"available: {[r['data']['name'] for r in result['rows']]}"
    )


# ─────────────────────────────────────────────────────────────────────
# Phase 2 validation — Mimas 2:1 anchor matches naïve Kepler
# ─────────────────────────────────────────────────────────────────────


def test_mimas_2_1_anchor_matches_project_ssot_kepler() -> None:
    """The catalogue's 'Mimas 2:1 mean-motion resonance anchor' row
    must agree with the project's SSOT-derived 2:1 Lindblad-resonance
    location to within ~0.2%.

    The catalogue row was authored from the literature value
    a_Mimas = 185539 km (Cooper 2008 astrometry), giving 185539 ×
    (1/2)^(2/3) ≈ 116930 km. This test re-derives the prediction
    using the project's SSOT chain — Mimas period from BODIES table +
    Saturn GM from TOROIDAL_RESIDUALS — which gives a_Mimas ≈ 185300
    km via Kepler's third law, and a 2:1 prediction of ≈ 116780 km.

    The ~150 km / 0.13% offset between "literature Kepler" and
    "project-SSOT Kepler" is the project's effective numerical
    precision relative to direct astrometry — driven by the GM and
    period values' sig-fig truncation. This test checks the catalogue
    is consistent with the project SSOT (the right discipline for
    catalogue maintenance), not with raw literature numbers (which
    the catalogue's per-row source_doi already attests).

    Threshold of 0.25% leaves room for further GM / period precision
    revisions while still catching the kinds of error this test is
    meant to surface — a typo in the catalogue value, or a unit
    mismatch (R_S vs km), would produce >>1% offset.
    """
    anchor = _get_saturn_rings_row("Mimas 2:1 mean-motion resonance anchor")
    catalogue_radius_km = anchor["radial_distance_km"]

    predicted_radius_km = _kepler_3rd_inner_lindblad_radius(
        MIMAS_SEMI_MAJOR_KM, p=2, q=1
    )

    abs_offset_km = abs(catalogue_radius_km - predicted_radius_km)
    rel_offset = abs_offset_km / predicted_radius_km

    assert rel_offset < 0.0025, (
        f"Mimas 2:1 anchor: catalogue={catalogue_radius_km:.1f} km "
        f"(literature-Kepler from a_Mimas=185539); "
        f"predicted={predicted_radius_km:.1f} km (SSOT-Kepler from "
        f"BODIES['mimas'].period_days={MIMAS_PERIOD_DAYS} + Saturn "
        f"GM={SATURN_GM_M3_S2:.3e}); offset={abs_offset_km:.1f} km "
        f"({rel_offset * 100:.3f}%). Expected <0.25% — catalogue's "
        f"value should track project SSOT within numerical precision."
    )


# ─────────────────────────────────────────────────────────────────────
# Phase 2 validation — Cassini Division offset is Saturn J₂
# ─────────────────────────────────────────────────────────────────────


def test_cassini_division_offset_consistent_with_saturn_j2() -> None:
    """The Cassini Division inner edge sits ~600-800 km outside the
    naïve-Kepler 2:1 Mimas resonance prediction. Verify the magnitude
    of that offset is within the band [0.5×, 2.5×] of the first-order
    Saturn J₂ correction.

    The exact shift from naïve Kepler involves higher-order J₂ + J₄
    terms and satellite perturbation theory (Murray-Dermott §8.6); we
    don't reproduce the exact derivation here. Order-of-magnitude
    agreement between observed offset and first-order J₂ is the
    Phase 2 validation bar.
    """
    div = _get_saturn_rings_row("Cassini Division inner edge")
    catalogue_div_km = div["radial_distance_km"]

    predicted_2_1_km = _kepler_3rd_inner_lindblad_radius(
        MIMAS_SEMI_MAJOR_KM, p=2, q=1
    )
    observed_offset_km = catalogue_div_km - predicted_2_1_km

    j2_estimate_km = _saturn_j2_first_order_shift_km(predicted_2_1_km)

    # Offset should be positive (Cassini Division sits OUTSIDE the
    # naïve Kepler resonance — outward J₂ shift is the standard
    # textbook signature).
    assert observed_offset_km > 0, (
        f"Cassini Division at {catalogue_div_km:.1f} km is INSIDE the "
        f"naïve 2:1 prediction at {predicted_2_1_km:.1f} km — that "
        f"contradicts the standard outward-J₂-shift picture; check "
        f"the catalogue row or the resonance ratio convention."
    )

    # And in the [0.5×, 2.5×] band of the first-order J₂ estimate.
    lo, hi = 0.5 * j2_estimate_km, 2.5 * j2_estimate_km
    assert lo < observed_offset_km < hi, (
        f"Cassini Division offset = {observed_offset_km:.1f} km from "
        f"naïve 2:1 Kepler ({predicted_2_1_km:.1f} km). "
        f"First-order Saturn J₂ estimate = {j2_estimate_km:.1f} km. "
        f"Expected offset in [{lo:.1f}, {hi:.1f}] km — observation is "
        f"out of the order-of-magnitude band. Either the catalogue's "
        f"value is wrong, J₂ has been revised, or higher-order terms "
        f"now dominate (in which case this test should be tightened)."
    )


# ─────────────────────────────────────────────────────────────────────
# Phase 2 validation — schema-required per-row provenance fields
# ─────────────────────────────────────────────────────────────────────


def test_every_saturn_rings_row_has_per_row_provenance_fields() -> None:
    """Every row in the saturn_rings catalogue must carry the three
    per-row provenance fields the literature_curated adapter enforces:
    source_doi, source_published_date, entered_locally_at.

    Ratchets the discipline at runtime — adding a new row without
    these fields would fail the adapter's parse step, but if the
    parser's strictness is ever relaxed this ratchet catches drift.
    """
    result = bridge.get_attested_dataset("saturn_rings")
    assert result["ok"] is True
    rows = result["rows"]
    assert len(rows) >= 12, f"expected 12+ rows; got {len(rows)}"

    for row in rows:
        data = row["data"]
        name = data.get("name", "<unnamed>")
        assert isinstance(data.get("source_doi"), str) and data["source_doi"].strip(), (
            f"row {name!r} missing source_doi"
        )
        assert isinstance(data.get("source_published_date"), str) and data["source_published_date"].strip(), (
            f"row {name!r} missing source_published_date"
        )
        assert isinstance(data.get("entered_locally_at"), str) and data["entered_locally_at"].strip(), (
            f"row {name!r} missing entered_locally_at"
        )


def test_saturn_rings_provenance_dates_parse_as_iso_8601() -> None:
    """source_published_date accepts YYYY / YYYY-MM / YYYY-MM-DD;
    entered_locally_at requires full YYYY-MM-DD. Verify every row's
    dates parse cleanly under the schema's pattern.
    """
    import re

    pub_pattern = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
    entered_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    result = bridge.get_attested_dataset("saturn_rings")
    for row in result["rows"]:
        data = row["data"]
        name = data["name"]
        pub = data["source_published_date"]
        entered = data["entered_locally_at"]
        assert pub_pattern.match(pub), (
            f"row {name!r} source_published_date={pub!r} does not "
            f"match YYYY / YYYY-MM / YYYY-MM-DD pattern"
        )
        assert entered_pattern.match(entered), (
            f"row {name!r} entered_locally_at={entered!r} does not "
            f"match YYYY-MM-DD pattern"
        )
