#!/usr/bin/env python3
"""gh #1653 / `#T1142` — FIX PROBE + peer-key census (rc444). PROTOTYPE ONLY.

Companion to ``_1653_t1142_planted_rc444.py`` (which proves the lapse 2x2). No
shipped file is edited: each candidate fix is applied as a runtime rebind of
``srmech.dsl._catalog`` module globals, which is faithful because
``_composite_op_refs`` reads ``_COMPOSITE_OP_KEYS`` per call and ``load_catalog``
calls ``_validate_composite`` through the module global.

THREE PASSES over the same fixture set
--------------------------------------
UNPATCHED  rc444 as shipped (re-affirms the lapse, and measures the dotted cells).
FIX-A      the one-liner: ``_COMPOSITE_OP_KEYS += ("map_op",)``. Contract-
           PRESERVING — it makes ``map_op`` obey the same ADR-0008 composite-body
           rule the other four keys already obey.
FIX-B      FIX-A **plus** a dotted-ref exemption in ``_validate_composite``.
           NOT a bug fix — a deliberate CONTRACT CHANGE. It contradicts the
           shipped, passing ratchet
           ``tests/test_dsl_op_naming_boundaries.py:509``
           (``test_composite_descriptor_body_rejects_dotted_stage_ref``), whose
           whole point is that the dotted arm is a BUILDER-surface property and
           a dotted ref inside a ``[composite]`` body is a LOAD error. Measured
           here only so the shipping session can see the cost of each option;
           choosing it means rewriting that ratchet in the same commit.
           Cell ``D_op_dotted`` IS that ratchet's input class, so its column
           reads directly as "pinned test passes (FIRES) / fails (OK-RUNS)".

CELLS
-----
A_map_unknown / A_fold_unknown   guarantee (a), uncovered vs covered key
B_map_cycle   / B_fold_cycle     guarantee (b), uncovered vs covered key
P_map_positive                   dotted map_op body (the documented identity map
                                 ``srmech.cascade.leaves.seq_get``,
                                 ``_chain.py:427``) — accepted + RUN today only
                                 because of the lapse; the contract forbids it
D_op_dotted                      the SAME input class on a COVERED key
                                 (``op = "srmech.cascade.magnitude"``) — the
                                 shipped ratchet's own case, so this column says
                                 whether a pass keeps that ratchet green
E_map_dotted_bad                 dotted map_op body whose module is NOT importable
                                 — bounds the residual FIX-B deliberately leaves

ALSO
----
R2     shipped-catalog non-regression under each pass (21 descriptors,
       ``describe()["cascade_catalog"]``, a shipped declared chain runs).
R3     peer-key census: every place in the tree that enumerates op-naming /
       discriminator keys, and whether it includes ``map_op``.
BONUS  the ``[[cascade.chain]]`` axis: ``_validate_composite`` runs ONLY on a
       ``[composite]`` body (``_catalog.py:293-295``), so a descriptor whose
       executable ``[[cascade.chain]]`` steps name a non-existent op is covered
       by NEITHER guarantee, for ANY key. Measured so the shipping session does
       not mistake the ``map_op`` hole for the whole hole.

Discipline: no abs(), no numpy, no RNG, no stdlib fractions. Writes only under
docs/srmech/notes/.

Run:
    cd docs/srmech/python && python3 ../notes/_1653_t1142_fixprobe_rc444.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PY = _HERE.parent / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

import srmech  # noqa: E402
from srmech import _native  # noqa: E402
from srmech import dsl  # noqa: E402
from srmech.dsl import _catalog  # noqa: E402

NDJSON_OUT = _HERE / "_1653_t1142_fixprobe_rc444.ndjson"
PLANTED = _HERE / "_1653_t1142_planted_rc444.py"

FIX_A_KEYS = ("op", "fold_op", "reduce_op", "parallel_body", "map_op")


def _load_planted_module():
    spec = importlib.util.spec_from_file_location("_t1142_planted", PLANTED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── FIX-B prototype: the shipped _validate_composite + a dotted-ref exemption ─
def _validate_composite_fix_b(name, catalog, path):
    """``_catalog._validate_composite`` with ONE added clause (marked below).

    The rationale FOR it: a dotted ref can never be a catalog key
    (``lookup_cascade_op:395`` routes a dotted name to the import arm before any
    catalog consultation, and ``load_catalog:258`` rejects a dotted
    ``[cascade].name`` outright), so ``ref not in catalog`` is a test a dotted
    body can never pass.

    The rationale AGAINST it: that asymmetry is the pinned ADR-0008 boundary —
    the dotted arm is a BUILDER-surface property, and
    ``tests/test_dsl_op_naming_boundaries.py:509`` executes exactly this input
    class and REQUIRES the load error. So this clause is a contract change, and
    it also weakens the guarantee: an unimportable dotted body (cell
    ``E_map_dotted_bad``) then goes uncaught at load and surfaces only at lookup.
    A stricter variant (validate a dotted ref by ATTEMPTING the import at load)
    would keep the load-time guarantee while widening the contract; not
    prototyped here because widening the contract at all is the shipping
    session's call, not this measurement's.
    """
    if name in path:
        raise ValueError(
            f"composite cascade cycle: {' -> '.join(path + (name,))}")
    desc = catalog.get(name)
    if not isinstance(desc, dict):
        raise ValueError(f"composite references unknown cascade op {name!r}")
    composite = desc.get("composite")
    if not isinstance(composite, dict):
        return
    stages = composite.get("stage")
    if not isinstance(stages, list) or not stages:
        raise ValueError(
            f"composite {name!r} ({desc.get('_source')}): [composite] needs a "
            f"non-empty [[composite.stage]] array")
    for ref in _catalog._composite_op_refs(composite):
        if "." in ref:
            continue                      # <-- FIX-B: dotted = import arm
        if ref not in catalog:
            raise ValueError(
                f"composite {name!r} references unknown op {ref!r}; "
                f"catalog: {sorted(catalog)}")
        _validate_composite_fix_b(ref, catalog, path + (name,))


# ── extra fixtures (injected into the planted module's tables) ───────────────
EXTRA_FIXTURES = {
    "D_op_dotted": {
        "d_op_dotted.toml": """
