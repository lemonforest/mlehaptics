r"""R-RBS-LM-POOLED — make the read cost INDEPENDENT of N (fixed candidate pool), validate that it preserves
the EXPONENT, then use the speedup to measure the exponent SPECTRUM properly.

User (2026-07-20): *"yes, build the pooled-read version in parallel. multifractal even follows the MFO reading
of 1D to 11D per excitation state where the floor seems to typically be the UV 2d range."*

WHY POOLED. The read scores each probe against ALL N candidates -> O(N*dim), so cost grows as the very
quantity being swept. Against a FIXED pool of P candidates (the true target + P-1 distractors) the read is
O(P*dim), INDEPENDENT of N. At dim=8192, N=5120 that is 4.2e7 -> 2.1e6 per probe, ~20x, improving as N grows.
That is what buys dim 16384 AND many thresholds inside one budget.

THE CAVEAT, STATED UP FRONT: recall-against-a-pool is an EASIER task than recall-against-all, so N_crit lands
at a different ABSOLUTE value. The claim under test is narrower and must be verified, not assumed:
**does the pooled read preserve the EXPONENT (how N_crit scales with dim)?** PART A does exactly that
comparison. If the exponents disagree, pooling is not a valid substitute and the speedup is unusable -- a real
possible outcome, not a formality.

WHY THIS MATTERS FOR THE MULTIFRACTAL QUESTION. The n=50 run gave exponents 0.867 / 0.801 / 0.767 at
thresholds 0.75 / 0.50 / 0.25 -- monotonically ordered, but with a spread (0.101) COMPARABLE TO THE FIT
RESIDUALS (up to 0.086). Three thresholds cannot separate "a real spectrum" from "scatter with a lucky
ordering". A multifractal claim needs a SPECTRUM: many thresholds, each with an error bar. PART B supplies
that -- 9 thresholds, bootstrap CIs -- so the question becomes decidable rather than suggestive.

FALSIFIER: if the per-threshold exponents share a common value within their bootstrap CIs, there is ONE
exponent and the spectrum reading is dead for this object. If no common value exists, the exponent is a
function of where you read -- the measurable form of "a projection, not a constant".

NOTE ON THE MFO MAPPING, kept honest: the user connects this to the MFO 1D..11D-per-excitation reading with a
UV floor near 2D. This harness does NOT test that and cannot, because there is no defined map from a capacity
exponent to an MFO dimension. What it CAN deliver is the SHAPE: whether a spectrum exists, its RANGE, and
whether it has a FLOOR. Supplying the exponent->dimension map is the separate and PRIOR piece of work; without
it, any numeric correspondence would be numerology.

srmech 0.9.0rc288. Class-K cascade.magnitude, never the builtin. Integer accumulators; no numpy.
Composes the n=50 threshold run, F1267, F1266, F1265, F1264, F1263, F1063 (scale as a fractal TOWER, not a
ladder), #243/F1070 (the asymmetric-resonator arc), #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-POOLED_*.py [--pool 256]
"""
import argparse
import math
import random
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


def score(C, key, cand):
    sc, b = 0, 0
    for k, x in zip(key, cand):
        sc += C[b + (k ^ x)]
        b += 4
    return sc


