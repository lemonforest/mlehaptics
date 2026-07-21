r"""R-RBS-LM-EXPONENT — (1) PIN the capacity exponent with a finer ladder over >=4 dimensions, and (2) test
whether the chunk-size structure is CAYLEY-DICKSON flavoured (C/H/O/S = 2/4/8/16) or just smooth.

User (2026-07-20): *"do the finer ladder over 4 dims to pin the exponent. also curious how that looks like the
same c/h/o/s tower, the chunk size. like these don't look magic, they look cayley-dickson flavored maybe."*

PART 1 — THE EXPONENT. F1266 refuted the ratio law (N/dim is not invariant: recall 0.778 sat at N/dim 0.2373
at dim 2048 and 0.1780 at dim 4096) and measured 1.50x capacity per doubling of dim, implying
capacity ~ dim^log2(1.5) = dim^0.585. BUT the ladder there WAS 1.5x geometric, so "one ladder step" and "1.5x"
were the same quantity -- the exponent could not be separated from the sampling. Fixed here by:
  * dims on a sqrt(2) ladder (1024, 1448, 2048, 2896, 4096) -- FIVE dims, and three of them non-dyadic
  * per dim, BISECT for the N where recall crosses 0.5 -- a threshold crossing, not a ladder step
  * fit log(N_crit) vs log(dim); the slope IS the exponent, and the residual says how well a power law fits
FALSIFIER: if the log-log fit has large residuals, a single power law is the wrong model and the honest answer
is "no clean exponent", not a fitted number.

PART 2 — THE CAYLEY-DICKSON READING. The chunk divisors that worked in F1266 were 16, 8, 4 -- and C/H/O/S sits
at 2/4/8/16, so the tower and the divisors coincide. THE TRAP IS THE SAME ONE F1266 CAUGHT ME IN: **I chose
those divisors.** Powers of two look structural when you only sample powers of two. So this sweeps k = 2..24
INCLUDING the non-CD values (3, 5, 6, 7, 9, 10, 12, 14, 20, 24) and asks whether the CD points {2,4,8,16} are
distinguished at all.
FALSIFIER for the CD reading: if recall-vs-k is a smooth monotone function with no feature at 2/4/8/16, the
tower is NOT showing up in this object and the resemblance was my sampling grid.

srmech 0.9.0rc288. Integer accumulators; Class-K cascade.magnitude, never the builtin. No numpy.
Composes F1266 (which refuted the ratio law and flagged the sampling trap this harness is built to avoid),
F1265, F1264, F1263, the Hurwitz/CD ladder (DUALITY.md / TRIALITY.md), #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-EXPONENT_*.py

DEFECT NOTICE (added 2026-07-21, issue #1454 / F1276): the chunk router below uses builtin `hash()`,
which is PYTHONHASHSEED-SALTED, so the partition it produces DIFFERS ON EVERY INTERPRETER RUN and the
exact numbers this harness printed are NOT reproducible. The harness is PRESERVED AS-RUN (it is the
historical probe that produced the finding; rewriting it would make it no longer that thing) — see the
F1260 precedent of repairing live code while preserving probes. The CLAIM was re-verified under pinned
salts in F1276: revival gap 0.9184 under every salt, spread 0.0408 at 48 probes, and Class-A
`format.sha256_bytes` routing reproduces it (1.0000). So the EFFECT stands; only the digits were ever
unreproducible. New code must route via `srmech.amsc.format.sha256_bytes` per the CLAUDE.md §2 row.
"""
from srmech.amsc import format as fmt  # Class-A content-address (F1284)
import math
import sys
import time
from array import array

from srmech.amsc import cascade, hdc

T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def build(bound, dim):
    C = array("i", bytes(4 * dim * 4))
    for v in bound:
        b = 0
        for s in v:
            C[b + s] += 1
            b += 4
    return C


def read_full(C, key, cands):
    best, bi = None, -1
    for j, c in enumerate(cands):
        sc, b = 0, 0
        for k, x in zip(key, c):
            sc += C[b + (k ^ x)]
            b += 4
        if best is None or sc > best:
            best, bi = sc, j
    return bi


_CACHE = {}


def carriers(n, dim):
    if dim not in _CACHE or len(_CACHE[dim][0]) < n:
        k = [bytes(hdc.klein4_random(dim, seed=10_000 + i)) for i in range(n)]
        v = [bytes(hdc.klein4_random(dim, seed=20_000 + i)) for i in range(n)]
        b = [bytes(x ^ y for x, y in zip(a, c)) for a, c in zip(k, v)]
        _CACHE[dim] = (k, v, b)
    k, v, b = _CACHE[dim]
    return k[:n], v[:n], b[:n]


