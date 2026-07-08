"""rc181 — the DSL chain interpreter FOUNDATION → C (ANNEX Batch B pt1).

Pins ``srmech_dsl_chain_run`` (srmech_dsl_chain_run.c): the F1 carrier-FFI +
the leaf-dispatch table (``lookup_cascade_op``) + the ``build_chain_from_dict``
stage-IR grammar + the LINEAR ``chain.run`` value-thread over the C-backed
cascade atoms.

Parity contract: for an eligible LINEAR chain over a C-backed leaf, the native
run (``Chain._run_native``) == the pure run (with the native lib disabled) —
byte-exact for the structural / exact atoms (chiral_flip / net_chirality /
pin_slot_at_zero / best_rational_signed / reorient), WITHIN-TOL for the numeric
ones (magnitude / autocorrelation are f64). A combinator stage, a non-C leaf, or
an unsupported carrier → the C peer returns non-OK → the pure path runs (rc103
inform-don't-limit). ABI stays 4 (additive symbols).

numpy-free (stdlib json/math + pytest.approx).
"""
from __future__ import annotations

import math

import pytest

from srmech.amsc import _native
from srmech.dsl import chain
from srmech.dsl._chain import _NATIVE_MISS, _desc_to_value, _value_to_desc

_HAS = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dsl_chain_run")
    and hasattr(_native.LIB, "srmech_dsl_chain_run_arena_bytes")
)
_needs_native = pytest.mark.skipif(
    not _HAS, reason="native srmech_dsl_chain_run not present (pure-only build)"
)


class _no_native:
    """Context manager: disable the native lib so a Chain.run takes the PURE path.

    ``Chain._run_native`` reads ``_native.HAS_NATIVE`` fresh each call, so flipping
    it here forces both the DSL runner AND the per-atom native dispatch onto their
    pure-Python fallbacks — the reference for the native==pure comparison.
    """

    def __enter__(self):
        self._saved = _native.HAS_NATIVE
        _native.HAS_NATIVE = False
        return self

    def __exit__(self, *exc):
        _native.HAS_NATIVE = self._saved
        return False


def _pure(ch, inp):
    with _no_native():
        return ch.run(inp)


# ─────────────────────────────────────────────────────────────────────
# Symbol surface + ABI
# ─────────────────────────────────────────────────────────────────────


@_needs_native
def test_symbols_bound_and_abi_4():
    assert hasattr(_native.LIB, "srmech_dsl_chain_run")
    assert hasattr(_native.LIB, "srmech_dsl_chain_run_arena_bytes")
    assert _native.NATIVE_ABI_VERSION == 4


# ─────────────────────────────────────────────────────────────────────
# F1 carrier round-trip (the shared carrier-FFI bedrock)
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("v", [
    None, 0, 5, -7, 2 ** 62, 3.14, -2.5, 0.0, "hi", "",
    [1, 2, 3], [1.0, -2.0, 3.5], (1, 2), (1.0, 2.0),
    [], (), [[1, 2], [3, 4]], [1, 2.0, "x", None],
])
def test_f1_descriptor_round_trip(v):
    """Every F1-representable value marshals to a descriptor + rebuilds equal
    (the Python side of the shared carrier-FFI; C uses the same wire format)."""
    desc = _value_to_desc(v)
    assert desc is not None
    assert _desc_to_value(desc) == v


@pytest.mark.parametrize("v", [
    True, False, 2 ** 70, -(2 ** 70), b"bytes", {"a": 1}, 1 + 2j,
])
def test_f1_unsupported_defers(v):
    """A non-F1 shape (bool / out-of-int64 / bytes / dict / complex) → None →
    the whole chain defers to pure."""
    assert _value_to_desc(v) is None


