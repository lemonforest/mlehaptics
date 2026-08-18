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


def _c_run(chain, inputs):
    """Run a chain in C. The ctx MUST be wrapped — see the ratchet's harness note."""
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
    chain = {"name": "t", "steps": [
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
    chain = {"name": "t", "steps": [
        {"fold_class": "C", "fold_op": "srmech.cascade.leaves.orientation_compose",
         "fold_init": 1, "over": "@input.orientations"}]}
    rc, raw = _c_run(chain, {"orientations": [0, -1]})
    assert rc == 0, rc
    assert json.loads(raw)["v"] == "0", (
        "the zero did not absorb — C returned %r. That is the reorient "
        "semantics, not orientation_compose." % json.loads(raw)["v"])


def test_a_fold_over_ANOTHER_op_still_DECLINES():
    """THE HONEST EDGE. The body table has ONE entry; this must not pass.

    ``gcd`` IS in the shared dispatch table, so a decline here isolates the
    fold BODY table from op availability. When the body is routed through
    ``cr_dispatch``, this test flips and the ratchet's fold ceiling drops.
    """
    chain = {"name": "t", "steps": [
        {"fold_class": "I", "fold_op": "gcd", "fold_init": 0,
         "over": "@input.xs"}]}
    rc, _ = _c_run(chain, {"xs": [12, 18, 24]})
    assert rc != 0, (
        "a fold over `gcd` RAN — if the body table was widened, lower "
        "CEIL_SURFACE_A_UNSUPPORTED_FORMS and update this test's premise")


def test_a_MIXED_step_is_rejected_not_guessed():
    """A step carrying two discriminators is malformed, never read as one.

    ``BAD_INPUT`` (malformed), deliberately distinct from the ``NOT_IMPL`` a
    recognised-but-unimplemented form earns.
    """
    chain = {"name": "t", "steps": [
        {"fold_op": "srmech.cascade.leaves.orientation_compose", "fold_init": 1,
         "over": "@input.xs", "op": "rational_add", "args": {}}]}
    rc, _ = _c_run(chain, {"xs": [1]})
    assert rc != 0, "a MIXED step ran — mutual exclusion is not enforced"


def test_fold_args_the_KEYWORD_fold_declines():
    """``fold_args`` selects a different iteration contract. Decline, not mis-run."""
    chain = {"name": "t", "steps": [
        {"fold_class": "C", "fold_op": "srmech.cascade.leaves.orientation_compose",
         "fold_init": 1, "over": "@input.xs", "fold_args": ["acc", "x"]}]}
    rc, _ = _c_run(chain, {"xs": [1, -1]})
    assert rc != 0, "the keyword-named fold ran on the positional arm"
