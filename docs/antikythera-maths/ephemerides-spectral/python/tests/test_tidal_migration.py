"""v0.21.6 — Sol Tidal Migration Catalog tests.

Pins the sixth cross-channel coupling surface:

* 6-pair roster (terra-luna, mars-phobos, jupiter-io, saturn-titan,
  neptune-triton, pluto-charon).
* Headline numerics: terra-luna 3.83 cm/yr outward (LLR canonical);
  saturn-titan 11 cm/yr outward (Lainey 2020 — 100× older estimates,
  the headline); mars-phobos -1.9 cm/yr inward (~50 Myr deadline);
  pluto-charon 0 cm/yr (dual-synchronous binary; unique).
* Direction-sign invariants verified.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.tidal_migration_catalog import (
    compute_tidal_migration,
    list_tidal_migrations,
)
from ephemerides_spectral._research.tidal_migration_data import (
    DIR_INWARD,
    DIR_LOCKED,
    DIR_OUTWARD,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    TIDAL_MIGRATIONS,
    TidalMigration,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_6() -> None:
    assert len(TIDAL_MIGRATIONS) == 6


def test_canonical_roster_members() -> None:
    pairs = {m.pair_name for m in TIDAL_MIGRATIONS}
    expected = {"terra-luna", "mars-phobos", "jupiter-io",
                "saturn-titan", "neptune-triton", "pluto-charon"}
    assert pairs == expected


def test_sources_count() -> None:
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_terra_luna_canonical_rate_pinned() -> None:
    """Williams 2014/2025 LLR: Moon outward at 3.83 cm/yr — the most
    precisely measured tidal-migration rate in the solar system."""
    by = {m.pair_name: m for m in TIDAL_MIGRATIONS}
    pair = by["terra-luna"]
    assert pair.migration_rate_cm_per_year == pytest.approx(3.83, abs=0.1)
    assert pair.migration_direction == DIR_OUTWARD
    assert pair.precision_flag == PRECISION_HIGH


def test_saturn_titan_lainey_2020_headline() -> None:
    """Lainey 2020: Titan outward at 11 cm/yr — 100× older equilibrium-
    tide predictions. Implies Saturn interior resonance locking."""
    by = {m.pair_name: m for m in TIDAL_MIGRATIONS}
    pair = by["saturn-titan"]
    assert pair.migration_rate_cm_per_year == pytest.approx(11.0, abs=2.0)
    assert pair.migration_direction == DIR_OUTWARD
    assert pair.is_resonance_locked is True
    assert "Saturn interior" in pair.additional_constraint or \
           "resonance locking" in pair.additional_constraint.lower()


def test_mars_phobos_inward_pinned() -> None:
    """Lainey 2007: Phobos inward at ~1.9 cm/yr; ~50 Myr Roche-limit
    crossing."""
    by = {m.pair_name: m for m in TIDAL_MIGRATIONS}
    pair = by["mars-phobos"]
    assert pair.migration_rate_cm_per_year < 0  # inward = negative
    assert abs(pair.migration_rate_cm_per_year) == pytest.approx(1.9, abs=0.5)
    assert pair.migration_direction == DIR_INWARD


def test_jupiter_io_galilean_resonance() -> None:
    """Lainey 2009: Galilean Laplace 1:2:4 currently EXPANDING
    (not contracting as classical theory assumed)."""
    by = {m.pair_name: m for m in TIDAL_MIGRATIONS}
    pair = by["jupiter-io"]
    assert pair.migration_direction == DIR_OUTWARD
    assert pair.is_resonance_locked is True
    assert "Laplace" in pair.additional_constraint


def test_pluto_charon_dual_lock() -> None:
    """The unique solar-system case: BOTH bodies tidally locked to
    each other. Migration rate = 0; direction = LOCKED."""
    by = {m.pair_name: m for m in TIDAL_MIGRATIONS}
    pair = by["pluto-charon"]
    assert pair.migration_rate_cm_per_year == 0.0
    assert pair.migration_direction == DIR_LOCKED
    assert "dual" in pair.additional_constraint.lower() or \
           "lock" in pair.additional_constraint.lower()


def test_neptune_triton_retrograde_inward() -> None:
    """Triton retrograde captured satellite → inward migration."""
    by = {m.pair_name: m for m in TIDAL_MIGRATIONS}
    pair = by["neptune-triton"]
    assert pair.migration_direction == DIR_INWARD
    assert pair.migration_rate_cm_per_year < 0


# ──────────────────────────────────────────────────────────────────────
# Direction-sign invariants
# ──────────────────────────────────────────────────────────────────────

def test_outward_is_positive_inward_is_negative_locked_is_zero() -> None:
    """Sign convention: outward → positive, inward → negative,
    locked → zero."""
    for m in TIDAL_MIGRATIONS:
        if m.migration_direction == DIR_OUTWARD:
            assert m.migration_rate_cm_per_year > 0
        elif m.migration_direction == DIR_INWARD:
            assert m.migration_rate_cm_per_year < 0
        elif m.migration_direction == DIR_LOCKED:
            assert m.migration_rate_cm_per_year == 0
        else:
            pytest.fail(f"unknown direction {m.migration_direction}")


def test_resonance_locked_pairs() -> None:
    """jupiter-io (Laplace) + saturn-titan (Saturn interior modes)
    are the only resonance-locked pairs in v0.21.6."""
    locked = {m.pair_name for m in TIDAL_MIGRATIONS if m.is_resonance_locked}
    assert locked == {"jupiter-io", "saturn-titan"}


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in TIDAL_MIGRATIONS:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in TIDAL_MIGRATIONS}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_pair() -> None:
    r = compute_tidal_migration(pair="krypton-zod")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_tidal_migration()
    assert r["ok"] is True
    assert r["n_pairs"] == 6


def test_compute_per_pair_saturn_titan() -> None:
    r = compute_tidal_migration(pair="saturn-titan")
    assert r["ok"] is True
    assert r["migration"]["migration_rate_cm_per_year"] == pytest.approx(11.0, abs=2.0)


def test_list_tidal_migrations_smoke() -> None:
    r = list_tidal_migrations()
    assert r["ok"] is True
    assert r["n_pairs"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_tidal_migration_smoke() -> None:
    r = bridge.get_tidal_migration(pair="terra-luna")
    assert r["ok"] is True
    assert r["migration"]["migration_rate_cm_per_year"] == pytest.approx(3.83, abs=0.1)


def test_bridge_get_tidal_migration_full_roster() -> None:
    r = bridge.get_tidal_migration()
    assert r["ok"] is True
    assert r["n_pairs"] == 6


def test_bridge_list_tidal_migrations_smoke() -> None:
    r = bridge.list_tidal_migrations()
    assert r["ok"] is True


def test_bridge_get_tidal_migration_rejects_unknown() -> None:
    r = bridge.get_tidal_migration(pair="krypton-zod")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_tidal_migration_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["tidal-migration", "--pair", "saturn-titan"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["migration"]["migration_rate_cm_per_year"] == pytest.approx(11.0, abs=2.0)


def test_cli_tidal_migrations_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["tidal-migrations"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_pairs"] == 6


def test_cli_tidal_help() -> None:
    """Both v0.21.6 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("tidal-migration", "tidal-migrations"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
