"""Leg 2 — does a SEVEN-FRAME `octonion_frame_read` buy anything? (rc421, `#T1122`)

Leg 1 (`octonion_frame_seven_frames_rc421.py`) measured that all seven Fano
lines are well-posed frames, so the shipped `frame=4` pin is a SCOPE. That does
not yet justify widening it. A parameter is only worth having if different
values give different answers, so this leg asks the question that decides the rc:

  Q1. Does the frame-committed READ (Hopf base / writhe / affine coordinate)
      actually DIFFER across the seven frames for the same octonion? If all
      seven reads agree, the frames are redundant and the pin costs nothing.

  Q2. Does the generalised reader reproduce the SHIPPED op BIT-EXACTLY at the
      Cayley-Dickson frame (line (1,2,3), l = e4)? Without this the widening is
      a behaviour change, not a generalisation.

  Q3. Is the S3-fiber invariance -- the property that makes the base "the
      coherent note" -- still non-tautological at every frame? The shipped
      docstring is careful that a NON-fiber move must be able to change the
      base. That guard has to survive the generalisation, at each frame.

HONESTY NOTE carried forward from leg 1. Leg 1 pre-registered four conditions;
condition (iv) ("no nonzero associator lies entirely inside the base") is
IMPLIED BY condition (ii) ("all 64 ordered base-triple associators vanish"),
because the line L is a subset of the base. (iv) therefore could not have
returned otherwise once (ii) passed, and it is NOT independent evidence -- it is
restated here as derived, not measured. Conditions (i), (ii) and (iii) are
genuine: each could have failed against srmech's own multiplication table.

The split, derived rather than assumed. For a frame with H base L = (i,j,k) and
splitting unit l, every seam unit e_m satisfies e_m = s * e_{sigma(m)} . e_l for
a unique base index sigma(m) and sign s in {+1,-1}. So

    x = q0 + q1 . l,  with  q0 = base part,  q1 = sum_m s_m x_m e_{sigma(m)}

and the signed permutation (sigma, s) is READ OFF cd_mult, not tabulated here.

Class discipline: the sign channel s is Class K (pin-slot) read and Class C
(which-way) re-application; no `abs()` appears.
"""

from __future__ import annotations

import itertools
import json
import sys

from srmech.cascade.cayley_dickson import (
    cd_conjugate,
    cd_mult,
    cd_norm_sq,
    octonion_frame_read,
)
from srmech.math.q import Q

DIM = 8
IMAG = range(1, DIM)


def e(i: int):
    return tuple(1 if k == i else 0 for k in range(DIM))


def as_signed_unit(v):
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
    lines = set()
    for i, j in itertools.combinations(IMAG, 2):
        got = as_signed_unit(cd_mult(e(i), e(j)))
        if got is not None and got[0] != 0:
            lines.add(frozenset((i, j, got[0])))
    return sorted(tuple(sorted(t)) for t in lines)


def seam_chart(line, ell):
    """Derive (sigma, sign) carrying each seam unit back to the base, via cd_mult."""
    base = [0] + list(line)
    chart = {}
    for m in range(DIM):
        if m in base:
            continue
        for b in base:
            got = as_signed_unit(cd_mult(e(b), e(ell)))
            if got is not None and got[0] == m:
                chart[m] = (b, got[1])
                break
        else:
            return None
    return chart


def h_mult(p, q, line):
    """Multiply two H elements given in the frame's base coordinates."""
    base = [0] + list(line)
    x = [0] * DIM
    y = [0] * DIM
    for idx, b in enumerate(base):
        x[b] = p[idx]
        y[b] = q[idx]
    prod = cd_mult(tuple(x), tuple(y))
    return tuple(prod[b] for b in base)


def h_conj(p, line):
    base = [0] + list(line)
    x = [0] * DIM
    for idx, b in enumerate(base):
        x[b] = p[idx]
    c = cd_conjugate(tuple(x))
    return tuple(c[b] for b in base)


def h_norm_sq(p):
    return sum((c * c for c in p), Q(0, 1))


def generalised_frame_read(x, line, ell):
    """The seven-frame read: O = H_L (+) H_L.l, then the quaternionic Hopf map."""
    base = [0] + list(line)
    chart = seam_chart(line, ell)
    q0 = tuple(Q(x[b], 1) if not isinstance(x[b], Q) else x[b] for b in base)
    q1 = [Q(0, 1)] * 4
    for m, (b, s) in chart.items():
        v = x[m] if isinstance(x[m], Q) else Q(x[m], 1)
        q1[base.index(b)] = v if s == 1 else -v
    q1 = tuple(q1)
    base_H = tuple(Q(2, 1) * c for c in h_mult(q0, h_conj(q1, line), line))
    n0, n1 = h_norm_sq(q0), h_norm_sq(q1)
    return {"q0": q0, "q1": q1, "base_H": base_H,
            "base_R": n0 - n1, "norm_sq": n0 + n1}


