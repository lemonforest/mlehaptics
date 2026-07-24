#!/usr/bin/env python3
"""Falsification spike: is the GENOME klein4 coupling (through the_one) NATIVE or SHADOW?

The user's worry: the genome does not use bare V4 — quad_turn couples turns
"through the_one" (klein4_from_one / klein4_bind / genome_from_graph coupling arg).
A bare V4 group is abelian/associative (native). But IF the_one-coupling introduced
an octonion-like (non-associative) twist, the genome could be pushed above the
non-associativity wall into frame-relative (SHADOW) territory like the octonion
(gauge dev 0.188).

TEST the ACTUAL genome coupling, not an idealized V4.

Reference numbers (prior octonion workflow):
  octonion (non-assoc) gauge dev 0.188   -> SHADOW / frame-relative
  C/U(1) magnetic + H quaternion gauge dev 3.3e-15 -> NATIVE / frame-free
  identity floor 0.000

In-framework (numpy-free) throughout: srmech's own klein4 ops + eigendecompose.
"""
import sys, random
from array import array
sys.path.insert(0, ".")

from srmech.amsc.hdc import klein4_bind, klein4_from_one, klein4_expand, HV
from srmech.amsc.cascade.one import the_one
from srmech.amsc.laplacian import klein4_gain_laplacian, symmetric_eigendecompose

random.seed(20260722)

# ------------------------------------------------------------------ Part A
# The actual algebra of the coupling operation. quad_turn(turn, coupling)
# == klein4_bind(turn, coupling) == element-wise XOR on symbols {0,1,2,3}.
# Each symbol is (g1<<1)|g0 in (F2)^2. Show the 4x4 Cayley table of the
# per-element operation (single-position vectors) and read off the group.
print("=" * 70)
print("PART A - the actual coupling algebra (klein4_bind == V4 XOR)")
print("=" * 70)
def elt(x):
    return HV(array("B", [x]), sectors=4)
table = []
for a in range(4):
    row = []
    for b in range(4):
        r = list(klein4_bind(elt(a), elt(b)))[0]
        row.append(r)
    table.append(row)
print("Cayley table (rows a=0..3, cols b=0..3), entry = a*b:")
for a in range(4):
    print("  ", table[a])
# Check group axioms on the 4-element table.
identity = None
for e in range(4):
    if all(table[e][b] == b for b in range(4)) and all(table[a][e] == a for a in range(4)):
        identity = e
comm_tbl = all(table[a][b] == table[b][a] for a in range(4) for b in range(4))
assoc_tbl = all(
    table[table[a][b]][c] == table[a][table[b][c]]
    for a in range(4) for b in range(4) for c in range(4)
)
self_inv = all(table[a][a] == 0 for a in range(4))
print(f"identity element     : {identity}")
print(f"commutative (4-elt)  : {comm_tbl}")
print(f"associative (4-elt)  : {assoc_tbl}")
print(f"every elt self-inverse (a*a=0, => exponent-2, => V4 not Z4): {self_inv}")
print("Verdict A: coupling op is the Klein four-group V4 = (Z2)^2 (abelian, "
      "associative, exponent 2). NOT a Cayley-Dickson / octonion product.")

# ------------------------------------------------------------------ Part B
# Empirical associativity + commutativity of the coupling over MANY random
# klein4 objects, at the FULL vector width, using BOTH:
#   (i)  arbitrary random klein4 vectors (klein4_expand), and
#   (ii) ACTUAL genome couplings from klein4_from_one(the_one(...)) -- the
#        exact objects the genome quad_turn slot consumes.
print()
print("=" * 70)
print("PART B - empirical associativity/commutativity of the GENOME coupling")
print("=" * 70)

def bind(a, b):
    return klein4_bind(a, b)

def eq(a, b):
    return bytes(bytearray(a)) == bytes(bytearray(b))

