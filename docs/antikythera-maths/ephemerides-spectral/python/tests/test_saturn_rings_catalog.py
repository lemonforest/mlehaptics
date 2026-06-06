"""v0.30.0 — Sol Saturn Ring System Catalog tests.

Pins the temporal-spectrum catalogue of a **multi-regime body** — the
staged dual-author ring data (12 ``RingFeature`` rows) promoted to a
full query surface:

* the four-regime partition (the v0.24.x dynamical regimes met
  separately, now spanning one body's rings);
* THE closure invariant — the integer ``(p:q)`` mean-motion
  commensurabilities predict the observed ring boundaries from the
  perturbing moons' semi-major axes to ``< 1 %``, with the sub-percent
  residual bounded by the leading Saturn-J₂ oblateness correction;
* the bounded-local-Laplacian eigenbasis on the radial feature graph
  (the v0.24.5 Hawaii machinery on ring radii).

The dual-author parity (hand-coded ``_data.py`` ↔ AMSC NDJSON) is the
separate ``test_saturn_rings_dual_author`` ratchet; this file pins the
catalogue query surface + the physics invariants.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.saturn_rings_catalog import (
    MOON_SEMI_MAJOR_AXIS_KM,
    SATURN_J2,
    SATURN_REFERENCE_RADIUS_KM,
    get_ring_radial_laplacian,
    get_ring_resonance_closure,
    get_saturn_ring_features,
    list_saturn_ring_features,
)
from ephemerides_spectral._research.saturn_rings_data import (
    SATURN_RING_FEATURES,
    SOURCES,
)


_REGIME_LABELS = {
    "rigid_body_action_angle_stable",
    "rigid_body_action_angle_mutual_lock",
    "temporal_quasi_periodic_cycle",
    "bounded_local_laplacian_family",
}


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_feature_count_12() -> None:
    """12 catalogued ring features (the staged dual-author roster)."""
    assert len(SATURN_RING_FEATURES) == 12


def test_sources_count_6() -> None:
    """6 sources after the v0.30.0 JPL-SSD moon-elements addition."""
    assert len(SOURCES) == 6


def test_jpl_ssd_source_present() -> None:
    """The moon semi-major axes used by the closure invariant resolve
    to the JPL SSD satellite-elements citation."""
    assert "jpl_ssd_sat_elements" in SOURCES


def test_feature_types_known() -> None:
    known = {
        "ring_boundary", "ring_gap", "resonance_anchor",
        "shepherd_moon", "ring_edge_structure",
    }
    for f in SATURN_RING_FEATURES:
        assert f.feature_type in known


# ──────────────────────────────────────────────────────────────────────
# Multi-regime partition
# ──────────────────────────────────────────────────────────────────────


def test_four_regimes() -> None:
    """The catalogue's headline: four dynamical regimes span the rings."""
    r = get_saturn_ring_features()
    assert r["n_regimes"] == 4
    assert set(r["regimes"]) == _REGIME_LABELS


def test_regime_partition_counts() -> None:
    """Each regime's membership count (a ratchet on the staged data)."""
    r = get_saturn_ring_features()
    counts = {label: len(members) for label, members in r["regimes"].items()}
    assert counts == {
        "rigid_body_action_angle_stable": 6,
        "rigid_body_action_angle_mutual_lock": 1,
        "temporal_quasi_periodic_cycle": 3,
        "bounded_local_laplacian_family": 2,
    }


def test_regime_partition_covers_every_feature() -> None:
    """Every feature lands in exactly one regime; the partition is a
    cover of the roster."""
    r = get_saturn_ring_features()
    partitioned = sum(len(m) for m in r["regimes"].values())
    assert partitioned == len(SATURN_RING_FEATURES)
    all_named = {name for members in r["regimes"].values() for name in members}
    assert all_named == {f.name for f in SATURN_RING_FEATURES}


# ──────────────────────────────────────────────────────────────────────
# Saturn oblateness constants (reused from the Geodetic Catalog)
# ──────────────────────────────────────────────────────────────────────


def test_saturn_j2_matches_geodetic() -> None:
    """J₂ reused from the in-repo Geodetic Catalog (Cassini-Iess-2019)."""
    assert SATURN_J2 == pytest.approx(1.6290573e-2, rel=1e-6)


def test_saturn_reference_radius() -> None:
    assert SATURN_REFERENCE_RADIUS_KM == pytest.approx(60330.0, abs=1.0)


def test_moon_axes_present() -> None:
    for moon in ("mimas", "janus", "epimetheus"):
        assert MOON_SEMI_MAJOR_AXIS_KM[moon] > 0


# ──────────────────────────────────────────────────────────────────────
# THE closure invariant: (p:q) mean-motion resonance
# ──────────────────────────────────────────────────────────────────────


def test_resonance_closure_two_boundaries() -> None:
    """Two ring boundaries are held by integer (p:q) resonances:
    Cassini Division inner edge (2:1 Mimas) and the A-ring outer edge
    (7:6 Janus-Epimetheus)."""
    r = get_ring_resonance_closure()
    assert r["n_resonances"] == 2


