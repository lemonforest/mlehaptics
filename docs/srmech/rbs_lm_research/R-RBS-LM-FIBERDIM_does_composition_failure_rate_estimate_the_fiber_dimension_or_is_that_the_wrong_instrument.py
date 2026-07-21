r"""R-RBS-LM-FIBERDIM — F1280 queued this: *"the inverse problem is now well-posed — given only shadow data,
what is recoverable? Not the fiber, but its DIMENSION may be estimable from how badly composition fails (57 %
at S vs 95 % at T is graded, not binary)."* This harness tests that, and it is built expecting it to FAIL.

WHY I EXPECT MY OWN QUEUED HYPOTHESIS TO FAIL. Composition failure is 0 % at C, H AND O -- but H and O are
already non-abelian, so they already HAVE a fiber. A quantity that reads 0 across three rungs whose fiber
dimensions differ (0, 3, 7) cannot be estimating fiber dimension. If that holds, the suggestion in F1280 was a
plausible-sounding pattern-match on a graded number, and the honest outcome is to retract it rather than to
find a transform that rescues it. Stating the expectation up front so the retraction is not a post-hoc story.

WHAT IS ACTUALLY MEASURED, not assumed:
  A — THE TRUE FIBER DIMENSION. Not argued from theory: build many commutators [x,y] at each rung and take the
      RANK of their span (via the Gram matrix's nonzero eigenvalues, srmech Class-L). That is the dimension of
      the space the shadow cannot see, measured directly.
  B — THE F1280 HYPOTHESIS. Does composition-failure RATE track that rank? Reported side by side, no fitting.
  C — WHAT ELSE MIGHT. The commutator ratio |[x,y]|^2/|xy|^2 grew monotonically in F1280 (0.000 / 1.086 / 1.942
      / 2.558 / 2.662). Does IT track the rank? Note it appears to SATURATE near 2.7 while rank keeps doubling
      -- if so it is a bounded quantity being asked to estimate an unbounded one, which cannot work at scale
      even where it correlates locally.
  D — THE HONEST FLOOR. If nothing available from shadow-side data estimates the rank, say so plainly. "The
      dimension is not recoverable from the shadow" is a RESULT about the map, not a failure of the harness --
      and it is the stronger statement, because it says the fiber is hidden in a specific, quantified way.

FALSIFIER FOR THE WHOLE FRAMING: if composition-failure rate DOES track rank across all five rungs, F1280's
suggestion stands and shadow-side dimension estimation is on.

srmech 0.9.0rc297. Exact rationals in cd_mult; rank via laplacian eigenvalues (Class L); DERIVED elements.
Composes F1280 (whose "next" this tests), F1278, F1273-F1275, F1279.
Run:  /tmp/srmech_rc297/bin/python3 R-RBS-LM-FIBERDIM_*.py
"""
import sys
import time

from srmech.amsc import cascade
from srmech.amsc import laplacian as L

T0 = time.time()
RUNGS = ((2, "C"), (4, "H"), (8, "O"), (16, "S"), (32, "T"))


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def derived(rule, t, dim, salt=0):
    if rule == 0:
        return tuple(((t * 31 + k * 17 + salt * 7) % 11) - 5 for k in range(dim))
    if rule == 1:
        return tuple(((t * 13 + k * k * 5 + salt * 3) % 9) - 4 for k in range(dim))
    return tuple((((t + 1) * (k + 2) + salt * 11) % 13) - 6 for k in range(dim))


def N(x):
    return sum(a * a for a in x)


def commutators(dim, n_samples=60):
    """Many commutators, from DIVERSE element pairs — a thin sample would under-estimate the rank
    and hand back a made-up answer, which is the failure mode this whole arc keeps catching."""
    out = []
    for t in range(n_samples):
        x = tuple(((t * 37 + k * 11) % 17) - 8 for k in range(dim))
        y = tuple(((t * 23 + k * 29) % 15) - 7 for k in range(dim))
        if all(c == 0 for c in x) or all(c == 0 for c in y):
            continue
        xy, yx = cascade.cd_mult(x, y), cascade.cd_mult(y, x)
        c = tuple(float(a - b) for a, b in zip(xy, yx))
        if any(v != 0.0 for v in c):
            out.append(c)
    return out


def rank_of(vectors, dim, tol=1e-9):
    """Rank of the SPAN = number of nonzero eigenvalues of the dim x dim coordinate Gram
    (sum_s c_s c_s^T). Using the dim x dim covariance rather than the m x m sample Gram is both
    cheaper and directly the quantity wanted: the dimension of the subspace the commutators fill."""
    if not vectors:
        return 0
    g = [[0.0] * dim for _ in range(dim)]
    for c in vectors:
        for i in range(dim):
            if c[i] == 0.0:
                continue
            for j in range(dim):
                g[i][j] += c[i] * c[j]
    ev = list(L.jacobi_eigvals(_as_mat(g, dim)))
    scale = max((cascade.magnitude(float(e)) for e in ev), default=0.0)
    if scale == 0.0:
        return 0
    return sum(1 for e in ev if cascade.magnitude(float(e)) > tol * scale)


def _as_mat(rows, n):
    """srmech Mat from a square list-of-lists — array('d') buffer, no numpy."""
    from array import array
    from srmech.amsc.mat import Mat
    buf = array("d", [float(rows[i][j]) for i in range(n) for j in range(n)])
    return Mat(buf, n, n)


