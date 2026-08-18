#!/usr/bin/env python3
"""gh #1653 / `#T1142` — PLANTED-FAILURE proof for the `map_op` composite-validation lapse.

WHAT IS UNDER TEST
------------------
``srmech/dsl/_catalog.py:151``::

    _COMPOSITE_OP_KEYS = ("op", "fold_op", "reduce_op", "parallel_body")

That tuple is the ONLY thing ``_composite_op_refs`` (``:308``) reads out of a
``[[composite.stage]]`` table, and ``_composite_op_refs`` is the ONLY source of
edges for ``_validate_composite`` (``:320``) — which carries BOTH load-time
guarantees the loader's own docstring promises (``load_catalog`` ``Raises``
block, ``:224-228``):

  (a) every referenced op RESOLVES  -> ``composite references unknown op`` (:348)
  (b) the composite graph is ACYCLIC -> ``composite cascade cycle``          (:330)

``map_op`` is the SIXTH combinator's discriminator (rc420, `#T1114`) — a real,
reserved, executable stage key (``_toml_chain.py:92`` ``_RESERVED_STAGE_KEYS``,
dispatched at ``:314``; C peer ``srmech_dsl_chain_run.c:747``
``dsl_run_map_indexed``, and C's own combinator-discriminator array at ``:639``
DOES list it). It is absent from ``_COMPOSITE_OP_KEYS``.

THE 2x2 (plus two attribution cells)
------------------------------------
                        | guarantee (a) unknown-op | guarantee (b) cycle
    map_op   (uncovered)|   A_map_unknown          |   B_map_cycle
    fold_op  (CONTROL)  |   A_fold_unknown         |   B_fold_cycle

The control cells are load-bearing: without them an absent error proves only
that nothing fired, not that the SAME planted defect fires when the key IS in
the tuple. ``fold_op`` (not ``op``) is the control on purpose — ``op`` is the
degenerate case that every existing test already pins
(``tests/test_byo_cascade_toml.py``), while ``fold_op`` is a genuine peer of
``map_op``: both are combinator BODY keys, one covered and one not.

Cell ``P_map_positive`` is the SILENT-ACCEPTANCE cell: a ``map_op`` composite
whose body is the documented identity map (``srmech.cascade.leaves.seq_get``,
``_chain.py:427``) loads, resolves and RUNS. That matters twice over —

* it proves the lapse is not a moot guard on dead grammar (the surface executes);
* and per the SHIPPED contract that descriptor should never have loaded at all.
  ``tests/test_dsl_op_naming_boundaries.py:509``
  (``test_composite_descriptor_body_rejects_dotted_stage_ref``) pins the
  ADR-0008 boundary that a DOTTED ref inside a ``[composite]`` body is rejected
  at load — the dotted arm is a BUILDER-surface property. The lapse is the only
  reason this one is accepted, so the ``map_op`` hole is not merely a missing
  error: it is a hole through which a contract-forbidden descriptor becomes a
  live, running catalog op.

Cells ``A_map_unknown`` / ``B_map_cycle`` additionally record the POST-LOAD
lookup outcome, i.e. what the lapse costs (when + what the caller sees instead).

CONFOUND GUARDS (an unattributed rejection is worse than nothing)
----------------------------------------------------------------
* Every cell runs against its OWN directory via ``SRMECH_CASCADE_PATH`` with
  ``load_catalog.cache_clear()`` — one planted defect per load, so no cell can
  mask another.
* HARNESS-LOADED-THE-DIR guard: on a successful load the fixture's op-names MUST
  be present in the returned catalog. If they are not, the env var was not
  honoured and the cell is reported ``UNATTRIBUTED`` (not "lapse").
* HARNESS-READ-OUR-FILE guard: on a raising load the exception message MUST name
  the fixture's own op / planted-op name. Otherwise ``UNATTRIBUTED``.
* Every fired error is attributed to a concrete ``file:lineno`` taken from the
  traceback's last frame, not from reading the source.
* ``_USER_CATALOG_DIRS`` is asserted empty (this harness uses ONLY the env-var
  arm, so ``register_catalog_dir``'s global is never mutated).
* The cycle-lookup probe lowers ``sys.setrecursionlimit`` to 220 for the
  duration (declared in the record as ``harness_note``) so an unguarded cycle
  raises a catchable ``RecursionError`` instead of risking a C-stack overflow.
  The limit is restored immediately.

Discipline: no ``abs()``, no numpy, no RNG, no stdlib ``fractions``; fixtures are
written under ``docs/srmech/notes/`` only — never into the shipped catalog dir.

Run:
    cd docs/srmech/python && python3 ../notes/_1653_t1142_planted_rc444.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PY = _HERE.parent / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

import srmech  # noqa: E402
from srmech import _native  # noqa: E402
from srmech import dsl  # noqa: E402
from srmech.dsl import _catalog  # noqa: E402

FIXTURE_ROOT = _HERE / "_1653_t1142_fixtures"
NDJSON_OUT = _HERE / "_1653_t1142_planted_rc444.ndjson"

# ── the planted fixtures ────────────────────────────────────────────────────
# Each value is {filename: toml-body}. Every op-name is prefixed t1142_ so it
# can never collide with (or shadow) a shipped A-tier name.

_PLANTED_OP = "t1142_no_such_op_planted"

FIXTURES = {
    # (a) unknown-op, key = map_op  (UNCOVERED)
    "A_map_unknown": {
        "a_map_unknown.toml": """
