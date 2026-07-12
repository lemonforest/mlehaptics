"""rc182 — the DSL chain interpreter COMPLETE → C (ANNEX Batch B pt2).

Pins the loop / fold / reduce COMBINATORS completing ``srmech_dsl_chain_run``
(srmech_dsl_chain_run.c) + the TOML front-end bridge
``srmech_dsl_toml_chain_to_json``:

* loop   {"loop_n":N,"sub_chain":[..]} — value-thread the sub-chain N times
         (bounded count + bounded nesting; the loop re-enters the stage-runner).
* fold   {"fold_init":<scalar>,"fold_op":<op>} — acc = seed; fold a C-backed
         BINARY body (cyclic_gcd) over the input LIST.
* reduce {"reduce_op":<op>} — acc = list[0]; fold the binary body over the rest.
* TOML   srmech_dsl_toml_chain_to_json parses a `[chain]` + `[[stage]]` spec via
         the C srmech_toml parser → the build_chain_from_dict IR (canonical JSON).

Parity contract: for a combinator chain over a C-backed body, the native run
(``Chain._run_native`` / ``run_toml_chain``) == the pure run (native lib
disabled) — byte-exact for the exact/structural atoms (chiral_flip / cyclic_gcd),
WITHIN-TOL for the numeric ones (magnitude f64). A `parallel` fan-out, a non-C
body, or an unsupported carrier → the C peer returns non-OK → the pure path runs
(rc103 inform-don't-limit). ABI stays 4 (additive symbols).

numpy-free (stdlib json/math + pytest.approx; the DSL is numpy-free).
"""
from __future__ import annotations

import json
import math

import pytest

from srmech.amsc import _native
from srmech.dsl import chain, run_toml_chain
from srmech.dsl._chain import _NATIVE_MISS
from srmech.dsl._toml_chain import (
    _toml_loads_native,
    build_chain_from_toml_str,
)

_HAS = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dsl_chain_run")
)
_HAS_TOML = _HAS and hasattr(_native.LIB, "srmech_dsl_toml_chain_to_json")
_needs_native = pytest.mark.skipif(
    not _HAS, reason="native srmech_dsl_chain_run not present (pure-only build)"
)
_needs_toml = pytest.mark.skipif(
    not _HAS_TOML, reason="native srmech_dsl_toml_chain_to_json not present"
)


class _no_native:
    """Disable the native lib so a Chain.run / run_toml_chain takes the PURE path."""

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
# symbol surface
# ─────────────────────────────────────────────────────────────────────


@_needs_toml
def test_toml_bridge_symbols_bound_and_abi_4():
    assert hasattr(_native.LIB, "srmech_dsl_toml_chain_to_json")
    assert hasattr(_native.LIB, "srmech_dsl_toml_chain_to_json_arena_bytes")
    assert _native.NATIVE_ABI_VERSION == 4


def test_no_combinator_defer_pin_present():
    """The rc181 'combinator defers to pure' pin is INVERTED — no live test asserts
    a loop/fold/reduce chain _run_native returns _NATIVE_MISS (rc182 makes them
    nativize). This guards against a stale deferral pin creeping back."""
    import pathlib
    here = pathlib.Path(__file__).resolve().parent
    src = (here / "test_dsl_chain_c_rc181.py").read_text(encoding="utf-8")
    assert "def test_combinator_chain_defers_to_pure" not in src, (
        "the rc181 combinator-defers pin must be inverted in rc182 (loop/fold/"
        "reduce now nativize)"
    )


# ─────────────────────────────────────────────────────────────────────
# LOOP — native == pure over the shipped loop chains
# ─────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("n,seq,expect", [
    (2, [1, 2, 3, 4], [1, 2, 3, 4]),        # even flips → identity
    (5, [1, 2, 3], [3, 2, 1]),              # odd flips → one flip
    (0, [1, 2, 3], [1, 2, 3]),              # zero-loop → input
    (1, [5, 6, 7, 8], [8, 7, 6, 5]),
])
def test_loop_chiral_flip_native_eq_pure(n, seq, expect):
    ch = chain("outer").loop(n, chain("inner").then("chiral_flip"))
    native = ch._run_native(seq)
    assert native is not _NATIVE_MISS
    assert native == expect == _pure(ch, seq)


@_needs_native
def test_loop_magnitude_native_within_tol():
    """loop over the f64 magnitude atom — native within-tol of pure (the rc171
    numeric-atom lesson: f64 atoms are within-tol, not byte-identical)."""
    ch = chain("loop").loop(3, chain("body").then("magnitude"))
    native = ch._run_native(-2.0)
    assert native is not _NATIVE_MISS
    assert native == pytest.approx(_pure(ch, -2.0))


