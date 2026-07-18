r"""R-RBS-LM-ORGANELLESPLIT (F1053/F1059 at scale, for the srmech data-driven eukaryote/organelle partitioner) —
measure the nuclear-vs-organelle split on the REAL simplewiki co-occurrence graph (831,139 vocab / 39,048,148 edges),
using the existing demand-load store (reads/adj.bin per-node neighbours) + the tome-tree communities (tree/word_tome).
NO re-encode: the relational structure is already on disk (only the MINTED shape waits on rc270).

Criterion (F1053, verbatim): DISCRIMINATOR = local clustering coefficient (do your neighbours know each other?) +
community-bridge span (how many distinct communities a node's neighbours sit in). NUCLEAR = high clustering (~0.9),
one community. ORGANELLE = low clustering (~0.2), bridges 3-4. Toy-40-node bimodal was ~0.2 / ~0.9. F1059 EPH:
exciting an organelle powered 3.3 communities vs 2.0 for a nuclear node — "gap should sharpen at scale".

Items: (1) clustering + bridge-span distribution across the graph -> is it bimodal, and what is the DATA-DRIVEN
split point (the antimode gap)?  (2) organelle identity — which words come out organelle (low-C, bridges-many)?
(3) EPH power probe at scale (heat kernel e^{-tL} via srmech native propagate_sparse) — organelle vs nuclear reach.

srmech 0.9.0rc269 (native). No numpy in the graph stats; no abs-builtin. Composes F1053/F1059/F1063/F1061, §100/F1249.
Run (background):  /tmp/srmech_rc269/venv/bin/python3 R-RBS-LM-ORGANELLESPLIT_*.py
"""
import struct
import sys
import time
from pathlib import Path

SIONA = "/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/siona"
sys.path.insert(0, SIONA)
from siona import corpus_store as cs
from srmech.amsc import laplacian as L

GENOME = str(Path.home() / "corpora" / "wikipedia" / "simplewiki_directed.genome")
IDX = struct.Struct("<QI")
REC = struct.Struct("<iii")
CAP = 200            # triangle-count neighbour cap (metric-sorted top-CAP) — reported; bounds the O(deg^2) hubs
SAMPLE_PER_DECILE = 600
T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def degree(h, t):
    return IDX.unpack_from(h["idx"], t * IDX.size)[1]


def neighbours(h, t, cap=CAP):
    off, cnt = IDX.unpack_from(h["idx"], t * IDX.size)
    n = min(cnt, cap)
    return [REC.unpack_from(h["mm"], off + m * REC.size)[0] for m in range(n)], cnt