[cascade]
name = "t1142_map_unknown"
purpose = "planted: map_op names a non-existent op (guarantee (a), map_op)"
kind = "stage"

[composite]
[[composite.stage]]
map_op = "%s"
""" % _PLANTED_OP,
    },
    # (a) unknown-op, key = fold_op  (CONTROL — key IS in _COMPOSITE_OP_KEYS)
    "A_fold_unknown": {
        "a_fold_unknown.toml": """
[cascade]
name = "t1142_fold_unknown"
purpose = "planted: fold_op names a non-existent op (guarantee (a), CONTROL)"
kind = "stage"

[composite]
[[composite.stage]]
fold_init = 0
fold_op = "%s"
""" % _PLANTED_OP,
    },
    # (b) cycle, key = map_op  (UNCOVERED):  A --map_op--> B --op--> A
    "B_map_cycle": {
        "b_map_cycle_a.toml": """
[cascade]
name = "t1142_map_cycle_a"
purpose = "planted: cycle leg 1 — map_op points at leg 2 (guarantee (b), map_op)"
kind = "stage"

[composite]
[[composite.stage]]
map_op = "t1142_map_cycle_b"
""",
        "b_map_cycle_b.toml": """
[cascade]
name = "t1142_map_cycle_b"
purpose = "planted: cycle leg 2 — plain op points back at leg 1"
kind = "stage"

[composite]
[[composite.stage]]
op = "t1142_map_cycle_a"
""",
    },
    # (b) cycle, key = fold_op  (CONTROL):  A --fold_op--> B --op--> A
    "B_fold_cycle": {
        "b_fold_cycle_a.toml": """
[cascade]
name = "t1142_fold_cycle_a"
purpose = "planted: cycle leg 1 — fold_op points at leg 2 (guarantee (b), CONTROL)"
kind = "stage"

[composite]
[[composite.stage]]
fold_init = 0
fold_op = "t1142_fold_cycle_b"
""",
        "b_fold_cycle_b.toml": """
[cascade]
name = "t1142_fold_cycle_b"
purpose = "planted: cycle leg 2 — plain op points back at leg 1"
kind = "stage"

[composite]
[[composite.stage]]
op = "t1142_fold_cycle_a"
""",
    },
    # POSITIVE control: a VALID map_op composite. Proves the grammar the lapse
    # sits on is live (loads, resolves, runs) — the lapse is not moot.
    "P_map_positive": {
        "p_map_positive.toml": """
[cascade]
name = "t1142_map_positive"
purpose = "valid map_op composite: the indexed identity map (seq_get)"
kind = "stage"

