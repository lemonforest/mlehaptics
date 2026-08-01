"""test_immolation — the NAMED release gate (rc131): introspection HONESTY +
the numpy-immolation guard, numpy-FREE.

**The established sister-package name.** ephemerides-spectral and
antikythera-spectral each ship a ``test_immolation.py`` as their release gate;
srmech gains its own here. The name is load-bearing: numpy was DELETED from
srmech in #564, and this file is the standing proof that the package never
advertises — nor silently produces — a return type it can no longer make.

**Why this file exists.** srmech's ``describe()`` / tool schema is its Class-H
self-recognition surface. Before rc131 it advertised ``returns = "np.ndarray"``
for 88 ops even though numpy is gone — every one a false self-description. The
§10.1 every-tool smoke in ``test_mcp.py`` held each op's ``raw`` return but only
serialise-checked it; it never asserted ``type(raw)`` AGREES with the advertised
``returns.type``. This file closes that gap and makes it permanent.

It asserts three things, all numpy-absent:

1. **Return-type honesty** — for EVERY ``mcp_callable`` ToolEntry: synth args,
   ``invoke_tool``, and when the op returns cleanly assert ``type(raw)`` agrees
   with the advertised ``returns.type`` (carrier-aware: ``Mat`` / ``Vec`` / ``HV``
   / ``array`` / ``list`` / ``tuple`` / scalar). Domain / binding errors on synth
   data are TOLERATED — same tolerance as test_mcp's §10.1 (can't observe a type
   from an op that legitimately rejects the minimal synth input).
2. **The immolation guard** — NO advertised ``returns.type`` anywhere in the
   registry contains the token ``ndarray``. numpy is gone; a permanent ratchet.
3. **The carrier idiom-surface contract** — call real carrier-returning ops and
   assert their ``Mat`` / ``Vec`` returns expose the full numpy-idiom surface
   (``.shape`` / ``len`` / iterate / ``m[i, j]`` / ``m[0]`` → ``Vec`` / ``.T`` /
   ``.conj`` / ``.tolist`` / ``.tobytes`` / ``==`` / ``@``). (Folded in from the
   rc130 ``test_carrier_contract_rc130.py``, now retired.)

Like the registry smoke, this module imports only ``srmech`` + stdlib + the
test-local synth harness, so the whole surface is certified reachable with numpy
genuinely absent (a representative slice is re-run with numpy hard-blocked).
"""

from __future__ import annotations

import builtins
from typing import Any

import pytest

from srmech.amsc.tool_schema import get_tool_schema
from srmech.math.mat import Mat
from srmech.math.vec import Vec
from srmech.math import laplacian as L
from srmech.mcp import invoke_tool

# Reuse the SAME synth harness the §10.1 every-tool smoke uses (single source of
# truth for minimal, schema-valid wire values per declared param type). Ensure
# this tests/ directory is importable when test_immolation is collected alone
# (pytest's prepend import-mode adds it, but guard for isolated collection).
import os as _os
import sys as _sys
_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)
# `#T1007` — the advertised-tool list, computed ONCE at collection time in
# test_mcp (warmup_all() + mcp_callable filter). Imported here so the
# return-type honesty gate PARAMETRIZES over the SAME node set as test_mcp's
# every-tool invocation smoke.
from test_mcp import _synth_args_for_entry, _is_binding_error, _ADVERTISED

# The carrier-aware return-type agreement check lives in conftest (shared with
# the §10.1 every-tool smoke; no cross-test import cycle).
from conftest import return_type_agrees as _return_type_agrees


