r"""R-RBS-LM-BITPACK (F1264 NEXT b + c) — realise the `ceil(log2 N)` storage instead of paying 32-64 bits a
cell, and push the DIMENSION lever to 32768 to find where it saturates.

User (2026-07-20): *"bit-pack the counts and push dim to 32768"*

F1264 measured two things this builds on:
  * the count matrix is 100% DENSE in cells — there is no occupancy sparsity — but the VALUE RANGE is small
    (max cell 1100 at N=4000), so `ceil(log2 N)` bits per cell suffices. Claimed 5.5 KB vs 32 KB naive.
  * DIMENSION is the working lever: recall 0.200 -> 0.800 across dim 1024 -> 8192 at fixed N=1000, clean and
    monotonic. Where does that stop?

PART A — BIT-PACKING, VERIFIED NOT ASSERTED. A packed store is only worth anything if it round-trips exactly.
So: build the plain counts, build the packed counts, assert cell-for-cell equality, and report the REAL byte
sizes (`sys.getsizeof` on the plain nested lists is the honest comparison target, not a formula). The packed
form is a flat bytearray addressed at bit granularity — Class-B framing, no third-party bitset.

PART B — THE DIMENSION PUSH. dim 8192 -> 16384 -> 32768 at fixed N, FULL read (F1264 established the
margin-sparse read is refuted, so it must not be used here). The read is flattened to one array and scored
with a zip, because at dim=32768 an O(N*dim) probe in nested Python loops is the difference between 30 s and
30 min. FALSIFIER for the lever: if recall flattens between 16384 and 32768, dimension has saturated and
F1259's designed-family question moves back up the queue.

srmech 0.9.0rc288. Integer accumulators; no numpy.
Composes F1264 (the storage + lever measurements), F1263 (the count structure), F1259 (the family question).
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-BITPACK_*.py [--n 1000]
"""
import argparse
import math
import sys
import time
from array import array

from srmech.amsc import hdc

T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


# ---------------------------------------------------------------- the plain store (F1263)
def build_counts_flat(bound, dim):
    """Flat counts: index = coordinate*4 + sector. Flat because the read is the hot path."""
    C = array("i", bytes(4 * dim * 4))
    for v in bound:
        base = 0
        for s in v:
            C[base + s] += 1
            base += 4
    return C


# ---------------------------------------------------------------- PART A: the packed store
class PackedCounts:
    """The count matrix at `bits` bits per cell — Class-B framing over a flat bytearray.

    F1264 measured that the matrix is dense in cells but small in VALUE RANGE, so the win is bit-width,
    not sparsity. `bits = ceil(log2(N+1))`.
    """

    def __init__(self, dim, n_items):
        self.dim = dim
        self.bits = max(1, math.ceil(math.log2(n_items + 1)))
        self.cells = dim * 4
        self.buf = bytearray((self.cells * self.bits + 7) // 8)

    def get(self, cell):
        off = cell * self.bits
        byte, sh = off >> 3, off & 7
        chunk = int.from_bytes(self.buf[byte:byte + (self.bits + sh + 7) // 8], "big")
        total = ((self.bits + sh + 7) // 8) * 8
        return (chunk >> (total - sh - self.bits)) & ((1 << self.bits) - 1)

    def set(self, cell, val):
        off = cell * self.bits
        byte, sh = off >> 3, off & 7
        nbytes = (self.bits + sh + 7) // 8
        total = nbytes * 8
        chunk = int.from_bytes(self.buf[byte:byte + nbytes], "big")
        mask = ((1 << self.bits) - 1) << (total - sh - self.bits)
        chunk = (chunk & ~mask) | ((val & ((1 << self.bits) - 1)) << (total - sh - self.bits))
        self.buf[byte:byte + nbytes] = chunk.to_bytes(nbytes, "big")

    def nbytes(self):
        return len(self.buf)


def part_a(bound, dim, N):
    log("")
    log("--- PART A: bit-pack the counts, and VERIFY the round-trip ---")
    C = build_counts_flat(bound, dim)
    P = PackedCounts(dim, N)
    for cell in range(dim * 4):
        P.set(cell, C[cell])
    bad = sum(1 for cell in range(dim * 4) if P.get(cell) != C[cell])
    log("  bits/cell     = %d   (ceil(log2(%d+1)))" % (P.bits, N))
    log("  round-trip    : %s  (%d mismatching cells of %d)" %
        ("EXACT" if bad == 0 else "*** BROKEN ***", bad, dim * 4))
    plain_bytes = C.itemsize * len(C)
    log("  plain array('i') = %8d B" % plain_bytes)
    log("  packed bytearray = %8d B   -> %.2fx smaller" % (P.nbytes(), plain_bytes / P.nbytes()))
    log("  bundle (for scale) = %6d B   -> packed counts are %.1fx the bundle" % (dim, P.nbytes() / dim))
    t = time.time()
    for cell in range(0, dim * 4, 97):
        P.get(cell)
    log("  read cost: %.1f us per packed get (vs a plain array index) — the price of the %.2fx"
        % (1e6 * (time.time() - t) / max(1, len(range(0, dim * 4, 97))), plain_bytes / P.nbytes()))
    return bad == 0


# ---------------------------------------------------------------- PART B: the dimension push
def read_full_flat(C, key, cands):
    """score(cand) = sum_i C[i*4 + (key[i]^cand[i])]. Flattened + zipped: the O(N*dim) probe, made bearable."""
    best, bi = None, -1
    for j, cand in enumerate(cands):
        sc = 0
        base = 0
        for k, c in zip(key, cand):
            sc += C[base + (k ^ c)]
            base += 4
        if best is None or sc > best:
            best, bi = sc, j
    return bi


def part_b(N, dims):
    log("")
    log("--- PART B: push the DIMENSION lever (FULL read — the sparse read is refuted, F1264) ---")
    log("  %-9s %-16s %-10s" % ("dim", "counts recall", "secs"))
    prev = None
    for d in dims:
        keys = [bytes(hdc.klein4_random(d, seed=10_000 + i)) for i in range(N)]
        vals = [bytes(hdc.klein4_random(d, seed=20_000 + i)) for i in range(N)]
        bound = [bytes(a ^ b for a, b in zip(k, v)) for k, v in zip(keys, vals)]
        C = build_counts_flat(bound, d)
        probes = list(range(0, N, max(1, N // 10)))
        t = time.time()
        hits = sum(1 for p in probes if read_full_flat(C, keys[p], vals) == p)
        r = hits / len(probes)
        log("  %-9d %-16.3f %-10.1f %s" % (d, r, time.time() - t,
                                           "" if prev is None else ("(+%.3f)" % (r - prev))))
        prev = r
    log("")
    log("  FALSIFIER: if recall flattens between the last two dims, the dimension lever has SATURATED")
    log("  and F1259's designed-family question moves back up the queue.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--pack-dim", type=int, default=4096)
    args = ap.parse_args()

    import srmech
    log("=== BITPACK + DIMENSION PUSH (srmech %s) ===" % srmech.__version__)

    d0 = args.pack_dim
    keys = [bytes(hdc.klein4_random(d0, seed=10_000 + i)) for i in range(args.n)]
    vals = [bytes(hdc.klein4_random(d0, seed=20_000 + i)) for i in range(args.n)]
    bound = [bytes(a ^ b for a, b in zip(k, v)) for k, v in zip(keys, vals)]
    part_a(bound, d0, args.n)

    part_b(args.n, (8192, 16384, 32768))
    return 0


if __name__ == "__main__":
    sys.exit(main())