def test_pool(name, pool, n_trials):
    assoc_fail = 0
    comm_fail = 0
    for _ in range(n_trials):
        a, b, c = random.choice(pool), random.choice(pool), random.choice(pool)
        # associativity: (a*b)*c == a*(b*c)
        if not eq(bind(bind(a, b), c), bind(a, bind(b, c))):
            assoc_fail += 1
        # commutativity: a*b == b*a
        if not eq(bind(a, b), bind(b, a)):
            comm_fail += 1
    print(f"[{name}] trials={n_trials}")
    print(f"    associativity failures : {assoc_fail}/{n_trials} "
          f"= {assoc_fail/n_trials:.6f}")
    print(f"    commutativity failures : {comm_fail}/{n_trials} "
          f"= {comm_fail/n_trials:.6f}")
    return assoc_fail, comm_fail

D = 64
# (i) arbitrary random klein4 vectors
rand_pool = [klein4_expand(D, random.randrange(1 << 30)) for _ in range(64)]
a1, c1 = test_pool("random klein4 vectors", rand_pool, 20000)

# (ii) ACTUAL genome couplings: klein4_from_one over a spread of (sigma, theta)
one_pool = []
for _ in range(64):
    sigma = random.choice((1, -1))
    tn = random.randrange(-500, 500)
    td = random.randrange(1, 500)
    one_pool.append(klein4_from_one(the_one(sigma, tn, td), D))
a2, c2 = test_pool("genome klein4_from_one couplings", one_pool, 20000)

# (iii) MIXED: couple a genome turn THROUGH the_one coupling exactly as
# quad_turn does, then re-associate against further couplings -- the precise
# "navigate across turns through coupling" chain the storage layer performs.
mixed_pool = rand_pool[:32] + one_pool[:32]
a3, c3 = test_pool("mixed turns + genome couplings (quad_turn chain)",
                   mixed_pool, 20000)

total_assoc = a1 + a2 + a3
total_comm = c1 + c2 + c3
print(f"\nTOTAL associativity failures: {total_assoc}/60000")
print(f"TOTAL commutativity failures: {total_comm}/60000")

# ------------------------------------------------------------------ Part C
# Put a gauge-deviation NUMBER on the "native" claim, matching the octonion
# workflow. Build a genome-coupled V4-gain Laplacian: per-edge V4 gains are
# derived from the ACTUAL genome coupling (klein4_from_one symbols). Then apply
# a random V4 SWITCHING (gauge transform) s: V -> V4, transform each gain
#     g'_uv = s(u) XOR g_uv XOR s(v)
# and re-measure the spectrum. An ABELIAN/ASSOCIATIVE gain group has a
# gauge-INVARIANT Laplacian spectrum (Reff 2012); a non-associative twist would
# break switching consistency and move the spectrum (the octonion 0.188 shadow).
print()
print("=" * 70)
print("PART C - genome-coupled V4-gain Laplacian: gauge deviation")
print("=" * 70)

def v4_xor(a, b):
    return a ^ b  # V4 additive = bitwise XOR on {0,1,2,3}

def sorted_spectrum(n, edges, weights, gains):
    lap = klein4_gain_laplacian(n, edges, weights, gains)
    spec = []
    for s in ("chi00", "chi01", "chi10", "chi11"):
        ev, _ = symmetric_eigendecompose(lap[s])
        spec.extend(sorted(float(x) for x in ev))
    return spec

def spectrum_dev(sp0, sp1):
    return max(abs(x - y) for x, y in zip(sorted(sp0), sorted(sp1)))

n = 8
edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
weights = [1.0 + 0.5 * ((i * 7 + 3) % 5) for i in range(len(edges))]

# genome coupling drives the per-edge gains: sample symbols from a real
# klein4_from_one coupling (the object the genome quad_turn slot holds).
gcoup = klein4_from_one(the_one(-1, 355, 113), max(64, len(edges)))
gsyms = list(gcoup)
gains = [gsyms[k % len(gsyms)] for k in range(len(edges))]

base = sorted_spectrum(n, edges, weights, gains)

