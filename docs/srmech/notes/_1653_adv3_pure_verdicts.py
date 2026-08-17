"""ADVERSARIAL round-3: the PURE-projection verdict for the 20 grammar rows,
plus the native verdict side by side, so the prototype's Section-3 "py:" column
can be checked against a real measurement instead of a table.

The pure projection is forced the round-1 way: monkeypatch
srmech.dsl._chain._then_native_desc -> None (leaf) and, for the combinators,
NEUTER the native IR by patching _is_c_scalar so the fold seed never nativizes
is NOT enough -- instead we drive both projections and record what each does.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import srmech  # noqa: E402
from srmech.dsl import _chain as _c  # noqa: E402
from srmech.dsl import chain  # noqa: E402


def run(build, force_pure):
    """build() -> Chain-with-.run bound; returns ('OK', repr) or ('RAISE', type, msg)."""
    orig = _c._then_native_desc
    orig_ir = _c.Chain._native_stage_list
    if force_pure:
        _c._then_native_desc = lambda *a, **k: None
        _c.Chain._native_stage_list = lambda self: None
    try:
        v = build()
        return {"outcome": "OK", "value": repr(v)}
    except Exception as exc:  # noqa: BLE001
        return {"outcome": "RAISE", "exc_type": type(exc).__name__, "exc": str(exc)}
    finally:
        _c._then_native_desc = orig
        _c.Chain._native_stage_list = orig_ir


ROWS = [
    ("00 leaf magnitude x=3", lambda: chain().then("magnitude", x=3).run(-3.5),
     "REJECT_UNDECLARED_KEY"),
    ("01 leaf best_rational_signed denom=6",
     lambda: chain().then("best_rational_signed", denom=6).run(0.5),
     "REJECT_UNDECLARED_KEY"),
    ("02 leaf reorient (no orientation)", lambda: chain().then("reorient").run(5),
     "REJECT_MISSING_REQUIRED"),
    ("03 leaf cyclic_gcd (no b)", lambda: chain().then("cyclic_gcd").run(12),
     "REJECT_MISSING_REQUIRED"),
    ("04 leaf no_such_op", lambda: chain().then("no_such_op").run(1), "UNKNOWN_OP"),
    ("05 leaf seq_get i=2", lambda: chain().then("seq_get", i=2).run([5, 6, 7]),
     "UNKNOWN_OP"),
    ("06 fold(1,cyclic_gcd)", lambda: chain().fold(1, "cyclic_gcd").run([12, 18]),
     "ACCEPT"),
    ("07 fold(1,cyclic_gcd,b=5)",
     lambda: chain().fold(1, "cyclic_gcd", b=5).run([12, 18]),
     "REJECT_UNDECLARED_KEY"),
    ("08 fold(1,cyclic_gcd,a=1)",
     lambda: chain().fold(1, "cyclic_gcd", a=1).run([12, 18]),
     "REJECT_UNDECLARED_KEY"),
    ("09 fold(1,cyclic_gcd,bogus=5)",
     lambda: chain().fold(1, "cyclic_gcd", bogus=5).run([12, 18]),
     "REJECT_UNDECLARED_KEY"),
    ("10 fold(1,dotted orientation_compose)",
     lambda: chain().fold(1, "srmech.cascade.leaves.orientation_compose").run([1, -1]),
     "ACCEPT"),
    ("11 fold(1,dotted oc, orientation=1)",
     lambda: chain().fold(1, "srmech.cascade.leaves.orientation_compose",
                          orientation=1).run([1, -1]), "REJECT_UNDECLARED_KEY"),
    ("12 fold(1,dotted oc, bogus=1)",
     lambda: chain().fold(1, "srmech.cascade.leaves.orientation_compose",
                          bogus=1).run([1, -1]), "REJECT_UNDECLARED_KEY"),
    ("13 fold(1,bare orientation_compose)",
     lambda: chain().fold(1, "orientation_compose").run([1, -1]), "UNKNOWN_OP"),
    ("14 fold(1,cyclic_gcd,arg_names=(acc,elem))",
     lambda: chain().fold(1, "cyclic_gcd", arg_names=("a", "b")).run([12, 18]),
     "DEFER_NAMED_BIND"),
    ("15 reduce(cyclic_gcd)", lambda: chain().reduce("cyclic_gcd").run([12, 18]),
     "ACCEPT"),
    ("16 reduce(cyclic_gcd,bogus=1)",
     lambda: chain().reduce("cyclic_gcd", bogus=1).run([12, 18]),
     "REJECT_UNDECLARED_KEY"),
    ("17 map_indexed(dotted seq_get)",
     lambda: chain().map_indexed("srmech.cascade.leaves.seq_get").run([5, 6, 7]),
     "ACCEPT"),
    ("18 map_indexed(dotted seq_get, i=2)",
     lambda: chain().map_indexed("srmech.cascade.leaves.seq_get", i=2).run([5, 6, 7]),
     "REJECT_UNDECLARED_KEY"),
    ("19 map_indexed(bare seq_get)",
     lambda: chain().map_indexed("seq_get").run([5, 6, 7]), "UNKNOWN_OP"),
]

print(f"srmech {srmech.__version__}  native_status={srmech.native_status()['has_native']}")
print()
hdr = f"{'row':<40} {'PURE':<10} {'NATIVE':<10} proto_want"
print(hdr)
print("-" * len(hdr))
recs = []
for label, fn, want in ROWS:
    pure = run(fn, force_pure=True)
    nat = run(fn, force_pure=False)
    rec = {"row": label, "pure": pure, "native": nat, "proto_want": want}
    recs.append(rec)
    print(f"{label:<40} {pure['outcome']:<10} {nat['outcome']:<10} {want}")
print()
for r in recs:
    print(json.dumps(r))
