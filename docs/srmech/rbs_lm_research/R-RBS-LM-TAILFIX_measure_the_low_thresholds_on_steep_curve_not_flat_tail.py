r"""R-RBS-LM-TAILFIX — re-measure the capacity curves with a DENSER, LONGER ladder and MORE probes, so the low
thresholds are read where the curve still has slope instead of in the flat tail.

User (2026-07-20): chose option (2) — extend/densify rather than trim the band post-hoc.

WHY NOT OPTION (1). Restricting to the steep band (0.91..0.55, where the ordering was a clean 6/6 monotone)
would be choosing the window AFTER seeing the answer — the exact grid-fitting failure that produced five
artifacts in this chain (F1265 dyadic grid, F1266 ceiling-as-plateau + 2-point trend, F1267 coarse ladder +
chosen divisors, F1268 under-powered probes). Trimming is only legitimate against a criterion fixed in
advance; measuring better needs no such defence.

WHAT ACTUALLY LIMITS THE TAIL, stated so the fix is aimed correctly:
    crossing error  ~=  recall_noise / |local slope|
Density alone does NOT help — it improves interpolation but leaves the noise term untouched. In the tail the
slope is small, so BOTH terms need work:
    * MORE PROBES        n=50 -> 80   (sd 0.071 -> 0.056)          attacks the numerator
    * DENSER TAIL LADDER 8 -> 13 pts, extra density past 1.4x      attacks the denominator (finer bracketing)
    * LONGER LADDER      max 2.5x -> 4.3x of centre                so low thresholds are BRACKETED, not
                                                                    extrapolated off the last point
HONEST BOUND: the tail is intrinsically the flat part of a sigmoid. This makes the low thresholds *better*
measured, not *well* measured. If the turn-up at 0.40/0.33 survives this, it is structure; if it flattens into
the monotone run, it was tail noise. Either outcome is reportable.

THE OPEN QUESTION IT DECIDES. F1269-pending measured alpha across 9 thresholds: 6/8 adjacent pairs in the
predicted direction (p=0.042), monotone over the top six (0.896 -> 0.812) then TURNING UP (0.812 -> 0.820 ->
0.853). A monotone partial-excitation reading does not predict a U-shape. So either something re-enters at low
threshold, or the tail alphas are noise. This run separates those.

srmech 0.9.0rc288. Class-K cascade.magnitude, never the builtin. Integer accumulators; no numpy.
Composes F1269-pending (the directional test), F1268 (the curves being re-measured), F1267, F1263,
F1063 (fractal tower), #243/F1070, #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-TAILFIX_*.py
"""
import math
import sys
import time
from array import array

from srmech.amsc import cascade, hdc

T0 = time.time()
PROBES = 80                                   # sd 0.056 (was 50 -> 0.071)
FACTORS = (0.35, 0.5, 0.7, 0.9, 1.15, 1.4, 1.65, 1.95, 2.3, 2.7, 3.2, 3.7, 4.3)   # 13 pts, dense past 1.4


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


def main():
    import srmech
    log("=== TAILFIX (srmech %s) — probes=%d, %d-point ladder to %.1fx centre ==="
        % (srmech.__version__, PROBES, len(FACTORS), FACTORS[-1]))
    log("  crossing error ~= noise/slope; attacking BOTH (more probes, denser+longer tail).")
    DIMS = [512, 1024, 2048, 4096, 8192]
    out = {}
    for dim in DIMS:
        centre = max(48, int(0.25 * dim))
        ladder = sorted({max(16, int(centre * f)) for f in FACTORS})
        k = [bytes(hdc.klein4_expand(dim, 10000 + i)) for i in range(ladder[-1])]
        v = [bytes(hdc.klein4_expand(dim, 20000 + i)) for i in range(ladder[-1])]
        b = [bytes(x ^ y for x, y in zip(a, c)) for a, c in zip(k, v)]
        rs, t0 = [], time.time()
        for n in ladder:
            C = build(b[:n], dim)
            pr = list(range(0, n, max(1, n // PROBES)))
            rs.append(sum(1 for p in pr if read_full(C, k[p], v[:n]) == p) / len(pr))
        out[dim] = (ladder, rs)
        log("  dim=%-6d N %s" % (dim, " ".join("%5d" % x for x in ladder)))
        log("  %-11s r %s  (%.0fs)" % ("", " ".join("%5.2f" % x for x in rs), time.time() - t0))
        # local slope in the tail, so the honest bound is visible
        tail = [(rs[i] - rs[i + 1]) for i in range(len(rs) - 1)][-4:]
        log("  %-11s tail deltas %s  (flat tail => crossing error stays large there)"
            % ("", " ".join("%+.3f" % x for x in tail)))

    log("")
    log("  --- curves for the directional re-test (transcribe into R-RBS-LM-DIRECTIONAL) ---")
    for dim in DIMS:
        lad, rs = out[dim]
        log("    %-6d: (%s," % (dim, lad))
        log("             %s)," % [round(x, 3) for x in rs])
    return 0


if __name__ == "__main__":
    sys.exit(main())