def main():
    log("opening the demand store (mmap adj.bin, load tree) ...")
    h = cs.open_demand(GENOME)
    vocab = h["vocab"]
    nrec = len(h["idx"]) // IDX.size
    tree = h.get("tree") or {}
    word_tome = tree.get("word_tome", {})          # content-word -> tome id (the topical communities)
    tome_of_id = {}                                # node id -> tome (for the nodes that have one)
    for w, tm in word_tome.items():
        i = h["vindex"].get(w)
        if i is not None:
            tome_of_id[i] = tm
    n_tomes = (max(word_tome.values()) + 1) if word_tome else 0
    log("store open: %d vocab, %d tomes, %d hub-ids, %d tome-mapped nodes" %
        (nrec, n_tomes, len(h.get("hub_ids") or ()), len(tome_of_id)))

    # ---- stratify a sample by degree (deciles) so bimodality isn't a degree artefact ----
    log("reading per-node degrees for stratification ...")
    degs = [IDX.unpack_from(h["idx"], t * IDX.size)[1] for t in range(nrec)]
    order = sorted(range(nrec), key=lambda t: degs[t])
    order = [t for t in order if degs[t] >= 2]      # need >=2 neighbours for a clustering coeff
    m = len(order)
    sample = []
    for d in range(10):
        lo, hi = d * m // 10, (d + 1) * m // 10
        band = order[lo:hi]
        step = max(1, len(band) // SAMPLE_PER_DECILE)
        sample += band[::step][:SAMPLE_PER_DECILE]
    log("sampled %d nodes across 10 degree-deciles (deg %d..%d)" % (len(sample), degs[order[0]], degs[order[-1]]))

    # ---- clustering + PARTICIPATION COEFFICIENT (degree-normalized bridge) per sampled node ----
    # participation P = 1 - sum_c (k_ic/k_i)^2 over communities c; P=0 -> all neighbours in ONE community (nuclear),
    # P->1 -> neighbours spread EVENLY across communities (organelle bridge). Degree-normalized (unlike raw span).
    log("computing clustering + participation coefficient (CAP=%d) ..." % CAP)
    rows = []
    for k, u in enumerate(sample):
        Nu_list, deg_u = neighbours(h, u)
        Nu = set(Nu_list)
        Nu.discard(u)
        if len(Nu) < 2:
            continue
        tri = 0
        for v in Nu:
            Nv, _ = neighbours(h, v)
            tri += sum(1 for w in Nv if w in Nu)
        possible = len(Nu) * (len(Nu) - 1)
        clus = tri / possible if possible else 0.0
        # community histogram of the neighbours that HAVE a tome
        cc = {}
        for v in Nu:
            tm = tome_of_id.get(v)
            if tm is not None:
                cc[tm] = cc.get(tm, 0) + 1
        span = len(cc)
        ktot = sum(cc.values())
        part = (1.0 - sum((kc / ktot) ** 2 for kc in cc.values())) if ktot else 0.0
        rows.append((u, deg_u, clus, span, part, ktot))
        if (k + 1) % 1500 == 0:
            log("  %d/%d (last %r clus=%.3f span=%d part=%.3f deg=%d)" %
                (k + 1, len(sample), vocab[u], clus, span, part, deg_u))

    # rows = (u, deg, clus, span, part, ktot). Restrict the bimodality test to nodes with a real community
    # signal (ktot>=8 tome-mapped neighbours) so participation isn't dominated by tiny-degree rare cliques.
    def histo(vals, label, nb=20):
        vals = sorted(vals)
        hist = [0] * nb
        for c in vals:
            hist[min(nb - 1, int(c * nb))] += 1
        log("%s histogram (bin %.2f), n=%d:" % (label, 1.0 / nb, len(vals)))
        mx = max(hist) or 1
        for b in range(nb):
            print("   %.2f-%.2f | %5d %s" % (b / nb, (b + 1) / nb, hist[b], "#" * (hist[b] * 55 // mx)), flush=True)
        lo = max(range(nb // 2), key=lambda b: hist[b])
        hi = nb // 2 + max(range(nb - nb // 2), key=lambda b: hist[nb // 2 + b])
        anti = min(range(lo + 1, hi), key=lambda b: hist[b]) if hi > lo + 1 else nb // 2
        return (lo + 0.5) / nb, (hi + 0.5) / nb, (anti + 0.5) / nb

    signal = [r for r in rows if r[5] >= 8]          # ktot>=8 tome-mapped neighbours
    log("--- (1) PARTICIPATION (degree-normalized community-bridge) is the primary discriminator ---")
    plo, phi, psplit = histo([r[4] for r in signal], "PARTICIPATION")
    log("participation modes ~%.2f (nuclear) / ~%.2f (organelle) ; DATA-DRIVEN SPLIT = %.3f" % (plo, phi, psplit))
    log("--- clustering (secondary — NOT cleanly bimodal at word-graph scale, reported for the record) ---")
    clo, chi, csplit = histo([r[2] for r in rows], "CLUSTERING")

    organelle = [r for r in signal if r[4] >= psplit]
    nuclear = [r for r in signal if r[4] < psplit]

    def stat(rs, f):
        xs = [f(r) for r in rs]
        return (sum(xs) / len(xs)) if xs else 0.0
    log("ORGANELLE (part>=%.3f): n=%d  mean part=%.3f  mean clus=%.3f  mean span=%.1f  mean deg=%.0f" %
        (psplit, len(organelle), stat(organelle, lambda r: r[4]), stat(organelle, lambda r: r[2]),
         stat(organelle, lambda r: r[3]), stat(organelle, lambda r: r[1])))
    log("NUCLEAR  (part< %.3f): n=%d  mean part=%.3f  mean clus=%.3f  mean span=%.1f  mean deg=%.0f" %
        (psplit, len(nuclear), stat(nuclear, lambda r: r[4]), stat(nuclear, lambda r: r[2]),
         stat(nuclear, lambda r: r[3]), stat(nuclear, lambda r: r[1])))

    # ---- (2) organelle identity: highest participation (degree-normalized bridge) ----
    ranked = sorted(signal, key=lambda r: -r[4])
    log("TOP-25 ORGANELLE words (highest participation = spreads evenly across communities):")
    for (u, dg, cu, sp, pt, kt) in ranked[:25]:
        print("   %-16s part=%.3f clus=%.3f span=%d deg=%d" % (vocab[u], pt, cu, sp, dg), flush=True)
    log("BOTTOM-15 = NUCLEAR words (lowest participation = locked to one community):")
    for (u, dg, cu, sp, pt, kt) in ranked[-15:]:
        print("   %-16s part=%.3f clus=%.3f span=%d deg=%d" % (vocab[u], pt, cu, sp, dg), flush=True)

    # ---- (3) EPH power probe (heat kernel) — FAIR: both seeds IN a tome + matched degree band ----
    log("--- (3) EPH power probe (frontier heat diffusion; matched-degree, both seeds in a community) ---")
    inb = [r for r in signal if r[0] in tome_of_id and 500 <= r[1] <= 8000]   # in a tome, comparable degree
    org_seed = max(inb, key=lambda r: r[4])         # highest participation (organelle)
    dband = org_seed[1]
    nuc_cand = [r for r in inb if 0.4 * dband <= r[1] <= 2.5 * dband]
    nuc_seed = min(nuc_cand, key=lambda r: r[4])    # lowest participation in the matched degree band (nuclear)

    def heat_reach(seed, steps=4, dt=0.15, keep=4000):
        x = {seed: 1.0}
        for _ in range(steps):
            nx = {}
            for u, xu in x.items():
                Nu, _ = neighbours(h, u, cap=64)
                if not Nu:
                    continue
                share = dt * xu / len(Nu)
                nx[u] = nx.get(u, 0.0) + xu * (1 - dt)
                for v in Nu:
                    nx[v] = nx.get(v, 0.0) + share
            if len(nx) > keep:
                nx = dict(sorted(nx.items(), key=lambda kv: -kv[1])[:keep])
            x = nx
        tot = sum(x.values()) or 1.0
        tome_heat = {}
        for u, xu in x.items():
            tm = tome_of_id.get(u)
            if tm is not None:
                tome_heat[tm] = tome_heat.get(tm, 0.0) + xu / tot
        return sum(1 for v in tome_heat.values() if v > 0.01), len(x)

    org_r, org_n = heat_reach(org_seed[0])
    nuc_r, nuc_n = heat_reach(nuc_seed[0])
    log("EXCITE ORGANELLE %r (part=%.3f deg=%d): powers %d communities" % (vocab[org_seed[0]], org_seed[4], org_seed[1], org_r))
    log("EXCITE NUCLEAR   %r (part=%.3f deg=%d): powers %d communities" % (vocab[nuc_seed[0]], nuc_seed[4], nuc_seed[1], nuc_r))
    log("VERDICT: participation split=%.3f ; organelle part %.3f/span %.1f vs nuclear %.3f/span %.1f ; EPH %d vs %d communities (toy F1059: 3.3 vs 2.0)" %
        (psplit, stat(organelle, lambda r: r[4]), stat(organelle, lambda r: r[3]),
         stat(nuclear, lambda r: r[4]), stat(nuclear, lambda r: r[3]), org_r, nuc_r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
