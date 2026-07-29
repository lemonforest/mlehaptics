"""rc360 RECOVERY — measure every shipped-prose number. Exact ints only."""
import itertools
import json
import sys

import srmech
from srmech.amsc import _native
from srmech.amsc.cascade import (algebra_table, associator, cd_basis,
                                 random_anticommutative_table)

print("ARTIFACT UNDER TEST:", srmech.__file__, srmech.__version__,
      "HAS_NATIVE=%s" % _native.HAS_NATIVE, flush=True)

OUT = []


def emit(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


def flex_violations(dim, table):
    """Linearised flexible law (x,y,z)+(z,y,x)=0 over the dim**3 triples."""
    basis = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any((u + v) != 0 for u, v in
                      zip(associator(basis[i], basis[j], basis[k], table=table),
                          associator(basis[k], basis[j], basis[i], table=table))))


# ── 1. the ladder is flexible at every rung we can reach ──────────────
for dim in (2, 4, 8, 16):
    emit(claim="ladder_flexible", dim=dim,
         violations=flex_violations(dim, algebra_table(dim)), total=dim ** 3)

# ── 2. all eight gamma-twists at dim 8 are flexible ───────────────────
tw = {}
for g in itertools.product((1, -1), repeat=3):
    tw["".join("+" if v == 1 else "-" for v in g)] = flex_violations(
        8, algebra_table(8, list(g)))
emit(claim="gamma_twists_flexible_dim8", n_twists=len(tw), by_twist=tw,
     all_zero=all(v == 0 for v in tw.values()))

# ── 3. the control BREAKS flexibility — 12 NAMED keys ─────────────────
KEYS12 = tuple("control-%02d" % n for n in range(1, 13))
for dim in (4, 8):
    xor = {k: flex_violations(dim, random_anticommutative_table(
        dim, k, keep_xor_lane=True)) for k in KEYS12}
    free = {k: flex_violations(dim, random_anticommutative_table(
        dim, k, keep_xor_lane=False)) for k in KEYS12}
    emit(claim="control_breaks_flexibility", dim=dim, total=dim ** 3,
         keys=list(KEYS12),
         xor_min=min(xor.values()), xor_max=max(xor.values()),
         xor_zero_keys=sorted(k for k, v in xor.items() if v == 0),
         free_min=min(free.values()), free_max=max(free.values()),
         free_zero_keys=sorted(k for k, v in free.items() if v == 0),
         xor=xor, free=free)

# ── 4. the three keys the test pins ───────────────────────────────────
emit(claim="test_pinned_keys_dim8",
     xor={k: flex_violations(8, random_anticommutative_table(
         8, k, keep_xor_lane=True))
          for k in ("negative-control-A", "negative-control-B", "k3")},
     free={k: flex_violations(8, random_anticommutative_table(
         8, k, keep_xor_lane=False))
           for k in ("negative-control-A", "negative-control-B", "k3")})

# ── 5. the associativity census THROUGH the op, incl. dim 32 ──────────
for dim in (2, 4, 8, 16, 32):
    basis = [cd_basis(dim, i) for i in range(dim)]
    n = sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
            if all(v == 0 for v in associator(basis[i], basis[j], basis[k])))
    emit(claim="associativity_census", dim=dim, associating=n, total=dim ** 3)

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for rec in OUT:
        fh.write(json.dumps(rec) + "\n")
print("WROTE", sys.argv[1])
