"""rc309 (#944 follow-on) — quaternion_cycle_holonomy: the k=2 discrete
holonomy channel over the quaternion units Q8 (the ℍ which-way / Lk-analog
reader). The NON-ABELIAN generalization of the abelian
``srmech.amsc.laplacian.cycle_holonomy``.

The load-bearing test is ``test_regauge_invariance_proof_gate`` — the rc309
PROOF GATE. Only the *conjugacy class* of a non-abelian cycle product is
gauge-invariant, so it is MEASURED, not assumed: a node-wise re-gauge
``g_uv → s_u·g_uv·conj(s_v)`` (random Q8 AND random continuous unit-quaternion
``s``) leaves the per-cycle SU(2) ``class_index`` UNCHANGED (to ~1e-15) while
the raw holonomy quaternion genuinely MOVES for the non-central (pure-imaginary)
cycles. The finding it also pins: the finer 5-class Q8 split ±i/±j/±k is
invariant only under DISCRETE Q8 re-gauge — continuous SU(2) merges the three
imaginary axes — so the frame-free keystone is the scalar-part (SU(2)) class.

numpy-free (``math`` + ``random`` only; the numpy-absent-venv guards elsewhere
in the suite verify numpy is genuinely absent). Computational-provenance
discipline: every random draw is seeded.
"""
from __future__ import annotations

import math
import random

import pytest

from srmech.amsc import _native
from srmech.qm import quaternion as Q

# ── The eight Q8 unit quaternions (scalar-first (w, x, y, z)) ─────────────────
ONE = [1.0, 0.0, 0.0, 0.0]
NEG = [-1.0, 0.0, 0.0, 0.0]
I = [0.0, 1.0, 0.0, 0.0]
NI = [0.0, -1.0, 0.0, 0.0]
J = [0.0, 0.0, 1.0, 0.0]
NJ = [0.0, 0.0, -1.0, 0.0]
K = [0.0, 0.0, 0.0, 1.0]
NK = [0.0, 0.0, 0.0, -1.0]
Q8 = [ONE, NEG, I, NI, J, NJ, K, NK]


def _qmul(a, b):
    """a·b via the module's byte-exact structure-table product."""
    return Q._quat_mul(list(a), list(b))


def _conj(a):
    return Q.quaternion_conjugate(list(a))


def _regauge(n, edges, gains, s):
    """Apply the node-wise re-gauge g_uv → s_u · g_uv · conj(s_v)."""
    out = []
    for (u, v), g in zip(edges, gains):
        out.append(_qmul(_qmul(s[u], g), _conj(s[v])))
    return out


def _rand_q8(rng):
    return list(rng.choice(Q8))


def _rand_unit_quat(rng):
    """A random CONTINUOUS unit quaternion (∈ SU(2)); numpy-free."""
    v = [rng.gauss(0.0, 1.0) for _ in range(4)]
    nrm = math.sqrt(sum(x * x for x in v))
    while nrm == 0.0:                                   # measure-zero guard
        v = [rng.gauss(0.0, 1.0) for _ in range(4)]
        nrm = math.sqrt(sum(x * x for x in v))
    return [x / nrm for x in v]


# ── The test graphs: (name, n, edges, gains) ─────────────────────────────────
# Each hand-picked so the holonomy set spans the three SU(2) classes.
_TRI = [(0, 1), (1, 2), (2, 0)]
_GRAPHS = [
    # ijk triangle: P0=1, P1=i, P2=i·j=k; H = k·k·conj(1) = k² = −1 → class 1.
    ("triangle_ijk", 3, _TRI, [I, J, K]),
    # iii triangle: H = −i → class 2 (pure-imaginary; MOVES under re-gauge).
    ("triangle_iii", 3, _TRI, [I, I, I]),
    # theta / digon (two parallel edges): tree i, co-tree j; H = j·conj(i) = k.
    ("theta_digon", 2, [(0, 1), (0, 1)], [I, J]),
    # K4 (complete, 6 edges → 3 fundamental cycles), mixed Q8 gains.
    ("K4", 4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
     [I, J, K, I, J, K]),
    # a pure 5-cycle: gains iiiii; H = i → class 2.
    ("cycle5", 5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)],
     [I, I, I, I, I]),
]


