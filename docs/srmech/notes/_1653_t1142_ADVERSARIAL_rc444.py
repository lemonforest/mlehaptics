#!/usr/bin/env python3
"""gh #1653 / `#T1142` — ADVERSARIAL RE-DERIVATION of the map_op lapse census.

Independent of ``_1653_t1142_planted_rc444.py`` on FOUR axes, so a shared
harness bug cannot produce the same answer twice:

1. ENTRY ROUTE — ``_catalog.register_catalog_dir()`` (the API arm), NOT the
   ``SRMECH_CASCADE_PATH`` env-var arm the original used.
2. OP NAMES — a different prefix (``adv1142_``), so no fixture is shared.
3. UNIT LEVEL — ``_composite_op_refs`` is also called DIRECTLY on a hand-built
   dict, with no file, no TOML parse, no catalog and no loader in the path.
   That arm cannot have an arena / marshalling / env-var confound at all.
4. RECURSION LIMIT — the cycle cell is ALSO run at the DEFAULT limit (the
   original only measured it at 220 and flagged that as a caveat).

Every rejection is attributed to (exception type, message, raising file:lineno
from the traceback's last frame). Writes only under docs/srmech/notes/.

Run:
    cd docs/srmech/python && python3 ../notes/_1653_t1142_ADVERSARIAL_rc444.py
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
from srmech.dsl import _toml_chain  # noqa: E402

ROOT = _HERE / "_1653_t1142_adversarial_fixtures"
OUT = _HERE / "_1653_t1142_ADVERSARIAL_rc444.ndjson"

PLANTED = "adv1142_absent_op"

FIXTURES = {
    "ADV_map_unknown": {"m.toml": '''[cascade]
name = "adv1142_map_unknown"
purpose = "adversarial: map_op names an absent op"
kind = "stage"

[composite]
[[composite.stage]]
map_op = "%s"
''' % PLANTED},
    "ADV_fold_unknown": {"f.toml": '''[cascade]
name = "adv1142_fold_unknown"
purpose = "adversarial control: fold_op names an absent op"
kind = "stage"

[composite]
[[composite.stage]]
fold_init = 0
fold_op = "%s"
''' % PLANTED},
    "ADV_reduce_unknown": {"r.toml": '''[cascade]
name = "adv1142_reduce_unknown"
purpose = "adversarial control 2: reduce_op names an absent op"
kind = "stage"

[composite]
[[composite.stage]]
reduce_op = "%s"
''' % PLANTED},
    "ADV_parallel_unknown": {"p.toml": '''[cascade]
name = "adv1142_parallel_unknown"
purpose = "adversarial control 3: parallel_body names an absent op"
kind = "stage"

[composite]
[[composite.stage]]
parallel_body = "%s"
''' % PLANTED},
    # 3-node cycle through map_op (original only planted a 2-node cycle)
    "ADV_map_cycle3": {
        "a.toml": '''[cascade]
name = "adv1142_c3_a"
purpose = "adversarial: 3-node cycle leg 1 via map_op"
kind = "stage"

[composite]
[[composite.stage]]
map_op = "adv1142_c3_b"
''',
        "b.toml": '''[cascade]
name = "adv1142_c3_b"
purpose = "adversarial: 3-node cycle leg 2 via op"
kind = "stage"

[composite]
[[composite.stage]]
op = "adv1142_c3_c"
''',
        "c.toml": '''[cascade]
name = "adv1142_c3_c"
purpose = "adversarial: 3-node cycle leg 3 back to leg 1"
kind = "stage"

[composite]
[[composite.stage]]
op = "adv1142_c3_a"
''',
    },
    # SELF-cycle through map_op: the shortest possible cycle
    "ADV_map_selfcycle": {"s.toml": '''[cascade]
name = "adv1142_self"
purpose = "adversarial: map_op points at its OWN descriptor"
kind = "stage"

[composite]
[[composite.stage]]
map_op = "adv1142_self"
'''},
    # self-cycle on a COVERED key, as the control for the above
    "ADV_op_selfcycle": {"s.toml": '''[cascade]
name = "adv1142_self_op"
purpose = "adversarial control: op points at its OWN descriptor"
kind = "stage"

[composite]
[[composite.stage]]
op = "adv1142_self_op"
'''},
    # map_op stage nested inside a sub_chain (the recursion arm at :313-316)
    "ADV_map_in_subchain": {"n.toml": '''[cascade]
name = "adv1142_nested"
purpose = "adversarial: absent map_op INSIDE a sub_chain (recursion arm)"
kind = "stage"

[composite]
[[composite.stage]]
loop_n = 2
[[composite.stage.sub_chain]]
map_op = "%s"
''' % PLANTED},
    "ADV_op_in_subchain": {"n.toml": '''[cascade]
name = "adv1142_nested_op"
purpose = "adversarial control: absent op INSIDE a sub_chain"
kind = "stage"

[composite]
[[composite.stage]]
loop_n = 2
[[composite.stage.sub_chain]]
op = "%s"
''' % PLANTED},
}

EXPECT_NAMES = {
    "ADV_map_unknown": ["adv1142_map_unknown"],
    "ADV_fold_unknown": ["adv1142_fold_unknown"],
    "ADV_reduce_unknown": ["adv1142_reduce_unknown"],
    "ADV_parallel_unknown": ["adv1142_parallel_unknown"],
    "ADV_map_cycle3": ["adv1142_c3_a", "adv1142_c3_b", "adv1142_c3_c"],
    "ADV_map_selfcycle": ["adv1142_self"],
    "ADV_op_selfcycle": ["adv1142_self_op"],
    "ADV_map_in_subchain": ["adv1142_nested"],
    "ADV_op_in_subchain": ["adv1142_nested_op"],
}

COVERED_KEY = {
    "ADV_map_unknown": False, "ADV_fold_unknown": True,
    "ADV_reduce_unknown": True, "ADV_parallel_unknown": True,
    "ADV_map_cycle3": False, "ADV_map_selfcycle": False,
    "ADV_op_selfcycle": True, "ADV_map_in_subchain": False,
    "ADV_op_in_subchain": True,
}

ORDER = list(FIXTURES)


def _frame(exc):
    fr = traceback.extract_tb(exc.__traceback__)
    if not fr:
        return "<no-traceback>"
    return "%s:%d" % (Path(fr[-1].filename).name, fr[-1].lineno)


def _write():
    for cell, files in FIXTURES.items():
        d = ROOT / cell
        d.mkdir(parents=True, exist_ok=True)
        for n, body in files.items():
            (d / n).write_text(body, encoding="utf-8")


def _cell(cell):
    """Load via register_catalog_dir (the API arm) — NOT the env var."""
    d = ROOT / cell
    rec = {"record": "cell", "cell": cell, "dir": str(d),
           "entry_route": "_catalog.register_catalog_dir (API arm)",
           "key_covered_by_gate": COVERED_KEY[cell],
           "files": sorted(p.name for p in d.glob("*.toml"))}
    # hard hygiene: the env-var arm must be OFF so the two routes can't mix
    assert "SRMECH_CASCADE_PATH" not in os.environ, "env arm must be unset"
    del _catalog._USER_CATALOG_DIRS[:]
    _catalog.register_catalog_dir(d)
    rec["registered_dirs"] = [str(p) for p in _catalog._USER_CATALOG_DIRS]
    try:
        cat = _catalog.load_catalog()
    except BaseException as exc:                          # noqa: BLE001
        msg = str(exc)
        rec.update(load="RAISED", exc_type=type(exc).__name__, exc_msg=msg,
                   raised_at=_frame(exc))
        mentioned = [n for n in EXPECT_NAMES[cell] if n in msg]
        rec["read_our_file_guard"] = mentioned
        rec["verdict"] = ("GUARANTEE FIRES" if mentioned else "UNATTRIBUTED")
        return rec
    listed = [n for n in EXPECT_NAMES[cell] if n in cat]
    rec.update(load="LOADED CLEAN", exc_type=None, exc_msg=None,
               raised_at=None, catalog_total=len(cat),
               loaded_the_dir_guard="%s of %s" % (listed, EXPECT_NAMES[cell]))
    if sorted(listed) != sorted(EXPECT_NAMES[cell]):
        rec["verdict"] = "UNATTRIBUTED (register_catalog_dir not honoured)"
        return rec
    rec["verdict"] = "GUARANTEE LAPSES (loaded clean)"
    # what it costs at the DEFAULT recursion limit (the original's caveat)
    rec["default_recursionlimit"] = sys.getrecursionlimit()
    try:
        dsl.lookup_cascade_op(EXPECT_NAMES[cell][0])
        rec["lookup_at_default_limit"] = "RESOLVED"
    except BaseException as exc:                          # noqa: BLE001
        m = str(exc)
        rec["lookup_at_default_limit"] = "RAISED"
        rec["lookup_exc_type"] = type(exc).__name__
        rec["lookup_exc_msg"] = m if len(m) <= 300 else m[:300] + "...[trunc]"
        rec["lookup_raised_at"] = _frame(exc)
    return rec


def _unit_arm():
    """Pure-unit arm: call _composite_op_refs on hand-built dicts.

    No file, no TOML, no catalog, no loader — so a harness/marshalling
    confound is structurally impossible here.
    """
    cases = [
        ("op", {"stage": [{"op": "X"}]}),
        ("fold_op", {"stage": [{"fold_init": 0, "fold_op": "X"}]}),
        ("reduce_op", {"stage": [{"reduce_op": "X"}]}),
        ("parallel_body", {"stage": [{"parallel_body": "X"}]}),
        ("map_op", {"stage": [{"map_op": "X"}]}),
        ("body_op", {"stage": [{"body_op": "X"}]}),
        ("map_op-in-sub_chain",
         {"stage": [{"loop_n": 2, "sub_chain": [{"map_op": "X"}]}]}),
        ("op-in-sub_chain",
         {"stage": [{"loop_n": 2, "sub_chain": [{"op": "X"}]}]}),
    ]
    out = []
    for label, comp in cases:
        refs = _catalog._composite_op_refs(comp)
        out.append({"record": "unit_refs", "key": label, "body": comp,
                    "refs_returned": refs, "ref_visible": ("X" in refs)})
    return out


def _discriminator_arm():
    """Which stage keys does the TOML dispatcher actually accept as a form?

    Executed, not read: build a one-stage chain from each key in turn.
    """
    probes = {
        "op": 'op = "magnitude"',
        "fold_op": 'fold_init = 0\nfold_op = "cyclic_gcd"',
        "reduce_op": 'reduce_op = "cyclic_gcd"',
        "parallel_body": 'parallel_body = "chiral_flip"',
        "map_op": 'map_op = "srmech.cascade.leaves.seq_get"',
        "body_op": 'body_op = "magnitude"',
        "loop_n+sub_chain": 'loop_n = 1\n[[stage.sub_chain]]\nop = "magnitude"',
    }
    out = []
    for key, body in probes.items():
        spec = "[chain]\nname = \"adv\"\n\n[[stage]]\n%s\n" % body
        rec = {"record": "discriminator_probe", "key": key,
               "reserved_stage_key": key in _toml_chain._RESERVED_STAGE_KEYS}
        try:
            _toml_chain.build_chain_from_toml_str(spec)
            rec["build"] = "ACCEPTED as a stage form"
        except BaseException as exc:                      # noqa: BLE001
            m = str(exc)
            rec["build"] = "REJECTED"
            rec["exc_type"] = type(exc).__name__
            rec["exc_msg"] = m if len(m) <= 240 else m[:240] + "...[trunc]"
            rec["raised_at"] = _frame(exc)
        out.append(rec)
    return out


def main() -> int:
    _write()
    del _catalog._USER_CATALOG_DIRS[:]
    os.environ.pop("SRMECH_CASCADE_PATH", None)
    _catalog.load_catalog.cache_clear()
    shipped = _catalog.load_catalog()

    # independent re-count of the shipped catalog + map_op usage in descriptors
    cat_dir = Path(_catalog.__file__).resolve().parent.parent / \
        "cascade" / "catalogs" / "cascade_catalog"
    toml_files = sorted(p.name for p in cat_dir.glob("*.toml"))
    map_op_in_shipped = sorted(
        p.name for p in cat_dir.glob("*.toml")
        if "map_op" in p.read_text(encoding="utf-8"))
    composite_in_shipped = sorted(
        n for n, d in shipped.items() if isinstance(d.get("composite"), dict))

    recs = [{
        "record": "env",
        "issue": "gh #1653", "task": "#T1142 adversarial re-derivation",
        "srmech_version": srmech.__version__,
        "has_native": bool(_native.HAS_NATIVE),
        "native_abi": getattr(_native, "NATIVE_ABI_VERSION", None),
        "gate_tuple": list(_catalog._COMPOSITE_OP_KEYS),
        "gate_len": len(_catalog._COMPOSITE_OP_KEYS),
        "shipped_catalog_total": len(shipped),
        "shipped_catalog_toml_files": len(toml_files),
        "shipped_descriptors_containing_map_op": map_op_in_shipped,
        "shipped_descriptors_with_composite_body": composite_in_shipped,
        "reserved_stage_keys": sorted(_toml_chain._RESERVED_STAGE_KEYS),
        "reserved_stage_keys_n": len(_toml_chain._RESERVED_STAGE_KEYS),
    }]

    try:
        for c in ORDER:
            recs.append(_cell(c))
    finally:
        del _catalog._USER_CATALOG_DIRS[:]
        _catalog.load_catalog.cache_clear()

    recs += _unit_arm()
    recs += _discriminator_arm()

    # ── report ──────────────────────────────────────────────────────────────
    print("srmech %s has_native=%s abi=%s" % (
        srmech.__version__, bool(_native.HAS_NATIVE),
        getattr(_native, "NATIVE_ABI_VERSION", None)))
    print("gate = %r (len %d)" % (tuple(recs[0]["gate_tuple"]),
                                  recs[0]["gate_len"]))
    print("shipped: %d catalog entries from %d .toml files; %d with a "
          "[composite] body; descriptors containing 'map_op': %s" % (
              len(shipped), len(toml_files), len(composite_in_shipped),
              map_op_in_shipped or "NONE"))
    print()
    cells = [r for r in recs if r["record"] == "cell"]
    w = max(len(r["cell"]) for r in cells)
    print("%-*s %-6s %-13s %-34s %s" % (w, "cell", "cov?", "load",
                                        "verdict", "raised_at"))
    for r in cells:
        print("%-*s %-6s %-13s %-34s %s" % (
            w, r["cell"], r["key_covered_by_gate"], r["load"], r["verdict"],
            r["raised_at"] or "-"))
    print()
    print("post-load lookup at the DEFAULT recursion limit "
          "(the original census's open caveat):")
    for r in cells:
        if "lookup_at_default_limit" in r:
            print("  %-22s limit=%d -> %s %s @ %s" % (
                r["cell"], r["default_recursionlimit"],
                r["lookup_at_default_limit"], r.get("lookup_exc_type", ""),
                r.get("lookup_raised_at", "-")))
    print()
    print("UNIT arm — _composite_op_refs on hand-built dicts (no file/loader):")
    for r in recs:
        if r["record"] == "unit_refs":
            print("  %-22s -> refs=%-10s visible=%s" % (
                r["key"], r["refs_returned"], r["ref_visible"]))
    print()
    print("DISCRIMINATOR arm — is the key a live stage form? (executed)")
    for r in recs:
        if r["record"] == "discriminator_probe":
            print("  %-18s reserved=%-6s %s %s" % (
                r["key"], r["reserved_stage_key"], r["build"],
                r.get("exc_type", "")))

    n_lapse = sum(1 for r in cells if r["verdict"].startswith("GUARANTEE LAPSES"))
    n_fires = sum(1 for r in cells if r["verdict"] == "GUARANTEE FIRES")
    n_unatt = sum(1 for r in cells if r["verdict"].startswith("UNATTRIBUTED"))
    print("\ntotals: %d cells = %d LAPSE + %d FIRES + %d UNATTRIBUTED" % (
        len(cells), n_lapse, n_fires, n_unatt))
    recs.append({"record": "totals", "cells": len(cells), "lapse": n_lapse,
                 "fires": n_fires, "unattributed": n_unatt})

    with OUT.open("w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print("wrote %s (%d records)" % (OUT, len(recs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
