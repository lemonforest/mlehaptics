r"""R-RBS-LM-COUNTHORIZON (F1263 NEXT 1-4) — how far does the count structure actually go, what does it cost,
and which lever attacks the residual COLLISION term?

User (2026-07-20): *"let's do next 4"* — the four follow-ups F1263 queued:
  (1) push N to 1e4-1e5 to find the count structure's OWN horizon
  (2) measure count-matrix SPARSITY — is the 4x storage claim pessimistic?
  (3) an INDEXED/SPARSE read to kill the O(N*dim) probe cost
  (4) re-open F1259's designed-family question against the now-dominant COLLISION term

ORDER MATTERS: (3) is a PREREQUISITE for (1). The naive read scores every candidate against every coordinate,
O(N*dim) per probe; at N=1e5, dim=4096 that is ~4e8 operations per probe in pure Python. So the sparse read is
built and VALIDATED against the full read first, then used to push N.

THE SPARSE READ, and why it is discipline-correct: keep the FULL count store, but READ only the coordinates
whose vote is DECISIVE. margin[i] = (top count - second count) at coordinate i. High margin == the
superposition is unambiguous there; near-tied coordinates are noise. Reading the top-M by margin is exactly
[[feedback_sparse_complete_never_top_k_truncation_at_storage]] applied the RIGHT way round: top-K as a READ,
never as a storage cut. The store stays sparse-and-complete; only the probe is cheap.

(4) THE COLLISION LEVER. F1259 measured two procedural families LOSING to the RNG on worst-case sector
agreement (Weyl 0.400, Walsh 0.500 vs random 0.267). So "design a better family" is not currently available.
The cheaper question is whether the collision term responds to DIMENSION instead — if recall at fixed N rises
with dim, then dim is the working lever and the family question is secondary. Measured here rather than argued.

srmech 0.9.0rc288. Integer accumulators; no numpy.
Composes F1263 (the count structure), F1259 (the sidelobe/family question), F1216, F1205/#263.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-COUNTHORIZON_*.py [--max-n 8000]
"""
import argparse
import sys
import time

from srmech.amsc import hdc

T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


# ---------------------------------------------------------------- the store (Class-L side)
def build_counts(bound, dim):
    C = [[0] * 4 for _ in range(dim)]
    for v in bound:
        for i, s in enumerate(v):
            C[i][s] += 1
    return C


def margins(C):
    """Per-coordinate decisiveness: top vote minus runner-up. High == unambiguous."""
    out = []
    for row in C:
        a = sorted(row, reverse=True)
        out.append(a[0] - a[1])
    return out


# ---------------------------------------------------------------- the reads
def read_full(C, key, cands):
    best, bi = None, -1
    for j, cand in enumerate(cands):
        sc = 0
        for i in range(len(C)):
            sc += C[i][key[i] ^ cand[i]]
        if best is None or sc > best:
            best, bi = sc, j
    return bi