devs = []
for _ in range(200):
    s = [random.randrange(4) for _ in range(n)]           # random V4 switching
    gains2 = [v4_xor(v4_xor(s[u], g), s[v])
              for (u, v), g in zip(edges, gains)]
    sp = sorted_spectrum(n, edges, weights, gains2)
    devs.append(spectrum_dev(base, sp))

max_dev = max(devs)
mean_dev = sum(devs) / len(devs)
print(f"genome-coupled V4-gain Laplacian, {len(devs)} random V4 switchings")
print(f"    max  gauge deviation : {max_dev:.3e}")
print(f"    mean gauge deviation : {mean_dev:.3e}")
print(f"  reference: octonion(non-assoc)=0.188 SHADOW | "
      f"C/U(1)+H native=3.3e-15 | identity floor=0.000")

# Identity-floor control: a switching with s == 0 must reproduce base exactly.
zero_dev = spectrum_dev(base, sorted_spectrum(n, edges, weights, gains))
print(f"    identity control (s=0 no-op) dev : {zero_dev:.3e}")

print()
print("=" * 70)
print("MEAS SUMMARY")
print("=" * 70)
print(f"algebra                 : klein4_bind == V4=(F2)^2 XOR (abelian, "
      f"associative, exponent-2); the_one is PROJECTED to a klein4 HV by "
      f"klein4_from_one and enters only as an XOR operand")
print(f"assoc failures (genome) : {total_assoc}/60000 = {total_assoc/60000:.6f}")
print(f"comm  failures (genome) : {total_comm}/60000 = {total_comm/60000:.6f}")
print(f"gauge dev (genome-coupled Laplacian) max={max_dev:.3e} mean={mean_dev:.3e}")
verdict = "NATIVE (frame-free)" if (total_assoc == 0 and total_comm == 0
                                    and max_dev < 1e-9) else "SHADOW (frame-relative)"
print(f"VERDICT                 : GENOME coupling is {verdict}")

# ---- NDJSON results (one record per line; computational-provenance discipline)
import json, os
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "genome_klein4_coupling_native_or_shadow_spike.ndjson") \
    if "__file__" in globals() else "genome_klein4_coupling_native_or_shadow_spike.ndjson"
_recs = [
    {"part": "A_algebra", "op": "klein4_bind==quad_turn", "cayley_table": table,
     "identity": identity, "commutative": comm_tbl, "associative": assoc_tbl,
     "self_inverse_all": self_inv, "group": "V4=(Z2)^2 Klein-four (abelian, exponent-2)"},
    {"part": "B_empirical", "pool": "random_klein4", "trials": 20000,
     "assoc_fail": a1, "comm_fail": c1},
    {"part": "B_empirical", "pool": "genome_klein4_from_one", "trials": 20000,
     "assoc_fail": a2, "comm_fail": c2},
    {"part": "B_empirical", "pool": "mixed_quad_turn_chain", "trials": 20000,
     "assoc_fail": a3, "comm_fail": c3},
    {"part": "B_empirical", "pool": "TOTAL", "trials": 60000,
     "assoc_fail": total_assoc, "comm_fail": total_comm,
     "assoc_frac": total_assoc / 60000, "comm_frac": total_comm / 60000},
    {"part": "C_gauge", "object": "genome-coupled V4-gain Laplacian",
     "n_nodes": n, "n_edges": len(edges), "n_switchings": len(devs),
     "max_gauge_dev": max_dev, "mean_gauge_dev": mean_dev,
     "identity_control_dev": zero_dev,
     "ref_octonion_shadow": 0.188, "ref_native_frame_free": 3.3e-15,
     "ref_identity_floor": 0.0},
    {"part": "VERDICT", "genome_coupling": verdict,
     "reason": "the_one is projected to a klein4 HV by klein4_from_one and enters "
               "ONLY as an XOR operand; the OPERATION is V4 XOR, associative+"
               "commutative regardless of operand content; no octonion twist"},
]
with open(_out, "w", encoding="utf-8") as _f:
    for _r in _recs:
        _f.write(json.dumps(_r) + "\n")
print(f"\nwrote {_out}")
