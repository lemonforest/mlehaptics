"""gh #1653 — the CR_DBL real carrier, and what "parity" does NOT mean for it.

``cr_value_t`` had no DOUBLE kind, so a real-number literal could not even be
INGESTED (``cr_json_scalar`` returned NULL for a JSON double) and a real-valued
result could not be marshalled back. That is two of the five measured gates —
``real_literal_arg`` (9 of 18 chains) and ``carrier_width`` (4) — and it sat
UPSTREAM of the op table: no amount of op work could reach a chain whose args
carried a float.

rc447 adds ``CR_DBL`` + the ``{"k":"f"}`` descriptor, the ``{"k":"l"}`` list
descriptor, and a Python ``k == "f"`` branch in the SAME change (a new type
closes its projection gap in the same change), with ABI 17 -> 18.

⚠️ MOST PARITY TESTS IN THIS AREA ARE TAUTOLOGICAL, AND THIS FILE IS NOT.
   Measured at rc447: ``autocorrelation``, ``chiral_flip``, ``reorient``,
   ``gcd``, ``mod_add/mul/pow/inv`` and ``best_rational`` ALL dispatch the
   Python surface to the SAME C symbol when ``HAS_NATIVE``. So the obvious test
   — run the chain in C, run it in Python, compare — is comparing **C against
   C** for those ops, and would pass even if the pure fallback were badly
   wrong. It is the same shape as the earlier harness trap where both controls
   passed their args as literals and so never exercised the ref path.

   The distinction that decides whether it matters:

   EXACT ops (integer / rational) — the tautology is HARMLESS. Both paths
   compute an exact value, so they agree whatever the dispatch does. Verified:
   the 6 cyclic chains + net_chirality are 30/30 identical against a
   FORCED-PURE Python (``_native.HAS_NATIVE = False``).

   FLOAT ops — the tautology HIDES A REAL DIVERGENCE. ``autocorrelation``'s C
   sum and its pure-Python fallback accumulate in DIFFERENT ORDERS, so they are
   NOT bit-identical. Measured over golden-ratio-derived spreads: 8 of 9 cases
   differ, growing 1.4e-17 (n=3) -> 1.0e-15 (n=64), and a mixed-magnitude input
   differs by 2.0 ABSOLUTE (~1 ulp relative at 1e16). The header's "parity to
   FFT roundoff (~1e-12)" is therefore a REAL caveat on this op, not boilerplate
   — and the pure path is exactly what runs in Pyodide / WASM, where there is no
   ``.so`` at all.

   So this file states the two claims separately and never rounds one into the
   other: ``chiral_dual`` is BIT-IDENTICAL in the native-dispatched
   configuration, and agrees to a stated RELATIVE tolerance against forced-pure.
"""
from __future__ import annotations

import ctypes
import json
import struct

import pytest

from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat
from srmech.dsl import run_cascade_chain

#: Golden-ratio derived, NOT drawn from an RNG — a seeded RNG would be an
#: undeclared pin, and evenly spaced values would make the sums agree trivially.
_PHI = (1.0 + 5.0 ** 0.5) / 2.0


def _spread(n):
    return [((i * _PHI) % 1.0) - 0.5 for i in range(1, n + 1)]


def _lib():
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        pytest.skip("no native library — this gate measures the C projection")
    return lib


def _hdr(chain):
    """rc452 (gh #1653 finding (b)): srmech_chain_run now refuses a chain
    missing name/summary/returns (the required-key rule every parse layer
    already enforced). This file's subject is op dispatch, not the header
    contract (the rc446 ratchet pins that), so the harness synthesizes the
    header exactly as cascade_chain_specs does. Idempotent over documents
    that already carry one."""
    out = dict(chain)
    out.setdefault("name", str(out.get("variant", "chain")))
    out.setdefault("summary", "")
    out.setdefault("returns", "")
    return out