[composite]
[[composite.stage]]
map_op = "srmech.cascade.leaves.seq_get"
""",
    },
}

# Which op-name each cell expects to be LISTED if the load succeeds, and which
# name a FIRED error message must mention (the two confound guards).
CELL_META = {
    "A_map_unknown": {
        "guarantee": "(a) unknown-op resolves at load",
        "key": "map_op",
        "covered": False,
        "expect_if_guard_holds": "ValueError: composite references unknown op",
        "names": ["t1142_map_unknown"],
        "must_mention": ["t1142_map_unknown", _PLANTED_OP],
        "lookup_probe": "t1142_map_unknown",
    },
    "A_fold_unknown": {
        "guarantee": "(a) unknown-op resolves at load",
        "key": "fold_op",
        "covered": True,
        "expect_if_guard_holds": "ValueError: composite references unknown op",
        "names": ["t1142_fold_unknown"],
        "must_mention": ["t1142_fold_unknown", _PLANTED_OP],
        "lookup_probe": "t1142_fold_unknown",
    },
    "B_map_cycle": {
        "guarantee": "(b) composite graph is acyclic",
        "key": "map_op",
        "covered": False,
        "expect_if_guard_holds": "ValueError: composite cascade cycle",
        "names": ["t1142_map_cycle_a", "t1142_map_cycle_b"],
        "must_mention": ["t1142_map_cycle_a", "t1142_map_cycle_b"],
        "lookup_probe": "t1142_map_cycle_a",
    },
    "B_fold_cycle": {
        "guarantee": "(b) composite graph is acyclic",
        "key": "fold_op",
        "covered": True,
        "expect_if_guard_holds": "ValueError: composite cascade cycle",
        "names": ["t1142_fold_cycle_a", "t1142_fold_cycle_b"],
        "must_mention": ["t1142_fold_cycle_a", "t1142_fold_cycle_b"],
        "lookup_probe": "t1142_fold_cycle_a",
    },
    "P_map_positive": {
        "guarantee": ("SILENT-ACCEPTANCE control — a map_op composite the "
                      "shipped contract forbids (dotted body; pinned by "
                      "tests/test_dsl_op_naming_boundaries.py:509) loads, "
                      "resolves and RUNS"),
        "key": "map_op",
        "covered": False,
        "expect_if_guard_holds": "loads clean, resolves, runs",
        "names": ["t1142_map_positive"],
        "must_mention": [],
        "lookup_probe": "t1142_map_positive",
        # A run probe: resolve, then RUN. Present => _run_cell executes the
        # resolved op on `run_input` and records the output (a lapse cell has
        # no run probe — there is nothing legitimate to run).
        "run_input": [7, 8, 9],
        "run_expect": [7, 8, 9],
        "positive": True,
    },
}

CELL_ORDER = ["A_map_unknown", "A_fold_unknown", "B_map_cycle", "B_fold_cycle",
              "P_map_positive"]


def _write_fixtures() -> None:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    for cell, files in FIXTURES.items():
        d = FIXTURE_ROOT / cell
        d.mkdir(parents=True, exist_ok=True)
        for fname, body in files.items():
            (d / fname).write_text(body.lstrip("\n"), encoding="utf-8")


def _last_frame(exc: BaseException) -> str:
    """`file:lineno` of the traceback's last frame — the line that RAISED."""
    frames = traceback.extract_tb(exc.__traceback__)
    if not frames:
        return "<no-traceback>"
    f = frames[-1]
    return "%s:%d" % (Path(f.filename).name, f.lineno)


def _shipped_baseline() -> dict:
    os.environ.pop("SRMECH_CASCADE_PATH", None)
    _catalog.load_catalog.cache_clear()
    cat = _catalog.load_catalog()
    return {"shipped_total": len(cat), "shipped_names": sorted(cat)}


