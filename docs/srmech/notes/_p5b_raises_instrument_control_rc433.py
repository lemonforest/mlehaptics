"""`#T1131` P5b — CONTROL on P5's ``Raises:``-block detector.

P5 returned ZERO ops-with-a-``Raises:``-block across the whole `#T1131`
population. A zero from a scanner that can only ever return zero is a FALSE
null, so this file drives the SAME regex over ops that are KNOWN to carry a
``Raises:`` block (rc431 `#T1129` added several, and they are pinned by
``tests/test_input_contracts_rc431.py::test_the_raises_block_matches_what_is_raised``).

If the control ops come back True and the `#T1131` ops come back False, the zero
is a real absence. If the control ops ALSO come back False, the detector is
broken and P5's null is UNSUPPORTED rather than EMPTY.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys

SPEC = importlib.util.spec_from_file_location(
    "_p5", "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p5_t1130_overlap_rc433.py")
_p5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(_p5)

OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p5b_raises_instrument_control_rc433.ndjson"

#: Ops rc431 DECLARED a Raises: block for (positive control).
POSITIVE = [
    "srmech.math.cyclic.lcm",
    "srmech.math.primes.factor",
    "srmech.math.rational.rational_div",
    "srmech.biology.q8.q8_mult",
    "srmech.math.rational.continued_fraction_convergents",
    "srmech.signal_processing.path_registry.lookup",
]

#: A sample of the `#T1131` population (negative control — expected False).
NEGATIVE = [
    "srmech.math.mat.Mat.from_rows",
    "srmech.math.vec.Vec.__getitem__",
    "srmech.math.hdc.loop_bind_hd",
    "srmech.math.laplacian.mat_matmul",
    "srmech.physics.qm.bell.operator_norm",
]


def probe(dotted):
    obj = _p5.resolve(dotted)
    doc = inspect.getdoc(obj) or "" if obj is not None else ""
    m = _p5._RAISES_RE.search(doc)
    blk = m.group(1).strip() if m else ""
    return {
        "op": dotted,
        "resolved": obj is not None,
        "has_raises_block": bool(blk),
        "declared": sorted(set(_p5._EXC_RE.findall(blk))) if blk else [],
        "doc_len": len(doc),
    }


def main():
    import srmech
    print("srmech", srmech.__file__, srmech.__version__)
    recs = []
    print("\n=== POSITIVE control (must be True) ===")
    n_pos_true = 0
    for d in POSITIVE:
        r = probe(d)
        r["arm"] = "positive"
        recs.append(r)
        n_pos_true += bool(r["has_raises_block"])
        print("  %-56s %-5s %s" % (d, r["has_raises_block"], r["declared"] or "-"))
    print("\n=== NEGATIVE control (#T1131 population; expected False) ===")
    n_neg_true = 0
    for d in NEGATIVE:
        r = probe(d)
        r["arm"] = "negative"
        recs.append(r)
        n_neg_true += bool(r["has_raises_block"])
        print("  %-56s %-5s %s" % (d, r["has_raises_block"], r["declared"] or "-"))

    verdict = ("EMPTY (real absence — detector demonstrably fires elsewhere)"
               if n_pos_true and not n_neg_true else
               "UNSUPPORTED (detector never fires; P5's zero proves nothing)"
               if not n_pos_true else
               "MIXED — re-read")
    print("\npositive True: %d/%d   negative True: %d/%d" % (
        n_pos_true, len(POSITIVE), n_neg_true, len(NEGATIVE)))
    print("NULL CLASSIFICATION:", verdict)

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "control_meta",
                             "n_positive_true": n_pos_true,
                             "n_positive": len(POSITIVE),
                             "n_negative_true": n_neg_true,
                             "n_negative": len(NEGATIVE),
                             "null_classification": verdict,
                             "srmech_version": srmech.__version__,
                             "python": sys.version.split()[0]},
                            sort_keys=True) + "\n")
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
