"""gh #1653 — indexed step refs (``@step[N].output[K]``) and the Class-K pin-slot.

``cr_resolve_ref`` accepted only a BARE ``.output`` and rejected any tail, so a
chain reading one HALF of a two-part step output could not run. That gate —
``ref_grammar`` — was reported as blocking 2 chains and, once the predicate was
corrected to also count the namespaces C cannot resolve at all (``@op`` /
``@bind`` / ``@idx``), turned out to block 8.

rc447 adds element indexing plus the two Class-K/C atoms that need it, making
``magnitude`` the 9th chain to execute in C:

    pin_slot_at_zero(x) -> [orientation, magnitude]   (Class K pin-slot)
    reorient(@step[0].output[1], orientation=1)       (Class C re-application)

That IS the sign-handling composition — never an ALU-magnitude call. The
descriptor's own summary calls it "the replacement for C99 fabs() inside cascade
code: keeps the cascade-count claimed in line with the cascade-count executed".

⚠️ NON-FINITE INPUTS CANNOT REACH C AT ALL, and that is adjudicated, not a bug.
   3 of ``magnitude``'s 8 proof cases are ``nan`` / ``inf`` / ``-inf``. RFC 8259
   has no non-finite literal; srmech's parser is strict and refuses them, and
   its writer DECLINES them for the matching reason (rc403 D4 option (c)): a
   canonical writer whose bytes go behind a sha256 must not emit a document its
   own parser refuses, or the attestation chain breaks at the re-read. So
   writer-output is a subset of parser-input unconditionally, and the two halves
   agree. The limit bounds which INPUTS can cross the wire, not which chains
   exist — so this file proves the 5 finite cases exactly AND pins the 3
   declines, rather than quietly testing only what passes.
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

_MAGNITUDE = {"name": "magnitude", "summary": "s", "returns": "r", "steps": [
    {"class": "K", "op": "srmech.cascade.pin_slot_at_zero",
     "args": {"x": "@input.x"}},
    {"class": "C", "op": "srmech.cascade.reorient",
     "args": {"value": "@step[0].output[1]", "orientation": 1}}]}


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


@pytest.mark.parametrize("x", [-3.5, 0.0, -0.0, 2.25, -1e-13])
def test_magnitude_is_bit_identical_on_every_FINITE_proof_case(x):
    rc, raw = _c_run(_MAGNITUDE, {"x": x})
    assert rc == 0, "magnitude(%r): C declined rc=%s" % (x, rc)
    got = _compose._reconstruct_value(json.loads(raw))
    ref = run_cascade_chain("magnitude", x=x)
    assert struct.pack("<d", got) == struct.pack("<d", ref), (x, got, ref)


@pytest.mark.parametrize("x", [float("nan"), float("inf"), float("-inf")])
def test_a_NON_FINITE_input_is_DECLINED_at_the_json_wire(x):
    """Pinned as a DECLINE so it can neither regress into a wrong answer nor be
    silently closed without updating the ledger row that explains it."""
    rc, _ = _c_run(_MAGNITUDE, {"x": x})
    assert rc != 0, (
        "a non-finite input crossed the wire. RFC 8259 has no such literal — if "
        "the parser was deliberately widened, update the "
        "non_finite_doubles_cannot_cross_json ledger row and rc403's D4 note")


def test_the_pin_slot_returns_BOTH_halves_addressably():
    """``[0]`` is the orientation, ``[1]`` the magnitude. If indexing silently
    returned the whole list, the reorient step would still 'work' on a truthy
    value and this asymmetry is what proves it does not."""
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "K", "op": "srmech.cascade.pin_slot_at_zero",
         "args": {"x": "@input.x"}}]}
    rc, raw = _c_run(chain, {"x": -3.5})
    assert rc == 0, rc
    # A TUPLE since v0.9.0rc451 (`#T1164`). This assertion read ``[-1, 3.5]``
    # from rc447 to rc450 and that LIST was never the contract -- it was the
    # WIRE'S LIMITATION, pinned as if it were one. ``pin_slot_at_zero``
    # declares ``-> Tuple[int, 'Real']`` and returns ``(-1, 3.5)``; the rc447
    # output-kind set {n,i,s,q,f,l} simply had no tuple spelling, so C could
    # only answer ``l`` and this line recorded the collapse. rc451 adds
    # ``{"k":"t"}`` and flags cr_op_pin_slot's CR_LIST, so the emitted wire is
    #     {"k": "t", "v": [{"k": "i", "v": "-1"}, {"k": "f", "v": 3.5}]}
    # and C now matches its Python peer exactly. The SUBJECT of this test is
    # untouched: ``[0]`` and ``[1]`` must still address the two halves
    # separately, which is what the docstring above is about and what the two
    # tests below exercise from the declining side.
    assert _compose._reconstruct_value(json.loads(raw)) == (-1, 3.5)


def test_an_OUT_OF_RANGE_index_declines_rather_than_wrapping():
    """Defer, never wrap or clamp — a wrong element is a wrong answer."""
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "K", "op": "srmech.cascade.pin_slot_at_zero",
         "args": {"x": "@input.x"}},
        {"class": "C", "op": "srmech.cascade.reorient",
         "args": {"value": "@step[0].output[7]", "orientation": 1}}]}
    rc, _ = _c_run(chain, {"x": -3.5})
    assert rc != 0, "an out-of-range element index resolved to something"


def test_indexing_a_NON_LIST_output_declines():
    """``@step[N].output[K]`` on a scalar must defer, not coerce."""
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"class": "N", "op": "rational_add", "args": {"a": [1, 2], "b": [1, 3]}},
        {"class": "C", "op": "srmech.cascade.reorient",
         "args": {"value": "@step[0].output[0]", "orientation": 1}}]}
    rc, _ = _c_run(chain, {})
    assert rc != 0, "indexing a non-list carrier produced a value"


def test_the_shipped_descriptor_still_matches_this_chain():
    """Guards the hand-written literal above against descriptor drift."""
    entry = _cc._chain_entries(_cat.load_catalog()["magnitude"])[0]
    got = [(s.get("op"), s.get("args")) for s in entry["steps"]]
    want = [(s["op"], s["args"]) for s in _MAGNITUDE["steps"]]
    assert got == want, "the magnitude descriptor changed; update this file"