# ──────────────────────────────────────────────────────────────────────
# 1. Return-type HONESTY: every clean return AGREES with its advertised type
#
# `#T1007` — one pytest node PER advertised tool (was a single ~26-min loop over
# every ``mcp_callable`` ToolEntry, an atomic node ``--dist loadfile`` could not
# split — the second-most-expensive test in the pure-Python CI cell). The per-op
# tolerance logic is UNCHANGED: domain / binding errors on synth data are
# TOLERATED (the type is unobservable); a clean return whose observed type
# DISAGREES with the advertised type FAILS. Per-op granularity is the
# improvement — a dishonest op NAMES itself instead of hiding in an accumulated
# list. The two cross-op aggregates (registry not small; the harness drives
# enough clean returns) move to a dedicated guard below.
# ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("entry", _ADVERTISED, ids=lambda e: e.name)
def test_advertised_return_type_is_honest(entry: Any) -> None:
    """For THIS ``mcp_callable`` ToolEntry, synth + invoke; when the op returns
    cleanly assert ``type(raw)`` AGREES with the advertised ``returns.type`` —
    the inspection the §10.1 smoke never did. Domain / binding errors on synth
    data are TOLERATED (the type is unobservable), exactly as §10.1 tolerates
    them. An op with no advertised return type is a no-op node (nothing to
    check), matching the pre-`#T1007` loop's ``if entry.returns is None:
    continue``."""
    if entry.returns is None:
        return
    synth = _synth_args_for_entry(entry)
    try:
        raw = invoke_tool(entry.name, synth)
    except TypeError as exc:
        if _is_binding_error(exc):
            pytest.fail(
                f"{entry.name}: advertised={entry.returns.type!r} :: "
                f"BINDING TypeError: {exc}"
            )
        return  # op-internal TypeError — domain rejection, type unobservable
    except Exception:  # noqa: BLE001 — tolerated domain error (can't observe type)
        return

    agrees = _return_type_agrees(raw, entry.returns.type)
    if agrees is None:
        return  # no assertable token (handle / unknown type)
    if agrees is False:
        pytest.fail(
            f"{entry.name}: advertised={entry.returns.type!r} :: OBSERVED "
            f"{type(raw).__name__!r} does not match advertised (the "
            f"self-description the package can no longer honour)"
        )


def test_return_type_honesty_harness_is_live() -> None:
    """Aggregate sanity split out of the (now parametrized) honesty gate
    (`#T1007`), preserving its two non-per-op assertions: the advertised
    registry is not small (the old ``len(advertised) > 50``), and the synth
    harness can DRIVE enough ops to a clean, type-observable return (the old
    ``checked > 30``). The second guards against a synth-harness regression that
    silently turns every op into a tolerated domain error — which would otherwise
    leave every per-op node green while NOTHING was actually type-checked.

    Bounded on purpose: it iterates the advertised surface only until it has
    observed 35 clean type-checked returns and then STOPS, so in the healthy
    case it costs a handful of fast invokes rather than re-creating the ~26-min
    full-surface scan the per-op parametrization exists to remove. (A genuinely
    degraded surface that never reaches 35 will scan further before failing —
    the expensive path is then the RED one, which is already broken.)"""
    assert len(_ADVERTISED) > 50, "advertised tool registry unexpectedly small"

    checked = 0
    for entry in _ADVERTISED:
        if checked >= 35:
            break
        if entry.returns is None:
            continue
        synth = _synth_args_for_entry(entry)
        try:
            raw = invoke_tool(entry.name, synth)
        except Exception:  # noqa: BLE001 — binding or domain: unobservable here
            continue
        if _return_type_agrees(raw, entry.returns.type) is None:
            continue
        checked += 1

    assert checked > 30, (
        f"only {checked} advertised returns were type-observable before the "
        f"scan bound; the synth harness should drive more — a regression in "
        f"_synth_args_for_entry?"
    )


# ──────────────────────────────────────────────────────────────────────
# 2. THE IMMOLATION GUARD: no advertised return type may name `ndarray`
# ──────────────────────────────────────────────────────────────────────
def test_no_advertised_return_type_names_ndarray() -> None:
    """numpy was DELETED from srmech (#564) — NO advertised ``returns.type`` may
    contain the token ``ndarray``. A permanent down-only guard: the tool schema
    is the package's self-recognition surface and must never claim a carrier it
    cannot produce."""
    schema = get_tool_schema()
    offenders = [
        e.name for e in schema.tools
        if e.returns is not None and "ndarray" in e.returns.type
    ]
    assert offenders == [], (
        "advertised RETURN types still naming the gone numpy ndarray:\n"
        + "\n".join(f"  - {n}" for n in offenders)
    )


