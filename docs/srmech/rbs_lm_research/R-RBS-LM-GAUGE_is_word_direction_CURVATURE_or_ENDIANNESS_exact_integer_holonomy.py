r"""R-RBS-LM-GAUGE (F1211/F1213 follow-up) — is a word's DIRECTION genuine CURVATURE, or merely ENDIANNESS?

User (2026-07-19): *"is that word direction curvature or endianness?"*

F1213 restored a direction channel to the ni-Vanuatu base: `word_to_kernel(w)` carries `edge_charge` =
w_fwd - w_bwd, and measured `cat` -> [-1,+1] vs `tac` -> [+1,-1], 11/11 "direction". But that pair differs by
a GLOBAL SIGN FLIP of the whole charge vector -- which is exactly what an endianness swap (reading the glyph
stream from the other end) does. So "distinguishes a word from its reverse" does NOT by itself establish
curvature.

THE DISTINCTION (discrete gauge theory, the srmech-native read):
  * a charge field theta_uv on a graph is PURE GAUGE (an EXACT form) iff there is a node potential phi with
    theta_uv = phi_v - phi_u. A global reading-frame/endianness convention is precisely such a phi.
  * CURVATURE is the part that survives every gauge: the HOLONOMY (net charge) around a closed CYCLE.
  * On an ACYCLIC graph (a tree) the cycle space is empty, so EVERY charge field is exact => zero curvature by
    TOPOLOGY. A word whose glyphs are all distinct is a PATH GRAPH -- a tree -- and its "direction" is the
    gradient of phi = glyph position. That is endianness, not curvature.
  * Curvature can only appear when the glyph-walk CLOSES ON ITSELF, i.e. a glyph REPEATS: `banana` walks
    a->n->a->n, and the cycle a->n->a carries holonomy +2+2 = +4, removable by no phi.

MEASURED HERE, EXACTLY (integers only -- no floats, no ALU absolute-value; Class-K `cascade.magnitude` where a magnitude is
needed): per word, build the directed glyph graph, take a BFS spanning tree, solve phi from the tree charges,
then test every NON-TREE edge: residual = charge_uv - (phi_v - phi_u). residual == 0 for all => the field is a
pure gradient => ENDIANNESS ONLY. Any residual != 0 IS the fundamental-cycle holonomy => genuine CURVATURE.

Cross-checked srmech-native against the magnetic Laplacian: lambda_min(L^(q)) == 0 iff the phase field is
gauge-equivalent to zero (frustration-free); lambda_min > 0 iff irremovable holonomy. Run at two different q to
avoid a holonomy that is accidentally = 0 mod 2pi at one q.

Reported over a REAL vocabulary (simplewiki tokens), by TYPE and by TOKEN frequency -- because if the
overwhelming majority of running text is acyclic-at-glyph-scale, then a byte/glyph re-base buys orientation,
not curvature, and the corpus-level directed object (F1209/F1210) remains the only place curvature lives.

srmech 0.9.0rc281. Composes F1211 (the metric-only base), F1213 (the direction fix), F1209/F1210 (curvature =
the responsion), F1080 (sandroing = Eulerian circuit -- a CLOSED walk, note), #231/PKG-3.
Run:  /tmp/srmech_rc272/venv/bin/python3 R-RBS-LM-GAUGE_*.py [--limit N]
"""
import argparse
import json
import sys
import time
from collections import deque
from pathlib import Path

from srmech.amsc import cascade, laplacian as L, text as T

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_gauge.report.json"
PROBES = ["cat", "tac", "act", "banana", "level", "deed", "stressed", "desserts",
          "listen", "silent", "abc", "cba", "mississippi", "aardvark", "the", "of"]
