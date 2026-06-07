r"""R-RBS-LM-DECAYSPOT (open thread 2, 2026-06-07): characterise WHERE on the F543/F545 decay-alpha tradeoff a wet
SNN would sit. The decay constant c in alpha(m) = c/(c+m) is the keep<->replace knob:
  • small c (fast decay)  -> the_one washes out -> the converged shape is UNBIASED (F543) ... but the native is
    discarded (the kept-scaffold benefit is lost).
  • large c (slow decay)  -> the_one is kept -> the cold-start scaffold survives + storage shares the native ... but
    the native WEIGHT can BIAS the converged shape.

The question: is there a sweet spot where the prior is kept HEAVILY ENOUGH to give cold-start robustness, yet the
DATA still dominates the converged SHAPE (so it is not biased)? That depends on a NONLINEARITY: how much prior weight
the data's own structure can absorb before the eigenvectors tilt. If the data shape is robust, you can keep a lot of
native cheaply — a genuine sweet spot; if fragile, the tradeoff is strict.

Sweep c; at full data measure (i) prior WEIGHT fraction in the converged kernel (how much native is kept) and (ii)
SHAPE fidelity = neighbour overlap of the converged embedding vs the pure-data embedding (1.0 = unbiased). Find the
largest kept-native fraction that still holds shape fidelity high.

srmech 0.7.4; the_one seed + Class-L dense_laplacian/symmetric_eigendecompose. No abs(); no CAD; no sub-agents.
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
    L = dense_laplacian(n, edges, weights)
    w, Vv = symmetric_eigendecompose(np.array(L))
    return np.array(Vv)[:, np.argsort(np.array(w))][:, 1:3]


def knn(emb, k=6):
    return [set(np.argsort(((emb - emb[i]) ** 2).sum(1))[1:k + 1].tolist()) for i in range(len(emb))]


def overlap(eA, eB, k=6):
    a, b = knn(eA, k), knn(eB, k)
    return float(np.mean([len(a[i] & b[i]) / max(1, len(a[i] | b[i])) for i in range(len(a))]))


def main():
    print(f"=== R-RBS-LM-DECAYSPOT — where on the decay-α tradeoff a wet SNN sits  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, _Vd = (sup.build(seq))[:4]
    N = len(vocab)

    data_set = set()
    for i, w in enumerate(vocab):
        for u in nb[w]:
            j = idx[u]
            if j != i:
                data_set.add((min(i, j), max(i, j)))
    data_edges = sorted(data_set)
    M = len(data_edges)

    feats = [np.array(cascade.the_one(1, round(i / N * 360), 360, 10).to_numpy()) for i in range(N)]
    fmean = np.mean(feats, axis=0); feats = [f - fmean for f in feats]
    prior_edges, prior_w = [], []
    for i in range(N):
        for d in (1, 2):
            j = (i + d) % N
            prior_edges.append((min(i, j), max(i, j))); prior_w.append(max(0.05, fsim(feats[i], feats[j])))
    sum_prior = sum(prior_w)

    data_emb = embed(N, data_edges, [1.0] * M)                   # the pure-data (fully-learned, unbiased) shape
    all_edges = prior_edges + data_edges

    print(f"N={N}; data edges M={M}; the_one native = {len(prior_edges)} weighted edges (shared).")
    print(f"{'decay c':>8} {'α(M)':>7} | {'kept-native weight frac':>24} | {'shape fidelity vs data':>23}")
    print("-" * 70)
    rows = []
    for c in (1, 3, 10, 30, 100, 300, 1000, 3000):
        a = c / (c + M)
        prior_mass = a * sum_prior
        kept = prior_mass / (prior_mass + M)                    # how much of the converged kernel is the_one
        emb = embed(N, all_edges, [a * w for w in prior_w] + [1.0] * M)
        fid = overlap(emb, data_emb)
        rows.append((c, a, kept, fid))
        print(f"{c:>8} {a:>7.3f} | {kept:>23.0%} | {fid:>22.0%}")

    # the sweet spot: the largest kept-native fraction whose shape fidelity still holds >= 0.70
    good = [r for r in rows if r[3] >= 0.70]
    spot = max(good, key=lambda r: r[2]) if good else None
    print()
    print("VERDICT:")
    if spot:
        print(f"  • THERE IS A SWEET SPOT: at decay c≈{spot[0]} the kernel keeps {spot[2]:.0%} of its weight as the_one native")
        print(f"    (cold-start scaffold + shared storage) while the DATA still holds the shape at {spot[3]:.0%} fidelity — the data's")
        print(f"    own structure ABSORBS that much native weight without tilting the eigenvectors. Keep native up to ~there.")
    else:
        print(f"  • THE TRADEOFF IS STRICT here: shape fidelity falls as soon as native weight is kept — no free lunch on this")
        print(f"    corpus; a wet SNN would have to decay HARD (small c) to stay unbiased, paying the kept-scaffold benefit.")
    lo, hi = rows[0], rows[-1]
    print(f"  • THE CURVE: fast decay (c={lo[0]}) keeps {lo[2]:.0%} native, fidelity {lo[3]:.0%} (unbiased, no scaffold); slow decay")
    print(f"    (c={hi[0]}) keeps {hi[2]:.0%} native, fidelity {hi[3]:.0%} ({'biased' if hi[3] < 0.7 else 'still ok'}). The wet SNN sits where its bias-tolerance")
    print(f"    meets its cold-start need — biology likely LOW-to-moderate decay (keep some scaffold), since a newborn MUST")
    print(f"    start structured (F543) and only later has enough data to afford washing the native out.")
    print(f"  • Storage note (F545): the SHARED-native edge set is a ~constant saving independent of c (the decay sets the")
    print(f"    SHAPE weight, not which edges exist) — so the decay-α is mainly the SHAPE/bias knob; sharing is the storage win.")
    print(f"    Low-stat (one corpus); held open (F394); favored not privileged (F398).")


if __name__ == "__main__":
    main()