def test_no_advertised_param_type_names_ndarray() -> None:
    """numpy was DELETED from srmech (#564) — NO advertised PARAMETER type may
    contain the token ``ndarray`` either (the rc132 lock closing the OTHER half
    of every tool signature). A ``np.ndarray`` in a ``P(...)`` type string is the
    same numpy-inviting lie the return-type guard forbids: it tells a caller / LLM
    / introspection "it's just a numpy array, do the math in numpy". The carrier
    (``Mat`` / ``Vec`` / ``HV`` and their ``Optional`` / ``Sequence`` / ``tuple``
    forms) is the lock — the numpy *spirit* without numpy. A permanent down-only
    ratchet: both sides of every tool signature stay numpy-name-free forever."""
    schema = get_tool_schema()
    offenders = [
        (e.name, p.name, p.type)
        for e in schema.tools
        for p in e.parameters
        if "ndarray" in p.type
    ]
    assert offenders == [], (
        "advertised PARAMETER types still naming the gone numpy ndarray "
        "(an LLM-side invitation to drop srmech and reach for numpy):\n"
        + "\n".join(f"  - {name}.{pname}: {ptype!r}"
                    for name, pname, ptype in offenders)
    )


# ──────────────────────────────────────────────────────────────────────
# 3. The carrier idiom-surface contract (folded in from rc130; now retired)
# ──────────────────────────────────────────────────────────────────────
def _assert_mat_idioms(m, *, expect_shape=None):
    """Assert ``m`` is a :class:`Mat` exposing the full numpy-idiom surface."""
    assert isinstance(m, Mat), f"expected Mat, got {type(m).__name__}"
    nr, nc = m.shape
    assert len(m.shape) == 2
    if expect_shape is not None:
        assert m.shape == expect_shape, (m.shape, expect_shape)
    assert len(m) == nr  # 2-D len == row count (numpy idiom)

    # 2-D scalar index m[i, j] → a PLAIN scalar (never a carrier / numpy scalar)
    if nr and nc:
        assert isinstance(m[0, 0], (int, float, complex))

    # single-index row m[0] → a Vec (the rc130 fix — NOT a bare list, NOT a raise)
    if nr:
        row0 = m[0]
        assert isinstance(row0, Vec), f"m[0] must be a Vec, got {type(row0).__name__}"
        assert row0.shape == (nc,)
        assert row0.tolist() == m.row(0)
        # negative single-index works too
        assert m[-1].tolist() == m.row(nr - 1)

    # iteration yields ROWS (as stdlib lists, numpy-free)
    rows = list(m)
    assert len(rows) == nr
    assert all(isinstance(r, list) for r in rows)

    # transpose (both spellings), conj, tolist, tobytes, value-equality
    assert m.T.shape == (nc, nr)
    assert m.transpose().shape == (nc, nr)
    assert isinstance(m.conj(), Mat)
    assert m.tolist() == [m.row(i) for i in range(nr)]
    assert isinstance(m.tobytes(), bytes)
    assert m == Mat.from_rows(m.tolist(), is_complex=m.is_complex)


def _assert_vec_idioms(v, *, expect_len=None):
    """Assert ``v`` is a :class:`Vec` exposing the full numpy-idiom surface."""
    assert isinstance(v, Vec), f"expected Vec, got {type(v).__name__}"
    (n,) = v.shape  # 1-D shape is a 1-tuple
    if expect_len is not None:
        assert n == expect_len, (n, expect_len)
    assert len(v) == n

    if n:
        assert isinstance(v[0], (int, float, complex))   # scalar index
        assert v[-1] == v.tolist()[-1]                   # negative index
    # iteration yields SCALARS (not rows)
    items = list(v)
    assert len(items) == n
    assert all(isinstance(x, (int, float, complex)) for x in items)

    assert isinstance(v.conj(), Vec)
    assert v.tolist() == list(v)
    assert isinstance(v.tobytes(), bytes)
    assert v == Vec.from_sequence(v.tolist(), is_complex=v.is_complex)


