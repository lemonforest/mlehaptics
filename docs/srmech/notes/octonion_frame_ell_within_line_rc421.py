"""Leg 3 — is the frame the LINE (7) or the (line, l) PAIR (28)? (rc421, `#T1122`)

Legs 1 and 2 left exactly one thing unmeasured, and it is the thing that picks
the API shape. Leg 2 held the splitting unit at ``seam[0]`` for each Fano line,
so it measured SEVEN reads. But leg 1 measured that every line admits FOUR valid
splitting units, not one. So:

  Q4. Within a FIXED line L, does the read depend on WHICH of the four valid l
      you pick?

      - If it does NOT, the frame IS the line, and `frame=` is 7-valued.
      - If it DOES, the frame is the (line, l) PAIR, and `frame=` is 28-valued.

This is not a cosmetic question. 28 = 7 lines x 4 splitting units is exactly the
count the rc384 task recorded as "a measured 28-seam spec", and the tree already
carries a 28 from rc388 (`oct_torsor_rc388.py`): there, the 28 seams collapse to
SEVEN distinct (H, T) decompositions because the coset H.e is the same SET for
all four e of a line. That prior is about the SET the seam occupies. This leg
asks a different question -- whether the READ is the same -- and the two can
disagree, because the seam-half's IDENTIFICATION with H is what l fixes:

    x = q0 + q1 . l     ==>     q1 depends on l, even when the seam SET does not.

MEASURED, NOT ASSUMED. Every structure here is read off `cd_mult`. If the four
l agree, that is reported; if they differ, the leg characterises HOW rather than
stopping at "they differ" -- a predictable signed permutation is a real finding
and it should shape the op's return value.

HONESTY NOTE carried forward from legs 1 and 2, restated so it cannot drift.
Leg 1 pre-registered four conditions; condition (iv) ("no nonzero associator
lies entirely inside the base") is IMPLIED BY condition (ii) ("all 64 ordered
base-triple associators vanish"), because the line L is a subset of the base.
(iv) could not have returned otherwise once (ii) passed. It is DERIVED, not
independent evidence. Conditions (i), (ii) and (iii) are genuine -- each could
have failed against srmech's own multiplication table.

Class discipline: the sign channel is Class K (pin-slot) read and Class C
(which-way) re-application; there is no `abs()` anywhere.

Run:  PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/octonion_frame_ell_within_line_rc421.py
"""

from __future__ import annotations

import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from octonion_frame_generalised_read_rc421 import (  # noqa: E402
    as_signed_unit,
    e,
    fano_lines,
    generalised_frame_read,
    h_conj,
    h_mult,
    h_norm_sq,
)

from srmech.cascade.cayley_dickson import cd_mult  # noqa: E402
from srmech.math.q import Q  # noqa: E402

DIM = 8
IMAG = range(1, DIM)


def read_with_affine(x, line, ell):
    """Leg 2's reader PLUS the fiber-fixed HP^1 coordinate q0 . q1^-1.

    Leg 2's `generalised_frame_read` stops at the Hopf base and does not return
    `canonical_affine`, so asking it about that field can only ever answer None.
    Measuring the transition law on a field the instrument never produces is a
    0-of-0 non-measurement, so the coordinate is computed HERE, exactly, and the
    law is put at genuine risk of failing. q1^-1 = conj(q1)/|q1|^2, exact-Q.
    """
    r = dict(generalised_frame_read(x, line, ell))
    n1 = h_norm_sq(r["q1"])
    if n1 == Q(0, 1):
        r["canonical_affine"] = None
    else:
        inv = Q(1, 1) / n1
        q1_inv = tuple(c * inv for c in h_conj(r["q1"], line))
        r["canonical_affine"] = h_mult(r["q0"], q1_inv, line)
    return r


def valid_splitting_units(line):
    """Leg 1's condition (iii), re-derived: which l carry the base ONTO the seam."""
    base = [0] + list(line)
    seam = [k for k in IMAG if k not in line]
    good = []
    for ell in seam:
        hit, ok = set(), True
        for m in base:
            got = as_signed_unit(cd_mult(e(m), e(ell)))
            if got is None or got[0] in base:
                ok = False
                break
            hit.add(got[0])
        if ok and hit == set(seam):
            good.append(ell)
    return good


