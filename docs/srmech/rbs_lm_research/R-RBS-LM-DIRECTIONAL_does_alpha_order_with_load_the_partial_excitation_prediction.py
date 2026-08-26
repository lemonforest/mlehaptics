r"""R-RBS-LM-DIRECTIONAL — does the capacity exponent ORDER with load, as partial-excitation predicts?

User (2026-07-20): *"it's quite possible that MAX D doesn't always fully excite 7D_gauge, so it's not that dims
are excited or not excited, they are asymptotically all excited such that apparent max D isn't always 11D ...
only as much as a D that needs excited gets excited."*

WHY THIS REPLACES THE QUESTION I WAS ASKING. I had been hunting a VALUE (is alpha 11/14? 4/5?). That assumes a
FIXED INTEGER effective dimension. If excitation is partial and load-driven, alpha has no reason to be
rational -- it sits wherever the load put it -- and hunting fractions inside a +/-0.086 window is numerology
with a framework costume (the window admits 11/14, 4/5, 7/9, ... alike).

The frame instead makes a DIRECTIONAL prediction: read the recall curve at a different threshold and you are
reading a different LOAD, hence a different excitation level, hence a different alpha -- and the ordering
should be MONOTONIC in threshold. Direction is far cheaper to test than value:
    3 thresholds all ordered  -> p = 1/3!  = 1/6          (what F1268 had: suggestive, nothing more)
    9 thresholds all ordered  -> p = 1/9!  = 1/362,880    (decisive)

METHOD, and the reason this costs NOTHING new: F1268 already measured full recall curves at n=50 probes over
5 dims. Extracting 9+ thresholds from THOSE SAME CURVES needs no new compute, and -- crucially -- every alpha
is read from IDENTICAL data, so any ordering is a property of the object and not of separate sampling runs.
The curves are transcribed here verbatim from that run's committed output.

WHY NOT THE POOLED READ: it pins the distractor count (255 regardless of N), which REMOVES the load-variation
this test is about. That is also why it fitted a near-perfect power law (resid 0.0001) while the full read
carries 0.0184 -- fixed-excitation vs varying-excitation. Correct to use the FULL curves here.

FALSIFIER: if the alphas are NOT monotone in threshold, the partial-excitation prediction fails on this object.
A partial ordering is reported honestly as partial, with its exact p-value, not rounded up to a trend.

srmech 0.9.0rc288. Class-K cascade.magnitude, never the builtin. No numpy.
Composes F1268 (whose curves these ARE), F1267, F1266, F1265, F1263, F1063 (the fractal-tower reading),
#243/F1070, #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-DIRECTIONAL_*.py
"""
import math
import sys
from itertools import permutations

from srmech.amsc import cascade

# --- F1268's measured full-read curves, n=50 probes/point (sd 0.071), transcribed verbatim -------------
CURVES = {
    512:  ([44, 64, 89, 115, 147, 185, 243, 320],
           [1.00, 0.98, 0.96, 0.84, 0.69, 0.58, 0.38, 0.26]),
    1024: ([89, 128, 179, 230, 294, 371, 486, 640],
           [1.00, 0.98, 0.88, 0.86, 0.59, 0.51, 0.26, 0.24]),
    2048: ([179, 256, 358, 460, 588, 742, 972, 1280],
           [1.00, 1.00, 0.87, 0.69, 0.57, 0.36, 0.27, 0.19]),
    4096: ([358, 512, 716, 921, 1177, 1484, 1945, 2560],
           [1.00, 0.92, 0.92, 0.62, 0.52, 0.40, 0.13, 0.04]),
    8192: ([716, 1024, 1433, 1843, 2355, 2969, 3891, 5120],
           [0.98, 0.92, 0.81, 0.50, 0.43, 0.18, 0.12, 0.08]),
}
DIMS = sorted(CURVES)


def crossing(ladder, rs, t):
    """First downward crossing of t, linearly interpolated."""
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