def read_sparse(C, key, cands, idx):
    """Score only the DECISIVE coordinates (idx). O(N*len(idx)) instead of O(N*dim)."""
    best, bi = None, -1
    for j, cand in enumerate(cands):
        sc = 0
        for i in idx:
            sc += C[i][key[i] ^ cand[i]]
        if best is None or sc > best:
            best, bi = sc, j
    return bi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dim", type=int, default=4096)
    ap.add_argument("--max-n", type=int, default=8000)
    args = ap.parse_args()
    dim = args.dim

    import srmech
    log("=== COUNTHORIZON (srmech %s) ===" % srmech.__version__)
    log("building carriers up to N=%d, dim=%d ..." % (args.max_n, dim))
    keys = [bytes(hdc.klein4_expand(dim, 10_000 + i)) for i in range(args.max_n)]
    vals = [bytes(hdc.klein4_expand(dim, 20_000 + i)) for i in range(args.max_n)]
    bound = [bytes(a ^ b for a, b in zip(k, v)) for k, v in zip(keys, vals)]
    log("carriers built.")

    # ---------------- (2) SPARSITY ----------------
    log("")
    log("--- (2) SPARSITY of the count matrix — is 4x storage pessimistic? ---")
    for N in (256, 2000, args.max_n):
        C = build_counts(bound[:N], dim)
        occupied = sum(sum(1 for c in row if c > 0) for row in C)
        log("  N=%-6d occupied cells %d / %d  (%.1f%%)  -> all 4 sectors fill once N >> 4"
            % (N, occupied, dim * 4, 100.0 * occupied / (dim * 4)))
    log("  => the matrix is DENSE in cells; the compressible axis is the VALUE range, not occupancy.")
    mx = max(max(r) for r in build_counts(bound[:args.max_n], dim))
    import math
    log("  max cell value at N=%d is %d -> %d bits/cell suffices (vs 32/64 for a plain int)"
        % (args.max_n, mx, max(1, math.ceil(math.log2(mx + 1)))))
    log("  so storage = dim * 4 * ceil(log2(N)) bits, NOT dim*4*64. At N=%d that is %.1f KB vs %.1f KB naive."
        % (args.max_n, dim * 4 * max(1, math.ceil(math.log2(mx + 1))) / 8192.0, dim * 4 * 8 / 1024.0))

    # ---------------- (3) SPARSE READ, validated ----------------
    log("")
    log("--- (3) INDEXED READ — validate the sparse read against the full read ---")
    Nv = 512
    C = build_counts(bound[:Nv], dim)
    mg = margins(C)
    order = sorted(range(dim), key=lambda i: -mg[i])
    probes = list(range(0, Nv, max(1, Nv // 20)))
    t = time.time()
    full = [read_full(C, keys[p], vals[:Nv]) for p in probes]
    t_full = time.time() - t
    fr = sum(1 for p, g in zip(probes, full) if p == g) / len(probes)
    log("  full read   : recall %.3f   %.2f s for %d probes" % (fr, t_full, len(probes)))
    log("  %-8s %-10s %-10s %-10s" % ("top-M", "recall", "time(s)", "agree(full)"))
    best_m = dim
    for M in (dim, dim // 2, dim // 4, dim // 8, dim // 16, dim // 32):
        idx = order[:M]
        t = time.time()
        got = [read_sparse(C, keys[p], vals[:Nv], idx) for p in probes]
        dt = time.time() - t
        r = sum(1 for p, g in zip(probes, got) if p == g) / len(probes)
        agree = sum(1 for a, b in zip(full, got) if a == b) / len(full)
        log("  %-8d %-10.3f %-10.2f %-10.3f" % (M, r, dt, agree))
        if r >= fr - 1e-9:
            best_m = M
    log("  => smallest M holding full-read recall: %d (%.1f%% of coordinates)" % (best_m, 100.0 * best_m / dim))

    # ---------------- (1) THE TRUE HORIZON ----------------
    log("")
    log("--- (1) THE COUNT STRUCTURE'S OWN HORIZON (sparse read, M=%d) ---" % best_m)
    log("  %-8s %-14s %-14s" % ("N", "bundle", "counts"))
    for N in (512, 1000, 2000, 4000, args.max_n):
        if N > args.max_n:
            continue
        C = build_counts(bound[:N], dim)
        idx = sorted(range(dim), key=lambda i: -margins(C)[i])[:best_m]
        probes = list(range(0, N, max(1, N // 20)))
        B = hdc.klein4_bundle([hdc.klein4_bind(hdc.klein4_expand(dim, 10_000 + i),
                                               hdc.klein4_expand(dim, 20_000 + i)) for i in range(N)])
        hb = 0
        for p in probes:
            probe = hdc.klein4_bind(B, hdc.klein4_expand(dim, 10_000 + p))
            best = max(range(N), key=lambda j: hdc.klein4_similarity(probe, hdc.klein4_expand(dim, 20_000 + j)))
            hb += (best == p)
        hc = sum(1 for p in probes if read_sparse(C, keys[p], vals[:N], idx) == p)
        log("  %-8d %-14.3f %-14.3f" % (N, hb / len(probes), hc / len(probes)))

    # ---------------- (4) THE COLLISION LEVER ----------------
    log("")
    log("--- (4) does the residual COLLISION term respond to DIMENSION? (fixed N=2000) ---")
    log("  F1259 showed designed families LOSE on worst-case sector agreement, so test the other lever.")
    log("  %-8s %-14s" % ("dim", "counts recall"))
    N2 = 2000
    for d2 in (1024, 2048, 4096, 8192):
        k2 = [bytes(hdc.klein4_expand(d2, 10_000 + i)) for i in range(N2)]
        v2 = [bytes(hdc.klein4_expand(d2, 20_000 + i)) for i in range(N2)]
        b2 = [bytes(a ^ b for a, b in zip(k, v)) for k, v in zip(k2, v2)]
        C2 = build_counts(b2, d2)
        M2 = max(64, int(best_m * d2 / dim))
        idx2 = sorted(range(d2), key=lambda i: -margins(C2)[i])[:M2]
        pr = list(range(0, N2, max(1, N2 // 20)))
        r = sum(1 for p in pr if read_sparse(C2, k2[p], v2, idx2) == p) / len(pr)
        log("  %-8d %-14.3f" % (d2, r))
    log("")
    log("  if recall rises with dim at fixed N, DIMENSION is the working lever and the")
    log("  designed-family question (F1259) is secondary rather than blocking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
