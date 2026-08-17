"""ADVERSARIAL round-3: INDEPENDENTLY re-derive the Python verdict for every one
of the 20 grammar rows the keyset-validator prototype's Section 3 asserts against,
plus the claimed 25th defect.

Nothing here reads the prototype's table; each row is re-built from the srmech
public DSL surface and RUN, and what Python actually does is printed.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import srmech  # noqa: E402
from srmech.dsl import chain, lookup_cascade_op  # noqa: E402

rows = []


def probe(label, fn):
    try:
        val = fn()
        rows.append({"probe": label, "outcome": "OK", "value": repr(val)})
    except Exception as exc:  # noqa: BLE001
        rows.append(
            {
                "probe": label,
                "outcome": "RAISE",
                "exc_type": type(exc).__name__,
                "exc": str(exc),
            }
        )


# ---- leaf rows (Section 3 [00]..[05]) --------------------------------------
probe("leaf .then('magnitude', x=3).run(-3.5)  [row 00; claimed 25th defect]",
      lambda: chain().then("magnitude", x=3).run(-3.5))
probe("leaf .then('magnitude').run(-3.5)  [control]",
      lambda: chain().then("magnitude").run(-3.5))
probe("leaf .then('best_rational_signed', denom=6).run(0.5)  [row 01]",
      lambda: chain().then("best_rational_signed", denom=6).run(0.5))
probe("leaf .then('best_rational_signed').run(0.5)  [control]",
      lambda: chain().then("best_rational_signed").run(0.5))
probe("leaf .then('reorient').run(5)  [row 02]",
      lambda: chain().then("reorient").run(5))
probe("leaf .then('reorient', orientation=-1).run(5)  [control]",
      lambda: chain().then("reorient", orientation=-1).run(5))
probe("leaf .then('cyclic_gcd').run(12)  [row 03]",
      lambda: chain().then("cyclic_gcd").run(12))
probe("leaf .then('cyclic_gcd', b=18).run(12)  [control]",
      lambda: chain().then("cyclic_gcd", b=18).run(12))
probe("leaf .then('no_such_op').run(1)  [row 04]",
      lambda: chain().then("no_such_op").run(1))
probe("leaf .then('seq_get', i=2).run([5,6,7])  [row 05]",
      lambda: chain().then("seq_get", i=2).run([5, 6, 7]))

# ---- fold rows (Section 3 [06]..[14]) --------------------------------------
probe("fold(1,'cyclic_gcd').run([12,18])  [row 06]",
      lambda: chain().fold(1, "cyclic_gcd").run([12, 18]))
probe("fold(1,'cyclic_gcd',b=5).run([12,18])  [row 07]",
      lambda: chain().fold(1, "cyclic_gcd", b=5).run([12, 18]))
probe("fold(1,'cyclic_gcd',a=1).run([12,18])  [row 08]",
      lambda: chain().fold(1, "cyclic_gcd", a=1).run([12, 18]))
probe("fold(1,'cyclic_gcd',bogus=5).run([12,18])  [row 09]",
      lambda: chain().fold(1, "cyclic_gcd", bogus=5).run([12, 18]))
probe("fold(1,'srmech.cascade.leaves.orientation_compose').run([1,-1])  [row 10]",
      lambda: chain().fold(1, "srmech.cascade.leaves.orientation_compose").run([1, -1]))
probe("fold(1,dotted orientation_compose, orientation=1).run([1,-1])  [row 11]",
      lambda: chain().fold(1, "srmech.cascade.leaves.orientation_compose",
                           orientation=1).run([1, -1]))
probe("fold(1,dotted orientation_compose, bogus=1).run([1,-1])  [row 12]",
      lambda: chain().fold(1, "srmech.cascade.leaves.orientation_compose",
                           bogus=1).run([1, -1]))
probe("fold(1,'orientation_compose').run([1,-1])  [row 13 — bare]",
      lambda: chain().fold(1, "orientation_compose").run([1, -1]))

# ---- reduce rows (Section 3 [15]..[16]) ------------------------------------
probe("reduce('cyclic_gcd').run([12,18])  [row 15]",
      lambda: chain().reduce("cyclic_gcd").run([12, 18]))
probe("reduce('cyclic_gcd',bogus=1).run([12,18])  [row 16]",
      lambda: chain().reduce("cyclic_gcd", bogus=1).run([12, 18]))

# ---- map rows (Section 3 [17]..[19]) ---------------------------------------
probe("map_indexed('srmech.cascade.leaves.seq_get').run([5,6,7])  [row 17]",
      lambda: chain().map_indexed("srmech.cascade.leaves.seq_get").run([5, 6, 7]))
probe("map_indexed(dotted seq_get, i=2).run([5,6,7])  [row 18]",
      lambda: chain().map_indexed("srmech.cascade.leaves.seq_get", i=2).run([5, 6, 7]))
probe("map_indexed('seq_get').run([5,6,7])  [row 19 — bare]",
      lambda: chain().map_indexed("seq_get").run([5, 6, 7]))

# ---- lookup_cascade_op direct probes (the D3 claim) ------------------------
for nm in ("seq_get", "srmech.cascade.leaves.seq_get", "orientation_compose",
           "srmech.cascade.leaves.orientation_compose", "cyclic_gcd", "magnitude"):
    probe(f"lookup_cascade_op({nm!r})", (lambda n=nm: lookup_cascade_op(n)))

print(f"srmech {srmech.__version__}")
for r in rows:
    print(json.dumps(r))