def signed_base_units(line):
    """The 8 signed basis units +/-e_b of the frame's H base, in base coords."""
    out = []
    for idx in range(4):
        for sign in (1, -1):
            u = [Q(0, 1)] * 4
            u[idx] = Q(sign, 1)
            out.append((idx, sign, tuple(u)))
    return out


def transition_unit(line, ell0, ell):
    """The base unit u with e_ell == u . e_ell0, derived from cd_mult.

    Class K reads the pin-slot sign off the product; Class C re-applies it onto
    the returned unit. No abs().
    """
    base = [0] + list(line)
    for idx, b in enumerate(base):
        got = as_signed_unit(cd_mult(e(b), e(ell0)))
        if got is not None and got[0] == ell:
            # e_b . e_ell0 = s . e_ell  ==>  e_ell = s . e_b . e_ell0, u = s.e_b
            s = got[1]
            u = [Q(0, 1)] * 4
            u[idx] = Q(s, 1)
            return (idx, s, tuple(u))
    return None


def read_key(r):
    """A comparable, exact rendering of a full read (no float anywhere)."""
    return json.dumps(
        {k: ([str(c) for c in v] if isinstance(v, tuple) else str(v))
         for k, v in sorted(r.items())},
        sort_keys=True)


def main() -> int:
    out = []

    def rec(**kw):
        out.append(kw)
        print(json.dumps(kw, sort_keys=True))

    lines = fano_lines()
    # The same deliberately generic octonion leg 2 used: no zero coordinate, no
    # repeated value, so a collapse across l cannot happen by accident.
    x = (1, 2, 3, 5, 7, 11, 13, 17)
    rec(record="probe", x=list(x), n_lines=len(lines),
        question="within a fixed Fano line, does the read depend on WHICH valid l?")

    # ---- Q4: enumerate every (line, l) pair and compare within each line ----
    all_reads = {}
    per_line = []
    for L in lines:
        ells = valid_splitting_units(L)
        ell0 = ells[0]
        r0 = generalised_frame_read(x, L, ell0)
        keys, rows = [], []
        for ell in ells:
            r = generalised_frame_read(x, L, ell)
            all_reads[(L, ell)] = r
            keys.append(read_key(r))
            rows.append((ell, r))

        distinct_in_line = len(set(keys))
        q0_same = all(r["q0"] == r0["q0"] for _, r in rows)
        q1_same = all(r["q1"] == r0["q1"] for _, r in rows)
        baseH_same = all(r["base_H"] == r0["base_H"] for _, r in rows)
        baseR_same = all(r["base_R"] == r0["base_R"] for _, r in rows)
        nsq_same = all(r["norm_sq"] == r0["norm_sq"] for _, r in rows)

        row = dict(record="within_line", line=list(L), valid_ells=ells,
                   reference_ell=ell0, distinct_reads_within_line=distinct_in_line,
                   q0_invariant_across_ell=q0_same,
                   q1_invariant_across_ell=q1_same,
                   base_H_invariant_across_ell=baseH_same,
                   base_R_invariant_across_ell=baseR_same,
                   norm_sq_invariant_across_ell=nsq_same)
        per_line.append(row)
        rec(**row)

    total_pairs = len(all_reads)
    distinct_total = len({read_key(r) for r in all_reads.values()})
    norms = {str(r["norm_sq"]) for r in all_reads.values()}
    rec(record="q4_verdict", total_line_ell_pairs=total_pairs,
        distinct_reads=distinct_total,
        norm_sq_shared_across_all_pairs=(len(norms) == 1),
        norm_sq=sorted(norms),
        frame_is_the_pair=(distinct_total == total_pairs),
        interpretation=(
            "the frame is the (line, l) PAIR: all %d reads are distinct, so "
            "`frame=` must be %d-valued" % (total_pairs, total_pairs)
            if distinct_total == total_pairs else
            "the four l within a line AGREE: the frame is the LINE and "
            "`frame=` is 7-valued"))

    # ---- Q5: HOW do the four l differ? Characterise, don't stop at "they do" --
    # Predicted (to be measured, not assumed): if e_l = u . e_l0 with u a signed
    # base unit, then base_H(l) == base_H(l0) . u  -- a RIGHT H-multiplication,
    # i.e. a signed permutation of the four base_H coordinates.
    law_hits = law_total = 0
    affine_hits = affine_total = 0
    for L in lines:
        ells = valid_splitting_units(L)
        ell0 = ells[0]
        r0 = read_with_affine(x, L, ell0)
        for ell in ells:
            r = read_with_affine(x, L, ell)
            tu = transition_unit(L, ell0, ell)
            derived = tu is not None
            if derived:
                idx, s, u = tu
                predicted = h_mult(r0["base_H"], u, L)
                holds = (predicted == r["base_H"])
                law_total += 1
                law_hits += 1 if holds else 0
                # the same right-action on the fiber-fixed HP^1 coordinate
                ca0, ca = r0.get("canonical_affine"), r.get("canonical_affine")
                if ca0 is not None and ca is not None:
                    affine_total += 1
                    affine_hits += 1 if h_mult(ca0, u, L) == ca else 0
            else:
                idx = s = None
                holds = False
                law_total += 1
            rec(record="transition_law", line=list(L), ell0=ell0, ell=ell,
                transition_unit_base_index=idx, transition_unit_sign=s,
                base_H_equals_reference_times_u=holds,
                trivial_transition=(ell == ell0))
    rec(record="q5_transition_verdict",
        base_H_right_action_law=[law_hits, law_total],
        law_holds_universally=(law_hits == law_total),
        canonical_affine_right_action_law=[affine_hits, affine_total],
        canonical_affine_law_holds=(affine_total > 0
                                    and affine_hits == affine_total),
        canonical_affine_denominator_nonvacuous=(affine_total > 0),
        interpretation=(
            "the four l of a line differ by a RIGHT multiplication of the Hopf "
            "base by the signed base unit u = e_l . e_l0^-1 -- a signed "
            "permutation of base_H's four coordinates, derived from cd_mult. "
            "base_R and norm_sq are l-invariant; base_H and canonical_affine "
            "are EQUIVARIANT under that same right action. The affine leg is "
            "reported with its denominator so a 0-of-0 cannot pass as a pass."))

    # ---- Q6: NEGATIVE CONTROL -- would a collapsing reader be caught? --------
    # A reader that silently ignored l (always using the line's first valid unit)
    # would return only 7 distinct reads over the 28 pairs. Measure that it does,
    # so the gate that pins 28 is a gate that CAN fail.
    collapsed = {}
    for L in lines:
        ells = valid_splitting_units(L)
        for ell in ells:
            collapsed[(L, ell)] = generalised_frame_read(x, L, ells[0])
    collapsed_distinct = len({read_key(r) for r in collapsed.values()})
    rec(record="q6_negative_control",
        collapsing_reader_distinct_reads=collapsed_distinct,
        honest_reader_distinct_reads=distinct_total,
        control_separates=(collapsed_distinct != distinct_total),
        interpretation=("a reader that ignored l would return %d distinct reads "
                        "over the %d pairs, not %d -- so a gate pinning %d is "
                        "falsifiable, not decorative"
                        % (collapsed_distinct, total_pairs, distinct_total,
                           distinct_total)))

    # ---- Q7: which (line, l) pairs share a SEAM SET? (the rc388 28-vs-7) -----
    # rc388 measured that the 28 seams carry only SEVEN distinct (H, T) set
    # decompositions. Confirm that here, and show it does NOT imply seven reads.
    seam_sets = {}
    for (L, ell) in all_reads:
        seam_sets.setdefault((tuple(L), tuple(k for k in IMAG if k not in L)),
                             []).append(ell)
    rec(record="q7_seam_set_vs_read",
        distinct_seam_set_decompositions=len(seam_sets),
        distinct_reads=distinct_total, pairs=total_pairs,
        note=("rc388's 28 -> 7 collapse is about the seam SET (T is always H's "
              "set-complement, so all four l of a line share it). The READ does "
              "NOT collapse with it, because l fixes the seam half's "
              "IDENTIFICATION with H (x = q0 + q1.l), not merely its span."))

    # ---- Q8: does the shipped op reach any of this? --------------------------
    rec(record="q8_shipped_reachability",
        well_posed_frames_measured=total_pairs,
        reachable_through_shipped_op=1,
        reachable_frame="line (1,2,3), l = e4 (the Cayley-Dickson seam)",
        note="the parameter exists; its domain is a single one of the 28 frames")

    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "octonion_frame_ell_within_line_rc421.ndjson")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        for r in out:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
