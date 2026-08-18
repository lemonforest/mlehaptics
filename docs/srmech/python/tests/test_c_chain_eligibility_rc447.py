"""gh #1653 rc447 — the PREDICATE must agree with the RUNNER, or the C work is unreachable.

⚠️ THE DEFECT THIS FILE EXISTS FOR. ``_run_chain_native`` returns ``_NATIVE_MISS``
— before the library is ever consulted — when ``_chain_c_eligible(spec)`` is
False. That predicate required ``step.class_id == "N"``, so every Class-I / C /
K / L chain was refused at the door.

Measured at rc447, before the fix::

    _chain_c_eligible says C-runnable :  0   of 18 executable descriptors
    ACTUALLY runs under srmech_chain_run :  9
    disagreements                        :  9   — wrong on every one

So the C chain runner was real, correct, parity-tested — and **unreachable from
the shipped Python API**. Nothing caught it, and the reason is worth stating:
every parity gate in this issue calls ``srmech_chain_run`` DIRECTLY through
ctypes, which bypasses the exact predicate that was blocking it. A gate that
reaches around the thing under test cannot see the thing under test.

After the fix the shipped ``run_cascade_chain`` drives the C runner for **32 of
89** proof cases, up from 0.

This file pins the agreement so it cannot drift back: a C arm added without
widening ``_RUN_C_OPS`` fails HERE rather than going quietly unreachable.
"""
from __future__ import annotations

import ctypes
import json
import re
from pathlib import Path

import pytest

from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat

_C_SRC = Path(__file__).resolve().parents[2] / "c" / "src" / "srmech_compose_run.c"


def _c_dispatch_ops():
    """Op names the C dispatch actually handles — read from the SOURCE.

    Both spellings are matched: the bare ``memcmp(op, "name", N)`` and the
    SUFFIX form ``memcmp(op + (opl - N), "name", N)`` used by ops whose
    descriptors write a dotted path. Reading only the first would under-report
    every dotted op and make this gate agree by accident.
    """
    src = _C_SRC.read_text(encoding="utf-8")
    ops = set(re.findall(r'memcmp\(op,\s*"([a-z0-9_]+)"', src))
    ops |= set(re.findall(r'memcmp\(op \+ \([^)]*\),\s*"([a-z0-9_]+)"', src))
    assert ops, "the C dispatch scan found NOTHING — anchors have drifted"
    return ops


def _executable():
    catalog = _cat.load_catalog()
    return [n for n in sorted(catalog)
            if _cc.descriptor_status(catalog[n]) == "executable"], catalog


def _spec(name, catalog):
    entry = _cc._chain_entries(catalog[name])[0]
    return _compose.parse_chain_spec({**entry, "name": name,
                                      "summary": entry.get("summary", ""),
                                      "returns": entry.get("returns", "")})


def _runs_in_c(name, catalog):
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        pytest.skip("no native library")
    entry = _cc._chain_entries(catalog[name])[0]
    case = (entry.get("proof_cases") or [{}])[0]
    chain = {k: v for k, v in entry.items()
             if k in ("name", "steps", "on_error", "chain_schema_version")}
    cj = json.dumps(chain).encode("utf-8")
    xj = json.dumps({"inputs": case.get("inputs") or {}}).encode("utf-8")
    n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * n)()
    cap = max(n // 2, 65536)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    return int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                    out, cap, ctypes.byref(ol))) == 0


def test_the_predicate_agrees_with_the_runner_on_every_chain():
    """THE CORE GATE. Predicate and runner must not disagree on any descriptor."""
    names, catalog = _executable()
    disagree = []
    for name in names:
        predicted = _compose._chain_c_eligible(_spec(name, catalog))
        actual = _runs_in_c(name, catalog)
        if predicted != actual:
            disagree.append((name, predicted, actual))
    assert not disagree, (
        "the eligibility predicate disagrees with srmech_chain_run:\n" +
        "\n".join("    %-26s predicate=%-6s runs=%s" % r for r in disagree) +
        "\n\nA predicate that says False for a chain C CAN run makes the C work "
        "unreachable from the package (that was the rc447 defect: 0 vs 9). A "
        "predicate that says True for one C CANNOT run costs a wasted attempt "
        "per call — the runner still declines and the pure path takes over, so "
        "it is a performance defect rather than a correctness one, but it is "
        "still a lie about the surface."
    )


def test_every_op_in_the_python_set_is_actually_dispatched_by_C():
    """No phantom entries: a name here that C does not handle is a false claim."""
    c_ops = _c_dispatch_ops()
    phantom = sorted(o for o in _compose._RUN_C_OPS if o not in c_ops)
    assert not phantom, (
        "_RUN_C_OPS names %s, which the C dispatch does not handle. Every call "
        "on such a chain pays a full marshal-and-decline before falling back."
        % phantom)


def test_the_fold_body_set_is_kept_SEPARATE_from_the_op_table():
    """The fold body is a PRIVATE single-entry table in C (``cr_fold_body``),
    not the shared dispatch. Merging the two sets would claim a generality C
    does not have — a fold over any other op still declines."""
    assert _compose._RUN_C_FOLD_OPS == frozenset({"orientation_compose"}), (
        "the fold body table changed; update cr_fold_body and this gate "
        "together, and lower CEIL_SURFACE_A_UNSUPPORTED_FORMS if the body now "
        "routes through the shared op table")


def test_the_shipped_api_ACTUALLY_drives_the_C_runner():
    """END TO END, through ``run_cascade_chain`` — not through ctypes.

    This is the assertion the whole rc turns on: the parity gates all reach
    around the predicate, so only a test that goes through the public surface
    can prove the C path is reachable at all.
    """
    from srmech.dsl import run_cascade_chain
    names, catalog = _executable()
    hits = {"n": 0}
    original = _compose._run_chain_native

    def spy(spec, row, inputs):
        result = original(spec, row, inputs)
        if result is not _compose._NATIVE_MISS:
            hits["n"] += 1
        return result

    _compose._run_chain_native = spy
    try:
        for name in names:
            entry = _cc._chain_entries(catalog[name])[0]
            for case in entry.get("proof_cases") or []:
                try:
                    run_cascade_chain(name, **(case.get("inputs") or {}))
                except Exception:            # noqa: BLE001 — routing, not values
                    pass
    finally:
        _compose._run_chain_native = original

    assert hits["n"] > 0, (
        "run_cascade_chain drove the C chain runner ZERO times across every "
        "shipped proof case. That is the rc447 defect exactly: the C work is "
        "present and unreachable.")