def _c_run(chain, inputs):
    lib = _lib()
    cj = json.dumps(_hdr(chain), ensure_ascii=False).encode("utf-8")
    xj = json.dumps({"inputs": inputs}, ensure_ascii=False).encode("utf-8")
    n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * n)()
    cap = max(n // 2, 65536)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                  out, cap, ctypes.byref(ol)))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def _bits(x):
    """Compare by BIT PATTERN, not by ``==`` — so -0.0 vs 0.0 is a difference
    and a NaN compares equal to itself."""
    return struct.pack("<d", x)


def test_chiral_dual_is_bit_identical_in_the_native_configuration():
    """The chain that CR_DBL unblocks. All 4 proof cases, exact bit patterns."""
    catalog = _cat.load_catalog()
    seen = 0
    for entry in _cc._chain_entries(catalog["chiral_dual"]):
        for case in entry.get("proof_cases") or []:
            inputs = case.get("inputs") or {}
            rc, raw = _c_run(entry, inputs)
            assert rc == 0, "chiral_dual %s: C declined rc=%s" % (inputs, rc)
            got = _compose._reconstruct_value(json.loads(raw))
            ref = run_cascade_chain("chiral_dual", **inputs)
            assert len(got) == len(ref), (got, ref)
            for a, b in zip(got, ref):
                assert _bits(a) == _bits(b), "chiral_dual %s: %r vs %r" % (inputs, a, b)
            seen += 1
    assert seen >= 4, "expected >= 4 proof cases, saw %d" % seen


@pytest.mark.parametrize("value", [
    0.1, -3.5, 0.30000000000000004, 1e300, 5e-324,
    1.7976931348623157e308, -0.0, 123456789.123456789,
])
def test_a_real_literal_ROUND_TRIPS_bit_exactly(value):
    """Ingest -> carrier -> descriptor -> Python must not lose a single bit.

    ``-0.0`` and ``5e-324`` (the smallest subnormal) are the cases a
    ``%.17g``-style writer would break; they pass because the C writer uses
    ``srmech_double_repr``, an integer-only Ryu matching CPython ``repr``.
    """
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "C", "op": "srmech.cascade.atoms.chiral_flip",
         "args": {"seq": "@input.x"}}]}
    rc, raw = _c_run(chain, {"x": [value]})
    assert rc == 0, rc
    got = _compose._reconstruct_value(json.loads(raw))
    assert _bits(got[0]) == _bits(value), "%r round-tripped as %r" % (value, got[0])


def test_the_list_descriptor_kind_is_produced_at_all():
    """``{"k":"l"}`` — a kind the Python reader has ALWAYS had a branch for and
    the C writer could never emit. The reader was ahead of the writer."""
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "C", "op": "srmech.cascade.atoms.chiral_flip",
         "args": {"seq": "@input.x"}}]}
    rc, raw = _c_run(chain, {"x": [1.0, 2.0]})
    assert rc == 0, rc
    assert json.loads(raw)["k"] == "l", json.loads(raw)


def test_an_empty_real_sequence_is_not_an_error():
    """``[]`` distinguishes "empty result" from "declined" — a carve returning
    NULL for n == 0 would collapse the two."""
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "C", "op": "srmech.cascade.atoms.chiral_flip",
         "args": {"seq": "@input.x"}}]}
    rc, raw = _c_run(chain, {"x": []})
    assert rc == 0 and _compose._reconstruct_value(json.loads(raw)) == [], (rc, raw)


def test_a_double_is_NOT_coerced_into_an_exact_op():
    """A float where a rational is required must DECLINE, never round.

    Silently coercing would turn a capability gap into a wrong answer, and
    would breach stay-rational discipline mid-cascade.
    """
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "N", "op": "rational_add",
         "args": {"a": [1.5, 2], "b": [1, 3]}}]}
    rc, _ = _c_run(chain, {})
    assert rc != 0, "a float operand was accepted by an exact rational op"


def test_autocorrelation_C_vs_FORCED_PURE_is_close_but_NOT_bit_identical():
    """THE HONEST CLAIM. Documents a real divergence rather than hiding it.

    Python's ``autocorrelation`` dispatches to the same C symbol, so the
    ordinary comparison is C-vs-C. Forcing the pure fallback reveals that the
    two summation orders do NOT agree to the last bit. This test asserts BOTH
    that they are close (a real parity claim) and that they are NOT identical
    (so the divergence cannot silently disappear or silently grow).
    """
    import srmech.cascade.composites as _comp
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "L", "op": "srmech.cascade.composites.autocorrelation",
         "args": {"x": "@input.x"}}]}
    x = _spread(64)
    rc, raw = _c_run(chain, {"x": x})
    assert rc == 0, rc
    got = _compose._reconstruct_value(json.loads(raw))

    orig = _comp._try_native_autocorrelation
    _comp._try_native_autocorrelation = lambda _x: None      # force the pure path
    try:
        pure = _comp.autocorrelation(x)
    finally:
        _comp._try_native_autocorrelation = orig

    scale = max((abs(v) for v in pure), default=1.0) or 1.0
    worst = max(abs(a - b) for a, b in zip(got, pure))
    assert worst / scale < 1e-12, (
        "C and pure-Python autocorrelation diverged by %.3g (relative %.3g) — "
        "beyond the documented FFT-roundoff parity" % (worst, worst / scale))
    assert any(_bits(a) != _bits(b) for a, b in zip(got, pure)), (
        "C and pure-Python autocorrelation are now BIT-identical. If the "
        "summation orders were deliberately aligned, delete this assertion and "
        "say so; until then its passing is what keeps the parity claim honest.")