# ─────────────────────────────────────────────────────────────────────
# native == pure over shipped LINEAR chains
# ─────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("x", [-3.14, 3.14, 0.0, -0.0, 2.5, -100.25])
def test_magnitude_native_eq_pure(x):
    ch = chain("mag").then("magnitude")
    native = ch._run_native(x)
    assert native is not _NATIVE_MISS
    assert native == pytest.approx(_pure(ch, x))


@_needs_native
@pytest.mark.parametrize("seq", [
    [1, 2, 3, 4], [5, -6, 7], (1, 2, 3), [10],
    [1.0, 2.0, 3.0], (1.5, -2.5, 3.5),
])
def test_chiral_flip_native_eq_pure_type_preserving(seq):
    ch = chain("flip").then("chiral_flip")
    native = ch._run_native(seq)
    assert native is not _NATIVE_MISS
    pure = _pure(ch, seq)
    assert native == pure
    assert type(native) is type(pure)          # list stays list, tuple stays tuple


@_needs_native
@pytest.mark.parametrize("seq", [[1, -1, 1], (1, 1, -1, -1), [1, 0, -1], [1], []])
def test_net_chirality_native_eq_pure(seq):
    ch = chain("net").then("net_chirality")
    native = ch._run_native(seq)
    assert native is not _NATIVE_MISS
    pure = _pure(ch, seq)
    assert native == pure and type(native) is int


@_needs_native
@pytest.mark.parametrize("x", [-3.14, 3.14, 0.0, 5.5, -0.001])
def test_pin_slot_native_eq_pure_tuple(x):
    ch = chain("pin").then("pin_slot_at_zero")
    native = ch._run_native(x)
    assert native is not _NATIVE_MISS
    pure = _pure(ch, x)
    assert native == pure and type(native) is tuple


@_needs_native
@pytest.mark.parametrize("x", [-3.14159, 0.5, 2.0, -0.3333])
def test_best_rational_signed_native_eq_pure(x):
    ch = chain("br").then("best_rational_signed", max_denominator=1000)
    native = ch._run_native(x)
    assert native is not _NATIVE_MISS
    pure = _pure(ch, x)
    assert native == pure and type(native) is tuple


@_needs_native
@pytest.mark.parametrize("x,orient", [(5.0, -1), (5.0, 1), (7, -1), (7, 1), (-3, -1)])
def test_reorient_native_eq_pure(x, orient):
    ch = chain("re").then("reorient", orientation=orient)
    native = ch._run_native(x)
    assert native is not _NATIVE_MISS
    pure = _pure(ch, x)
    assert native == pure and type(native) is type(pure)


@_needs_native
@pytest.mark.parametrize("seq", [[1.0, 2.0, 3.0, 4.0], [1, 2, 3], [2.5, -1.5]])
def test_autocorrelation_native_within_tol(seq):
    """autocorrelation is f64 — native (direct O(n²) sum) vs pure agree WITHIN
    TOL (~1e-9), NOT byte-identical (the rc171 numeric-atom lesson)."""
    ch = chain("ac").then("autocorrelation")
    native = ch._run_native(seq)
    assert native is not _NATIVE_MISS
    pure = _pure(ch, seq)
    assert native == pytest.approx(pure, rel=1e-9, abs=1e-9)


@_needs_native
def test_multi_stage_linear_then_thread():
    """A multi-stage `.then()`-thread runs end-to-end in C: the value threads
    prev-output → next-input through the C-backed atoms."""
    # magnitude then best_rational_signed: -3.14 -> 3.14 -> (num, den)
    ch = chain("m2b").then("magnitude").then("best_rational_signed", max_denominator=100)
    native = ch._run_native(-3.14)
    assert native is not _NATIVE_MISS
    assert native == _pure(ch, -3.14)
    # chiral_flip then net_chirality: reversal then net handedness
    ch2 = chain("f2n").then("chiral_flip").then("net_chirality")
    native2 = ch2._run_native([1, -1, 1])
    assert native2 is not _NATIVE_MISS
    assert native2 == _pure(ch2, [1, -1, 1])


