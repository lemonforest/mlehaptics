"""gh #1653 — the Surface-A FOLD step form in C, and the honest edge of it.

``cr_run_steps`` demanded every step carry ``op``. A FOLD step carries
``fold_op``, so it was rejected ``BAD_INPUT`` *before dispatch was reached* —
a STEP-FORM gate, not an op-table gate. No amount of op work could have reached
it, which is why the gate matrix lists ``step_form`` separately.

rc446 adds ``cr_step_form`` + ``cr_run_fold`` + ``cr_fold_body``, which makes
``net_chirality`` the 7th chain to execute in the compiled projection.

⚠️ WHAT THIS DOES **NOT** MAKE TRUE — and the ratchet is kept honest about it.
   The fold BODY dispatches through a PRIVATE single-entry table
   (``orientation_compose`` only), NOT through the shared ``cr_dispatch`` op
   table. A fold over any other op still declines. So the fold FORM executes
   and a general fold does not, and ``CEIL_SURFACE_A_UNSUPPORTED_FORMS`` still
   counts ``fold`` as unsupported on purpose. The tests below assert BOTH
   halves, because a file that only proved the working half would read as
   "fold is done".
"""
from __future__ import annotations

import ctypes
import json

import pytest

from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat
from srmech.dsl import run_cascade_chain


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
    """Run a chain in C. The ctx MUST be wrapped — see the ratchet's harness note."""
    lib = _lib()
    cj = json.dumps(_hdr(chain), ensure_ascii=False).encode("utf-8")
    xj = json.dumps({"inputs": inputs}, ensure_ascii=False).encode("utf-8")
    n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * n)()
    cap = max(n // 2, 16384)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                  out, cap, ctypes.byref(ol)))
    return rc, (out.raw[:ol.value].decode("utf-8") if rc == 0 else None)


def test_net_chirality_every_proof_case_is_byte_identical():
    """PARITY over every shipped proof case, not just the first."""
    catalog = _cat.load_catalog()
    seen = 0
    for entry in _cc._chain_entries(catalog["net_chirality"]):
        for case in entry.get("proof_cases") or []:
            inputs = case.get("inputs") or {}
            rc, raw = _c_run(entry, inputs)
            assert rc == 0, "net_chirality %s: C declined rc=%s" % (inputs, rc)
            c_val = json.loads(raw).get("v")
            py_val = run_cascade_chain("net_chirality", **inputs)
            assert str(c_val) == str(py_val), (
                "net_chirality %s: C=%r python=%r" % (inputs, c_val, py_val))
            seen += 1
    assert seen >= 7, "expected >= 7 proof cases, saw %d" % seen


def test_the_empty_fold_returns_the_SEED():
    """``[]`` is the case that proves ``fold_init`` is read at all.

    Every other proof case would still pass if the seed were ignored and the
    accumulator started at the first element.
    """
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"fold_class": "C", "fold_op": "srmech.cascade.leaves.orientation_compose",
         "fold_init": 1, "over": "@input.orientations"}]}
    rc, raw = _c_run(chain, {"orientations": []})
    assert rc == 0 and json.loads(raw)["v"] == "1", (rc, raw)


def test_the_absorbing_zero_is_a_class_K_pin_slot():
    """``0`` ABSORBS — it is not a multiply-by-zero that a sign fold would give.

    A bare ``reorient`` fold cannot absorb (its ``orientation == 0`` branch is a
    no-op), so this is the case that distinguishes the two ops. ``[0, -1]`` must
    be ``0``; a reorient fold returns ``-1``.
    """
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"fold_class": "C", "fold_op": "srmech.cascade.leaves.orientation_compose",
         "fold_init": 1, "over": "@input.orientations"}]}
    rc, raw = _c_run(chain, {"orientations": [0, -1]})
    assert rc == 0, rc
    assert json.loads(raw)["v"] == "0", (
        "the zero did not absorb — C returned %r. That is the reorient "
        "semantics, not orientation_compose." % json.loads(raw)["v"])


def test_a_fold_over_ANOTHER_op_now_RUNS_and_returns_the_right_value():
    """THE FLIP THIS TEST'S OWN rc446 TEXT PREDICTED.

    Through rc451 this asserted ``rc != 0`` and said: *"When the body is routed
    through cr_dispatch, this test flips and the ratchet's fold ceiling drops."*
    rc452 (`#T1166`) routes it — the fold body dispatches through the SHARED
    ``CR_OP_REG`` atom table's ``bin`` column — so the premise is updated here
    and ``CEIL_SURFACE_A_UNSUPPORTED_FORMS`` drops in the same change.

    ⚠️ IT ASSERTS THE VALUE, NOT ``rc == 0``. An ``rc``-only flip is the defect
    class this whole arc exists to close: a fold arm that ran the wrong body,
    or folded in the wrong order, or ignored the seed, returns 0 just as
    happily. gcd(gcd(gcd(0,12),18),24) = 6, and a seed the arm failed to read
    would give the same 6 here — so the ``[]`` case below is what proves the
    seed is read at all, and this case proves the body is.
    """
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"fold_class": "I", "fold_op": "gcd", "fold_init": 0,
         "over": "@input.xs"}]}
    rc, raw = _c_run(chain, {"xs": [12, 18, 24]})
    assert rc == 0, (
        "a fold over `gcd` DECLINED — rc452 routes the fold body through the "
        "shared atom table, so this is a regression in that routing")
    assert json.loads(raw) == {"k": "i", "v": "6"}, (
        "the fold ran but returned %r; gcd folded from seed 0 over "
        "[12, 18, 24] is 6" % (raw,))


def test_a_fold_over_gcd_READS_ITS_SEED():
    """The empty sequence returns the seed unchanged — the only case that can
    prove the seed is read, since any non-empty gcd fold from 0 absorbs it."""
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"fold_class": "I", "fold_op": "gcd", "fold_init": 7,
         "over": "@input.xs"}]}
    rc, raw = _c_run(chain, {"xs": []})
    assert rc == 0, "an empty fold over gcd declined"
    assert json.loads(raw) == {"k": "i", "v": "7"}, (
        "an empty fold must return the seed unchanged; got %r" % (raw,))


def test_a_MIXED_step_is_rejected_not_guessed():
    """A step carrying two discriminators is malformed, never read as one.

    ``BAD_INPUT`` (malformed), deliberately distinct from the ``NOT_IMPL`` a
    recognised-but-unimplemented form earns.
    """
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"fold_op": "srmech.cascade.leaves.orientation_compose", "fold_init": 1,
         "over": "@input.xs", "op": "rational_add", "args": {}}]}
    rc, _ = _c_run(chain, {"xs": [1]})
    assert rc != 0, "a MIXED step ran — mutual exclusion is not enforced"


def test_fold_args_the_KEYWORD_fold_declines():
    """``fold_args`` selects a different iteration contract. Decline, not mis-run."""
    chain = {"name": "t", "summary": "s", "returns": "r", "steps": [
        {"fold_class": "C", "fold_op": "srmech.cascade.leaves.orientation_compose",
         "fold_init": 1, "over": "@input.xs", "fold_args": ["acc", "x"]}]}
    rc, _ = _c_run(chain, {"xs": [1, -1]})
    assert rc != 0, "the keyword-named fold ran on the positional arm"
