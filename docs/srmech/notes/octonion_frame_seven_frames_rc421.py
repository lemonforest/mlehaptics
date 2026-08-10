"""Is `octonion_frame_read`'s `frame=4` pin a THEOREM or a SCOPE? (rc421, `#T1122`)

`srmech.cascade.cayley_dickson.octonion_frame_read` accepts a `frame=` keyword
but rejects every value except ``4`` with a ValueError whose message argues:

    "Only l = e4 is well-posed on the standard basis - e1/e2/e3 lie inside the
     H base and e5/e6/e7 = e_{1,2,3}.e4 are not independent seam generators, so
     no other single basis unit splits O = H (+) Hl cleanly."

That argument is CORRECT but answers a narrower question than the parameter
name implies: it asks "holding the base fixed at {e0,e1,e2,e3}, which single
unit may serve as l?" A *frame*, though, is a choice of H SUBALGEBRA, and the
splitting unit follows from it. O has seven quaternion subalgebras, one per
Fano line. So the pin may be a genuine theorem (only one frame is well-posed)
or merely the scope the op was built at (seven are, and six were never wired).

This script decides it by MEASUREMENT, deriving every structure from srmech's
own ops. Nothing about the Fano plane is asserted; the lines are read off
`cd_mult`.

PRE-REGISTERED FALSIFIER, stated before running. The generalisation is real
only if ALL of these hold for all seven lines L:

  (i)   span{e0} u L is CLOSED under cd_mult (it is an H subalgebra at all);
  (ii)  every one of its 64 ordered basis-triple associators vanishes (it is
        genuinely associative, i.e. a coherent base, not merely closed);
  (iii) {e_m . e_l : m in base} spans the seam for some l outside the base --
        without this, O = H (+) Hl is not a splitting and `frame` is ill-posed;
  (iv)  ZERO of the octonion's nonzero associators live entirely inside the
        base -- i.e. the "all non-closure crosses the seam" property that the
        docstring measures for L={1,2,3} MOVES WITH THE FRAME.

If (iv) fails for any line, the e4 pin is load-bearing and must stay. If all
four hold for all seven, the pin is a scope and `frame=` should accept a line.

Class discipline: sign handling is Class K (pin-slot) + Class C (re-application)
via srmech ops; there is no `abs()` anywhere here.

Run:  PYTHONPATH=docs/srmech/python python docs/srmech/notes/octonion_frame_seven_frames_rc421.py
"""

from __future__ import annotations

import itertools
import json
import sys

from srmech.cascade.cayley_dickson import (
    associator,
    cd_mult,
    octonion_frame_read,
)

DIM = 8
UNITS = range(DIM)
IMAG = range(1, DIM)


def e(i: int):
    """Basis unit e_i of O as an 8-vector."""
    return tuple(1 if k == i else 0 for k in range(DIM))


def as_signed_unit(v):
    """Read an 8-vector that IS +/-e_k back as (k, sign), else None.

    Class K reads the pin-slot sign; Class C re-applies it as the which-way.
    No abs(): the sign is a returned channel, not something discarded.
    """
    nz = [(k, c) for k, c in enumerate(v) if c != 0]
    if len(nz) != 1:
        return None
    k, c = nz[0]
    if c == 1:
        return (k, 1)
    if c == -1:
        return (k, -1)
    return None


def fano_lines():
    """Derive the 7 Fano lines from cd_mult -- NOT asserted from a convention."""
    lines = set()
    for i, j in itertools.combinations(IMAG, 2):
        got = as_signed_unit(cd_mult(e(i), e(j)))
        if got is None:
            continue
        k, _sign = got
        if k == 0:
            continue
        lines.add(frozenset((i, j, k)))
    return sorted(sorted(t) for t in lines)


def main() -> int:
    out = []

    def rec(**kw):
        out.append(kw)
        print(json.dumps(kw, sort_keys=True))

    lines = fano_lines()
    rec(record="fano_lines", derived_from="cd_mult", n_lines=len(lines),
        lines=[list(t) for t in lines])

    # --- the octonion's own non-closure census, once ---------------------
    nonzero_triples = []
    for t in itertools.product(IMAG, repeat=3):
        a = associator(e(t[0]), e(t[1]), e(t[2]))
        if any(c != 0 for c in a):
            nonzero_triples.append(t)
    rec(record="associator_census", ordered_imag_triples=len(IMAG) ** 3,
        nonzero=len(nonzero_triples))

    # --- per-frame evaluation of the four falsifier conditions -----------
    all_pass = True
    per_frame = []
    for L in lines:
        base = [0] + list(L)
        seam = [k for k in IMAG if k not in L]

        # (i) closure of span{e0} u L under cd_mult
        closed = True
        for a, b in itertools.product(base, repeat=2):
            got = as_signed_unit(cd_mult(e(a), e(b)))
            if got is None or got[0] not in base:
                closed = False
                break

        # (ii) all 64 ordered base-triple associators vanish
        base_assoc_nonzero = 0
        for t in itertools.product(base, repeat=3):
            a = associator(e(t[0]), e(t[1]), e(t[2]))
            if any(c != 0 for c in a):
                base_assoc_nonzero += 1

        # (iii) does some l outside the base carry the base ONTO the seam?
        good_ells = []
        for ell in seam:
            hit = set()
            ok = True
            for m in base:
                got = as_signed_unit(cd_mult(e(m), e(ell)))
                if got is None or got[0] in base:
                    ok = False
                    break
                hit.add(got[0])
            if ok and hit == set(seam):
                good_ells.append(ell)

        # (iv) does the non-closure ALL cross THIS frame's seam?
        inside_base = sum(1 for t in nonzero_triples if all(k in L for k in t))
        crossing = len(nonzero_triples) - inside_base

        ok = (closed and base_assoc_nonzero == 0
              and len(good_ells) > 0 and inside_base == 0)
        all_pass = all_pass and ok
        row = dict(record="frame", line=list(L), seam=seam,
                   i_closed=closed, ii_base_assoc_nonzero=base_assoc_nonzero,
                   iii_valid_splitting_units=good_ells,
                   iv_nonzero_assoc_inside_base=inside_base,
                   iv_nonzero_assoc_crossing_seam=crossing, passes=ok)
        per_frame.append(row)
        rec(**row)

    rec(record="verdict_seven_frames", all_four_conditions_hold_for_all=all_pass,
        n_frames=len(lines),
        interpretation=("the e4 pin is a SCOPE, not a theorem: every Fano line "
                        "is a well-posed frame" if all_pass else
                        "at least one line FAILS; the pin may be load-bearing"))

    # --- what the SHIPPED op does with each of the seven -----------------
    probe = (0, 1, 2, 3, 4, 5, 6, 7)
    accepted, rejected = [], []
    for L in lines:
        seam = [k for k in IMAG if k not in L]
        for ell in seam:
            try:
                octonion_frame_read(probe, frame=ell)
                accepted.append(ell)
            except ValueError:
                rejected.append(ell)
    rec(record="shipped_op_reachability",
        distinct_frames_measured_well_posed=len(lines),
        distinct_splitting_units_accepted_by_shipped_op=sorted(set(accepted)),
        distinct_splitting_units_rejected=sorted(set(rejected)),
        note=("the op exposes ONE of the well-posed frames; the parameter "
              "exists but its domain is a single value"))

    with open("docs/srmech/notes/octonion_frame_seven_frames_rc421.ndjson",
              "w", encoding="utf-8", newline="\n") as fh:
        for r in out:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