def recall_at(n, dim, n_probe=8):
    k, v, b = carriers(n, dim)
    C = build(b, dim)
    pr = list(range(0, n, max(1, n // n_probe)))
    return sum(1 for p in pr if read_full(C, k[p], v) == p) / len(pr)


# ---------------------------------------------------------------- PART 1
def part1():
    log("")
    log("=== PART 1 — PIN THE EXPONENT (bisect for the recall=0.5 crossing, 5 dims, sqrt(2) ladder) ===")
    log("  F1266 measured 1.50x per doubling but its ladder WAS 1.5x geometric — exponent inseparable")
    log("  from sampling. Here: a threshold CROSSING per dim, then a log-log fit.")
    DIMS = [1024, 1448, 2048, 2896, 4096]
    TARGET = 0.5
    pts = []
    log("")
    log("  %-8s %-10s %-10s %-8s" % ("dim", "N_crit", "N/dim", "evals"))
    for dim in DIMS:
        lo, hi = 32, 4096
        # coarse bracket first so the bisect stays cheap
        while recall_at(hi, dim, 6) > TARGET and hi < 6000:
            lo, hi = hi, int(hi * 1.6)
        evals = 0
        while hi - lo > max(16, lo // 12):
            mid = (lo + hi) // 2
            if recall_at(mid, dim, 6) > TARGET:
                lo = mid
            else:
                hi = mid
            evals += 1
        ncrit = (lo + hi) // 2
        pts.append((dim, ncrit))
        log("  %-8d %-10d %-10.4f %-8d" % (dim, ncrit, ncrit / dim, evals))

    # log-log fit: log N = a*log dim + b
    xs = [math.log(d) for d, _ in pts]
    ys = [math.log(n) for _, n in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    a = sxy / sxx
    b = my - a * mx
    resid = [y - (a * x + b) for x, y in zip(xs, ys)]
    maxres = max(cascade.magnitude(r) for r in resid)
    log("")
    log("  log-log fit:  N_crit ~ dim^%.3f" % a)
    log("  max |residual| in log space = %.4f  (%.1f%% in linear terms)" % (maxres, 100 * (math.exp(maxres) - 1)))
    log("")
    log("  reference exponents:  ratio law 1.000 | measured %.3f | sqrt law 0.500" % a)
    verdict = ("a single power law FITS (residuals small)" if maxres < 0.10
               else "residuals LARGE — one power law is the wrong model; no clean exponent")
    log("  => %s" % verdict)
    return a


# ---------------------------------------------------------------- PART 2
def part2():
    log("")
    log("=== PART 2 — IS THE CHUNK STRUCTURE CAYLEY-DICKSON (C/H/O/S = 2/4/8/16)? ===")
    log("  THE TRAP, same one F1266 caught: F1266's divisors were 16, 8, 4 — I CHOSE powers of two,")
    log("  so of course they line up with the CD tower. Sweeping NON-CD divisors to see if 2/4/8/16")
    log("  are distinguished at all.")
    dim, M = 2048, 3000
    k, v, b = carriers(M, dim)
    CD = {2, 4, 8, 16}
    log("")
    log("  %-6s %-9s %-9s %-10s %-6s" % ("k", "chunk cap", "chunks", "recall", "CD?"))
    rows = []
    for kk in (2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 24):
        cap = dim // kk
        n_ch = (M + cap - 1) // cap
        buckets = [[] for _ in range(n_ch)]
        for i in range(M):
            buckets[int(fmt.sha256_bytes(k[i])[:16], 16) % n_ch].append(i)
        stores = [build([b[i] for i in bk], dim) if bk else None for bk in buckets]
        probes = list(range(0, M, max(1, M // 12)))
        hits = 0
        for p in probes:
            ch = int(fmt.sha256_bytes(k[p])[:16], 16) % n_ch
            mem = buckets[ch]
            if not mem:
                continue
            got = read_full(stores[ch], k[p], [v[i] for i in mem])
            hits += (mem[got] == p)
        r = hits / len(probes)
        rows.append((kk, r))
        log("  %-6d %-9d %-9d %-10.3f %-6s" % (kk, cap, n_ch, r, "CD" if kk in CD else ""))

    # is there a FEATURE at the CD points, or is it smooth?
    log("")
    log("  --- is recall-vs-k SMOOTH, or featured at 2/4/8/16? ---")
    d1 = [(rows[i + 1][0], rows[i + 1][1] - rows[i][1]) for i in range(len(rows) - 1)]
    log("    step deltas: %s" % " ".join("%d:%+.2f" % (kk, d) for kk, d in d1))
    cd_steps = [d for kk, d in d1 if kk in CD]
    non_cd = [d for kk, d in d1 if kk not in CD]
    if cd_steps and non_cd:
        mcd = sum(cascade.magnitude(x) for x in cd_steps) / len(cd_steps)
        mnc = sum(cascade.magnitude(x) for x in non_cd) / len(non_cd)
        log("    mean |delta| ENTERING a CD divisor     = %.4f  (n=%d)" % (mcd, len(cd_steps)))
        log("    mean |delta| entering a non-CD divisor = %.4f  (n=%d)" % (mnc, len(non_cd)))
        log("    => %s" % ("CD points ARE distinguished (bigger jumps)" if mcd > 1.8 * mnc else
                           "NO CD feature — the curve is smooth in k; the tower resemblance was the sampling grid"))


def main():
    import srmech
    log("=== EXPONENT + CD (srmech %s) ===" % srmech.__version__)
    part1()
    part2()
    log("")
    log("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