def _run_cell(cell: str, baseline_names: list) -> dict:
    meta = CELL_META[cell]
    d = FIXTURE_ROOT / cell
    rec = {
        "record": "cell",
        "cell": cell,
        "guarantee": meta["guarantee"],
        "key": meta["key"],
        "key_in_COMPOSITE_OP_KEYS": meta["covered"],
        "fixture_dir": str(d),
        "fixture_files": sorted(p.name for p in d.glob("*.toml")),
        "expect_if_guard_holds": meta["expect_if_guard_holds"],
    }
    os.environ["SRMECH_CASCADE_PATH"] = str(d)
    _catalog.load_catalog.cache_clear()
    assert not _catalog._USER_CATALOG_DIRS, (
        "harness hygiene: _USER_CATALOG_DIRS must stay empty (env-var arm only)")
    try:
        cat = _catalog.load_catalog()
    except BaseException as exc:                      # noqa: BLE001 — we classify
        msg = str(exc)
        rec["load"] = "RAISED"
        rec["load_exc_type"] = type(exc).__name__
        rec["load_exc_msg"] = msg
        rec["load_raised_at"] = _last_frame(exc)
        mentioned = [n for n in meta["must_mention"] if n in msg]
        rec["confound_guard"] = "read-our-file: mentioned=%s" % mentioned
        if meta["must_mention"] and not mentioned:
            rec["verdict"] = "UNATTRIBUTED"
            rec["verdict_note"] = (
                "load raised but the message names none of this cell's planted "
                "op-names — cannot attribute the rejection to the planted defect")
        else:
            rec["verdict"] = "GUARANTEE FIRES"
        rec["lookup"] = "n/a (never loaded)"
        return rec

    # Loaded. Confound guard: did the harness actually read the fixture dir?
    listed = [n for n in meta["names"] if n in cat]
    rec["load"] = "LOADED CLEAN"
    rec["load_exc_type"] = None
    rec["load_exc_msg"] = None
    rec["load_raised_at"] = None
    rec["catalog_total"] = len(cat)
    rec["catalog_delta_vs_shipped"] = len(cat) - len(baseline_names)
    rec["fixture_names_listed"] = listed
    rec["confound_guard"] = "loaded-the-dir: listed=%s of %s" % (
        listed, meta["names"])
    if sorted(listed) != sorted(meta["names"]):
        rec["verdict"] = "UNATTRIBUTED"
        rec["verdict_note"] = (
            "load succeeded but the fixture op-names are NOT in the catalog — "
            "SRMECH_CASCADE_PATH was not honoured; this is a harness failure, "
            "not a guarantee lapse")
        rec["lookup"] = "not attempted (harness failure)"
        return rec
    rec["verdict"] = ("POSITIVE CONTROL LOADS" if meta.get("positive")
                      else "GUARANTEE LAPSES (loaded clean, no error)")

    # What the lapse COSTS: the post-load lookup / run outcome.
    probe = meta["lookup_probe"]
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(220)
    rec["harness_note"] = (
        "lookup probe ran with sys.setrecursionlimit(220) (restored after) so an "
        "unguarded composite cycle raises a catchable RecursionError rather than "
        "risking a C-stack overflow; default was %d" % old_limit)
    try:
        fn = dsl.lookup_cascade_op(probe)
        rec["lookup"] = "RESOLVED"
        rec["lookup_exc_type"] = None
        rec["lookup_exc_msg"] = None
        rec["lookup_raised_at"] = None
        if meta.get("run_input") is not None:
            got = fn(meta["run_input"])
            got = list(got) if isinstance(got, (list, tuple)) else got
            rec["run_input"] = meta["run_input"]
            rec["run_output"] = got
            rec["run_ok"] = (got == meta["run_expect"])
    except BaseException as exc:                      # noqa: BLE001
        rec["lookup"] = "RAISED"
        rec["lookup_exc_type"] = type(exc).__name__
        m = str(exc)
        rec["lookup_exc_msg"] = m if len(m) <= 400 else m[:400] + "...[trunc]"
        rec["lookup_raised_at"] = _last_frame(exc)
    finally:
        sys.setrecursionlimit(old_limit)
    return rec


