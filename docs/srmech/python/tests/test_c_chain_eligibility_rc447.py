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
    # ⚠️ READ THE TABLE, NOT THE ARMS (v0.9.0rc452, `#T1166`). Through rc451 the
    # dispatch was an if-chain and this scan matched its `cr_op_is` arms. rc452
    # converts CR_OP_REG into the atom table (rows now carry the A1 enum
    # columns dom/sub/bin — the first cut's function-pointer columns violated
    # JPL Rule 9) and cr_dispatch into a row lookup with ZERO arms of its own —
    # so the arm patterns below now match only `cr_op_row`'s single generic
    # call, whose operand is a table field rather than a literal, and the
    # derived set went to EMPTY. An empty derived set does not fail loudly here
    # by itself: it makes `_RUN_C_OPS - ops` report every Python entry as a
    # phantom, which is the shape of a gate that has stopped observing while
    # still returning a verdict. The table IS the dispatch surface now, so the
    # table is what this reads; the `assert ops` below still refuses an empty
    # parse.
    m = re.search(r"\}\s*CR_OP_REG\[\d+\]\s*=\s*\{", src)
    assert m, ("CR_OP_REG's initialiser was not found — the dispatch surface "
               "was reshaped and this scan has stopped observing. Re-point it; "
               "do not delete the assertion.")
    body = src[m.end():src.index("};", m.end())]
    # A row is { "bare", Nu, "full", dom, sub, bin, un }; the FIRST string is
    # the
    # spelling the matcher compares. Rows whose `dom` is CR_DOM_NONE are
    # fold-body-only and are NOT plain-dispatchable, so they are excluded —
    # otherwise this set would claim a plain-step capability the runner
    # declines.
    ops = set()
    for bare, _ln, _full, dom, _sub, _bn, _un in re.findall(
            r'\{\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*,\s*(\d+)u\s*,'
            r'\s*"([A-Za-z0-9_.]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,'
            r'\s*([A-Za-z0-9_]+)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,'
            r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}', body):
        if dom != "CR_DOM_NONE":
            ops.add(bare)
    assert ops, "the C dispatch scan found NOTHING — anchors have drifted"
    return ops


def _c_fold_body_ops():
    """Op names the C FOLD BODY dispatches — the table's non-NONE ``bin`` column.

    rc451 pinned this set to the single private-table entry
    ``orientation_compose``. rc452 gives the fold body the SHARED table, so the
    set is derived the same way the plain set is, from the same rows.
    """
    src = _C_SRC.read_text(encoding="utf-8")
    m = re.search(r"\}\s*CR_OP_REG\[\d+\]\s*=\s*\{", src)
    assert m, "CR_OP_REG's initialiser was not found"
    body = src[m.end():src.index("};", m.end())]
    ops = set()
    for bare, _ln, _full, _dom, _sub, bn, _un in re.findall(
            r'\{\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*,\s*(\d+)u\s*,'
            r'\s*"([A-Za-z0-9_.]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,'
            r'\s*([A-Za-z0-9_]+)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*,'
            r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}', body):
        if bn != "CR_BIN_NONE":
            ops.add(bare)
    assert ops, "the C fold-body scan found NOTHING — anchors have drifted"
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
    # rc452 (gh #1653 finding (b)): the runner refuses a headerless chain, so
    # this probe synthesizes the header the way cascade_chain_specs does —
    # same repair as every other srmech_chain_run harness in this suite.
    chain = {k: v for k, v in entry.items()
             if k in ("name", "summary", "returns", "steps", "on_error",
                      "chain_schema_version")}
    chain.setdefault("name", name)
    chain.setdefault("summary", "")
    chain.setdefault("returns", "")
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


def test_the_fold_body_set_AGREES_WITH_C_row_for_row():
    """The Python fold-body set equals the C table's non-NULL ``bin`` column.

    ⚠️ THIS GATE INVERTED AT rc452 (`#T1166`), DELIBERATELY, AND ITS OLD TEXT
    PREDICTED THE INVERSION. Through rc451 it asserted
    ``_RUN_C_FOLD_OPS == {"orientation_compose"}`` and said so on the grounds
    that "the fold body is a PRIVATE single-entry table in C, not the shared
    dispatch — merging the two sets would claim a generality C does not have."
    That was TRUE THEN and is false now: rc452 gives the fold body the shared
    atom table (as a ``bin`` column on the same rows), so the set is no longer
    a hand-written literal on either side and pinning it to one op would claim
    LESS generality than C has — which is the same defect mirrored.

    So the pin becomes an AGREEMENT, derived on both sides, exactly as the
    plain op set already is. Its old instruction ("lower
    CEIL_SURFACE_A_UNSUPPORTED_FORMS if the body now routes through the shared
    op table") is the change rc452 makes.
    """
    c_ops = _c_fold_body_ops()
    py_ops = set(_compose._RUN_C_FOLD_OPS)
    assert py_ops == c_ops, (
        "the Python fold-body set and the C `bin` column disagree.\n"
        "  python-only (chain admitted, C body declines -> wasted C attempt): "
        f"{sorted(py_ops - c_ops)}\n"
        "  C-only (real capability unreachable from run_cascade_chain — the "
        f"rc447 defect class): {sorted(c_ops - py_ops)}")


def test_the_shipped_api_ACTUALLY_drives_the_C_runner():
    """END TO END, through ``run_cascade_chain`` — not through ctypes.

    This is the assertion the whole rc turns on: the parity gates all reach
    around the predicate, so only a test that goes through the public surface
    can prove the C path is reachable at all.
    """
    from srmech.dsl import run_cascade_chain
    if _compose._compose_lib("srmech_chain_run",
                             "srmech_chain_run_arena_bytes") is None:
        pytest.skip(
            "no native library — with no .so there IS no C runner to drive, so "
            "zero hits is CORRECT here, not the rc447 defect this asserts. The "
            "pure-Python fallback CI cell runs exactly this configuration.")
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
