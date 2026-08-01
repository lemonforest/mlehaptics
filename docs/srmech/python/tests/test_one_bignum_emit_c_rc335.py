"""rc335 (#948 / #887) — One.flat + One.scalar earn native make_class dispatch via
a new SRMECH_MVAL_BIGINT emit kind; the One [class] is now FULLY C-hosted.

The last two EXACT make_class -> C defers were EMIT-ONLY: the COMPUTE
(srmech_the_one / srmech_one_scalar) and the base-2^32 -> decimal render
(srmech_bigint_to_dec) already shipped in C; the only gap was an mval carrier for
an arbitrary-precision integer (the 14 flat rationals + the trace/sqnorm/component
scalar carry 249-bit-and-larger numerators that OVERFLOW int64). This proves:

  (1) One.flat  DISPATCHES byte-identical to the pure One.to_flat_rational
      (LIST[14] of LIST[2] of BIGINT);
  (2) One.scalar DISPATCHES byte-identical to the pure to_scalar across all three
      modes (LIST[2] of BIGINT [num, den]) — as_float=True DEFERS;
  (3) the emitted bignum bytes are RAW / UNQUOTED (like an int, NOT a JSON string)
      and byte-for-byte json.dumps(int) / CPython str(int);
  (4) the leaves GENUINELY overflow int64 (so BIGINT is load-bearing, not int).

numpy-free (stdlib json + srmech) per
[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]].
"""
from __future__ import annotations

import json

import pytest

from srmech import _native
from srmech.amsc.cascade.one import DEFAULT_TERMS, the_one
from srmech.dsl._class_catalog import CLASS_CATALOG_DIR
from srmech.mcp._coercion import serialise_native

pytestmark = pytest.mark.skipif(
    not _native.has_native_make_class(),
    reason="rc201 make_class engine C peer not built",
)

_ONE_TOML = (CLASS_CATALOG_DIR / "one.toml").read_text(encoding="utf-8")
_SEP = (",", ":")

# (sigma, theta_num, theta_den, terms) — the prototype's coverage, incl. the
# ~249-bit (1/2, 24-term) numerator + the hard 50-term factorial cap.
_CASES = [
    (+1, 0, 1, DEFAULT_TERMS),
    (-1, 0, 1, DEFAULT_TERMS),
    (+1, 1, 2, DEFAULT_TERMS),        # the ~249-bit trace numerator
    (-1, 1, 2, DEFAULT_TERMS),
    (+1, 99, 100, DEFAULT_TERMS),
    (+1, 355, 113, 30),
    (+1, 1, 1, 50),                   # the 50-term factorial cap (largest bignums)
    (-1, 22, 7, 40),
]

_INT64_MAX = (1 << 63) - 1
_INT64_MIN = -(1 << 63)


def _run(method, oj, args):
    return _native.make_class_run_c(_ONE_TOML, method, {"one": oj}, args)


# ── (1) One.flat — byte-identical to the pure One.to_flat_rational ──────────────

@pytest.mark.parametrize("sigma,tn,td,terms", _CASES)
def test_flat_byte_identical(sigma, tn, td, terms):
    one = the_one(sigma, tn, td, terms)
    oj = one._to_jsonable()
    dispatched, text = _run("flat", oj, {})
    assert dispatched, f"One.flat must DISPATCH ({sigma},{tn}/{td},{terms})"
    expected = {"result": serialise_native(one.to_flat_rational()),
                "fields": {"one": oj}}
    assert text == json.dumps(expected, separators=_SEP)


# ── (2) One.scalar — byte-identical across trace / sqnorm / component ────────────

@pytest.mark.parametrize("sigma,tn,td,terms", _CASES)
@pytest.mark.parametrize("kwargs", [
    {}, {"mode": "trace"}, {"mode": "sqnorm"},
    {"mode": "component", "index": 0}, {"mode": "component", "index": 4},
    {"mode": "component", "index": 13},
])
def test_scalar_byte_identical(sigma, tn, td, terms, kwargs):
    one = the_one(sigma, tn, td, terms)
    oj = one._to_jsonable()
    dispatched, text = _run("scalar", oj, kwargs)
    assert dispatched, f"One.scalar must DISPATCH ({kwargs}; {sigma},{tn}/{td})"
    # The scalar carrier is a Q; serialise_native(Q) -> [num, den] is the oracle
    # (bare _norm cannot emit a Q — that is exactly why this uses serialise_native).
    expected = {"result": serialise_native(one.to_scalar(**kwargs)),
                "fields": {"one": oj}}
    assert text == json.dumps(expected, separators=_SEP)


