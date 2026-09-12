#!/usr/bin/env python3
"""rc473 A3b -- the header's `MEASURED ... EQUAL at 17` sentence, tested.

`c/include/srmech.h` shipped a sentence LABELLED MEASURED:

    "the tagged set and the Class-N transcendental status-returning family
     are now EQUAL at 17 -- 0 family members untagged, 0 tagged names
     outside the family"

An equality has two directions and the sentence asserts both.  This script
measures both, over the MASKED header (block/line comments, string and char
literals blanked, line count preserved), so a declaration quoted inside a
comment cannot be counted as a declaration.

The FAMILY PREDICATE is stated here rather than inferred, because "Class-N
transcendental status-returning family" is prose and prose cannot be run:

    a status-returning `srmech_*` export whose name carries, as an
    underscore-delimited token, one of the Class-N transcendental or root
    stems below.

Run from ``docs/srmech``:

    python3 notes/_rc473_a3b_nodiscard_family.py            # human table
    python3 notes/_rc473_a3b_nodiscard_family.py --ndjson   # one row per line
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

HEADER = "c/include/srmech.h"

# Class-N transcendental + root stems.  `series_truncate` is not a stem: the
# six `*_series_truncate*` members are caught by their sin/cos/exp/atan/log1p
# stems, which is the point -- CLAUDE.md §2 names those six as THE Class-N
# asymptotic-calculus surface.
STEMS = frozenset(
    """
    sin cos tan asin acos atan atan2 sinh cosh tanh
    exp log log1p ln
    sqrt isqrt rsqrt cbrt root pow
    """.split()
)

DECL = re.compile(
    r"^(?P<tag>SRMECH_NODISCARD\s+)?srmech_status_t\s+(?P<name>srmech_\w+)\s*\(",
    re.MULTILINE,
)


def mask(text: str) -> str:
    """Blank comments and string/char literals; preserve line count."""
    out: list[str] = []
    i, n, state = 0, len(text), None
    while i < n:
        c = text[i]
        if state is None:
            if text.startswith("/*", i):
                state, i = "block", i + 2
                out.append("  ")
                continue
            if text.startswith("//", i):
                state, i = "line", i + 2
                out.append("  ")
                continue
            if c in "\"'":
                state, i = c, i + 1
                out.append(" ")
                continue
            out.append(c)
            i += 1
        elif state == "block":
            if text.startswith("*/", i):
                state, i = None, i + 2
                out.append("  ")
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
        elif state == "line":
            if c == "\n":
                state, i = None, i + 1
                out.append("\n")
                continue
            out.append(" ")
            i += 1
        else:
            if c == "\\":
                out.append("  ")
                i += 2
                continue
            if c == state:
                state = None
            out.append("\n" if c == "\n" else " ")
            i += 1
    return "".join(out)


#: Stem hits this pass did NOT tag, each with the reason, written out rather
#: than excluded by a cleverer predicate -- the same idiom
#: python/tests/test_value_status_c_boundary_rc473.py uses for
#: ``_NOT_A_RATIONAL_PEER``.  A carve-out with no stated reason is
#: indistinguishable from an oversight, and a stale one is asserted below.
NOT_TAGGED = {
    "srmech_mod_pow": (
        "`pow` is a LEXICAL hit. Modular exponentiation is Class I/J cyclic "
        "arithmetic, not a Class-N transcendental."
    ),
    "srmech_bigint_pow_u32": (
        "`pow` is a LEXICAL hit. Integer exponentiation is algebraic; it is "
        "not a transcendental or a root extraction."
    ),
    "srmech_rational_pow_uint": (
        "`pow` is a LEXICAL hit. A rational raised to an unsigned integer "
        "power is algebraic."
    ),
    "srmech_rational_pow_uint_big": (
        "`pow` is a LEXICAL hit; the bigint peer of srmech_rational_pow_uint "
        "and out for the same reason."
    ),
    "srmech_poly_root_box_certify": (
        "`root` is a LEXICAL hit. A polynomial-root box certifier is not a "
        "root EXTRACTION; nothing here calls the Class-N sqrt cascade."
    ),
}

#: Tagged names the stem predicate cannot reach: Class-N by ROLE, not by
#: spelling. Enumerated so DIRECTION 2 is a named residual and not a surprise.
TAGGED_WITHOUT_STEM_REASON = {
    "srmech_hypercomplex_couple_q61": "Class-N Q61 coupling; no stem in the name.",
    "srmech_hypercomplex_couple_turn_q61": "peer of the above; no stem in the name.",
    "srmech_winding_fold": "Class-N winding; no stem in the name.",
    "srmech_winding_tower": "peer of srmech_winding_fold; tagged at this pass.",
}


def tokens(name: str) -> list[str]:
    return name[len("srmech_"):].split("_") if name.startswith("srmech_") else name.split("_")


def in_family(name: str) -> bool:
    return any(t in STEMS for t in tokens(name))


def scan(root: pathlib.Path):
    raw = (root / HEADER).read_text(encoding="utf-8")
    masked = mask(raw)
    lineno = {}
    decls: dict[str, bool] = {}
    for m in DECL.finditer(masked):
        name = m.group("name")
        tagged = m.group("tag") is not None
        # a symbol declared twice keeps `tagged` if ANY declaration carries it
        decls[name] = decls.get(name, False) or tagged
        lineno.setdefault(name, masked[: m.start()].count("\n") + 1)
    return decls, lineno


def main(argv: list[str]) -> int:
    root = pathlib.Path(".")
    for a in argv[1:]:
        if not a.startswith("--"):
            root = pathlib.Path(a)
    decls, lineno = scan(root)

    tagged = {n for n, t in decls.items() if t}
    family = {n for n in decls if in_family(n)}

    untagged_family = sorted(family - tagged)
    tagged_outside = sorted(tagged - family)
    stale_carveouts = sorted(set(NOT_TAGGED) - set(untagged_family))
    unexplained = sorted(set(untagged_family) - set(NOT_TAGGED))
    unexplained_outside = sorted(set(tagged_outside) - set(TAGGED_WITHOUT_STEM_REASON))

    rows = {
        "status_returning_decls": len(decls),
        "tagged": len(tagged),
        "family_by_stem_predicate": len(family),
        "family_members_untagged": len(untagged_family),
        "tagged_names_outside_family": len(tagged_outside),
        "equality_holds": not untagged_family and not tagged_outside,
        "untagged_family_names": untagged_family,
        "tagged_outside_family_names": tagged_outside,
        "untagged_without_a_stated_reason": unexplained,
        "tagged_outside_without_a_stated_reason": unexplained_outside,
        "stale_carveouts": stale_carveouts,
        "tagged_names": sorted(tagged),
        "stems": sorted(STEMS),
    }

    if "--ndjson" in argv:
        print(json.dumps(rows, sort_keys=True))
        return 0

    print(f"status-returning srmech_* declarations (masked) : {len(decls)}")
    print(f"SRMECH_NODISCARD-tagged                          : {len(tagged)}")
    print(f"family by the stem predicate                     : {len(family)}")
    print()
    print(f"DIRECTION 1 -- family members UNTAGGED  : {len(untagged_family)}")
    for n in untagged_family:
        why = NOT_TAGGED.get(n, "*** NO STATED REASON ***")
        print(f"    {n}   (srmech.h:{lineno[n]})")
        print(f"        {why}")
    print()
    print(f"DIRECTION 2 -- tagged names OUTSIDE the family : {len(tagged_outside)}")
    for n in tagged_outside:
        why = TAGGED_WITHOUT_STEM_REASON.get(n, "*** NO STATED REASON ***")
        print(f"    {n}   (srmech.h:{lineno[n]})")
        print(f"        {why}")
    print()
    print("EQUALITY HOLDS:", rows["equality_holds"])
    print("untagged with NO stated reason        :", unexplained or "none")
    print("tagged-outside with NO stated reason  :", unexplained_outside or "none")
    print("stale carve-outs (named, now tagged)  :", stale_carveouts or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
