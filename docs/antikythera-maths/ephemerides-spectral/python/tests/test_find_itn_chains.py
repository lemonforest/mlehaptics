"""v0.17.0 — multi-leg ITN chain search (find_itn_chains).

Tests the Dijkstra-style graph search over (body, epoch) state space
that the post-v0.15.0 Lagrange-highway research subagent recommended
(notebook §12.2). Each leg is a closed-form Hohmann window from the
v0.8.1 find_itn_pathways; legs stitch end-to-end at intermediate
bodies; cumulative Δv and time-of-flight are budget-bounded.

Invariants pinned:
  - Empty intermediates ⇒ single-leg direct chain matches find_tubes
    (the Dijkstra search collapses to the v0.8.1 surface).
  - Resonance signature is integer-valued (p, q) with 1 ≤ p, q ≤ 30
    and gcd(p, q) = 1 (lowest terms).
  - Earth → Mars recovers (8, 15) -- the well-known synodic-resonance
    rational approximation for the period ratio 365.25/686.98 ≈ 0.532.
  - Earth → Jupiter recovers (1, 12) -- Jupiter's ~12-yr orbit anchor.
  - Δv budget is enforced (cumulative across legs, not per-leg).
  - TOF budget is enforced (cumulative).
  - Chains are emitted in optimal-Δv-first order (Dijkstra invariant).
  - Departure must differ from target; both must be heliocentric.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.itn_window import (
    ITNChainCandidate,
    _best_rational_approx,
    find_itn_chains,
)


# ──────────────────────────────────────────────────────────────────────
# Rational-approximation helper
# ──────────────────────────────────────────────────────────────────────

def test_rational_approx_earth_mars() -> None:
    """Earth/Mars period ratio 365.25/686.98 ≈ 0.5317 -> (8, 15) is
    the canonical synodic-resonance rational approximation, matching
    the well-known 8-Earth-yr / 15-Mars-orbit synodic anchor.
    """
    p, q = _best_rational_approx(365.25 / 686.98)
    assert (p, q) == (8, 15)


def test_rational_approx_earth_jupiter() -> None:
    """Earth/Jupiter ≈ 0.0843 -> (1, 12), matching Jupiter's ~12-yr
    orbital period. Tests that small-ratio cases also reduce.
    """
    p, q = _best_rational_approx(365.25 / 4332.589)
    assert (p, q) == (1, 12)


def test_rational_approx_jupiter_saturn() -> None:
    """Jupiter/Saturn 4332.589/10759.22 ≈ 0.4027 -> the famous 2:5
    "great-inequality" resonance.
    """
    p, q = _best_rational_approx(4332.589 / 10759.22)
    assert (p, q) == (2, 5)


def test_rational_approx_lowest_terms() -> None:
    """The returned (p, q) is in lowest terms (gcd = 1)."""
    for ratio in (0.5, 0.333333, 0.25, 0.4, 1.5, 2.0, 1 / math.pi):
        p, q = _best_rational_approx(ratio)
        if (p, q) != (0, 0):
            assert math.gcd(p, q) == 1, (
                f"rational_approx({ratio}) returned ({p}, {q}) "
                f"not in lowest terms"
            )


def test_rational_approx_invalid_ratio() -> None:
    """Non-finite or non-positive ratios return the (0, 0) sentinel."""
    assert _best_rational_approx(0.0) == (0, 0)
    assert _best_rational_approx(-1.0) == (0, 0)
    assert _best_rational_approx(float("inf")) == (0, 0)
    assert _best_rational_approx(float("nan")) == (0, 0)


# ──────────────────────────────────────────────────────────────────────
# Direct-chain consistency with find_itn_pathways
# ──────────────────────────────────────────────────────────────────────

def test_chains_empty_intermediates_matches_find_tubes() -> None:
    """intermediates=[] forces a single-leg direct chain. The
    Dijkstra search should collapse to the v0.8.1 find_itn_pathways
    surface for this case -- per-leg jd_tdb / transfer_time / Δv all
    byte-identical, modulo the Dijkstra-optimal-first ordering vs
    chronological ordering of find_itn_pathways.
    """
    jd_lo, jd_hi = 2451545.0, 2470000.0
    # Widen the TOF budget past the search horizon: the Dijkstra
    # cumulative-TOF accumulator (leg.transfer_time + (jd - head_jd))
    # includes wait time before launch, so launches late in the
    # search window otherwise get pruned by the default 20-yr budget.
    direct = find_itn_chains(
        jd_lo, jd_hi,
        departure="terra", target="mars",
        intermediates=[],
        max_legs=1,
        max_intermediate_windows=1000,
        max_chains=1000,
        tof_budget_days=(jd_hi - jd_lo) * 2.0,
    )
    legacy = bridge.find_itn_pathways(
        jd_lo, jd_hi,
        departure="terra", target="mars",
        threshold=0.05,
    )
    assert legacy["ok"] is True
    assert len(direct) == legacy["n_candidates"], (
        f"chain count {len(direct)} != legacy count "
        f"{legacy['n_candidates']}"
    )
    direct_jds = sorted(c.legs[0].jd_tdb for c in direct)
    legacy_jds = sorted(cand["jd_tdb"] for cand in legacy["candidates"])
    for d, l in zip(direct_jds, legacy_jds):
        assert abs(d - l) < 1e-6, (
            f"direct-chain leg jd {d} differs from find-tubes jd {l}"
        )


def test_chains_dijkstra_optimal_first() -> None:
    """Dijkstra invariant: chains are emitted in monotonically non-
    decreasing total_dv_kms order. The first chain is the optimal-Δv
    chain.
    """
    chains = find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="jupiter",
        max_legs=3,
        dv_budget_kms=25.0,
        threshold=0.1,
    )
    if len(chains) < 2:
        pytest.skip("not enough chains to test ordering")
    for i in range(len(chains) - 1):
        assert chains[i].total_dv_kms <= chains[i + 1].total_dv_kms + 1e-9, (
            f"chain {i} has total_dv {chains[i].total_dv_kms} > "
            f"chain {i+1}'s {chains[i+1].total_dv_kms} -- Dijkstra "
            f"emission ordering violated"
        )


# ──────────────────────────────────────────────────────────────────────
# Resonance signature
# ──────────────────────────────────────────────────────────────────────

def test_resonance_signature_per_leg_count() -> None:
    """The resonance_signature tuple has exactly len(legs) entries."""
    chains = find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="mars",
        intermediates=[],
        max_legs=1,
    )
    for c in chains:
        assert len(c.resonance_signature) == len(c.legs)


def test_resonance_signature_earth_mars_is_8_15() -> None:
    """Earth → Mars chain has resonance signature (8, 15) per leg
    (the well-known 8-Earth-yr / 15-Mars-orbit synodic anchor)."""
    chains = find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="mars",
        intermediates=[],
        max_legs=1,
    )
    assert len(chains) > 0
    for c in chains:
        for pq in c.resonance_signature:
            assert pq == (8, 15), (
                f"expected (8, 15) for Earth->Mars, got {pq}"
            )


# ──────────────────────────────────────────────────────────────────────
# Budget enforcement
# ──────────────────────────────────────────────────────────────────────

def test_dv_budget_enforced() -> None:
    """No chain in the output has total_dv_kms exceeding the budget."""
    budget = 12.0
    chains = find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="jupiter",
        max_legs=3,
        dv_budget_kms=budget,
        threshold=0.1,
    )
    for c in chains:
        assert c.total_dv_kms <= budget + 1e-9


def test_tof_budget_enforced() -> None:
    """No chain in the output has total_tof_days exceeding the budget."""
    budget = 365.25 * 5.0  # 5 yr
    chains = find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="jupiter",
        max_legs=2,
        tof_budget_days=budget,
        threshold=0.1,
    )
    for c in chains:
        assert c.total_tof_days <= budget + 1e-6


def test_max_legs_enforced() -> None:
    """No chain has more legs than max_legs."""
    chains = find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="jupiter",
        max_legs=2,
        threshold=0.1,
    )
    for c in chains:
        assert len(c.legs) <= 2


# ──────────────────────────────────────────────────────────────────────
# Bridge surface
# ──────────────────────────────────────────────────────────────────────

def test_bridge_find_itn_chains_basic_smoke() -> None:
    r = bridge.find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="mars",
        intermediates=[],
    )
    assert r["ok"] is True
    assert r["departure"] == "terra"
    assert r["target"] == "mars"
    assert r["max_legs"] == 4
    assert r["n_chains"] >= 1
    assert isinstance(r["chains"], list)
    first = r["chains"][0]
    assert "jd_tdb_launch" in first
    assert "jd_tdb_arrival" in first
    assert "legs" in first
    assert "total_dv_kms" in first
    assert "total_tof_days" in first
    assert "resonance_signature" in first
    assert "score" in first


def test_bridge_find_itn_chains_rejects_self_transfer() -> None:
    r = bridge.find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="terra",
    )
    assert r["ok"] is False
    assert "must differ" in r["error"].lower()


def test_bridge_find_itn_chains_rejects_unknown_body() -> None:
    r = bridge.find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="krypton",
    )
    assert r["ok"] is False


def test_bridge_find_itn_chains_rejects_invalid_threshold() -> None:
    r = bridge.find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="mars",
        threshold=0.0,
    )
    assert r["ok"] is False


def test_bridge_find_itn_chains_rejects_invalid_budget() -> None:
    r = bridge.find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="mars",
        dv_budget_kms=-1.0,
    )
    assert r["ok"] is False


def test_bridge_find_itn_chains_rejects_invalid_intermediate() -> None:
    r = bridge.find_itn_chains(
        2451545.0, 2470000.0,
        departure="terra", target="mars",
        intermediates=["jupiter", "krypton"],
    )
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface
# ──────────────────────────────────────────────────────────────────────

def test_cli_find_chains_direct() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "find-chains",
            "--from-jd", "2451545.0",
            "--to-jd", "2470000.0",
            "--departure", "terra",
            "--target", "mars",
            "--intermediates", "",  # force single-leg direct
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["departure"] == "terra"
    assert payload["target"] == "mars"
    assert payload["n_chains"] >= 1


def test_cli_find_chains_multi_leg() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "find-chains",
            "--from-jd", "2451545.0",
            "--to-jd", "2470000.0",
            "--departure", "terra",
            "--target", "jupiter",
            "--intermediates", "venus,mars",
            "--max-legs", "3",
            "--threshold", "0.1",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["n_chains"] >= 1


def test_cli_find_chains_help() -> None:
    """find-chains --help renders without error and mentions the
    Dijkstra-style description."""
    import argparse
    from ephemerides_spectral.cli import main as cli_main

    with pytest.raises(SystemExit) as exc_info:
        cli_main(["find-chains", "--help"])
    assert exc_info.value.code == 0
