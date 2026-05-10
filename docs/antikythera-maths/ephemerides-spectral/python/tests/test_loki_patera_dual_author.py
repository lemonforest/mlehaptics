"""Sol Loki Patera Eruption Cycle dual-author diff test —
v0.27.0 phase A.

12-row roster across 2 row types (6 cycle_peak + 6 cycle_mode).
Mirrors prior phase A multi-row-type patterns (axial_seamount).
Headline physics ratchets pin the v0.24.12 ship: the canonical
~540-day mean cycle period (Rathbun 2002), the Galilean Laplace
4:2:1 mean-motion commensurability between Io / Europa / Ganymede
that drives Io's tidal heating, and the Rathbun-2002-anchored
cycle-index discipline.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ephemerides_spectral import bridge

from _loki_patera_amsc_helpers import (
    ENTERED_LOCALLY_AT,
    SOURCE_KEY_PROVENANCE,
    hand_coded_rows_in_amsc_shape,
)


def _amsc_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    result = bridge.get_attested_dataset("loki_patera")
    assert result["ok"] is True, f"AMSC load failed: {result}"
    out: Dict[str, Dict[str, Any]] = {}
    for row in result["rows"]:
        data = row["data"]
        out[data["name"]] = data
    return out


def _hand_coded_rows_indexed_by_name() -> Dict[str, Dict[str, Any]]:
    return {d["name"]: d for d in hand_coded_rows_in_amsc_shape()}


def test_amsc_dataset_loads() -> None:
    result = bridge.get_attested_dataset("loki_patera")
    assert result["ok"] is True
    assert len(result["rows"]) == 12, (
        f"expected 12 rows; got {len(result['rows'])}"
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
    from ephemerides_spectral._research.loki_patera_data import (
        LOKI_CYCLE_MODES,
        LOKI_CYCLE_PEAKS,
    )
    referenced = (
        {p.source_key for p in LOKI_CYCLE_PEAKS}
        | {m.source_key for m in LOKI_CYCLE_MODES}
    )
    missing = referenced - set(SOURCE_KEY_PROVENANCE)
    assert not missing


def test_provenance_entries_have_required_fields() -> None:
    import re
    iso_pattern = re.compile(r"^[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?$")
    for key, entry in SOURCE_KEY_PROVENANCE.items():
        assert isinstance(entry["source_doi"], str)
        assert len(entry["source_doi"]) >= 5
        assert iso_pattern.match(entry["source_published_date"])


def test_row_type_distribution() -> None:
    """The 12 rows split as: 6 cycle_peak (1990 / 1995 / 1997 / 2002 /
    2013 / 2015 — Veeder 1994 KAO through de Kleer 2019 adaptive-
    optics era) + 6 cycle_mode (loki_main_cycle + brightening_phase +
    resurfacing_wave + cooling_phase + io_orbital_period +
    galilean_laplace_4_2_1)."""
    rows = _amsc_rows_indexed_by_name()
    by_type: Dict[str, int] = {}
    for row in rows.values():
        by_type[row["row_type"]] = by_type.get(row["row_type"], 0) + 1
    assert by_type == {
        "cycle_peak": 6,
        "cycle_mode": 6,
    }, f"unexpected row_type distribution: {by_type}"


def test_main_cycle_period_is_540_days() -> None:
    """Headline physics ratchet: the Loki Patera main brightening
    cycle period is 540 days — the canonical Rathbun 2002 *GRL*
    quasi-periodic value derived from 12 years of multi-band ground-
    based + Galileo-era thermal observations. Quasi-periodic, not
    strictly periodic; observed range 480-580 d. The 540-day mean is
    the catalog headline value justifying the v0.24.12 ship's
    placement in the temporal_quasi_periodic_cycle regime (alongside
    v0.24.8 Axial Seamount)."""
    rows = _amsc_rows_indexed_by_name()
    main_cycle = rows["loki_main_cycle"]
    assert main_cycle["row_type"] == "cycle_mode"
    assert main_cycle["mode_class"] == "cycle"
    assert main_cycle["period_days"] == 540.0, (
        f"main cycle period should be 540.0 d (Rathbun 2002 mean); "
        f"got {main_cycle['period_days']}"
    )
    assert main_cycle["precision_flag"] == "high"


def test_galilean_laplace_4_2_1_commensurability_arithmetic() -> None:
    """Headline cross-channel ratchet: Loki's existence depends on the
    Galilean Laplace 4:2:1 mean-motion near-resonance between Io /
    Europa / Ganymede that forces Io's orbital eccentricity to ~0.0041
    (driving the ~10^14 W tidal-heating budget). Pin the textbook
    arithmetic:

        4 * P_Io  ≈  2 * P_Europa  ≈  P_Ganymede

    with P_Io = 1.7691378 d, P_Europa = 3.5511810 d, P_Ganymede =
    7.1545530 d. The exact integer-ratio commensurability is broken
    by ~26 / 52 / 78 ms (~1% of period), small enough that the
    resonance is dynamically locked but large enough to drive forced
    eccentricity. The exact Laplace relation
    n_Io − 3·n_Europa + 2·n_Ganymede = 0 holds to much higher
    precision; 4:2:1 is the period-ratio approximation. This is the
    Peale-Cassen-Reynolds 1979 prediction that Voyager 1 confirmed
    2 weeks later by observing active volcanism on Io."""
    from ephemerides_spectral._research.loki_patera_data import (
        EUROPA_ORBITAL_PERIOD_DAYS,
        GANYMEDE_ORBITAL_PERIOD_DAYS,
        IO_ORBITAL_PERIOD_DAYS,
    )
    rows = _amsc_rows_indexed_by_name()
    laplace_row = rows["galilean_laplace_4_2_1_commensurability"]
    assert laplace_row["row_type"] == "cycle_mode"
    assert laplace_row["mode_class"] == "commensurability"
    # The 4:2:1 period-ratio approximation holds to ~1% (NOT exact;
    # the lock breaks the 4:2:1 by ~26 / 52 / 78 ms across the three
    # body-pairs, small enough to lock dynamically but large enough
    # to drive forced eccentricity). Pin a 0.1 d tolerance which is
    # ~1.4% of P_Ganymede.
    pair_io_europa = abs(4 * IO_ORBITAL_PERIOD_DAYS - 2 * EUROPA_ORBITAL_PERIOD_DAYS)
    pair_europa_ganymede = abs(2 * EUROPA_ORBITAL_PERIOD_DAYS - GANYMEDE_ORBITAL_PERIOD_DAYS)
    pair_io_ganymede = abs(4 * IO_ORBITAL_PERIOD_DAYS - GANYMEDE_ORBITAL_PERIOD_DAYS)
    assert pair_io_europa < 0.1, (
        f"|4*P_Io - 2*P_Europa| = {pair_io_europa:.4f} d should be < 0.1 d"
    )
    assert pair_europa_ganymede < 0.1, (
        f"|2*P_Europa - P_Ganymede| = {pair_europa_ganymede:.4f} d should be < 0.1 d"
    )
    assert pair_io_ganymede < 0.1, (
        f"|4*P_Io - P_Ganymede| = {pair_io_ganymede:.4f} d should be < 0.1 d"
    )
    # The commensurability mode's period_days carries Io's orbital
    # period (the fundamental of the resonance).
    assert laplace_row["period_days"] == IO_ORBITAL_PERIOD_DAYS


def test_cycle_peaks_chronologically_ordered() -> None:
    """Sanity ratchet: the 6 cycle peaks are chronologically ordered —
    1990 → 1995 → 1997 → 2002 → 2013 → 2015. Pin the chronology that
    spans the Rathbun 2002 anchor cycle (index 0) plus seven intervening
    cycles to the de Kleer 2017+ adaptive-optics era."""
    rows = _amsc_rows_indexed_by_name()
    peaks = sorted(
        ((row["peak_year"], name) for name, row in rows.items()
         if row["row_type"] == "cycle_peak")
    )
    assert [year for year, _ in peaks] == [
        1990, 1995, 1997, 2002, 2013, 2015,
    ], f"unexpected peak chronology: {peaks}"


def test_rathbun_2002_is_anchor_cycle() -> None:
    """The Rathbun 2002 paper (canonical ~540-day periodicity) is the
    catalogue's anchor cycle (cycle_index_from_anchor = 0). Pre-anchor
    1990s peaks have null cycle_index; post-anchor peaks (2013 / 2015)
    carry positive integer indices."""
    rows = _amsc_rows_indexed_by_name()
    anchor_peak = rows["loki_peak_2002"]
    assert anchor_peak["cycle_index_from_anchor"] == 0, (
        f"2002 peak should be anchor (index 0); "
        f"got {anchor_peak['cycle_index_from_anchor']}"
    )
    # 1990s peaks carry null cycle_index_from_anchor (pre-anchor).
    assert rows["loki_peak_1990"]["cycle_index_from_anchor"] is None
    assert rows["loki_peak_1995"]["cycle_index_from_anchor"] is None
    assert rows["loki_peak_1997"]["cycle_index_from_anchor"] is None
    # AO-era peaks have positive indices.
    assert rows["loki_peak_2013"]["cycle_index_from_anchor"] == 7
    assert rows["loki_peak_2015"]["cycle_index_from_anchor"] == 8


def test_three_subcycle_phase_modes_cover_full_cycle() -> None:
    """The three sub-cycle phase modes (brightening + resurfacing wave
    + cooling) document the full ~540-day cycle structure: a multi-
    week heat-up, a multi-month resurfacing wave at ~1 km/day across
    the ~200-km-diameter caldera, and a multi-month cooling decay.
    Pin the mode_class='phase' classification + the de Kleer 2017 /
    de Kleer 2019 source attribution."""
    rows = _amsc_rows_indexed_by_name()
    expected_phase_modes = {
        "brightening_phase",
        "resurfacing_wave",
        "cooling_phase",
    }
    for name in expected_phase_modes:
        row = rows[name]
        assert row["row_type"] == "cycle_mode"
        assert row["mode_class"] == "phase", (
            f"{name} should be phase-class; got {row['mode_class']}"
        )
        assert row["period_days"] is not None and row["period_days"] > 0


def test_isbn_prefix_only_for_textbook() -> None:
    """The `isbn:` prefix appears exactly once in this catalogue —
    Murray-Dermott 1999 *Solar System Dynamics* (the canonical
    Galilean-Laplace 4:2:1 reference). All other source DOIs are real
    Crossref-indexed papers (Veeder 1994 / Rathbun 2002 / de Kleer
    2017 / de Kleer 2019 *Nature* / Peale-Cassen-Reynolds 1979)."""
    isbn_keys = [
        key for key, prov in SOURCE_KEY_PROVENANCE.items()
        if prov["source_doi"].startswith("isbn:")
    ]
    assert isbn_keys == ["murray_dermott_1999"], (
        f"isbn: prefix should be Murray-Dermott only; got {isbn_keys}"
    )
    # And confirm no nodoi: / historical: prefixes are present.
    for key, prov in SOURCE_KEY_PROVENANCE.items():
        doi = prov["source_doi"]
        assert not doi.startswith(("nodoi:", "historical:", "ads:")), (
            f"unexpected non-Crossref prefix in {key!r}: {doi!r}"
        )
