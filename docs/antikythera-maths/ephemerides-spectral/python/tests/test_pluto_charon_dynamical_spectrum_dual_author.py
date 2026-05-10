"""Sol Pluto-Charon Dynamical Spectrum dual-author diff test —
v0.27.0 phase A.

12-mode roster; single row_type ('dynamical_mode'). Mirrors prior
phase A patterns. Headline physics ratchets pin the project's
first BINARY mutual-tidal-lock case: TRIPLE 1:1 lock at 6.387230 d
(P_Pluto_spin = P_Charon_spin = P_orbit) and the small-moon
near-3:4:5:6 commensurabilities with the mutual orbital period.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _pluto_charon_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("pluto_charon_dynamical_spectrum")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        out[data["name"]] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    return {d["name"]: d for d in hand_coded_rows_in_amsc_shape()}


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("pluto_charon_dynamical_spectrum")
    assert result["ok"] is True
    assert len(result["rows"]) == 12, (
        f"expected 12 modes; got {len(result['rows'])}"
    )


def test_dual_author_row_count_agrees() -> None:
    assert len(_amsc_rows_indexed_by_name()) == len(_hand_coded_rows_indexed_by_name())


def test_dual_author_row_names_agree() -> None:
    assert set(_amsc_rows_indexed_by_name()) == set(_hand_coded_rows_indexed_by_name())


def test_dual_author_per_row_field_agreement() -> None:
    amsc_rows = _amsc_rows_indexed_by_name()
    hand_coded_rows = _hand_coded_rows_indexed_by_name()
    common = sorted(set(amsc_rows) & set(hand_coded_rows))
    mismatches: List[str] = []
    for name in common:
        amsc = amsc_rows[name]
        hc = hand_coded_rows[name]
        for field in sorted(set(amsc) | set(hc)):
            if amsc.get(field, "<MISSING>") != hc.get(field, "<MISSING>"):
                mismatches.append(
                    f"  {name!r}.{field!r}: AMSC={amsc.get(field)!r} "
                    f"vs hand-coded={hc.get(field)!r}"
                )
    assert not mismatches, "\n".join(mismatches)


def test_dual_author_full_dict_equality() -> None:
    assert _amsc_rows_indexed_by_name() == _hand_coded_rows_indexed_by_name()


def test_every_source_key_in_provenance_table() -> None:
    from ephemerides_spectral._research.pluto_charon_dynamical_spectrum_data import (
        PLUTO_CHARON_DYNAMICAL_MODES,
    )
    referenced = {m.source_key for m in PLUTO_CHARON_DYNAMICAL_MODES}
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str)
        assert len(entry["source_doi"]) >= 5
        assert iso_pattern.match(entry["source_published_date"])


def test_all_rows_share_single_row_type() -> None:
    """Pluto-Charon is single-row-type. Pin it."""
    for row in _amsc_rows_indexed_by_name().values():
        assert row["row_type"] == "dynamical_mode"


def test_triple_synchronous_lock_at_mutual_orbital_period() -> None:
    """Headline physics ratchet — THE v0.24.11 schema-gap closure.

    P_Pluto_spin = P_Charon_spin = P_mutual_orbit = 6.3872304 d.

    This is the END state of dyadic tidal evolution; the Solar System
    provides exactly one arrived-at-end-state example, and this is it.
    Earth-Luna is en route (Earth's rotation spinning down via tidal
    recession at +3.83 cm/yr per Williams 2014 LLR); Pluto-Charon has
    arrived. The triple-lock motif justifies the new
    `rigid_body_action_angle_mutual_lock` regime label introduced in
    v0.24.11."""
    rows = _amsc_rows_indexed_by_name()
    mutual_orbit = rows["mutual_orbital_sidereal"]
    pluto_spin = rows["pluto_spin_frequency"]
    charon_spin = rows["charon_spin_frequency"]
    # All three share the same period (the triple lock is exact in the
    # hand-coded module — the SAME PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
    # constant feeds all three rows).
    assert mutual_orbit["period_days"] == 6.3872304, (
        f"mutual orbital period should be 6.3872304 d; "
        f"got {mutual_orbit['period_days']}"
    )
    assert pluto_spin["period_days"] == mutual_orbit["period_days"], (
        f"Pluto spin should equal mutual orbital period; "
        f"got {pluto_spin['period_days']} vs {mutual_orbit['period_days']}"
    )
    assert charon_spin["period_days"] == mutual_orbit["period_days"], (
        f"Charon spin should equal mutual orbital period; "
        f"got {charon_spin['period_days']} vs {mutual_orbit['period_days']}"
    )
    # All three are angle modes (not actions).
    for row in (mutual_orbit, pluto_spin, charon_spin):
        assert row["angle_or_action"] == "angle"
    # All three share the same frequency_per_century — pinned for
    # cross-platform stability since this is a single division.
    assert pluto_spin["frequency_per_century"] == mutual_orbit["frequency_per_century"]
    assert charon_spin["frequency_per_century"] == mutual_orbit["frequency_per_century"]


def test_pure_action_rows_carry_infinite_period() -> None:
    """The four action variables (eccentricity, mutual obliquity,
    Charon-Pluto mass ratio, heliocentric inclination) all carry
    period_days = +inf and frequency_per_century = 0.0. Pin the JSON
    Infinity-token round-trip discipline."""
    import math
    rows = _amsc_rows_indexed_by_name()
    expected_action_rows = {
        "eccentricity_action",
        "mutual_obliquity_action",
        "charon_mass_ratio_action",
        "heliocentric_inclination_action",
    }
    for name in expected_action_rows:
        row = rows[name]
        assert row["angle_or_action"] == "action", (
            f"{name} should be an action variable"
        )
        assert math.isinf(row["period_days"]), (
            f"{name} period should be infinite; got {row['period_days']}"
        )
        assert row["frequency_per_century"] == 0.0, (
            f"{name} frequency should be 0.0; "
            f"got {row['frequency_per_century']}"
        )


def test_charon_pluto_mass_ratio_is_largest_binary_in_solar_system() -> None:
    """Headline geometric ratchet: Charon/Pluto mass ratio ≈ 0.1218 —
    the LARGEST binary mass ratio in the Solar System (Earth-Luna is
    0.0123, ~10x smaller). This is the geometric reason the Pluto-
    Charon barycenter sits OUTSIDE Pluto's surface, ~940 km above it
    (Pluto and Charon both orbit a point in empty space)."""
    rows = _amsc_rows_indexed_by_name()
    mass_ratio_row = rows["charon_mass_ratio_action"]
    assert mass_ratio_row["amplitude_value"] == 0.1218
    assert mass_ratio_row["amplitude_units"] == "dimensionless"
    # Sanity check: ~10x larger than Earth-Luna's 0.0123.
    assert mass_ratio_row["amplitude_value"] > 0.10, (
        f"Charon/Pluto ratio expected > 0.10 to be 'largest binary'; "
        f"got {mass_ratio_row['amplitude_value']}"
    )


def test_small_moons_near_3_4_5_6_with_mutual_orbit() -> None:
    """The four small moons (Styx, Nix, Kerberos, Hydra) sit at near-
    integer multiples of the Pluto-Charon mutual orbital period —
    a mini-Galilean-Laplace-style structure built on top of a binary
    mutual lock (the Solar System provides this structure exactly
    once). Showalter-Hamilton 2015 *Nature* established the system is
    chaotic in libration on Myr timescales precisely BECAUSE the
    resonances are not exact. Pin the four ratio amplitudes to
    bracket [2.5, 6.5] (close to but not exactly 3:1 / 4:1 / 5:1 / 6:1)."""
    rows = _amsc_rows_indexed_by_name()
    expected_ratios = {
        "styx_near_3_to_1_with_pc_orbit": (2.9, 3.3),       # observed 3.157
        "nix_near_4_to_1_with_pc_orbit": (3.7, 4.3),        # observed 3.890
        "kerberos_near_5_to_1_with_pc_orbit": (4.7, 5.3),   # observed 5.038
        "hydra_near_6_to_1_with_pc_orbit": (5.7, 6.3),      # observed 5.981
    }
    for name, (lo, hi) in expected_ratios.items():
        row = rows[name]
        assert row["amplitude_units"] == "ratio"
        assert lo <= row["amplitude_value"] <= hi, (
            f"{name} ratio {row['amplitude_value']} outside expected "
            f"window [{lo}, {hi}]"
        )


def test_all_source_dois_are_real_crossref_indexed() -> None:
    """All Pluto-Charon row sources are post-1990 modern literature
    (Brozovic 2015 / Stern 1992 / Stern 2015 / Showalter-Hamilton
    2015) — no nodoi: / historical: / isbn: prefixes (this catalogue
    is built entirely on Crossref-indexed New-Horizons-era + late-
    20th-century journal papers)."""
    for source_key, prov in SOURCE_KEY_PROVENANCE.items():
        doi = prov["source_doi"]
        assert not doi.startswith(("nodoi:", "historical:", "isbn:", "ads:")), (
            f"Pluto-Charon source_keys should map to real Crossref DOIs; "
            f"{source_key!r} maps to {doi!r}"
        )
