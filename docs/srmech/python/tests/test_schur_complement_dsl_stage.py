"""v0.7.1rc2 — ``schur_complement`` is a data-first DSL chain stage.

#897 §26: the Class-L Schur-complement / Dirichlet-to-Neumann op shipped in
v0.7.1rc1 at ``srmech.amsc.laplacian.schur_complement`` but was not reachable
from the chain DSL — the chain runner resolves stage ops via
``getattr(srmech.amsc.cascade, name)`` and the op lived only on the laplacian
module. rc2 wires it: the op is re-exported flat onto ``srmech.amsc.cascade``
(DSL resolution alias, not a second primitive) and a cascade-catalog
descriptor (``schur_complement.toml``) threads ``boundary_idx`` (required) +
``exact`` (default False) through the chain contract as non-reserved bound
stage kwargs — the same data-first pattern as ``reorient``'s ``orientation``.

The op pipes the Laplacian into arg0 (``schur_complement(L, ...)``); the
boundary set and exactness arrive as bound kwargs. These tests pin the wiring
via the Python ``.then()`` API and via a TOML chain, on the path-4 graph
worked instance from rc1: boundary {0,3} → S = (1/3)[[1,-1],[-1,1]].
"""

from fractions import Fraction

import pytest

from srmech.amsc import cascade, laplacian
from srmech.dsl import (
    Chain,
    get_descriptor,
    list_cascade_ops,
    lookup_cascade_op,
    run_toml_chain,
)

# Path graph 0-1-2-3 (degrees 1,2,2,1). L = D - A. Boundary {0,3},
# interior {1,2}. Exact Schur complement S = (1/3)[[1,-1],[-1,1]] — the rc1
# worked instance (row-sums 0; rank |∂|-1 = 1 for the connected graph).
_PATH4_L = [
    [1, -1, 0, 0],
    [-1, 2, -1, 0],
    [0, -1, 2, -1],
    [0, 0, -1, 1],
]
_THIRD = Fraction(1, 3)
_EXPECTED_S = [[_THIRD, -_THIRD], [-_THIRD, _THIRD]]


def _assert_exact_equals(got, expected):
    assert len(got) == len(expected)
    for grow, erow in zip(got, expected):
        assert len(grow) == len(erow)
        for g, e in zip(grow, erow):
            assert Fraction(g) == e, (got, expected)


# ── catalog wiring ────────────────────────────────────────────────────


def test_schur_complement_is_in_cascade_catalog():
    # The descriptor makes the op discoverable; it is the 14th catalog op.
    assert "schur_complement" in list_cascade_ops()
    desc = get_descriptor("schur_complement")
    assert desc["cascade"]["class_composition"] == "L"


def test_lookup_resolves_to_the_laplacian_op():
    # The flat re-export on srmech.amsc.cascade IS the laplacian-registered
    # callable — same object, reached for the chain contract.
    fn = lookup_cascade_op("schur_complement")
    assert callable(fn)
    assert fn is cascade.schur_complement
    assert fn is laplacian.schur_complement


# ── drives as a .then() stage ─────────────────────────────────────────


def test_schur_drives_as_then_stage_exact():
    # The finding: schur_complement must be invokable as an op= stage. The
    # runner pipes L into arg0; boundary_idx + exact are bound kwargs.
    ch = Chain("dtn").then("schur_complement", boundary_idx=[0, 3], exact=True)
    _assert_exact_equals(ch.run(_PATH4_L), _EXPECTED_S)


def test_schur_boundary_idx_is_a_required_bound_kwarg():
    # boundary_idx has no default — a chain that omits it fails at run time
    # (TypeError: missing required keyword-only argument), not silently.
    ch = Chain("nobound").then("schur_complement")
    with pytest.raises(TypeError):
        ch.run(_PATH4_L)


# ── drives from a TOML chain ──────────────────────────────────────────


def test_schur_drives_from_toml_chain_exact():
    # boundary_idx (a list) + exact (a bool) are non-reserved [[stage]] keys,
    # forwarded as ch.then("schur_complement", boundary_idx=[0,3], exact=True).
    spec = """
name = "toml-dtn"
[[stage]]
op = "schur_complement"
boundary_idx = [0, 3]
exact = true
"""
    _assert_exact_equals(run_toml_chain(spec, _PATH4_L), _EXPECTED_S)


# ── float path (default; needs the srmech[scientific] numpy extra) ────


def test_schur_then_stage_float_path_when_numpy_present():
    np = pytest.importorskip("numpy")
    # Default exact=False → numpy-backed float Schur complement. Same matrix.
    ch = Chain("dtn-f").then("schur_complement", boundary_idx=[0, 3])
    S = ch.run([[float(x) for x in row] for row in _PATH4_L])
    expected = np.array([[1.0, -1.0], [-1.0, 1.0]]) / 3.0
    assert np.allclose(np.asarray(S, dtype=float), expected)