def key(r):
    return json.dumps({k: [str(c) for c in v] if isinstance(v, tuple) else str(v)
                       for k, v in r.items()}, sort_keys=True)


def main() -> int:
    out = []

    def rec(**kw):
        out.append(kw)
        print(json.dumps(kw, sort_keys=True))

    lines = fano_lines()
    # A deliberately generic octonion: no zero coordinate, no repeated value,
    # so a read that collapses across frames cannot do so by accident.
    x = (1, 2, 3, 5, 7, 11, 13, 17)
    rec(record="probe", x=list(x), n_frames=len(lines))

    # --- Q2: bit-exact agreement with the SHIPPED op at the CD frame -------
    shipped = octonion_frame_read(x, frame=4)
    mine = generalised_frame_read(x, (1, 2, 3), 4)
    agree = (tuple(shipped["q0"]) == mine["q0"]
             and tuple(shipped["q1"]) == mine["q1"]
             and tuple(shipped["base_H"]) == mine["base_H"]
             and shipped["base_R"] == mine["base_R"]
             and shipped["norm_sq"] == mine["norm_sq"])
    rec(record="q2_backcompat_cd_frame", line=[1, 2, 3], ell=4,
        bit_exact_vs_shipped_op=agree,
        base_H=[str(c) for c in mine["base_H"]], base_R=str(mine["base_R"]))

    # --- Q1: do the seven frames give SEVEN DIFFERENT reads? --------------
    reads, rows = {}, []
    for L in lines:
        seam = [k for k in IMAG if k not in L]
        ell = seam[0]
        r = generalised_frame_read(x, L, ell)
        reads[(L, ell)] = r
        rows.append((L, ell, r))
        rec(record="frame_read", line=list(L), ell=ell,
            base_H=[str(c) for c in r["base_H"]], base_R=str(r["base_R"]),
            norm_sq=str(r["norm_sq"]))

    distinct = len({key(r) for _, _, r in rows})
    norms = {str(r["norm_sq"]) for _, _, r in rows}
    rec(record="q1_frames_are_distinct", n_frames=len(rows),
        distinct_reads=distinct,
        norm_sq_shared_across_all_frames=(len(norms) == 1),
        norm_sq=sorted(norms),
        interpretation=("each frame is a GENUINELY DIFFERENT read of the same "
                        "octonion; the shared norm_sq is the frame-independent "
                        "scale" if distinct == len(rows) else
                        "frames COLLAPSE -- widening the parameter buys nothing"))

    # --- Q3: is S3-fiber invariance still non-tautological per frame? -----
    lam = (1, 1, 1, 1)          # unit-scaled fiber element (|lam|^2 = 4)
    q3 = []
    for L in lines:
        seam = [k for k in IMAG if k not in L]
        ell = seam[0]
        r = generalised_frame_read(x, L, ell)
        # fiber move: right-multiply BOTH halves by lam
        q0l = h_mult(r["q0"], lam, L)
        q1l = h_mult(r["q1"], lam, L)
        bH = tuple(Q(2, 1) * c for c in h_mult(q0l, h_conj(q1l, L), L))
        scale = h_norm_sq(lam)
        fiber_ok = all(a * scale == b for a, b in zip(r["base_H"], bH))
        # NON-fiber control: move only q0. Must CHANGE the base.
        bH2 = tuple(Q(2, 1) * c
                    for c in h_mult(q0l, h_conj(r["q1"], L), L))
        control_changes = any(a * scale != b
                              for a, b in zip(r["base_H"], bH2))
        q3.append(fiber_ok and control_changes)
        rec(record="q3_fiber_invariance", line=list(L), ell=ell,
            fiber_move_preserves_base_up_to_scale=fiber_ok,
            non_fiber_control_changes_base=control_changes)
    rec(record="q3_verdict", all_frames_nontautological=all(q3))

    rec(record="VERDICT",
        q1_frames_distinct=(distinct == len(rows)),
        q2_backcompat_bit_exact=agree,
        q3_guard_survives=all(q3),
        ship=("YES - widen `frame=` to a Fano line; seven distinct reads, "
              "bit-exact back-compat at the CD frame, fiber guard intact"
              if (distinct == len(rows) and agree and all(q3)) else
              "NO - at least one leg failed"))

    with open("docs/srmech/notes/octonion_frame_generalised_read_rc421.ndjson",
              "w", encoding="utf-8", newline="\n") as fh:
        for r in out:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