@_needs_native
def test_loop_full_run_uses_native():
    """The public Chain.run (not just _run_native) takes the C combinator path."""
    ch = chain("outer").loop(5, chain("inner").then("chiral_flip"))
    assert ch.run([1, 2, 3]) == [3, 2, 1]


@_needs_native
def test_nested_loop_native_eq_pure():
    """A loop whose sub-chain is itself a loop — the C stage-runner recurses
    (depth-bounded) and matches the pure nested run."""
    inner = chain("i").loop(2, chain("f").then("chiral_flip"))   # identity
    outer = chain("o").loop(3, inner)
    native = outer._run_native([1, 2, 3, 4])
    assert native is not _NATIVE_MISS
    assert native == [1, 2, 3, 4] == _pure(outer, [1, 2, 3, 4])


# ─────────────────────────────────────────────────────────────────────
# FOLD — native == pure over the shipped fold chains
# ─────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("seed,seq,expect", [
    (0, [12, 8, 4], 4),      # gcd(0,12)=12; gcd(12,8)=4; gcd(4,4)=4
    (0, [7], 7),
    (0, [], 0),              # empty → seed
    (42, [], 42),
    (0, [12, 18, 24], 6),
])
def test_fold_cyclic_gcd_native_eq_pure(seed, seq, expect):
    ch = chain("fold").fold(seed, "cyclic_gcd")
    native = ch._run_native(seq)
    assert native is not _NATIVE_MISS
    assert native == expect == _pure(ch, seq)
    assert type(native) is int


# ─────────────────────────────────────────────────────────────────────
# REDUCE — native == pure over the shipped reduce chains
# ─────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("seq,expect", [
    ([12, 8, 4], 4),
    ([7], 7),
    ([5, 7, 11], 1),         # coprime → 1
    ([100, 75, 50], 25),
])
def test_reduce_cyclic_gcd_native_eq_pure(seq, expect):
    ch = chain("red").reduce("cyclic_gcd")
    native = ch._run_native(seq)
    assert native is not _NATIVE_MISS
    assert native == expect == _pure(ch, seq)


@_needs_native
def test_reduce_empty_defers_to_pure_raises():
    """reduce on an empty sequence → C non-OK → pure runs → ValueError (the
    functools.reduce convention is preserved)."""
    ch = chain("red").reduce("cyclic_gcd")
    assert ch._run_native([]) is _NATIVE_MISS
    with pytest.raises(ValueError, match="reduce on empty sequence"):
        ch.run([])


# ─────────────────────────────────────────────────────────────────────
# multi-stage combinator chains
# ─────────────────────────────────────────────────────────────────────


@_needs_native
def test_flip_then_reduce_native_eq_pure():
    """A linear atom feeding a reduce combinator, end-to-end in C."""
    ch = chain("mix").then("chiral_flip").reduce("cyclic_gcd")
    native = ch._run_native([12, 8, 4])
    assert native is not _NATIVE_MISS
    assert native == _pure(ch, [12, 8, 4]) == 4


# ─────────────────────────────────────────────────────────────────────
# defer paths: parallel + non-C fold body
# ─────────────────────────────────────────────────────────────────────


@_needs_native
def test_parallel_combinator_defers_to_pure():
    """A `parallel` fan-out runs on host threads → the C engine declines
    (_run_native miss) → the pure sector dispatch runs (inform-don't-limit)."""
    ch = chain("par").parallel_sectors("chiral_flip", n_sectors=4, combine="bundle")
    assert ch._run_native([1.0, 2.0, 3.0, 4.0]) is _NATIVE_MISS
    # the pure parallel path still produces a value:
    assert ch.run([1.0, 2.0, 3.0, 4.0]) is not None


@_needs_native
def test_fold_negative_operand_defers_to_pure():
    """cyclic_gcd is the uint64 gcd surface — a negative element / seed is outside
    it → C non-OK → pure. The pure cyclic_gcd raises ValueError for negatives, so
    _run_native must MISS (not silently answer)."""
    ch = chain("fneg").fold(0, "cyclic_gcd")
    assert ch._run_native([12, -8]) is _NATIVE_MISS


@_needs_native
def test_fold_non_c_body_defers_to_pure():
    """A fold whose body op is not the C binary kernel → C non-OK → pure. (Only
    cyclic_gcd is C-binary; a hypothetical other binary op defers.)"""
    # chiral_dual is 2-ary but NOT in the C binary dispatch → defer.
    ch = chain("fd").fold(0, "chiral_dual")
    assert ch._run_native([1, 2, 3]) is _NATIVE_MISS