[cascade]
name = "t1142_op_dotted"
purpose = "VALID dotted body on a COVERED key (op = a dotted shipped callable)"
kind = "stage"

[composite]
[[composite.stage]]
op = "srmech.cascade.magnitude"
""",
    },
    "E_map_dotted_bad": {
        "e_map_dotted_bad.toml": """
[cascade]
name = "t1142_map_dotted_bad"
purpose = "dotted map_op body whose module is NOT importable (residual bound)"
kind = "stage"

[composite]
[[composite.stage]]
map_op = "t1142_no_such_module.no_such_attr"
""",
    },
}

EXTRA_META = {
    "D_op_dotted": {
        "guarantee": ("dotted body on a COVERED key — the input class of the "
                      "shipped ratchet tests/test_dsl_op_naming_boundaries.py:509"
                      " (FIRES = that ratchet stays green)"),
        "key": "op (dotted)",
        "covered": True,
        "expect_if_guard_holds": "ValueError at load: references unknown op",
        "names": ["t1142_op_dotted"],
        "must_mention": ["t1142_op_dotted", "srmech.cascade.magnitude"],
        "lookup_probe": "t1142_op_dotted",
        "run_input": -5,
        "run_expect": 5,
        "positive": True,
    },
    "E_map_dotted_bad": {
        "guarantee": "dotted map_op body with an unimportable module",
        "key": "map_op (dotted, bad)",
        "covered": False,
        "expect_if_guard_holds": "ValueError at load (ideal) or at lookup",
        "names": ["t1142_map_dotted_bad"],
        "must_mention": ["t1142_map_dotted_bad", "t1142_no_such_module"],
        "lookup_probe": "t1142_map_dotted_bad",
    },
}

PASS_CELLS = ["A_map_unknown", "A_fold_unknown", "B_map_cycle", "B_fold_cycle",
              "P_map_positive", "D_op_dotted", "E_map_dotted_bad"]


def _shipped_census() -> dict:
    os.environ.pop("SRMECH_CASCADE_PATH", None)
    _catalog.load_catalog.cache_clear()
    cat = _catalog.load_catalog()
    import srmech.introspect as introspect
    d = introspect.describe()["cascade_catalog"]
    ran = dsl.run_cascade_chain("magnitude", {"x": -3.5})
    return {
        "total": len(cat),
        "describe_cascade_catalog": {k: v for k, v in d.items()
                                     if not isinstance(v, dict)},
        "shipped_chain_probe": "run_cascade_chain('magnitude', x=-3.5)",
        "shipped_chain_result": ran,
    }


def _tag(rec: dict) -> str:
    """One-word outcome for the pass table."""
    v = rec["verdict"]
    if v.startswith("GUARANTEE LAPSES"):
        return "LAPSE"
    if v == "GUARANTEE FIRES":
        return "FIRES"
    if v == "POSITIVE CONTROL LOADS":
        return "OK-RUNS" if rec.get("run_ok") else "OK-LOADS"
    return v


def _run_pass(planted, label: str, base_names: list) -> list:
    out = []
    for cell in PASS_CELLS:
        r = planted._run_cell(cell, base_names)
        r["record"] = "cell"
        r["pass"] = label
        r["gate_value"] = list(_catalog._COMPOSITE_OP_KEYS)
        r["validate_fn"] = _catalog._validate_composite.__name__
        r["tag"] = _tag(r)
        out.append(r)
    return out


def main() -> int:
    planted = _load_planted_module()
    planted.FIXTURES.update(EXTRA_FIXTURES)
    planted.CELL_META.update(EXTRA_META)
    planted._write_fixtures()

    os.environ.pop("SRMECH_CASCADE_PATH", None)
    _catalog.load_catalog.cache_clear()
    base_names = sorted(_catalog.load_catalog())

    records = [{
        "record": "env",
        "issue": "gh #1653",
        "task": "#T1142",
        "srmech_version": srmech.__version__,
        "has_native": bool(_native.HAS_NATIVE),
        "native_abi": getattr(_native, "NATIVE_ABI_VERSION", None),
        "unpatched_gate": list(_catalog._COMPOSITE_OP_KEYS),
        "fix_a": "_catalog.py:151 tuple += 'map_op'",
        "fix_b": "FIX-A + skip dotted refs in _validate_composite (:346)",
        "patch_mechanism": (
            "runtime rebind of _catalog module globals; _composite_op_refs reads "
            "_COMPOSITE_OP_KEYS per call and load_catalog calls "
            "_validate_composite through the global, so both rebinds are "
            "equivalent to the source edits (no shipped file touched)"),
        "shipped_catalog_total": len(base_names),
    }]

    orig_keys = _catalog._COMPOSITE_OP_KEYS
    orig_validate = _catalog._validate_composite
    census = {}
    try:
        # PASS 1 — unpatched
        records += _run_pass(planted, "UNPATCHED", base_names)
        census["UNPATCHED"] = _shipped_census()
        # PASS 2 — FIX-A (naive one-liner)
        _catalog._COMPOSITE_OP_KEYS = FIX_A_KEYS
        _catalog.load_catalog.cache_clear()
        records += _run_pass(planted, "FIX-A", base_names)
        census["FIX-A"] = _shipped_census()
        # PASS 3 — FIX-B (one-liner + dotted-ref exemption)
        _catalog._validate_composite = _validate_composite_fix_b
        _catalog.load_catalog.cache_clear()
        records += _run_pass(planted, "FIX-B", base_names)
        census["FIX-B"] = _shipped_census()
    finally:
        _catalog._COMPOSITE_OP_KEYS = orig_keys
        _catalog._validate_composite = orig_validate
        os.environ.pop("SRMECH_CASCADE_PATH", None)
        _catalog.load_catalog.cache_clear()

    records.append({
        "record": "shipped_non_regression",
        "census": census,
        "all_three_identical": (census["UNPATCHED"] == census["FIX-A"]
                                == census["FIX-B"]),
        "shipped_descriptors_using_map_op": 0,
    })

    # ── R3: peer-key census ───────────────────────────────────────────────
    peers = [
        ("srmech/dsl/_catalog.py", r"_COMPOSITE_OP_KEYS\s*=\s*\(([^)]*)\)",
         "composite-stage op-name keys (the load-time validation gate)"),
        ("srmech/dsl/_toml_chain.py",
         r"_RESERVED_STAGE_KEYS\s*=\s*frozenset\(\{([^}]*)\}",
         "reserved stage discriminators (the TOML stage dispatcher)"),
        ("tests/test_dsl_op_naming_boundaries.py",
         r"_CHAIN_OP_KEYS\s*=\s*\(([^)]*)\)",
         "chain-step op-name keys (the dotted-spelling visibility census)"),
        ("tests/test_combinator_kernel_closure.py",
         r"C_COMBINATOR_KEYS\s*=\s*frozenset\(\{([^}]*)\}",
         "C combinator discriminators (mirrors dsl_stage_is_combinator)"),
        ("../c/src/srmech_dsl_chain_run.c", r"disc\[7\]\s*=\s*\{([^}]*)\}",
         "C dsl_stage_is_combinator discriminator array"),
    ]
    for rel, pat, purpose in peers:
        text = (_PY / rel).read_text(encoding="utf-8", errors="replace")
        m = re.search(pat, text, re.S)
        body = m.group(1) if m else ""
        keys = sorted(set(re.findall(r'"([a-z_0-9]+)"', body)))
        records.append({
            "record": "peer_keyset",
            "file": rel,
            "line": (text[:m.start()].count("\n") + 1) if m else None,
            "purpose": purpose,
            "keys": keys,
            "includes_map_op": "map_op" in keys,
        })

    # ── FIX-A consequence: is any BARE catalog name usable as a map body? ──
    # FIX-A confines a composite's map_op to bare catalog names (the ADR-0008
    # boundary). A map body must be DATA-FIRST — body(input_seq, k). If no bare
    # name satisfies that, FIX-A makes map_op un-declarable inside a [composite]
    # until a bare data-first op is minted. Measured by EXECUTION, not by reading.
    usable, rejected = [], []
    for n in sorted(_catalog.load_catalog()):
        try:
            out = dsl.chain().map_indexed(n).run([2, 3, 4])
            usable.append({"op": n, "output": out})
        except BaseException as exc:                  # noqa: BLE001
            rejected.append({"op": n, "exc": type(exc).__name__})
    records.append({
        "record": "bare_map_body_census",
        "question": ("after FIX-A, can any BARE catalog op serve as a "
                     "[composite] map_op body?"),
        "probe": "dsl.chain().map_indexed(<bare name>).run([2, 3, 4])",
        "n_catalog": len(rejected) + len(usable),
        "n_usable": len(usable),
        "usable": usable,
        "rejected": rejected,
        "consequence": (
            "0 usable => FIX-A leaves map_op correct-but-undeclarable in a "
            "[composite] body until a bare data-first op (e.g. a seq_get "
            "descriptor) is minted, or the ADR-0008 boundary is widened"
            if not usable else
            "at least one bare body exists, so FIX-A leaves map_op declarable"),
    })

    # ── BONUS: the [[cascade.chain]] axis ─────────────────────────────────
    bonus_dir = planted.FIXTURE_ROOT / "X_chain_unknown"
    bonus_dir.mkdir(parents=True, exist_ok=True)
    (bonus_dir / "x_chain_unknown.toml").write_text(
        '[cascade]\n'
        'name = "t1142_chain_unknown"\n'
        'purpose = "planted: an executable [[cascade.chain]] step names a '
        'non-existent op"\n'
        'kind = "stage"\n\n'
        '[[cascade.chain]]\n'
        'chain_schema_version = 2\n'
        'variant = "default"\n'
        'summary = "planted unknown-op chain step"\n'
        'returns = "nothing — the op does not exist"\n'
        '[[cascade.chain.steps]]\n'
        'op = "t1142_no_such_op_planted"\n'
        'out = "r"\n',
        encoding="utf-8")
    os.environ["SRMECH_CASCADE_PATH"] = str(bonus_dir)
    _catalog.load_catalog.cache_clear()
    bonus = {
        "record": "bonus_cascade_chain_axis",
        "fixture_dir": str(bonus_dir),
        "question": ("does load_catalog validate a [[cascade.chain]] step's "
                     "op-name (any key)?"),
        "gate": ("_catalog.py:293-295 — _validate_composite runs only when "
                 "desc.get('composite') is a dict"),
    }
    try:
        cat = _catalog.load_catalog()
        bonus["load"] = "LOADED CLEAN"
        bonus["fixture_listed"] = "t1142_chain_unknown" in cat
        bonus["verdict"] = (
            "NO LOAD-TIME VALIDATION on the [[cascade.chain]] axis"
            if "t1142_chain_unknown" in cat
            else "UNATTRIBUTED (fixture not in catalog — harness failure)")
        try:
            dsl.run_cascade_chain("t1142_chain_unknown")
            bonus["run"] = "RAN (unexpected)"
        except BaseException as exc:                  # noqa: BLE001
            bonus["run"] = "RAISED"
            bonus["run_exc_type"] = type(exc).__name__
            m = str(exc)
            bonus["run_exc_msg"] = m if len(m) <= 300 else m[:300] + "...[trunc]"
            bonus["run_raised_at"] = planted._last_frame(exc)
    except BaseException as exc:                      # noqa: BLE001
        bonus["load"] = "RAISED"
        bonus["load_exc_type"] = type(exc).__name__
        bonus["load_exc_msg"] = str(exc)
        bonus["load_raised_at"] = planted._last_frame(exc)
        bonus["verdict"] = "the [[cascade.chain]] axis IS validated at load"
    finally:
        os.environ.pop("SRMECH_CASCADE_PATH", None)
        _catalog.load_catalog.cache_clear()
    records.append(bonus)

    # ── report ────────────────────────────────────────────────────────────
    print("srmech %s  has_native=%s  abi=%s" % (
        srmech.__version__, bool(_native.HAS_NATIVE),
        getattr(_native, "NATIVE_ABI_VERSION", None)))
    print("\nthree passes over 7 cells "
          "(FIRES = load-time ValueError, LAPSE = loaded clean, "
          "OK-RUNS = loaded+resolved+ran):")
    w = max(len(c) for c in PASS_CELLS)
    hdr = "%-*s | %-22s | %-22s | %-22s" % (w, "cell", "UNPATCHED", "FIX-A",
                                            "FIX-B")
    print(hdr)
    print("-" * len(hdr))
    for cell in PASS_CELLS:
        row = []
        for label in ("UNPATCHED", "FIX-A", "FIX-B"):
            r = [x for x in records if x.get("record") == "cell"
                 and x.get("pass") == label and x["cell"] == cell][0]
            row.append("%-7s %s" % (r["tag"],
                                    r["load_exc_type"] or r.get("lookup", "")))
        print("%-*s | %-22s | %-22s | %-22s" % (w, cell, row[0], row[1], row[2]))
    nr = [r for r in records if r["record"] == "shipped_non_regression"][0]
    print("\nshipped catalog identical across all three passes: %s" %
          nr["all_three_identical"])
    print("  %s" % json.dumps(census["UNPATCHED"], sort_keys=True))
    print("\npeer key-sets that enumerate op-naming / discriminator keys:")
    for r in records:
        if r.get("record") != "peer_keyset":
            continue
        print("  %-46s :%-5s map_op=%-5s %s" % (
            r["file"], r["line"], r["includes_map_op"], r["keys"]))
    bmc = [r for r in records if r["record"] == "bare_map_body_census"][0]
    print("\nbare catalog names usable as a [composite] map_op body: %d of %d"
          % (bmc["n_usable"], bmc["n_catalog"]))
    print("  -> %s" % bmc["consequence"])
    print("\nBONUS [[cascade.chain]] axis: load=%s -> %s" % (
        bonus["load"], bonus["verdict"]))
    print("      run -> %s %s @ %s" % (
        bonus.get("run"), bonus.get("run_exc_type", ""),
        bonus.get("run_raised_at", "-")))

    with NDJSON_OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print("\nwrote %s (%d records)" % (NDJSON_OUT, len(records)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
