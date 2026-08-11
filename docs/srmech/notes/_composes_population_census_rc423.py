"""rc423 (`#T1113`) — the `composes` POPULATION census + adjudication-ledger
generator.

COMPUTATIONAL PROVENANCE. Every number in the rc423 CHANGELOG entry, in
``tests/test_composes_population_rc423.py``'s ceiling comment, and in the
ADR-0012 §6.1 amendment is produced by THIS script. It is committed so the
census can be re-run rather than believed.

WHAT IT DOES
============
Walks the whole shipped registry through the **rc412 instrument** — the
identity-resolved AST call-graph in ``tests/test_composes_grain_rc412.py`` —
and partitions every op into exactly one adjudication tier:

  DECLARED   already carries a non-empty ``composes`` (the rc305/rc412/rc419/
             rc422 human-traced ROSTER). Untouched here.
  LEAF       ``_derived(name, depth=3)`` is EMPTY. "This op composes nothing
             registered" is then a MEASURED statement, not an absence.
  SINGLE     the op's OWN BODY directly calls exactly ONE registered op
             (``_derived(name, depth=1)`` is a singleton). The ordered tuple
             is FORCED — a one-element sequence has exactly one ordering — so
             no human trace is needed and none is guessed.
  REFUSED    a tier-eligible row a prior rc reviewed and deliberately declined.
  RESIDUAL   everything else: two or more direct call edges, where ORDER is a
             human act (rc412 measured lexical first-call order at 0 of 2 on
             ground truth). These are what the down-only ceiling drains.

WHY THE INSTRUMENT IS IMPORTED, NOT RE-IMPLEMENTED
==================================================
A census that re-implements the gate's derivation can drift from it silently,
and then the ledger and the gate disagree about what was measured. This
imports ``tests/composes_derive.py`` — the same module both gates import — so
there is exactly one derivation in the tree.

⚠️ IT IS IDEMPOTENT, AND THAT TOOK A FIX WORTH RECORDING
========================================================
The obvious rule for the DECLARED tier is "the row already carries a non-empty
``composes``". It is wrong, and it is wrong in a way that only shows on the
SECOND run: after the seeding pass the 148 SINGLE rows all carry a tuple, so a
re-run would re-tier every one of them as DECLARED, empty the SINGLE tier, and
produce a ledger against which the population gate fails. A census whose
output changes its own next answer is not a census.

So DECLARED is keyed off ``test_composes_grain_rc412.py::ROSTER`` — the
HAND-TRACED population, which is what "declared" was ever meant to mean here —
and every other row is classified from the derivation alone. Running this
script twice now produces byte-identical output.

USAGE
=====
    PYTHONPATH=docs/srmech/python python3 \
        docs/srmech/notes/_composes_population_census_rc423.py <python-root>

Writes ``tests/composes_adjudication_rc423.ndjson`` (the reviewed ledger the
gate reads) and prints the census table. numpy-free; stdlib only.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# DELIBERATE NON-DECLARATIONS — a tier-eligible row a prior review declined.
#
# This carve-out is DATA, not a silent skip. `covering_catalog` is a depth-1
# singleton on `spin8_center` and the mechanical SINGLE rule would admit it;
# rc422 read the implementation and refused, because the catalog CONSULTS
# spin8_center to recompute two fields a reader would want to disbelieve
# rather than being BUILT FROM it. That review stands. It is recorded here so
# the exception is visible in the census output instead of vanishing.
# ──────────────────────────────────────────────────────────────────────
REFUSED = {
    "srmech.math.covering.covering_catalog": (
        "rc422 reviewed and declined: covering_catalog calls spin8_center to "
        "recompute the two fields a reader would most want to disbelieve, but "
        "the catalog is not BUILT FROM it — the other three reached rows and "
        "all five rejections stand without that call. Declaring it would "
        "over-attribute. The mechanical SINGLE rule would otherwise admit "
        "this row; the refusal is deliberate and is recorded, not silent."
    ),
}


def main() -> int:
    py_root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(py_root))
    sys.path.insert(0, str(py_root / "tests"))

    import srmech
    print(f"srmech : {srmech.__file__}", file=sys.stderr)
    print(f"version: {srmech.__version__}", file=sys.stderr)

    from composes_derive import BY_NAME as by_name, derived

    # ROSTER is the HAND-TRACED population and the only thing that makes a row
    # DECLARED here. Keying off the live `composes` field instead would make
    # this script non-idempotent — see the ⚠️ in the module docstring.
    spec = importlib.util.spec_from_file_location(
        "_rc412_roster", py_root / "tests" / "test_composes_grain_rc412.py")
    rc412 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc412)
    roster = rc412.ROSTER

    names = sorted(by_name)
    print(f"registry: {len(names)}", file=sys.stderr)

    records = []
    for i, name in enumerate(names):
        if i % 100 == 0:
            print(f"  ...{i}/{len(names)}", file=sys.stderr)
        d1 = sorted(derived(name, 1))
        d3 = sorted(derived(name, 3))

        if name in roster:
            tier = "DECLARED"
            composes = list(roster[name])
        elif name in REFUSED:
            tier = "REFUSED"
            composes = []
        elif not d3:
            tier = "LEAF"
            composes = []
        elif len(d1) == 1:
            tier = "SINGLE"
            composes = list(d1)
        else:
            tier = "RESIDUAL"
            composes = []

        records.append({
            "name": name,
            "tier": tier,
            "composes": composes,
            "d1_count": len(d1),
            "d3_count": len(d3),
        })

    # ── the ledger: the ADJUDICATED rows only. RESIDUAL is the complement
    # and is deliberately NOT enumerated — a ledger that listed the residual
    # would make the ceiling a second copy of the same list, and the two
    # would drift.
    ledger = [r for r in records if r["tier"] in ("LEAF", "SINGLE", "REFUSED")]
    out = py_root / "tests" / "composes_adjudication_rc423.ndjson"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for r in sorted(ledger, key=lambda r: (r["tier"], r["name"])):
            fh.write(json.dumps(
                {"name": r["name"], "tier": r["tier"],
                 "composes": r["composes"]},
                sort_keys=True) + "\n")
    print(f"wrote {out} ({len(ledger)} rows)", file=sys.stderr)

    counts = {}
    for r in records:
        counts[r["tier"]] = counts.get(r["tier"], 0) + 1

    print()
    print("=" * 62)
    print(f"  rc423 composes POPULATION census — registry {len(records)}")
    print("=" * 62)
    for tier in ("DECLARED", "SINGLE", "LEAF", "REFUSED", "RESIDUAL"):
        print(f"  {tier:9s} {counts.get(tier, 0):4d}")
    adjudicated = sum(counts.get(t, 0)
                      for t in ("DECLARED", "SINGLE", "LEAF", "REFUSED"))
    print("-" * 62)
    print(f"  adjudicated      {adjudicated:4d}")
    print(f"  UNADJUDICATED    {counts.get('RESIDUAL', 0):4d}   <- the ceiling")
    print(f"  total            {len(records):4d}")
    print()
    print(f"  composes population after seeding: "
          f"{counts.get('DECLARED', 0) + counts.get('SINGLE', 0)}"
          f" / {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