# =====================================================================
# THE PROOF GATE — re-gauge invariance (NON-NEGOTIABLE)
# =====================================================================
def test_regauge_invariance_proof_gate():
    """The rc309 keystone: the per-cycle SU(2) conjugacy-class index is
    re-gauge-invariant (to ~1e-15) under BOTH discrete Q8 and continuous
    unit-quaternion re-gauges, while the raw holonomy quaternion genuinely
    MOVES for the non-central (pure-imaginary) cycles and stays pointwise
    fixed for the central ones (the center is gauge-invariant pointwise)."""
    rng = random.Random(20260722)
    n_draws = 80
    saw_class2 = False                                 # the whole gate is vacuous otherwise
    for name, n, edges, gains in _GRAPHS:
        base = Q.quaternion_cycle_holonomy(edges, gains, n=n)
        n_cyc = base["n_cycles"]
        assert n_cyc >= 1, name
        base_cls = base["class_index"]
        base_par = base["center_parity"]
        base_hol = base["holonomies"]
        base_edges = base["cycle_edges"]
        if 2 in base_cls:
            saw_class2 = True
        # max raw-holonomy movement per cycle across all draws
        max_move = [0.0] * n_cyc
        # worst class-invariance residual (scalar part vs the base bucket centre)
        for draw in range(n_draws):
            s = ([_rand_q8(rng) for _ in range(n)] if draw % 2 == 0
                 else [_rand_unit_quat(rng) for _ in range(n)])
            rg = _regauge(n, edges, gains, s)
            res = Q.quaternion_cycle_holonomy(edges, rg, n=n)
            # the graph structure (hence the fundamental-cycle basis) is fixed
            assert res["cycle_edges"] == base_edges, (name, draw)
            # THE INVARIANT: class + central parity UNCHANGED, exactly.
            assert res["class_index"] == base_cls, (
                name, draw, res["class_index"], base_cls)
            assert res["center_parity"] == base_par, (name, draw)
            for c in range(n_cyc):
                d = max(abs(res["holonomies"][c][t] - base_hol[c][t])
                        for t in range(4))
                if d > max_move[c]:
                    max_move[c] = d
        # class 2 (pure-imaginary) MUST move; class 0/1 (central) MUST stay put.
        for c in range(n_cyc):
            if base_cls[c] == 2:
                assert max_move[c] > 1e-3, (
                    name, c, "a pure-imaginary holonomy must MOVE under re-gauge",
                    max_move[c])
            else:
                assert max_move[c] < 1e-9, (
                    name, c, "a central holonomy is pointwise gauge-fixed",
                    max_move[c])
    assert saw_class2, "the proof gate never exercised a moving (class-2) cycle"


def test_scalar_part_is_exactly_conjugation_invariant():
    """The mechanism behind the gate: Re(s·H·conj(s)) = Re(H). Measure the
    scalar-part residual directly across continuous re-gauges (the tight
    ~1e-15 number the CHANGELOG quotes)."""
    rng = random.Random(7)
    worst = 0.0
    for name, n, edges, gains in _GRAPHS:
        base = Q.quaternion_cycle_holonomy(edges, gains, n=n)
        base_w = [h[0] for h in base["holonomies"]]
        for _ in range(40):
            s = [_rand_unit_quat(rng) for _ in range(n)]
            res = Q.quaternion_cycle_holonomy(edges, _regauge(n, edges, gains, s), n=n)
            for c, h in enumerate(res["holonomies"]):
                worst = max(worst, abs(h[0] - base_w[c]))
    assert worst < 1e-12, f"scalar part drifted {worst} > 1e-12"


# =====================================================================
# native == pure, byte-for-byte
# =====================================================================
def test_native_pure_parity_byte_for_byte():
    if not _native.has_native_quaternion_cycle_holonomy():
        pytest.skip("native quaternion_cycle_holonomy not loaded")
    rng = random.Random(31337)
    for name, n, edges, base_gains in _GRAPHS:
        edge_list = [tuple(e) for e in edges]
        trials = [base_gains]
        for _ in range(20):                            # random Q8 gains
            trials.append([_rand_q8(rng) for _ in edges])
        for _ in range(20):                            # CONTINUOUS Q8-re-gauges
            s = [_rand_unit_quat(rng) for _ in range(n)]
            trials.append(_regauge(n, edges, base_gains, s))
        for gains in trials:
            gain_flat = [c for g in gains for c in g]
            nat = Q._quaternion_cycle_holonomy_native(n, edge_list, gain_flat)
            pur = Q._quaternion_cycle_holonomy_py(n, edge_list, gains)
            assert nat is not None, name
            ncls, npar, nedges, nhol = nat
            pcls, ppar, pedges, phol = pur
            assert ncls == pcls, (name, "class_index")
            assert npar == ppar, (name, "center_parity")
            assert nedges == pedges, (name, "cycle_edges")
            # BYTE-FOR-BYTE: exact float equality of the raw holonomy.
            assert nhol == phol, (name, "raw holonomy not byte-identical")


def test_native_pure_parity_identity_gains():
    """The NULL-gains (identity) path — native passes NULL, pure passes None;
    both give the trivial (balanced) holonomy on every cycle."""
    if not _native.has_native_quaternion_cycle_holonomy():
        pytest.skip("native not loaded")
    for name, n, edges, _g in _GRAPHS:
        edge_list = [tuple(e) for e in edges]
        nat = Q._quaternion_cycle_holonomy_native(n, edge_list, None)
        pur = Q._quaternion_cycle_holonomy_py(n, edge_list, None)
        assert nat is not None
        assert nat[0] == pur[0] and nat[1] == pur[1]
        assert nat[2] == pur[2] and nat[3] == pur[3]
        assert all(c == 0 for c in nat[0]), name       # identity → class {1}


