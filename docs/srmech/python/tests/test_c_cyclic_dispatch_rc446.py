"""gh #1653 — the Class-I cyclic arm of ``cr_dispatch``: parity AND the decline contract.

Six catalog chains (``cyclic_gcd`` / ``mod_add`` / ``mod_inv`` / ``mod_mul`` /
``mod_mul_wide`` / ``mod_pow``) were blocked by the C op table ALONE — measured at
rc445 in ``notes/_1653_gate_matrix_rc445.ndjson``, and that "alone" is what made
them the first slice: no carrier, ref-grammar or real-literal work is entangled.

TWO PROPERTIES, and the second is the one that matters more
-----------------------------------------------------------
1. PARITY — every shipped proof case runs in C and is byte-identical to Python.
2. THE DECLINE CONTRACT — the chain carrier is arbitrary precision; the shipped
   Class-I exports take ``uint64``. Where an operand does not fit that wire the C
   arm must **REFUSE**, never narrow it. A narrower projection that answers
   anyway does not have a capability gap, it has a WRONG ANSWER, and the two
   projections then disagree on a value rather than on a capability — which is
   strictly worse and much harder to notice.

   The probe below is chosen to make truncation VISIBLE rather than plausible:
   ``gcd(2**64 + 7, 21)`` is **1**, but a narrowed operand becomes ``7`` and the
   answer becomes ``7``. A test using a random huge number would pass whether or
   not the guard worked.

WHY ``mod_mul_wide`` ROUTES TO ``srmech_mod_mul``: that export is Russian-peasant
doubling (``srmech_cyclic.c``), already overflow-safe across the full uint64
range, so the two ops differ only in the CAP — which ``cr_as_u64`` enforces.
Verified in Python at rc445: ``mod_mul(2**63-1, 2**63-1, 12)`` and
``mod_mul_wide(...)`` both give 1.

⚠️ WHAT THIS DOES NOT PROVE. The decline currently observed for a huge LITERAL
arrives as ``SRMECH_ERR_LIMIT`` from ``srmech_json_parse``, upstream of
``cr_as_u64`` — so for literals the guard is belt-and-braces rather than the
thing doing the work. It is load-bearing on the path where an out-of-range value
arrives from a ``@step[N].output`` ref (computed, never parsed as a literal),
which no shipped descriptor exercises today. Stated so the guard is not credited
with a job the parser is doing.
"""
from __future__ import annotations

import ctypes
import json

import pytest

from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat
from srmech.dsl import run_cascade_chain

CYCLIC_CHAINS = ("cyclic_gcd", "cyclic_mod_add", "cyclic_mod_inv",
                 "cyclic_mod_mul", "cyclic_mod_mul_wide", "cyclic_mod_pow")


def _lib():
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        pytest.skip("no native library — this gate measures the C projection")
    return lib


def _c_run(chain, inputs):
    """Run a chain in C. NOTE the ctx WRAPPING — see the ratchet's harness note."""
    lib = _lib()
    cj = json.dumps(chain, ensure_ascii=False).encode("utf-8")
    xj = json.dumps({"inputs": inputs}, ensure_ascii=False).encode("utf-8")
    n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * n)()
    cap = max(n // 2, 16384)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                  out, cap, ctypes.byref(ol)))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


@pytest.mark.parametrize("name", CYCLIC_CHAINS)
def test_every_proof_case_runs_in_c_byte_identical(name):
    """PARITY. Every shipped proof case, not just the first."""
    catalog = _cat.load_catalog()
    seen = 0
    for entry in _cc._chain_entries(catalog[name]):
        for case in entry.get("proof_cases") or []:
            inputs = case.get("inputs") or {}
            rc, raw = _c_run(entry, inputs)
            assert rc == 0, "%s %s: C declined rc=%s" % (name, inputs, rc)
            c_val = json.loads(raw).get("v")
            py_val = run_cascade_chain(name, **inputs)
            assert str(c_val) == str(py_val), (
                "%s %s: C=%r python=%r" % (name, inputs, c_val, py_val))
            seen += 1
    assert seen, "%s declared no proof cases — parity claim would be vacuous" % name


@pytest.mark.parametrize("a,b,narrowed_would_give", [
    (2 ** 64 + 7, 21, 7),      # narrowing gives gcd(7,21)=7; the truth is 1
    (2 ** 64, 18, 18),         # narrowing gives gcd(0,18)=18; the truth is 2
])
def test_out_of_uint64_operand_is_DECLINED_not_narrowed(a, b, narrowed_would_give):
    """THE DECLINE CONTRACT, probed where narrowing would be VISIBLE."""
    chain = {"name": "t", "steps": [
        {"class": "I", "op": "gcd", "args": {"a": "@input.a", "b": "@input.b"}}]}
    truth = run_cascade_chain("cyclic_gcd", a=a, b=b)
    assert truth != narrowed_would_give, (
        "this probe cannot detect narrowing: the true answer and the narrowed "
        "answer coincide, so it would pass either way")
    rc, raw = _c_run(chain, {"a": a, "b": b})
    assert rc != 0, (
        "C returned a value for an out-of-uint64 operand: %r. It must DECLINE — "
        "a narrower wire that answers anyway produces a WRONG ANSWER, not a "
        "capability gap." % raw)


def test_in_range_control_still_runs():
    """The positive control. A guard that declines everything is not a fix."""
    chain = {"name": "t", "steps": [
        {"class": "I", "op": "gcd", "args": {"a": "@input.a", "b": "@input.b"}}]}
    rc, raw = _c_run(chain, {"a": 12, "b": 18})
    assert rc == 0 and json.loads(raw)["v"] == "6", (rc, raw)