def test_mat_numpy_idiom_surface():
    """A hand-built ``Mat`` exposes ``.shape`` / ``m[i, j]`` / ``m[0]`` → Vec /
    ``@`` — real and complex. The two rc130 gaps (``m[0]`` raised, ``@``
    unsupported) are asserted FIXED here."""
    A = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    _assert_mat_idioms(A, expect_shape=(2, 2))

    B = Mat.from_rows([[5.0, 6.0], [7.0, 8.0]])
    # Mat · Mat → Mat (the rc130 @ matmul fix)
    C = A @ B
    assert isinstance(C, Mat)
    assert C.tolist() == [[19.0, 22.0], [43.0, 50.0]]

    # Mat · Vec → Vec
    v = Vec.from_sequence([1.0, 2.0])
    mv = A @ v
    assert isinstance(mv, Vec)
    assert mv.tolist() == [5.0, 11.0]

    # complex carrier: m[0] preserves the complex layout; matmul stays complex
    Ac = Mat.from_rows([[1j, 2.0], [3.0, 4j]], is_complex=True)
    _assert_mat_idioms(Ac, expect_shape=(2, 2))
    assert Ac[0].is_complex
    vc = Vec.from_sequence([1j, 1.0], is_complex=True)
    out = Ac @ vc
    assert isinstance(out, Vec) and out.is_complex
    assert out.tolist() == [1 + 0j, 7j]


