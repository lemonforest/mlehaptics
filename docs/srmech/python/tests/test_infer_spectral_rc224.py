"""rc224 — #796 CLOSED: the SPECTRAL infer row dispatches in C via the EXACT
operator-level verdict.

The naive spectral row would be a FLOAT eigensolve with a within-tolerance
verdict — wrong (last-ULP cross-platform divergence). rc224 ships the exact
design instead: **the spectral verdict is an exact operator-level structural
fact — the reduction EXISTS iff L is real-symmetric** (the spectral theorem's
own hypothesis), checked BIT-EXACT (``L[i][j] == L[j][i]`` IEEE equality over
all pairs). The old ``Λ² ≈ L·L`` float check was a TAUTOLOGY of the spectral
theorem (``l1·l1 == l2`` exactly whenever ``VᵀV = I``) — in float it was only
an eigensolve-quality gate, and it agreed 400/400 with the exact symmetry
predicate over random symmetric Laplacians. The eigenvalues are the OPERAND
(the ``resonant_spectrum`` payload), never the verdict.

The C peer (``srmech_infer.c``): the payload's f64 leaves ride the wire as
IEEE-754 BIT PATTERNS (signed int64 — no decimal float parse in the decision
path); L is built in C (edges → the Class-L ``srmech_graph_dense_laplacian``
kernel, the SAME builder the pure path dispatches to; matrix → the raw grid;
adjacency → the in-place D−A transform in the pure ``_build_laplacian``'s
exact float-op order); the verdict is the bit-exact symmetry predicate — NO
eigensolve, NO ``resonant_spectrum`` call, NO float tolerance in the C
decision path. Non-finite payload leaves are NOT marshalled (→ pure), so the
native decision is PROVABLY identical to the pure decision on every platform
(finite accumulation can overflow to ±inf but never to NaN, and only a NaN
breaks an entry's IEEE self-equality).

This test pins:
  (1) PARITY — native infer verdict == pure infer verdict for the edges /
      explicit-matrix / adjacency reducible cases, the explicit ASYMMETRIC
      matrix (OPEN on both), and a non-spectral payload (stays OPEN). The
      VERDICT fields (reducible/row/reducer/verified + the OPEN shape) are
      asserted identical; float-eigenvalue identity is NOT asserted (the
      eigenvalues are payload).
  (2) THE EXACTNESS PROOF — the C verdict is a pure function of the bit-exact
      symmetry of L: two symmetric Laplacians with wildly different spectra
      (1e−200-scale vs 1e+200-scale) both give reducible:true from the raw C
      decision (no eigensolve in C — no overflow either), and a 1-ULP nudge of
      ONE off-diagonal entry flips the verdict to the definitive
      reducible:false on BOTH arms.
  (3) native == pure over a deterministic battery of small random symmetric
      Laplacians (edges+weights form AND the explicit-matrix form of the same
      L), plus their 1-ULP-perturbed asymmetric twins.
  (4) The safety rails: non-finite payloads decline the marshal (→ pure);
      a monstrous n declines past SRMECH_INFER_WS_CEILING_MB (→ pure); a
      malformed payload falls to pure — never a fabricated decision.

numpy-FREE and math-FREE (stdlib struct for the IEEE bit patterns — the same
wire transform the marshal uses).
"""

from __future__ import annotations

import copy
import os
import random
import struct

import pytest

from srmech.amsc import _native
from srmech.math import laplacian as _L
from srmech.math.dispatch import infer, _marshal_relationship