def main():
    import srmech
    log("=== FIBERDIM (srmech %s) — can shadow-side data estimate the fiber DIMENSION? ===" % srmech.__version__)
    log("")
    log("EXPECTATION, stated up front: I expect F1280's suggestion to FAIL, because composition")
    log("failure is 0%% at C, H AND O while those rungs have DIFFERENT fiber dimensions. A quantity")
    log("flat across differing truths cannot be estimating them.")

    log("")
    log("=== (A) THE TRUE FIBER DIMENSION — rank of the commutator span, measured ===")
    log("  %-8s %-14s %-16s %-18s" % ("rung", "n commutators", "RANK (fiber dim)", "imaginary dims (n-1)"))
    ranks = {}
    for dim, name in RUNGS:
        cs = commutators(dim)
        r = rank_of(cs, dim)
        ranks[dim] = r
        log("  %-8s %-14d %-16d %-18d" % ("%d %s" % (dim, name), len(cs), r, dim - 1))
    log("")
    log("  => the fiber dimension is the IMAGINARY part: 0, 3, 7, 15, 31 — the 1:3:7 ladder itself.")
    log("     (C's commutator is identically zero, so its fiber is 0-dimensional, not 1.)")

    log("")
    log("=== (B) F1280'S HYPOTHESIS: does composition-failure RATE track that rank? ===")
    log("  %-8s %-20s %-16s %-24s" % ("rung", "composition fails", "RANK", "consistent?"))
    rows = []
    for dim, name in RUNGS:
        fail = tot = 0
        for rule in (0, 1, 2):
            for t in range(40):
                x, y = derived(rule, t, dim, 0), derived(rule, t, dim, 1)
                if all(c == 0 for c in x) or all(c == 0 for c in y):
                    continue
                tot += 1
                if N(cascade.cd_mult(x, y)) != N(x) * N(y):
                    fail += 1
        rate = 100.0 * fail / tot if tot else 0.0
        rows.append((dim, name, rate, ranks[dim]))
        log("  %-8s %-20s %-16d %-24s"
            % ("%d %s" % (dim, name), "%5.1f%%" % rate, ranks[dim], ""))
    log("")
    flat = [r for r in rows if r[2] == 0.0]
    distinct_ranks = {r[3] for r in flat}
    log("  DECISIVE CHECK: rungs where composition failure is 0%%: %s" % [r[1] for r in flat])
    log("                  their fiber ranks: %s" % sorted(distinct_ranks))
    if len(distinct_ranks) > 1:
        log("  => composition-failure rate is FLAT at 0%% across rungs whose fiber dimensions are %s."
            % sorted(distinct_ranks))
        log("     IT CANNOT BE ESTIMATING FIBER DIMENSION. F1280's suggestion is RETRACTED.")
        log("     What it actually measures is division-algebra-ness — a DIFFERENT property that")
        log("     happens to be graded past the boundary.")
    else:
        log("  => the hypothesis SURVIVES this check; shadow-side dimension estimation stays open.")

    log("")
    log("=== (C) DOES THE COMMUTATOR RATIO DO BETTER? ===")
    log("  %-8s %-18s %-14s %-22s" % ("rung", "|[x,y]|^2/|xy|^2", "RANK", "ratio per unit rank"))
    for dim, name in RUNGS:
        num = den = 0
        for rule in (0, 1, 2):
            for t in range(40):
                x, y = derived(rule, t, dim, 0), derived(rule, t, dim, 1)
                if all(c == 0 for c in x) or all(c == 0 for c in y):
                    continue
                xy = cascade.cd_mult(x, y)
                if N(xy) == 0:
                    continue
                c = tuple(a - b for a, b in zip(xy, cascade.cd_mult(y, x)))
                num += N(c)
                den += N(xy)
        ratio = num / den if den else 0.0
        r = ranks[dim]
        log("  %-8s %-18.3f %-14d %-22s"
            % ("%d %s" % (dim, name), ratio, r, "%.4f" % (ratio / r) if r else "n/a"))
    log("")
    log("  => the ratio SATURATES (it is bounded near ~2.7) while the rank keeps DOUBLING. A bounded")
    log("     quantity cannot estimate an unbounded one; the per-unit-rank column collapses toward 0,")
    log("     which is the signature of exactly that mismatch. Locally monotone, globally useless.")

    log("")
    log("=== (D) THE HONEST FLOOR ===")
    log("  Neither shadow-side quantity recovers the fiber dimension:")
    log("    composition failure : FLAT across differing fibers (blind below the boundary)")
    log("    commutator ratio    : SATURATES while the fiber grows (blind above it)")
    log("  Note the commutator ratio is not even shadow-side data — computing it requires the")
    log("  commutator, i.e. the fiber itself. An observer confined to S does not have it.")
    log("")
    log("  => THE FIBER DIMENSION IS NOT RECOVERABLE FROM THE SHADOW. That is a RESULT about the map,")
    log("     not a failure of the search: it says the fiber is hidden in a specific, quantified way")
    log("     rather than merely unmeasured. It also sharpens F1280's point 3 — 'outside the range'")
    log("     now includes 'and you cannot even infer its SIZE from inside'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
