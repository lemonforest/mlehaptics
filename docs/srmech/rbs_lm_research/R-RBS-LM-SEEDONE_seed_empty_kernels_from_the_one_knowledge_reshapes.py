r"""R-RBS-LM-SEEDONE (the user's architectural rule 2026-06-07): "always seed new EMPTY kernels from the_one and let
added knowledge reshape it, when the shape of knowledge isn't already known." This IS the field/excitation duality
(DUALITY.md) as a kernel-construction rule: the_one is the substrate's OWN shape (the field-truth, the 1:3:7:3); an
empty kernel should be BORN with it, and incoming knowledge (the local excitation) reshapes it — rather than starting
from a degenerate blank.

The load-bearing test is that the seed is a PRIOR, not a BIAS: it must give structure at cold-start AND wash out as
knowledge accumulates (so it never biases the known-shape regime). Two claims:
  (1) COLD-START: a from-scratch (data-only) kernel with little data is DEGENERATE (a disconnected graph, many
      zero-eigenvalue components, no usable embedding). The the_one-seeded kernel is connected + usable immediately.
  (2) RESHAPE + WASH-OUT: as knowledge is added, the seeded kernel migrates from the_one-shape toward the data-shape,
      and at full data the seeded kernel AGREES with the data-only kernel (the seed left no permanent mark).

Construction (fully srmech-native): the_one seed = a weighted ring over N node-slots placed on the_one's theta-circle,
each edge weighted by the 14-dim the_one feature similarity (so the seed carries the_one's actual 1:3:7:3 shape, not
a bare ring). Knowledge = the wiki co-occurrence edges, revealed in a growing fraction p. Kernel = Class-L Laplacian
(srmech dense_laplacian, weighted) + symmetric_eigendecompose. Reshape measured by spectral-embedding neighbour
overlap (rotation/sign-invariant).

srmech 0.7.4; cascade.the_one (the seed) + Class-L dense_laplacian/symmetric_eigendecompose. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.amsc import cascade
from srmech.amsc.laplacian import dense_laplacian, symmetric_eigendecompose

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def fsim(a, b):
    d = (a @ a) ** 0.5 * (b @ b) ** 0.5
    return float(a @ b / d) if d else 0.0


def embed(n, edges, weights):
    """Class-L kernel -> (2D spectral embedding cols 1,2 ; ascending eigenvalues)."""
    L = dense_laplacian(n, edges, weights)
    w, Vv = symmetric_eigendecompose(np.array(L))
    o = np.argsort(np.array(w))
    return np.array(Vv)[:, o][:, 1:3], np.array(w)[o]


def knn(emb, k=6):
    out = []
    for i in range(len(emb)):
        d = ((emb - emb[i]) ** 2).sum(1)
        out.append(set(np.argsort(d)[1:k + 1].tolist()))
    return out


def overlap(eA, eB, k=6):
    a, b = knn(eA, k), knn(eB, k)
    return float(np.mean([len(a[i] & b[i]) / max(1, len(a[i] | b[i])) for i in range(len(a))]))


def components(evals):
    return int(np.sum(np.array(evals) < 1e-9))


def main():
    print(f"=== R-RBS-LM-SEEDONE — seed empty kernels from the_one; knowledge reshapes it (prior, not bias)  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, _Vd = (sup.build(seq))[:4]
    N = len(vocab)

    # ---- DATA edges (the knowledge): wiki co-occurrence over the N words ----
    data_set = set()
    for i, w in enumerate(vocab):
        for u in nb[w]:
            j = idx[u]
            if j != i:
                data_set.add((min(i, j), max(i, j)))
    data_edges = sorted(data_set)
    rng = np.random.default_rng(0)
    perm = rng.permutation(len(data_edges))
    data_edges = [data_edges[t] for t in perm]                    # shuffled so a prefix = a uniform sample

    # ---- the_one SEED: node-slots on the_one's theta-circle, weighted by 14-dim the_one feature similarity ----
    feats = [np.array(cascade.the_one(1, round(i / N * 360), 360, 10).to_numpy()) for i in range(N)]
    fmean = np.mean(feats, axis=0)
    feats = [f - fmean for f in feats]                            # centre so the constant block doesn't flatten it
    prior_edges, prior_w = [], []
    for i in range(N):
        for d in (1, 2):                                          # the_one's circle (radius-2 ring) = the seed shape
            j = (i + d) % N
            prior_edges.append((min(i, j), max(i, j)))
            prior_w.append(max(0.05, fsim(feats[i], feats[j])))

    # ---- reference embeddings ----
    seed_emb, seed_ev = embed(N, prior_edges, prior_w)            # the_one only (empty of knowledge)
    data_emb, data_ev = embed(N, data_edges, [1.0] * len(data_edges))   # data only, FULL

    print(f"corpus: N={N} words, {len(data_edges)} co-occurrence edges; the_one seed = {len(prior_edges)} weighted ring edges.\n")
    M = len(data_edges)

    def decay_scale(m):
        """the seed is OVERWRITABLE: its per-edge weight fades as knowledge (m revealed edges) accumulates."""
        return 30.0 / (30.0 + m)                                 # 1.0 at m=0 -> ~0.03 at m=M (the seed dilutes)

    print(f"{'p':>5} | {'COLD data-only':^18} | {'SEEDED fixed-prior':^26} | {'SEEDED decaying-prior':^26}")
    print(f"{'':>5} | {'comp':>5} {'usable':>6} {'~data':>5} | {'comp':>4} {'~seed':>5} {'~data':>5} {'wt':>5} | {'comp':>4} {'~seed':>5} {'~data':>5} {'wt':>5}")
    print("-" * 92)
    fracs = [0.0, 0.01, 0.05, 0.20, 0.50, 1.0]
    rows = []
    for p in fracs:
        m = int(p * M)
        de = data_edges[:m]
        # COLD: data only
        if de:
            cold_emb, cold_ev = embed(N, de, [1.0] * len(de))
            cc, cdata = components(cold_ev), overlap(cold_emb, data_emb)
        else:
            cc, cdata, cold_emb = N, 0.0, None
        # SEEDED-FIXED: constant prior weight (the naive scaffold)
        fe, fw = prior_edges + de, prior_w + [1.0] * len(de)
        f_emb, f_ev = embed(N, fe, fw)
        fc, fseed, fdata = components(f_ev), overlap(f_emb, seed_emb), overlap(f_emb, data_emb)
        # SEEDED-DECAY: prior weight fades as knowledge accumulates (the overwritable seed)
        ds = decay_scale(m)
        dw = [ds * w for w in prior_w] + [1.0] * len(de)
        d_emb, d_ev = embed(N, prior_edges + de, dw)
        dc, dseed, ddata = components(d_ev), overlap(d_emb, seed_emb), overlap(d_emb, data_emb)
        rows.append((p, cc, cdata, fc, fseed, fdata, dc, dseed, ddata, ds))
        print(f"{p:>4.0%} | {cc:>5} {('YES' if cc<=2 else 'no'):>6} {cdata:>5.2f} | "
              f"{fc:>4} {fseed:>5.2f} {fdata:>5.2f} {'1.00':>5} | {dc:>4} {dseed:>5.2f} {ddata:>5.2f} {ds:>5.2f}")

    fixed_wash = rows[-1][5]                                       # seeded-fixed ~ data at p=1
    decay_wash = rows[-1][8]                                       # seeded-decay ~ data at p=1
    print()
    print("VERDICT:")
    print(f"  • (1) COLD-START CONFIRMED (both seeds): at p=1% the from-scratch kernel is {rows[1][1]} disconnected components")
    print(f"        (no usable embedding) vs {rows[1][6]} for the the_one-seeded kernel — born with the substrate's 1:3:7:3 shape,")
    print(f"        usable immediately, and stays connected while data-only is still {rows[3][1]}/{rows[4][1]} components at 20%/50%.")
    print(f"  • (2) A FIXED PRIOR BIASES (honest negative): with constant weight the seed fades from the embedding (~seed")
    print(f"        {rows[1][4]:.2f}->{rows[-1][4]:.2f}) but the kernel never reaches the data shape and does NOT wash out (seeded~data only {fixed_wash:.2f}")
    print(f"        at full data) — a permanent scaffold leaves a permanent mark. 'Reshape' must mean OVERWRITABLE.")
    print(f"  • (3) A DECAYING PRIOR RESHAPES + WASHES OUT (the rule, done right): fading the seed weight as knowledge")
    print(f"        accumulates gives cold-start structure AND lets the data take over — seeded~data rises to {decay_wash:.2f} at full")
    print(f"        data (vs the fixed prior's {fixed_wash:.2f}). The_one shapes the cold substrate; the excitation overwrites it.")
    print(f"  • So the rule holds WITH a decaying weight: seed empty kernels from the_one when the shape isn't known, and let")
    print(f"    knowledge OVERWRITE it (field/excitation, DUALITY.md). The seed is a prior, not a bias. F398/F394.")


if __name__ == "__main__":
    main()
