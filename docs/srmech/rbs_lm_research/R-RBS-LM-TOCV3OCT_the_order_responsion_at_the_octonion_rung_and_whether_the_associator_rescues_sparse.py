r"""R-RBS-LM-TOCV3OCT — the v3 order-responsion at the OCTONION rung, and whether the ASSOCIATOR
(a read with NO ℍ analogue) rescues the sparse regime. Extends F1315 up the Hurwitz tower.

WHY THE 𝕆 RUNG IS NOT JUST "MORE OF THE SAME". Measured on rc335:
    commuting pairs   Q8  40/64  = 62.5%      O  88/256 = 34.4%   (O is ~2x LESS commutative)
    associating triples                        O  2752/4096 = 67.2%  -> 1344 NON-associating
So 𝕆 is a strictly richer algebra, AND it carries a read that ℍ does not have at all:
`genome_octonion_associator` (the non-associativity of the ordered fold). Two questions:

  Q-A  Is the v2 false shadow (F1314/F1315) CARRIER-DEPENDENT or CARRIER-INDEPENDENT?
       PREDICTION: carrier-INDEPENDENT and it will fail identically at 𝕆 — because the defect is
       driven by the IDENTITY element (byte 0 commutes with everything at BOTH rungs) plus disjoint
       per-slot support, NOT by how non-commutative the algebra is. A richer algebra cannot save a
       fold that never multiplies two non-identity values in the same slot.
  Q-B  Does the ASSOCIATOR — the genuinely new 𝕆 read — rescue the sparse regime where the
       holonomy cannot? PREDICTION: no, for the same reason (an associator over identities is
       trivial), which would make the associator a richness read, not an ORDER read.

If Q-A confirms, the repair is carrier-independent too, and this responsion is GENOME MACHINERY
(biology:simulation parity — the strand's order-integrity check at every rung) rather than a
siona-local trick: it belongs upstream in srmech. That is the finding this file measures.

Candidates (all on 𝕆 leaves, symbols 0..15, identity 0):
  v2O   per-slot `genome_octonion_holonomy`                       — the shipped fold
  v3aO  position-tag the VALUES (dense Class-A key) then fold      — the "densify" fix
  v3cO  ROTATE-BY-INDEX (Class-C reorient) then fold               — the F1315 winner, lifted
  v3eO  holonomy || ASSOCIATOR (the 𝕆-only read)                   — does non-associativity help?
  v3d   ordered Class-A content-address                            — the carrier-independent bound

DISCIPLINE. Deterministic content-derived leaves (Class-A; never an RNG — F1259/F1304). Degenerate
permutations (every moved leaf byte-identical to the one it replaces = a wire no-op) are filtered.
No numpy, no fractions, no abs(). Shipped ops only: `oct_mult`, `oct_bind`,
`genome_octonion_holonomy`, `genome_octonion_associator`, `sha256_bytes`.

srmech 0.9.0rc335. Composes F1315 (the ℍ-rung result this lifts), F1314 (the false shadow),
F1310/F1311 (the 𝕆 rung + the associator as the 3-index object no 2-tensor holds).
Run:  /tmp/srmech_335/bin/python3 R-RBS-LM-TOCV3OCT_*.py
"""
import itertools
import sys

from srmech.amsc import genome as G, octonion as O
from srmech.amsc.format import sha256_bytes

LEAF_DIM = 128
N_LEAVES = 4
TRIALS = 20
DENSITIES = (1, 2, 4, 8, 16, 32, 64, 128)
SECT = G.OCTONION_SECTORS          # 16


def _digest_stream(key, n):
    out, ctr = bytearray(), 0
    while len(out) < n:
        out.extend(bytes.fromhex(sha256_bytes(key + b":%d" % ctr)))
        ctr += 1
    return bytes(out[:n])


def sparse_leaf(key, nonzero):
    """An 𝕆 leaf with exactly `nonzero` non-identity slots (values 1..15), content-deterministic."""
    ds = _digest_stream(key, LEAF_DIM * 2)
    slots, i = [], 0
    while len(slots) < nonzero and i < len(ds):
        s = ds[i] % LEAF_DIM
        if s not in slots:
            slots.append(s)
        i += 1
    leaf = bytearray(LEAF_DIM)
    for j, s in enumerate(slots):
        leaf[s] = (ds[LEAF_DIM + j] % (SECT - 1)) + 1     # 1..15, never the identity
    return bytes(leaf)


def position_key(idx):
    """DENSE Class-A position key over 𝕆: every slot in 1..15."""
    ds = _digest_stream(b"toc/v3aO/pos:%d" % idx, LEAF_DIM)
    return bytes((b % (SECT - 1)) + 1 for b in ds)


def _fold(turns):
    return bytes(int(x) for x in G.genome_octonion_holonomy(list(turns), LEAF_DIM))


def order_fp_v2O(turns):
    return sha256_bytes(b"v2O:" + _fold(turns))[:16]


def order_fp_v3aO(turns):
    tagged = [O.oct_bind(t, position_key(i)) for i, t in enumerate(turns)]
    return sha256_bytes(b"v3aO:" + _fold(tagged))[:16]


def _rotated(turns):
    stride = (int(sha256_bytes(b"toc/v3cO/stride")[:2], 16) % (LEAF_DIM - 1)) + 1
    out = []
    for i, t in enumerate(turns):
        k = (stride * i) % LEAF_DIM
        out.append(bytes(t[-k:] + t[:-k]) if k else bytes(t))
    return out


