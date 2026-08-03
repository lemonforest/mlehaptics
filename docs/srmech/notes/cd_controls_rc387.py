"""rc387 (`#T1037`, closing `#T1032`) — the two STRUCTURED Cayley–Dickson
negative controls, now SHIPPED ops, reproduced THROUGH the shipped measurement
ops (associator + inertia_signature). Exact ints only.

Run:  python cd_controls_rc387.py cd_controls_rc387.ndjson

This lifts the two structured controls that rc360 hand-rolled in
`docs/srmech/notes/rc360_exact_ops_verification.py` (functions ``flip_pair`` and
``group_ring`` there) and re-measures them, now that they are registered ops
``srmech.cascade.flip_pair`` and ``srmech.cascade.group_algebra_table``. The
numbers below back the shipped prose:

* flip_pair breaks FLEXIBILITY at a CONSTANT 4 per rung (4/64 at dim 4, 4/512 at
  dim 8, 4/4096 at dim 16), uniformly over every admissible pair, while its
  inertia signature is IDENTICAL to the definite ladder's (the flip is
  off-diagonal, the trace form is diagonal).
* group_algebra_table is flexible AND associative (0 bite on the laws), and its
  bite is the METRIC: trace signatures (2,0,0)/(3,1,0)/(5,3,0)/(9,7,0) at dim
  2/4/8/16 vs the ladder's (1,1,0)/(1,3,0)/(1,7,0)/(1,15,0).
* the "wrong-quotient differs from the ladder on N triples" number is a FORCED
  IDENTITY (the group ring's own defect is identically 0, so it differs exactly
  where the ladder is non-associating) — recorded, and LABELLED, as one.

No stdlib fractions; the CD element carrier is srmech.math.q.Q. No abs().
"""
import json
import sys

import srmech
from srmech import _native
from srmech.cascade import (algebra_table, associator, cd_basis, flip_pair,
                            group_algebra_table, inertia_signature)

print("ARTIFACT UNDER TEST:", srmech.__file__, srmech.__version__,
      "HAS_NATIVE=%s" % _native.HAS_NATIVE, flush=True)

OUT = []


def emit(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


def flex_violations(dim, table):
    """Linearised flexible law (x,y,z)+(z,y,x)=0 over the dim**3 triples, read
    THROUGH the shipped associator."""
    basis = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any((u + v) != 0 for u, v in
                      zip(associator(basis[i], basis[j], basis[k], table=table),
                          associator(basis[k], basis[j], basis[i], table=table))))


def nonassoc(dim, table):
    basis = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any(v != 0 for v in associator(basis[i], basis[j], basis[k],
                                                 table=table)))


def sig(table):
    return list(inertia_signature(table)["signature"])


# -- 1. flip_pair: the ONLY flexibility control, a CONSTANT 4 per rung --------
for dim, pairs in ((4, [(i, j) for i in range(1, 4) for j in range(i + 1, 4)]),
                   (8, [(i, j) for i in range(1, 8) for j in range(i + 1, 8)]),
                   (16, [(1, 2)])):
    rows = {}
    for (i, j) in pairs:
        t = flip_pair(dim, i, j)
        rows["%d,%d" % (i, j)] = {"flex": flex_violations(dim, t),
                                  "nonassoc": nonassoc(dim, t),
                                  "signature": sig(t)}
    ladder_sig = sig(algebra_table(dim))
    emit(claim="flip_pair_flexibility_control", dim=dim, total=dim ** 3,
         n_pairs=len(pairs),
         distinct=sorted({(v["flex"], tuple(v["signature"]))
                          for v in rows.values()}),
         all_break_flexibility=all(v["flex"] > 0 for v in rows.values()),
         flex_is_constant_4=all(v["flex"] == 4 for v in rows.values()),
         signature_unchanged=all(v["signature"] == ladder_sig
                                 for v in rows.values()),
         ladder_signature=ladder_sig)

# -- 2. group_algebra_table: 0 bite on the laws, full bite on the METRIC ------
for dim in (2, 4, 8, 16):
    ring, ladder = group_algebra_table(dim), algebra_table(dim)
    basis = [cd_basis(dim, i) for i in range(dim)]
    # THE TAUTOLOGY, recorded as one: the ring's own defect is identically 0,
    # so "differs from the ladder" IS the ladder's own non-associating census.
    differs = sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
                  if associator(basis[i], basis[j], basis[k], table=ladder)
                  != associator(basis[i], basis[j], basis[k], table=ring))
    la_nonassoc = nonassoc(dim, ladder)
    emit(claim="group_algebra_wrong_quotient_control", dim=dim, total=dim ** 3,
         ring_flex=flex_violations(dim, ring), ring_nonassoc=nonassoc(dim, ring),
         ring_signature=sig(ring), ladder_signature=sig(ladder),
         differs_from_ladder=differs, ladder_nonassoc=la_nonassoc,
         differs_is_forced_identity=(differs == la_nonassoc))

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for rec in OUT:
        fh.write(json.dumps(rec) + "\n")
print("WROTE", sys.argv[1])