def test_scalar_as_float_defers():
    """as_float=True is the terminal float cast (the pure caller's job) — the C
    scalar thunk emits ONLY the exact (num, den) bignum rational, so it DEFERS."""
    oj = the_one(+1, 1, 2, DEFAULT_TERMS)._to_jsonable()
    assert _run("scalar", oj, {"as_float": True}) == (False, None)


def test_scalar_bad_mode_defers():
    """An unknown mode string DEFERS (the pure path raises the ValueError)."""
    oj = the_one(+1, 1, 2, DEFAULT_TERMS)._to_jsonable()
    assert _run("scalar", oj, {"mode": "nonsense"}) == (False, None)


# ── (3) the emitted bignum is RAW / UNQUOTED — byte-for-byte json.dumps(int) ─────

def test_flat_emit_is_raw_unquoted_and_matches_str_int():
    """Each flat leaf is emitted as bare decimal digits (NOT a quoted JSON string),
    byte-for-byte CPython str(int) — the SRMECH_MVAL_BIGINT raw-emit contract."""
    one = the_one(+1, 1, 2, DEFAULT_TERMS)
    oj = one._to_jsonable()
    dispatched, text = _run("flat", oj, {})
    assert dispatched
    result = json.loads(text)["result"]
    assert len(result) == 14 and all(len(p) == 2 for p in result)
    # json.loads gives back ints (not strings) — proof the wire form was unquoted.
    for (n, d), (pn, pd) in zip(result, one.to_flat_rational()):
        assert isinstance(n, int) and isinstance(d, int)
        assert (n, d) == (pn, pd)
    # And there is NO quote anywhere in the numeric result payload.
    payload = text.split('"result":', 1)[1].split(',"fields"', 1)[0]
    assert '"' not in payload


def test_scalar_trace_numerator_overflows_int64():
    """The (1/2, 24-term) trace numerator is a ~249-bit integer that OVERFLOWS
    int64 — so SRMECH_MVAL_BIGINT is genuinely load-bearing here (an int64 mval
    could not emit it). The native emit must still equal the pure exact rational."""
    one = the_one(+1, 1, 2, DEFAULT_TERMS)
    q = one.to_scalar(mode="trace")
    assert not (_INT64_MIN <= q.numerator <= _INT64_MAX), "expected an int64 overflow"
    assert q.numerator.bit_length() >= 200
    dispatched, text = _run("scalar", one._to_jsonable(), {"mode": "trace"})
    assert dispatched
    assert json.loads(text)["result"] == [q.numerator, q.denominator]


def test_some_flat_leaf_overflows_int64_across_cases():
    """At least one flat leaf across the covered cases overflows int64 (proof the
    bignum path — not an int64 fallback — is exercised)."""
    saw_overflow = False
    for sigma, tn, td, terms in _CASES:
        for n, d in the_one(sigma, tn, td, terms).to_flat_rational():
            if not (_INT64_MIN <= n <= _INT64_MAX) or not (_INT64_MIN <= d <= _INT64_MAX):
                saw_overflow = True
    assert saw_overflow, "no flat leaf overflowed int64 — BIGINT not exercised"


# ── (4) run_class_method (class NAME resolved IN C) dispatches too ──────────────

def test_run_class_method_flat_and_scalar_dispatch():
    if not _native.has_native_run_class_method():
        pytest.skip("rc202 run_class_method C peer not built")
    one = the_one(+1, 1, 2, DEFAULT_TERMS)
    oj = one._to_jsonable()
    d1, t1 = _native.run_class_method_c("One", "flat", {"one": oj}, {})
    assert d1
    assert t1 == json.dumps(
        {"class": "One", "method": "flat",
         "result": serialise_native(one.to_flat_rational()), "fields": {"one": oj}},
        separators=_SEP)
    d2, t2 = _native.run_class_method_c("One", "scalar", {"one": oj}, {"mode": "sqnorm"})
    assert d2
    assert t2 == json.dumps(
        {"class": "One", "method": "scalar",
         "result": serialise_native(one.to_scalar(mode="sqnorm")),
         "fields": {"one": oj}},
        separators=_SEP)