# =====================================================================
# known cycles + semantics
# =====================================================================
def test_triangle_known_q8_product():
    """A triangle with gains i, j, k: tree 0-1 (i), 1-2 (j) → P₂ = i·j = k;
    co-tree 2-0 (k) → H = k·k·conj(1) = k² = −1 → class {−1}, parity −1."""
    res = Q.quaternion_cycle_holonomy(_TRI, [I, J, K], n=3)
    assert res["n_cycles"] == 1
    assert res["cycle_edges"] == [(2, 0)]
    assert res["class_index"] == [1]                   # {−1}
    assert res["center_parity"] == [-1]
    assert res["balanced"] is False
    h = res["holonomies"][0]
    assert h[0] == pytest.approx(-1.0, abs=1e-12)
    assert all(abs(h[t]) < 1e-12 for t in range(1, 4))


def test_triangle_pure_imaginary_class():
    """Gains i, i, i on the triangle: H = −i → class 2 (pure-imaginary),
    center_parity 0."""
    res = Q.quaternion_cycle_holonomy(_TRI, [I, I, I], n=3)
    assert res["class_index"] == [2]
    assert res["center_parity"] == [0]
    h = res["holonomies"][0]
    assert abs(h[0]) < 1e-12                            # scalar ≈ 0
    assert h[1] == pytest.approx(-1.0, abs=1e-12)       # −i


def test_balanced_identity_gains():
    res = Q.quaternion_cycle_holonomy(_TRI, None, n=3)
    assert res["balanced"] is True
    assert res["class_index"] == [0]                   # {1}
    assert res["center_parity"] == [1]
    h = res["holonomies"][0]
    assert h[0] == pytest.approx(1.0, abs=1e-12)
    assert all(abs(h[t]) < 1e-12 for t in range(1, 4))


def test_tree_only_graph_has_no_cycles():
    """A spanning tree (no co-tree edge) → zero cycles → balanced."""
    res = Q.quaternion_cycle_holonomy([(0, 1), (1, 2)], [I, J], n=3)
    assert res["n_cycles"] == 0
    assert res["class_index"] == []
    assert res["balanced"] is True


# =====================================================================
# quaternion_conjugate (native dispatch)
# =====================================================================
def test_quaternion_conjugate_correctness():
    assert Q.quaternion_conjugate([1.0, 2.0, 3.0, 4.0]) == [1.0, -2.0, -3.0, -4.0]
    # unit inverse: q·conj(q) = 1 for a unit q.
    q = Q.quaternion_exp(0.7, "ijk")
    prod = Q._quat_mul(q, Q.quaternion_conjugate(q))
    assert prod[0] == pytest.approx(1.0, abs=1e-12)
    assert all(abs(prod[t]) < 1e-12 for t in range(1, 4))


def test_quaternion_conjugate_native_dispatch():
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_quaternion_conjugate")):
        pytest.skip("native srmech_quaternion_conjugate not loaded")
    got = Q._try_native_conjugate([1.0, -2.5, 3.0, -4.0])
    assert got == [1.0, 2.5, -3.0, 4.0]


# =====================================================================
# error / edge cases
# =====================================================================
def test_edge_endpoint_out_of_range():
    with pytest.raises(ValueError):
        Q.quaternion_cycle_holonomy([(0, 5)], [I], n=2)


def test_gains_length_mismatch():
    with pytest.raises(ValueError):
        Q.quaternion_cycle_holonomy(_TRI, [I, J], n=3)


def test_non_q8_holonomy_rejected():
    """A non-Q8 (generic-angle) holonomy scalar is not near {−1, 0, 1} →
    ValueError (the op's documented Q8/unit domain)."""
    off = Q.quaternion_exp(0.5, "i")                   # scalar cos(0.5) ≈ 0.877
    with pytest.raises(ValueError):
        Q.quaternion_cycle_holonomy(_TRI, [off, ONE, ONE], n=3)


def test_empty_graph():
    res = Q.quaternion_cycle_holonomy([], None, n=0)
    assert res["n_cycles"] == 0 and res["balanced"] is True


# =====================================================================
# registration ratchet
# =====================================================================
def test_registration_ratchet():
    import srmech
    assert srmech.describe()["tools"]["total"] == 516
    assert "quaternion_cycle_holonomy" in Q.__all__
    assert "quaternion_conjugate" in Q.__all__


def test_tool_schema_entry_present():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.qm.quaternion.quaternion_cycle_holonomy" in names
    assert "srmech.qm.quaternion.quaternion_conjugate" in names