def order_fp_v3cO(turns):
    return sha256_bytes(b"v3cO:" + _fold(_rotated(turns)))[:16]


def order_fp_v3eO(turns):
    """holonomy || ASSOCIATOR — the 𝕆-only read. Does non-associativity add ORDER information?"""
    assoc = bytes(int(x) for x in G.genome_octonion_associator(list(turns), LEAF_DIM))
    return sha256_bytes(b"v3eO:" + _fold(turns) + b"|" + assoc)[:16]


def order_fp_v3d(turns):
    acc = bytearray()
    for t in turns:
        acc.extend(t)
    return sha256_bytes(b"toc/v3d:" + bytes(acc))[:16]


RESPONSIONS = (("v2O  (per-slot fold)", order_fp_v2O),
               ("v3aO (position-tag)", order_fp_v3aO),
               ("v3cO (rotate-by-index)", order_fp_v3cO),
               ("v3eO (holo||associator)", order_fp_v3eO),
               ("v3d  (ordered Class-A)", order_fp_v3d))


def main():
    import srmech
    print("=== v3 order-responsion at the OCTONION rung (srmech %s) ===" % srmech.__version__)
    com = sum(1 for a in range(SECT) for b in range(SECT) if O.oct_mult(a, b) == O.oct_mult(b, a))
    tot = SECT ** 3
    assoc = sum(1 for a in range(SECT) for b in range(SECT) for c in range(SECT)
                if O.oct_mult(O.oct_mult(a, b), c) == O.oct_mult(a, O.oct_mult(b, c)))
    print("    O structure: commuting %d/%d (%.1f%%) | associating %d/%d (%.1f%%) | identity 0 commutes with all: %s"
          % (com, SECT * SECT, 100.0 * com / (SECT * SECT), assoc, tot, 100.0 * assoc / tot,
             all(O.oct_mult(0, x) == x for x in range(SECT))))
    perms = [p for p in itertools.permutations(range(N_LEAVES)) if p != tuple(range(N_LEAVES))]
    print("    %d leaves x %d slots | %d perms x %d trials = %d perms/row\n"
          % (N_LEAVES, LEAF_DIM, len(perms), TRIALS, len(perms) * TRIALS))
    header = "  nonzero/leaf  density  " + "".join("%-25s" % n for n, _ in RESPONSIONS)
    print(header)
    print("  " + "-" * (len(header) - 2))
    totals = {n: 0 for n, _ in RESPONSIONS}
    for nz in DENSITIES:
        counts = {n: 0 for n, _ in RESPONSIONS}
        denom = 0
        for trial in range(TRIALS):
            leaves = [sparse_leaf(b"toc/v3O/nz%d/t%d/leaf%d" % (nz, trial, k), nz)
                      for k in range(N_LEAVES)]
            base = {n: fn(leaves) for n, fn in RESPONSIONS}
            for p in perms:
                if all(leaves[p[i]] == leaves[i] for i in range(N_LEAVES) if p[i] != i):
                    continue                       # degenerate no-op; equal fp is CORRECT
                permuted = [leaves[i] for i in p]
                denom += 1
                for n, fn in RESPONSIONS:
                    if fn(permuted) == base[n]:
                        counts[n] += 1
        for n in counts:
            totals[n] += counts[n]
        cells = "".join("%-25s" % ("%d/%d = %5.1f%%" % (counts[n], denom, 100.0 * counts[n] / denom))
                        for n, _ in RESPONSIONS)
        print("  %10d    %5.1f%%  %s" % (nz, 100.0 * nz / LEAF_DIM, cells))

    print("\n  TOTAL collisions:")
    for n, _ in RESPONSIONS:
        print("    %-25s %d" % (n, totals[n]))

    print("\n=== the mandated-regime gate (1 non-zero slot/leaf) ===")
    leaves = [sparse_leaf(b"toc/v3O/gate/leaf%d" % k, 1) for k in range(N_LEAVES)]
    passers = []
    for n, fn in RESPONSIONS:
        base = fn(leaves)
        coll = sum(1 for p in perms if fn([leaves[i] for i in p]) == base)
        if coll == 0:
            passers.append(n)
        print("    %-25s %2d/%d -> %s" % (n, coll, len(perms), "PASS" if coll == 0 else "FALSE SHADOW"))

    print("\n=== Q-A: is the v2 false shadow CARRIER-DEPENDENT? ===")
    print("    O is ~2x less commutative than Q8 (34.4%% vs 62.5%%) and 32.8%% non-associative.")
    print("    v2O at the gate: %s"
          % ("STILL FAILS -> the defect is CARRIER-INDEPENDENT (identity + disjoint support, not algebra richness)"
             if "v2O  (per-slot fold)" not in passers else "passes -> the defect WAS carrier-dependent"))
    print("=== Q-B: does the ASSOCIATOR rescue sparse? ===")
    print("    v3eO at the gate: %s"
          % ("NO -> the associator is a RICHNESS read, not an ORDER read"
             if "v3eO (holo||associator)" not in passers else "YES -> non-associativity adds order information"))

    ok = "v3cO (rotate-by-index)" in passers
    print("\n=== %s ===" % ("PASS: the Class-C reorient repair LIFTS to the O rung — carrier-independent machinery."
                            if ok else "FAIL: the repair does NOT lift to O."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
