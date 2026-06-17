"""DSL-class ↔ Python equivalence for the GatewayNavigation [class] TOML.

Per `[[feedback_prefer_config_driven_toml_classes]]`: every config-driven
class conversion is proven with a DSL-class-vs-Python equivalence test.
The ``GatewayNavigation`` class (``class_catalog/gateway_navigation.toml``)
declares the ITN / etak navigation cascade over the flat
``navigation_ops`` adapters; here we assert the declarative path is
byte-identical to calling those adapters directly, and that the
``fiedler`` view reproduces the live ``body_architecture`` partition.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral._research import body_architecture as ba
from ephemerides_spectral._research import navigation_ops as nav
from ephemerides_spectral._research import _srmech_classes


def _resonance_laplacian_and_pivot(bodies):
    """Build the resonance Laplacian + shortest-period pivot (the same
    inputs body_architecture feeds the cascade)."""
    from ephemerides_spectral._research.bodies import BODIES
    periods = [BODIES[name].period_days for name in bodies]
    n = len(bodies)
    edges, weights = nav.symmetric_pairs_to_edges(
        n, lambda i, j: ba._resonance_weight(periods[i], periods[j])
    )
    L = nav.adjacency_to_laplacian(n, edges, weights)
    pivot = periods.index(min(periods))
    return L, pivot


def _gw():
    """The GatewayNavigation DSL-class factory (skips if unavailable)."""
    try:
        return _srmech_classes.gateway_navigation_class()
    except Exception as exc:  # pragma: no cover - srmech DSL missing
        pytest.skip(f"GatewayNavigation class unavailable: {exc}")


def test_class_registers_and_constructs():
    GW = _gw()
    L, pivot = _resonance_laplacian_and_pivot(ba.HELIOCENTRIC_BODIES)
    inst = GW(L=L, pivot=pivot)
    assert inst is not None


def test_fiedler_view_matches_navigation_ops():
    GW = _gw()
    L, pivot = _resonance_laplacian_and_pivot(ba.HELIOCENTRIC_BODIES)
    lam2_dsl, f2_dsl = GW(L=L, pivot=pivot).fiedler()
    lam2_py, f2_py = nav.fiedler_partition(L, pivot)
    assert lam2_dsl == lam2_py
    assert list(f2_dsl) == list(f2_py)


def test_embed2d_view_matches_navigation_ops():
    GW = _gw()
    L, pivot = _resonance_laplacian_and_pivot(ba.HELIOCENTRIC_BODIES)
    lam2_d, lam3_d, f2_d, f3_d = GW(L=L, pivot=pivot).embed2d()
    lam2_p, lam3_p, f2_p, f3_p = nav.fiedler_embedding_2d(L, pivot)
    assert (lam2_d, lam3_d) == (lam2_p, lam3_p)
    assert list(f2_d) == list(f2_p) and list(f3_d) == list(f3_p)


def test_fiedler_view_reproduces_body_architecture_partition():
    """The DSL ``fiedler`` view's sign pattern == the live body_architecture
    inner/outer partition (the etak ≡ ITN architecture identity)."""
    GW = _gw()
    bodies = ba.HELIOCENTRIC_BODIES
    L, pivot = _resonance_laplacian_and_pivot(bodies)
    _, f2 = GW(L=L, pivot=pivot).fiedler()
    dsl_inner = {bodies[i] for i, v in enumerate(f2) if v >= 0.0}
    arch = ba.compute_body_architecture()
    assert dsl_inner == set(arch["partitions"]["inner"])