@_needs_native
def test_full_run_uses_native_and_matches_pure():
    """The public Chain.run (not just _run_native) matches the pure run."""
    ch = chain("run").then("magnitude")
    assert ch.run(-3.14) == pytest.approx(_pure(ch, -3.14))
    ch2 = chain("run2").then("chiral_flip")
    assert ch2.run([1, 2, 3]) == _pure(ch2, [1, 2, 3])


# ─────────────────────────────────────────────────────────────────────
# defer-to-pure: combinators, non-C leaves, unsupported carriers
# ─────────────────────────────────────────────────────────────────────


@_needs_native
def test_combinator_chain_defers_to_pure():
    """A loop / fold / reduce / parallel combinator stage → _run_native miss →
    the pure combinator path runs (rc182 adds the combinators to C)."""
    looped = chain("loop").loop(3, chain("body").then("magnitude"))
    assert looped._run_native(-2.0) is _NATIVE_MISS
    # and the pure path still runs correctly (magnitude of a magnitude ...):
    assert looped.run(-2.0) == pytest.approx(2.0)
    folded = chain("fold").fold(0, "cyclic_gcd")
    assert folded._run_native([12, 18]) is _NATIVE_MISS
    reduced = chain("red").reduce("cyclic_gcd")
    assert reduced._run_native([12, 18, 24]) is _NATIVE_MISS


@_needs_native
def test_non_c_leaf_defers_to_pure():
    """A cascade op with NO C leaf in the table (chiral_dual / kuramoto_step /
    quaternion_dft / octonion_dft) → the C peer returns non-OK → _run_native
    miss (the whole chain defers to the pure runner)."""
    for op in ("chiral_dual", "kuramoto_step", "quaternion_dft", "octonion_dft"):
        ch = chain("nc").then(op)
        assert ch._run_native([1.0, 2.0, 3.0, 4.0]) is _NATIVE_MISS


@_needs_native
def test_unsupported_carrier_for_c_leaf_defers():
    """A C-backed leaf handed a carrier its strict path does not cover → the C
    peer returns non-OK → pure. magnitude(int) stays int on the pure path."""
    ch = chain("mi").then("magnitude")
    assert ch._run_native(5) is _NATIVE_MISS          # int seed -> C defers
    assert ch.run(5) == 5 and type(ch.run(5)) is int  # pure magnitude(int) -> int


@_needs_native
def test_out_of_int64_seed_defers():
    """A seed outside int64 (or a mixed / non-numeric list) → Python marshal
    returns None → _run_native miss → pure."""
    ch = chain("big").then("chiral_flip")
    assert ch._run_native([2 ** 70, 1]) is _NATIVE_MISS
    # a mixed-type list is not a homogeneous C chiral_flip -> C defers -> pure:
    ch2 = chain("mix").then("chiral_flip")
    assert ch2._run_native([1, 2.0, 3]) is _NATIVE_MISS
    assert ch2.run([1, 2.0, 3]) == [3, 2.0, 1]        # pure seq[::-1]


@_needs_native
def test_empty_chain_is_pure_identity():
    """An empty chain is the identity — _run_native declines (pure returns the
    seed unchanged)."""
    ch = chain("id")
    assert ch._run_native(42) is _NATIVE_MISS
    assert ch.run(42) == 42


def test_marshal_helpers_importable_without_native():
    """The F1 marshal helpers are pure-Python (usable in a numpy/native-absent
    build) — the carrier-FFI wire format is not gated on HAS_NATIVE."""
    assert _value_to_desc([1, 2.0, (3, 4)]) == {
        "k": "l", "v": [
            {"k": "i", "v": 1}, {"k": "f", "v": 2.0},
            {"k": "t", "v": [{"k": "i", "v": 3}, {"k": "i", "v": 4}]},
        ],
    }
    assert math.isclose(_desc_to_value({"k": "f", "v": 1.5}), 1.5)