def test_resonance_closure_within_1pct() -> None:
    """THE headline: integer commensurabilities predict the observed
    ring boundaries to < 1%."""
    r = get_ring_resonance_closure()
    assert r["max_residual_pct"] < 1.0


def test_resonance_residual_bounded_by_j2_scale() -> None:
    """Every resonant boundary's residual is bounded by the leading
    Saturn-J₂ epicyclic-frequency correction (3/2) J₂ (R/a)² at its
    radius — the residual IS the oblateness signature, not a failure of
    the resonance model."""
    r = get_ring_resonance_closure()
    for row in r["resonances"]:
        assert row["residual_within_j2_scale"] is True, (
            f"{row['name']}: residual {row['residual_pct']:.4f}% "
            f"exceeds J2 scale {row['j2_frequency_correction_pct']:.4f}%"
        )


def test_resonance_predicted_interior_to_observed() -> None:
    """Each catalogued resonance is an *inner* Lindblad resonance — the
    naïve-Kepler prediction sits interior to (below) the observed
    boundary; Saturn's oblateness shifts it outward."""
    r = get_ring_resonance_closure()
    for row in r["resonances"]:
        assert row["predicted_radius_km"] < row["observed_radius_km"]


def test_resonance_anchor_cross_check() -> None:
    """The Mimas 2:1 resonance-anchor row stores a literature predicted
    location; the catalogue's fresh (q/p)^(2/3) computation agrees with
    it to < 0.1%."""
    r = get_ring_resonance_closure()
    cc = r["anchor_cross_check"]
    assert cc["resonance"] == "2:1"
    assert cc["difference_pct"] < 0.1


# ──────────────────────────────────────────────────────────────────────
# Bounded-local-Laplacian eigenbasis on the radial feature graph
# ──────────────────────────────────────────────────────────────────────


def test_radial_laplacian_fiedler_positive() -> None:
    """Connected proximity graph → positive Fiedler eigenvalue."""
    r = get_ring_radial_laplacian()
    assert r["fiedler_eigenvalue"] > 0.0


def test_radial_laplacian_single_sign_change() -> None:
    """Quasi-1D radial chain → the Fiedler vector has a single sign
    change along the radial ordering (one clean bisection)."""
    r = get_ring_radial_laplacian()
    assert r["n_sign_changes"] == 1


def test_radial_laplacian_inner_cluster() -> None:
    """The Fiedler vector splits off the two innermost features (the
    C-ring outer / B-ring inner boundaries at ~92 000 km) from the
    Cassini Division and everything outward."""
    r = get_ring_radial_laplacian()
    assert set(r["fiedler_partition"]["inner"]) == {
        "C-ring outer edge", "B-ring inner edge",
    }


def test_radial_laplacian_largest_gap() -> None:
    """The bisection seam is the largest radial gap — the ~25 000 km
    void between the B-ring inner edge and the Cassini-region features."""
    r = get_ring_radial_laplacian()
    gap = r["largest_radial_gap"]
    assert gap["gap_km"] > 20000.0
    assert "B-ring inner edge" in gap["between"]


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_saturn_ring_features_smoke() -> None:
    r = get_saturn_ring_features()
    assert r["ok"] is True
    assert r["body"] == "saturn"
    assert r["n_features"] == 12


def test_get_ring_resonance_closure_smoke() -> None:
    r = get_ring_resonance_closure()
    assert r["ok"] is True
    assert r["max_residual_pct"] < 1.0


def test_list_saturn_ring_features_smoke() -> None:
    r = list_saturn_ring_features()
    assert r["ok"] is True
    assert r["n_features"] == 12
    assert r["n_sources"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_saturn_ring_features() -> None:
    r = bridge.get_saturn_ring_features()
    assert r["ok"] is True
    assert r["n_regimes"] == 4


def test_bridge_get_ring_resonance_closure() -> None:
    r = bridge.get_ring_resonance_closure()
    assert r["ok"] is True
    assert r["n_resonances"] == 2


def test_bridge_get_ring_radial_laplacian() -> None:
    r = bridge.get_ring_radial_laplacian()
    assert r["ok"] is True
    assert r["n_sign_changes"] == 1


def test_bridge_list_saturn_ring_features() -> None:
    r = bridge.list_saturn_ring_features()
    assert r["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def _cli_json(argv):
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(argv)
    assert rc == 0
    return _json.loads(buf.getvalue())


def test_cli_saturn_ring_features_smoke() -> None:
    payload = _cli_json(["saturn-ring-features"])
    assert payload["body"] == "saturn"
    assert payload["n_features"] == 12


def test_cli_ring_resonance_closure_smoke() -> None:
    payload = _cli_json(["ring-resonance-closure"])
    assert payload["max_residual_pct"] < 1.0


def test_cli_ring_radial_laplacian_smoke() -> None:
    payload = _cli_json(["ring-radial-laplacian"])
    assert payload["n_sign_changes"] == 1


def test_cli_saturn_ring_features_full_smoke() -> None:
    payload = _cli_json(["saturn-ring-features-full"])
    assert payload["n_sources"] == 6


def test_cli_saturn_ring_help() -> None:
    """All v0.30.0 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("saturn-ring-features",
                "ring-resonance-closure",
                "ring-radial-laplacian",
                "saturn-ring-features-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