T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def glyph_graph(word):
    """word -> (nodes, undirected edge list, per-edge integer charge = fwd - bwd). The F1213 object."""
    gl = list(word)
    idx, order = {}, []
    for g in gl:
        if g not in idx:
            idx[g] = len(order)
            order.append(g)
    flow = {}                                   # (u,v) canonical u<v -> net directed flow u->v
    for a, b in zip(gl, gl[1:]):
        u, v = idx[a], idx[b]
        if u == v:
            continue                            # self-loop: no cycle-space content, carries no holonomy
        key = (u, v) if u < v else (v, u)
        flow[key] = flow.get(key, 0) + (1 if u < v else -1)
    edges = sorted(flow)
    return order, edges, [flow[e] for e in edges]


def gauge_decompose(n, edges, charges):
    """EXACT integer test: is the charge field a pure gradient (endianness) or does it carry holonomy?

    BFS spanning forest -> phi from tree edges -> every non-tree edge's residual IS its fundamental-cycle
    holonomy. Returns (betti1, n_holonomy_edges, max_holonomy, components).
    """
    adj = {i: [] for i in range(n)}
    for k, (u, v) in enumerate(edges):
        adj[u].append((v, k, +1))
        adj[v].append((u, k, -1))
    phi = {}
    tree = set()
    comps = 0
    for s in range(n):
        if s in phi:
            continue
        comps += 1
        phi[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v, k, sgn in adj[u]:
                if v not in phi:
                    # charge on edge k points low->high index; sgn orients it out of u
                    phi[v] = phi[u] + sgn * charges[k]
                    tree.add(k)
                    q.append(v)
    n_hol, max_hol = 0, 0
    for k, (u, v) in enumerate(edges):
        if k in tree:
            continue
        residual = charges[k] - (phi[v] - phi[u])       # the fundamental-cycle holonomy
        if residual != 0:
            n_hol += 1
            m = cascade.magnitude(residual)             # Class-K pin-slot magnitude (the cascade-honest form)
            if m > max_hol:
                max_hol = m
    betti1 = len(edges) - n + comps
    return betti1, n_hol, max_hol, comps


def spectral_check(word, qs=(0.1, 0.137)):
    """srmech-native cross-check: lambda_min(magnetic_laplacian) == 0 <=> pure gauge (frustration-free)."""
    order, edges, charges = glyph_graph(word)
    if not edges:
        return None
    out = []
    for q in qs:
        # per-edge charges CARRY the phase themselves (q is mutually exclusive), so scale them directly;
        # two different scalings guard against a holonomy that is accidentally = 0 mod 2pi at one of them
        H = L.magnetic_laplacian(len(order), edges, charges=[c * q for c in charges])
        # NOTE (§104): use hermitian_eigendecompose, NOT mat_eigvals — mat_eigvals is WRONG on
        # hub-dominated (star) matrices: it returns lambda_min = 0.268 for K1,3 whose true lambda_min is
        # exactly 0, and is blind to the phase entirely. jacobi_/symmetric_/hermitian_ are all correct.
        ev = sorted(float(v) for v in L.hermitian_eigendecompose(H)[0])
        out.append(ev[0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40000, help="documents to scan for the vocabulary")
    args = ap.parse_args()

    import srmech
    log("=== GAUGE — is word DIRECTION curvature or endianness? (srmech %s) ===" % srmech.__version__)

    # ---------- the probes (including F1213's own examples) ----------
    log("")
    log("--- PROBE WORDS: exact integer gauge decomposition ---")
    log("  %-14s %-4s %-4s %-7s %-9s %-8s %s" % ("word", "V", "E", "betti1", "holo_edges", "max_hol", "VERDICT"))
    probe_rows = []
    for w in PROBES:
        order, edges, charges = glyph_graph(w)
        b1, nh, mh, _ = gauge_decompose(len(order), edges, charges)
        verdict = "CURVATURE" if nh else ("endianness (acyclic)" if b1 == 0 else "endianness (cycles, zero holonomy)")
        log("  %-14s %-4d %-4d %-7d %-9d %-8d %s" % (w, len(order), len(edges), b1, nh, mh, verdict))
        probe_rows.append({"word": w, "V": len(order), "E": len(edges), "betti1": b1,
                           "holonomy_edges": nh, "max_holonomy": mh, "verdict": verdict})

    # ---------- srmech-native spectral confirmation on a contrasting pair ----------
    log("")
    log("--- SPECTRAL CROSS-CHECK (magnetic Laplacian lambda_min; 0 => pure gauge) ---")
    for w in ("cat", "tac", "banana", "mississippi"):
        lam = spectral_check(w)
        if lam:
            log("  %-14s lambda_min @q=0.100: %.3e   @q=0.137: %.3e" % (w, lam[0], lam[1]))

    # ---------- the real vocabulary, by TYPE and by TOKEN ----------
    log("")
    log("--- REAL VOCABULARY (simplewiki, %d docs) ---" % args.limit)
    freq = {}
    with open(ART) as f:
        for i, line in enumerate(f):
            if i >= args.limit:
                break
            for t in T.tokenize(json.loads(line).get("text", "")):
                freq[t] = freq.get(t, 0) + 1
    log("  vocabulary: %d types, %d tokens" % (len(freq), sum(freq.values())))

    acyc_ty = cyc_flat_ty = curv_ty = 0
    acyc_to = cyc_flat_to = curv_to = 0
    for w, c in freq.items():
        order, edges, charges = glyph_graph(w)
        if not edges:
            acyc_ty += 1
            acyc_to += c
            continue
        b1, nh, _, _ = gauge_decompose(len(order), edges, charges)
        if nh:
            curv_ty += 1
            curv_to += c
        elif b1 == 0:
            acyc_ty += 1
            acyc_to += c
        else:
            cyc_flat_ty += 1
            cyc_flat_to += c

    n_ty = max(1, len(freq))
    n_to = max(1, sum(freq.values()))
    log("")
    log("  %-38s %-22s %s" % ("class", "by TYPE", "by TOKEN"))
    log("  %-38s %-9d %-11.2f%% %-9d %.2f%%" % ("acyclic (provably endianness only)",
                                                acyc_ty, 100.0 * acyc_ty / n_ty, acyc_to, 100.0 * acyc_to / n_to))
    log("  %-38s %-9d %-11.2f%% %-9d %.2f%%" % ("cyclic but ZERO holonomy (gauge)",
                                                cyc_flat_ty, 100.0 * cyc_flat_ty / n_ty, cyc_flat_to,
                                                100.0 * cyc_flat_to / n_to))
    log("  %-38s %-9d %-11.2f%% %-9d %.2f%%" % ("GENUINE CURVATURE (holonomy != 0)",
                                                curv_ty, 100.0 * curv_ty / n_ty, curv_to, 100.0 * curv_to / n_to))

    gauge_ty = acyc_ty + cyc_flat_ty
    gauge_to = acyc_to + cyc_flat_to
    log("")
    log("  => PURE GAUGE (endianness) total: %.2f%% of types, %.2f%% of running tokens" %
        (100.0 * gauge_ty / n_ty, 100.0 * gauge_to / n_to))

    rec = {"srmech": srmech.__version__, "docs": args.limit, "probes": probe_rows,
           "types": len(freq), "tokens": sum(freq.values()),
           "by_type": {"acyclic": acyc_ty, "cyclic_zero_holonomy": cyc_flat_ty, "curvature": curv_ty},
           "by_token": {"acyclic": acyc_to, "cyclic_zero_holonomy": cyc_flat_to, "curvature": curv_to},
           "seconds": round(time.time() - T0, 1)}
    REPORT.write_text(json.dumps(rec) + "\n")
    log("report -> %s" % REPORT)
    log("VERDICT: if the curvature row is small, F1213 restored ORIENTATION (the exact/gradient part), not "
        "curvature — and the byte/glyph re-base buys endianness, not the Class-C which-way.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
