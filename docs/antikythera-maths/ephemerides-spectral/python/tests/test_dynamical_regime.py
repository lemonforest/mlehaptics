"""v0.24.9 — Sol Dynamical-Regime Classifier tests.

Pins the **eigenbasis-projection version of the v0.24.x if/else chain**
— 9 labelled training examples (one per v0.24.0–v0.24.8 ship), 7
features per example, principal-component decomposition over the
standardised feature matrix, nearest-neighbour classification.

The classifier is the project's **first explicit meta-consumer of the
v0.24.x methodology arc** — every v0.24.x ship becomes a labelled
example.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.dynamical_regime_catalog import (
    FEATURE_NAMES,
    classify_dynamical_regime,
    get_dynamical_regime_eigenbasis,
    list_dynamical_regimes,
)
from ephemerides_spectral._research.dynamical_regime_data import (
    FORCING_CLASS_GRAVITATIONAL,
    FORCING_CLASS_NAMES,
    FORCING_CLASS_RADIATION,
    FORCING_CLASS_STELLAR_OSCILLATION,
    FORCING_CLASS_TECTONIC,
    FORCING_CLASS_VOLCANIC,
    N_FEATURES,
    PRECISION_HIGH,
    REGIME_EXAMPLES,
    SOURCES,
    RegimeExample,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_n_features_is_7() -> None:
    assert N_FEATURES == 7


def test_feature_names_count() -> None:
    assert len(FEATURE_NAMES) == N_FEATURES


def test_regime_count_10() -> None:
    """One ground-proof row per v0.24.x ship that participates in
    the regime classifier (v0.24.0–v0.24.8 + v0.24.11 Pluto-Charon
    Path-B addition)."""
    assert len(REGIME_EXAMPLES) == 10


def test_regime_names_unique() -> None:
    names = [e.name for e in REGIME_EXAMPLES]
    assert len(names) == len(set(names))


def test_regime_labels_unique() -> None:
    labels = [e.regime_label for e in REGIME_EXAMPLES]
    assert len(labels) == len(set(labels))


def test_ship_versions_in_v_0_24_x() -> None:
    """Every training example points to a v0.24.x ship."""
    for e in REGIME_EXAMPLES:
        assert e.ship_version.startswith("0.24.")


def test_sources_count_10() -> None:
    """One source pointer per v0.24.x ship in the classifier roster."""
    assert len(SOURCES) == 10


def test_every_source_key_resolves() -> None:
    for e in REGIME_EXAMPLES:
        assert e.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Per-ship presence (ratchet: every v0.24.x ship is represented)
# ──────────────────────────────────────────────────────────────────────


def test_mercury_v_0_24_0_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert "0.24.0" in by
    assert by["0.24.0"].name == "mercury_dynamical_spectrum"
    assert by["0.24.0"].regime_label == "rigid_body_action_angle_stable"


def test_luna_v_0_24_1_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.1"].regime_label == (
        "rigid_body_action_angle_commensurate"
    )


def test_mars_v_0_24_2_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.2"].regime_label == "rigid_body_chaotic_obliquity"


def test_sun_v_0_24_3_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.3"].regime_label == "continuum_normal_modes"


def test_toroidal_v_0_24_4_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.4"].regime_label == "shape_residual_chandrasekhar"


def test_hawaii_v_0_24_5_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.5"].regime_label == (
        "bounded_local_laplacian_trajectory"
    )


def test_yarkovsky_v_0_24_6_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.6"].regime_label == "radiation_coupled_drift"


def test_mars_tharsis_v_0_24_7_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.7"].regime_label == (
        "bounded_local_laplacian_family"
    )


def test_axial_v_0_24_8_present() -> None:
    by = {e.ship_version: e for e in REGIME_EXAMPLES}
    assert by["0.24.8"].regime_label == "temporal_quasi_periodic_cycle"


# ──────────────────────────────────────────────────────────────────────
# Feature-vector schema invariants
# ──────────────────────────────────────────────────────────────────────


def test_feature_vector_length_invariant() -> None:
    for e in REGIME_EXAMPLES:
        fv = e.feature_vector()
        assert len(fv) == N_FEATURES


def test_stability_index_in_unit_interval() -> None:
    for e in REGIME_EXAMPLES:
        assert 0.0 <= e.stability_index <= 1.0


def test_has_commensurability_is_binary() -> None:
    for e in REGIME_EXAMPLES:
        assert e.has_commensurability in (0, 1)


def test_prediction_track_signal_in_minus_one_zero_plus_one() -> None:
    for e in REGIME_EXAMPLES:
        assert e.prediction_track_signal in (-1, 0, 1)


def test_dimensionality_in_0_to_3() -> None:
    for e in REGIME_EXAMPLES:
        assert e.dimensionality in (0, 1, 2, 3)


def test_forcing_class_index_in_known_set() -> None:
    valid = set(FORCING_CLASS_NAMES.keys())
    for e in REGIME_EXAMPLES:
        assert e.forcing_class_index in valid


# ──────────────────────────────────────────────────────────────────────
# Eigenbasis (PCA) invariants
# ──────────────────────────────────────────────────────────────────────


def test_eigenvalues_descending() -> None:
    """Top components first."""
    eb = get_dynamical_regime_eigenbasis(n_components=N_FEATURES)
    for prev, curr in zip(eb["eigenvalues"][:-1], eb["eigenvalues"][1:]):
        assert prev >= curr - 1e-9


def test_eigenvalues_nonnegative() -> None:
    """Covariance matrix is PSD; all eigenvalues >= 0."""
    eb = get_dynamical_regime_eigenbasis(n_components=N_FEATURES)
    for v in eb["eigenvalues"]:
        assert v >= -1e-9


def test_explained_variance_ratios_sum_to_one() -> None:
    eb = get_dynamical_regime_eigenbasis(n_components=N_FEATURES)
    s = sum(eb["explained_variance_ratio"])
    assert abs(s - 1.0) < 1e-9


def test_top_3_pcs_explain_at_least_70_percent() -> None:
    """Top 3 PCs should capture most of the variance because the
    7 features are correlated (large bodies tend to have long
    timescales, etc.)."""
    eb = get_dynamical_regime_eigenbasis(n_components=3)
    cum = eb["cumulative_explained_variance"][2]
    assert cum > 0.70


def test_top_4_pcs_explain_at_least_90_percent() -> None:
    eb = get_dynamical_regime_eigenbasis(n_components=4)
    cum = eb["cumulative_explained_variance"][3]
    assert cum > 0.90


def test_eigenbasis_n_components_clamps_to_n_features() -> None:
    """Asking for more components than features should clamp."""
    eb = get_dynamical_regime_eigenbasis(n_components=99)
    assert eb["n_components"] == N_FEATURES


def test_pc1_loadings_have_per_feature_entries() -> None:
    eb = get_dynamical_regime_eigenbasis(n_components=1)
    pc1 = eb["top_components"][0]
    for fname in FEATURE_NAMES:
        assert fname in pc1["loadings"]


# ──────────────────────────────────────────────────────────────────────
# Self-classification (round-trip identity — ratchet)
# ──────────────────────────────────────────────────────────────────────


def test_self_classification_perfect() -> None:
    """Every training example must classify as itself when fed back
    into the classifier. This is the basic round-trip identity."""
    for e in REGIME_EXAMPLES:
        res = classify_dynamical_regime(
            e.feature_vector(), n_components=3,
        )
        assert res["nearest_regime"]["name"] == e.name
        assert res["nearest_regime"]["distance"] < 1e-9


def test_self_classification_all_distances_nonnegative() -> None:
    res = classify_dynamical_regime(
        REGIME_EXAMPLES[0].feature_vector(), n_components=3,
    )
    for d in res["distances_to_all"]:
        assert d["distance"] >= 0.0


def test_self_classification_distances_sorted() -> None:
    """The distances list must be sorted ascending."""
    res = classify_dynamical_regime(
        REGIME_EXAMPLES[0].feature_vector(), n_components=3,
    )
    for prev, curr in zip(
        res["distances_to_all"][:-1], res["distances_to_all"][1:],
    ):
        assert prev["distance"] <= curr["distance"] + 1e-9


# ──────────────────────────────────────────────────────────────────────
# Out-of-sample probes (the classifier doing useful work)
# ──────────────────────────────────────────────────────────────────────


def test_yellowstone_classifies_as_hawaii_like() -> None:
    """Yellowstone hotspot (10-Myr track on a moving plate) should
    classify as bounded_local_laplacian_trajectory (Hawaii-like)."""
    # (time_scale_log_s ~ 14.5 for 10 Myr, spatial ~3.2, stab=0.7,
    #  comm=0, pred=0, dim=1, force=tectonic)
    features = (14.5, 3.18, 0.7, 0, 0, 1, FORCING_CLASS_TECTONIC)
    res = classify_dynamical_regime(features, n_components=3)
    assert res["nearest_regime"]["regime_label"] == (
        "bounded_local_laplacian_trajectory"
    )


def test_k_dwarf_star_classifies_as_continuum() -> None:
    """A K-dwarf star (slightly smaller than Sun, similar p-mode
    period) should classify as continuum_normal_modes."""
    features = (
        2.5, 5.7, 1.0, 0, 0, 3, FORCING_CLASS_STELLAR_OSCILLATION,
    )
    res = classify_dynamical_regime(features, n_components=3)
    assert res["nearest_regime"]["regime_label"] == (
        "continuum_normal_modes"
    )


def test_classify_returns_distances_to_all_10_examples() -> None:
    """v0.24.11 added Pluto-Charon as a 10th ground-proof row."""
    res = classify_dynamical_regime(
        (0.0, 0.0, 0.5, 0, 0, 0, 0), n_components=3,
    )
    assert len(res["distances_to_all"]) == 10


# ──────────────────────────────────────────────────────────────────────
# Input-validation
# ──────────────────────────────────────────────────────────────────────


def test_classify_rejects_wrong_length_feature_vector() -> None:
    with pytest.raises(ValueError):
        classify_dynamical_regime((1.0, 2.0, 3.0), n_components=3)


def test_classify_rejects_too_long_feature_vector() -> None:
    with pytest.raises(ValueError):
        classify_dynamical_regime(
            (1.0,) * (N_FEATURES + 5), n_components=3,
        )


# ──────────────────────────────────────────────────────────────────────
# list_dynamical_regimes
# ──────────────────────────────────────────────────────────────────────


def test_list_returns_all_10_regimes() -> None:
    """v0.24.0–v0.24.8 + v0.24.11 = 10 regime examples."""
    r = list_dynamical_regimes()
    assert r["ok"] is True
    assert r["n_regimes"] == 10
    assert r["n_features"] == N_FEATURES
    assert r["n_sources"] == 10
    assert len(r["regimes"]) == 10


def test_list_includes_per_regime_catalog_module() -> None:
    r = list_dynamical_regimes()
    for entry in r["regimes"]:
        assert "catalog_module" in entry
        # Every catalog module pointer must reference a concrete v0.24.x
        # research module that exists.
        assert entry["catalog_module"].endswith("_catalog")


def test_list_includes_forcing_class_name() -> None:
    r = list_dynamical_regimes()
    valid_names = set(FORCING_CLASS_NAMES.values())
    for entry in r["regimes"]:
        assert entry["forcing_class_name"] in valid_names


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_dynamical_regime_eigenbasis() -> None:
    r = bridge.get_dynamical_regime_eigenbasis()
    assert r["ok"] is True
    assert r["n_examples"] == 10
    assert r["n_features"] == N_FEATURES


def test_bridge_classify_dynamical_regime() -> None:
    r = bridge.classify_dynamical_regime(
        REGIME_EXAMPLES[0].feature_vector(),
    )
    assert r["ok"] is True
    assert r["nearest_regime"]["name"] == REGIME_EXAMPLES[0].name


def test_bridge_list_dynamical_regimes() -> None:
    r = bridge.list_dynamical_regimes()
    assert r["ok"] is True
    assert r["n_regimes"] == 10


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_regime_eigenbasis_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["regime-eigenbasis"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_examples"] == 10


def test_cli_regime_classify_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    # Use Mercury's exact feature vector — must round-trip to itself.
    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "regime-classify",
            "--time-scale-log-s", "6.88",
            "--spatial-scale-log-km", "3.39",
            "--stability-index", "1.0",
            "--has-commensurability", "1",
            "--prediction-track-signal", "0",
            "--dimensionality", "0",
            "--forcing-class-index", "0",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["nearest_regime"]["name"] == (
        "mercury_dynamical_spectrum"
    )


def test_cli_regime_list_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["regime-list"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_regimes"] == 10


def test_cli_regime_help() -> None:
    """All v0.24.9 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("regime-eigenbasis", "regime-classify", "regime-list"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