def recall_full(C, keys, vals, n, n_probe):
    pr = list(range(0, n, max(1, n // n_probe)))
    return sum(1 for p in pr
               if max(range(n), key=lambda j: score(C, keys[p], vals[j])) == p) / len(pr)


def recall_pooled(C, keys, vals, n, n_probe, pool, rng):
    """O(pool*dim) per probe — INDEPENDENT of n. Target + (pool-1) distractors drawn from the store."""
    pr = list(range(0, n, max(1, n // n_probe)))
    hits = 0
    for p in pr:
        cands = [p]
        while len(cands) < min(pool, n):
            j = rng.randrange(n)
            if j != p:
                cands.append(j)
        best = max(cands, key=lambda j: score(C, keys[p], vals[j]))
        hits += (best == p)
    return hits / len(pr)


def carriers(n, dim):
    k = [bytes(hdc.klein4_expand(dim, 10_000 + i)) for i in range(n)]
    v = [bytes(hdc.klein4_expand(dim, 20_000 + i)) for i in range(n)]
    b = [bytes(x ^ y for x, y in zip(a, c)) for a, c in zip(k, v)]
    return k, v, b


def ladder_for(dim):
    centre = max(48, int(0.25 * dim))
    return sorted({max(16, int(centre * f)) for f in (0.35, 0.5, 0.7, 0.9, 1.15, 1.45, 1.9, 2.5, 3.2)})


def crossing(ladder, rs, t):
    for i in range(len(ladder) - 1):
        r0, r1 = rs[i], rs[i + 1]
        if r0 >= t >= r1 and r0 != r1:
            return ladder[i] + (r0 - t) / (r0 - r1) * (ladder[i + 1] - ladder[i])
    return None


def fit(pts):
    xs = [math.log(d) for d, _ in pts]
    ys = [math.log(n) for _, n in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    b = my - a * mx
    res = max(cascade.magnitude(y - (a * x + b)) for x, y in zip(xs, ys))
    return a, res


def bootstrap_exp(pts, rng, reps=200):
    if len(pts) < 3:
        return None, None
    out = []
    for _ in range(reps):
        samp = [pts[rng.randrange(len(pts))] for _ in pts]
        if len({d for d, _ in samp}) < 2:
            continue
        try:
            out.append(fit(samp)[0])
        except ZeroDivisionError:
            continue
    if len(out) < 20:
        return None, None
    out.sort()
    return out[int(0.05 * len(out))], out[int(0.95 * len(out))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", type=int, default=256)
    ap.add_argument("--probes", type=int, default=50)
    args = ap.parse_args()
    rng = random.Random(1080)

    import srmech
    log("=== POOLED (srmech %s) — pool=%d, probes=%d ===" % (srmech.__version__, args.pool, args.probes))

    # ---------------- PART A: does the pool preserve the EXPONENT? ----------------
    log("")
    log("=== PART A — VALIDATE: does the pooled read preserve the exponent? ===")
    log("  pooled recall is an EASIER task, so N_crit shifts. The claim under test is ONLY that the")
    log("  SCALING is preserved. If the exponents disagree, pooling is unusable and part B is void.")
    pts_full, pts_pool = [], []
    log("")
    log("  %-8s %-14s %-14s %-10s" % ("dim", "N_crit full", "N_crit pooled", "secs"))
    for dim in (512, 1024, 2048):
        lad = ladder_for(dim)
        k, v, b = carriers(lad[-1], dim)
        t = time.time()
        rf, rp = [], []
        for n in lad:
            C = build(b[:n], dim)
            rf.append(recall_full(C, k, v, n, args.probes))
            rp.append(recall_pooled(C, k, v, n, args.probes, args.pool, rng))
        cf, cp = crossing(lad, rf, 0.5), crossing(lad, rp, 0.5)
        if cf:
            pts_full.append((dim, cf))
        if cp:
            pts_pool.append((dim, cp))
        log("  %-8d %-14s %-14s %-10.0f" % (dim, "%.0f" % cf if cf else " --",
                                            "%.0f" % cp if cp else " --", time.time() - t))
    if len(pts_full) >= 3 and len(pts_pool) >= 3:
        af, rfz = fit(pts_full)
        apz, rpz = fit(pts_pool)
        d = cascade.magnitude(af - apz)
        log("")
        log("  exponent FULL   = %.3f (resid %.4f)" % (af, rfz))
        log("  exponent POOLED = %.3f (resid %.4f)" % (apz, rpz))
        log("  => %s (|delta| %.3f)" %
            ("POOLING PRESERVES THE EXPONENT — usable" if d < 0.10 else
             "POOLING CHANGES THE EXPONENT — NOT a valid substitute", d))
        if d >= 0.10:
            log("  STOPPING: part B would inherit an invalid method.")
            return 0
    else:
        log("  insufficient crossings to validate — STOPPING.")
        return 0

    # ---------------- PART B: the exponent SPECTRUM ----------------
    log("")
    log("=== PART B — THE EXPONENT SPECTRUM (9 thresholds, bootstrap CIs) ===")
    DIMS = [512, 1024, 2048, 4096, 8192, 16384]
    THRESH = [0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15, 0.10]
    curves = {}
    for dim in DIMS:
        lad = ladder_for(dim)
        k, v, b = carriers(lad[-1], dim)
        t = time.time()
        rs = []
        for n in lad:
            C = build(b[:n], dim)
            rs.append(recall_pooled(C, k, v, n, args.probes, args.pool, rng))
        curves[dim] = (lad, rs)
        log("  dim=%-6d r %s  (%.0fs)" % (dim, " ".join("%4.2f" % x for x in rs), time.time() - t))

    log("")
    log("  %-8s %-10s %-18s %-8s" % ("thresh", "exponent", "90% CI", "n_dims"))
    spec = []
    for t in THRESH:
        pts = [(d, crossing(*curves[d], t)) for d in DIMS]
        pts = [(d, n) for d, n in pts if n]
        if len(pts) < 3:
            log("  %-8.2f (too few crossings)" % t)
            continue
        a, _ = fit(pts)
        lo, hi = bootstrap_exp(pts, rng)
        spec.append((t, a, lo, hi))
        log("  %-8.2f %-10.3f %-18s %-8d" %
            (t, a, ("[%.3f, %.3f]" % (lo, hi)) if lo else "  --", len(pts)))

    if len(spec) >= 4:
        exps = [a for _, a, _, _ in spec]
        los = [lo for _, _, lo, _ in spec if lo]
        his = [hi for _, _, hi, _ in spec if hi]
        common = (max(los) <= min(his)) if los and his else None
        log("")
        log("  exponent range: %.3f .. %.3f  (spread %.3f)" % (min(exps), max(exps), max(exps) - min(exps)))
        log("  do all 90%% CIs share a common value? %s" % ("YES" if common else "NO"))
        log("")
        if common:
            log("  => ONE EXPONENT. The spectrum reading is DEAD for this object; the monotone")
            log("     ordering at 3 thresholds was scatter.")
        else:
            log("  => THE EXPONENT IS A FUNCTION OF THRESHOLD — no single value fits all readings.")
            log("     That is the measurable form of 'a projection, not a constant'.")
            log("     spectrum extent %.3f..%.3f ; FLOOR = %.3f" % (min(exps), max(exps), min(exps)))
            log("     MFO CAVEAT: mapping this onto 1D..11D with a UV floor ~2D needs a DEFINED")
            log("     exponent->dimension map. None exists yet. Without it the correspondence")
            log("     would be numerology, so it is NOT claimed here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