# ── helpers ───────────────────────────────────────────────────────────────────
def _infer_with(relationship, native_on):
    """Run infer() with the native path forced on/off (the parity toggle)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = native_on and saved   # can't fabricate native
        return infer(copy.deepcopy(relationship))
    finally:
        _native.HAS_NATIVE = saved


def _verdict(d):
    """The full VERDICT signature of an infer() result (never the float
    eigenvalue payload)."""
    return (d["reducible"], d["row"], d.get("reducer"), d.get("verified"),
            d.get("reason"), d.get("candidate_next_theory"))


def _ulp_up(x: float) -> float:
    """x nudged by exactly one ULP (via the IEEE-754 bit pattern)."""
    b = struct.unpack("<q", struct.pack("<d", x))[0]
    return struct.unpack("<d", struct.pack("<q", b + 1))[0]


# ── fixtures ──────────────────────────────────────────────────────────────────
_P4_EDGES = {"edges": [(0, 1), (1, 2), (2, 3)], "n": 4}
_W_EDGES = {"edges": [(0, 1), (1, 2)], "weights": [0.25, 3.5], "n": 3}
_P3_LAP = {"laplacian": [[1.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0, 1.0]]}
_SYM_MAT = {"matrix": [[2.0, -0.5, 0.0], [-0.5, 1.0, 0.25], [0.0, 0.25, 3.0]]}
_ASYM_MAT = {"matrix": [[1.0, 2.0], [3.0, 1.0]]}
_ADJ_TRI = {"row": "spectral", "adjacency": [[0, 1, 1], [1, 0, 1], [1, 1, 0]]}
_ADJ_ASYM = {"adjacency": [[0.0, 1.0], [2.0, 0.0]]}
_NON_SPECTRAL = {"nonsense": 1}

_REDUCIBLE = {"edges-P4": _P4_EDGES, "edges-weights": _W_EDGES,
              "laplacian-P3": _P3_LAP, "matrix-sym": _SYM_MAT,
              "adjacency-tri": _ADJ_TRI}
_OPEN = {"matrix-asym": _ASYM_MAT, "adjacency-asym": _ADJ_ASYM,
         "non-spectral": _NON_SPECTRAL}


# ── (1) PARITY: native verdict == pure verdict, byte-identical ────────────────
@pytest.mark.parametrize("name", sorted(_REDUCIBLE) + sorted(_OPEN))
def test_native_verdict_equals_pure_verdict(name):
    rel = {**_REDUCIBLE, **_OPEN}[name]
    nat = _infer_with(rel, native_on=True)
    pur = _infer_with(rel, native_on=False)
    assert _verdict(nat) == _verdict(pur), (
        f"{name}: native {_verdict(nat)} != pure {_verdict(pur)}")


@pytest.mark.parametrize("name", sorted(_REDUCIBLE))
def test_reducible_row_reducer_verified(name):
    out = _infer_with(_REDUCIBLE[name], native_on=True)
    assert out["reducible"] is True
    assert out["row"] == "spectral"
    assert out["reducer"] == "resonant_spectrum"
    assert out["verified"] is True
    # the closed form IS the resonant_spectrum payload (the operand).
    assert set(out["closed_form"].keys()) == {"tensions", "modes",
                                              "force_orders", "resonances"}


@pytest.mark.parametrize("name", sorted(_OPEN))
def test_open_stays_open_on_both_arms(name):
    for on in (True, False):
        out = _infer_with(_OPEN[name], native_on=on)
        assert out["reducible"] is False
        assert out["row"] is None
        assert out["reason"] == "not reducible in current vocabulary"
        assert out["candidate_next_theory"]


# ── (2) THE EXACTNESS PROOF: verdict = f(symmetry) only ───────────────────────
@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_spectral_row_native_present():
    assert _native.has_native_spectral_row() is True


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_c_verdict_independent_of_eigenvalue_magnitudes():
    """Two symmetric Laplacians with WILDLY different spectra (~1e-200 vs
    ~1e+200 — 400 orders of magnitude apart, far outside any eigensolve's
    comfort) both come back reducible:true from the RAW C decision: the C
    path never runs an eigensolve, so no magnitude can perturb the verdict."""
    tiny = {"matrix": [[1e-200, 0.0], [0.0, 2e-200]]}
    huge = {"matrix": [[1e200, -1e199], [-1e199, 3e200]]}
    for rel in (tiny, huge):
        m = _marshal_relationship(rel)
        assert m is not None
        d = _native.infer_c(*m)
        assert d == {"reducer": "resonant_spectrum", "reducible": True,
                     "row": "spectral", "verified": True}


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_one_ulp_asymmetry_flips_the_c_verdict():
    """The verdict is BIT-exact: nudging ONE mirrored off-diagonal entry by a
    single ULP flips the raw C decision from the verified reduction to the
    DEFINITIVE reducible:false — and the pure predicate reads the same."""
    x = 0.1 + 0.2                        # a non-representable-decimal double
    sym = {"matrix": [[1.0, x], [x, 1.0]]}
    asym = {"matrix": [[1.0, x], [_ulp_up(x), 1.0]]}
    d_sym = _native.infer_c(*_marshal_relationship(sym))
    d_asym = _native.infer_c(*_marshal_relationship(asym))
    assert d_sym["reducible"] is True
    assert d_asym == {"reducible": False, "row": "spectral"}
    assert _infer_with(sym, False)["reducible"] is True
    assert _infer_with(asym, False)["reducible"] is False
    assert _verdict(_infer_with(asym, True)) == _verdict(_infer_with(asym, False))


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
@pytest.mark.parametrize("name,expect", [
    ("edges-P4", True), ("laplacian-P3", True), ("adjacency-tri", True),
    ("matrix-asym", False), ("adjacency-asym", False)])
def test_c_row_genuinely_engaged(name, expect):
    """The spectral row really RUNS in C: the raw decision is the structural
    verdict literal (both polarities are DEFINITIVE for this row — the C-built
    L is entry-for-entry the pure build)."""
    rel = {**_REDUCIBLE, **_OPEN}[name]
    m = _marshal_relationship(rel)
    assert m is not None, f"{name} should marshal"
    d = _native.infer_c(*m)
    if expect:
        assert d == {"reducer": "resonant_spectrum", "reducible": True,
                     "row": "spectral", "verified": True}
    else:
        assert d == {"reducible": False, "row": "spectral"}


def test_wire_is_bit_patterns_not_decimal_floats():
    """The marshalled wire carries ONLY int64 IEEE bit patterns for f64 leaves
    (never a JSON decimal float — no strtod in the decision path); −0.0 rides
    as INT64_MIN, bit-exactly."""
    m = _marshal_relationship({"matrix": [[1.0, -0.0], [0.0, 1.0]]})
    assert m is not None
    wire, n = m
    assert n == 2
    assert "." not in wire               # no decimal floats anywhere
    assert str(-(2 ** 63)) in wire       # −0.0 == INT64_MIN bit pattern
    assert str(struct.unpack("<q", struct.pack("<d", 1.0))[0]) in wire


# ── (3) the deterministic battery ─────────────────────────────────────────────
def test_battery_native_equals_pure_random_symmetric_laplacians():
    """Over a seeded battery of small random weighted graphs: the native and
    pure verdicts agree on the edges form, on the explicit-matrix form of the
    SAME L, and on a 1-ULP-perturbed asymmetric twin (OPEN on both)."""
    rng = random.Random(20260712)
    for trial in range(40):
        n = rng.randint(2, 8)
        edges, weights = [], []
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < 0.6:
                    edges.append((i, j))
                    weights.append(round(rng.uniform(-3, 3), 6))
        rel = {"edges": edges, "weights": weights, "n": n}
        nat, pur = _infer_with(rel, True), _infer_with(rel, False)
        assert _verdict(nat) == _verdict(pur), (trial, "edges", rel)
        assert nat["reducible"] is True          # dense_laplacian is symmetric
        # the explicit-matrix form of the same L
        L = _L.dense_laplacian(n, edges, weights)
        rows = [[L[i, j] for j in range(n)] for i in range(n)]
        nat_m, pur_m = (_infer_with({"matrix": rows}, True),
                        _infer_with({"matrix": rows}, False))
        assert _verdict(nat_m) == _verdict(pur_m), (trial, "matrix")
        assert nat_m["reducible"] is True
        # a 1-ULP asymmetric twin (perturb one strict off-diagonal entry)
        if n >= 2 and rows[0][1] == rows[1][0]:
            rows_p = [list(r) for r in rows]
            rows_p[0][1] = _ulp_up(rows_p[0][1])
            nat_p, pur_p = (_infer_with({"matrix": rows_p}, True),
                            _infer_with({"matrix": rows_p}, False))
            assert _verdict(nat_p) == _verdict(pur_p), (trial, "perturbed")
            assert nat_p["reducible"] is False


# ── (4) the safety rails ──────────────────────────────────────────────────────
def test_non_finite_payload_declines_marshal_and_falls_to_pure():
    """A NaN / inf leaf is NOT marshalled (the bit-exactness proof assumes
    finite leaves), so the native path falls to pure — and infer() lands the
    same verdict on both arms (a NaN Laplacian is never symmetric: the IEEE
    self-compare fails)."""
    for bad in (float("nan"), float("inf"), float("-inf")):
        rel = {"edges": [(0, 1)], "weights": [bad], "n": 2}
        with pytest.raises(ValueError):
            _marshal_relationship(rel)           # infer() catches this → pure
        nat, pur = _infer_with(rel, True), _infer_with(rel, False)
        assert _verdict(nat) == _verdict(pur)
    # NaN specifically: asymmetric-by-self-compare → OPEN on both arms.
    rel = {"matrix": [[float("nan"), 0.0], [0.0, 1.0]]}
    nat, pur = _infer_with(rel, True), _infer_with(rel, False)
    assert _verdict(nat) == _verdict(pur) and nat["reducible"] is False


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_monstrous_n_declines_past_ceiling_to_pure():
    """An n whose n×n grid would blow the SRMECH_INFER_WS_CEILING_MB arena
    ceiling (default 256) declines the native path (infer_c → None) — the
    pure path owns the allocation question."""
    if os.environ.get("SRMECH_INFER_WS_CEILING_MB"):
        pytest.skip("ceiling overridden in this environment")
    m = _marshal_relationship({"edges": [[0, 9999]], "n": 10000})
    assert m is not None
    assert _native.infer_c(*m) is None


def test_malformed_spectral_payloads_stay_open_on_both_arms():
    """Unbuildable payloads (ragged grid / empty grid / out-of-range edge /
    weight-length mismatch / n=0) land the SAME honest OPEN on both arms —
    never a fabricated decision."""
    bads = [
        {"matrix": [[1.0, 2.0], [2.0]]},               # ragged
        {"matrix": []},                                 # empty
        {"edges": [(0, 5)], "n": 2},                    # node out of range
        {"edges": [(0, 1)], "weights": [1.0, 2.0], "n": 2},  # length mismatch
        {"row": "spectral"},                            # no payload at all
    ]
    for rel in bads:
        nat, pur = _infer_with(rel, True), _infer_with(rel, False)
        assert _verdict(nat) == _verdict(pur), rel
        assert nat["reducible"] is False and nat["row"] is None


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native lib")
def test_spectral_sizer_bound_and_monotone():
    """The dedicated rc224 sizer is bound, distinct, and monotone in n (and it
    declines an absurd n with a SIZE_MAX-shaped answer, never a wrapped one)."""
    import ctypes
    sz = _native.LIB.srmech_infer_spectral_arena_bytes
    small = int(sz(ctypes.c_size_t(64), ctypes.c_size_t(4)))
    big = int(sz(ctypes.c_size_t(64), ctypes.c_size_t(512)))
    assert 0 < small < big
    absurd = int(sz(ctypes.c_size_t(64), ctypes.c_size_t(2 ** 40)))
    assert absurd >= big                                # declined, not wrapped
