"""v0.18.0 — Body Architecture (resonance-weighted gateway-graph
Laplacian Fiedler partition; inner/outer classification).

The §13.8 research finding promoted to a stable ship surface. Tests
pin:

* The 13-body heliocentric default roster classifies into the
  canonical inner-8 / outer-5 split.
* Specific bodies land on the right side (mercury → inner, pluto →
  outer, the asteroid belt → inner).
* Pluto + Neptune share the deepest negative Fiedler entry (the 2:3
  mean-motion lock signature).
* The Fiedler-vector sign is reproducible (anchored to the shortest-
  period body being positive).
* Bridge surface (full + single-body + rejection paths).
* CLI surface (full + --target + --help).
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.body_architecture import (
    HELIOCENTRIC_BODIES,
    INNER_CLASS,
    OUTER_CLASS,
    compute_body_architecture,
)


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — compute_body_architecture
# ──────────────────────────────────────────────────────────────────────

def test_default_roster_classifies_13_bodies() -> None:
    """Default heliocentric roster has 13 bodies and they all classify."""
    r = compute_body_architecture()
    assert r["ok"] is True
    assert r["n_bodies"] == 13
    assert len(r["bodies"]) == 13
    assert all(b["class"] in (INNER_CLASS, OUTER_CLASS) for b in r["bodies"])


def test_outer_partition_is_the_canonical_outer_5() -> None:
    """The outer partition contains exactly jupiter, saturn, uranus,
    neptune, pluto — the canonical "outer system" by inspection.
    """
    r = compute_body_architecture()
    assert set(r["partitions"][OUTER_CLASS]) == {
        "jupiter", "saturn", "uranus", "neptune", "pluto",
    }


def test_inner_partition_is_the_canonical_inner_8() -> None:
    """The inner partition contains mercury, venus, terra, mars,
    plus the four main-belt asteroids vesta / ceres / pallas / hygiea.
    """
    r = compute_body_architecture()
    assert set(r["partitions"][INNER_CLASS]) == {
        "mercury", "venus", "terra", "mars",
        "vesta", "ceres", "pallas", "hygiea",
    }


def test_partition_sizes() -> None:
    """Inner has 8 bodies, outer has 5, summing to 13."""
    r = compute_body_architecture()
    assert len(r["partitions"][INNER_CLASS]) == 8
    assert len(r["partitions"][OUTER_CLASS]) == 5


def test_pluto_neptune_share_deepest_outer_entries() -> None:
    """Pluto and Neptune share the deepest negative Fiedler entries —
    the spectral signature of their 2:3 mean-motion lock dragging both
    deep into the outer cluster. Test pins that both have entry below
    -0.5 and that they are within 0.01 of each other.
    """
    r = compute_body_architecture()
    by_name = {b["name"]: b["fiedler_value"] for b in r["bodies"]}
    assert by_name["pluto"] < -0.5
    assert by_name["neptune"] < -0.5
    assert abs(by_name["pluto"] - by_name["neptune"]) < 0.01


def test_mercury_has_largest_positive_fiedler_entry() -> None:
    """Mercury — the shortest-period body in the roster — has the
    largest positive Fiedler entry. The sign convention anchors on the
    shortest-period body being positive, so this is also the
    reproducibility check.
    """
    r = compute_body_architecture()
    by_name = {b["name"]: b["fiedler_value"] for b in r["bodies"]}
    inner_max = max(
        by_name[name] for name in r["partitions"][INNER_CLASS]
    )
    assert by_name["mercury"] == inner_max
    assert by_name["mercury"] > 0.0


def test_fiedler_values_are_sorted_ascending() -> None:
    """The bodies list is sorted by Fiedler value ascending."""
    r = compute_body_architecture()
    f_values = [b["fiedler_value"] for b in r["bodies"]]
    assert f_values == sorted(f_values)


def test_lambda_2_is_positive() -> None:
    """The algebraic connectivity is strictly positive (the gateway
    graph is connected; λ₁ = 0 trivially, λ₂ > 0)."""
    r = compute_body_architecture()
    assert r["lambda_2"] > 0.0


def test_classification_is_deterministic() -> None:
    """Repeated calls return identical classification + Fiedler
    values. The sign convention removes LAPACK-pivoting nondeterminism.
    """
    r1 = compute_body_architecture()
    r2 = compute_body_architecture()
    assert r1["partitions"] == r2["partitions"]
    f1 = [b["fiedler_value"] for b in r1["bodies"]]
    f2 = [b["fiedler_value"] for b in r2["bodies"]]
    for v1, v2 in zip(f1, f2):
        assert abs(v1 - v2) < 1e-12


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — error paths
# ──────────────────────────────────────────────────────────────────────

def test_rejects_too_few_bodies() -> None:
    with pytest.raises(ValueError, match="≥ 2 bodies"):
        compute_body_architecture(bodies=["terra"])


def test_rejects_duplicate_bodies() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        compute_body_architecture(bodies=["terra", "mars", "terra"])


def test_rejects_unknown_body() -> None:
    with pytest.raises(ValueError, match="unknown body"):
        compute_body_architecture(bodies=["terra", "krypton"])


def test_rejects_zero_period_body() -> None:
    """Sun has period_days = 0.0 (it is the central potential, not a
    transit node). Including it raises."""
    with pytest.raises(ValueError, match="non-positive"):
        compute_body_architecture(bodies=["sun", "terra", "mars"])


# ──────────────────────────────────────────────────────────────────────
# Bridge surface
# ──────────────────────────────────────────────────────────────────────

def test_bridge_full_partition() -> None:
    r = bridge.body_architecture()
    assert r["ok"] is True
    assert r["n_bodies"] == 13
    assert "bodies" in r
    assert "partitions" in r
    assert set(r["partitions"][OUTER_CLASS]) == {
        "jupiter", "saturn", "uranus", "neptune", "pluto",
    }


@pytest.mark.parametrize("body,expected_class", [
    ("mercury", INNER_CLASS),
    ("venus", INNER_CLASS),
    ("terra", INNER_CLASS),
    ("mars", INNER_CLASS),
    ("ceres", INNER_CLASS),
    ("vesta", INNER_CLASS),
    ("pallas", INNER_CLASS),
    ("hygiea", INNER_CLASS),
    ("jupiter", OUTER_CLASS),
    ("saturn", OUTER_CLASS),
    ("uranus", OUTER_CLASS),
    ("neptune", OUTER_CLASS),
    ("pluto", OUTER_CLASS),
])
def test_bridge_single_body_lookup(body: str, expected_class: str) -> None:
    r = bridge.body_architecture(target=body)
    assert r["ok"] is True
    assert r["name"] == body
    assert r["class"] == expected_class
    assert "fiedler_value" in r
    assert "period_days" in r
    assert "lambda_2" in r


def test_bridge_target_case_insensitive() -> None:
    """Mixed-case body names lower-case correctly."""
    r = bridge.body_architecture(target="TERRA")
    assert r["ok"] is True
    assert r["name"] == "terra"


def test_bridge_rejects_unknown_target() -> None:
    r = bridge.body_architecture(target="krypton")
    assert r["ok"] is False
    assert "unknown" in r["error"].lower()


def test_bridge_rejects_non_heliocentric_target() -> None:
    """Bodies in the wider 52-body roster but NOT in the 13-body
    heliocentric subset (e.g. moons, the Sun) are rejected."""
    r = bridge.body_architecture(target="luna")
    assert r["ok"] is False
    r2 = bridge.body_architecture(target="sun")
    assert r2["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface
# ──────────────────────────────────────────────────────────────────────

def test_cli_body_architecture_full() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["body-architecture"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["n_bodies"] == 13
    assert set(payload["partitions"]["outer"]) == {
        "jupiter", "saturn", "uranus", "neptune", "pluto",
    }


def test_cli_body_architecture_target() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["body-architecture", "--target", "jupiter"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["name"] == "jupiter"
    assert payload["class"] == OUTER_CLASS


def test_cli_body_architecture_help() -> None:
    """body-architecture --help renders without error."""
    from ephemerides_spectral.cli import main as cli_main

    with pytest.raises(SystemExit) as exc_info:
        cli_main(["body-architecture", "--help"])
    assert exc_info.value.code == 0


# ──────────────────────────────────────────────────────────────────────
# Default roster contract
# ──────────────────────────────────────────────────────────────────────

def test_default_roster_is_heliocentric_13_body() -> None:
    """The default ``HELIOCENTRIC_BODIES`` list is the 13-body
    heliocentric subset of the v0.16.0 BODIES roster.
    """
    assert HELIOCENTRIC_BODIES == [
        "mercury", "venus", "terra", "mars",
        "jupiter", "saturn", "uranus", "neptune", "pluto",
        "ceres", "vesta", "pallas", "hygiea",
    ]
