"""`#T1131` P5 — the DECLARED-vs-ENFORCED overlap with `#T1130`.

`#T1130` is the *declared-vs-enforced* half: a docstring names an exception the
code never raises. `#T1131` (this scope) is the *test-pins-the-assert* half. The
two meet wherever an op in the `#T1131` population ALSO has a ``Raises:`` block,
because a rc433 promotion (assert -> real raise) changes the very thing `#T1130`
would be re-declaring. This file enumerates that intersection so the two rcs do
not both edit the same line.

For every op behind a `#T1131` site:
  * does its docstring carry a ``Raises:`` / ``Raises\\n-----`` block?
  * which exception names does it declare?
  * which does it ACTUALLY raise for the `#T1131` input class (measured in P2)?
  * therefore: OVERLAP (both scopes touch the docstring) or DISJOINT.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import re
import sys

OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p5_t1130_overlap_rc433.ndjson"

#: (site, dotted-op, the exception P2 MEASURED under -O for the pinned input)
SITES = [
    ("tests/test_bell_chsh.py:334", "srmech.physics.qm.bell.operator_norm", "ValueError"),
    ("tests/test_bell_chsh.py:344", "srmech.physics.qm.bell.operator_norm", "TypeError"),
    ("tests/test_byo_cascade_toml.py:156", "srmech.dsl._catalog.register_catalog_dir",
     "FileNotFoundError (DEFERRED to load_catalog)"),
    ("tests/test_loop_bind_hd.py:115", "srmech.math.hdc.loop_bind_hd", "NONE (silent truncation)"),
    ("tests/test_loop_bind_hd.py:117", "srmech.math.hdc.loop_unbind_hd", "NONE (silent truncation)"),
    ("tests/test_loop_hd_division.py:186", "srmech.math.hdc.loop_conj_hd", "NONE (silent truncation)"),
    ("tests/test_loop_hd_division.py:186", "srmech.math.hdc.loop_inv_hd", "NONE (silent truncation)"),
    ("tests/test_loop_hd_division.py:192", "srmech.math.hdc.loop_runbind_hd", "NONE (silent truncation)"),
    ("tests/test_loop_hd_division.py:195", "srmech.math.hdc.loop_runbind_hd", "IndexError"),
    ("tests/test_loop_hd_native_parity.py:178", "srmech.math.hdc.loop_inv_hd", "ZeroDivisionError"),
    ("tests/test_mat_carrier_rc69.py:72", "srmech.math.mat.Mat.from_rows", "NONE (silent, wrong shape)"),
    ("tests/test_mat_matmul_bridge_rc72.py:131", "srmech.math.laplacian.mat_matmul", "AttributeError"),
    ("tests/test_vec_carrier_rc129.py:90", "srmech.math.vec.Vec.__getitem__",
     "IndexError (positive) / NONE (negative)"),
    # class (c) — listed so the enumeration is complete, not because they overlap
    ("tests/test_frame_scope_rc430.py:587", "tests.test_frame_scope_rc430.assert_declaration_matches", "n/a"),
    ("tests/test_genome_q8_coupling_rc311.py:233", "srmech.biology.genome._q8_couple", "n/a (unreachable)"),
    ("tests/test_octonion_carrier_rc324.py:355", "srmech.biology.genome._oct_couple", "n/a (unreachable)"),
    ("tests/test_owner_axis_rc410.py:659", "tests.test_tool_schema.test_unregister_profile_tools_removes_all", "n/a"),
]

# NOTE (rc433): the ``\Z`` alternative must NOT sit inside the ``\n\s*`` prefix
# group. It did in the first draft, so a docstring whose ``Raises:`` block is the
# LAST thing in the string (no trailing newline) did not match — which is the
# common shape. Caught by P5b's positive control: 2 of 6 known-positive ops came
# back False. Without that control P5's "0 of 17" would have shipped as a
# measurement while the instrument was leaking ~33%.
_RAISES_RE = re.compile(
    r"(?:^|\n)[ \t]*(?:Raises:|Raises[ \t]*\n[ \t]*-{3,})"
    r"(.*?)(?=\n[ \t]*(?:Args:|Returns:|Note|Example|Parameters)|\Z)",
    re.S)
_EXC_RE = re.compile(r"\b([A-Z][A-Za-z0-9]*(?:Error|Exception))\b")


def resolve(dotted):
    parts = dotted.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        mod = ".".join(parts[:cut])
        try:
            m = importlib.import_module(mod)
        except Exception:
            continue
        obj = m
        try:
            for a in parts[cut:]:
                obj = getattr(obj, a)
        except AttributeError:
            continue
        return obj
    return None


def main():
    import srmech
    print("srmech", srmech.__file__, srmech.__version__)
    recs = []
    seen = set()
    for site, dotted, measured in SITES:
        key = dotted
        obj = resolve(dotted)
        doc = inspect.getdoc(obj) or "" if obj is not None else ""
        m = _RAISES_RE.search(doc)
        block = m.group(1).strip() if m else ""
        declared = sorted(set(_EXC_RE.findall(block))) if block else []
        # also scan the whole docstring for exception NAMES outside a Raises block
        anywhere = sorted(set(_EXC_RE.findall(doc)))
        overlap = bool(declared)
        rec = {
            "site": site,
            "op": dotted,
            "resolved": obj is not None,
            "has_raises_block": bool(block),
            "declared_in_raises_block": declared,
            "exception_names_anywhere_in_docstring": anywhere,
            "measured_under_dash_O": measured,
            "t1130_overlap": overlap,
        }
        recs.append(rec)
        if key not in seen:
            seen.add(key)
        print("%-46s %-52s raises_block=%-5s declared=%s" % (
            site, dotted.split(".")[-1], bool(block), declared or "-"))

    n_over = sum(1 for r in recs if r["t1130_overlap"])
    print("\nsites with a Raises: block (=> #T1130 overlap): %d of %d" % (n_over, len(recs)))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "overlap_meta", "n_sites": len(recs),
                             "n_overlap": n_over,
                             "srmech_version": srmech.__version__,
                             "srmech_file": srmech.__file__,
                             "python": sys.version.split()[0]},
                            sort_keys=True) + "\n")
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