# ─────────────────────────────────────────────────────────────────────
# TOML front-end bridge (srmech_dsl_toml_chain_to_json)
# ─────────────────────────────────────────────────────────────────────

_LOOP_TOML = """
[chain]
name = "demo"

[[stage]]
op = "chiral_flip"

[[stage]]
loop_n = 2
[[stage.sub_chain]]
op = "chiral_flip"
"""

_FOLD_TOML = """
[chain]
name = "f"

[[stage]]
fold_init = 0
fold_op = "cyclic_gcd"
"""

_KWARGS_TOML = """
[chain]
name = "r"

[[stage]]
op = "best_rational_signed"
max_denominator = 50
"""


@_needs_toml
def test_toml_bridge_emits_the_build_chain_from_dict_ir():
    """The C bridge parses TOML → the exact build_chain_from_dict IR (dict)."""
    data = _toml_loads_native(_LOOP_TOML)
    assert data == {
        "chain": {"name": "demo"},
        "stage": [
            {"op": "chiral_flip"},
            {"loop_n": 2, "sub_chain": [{"op": "chiral_flip"}]},
        ],
    }


@_needs_toml
def test_toml_bridge_matches_tomllib():
    """The C toml parse == the stdlib tomllib parse for the chain-spec grammar."""
    import sys
    if sys.version_info >= (3, 11):
        import tomllib as toml
    else:
        import tomli as toml
    for spec in (_LOOP_TOML, _FOLD_TOML, _KWARGS_TOML):
        assert _toml_loads_native(spec) == toml.loads(spec)


@_needs_native
def test_toml_built_chain_native_eq_pure():
    """A TOML-built chain runs native == pure end-to-end."""
    ch = build_chain_from_toml_str(_LOOP_TOML)
    native = ch._run_native([1, 2, 3, 4])
    assert native is not _NATIVE_MISS
    assert native == _pure(ch, [1, 2, 3, 4])


@_needs_native
@pytest.mark.parametrize("spec,inp,expect", [
    (_FOLD_TOML, [12, 8, 4], 4),
    (_KWARGS_TOML, 0.5, (1, 2)),
    # chiral_flip THEN loop-2 chiral_flip = 3 net flips = one flip: [1,2,3,4]→[4,3,2,1]
    (_LOOP_TOML, [1, 2, 3, 4], [4, 3, 2, 1]),
])
def test_run_toml_chain_native_eq_pure(spec, inp, expect):
    """run_toml_chain (build + srmech_dsl_chain_run) — the one-shot LLM entry —
    matches the pure build+run and the expected value."""
    native = run_toml_chain(spec, inp)
    with _no_native():
        pure = run_toml_chain(spec, inp)
    assert native == expect == pure


@_needs_toml
def test_toml_syntax_error_falls_back_and_raises():
    """A genuine TOML syntax error → the C bridge declines → tomllib raises the
    proper decode error (the fallback preserves error behavior)."""
    import sys
    if sys.version_info >= (3, 11):
        import tomllib as toml
    else:
        import tomli as toml
    bad = "[chain]\nname = \nthis is not toml"
    assert _toml_loads_native(bad) is None      # C parser declines
    with pytest.raises(toml.TOMLDecodeError):
        build_chain_from_toml_str(bad)


def test_toml_helpers_importable():
    """The TOML front-end surface imports (numpy/native-absent safe)."""
    assert callable(build_chain_from_toml_str)
    assert callable(run_toml_chain)
    # round-trips a minimal spec through the FULL path (native or pure fallback):
    ch = build_chain_from_toml_str(_FOLD_TOML)
    assert ch.run([12, 8, 4]) == 4


def test_json_marshal_sanity():
    """The chain_dict the Python side hands to C is JSON-clean for a combinator."""
    ch = chain("c").loop(2, chain("s").then("chiral_flip")).fold(0, "cyclic_gcd")
    ir = ch._native_stage_list()
    assert ir is not None
    # round-trips through json (the wire format to srmech_dsl_chain_run):
    assert json.loads(json.dumps({"chain": {"name": "c"}, "stage": ir})) == {
        "chain": {"name": "c"},
        "stage": [
            {"loop_n": 2, "sub_chain": [{"op": "chiral_flip"}]},
            {"fold_init": 0, "fold_op": "cyclic_gcd"},
        ],
    }
    assert math.isclose(1.0, 1.0)   # numpy-free sanity marker