def main() -> int:
    _write_fixtures()
    base = _shipped_baseline()
    header = {
        "record": "env",
        "issue": "gh #1653",
        "task": "#T1142",
        "srmech_version": srmech.__version__,
        "has_native": bool(_native.HAS_NATIVE),
        "native_abi": getattr(_native, "NATIVE_ABI_VERSION", None),
        "gate_source": "srmech/dsl/_catalog.py:151 _COMPOSITE_OP_KEYS",
        "gate_value": list(_catalog._COMPOSITE_OP_KEYS),
        "map_op_covered": "map_op" in _catalog._COMPOSITE_OP_KEYS,
        "map_op_is_reserved_stage_key": None,   # filled below
        "shipped_catalog_total": base["shipped_total"],
        "fixture_root": str(FIXTURE_ROOT),
    }
    from srmech.dsl import _toml_chain
    header["map_op_is_reserved_stage_key"] = (
        "map_op" in _toml_chain._RESERVED_STAGE_KEYS)

    records = [header]
    try:
        for cell in CELL_ORDER:
            records.append(_run_cell(cell, base["shipped_names"]))
    finally:
        os.environ.pop("SRMECH_CASCADE_PATH", None)
        _catalog.load_catalog.cache_clear()

    # ── the 2x2 ────────────────────────────────────────────────────────────
    by_cell = {r["cell"]: r for r in records if r.get("record") == "cell"}
    print("srmech %s  has_native=%s  abi=%s" % (
        header["srmech_version"], header["has_native"], header["native_abi"]))
    print("_COMPOSITE_OP_KEYS = %r   ('map_op' covered: %s)" % (
        tuple(header["gate_value"]), header["map_op_covered"]))
    print("'map_op' in _RESERVED_STAGE_KEYS (i.e. a real stage form): %s" %
          header["map_op_is_reserved_stage_key"])
    print("shipped catalog total: %d" % header["shipped_catalog_total"])
    print()
    hdr = "%-28s %-10s %-6s %-14s %s" % (
        "cell", "key", "cov?", "load", "verdict")
    print(hdr)
    print("-" * len(hdr))
    for cell in CELL_ORDER:
        r = by_cell[cell]
        print("%-28s %-10s %-6s %-14s %s" % (
            cell, r["key"], r["key_in_COMPOSITE_OP_KEYS"], r["load"],
            r["verdict"]))
    print()
    print("2x2 (rows = key, cols = guarantee):")
    grid = {
        ("map_op", "a"): by_cell["A_map_unknown"],
        ("fold_op", "a"): by_cell["A_fold_unknown"],
        ("map_op", "b"): by_cell["B_map_cycle"],
        ("fold_op", "b"): by_cell["B_fold_cycle"],
    }
    print("%-10s | %-42s | %-42s" % ("key", "(a) unknown-op", "(b) cycle"))
    for key in ("map_op", "fold_op"):
        cells = []
        for g in ("a", "b"):
            r = grid[(key, g)]
            tag = ("LAPSE" if r["verdict"].startswith("GUARANTEE LAPSES")
                   else "FIRES" if r["verdict"] == "GUARANTEE FIRES"
                   else r["verdict"])
            detail = (r["load_exc_type"] or "no error")
            cells.append("%-5s (%s @ %s)" % (
                tag, detail, r["load_raised_at"] or "-"))
        print("%-10s | %-42s | %-42s" % (key, cells[0], cells[1]))
    print()
    for cell in ("A_map_unknown", "B_map_cycle"):
        r = by_cell[cell]
        print("%s post-load lookup: %s %s @ %s" % (
            cell, r["lookup"], r.get("lookup_exc_type") or "",
            r.get("lookup_raised_at") or "-"))
    p = by_cell["P_map_positive"]
    print("P_map_positive: lookup=%s run_ok=%s output=%s" % (
        p["lookup"], p.get("run_ok"), p.get("run_output")))

    with NDJSON_OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("\nwrote %s (%d records)" % (NDJSON_OUT, len(records)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