def test_vec_numpy_idiom_surface():
    """A hand-built ``Vec`` exposes ``.shape`` / scalar ``v[i]`` / scalar
    iteration / ``@`` — ``Vec · Vec`` → scalar dot, ``Vec · Mat`` → Vec."""
    v = Vec.from_sequence([1.0, 2.0, 3.0])
    _assert_vec_idioms(v, expect_len=3)

    # Vec · Vec → a PLAIN scalar inner product (the rc130 @ matmul fix)
    d = v @ Vec.from_sequence([4.0, 5.0, 6.0])
    assert isinstance(d, float)
    assert d == 1 * 4 + 2 * 5 + 3 * 6  # 32

    # Vec · Mat → Vec (row-vector · matrix)
    M = Mat.from_rows([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    vm = v @ M  # [1,2,3] · 3x2 = [1+6+15, 2+8+18] = [22, 28]
    assert isinstance(vm, Vec)
    assert vm.tolist() == [22.0, 28.0]


def test_carrier_returning_ops_expose_numpy_idioms_numpy_free():
    """CALL representative carrier-returning registered ops and assert their
    RETURNS expose the documented numpy-idiom surface — the check the registry
    walk cannot do (it never invokes an op). A path-graph ``0-1-2-3``."""
    n = 4
    edges = [(0, 1), (1, 2), (2, 3)]

    # Class-L matrix builders → Mat
    Lap = L.dense_laplacian(n, edges)
    _assert_mat_idioms(Lap, expect_shape=(n, n))
    Adj = L.dense_adjacency(n, edges)
    _assert_mat_idioms(Adj, expect_shape=(n, n))

    # eigenvalues / Fiedler vector → Vec
    eigs = L.jacobi_eigvals(Lap)
    _assert_vec_idioms(eigs, expect_len=n)
    fied = L.fiedler_vector(Lap)
    _assert_vec_idioms(fied, expect_len=n)

    # dense contraction ops → Mat / Vec / scalar
    A = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    B = Mat.from_rows([[5.0, 6.0], [7.0, 8.0]])
    _assert_mat_idioms(L.mat_matmul(A, B), expect_shape=(2, 2))
    _assert_vec_idioms(
        L.mat_matvec(A, Vec.from_sequence([1.0, 1.0])), expect_len=2
    )
    _assert_mat_idioms(
        L.mat_outer([1.0, 2.0, 3.0], [4.0, 5.0]), expect_shape=(3, 2)
    )
    assert isinstance(L.mat_dot([1.0, 2.0], [3.0, 4.0]), float)

    # the rc131 straggler flips return carriers too — dense_solve → Mat / Vec.
    _assert_mat_idioms(
        L.dense_solve([[2.0, 0.0], [0.0, 3.0]], [[1.0, 0.0], [0.0, 1.0]]),
        expect_shape=(2, 2),
    )
    _assert_vec_idioms(
        L.dense_solve([[2.0, 0.0], [0.0, 3.0]], [1.0, 1.0]), expect_len=2
    )

    # and the carrier returns CHAIN through the @ idiom (op-return @ op-return)
    chained = L.dense_laplacian(n, edges) @ L.fiedler_vector(Lap)
    _assert_vec_idioms(chained, expect_len=n)


# ──────────────────────────────────────────────────────────────────────
# 3b. The carrier is AGNOSTIC about input (rc132): a carrier-typed param
#     accepts the carrier OR its degenerate list / tuple / Vec / array form,
#     and the op returns the SAME value either way. This is what makes the
#     advertised carrier honest — it is the numpy *spirit* (accepts every shape
#     the no-math plan used) without numpy.
# ──────────────────────────────────────────────────────────────────────
def test_carrier_typed_params_accept_degenerate_forms_numpy_free():
    """A representative carrier-returning op (per carrier kind) gives the SAME
    result whether fed the CARRIER or its degenerate list / tuple form — proving
    the advertised ``Mat`` / ``Vec`` / ``HV`` param genuinely ACCEPTS the looser
    shapes (list-of-lists, tuple-of-rows, flat list, ``array.array``). numpy-free."""
    from array import array as _array
    from srmech.math.hv import HV
    from srmech.math import hdc

    # ── Mat-typed param (A): a Mat OR list-of-lists OR tuple-of-rows ──
    rows = [[2.0, 0.0], [0.0, 3.0]]
    rhs = [[1.0, 0.0], [0.0, 1.0]]
    as_mat = L.dense_solve(Mat.from_rows(rows), Mat.from_rows(rhs))
    as_list = L.dense_solve(rows, rhs)                       # list-of-lists
    as_tuple = L.dense_solve(tuple(tuple(r) for r in rows),  # tuple-of-rows
                             tuple(tuple(r) for r in rhs))
    assert isinstance(as_mat, Mat) and isinstance(as_list, Mat)
    assert as_mat.tolist() == as_list.tolist() == as_tuple.tolist()

    # ── Mat | Vec-typed RHS (B): a Vec OR a flat list as a 1-D right-hand side ──
    b_vec = L.dense_solve(rows, Vec.from_sequence([1.0, 1.0]))
    b_flat = L.dense_solve(rows, [1.0, 1.0])
    assert isinstance(b_vec, Vec) and isinstance(b_flat, Vec)
    assert b_vec.tolist() == b_flat.tolist()

    # ── Vec-typed param (matvec v): a Vec OR flat list OR tuple OR array.array ──
    M = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    base = L.mat_matvec(M, Vec.from_sequence([1.0, 1.0]))
    flat = L.mat_matvec(M, [1.0, 1.0])               # flat list
    tup = L.mat_matvec(M, (1.0, 1.0))                # flat tuple
    arr = L.mat_matvec(M, _array("d", [1.0, 1.0]))   # array.array
    assert isinstance(base, Vec)
    assert base.tolist() == flat.tolist() == tup.tolist() == arr.tolist()

    # ── HV-typed param (klein4 byte carrier): an HV OR flat int list OR
    #    array.array OR tuple — bind is value-identical across all forms ──
    a_list = [0, 1, 2, 3, 0, 1, 2, 3]
    b_list = [1, 1, 1, 1, 0, 0, 0, 0]
    r_list = hdc.klein4_bind(a_list, b_list)                # flat int lists
    r_hv = hdc.klein4_bind(HV.from_sequence(a_list),        # HV carriers
                           HV.from_sequence(b_list))
    r_tup = hdc.klein4_bind(tuple(a_list), tuple(b_list))   # flat tuples
    r_arr = hdc.klein4_bind(_array("B", a_list), _array("B", b_list))  # array
    assert isinstance(r_list, HV)
    assert r_list.tolist() == r_hv.tolist() == r_tup.tolist() == r_arr.tolist()

    # ── HV-typed param (octonion power-of-two float carrier): an HV/list/tuple
    #    of the same length-8 vector binds identically (the loop_bind family) ──
    x = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # the octonion identity e0
    y = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    p_list = hdc.loop_bind(x, y)
    p_tup = hdc.loop_bind(tuple(x), tuple(y))
    p_vec = hdc.loop_bind(Vec.from_sequence(x), Vec.from_sequence(y))
    assert p_list == p_tup == p_vec  # e0 · e1 = e1, same for every input form


def test_carrier_coercers_produce_op_accepted_structures_numpy_free():
    """The MCP inbound coercer for each carrier type produces a structure the
    underlying numpy-free op ACCEPTS — the wire-path proof that the advertised
    carrier is callable end-to-end. ``Vec`` / ``HV`` coercers yield a flat list,
    ``Mat`` a nested list, all of which the agnostic ops consume. numpy-free."""
    from srmech.mcp._coercion import coerce_param

    # Vec wire form (flat JSON list) -> a flat Python list the matvec op accepts.
    v = coerce_param([1.0, 1.0], "Vec")
    assert isinstance(v, list) and v == [1.0, 1.0]
    # HV wire form (flat JSON int list) -> a flat list the klein4 op accepts.
    h = coerce_param([0, 1, 2, 3], "HV")
    assert isinstance(h, list) and h == [0, 1, 2, 3]
    # Mat wire form (nested JSON list) -> a real Mat carrier.
    m = coerce_param([[1.0, 0.0], [0.0, 1.0]], "Mat")
    assert isinstance(m, Mat) and m.shape == (2, 2)
    # the produced structures drive a real op cleanly via the SAME wire forms.
    M = coerce_param([[1.0, 2.0], [3.0, 4.0]], "Mat")
    out = L.mat_matvec(M, coerce_param([1.0, 1.0], "Vec"))
    assert isinstance(out, Vec) and out.tolist() == [3.0, 7.0]


# ──────────────────────────────────────────────────────────────────────
# 4. The whole gate runs with numpy HARD-BLOCKED at import
# ──────────────────────────────────────────────────────────────────────
def test_immolation_is_itself_numpy_free():
    """Re-run a representative slice (return-type honesty on a carrier-flipped
    op, the immolation guard, and the carrier idiom surface) with numpy hard-
    blocked at import — this file is part of the numpy-FREE surface it certifies,
    #564. Mirrors the ``builtins.__import__`` block pattern in
    ``test_carrier_contract_rc130`` / ``test_registry_smoke_rc127``."""
    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "numpy" or name.startswith("numpy."):
            raise ImportError("numpy is removed (#564 numpy-zero gate)")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = _blocked
    try:
        # (a) immolation guard holds numpy-absent — BOTH halves of every tool
        #     signature: no advertised RETURN nor PARAMETER type names ndarray.
        schema = get_tool_schema()
        assert not any(
            e.returns is not None and "ndarray" in e.returns.type
            for e in schema.tools
        )
        assert not any(
            "ndarray" in p.type
            for e in schema.tools for p in e.parameters
        )
        # (b) a carrier-flipped op invoked via the wire path returns the carrier,
        #     and the observed type AGREES with the advertised type — numpy-absent.
        entry = schema.lookup("srmech.math.laplacian.dense_solve")
        assert entry is not None
        raw = invoke_tool(
            "srmech.math.laplacian.dense_solve",
            {"A": [[2.0, 0.0], [0.0, 3.0]], "B": [[1.0, 0.0], [0.0, 1.0]]},
        )
        assert isinstance(raw, Mat)
        assert _return_type_agrees(raw, entry.returns.type) is True
        # (c) the carrier idiom surface needs no numpy
        A = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
        _assert_mat_idioms(A, expect_shape=(2, 2))
        assert isinstance(A[0], Vec)         # m[0] → Vec, numpy-absent
        assert isinstance(A @ A, Mat)        # @ matmul, numpy-absent
        v = Vec.from_sequence([1.0, 2.0])
        _assert_vec_idioms(v, expect_len=2)
        assert isinstance(v @ v, float)      # Vec@Vec dot, numpy-absent
        Lap = L.dense_laplacian(3, [(0, 1), (1, 2)])
        _assert_mat_idioms(Lap, expect_shape=(3, 3))
    finally:
        builtins.__import__ = real_import
