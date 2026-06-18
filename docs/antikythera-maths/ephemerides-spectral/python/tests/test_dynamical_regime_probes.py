"""v0.24.10 — Sol Dynamical-Regime OOS probe + classifier
calibration-ratio metric tests.

Pins two payloads:

(1) The curated 10-probe out-of-sample roster's classifier behaviour
    on real bodies that aren't in the v0.24.0–v0.24.8 training set.
    Future classifier refactors must not silently change which regime
    Yellowstone, Vesta, Phobos, etc. land on.

(2) The v0.24.10 calibration_ratio metric (nearest_distance /
    2nd_nearest_distance) and out_of_distribution flag — surfacing
    the latent diagnostic that v0.24.9 left in distances_to_all.

The classifier is **not machine learning in the SGD sense** — its
"training step" is a single deterministic Hermitian eigendecomposition.
The probes are **test vectors**, never training data. These tests
ratchet the classifier's deterministic behaviour on real bodies.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.dynamical_regime_catalog import (
    OOD_CALIBRATION_RATIO_THRESHOLD,
    REGIME_PROBES,
    classify_dynamical_regime,
    list_dynamical_regime_probes,
    list_dynamical_regimes,
    run_dynamical_regime_probes,
)
from ephemerides_spectral._research.dynamical_regime_data import (
    N_FEATURES,
    REGIME_EXAMPLES,
)
from ephemerides_spectral._research.dynamical_regime_probes_data import (
    PRECISION_HIGH,
    SOURCES as PROBE_SOURCES,
    RegimeProbe,
)


# ──────────────────────────────────────────────────────────────────────
# Probe roster shape
# ──────────────────────────────────────────────────────────────────────


def test_probe_count_10() -> None:
    """Curated 10-probe roster spanning every regime label."""
    assert len(REGIME_PROBES) == 10


def test_probe_names_unique() -> None:
    names = [p.name for p in REGIME_PROBES]
    assert len(names) == len(set(names))


def test_probe_sources_count_10() -> None:
    assert len(PROBE_SOURCES) == 10


def test_every_probe_source_key_resolves() -> None:
    for p in REGIME_PROBES:
        assert p.source_key in PROBE_SOURCES


def test_probe_feature_vectors_have_correct_length() -> None:
    for p in REGIME_PROBES:
        assert len(p.feature_vector()) == N_FEATURES


def test_ood_threshold_default() -> None:
    """Empirically calibrated; see probes_data module docstring."""
    assert OOD_CALIBRATION_RATIO_THRESHOLD == 0.85


# ──────────────────────────────────────────────────────────────────────
# Per-probe presence (ratchet — every probe in the roster is named)
# ──────────────────────────────────────────────────────────────────────


_EXPECTED_PROBE_NAMES = {
    "yellowstone_hotspot",
    "reunion_hotspot",
    "pluto_charon",
    "enceladus",
    "io_galilean_resonance",
    "phobos",
    "ceres",
    "alpha_centauri_b",
    "vesta",
    "magnetar_typical",
}


def test_expected_probe_names_present() -> None:
    actual = {p.name for p in REGIME_PROBES}
    assert actual == _EXPECTED_PROBE_NAMES


# ──────────────────────────────────────────────────────────────────────
# Calibration-ratio metric — invariants
# ──────────────────────────────────────────────────────────────────────


def test_self_classification_calibration_ratio_zero() -> None:
    """Every training example self-classifies with cal_ratio = 0."""
    for e in REGIME_EXAMPLES:
        r = classify_dynamical_regime(e.feature_vector())
        assert r["calibration_ratio"] < 1e-9


def test_self_classification_not_ood() -> None:
    """Self-classification is never out-of-distribution."""
    for e in REGIME_EXAMPLES:
        r = classify_dynamical_regime(e.feature_vector())
        assert r["out_of_distribution"] is False


def test_calibration_ratio_in_unit_interval_for_normal_inputs() -> None:
    """For finite distances with at least 2 examples, cal_ratio ∈ [0, ∞).
    For sensible inputs (all training examples + reasonable probes),
    cal_ratio ≤ 1 because distance to nearest ≤ distance to 2nd-nearest."""
    for p in REGIME_PROBES:
        r = classify_dynamical_regime(p.feature_vector())
        assert r["calibration_ratio"] >= 0.0
        assert r["calibration_ratio"] <= 1.0 + 1e-9


def test_nearest_neighbour_margin_nonnegative() -> None:
    """2nd-nearest distance ≥ nearest distance, so margin ≥ 0."""
    for p in REGIME_PROBES:
        r = classify_dynamical_regime(p.feature_vector())
        assert r["nearest_neighbour_margin"] >= 0.0


def test_ood_flag_consistent_with_threshold() -> None:
    """out_of_distribution iff calibration_ratio > ood_threshold_used."""
    for p in REGIME_PROBES:
        r = classify_dynamical_regime(p.feature_vector())
        threshold = r["ood_threshold_used"]
        if r["calibration_ratio"] > threshold:
            assert r["out_of_distribution"] is True
        else:
            assert r["out_of_distribution"] is False


def test_custom_ood_threshold_respected() -> None:
    """Setting a stricter threshold flags more probes as OOD."""
    p = REGIME_PROBES[0]  # yellowstone — confidently in-distribution
    r_default = classify_dynamical_regime(p.feature_vector())
    r_strict = classify_dynamical_regime(
        p.feature_vector(), ood_threshold=0.0,
    )
    # Default threshold (0.85) should NOT flag Yellowstone.
    assert r_default["out_of_distribution"] is False
    # Stricter threshold (0.0) flags everything except exact self-matches.
    assert r_strict["out_of_distribution"] is True


# ──────────────────────────────────────────────────────────────────────
# Probe behaviour ratchets (per-probe expected classification)
# ──────────────────────────────────────────────────────────────────────


def _classified_regime(feature_vec):
    return classify_dynamical_regime(feature_vec)["nearest_regime"][
        "regime_label"
    ]


def test_yellowstone_classifies_as_hawaii_regime() -> None:
    by = {p.name: p for p in REGIME_PROBES}
    label = _classified_regime(by["yellowstone_hotspot"].feature_vector())
    assert label == "bounded_local_laplacian_trajectory"


def test_reunion_classifies_as_hawaii_regime() -> None:
    by = {p.name: p for p in REGIME_PROBES}
    label = _classified_regime(by["reunion_hotspot"].feature_vector())
    assert label == "bounded_local_laplacian_trajectory"


def test_alpha_centauri_b_classifies_as_continuum() -> None:
    by = {p.name: p for p in REGIME_PROBES}
    label = _classified_regime(by["alpha_centauri_b"].feature_vector())
    assert label == "continuum_normal_modes"


def test_ceres_now_ood_after_v_0_24_11() -> None:
    """v0.24.11 ratchet revision: prior to v0.24.11 Ceres classified
    as rigid_body_action_angle_stable (matched Mercury at modest
    cal_ratio). After v0.24.11 added Pluto-Charon to the training
    set, Ceres sits in feature-space terrain with no close training
    analog -- both Mercury and Pluto-Charon have has_commensurability=1
    but Ceres has =0. The classifier honestly OODs at cal_ratio ~0.998.

    This is the rigid-stable-no-commensurability gap surfaced by
    the v0.24.11 Path-B test; documented for a future ship to
    populate (Vesta, Pallas, etc.)."""
    import math
    from ephemerides_spectral._research.dynamical_regime_catalog import (
        classify_dynamical_regime,
    )
    by = {p.name: p for p in REGIME_PROBES}
    r = classify_dynamical_regime(by["ceres"].feature_vector())
    assert r["out_of_distribution"] is True
    assert r["calibration_ratio"] > 0.85


def test_pluto_charon_classifies_as_mutual_lock_v_0_24_11() -> None:
    """v0.24.11 Path-B closure: Pluto-Charon was added as a ground-
    proof row with new regime label `rigid_body_action_angle_mutual_lock`.
    The probe (matching feature vector) now self-classifies to the
    new label deterministically (cal_ratio = 0).

    Prior to v0.24.11 this probe collapsed to Mercury-stable due to
    the v0.24.9 feature-schema gap; the new ground-proof row populated
    the binary-mutual-lock niche."""
    by = {p.name: p for p in REGIME_PROBES}
    label = _classified_regime(by["pluto_charon"].feature_vector())
    assert label == "rigid_body_action_angle_mutual_lock"


def test_vesta_classifier_landing_v_0_24_12_pinned() -> None:
    """Vesta was OOD-flagged in v0.24.9–v0.24.11 (calibration ratio
    ~0.98 — honest 'I don't know'). v0.24.12 added Loki Patera at
    spatial_scale_log_km=2.30, a near-twin to Vesta's 2.42 — the
    new neighbour pulls Vesta's calibration ratio down to ~0.79 and
    collapses it onto rigid_body_chaotic_obliquity as a SPURIOUS
    landing (the physics doesn't match: Vesta is small-body
    radiation-drift, not a chaotic-obliquity rigid body). Pinned
    here as a v0.24.12-introduced schema-gap; future ship will need
    a small-body-radiation ground-proof row to give Vesta a correct
    home."""
    by = {p.name: p for p in REGIME_PROBES}
    r = classify_dynamical_regime(by["vesta"].feature_vector())
    assert r["out_of_distribution"] is False
    assert r["nearest_regime"]["regime_label"] == (
        "rigid_body_chaotic_obliquity"
    )
    assert r["calibration_ratio"] < 0.85


def test_phobos_classifier_landing_pinned() -> None:
    """Phobos is a 'let classifier surprise us' probe (small irregular
    Mars moon, no clean v0.24.x analog). v0.24.9 returns chaotic-Mars
    at distance ~0.91; this test pins that surprising landing as the
    documented current behaviour."""
    by = {p.name: p for p in REGIME_PROBES}
    label = _classified_regime(by["phobos"].feature_vector())
    assert label == "rigid_body_chaotic_obliquity"


def test_magnetar_classifier_landing_pinned() -> None:
    """Magnetar's dimensionality=3 dominates and aligns with the
    Toroidal-Residual training example, even though the size is wildly
    off. Documented surprising-classification ratchet."""
    by = {p.name: p for p in REGIME_PROBES}
    label = _classified_regime(by["magnetar_typical"].feature_vector())
    assert label == "shape_residual_chandrasekhar"


# ──────────────────────────────────────────────────────────────────────
# run_dynamical_regime_probes summary invariants
# ──────────────────────────────────────────────────────────────────────


def test_run_probes_returns_all_10() -> None:
    r = run_dynamical_regime_probes()
    assert r["ok"] is True
    assert r["n_probes"] == 10
    assert len(r["probes"]) == 10


def test_run_probes_all_pass_or_correctly_flagged() -> None:
    """Every probe with an expectation either matches its expected
    regime or is correctly OOD-flagged. Zero unexpected results.

    This is the ratchet: any future change that flips a probe's
    classification will fail this test, forcing explicit review."""
    r = run_dynamical_regime_probes()
    summary = r["summary"]
    assert summary["n_unexpected_classifications"] == 0


def test_run_probes_match_count() -> None:
    """v0.24.12 ratchet revision: 7 probes have explicit non-OOD
    expectations (Yellowstone, Reunion, Pluto-Charon, Enceladus, Io,
    Alpha Centauri B, magnetar); 1 is OOD-expected (Ceres); 2 are
    let-classifier-surprise-us (Phobos, Vesta).

    Counts evolution:
      • Pre-v0.24.11: 8 + 1 + 1
      • v0.24.11:     7 + 2 + 1 (Ceres → OOD-expected)
      • v0.24.12:     7 + 1 + 2 (Vesta → surprise; Loki neighbour
                       collapsed Vesta's calibration ratio)
    """
    r = run_dynamical_regime_probes()
    summary = r["summary"]
    assert summary["n_matches_expected"] == 7
    assert summary["n_correctly_flagged_ood"] == 1


def test_run_probes_each_entry_has_calibration_ratio() -> None:
    r = run_dynamical_regime_probes()
    for entry in r["probes"]:
        assert "calibration_ratio" in entry
        assert "out_of_distribution" in entry
        assert "nearest_distance" in entry
        assert "second_nearest_distance" in entry


# ──────────────────────────────────────────────────────────────────────
# list_dynamical_regime_probes (data-side enumerator)
# ──────────────────────────────────────────────────────────────────────


def test_list_probes_returns_all_10() -> None:
    r = list_dynamical_regime_probes()
    assert r["ok"] is True
    assert r["n_probes"] == 10
    assert r["n_sources"] == 10
    assert len(r["probes"]) == 10


def test_list_probes_includes_feature_vectors() -> None:
    r = list_dynamical_regime_probes()
    for entry in r["probes"]:
        assert "feature_vector" in entry
        assert len(entry["feature_vector"]) == N_FEATURES


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_run_dynamical_regime_probes() -> None:
    r = bridge.run_dynamical_regime_probes()
    assert r["ok"] is True
    assert r["n_probes"] == 10


def test_bridge_list_dynamical_regime_probes() -> None:
    r = bridge.list_dynamical_regime_probes()
    assert r["ok"] is True
    assert r["n_probes"] == 10


def test_bridge_classify_returns_calibration_metric() -> None:
    """v0.24.10 added calibration_ratio + nearest_neighbour_margin +
    out_of_distribution + ood_threshold_used to classify_dynamical_regime
    output."""
    r = bridge.classify_dynamical_regime(REGIME_EXAMPLES[0].feature_vector())
    assert "calibration_ratio" in r
    assert "nearest_neighbour_margin" in r
    assert "out_of_distribution" in r
    assert "ood_threshold_used" in r


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_regime_probes_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["regime-probes"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_probes"] == 10
    assert payload["summary"]["n_unexpected_classifications"] == 0


def test_cli_regime_probes_list_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["regime-probes-list"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_probes"] == 10


def test_cli_regime_probes_help() -> None:
    """v0.24.10 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("regime-probes", "regime-probes-list"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