def main():
    import srmech
    print("=== DIRECTIONAL — does alpha order with threshold? (srmech %s) ===" % srmech.__version__)
    print("  data: F1268's n=50 full-read curves, 5 dims. NO new compute; identical data per threshold.")
    print()

    # widest band crossed by EVERY dim
    lo = max(min(rs) for _, rs in CURVES.values())
    hi = min(max(rs) for _, rs in CURVES.values())
    print("  common recall band across all dims: %.2f .. %.2f" % (lo, hi))
    THRESH = [round(x, 3) for x in
              [hi - (hi - lo) * i / 10.0 for i in range(1, 10)]]
    print("  thresholds (9, inside the band): %s" % " ".join("%.2f" % t for t in THRESH))
    print()

    print("  %-8s %-10s %-10s %-8s %s" % ("thresh", "alpha", "max resid", "n_dims", "N_crit per dim"))
    rows = []
    for t in THRESH:
        pts = [(d, crossing(*CURVES[d], t)) for d in DIMS]
        pts = [(d, n) for d, n in pts if n]
        if len(pts) < 4:
            print("  %-8.2f (only %d crossings — skipped)" % (t, len(pts)))
            continue
        a, res = fit(pts)
        rows.append((t, a, res, len(pts)))
        print("  %-8.2f %-10.4f %-10.4f %-8d %s"
              % (t, a, res, len(pts), " ".join("%.0f" % n for _, n in pts)))

    if len(rows) < 4:
        print("\n  too few usable thresholds — the test cannot run on this data.")
        return 0

    # ---- the directional test ----
    print()
    print("  --- THE DIRECTIONAL TEST ---")
    alphas = [a for _, a, _, _ in rows]
    k = len(alphas)
    desc = all(alphas[i] >= alphas[i + 1] for i in range(k - 1))
    asc = all(alphas[i] <= alphas[i + 1] for i in range(k - 1))
    # count adjacent pairs in the predicted (descending-with-threshold) direction
    agree = sum(1 for i in range(k - 1) if alphas[i] >= alphas[i + 1])
    print("  thresholds run HIGH -> LOW; partial-excitation predicts alpha DECREASES with them.")
    print("  alphas in threshold order: %s" % " ".join("%.3f" % a for a in alphas))
    print("  adjacent pairs in predicted direction: %d / %d" % (agree, k - 1))
    print("  fully monotone? %s" % ("YES (descending)" if desc else ("YES (ascending — WRONG direction)" if asc else "NO")))

    # exact p for a full ordering under the null of random order
    pfull = 1.0 / math.factorial(k)
    # exact p for >= `agree` adjacent-pairs-correct, by enumeration over permutations (k<=9 is fine)
    if k <= 9:
        base = sorted(range(k))
        cnt = 0
        tot = 0
        for perm in permutations(base):
            tot += 1
            ag = sum(1 for i in range(k - 1) if perm[i] >= perm[i + 1])
            if ag >= agree:
                cnt += 1
        pobs = cnt / tot
    else:
        pobs = None
    print()
    print("  p(all %d ordered by chance)          = %.3g" % (k, pfull))
    if pobs is not None:
        print("  p(>= %d/%d adjacent pairs by chance) = %.4g   <- the honest test statistic" % (agree, k - 1, pobs))
    print()
    spread = max(alphas) - min(alphas)
    maxres = max(r for _, _, r, _ in rows)
    print("  alpha spread %.3f   vs max fit residual %.3f" % (spread, maxres))
    if pobs is not None and pobs < 0.01 and spread > maxres:
        print("  => DIRECTIONAL PREDICTION SUPPORTED: alpha moves with load, ordered, beyond chance.")
    elif pobs is not None and pobs < 0.05:
        print("  => SUGGESTIVE but not decisive (p<0.05, not p<0.01). More thresholds or tighter curves.")
    else:
        print("  => NOT SUPPORTED on this data. The ordering is consistent with chance.")
    print()
    print("  NOTE: alphas at nearby thresholds are NOT independent (one curve, overlapping")
    print("  interpolation intervals), so the permutation p is OPTIMISTIC. Treat it as an")
    print("  upper bound on significance, not a clean frequentist claim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
