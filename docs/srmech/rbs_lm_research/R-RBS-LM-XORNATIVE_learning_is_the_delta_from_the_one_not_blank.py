r"""R-RBS-LM-XORNATIVE (the user's insight 2026-06-07): "why would a wet SNN start blank? learning is changing the
substrate-stored / XOR from NATIVE values of how biology stores things — what actually gets stored is the DELTA, and
the decay-alpha we use for simulated learning is the same thing that reshapes the substrate-native rules into
etak-shaped rules of knowledge."

This is the founding delta-encode principle (F172: store only what CHANGED) applied to the_one as the base. The claim:
  • The substrate-native base (the_one — the 1:3:7:3 loop) is SHARED — computed, not stored per individual.
  • A newborn kernel IS the_one: nothing is learned, so the stored delta is EMPTY (not a blank slate — a the_one slate).
  • Learning writes a DELTA (an XOR / symmetric-difference) onto the native; the F543 decay-alpha is exactly the rate
    that delta accumulates (native reshapes into knowledge).
  • Reconstruction is EXACT and reversible: knowledge = native XOR delta (set sym-diff is its own inverse), so the
    SHARED native + the individual's SMALL delta = the full knowledge. You store the deviation, not the absolute.

Test: native = the_one-seed embedding (a word's neighbour-set under the the_one base); knowledge(p) = the F543
decaying-seed kernel at learning fraction p; delta(p) = symmetric difference (what each word's neighbourhood changed
from native). Measure: delta starts EMPTY at p=0 (newborn), grows with learning; reconstruction native△delta==knowledge
is exact; and the stored delta is far smaller than the absolute knowledge while learning is partial.

srmech 0.7.4; the_one seed + Class-L dense_laplacian/symmetric_eigendecompose; set-XOR delta (basis-invariant). No abs(); no CAD; no sub-agents.
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
    o = np.argsort(np.array(w))
    return np.array(Vv)[:, o][:, 1:3]


def knn(emb, k=6):
    return [set(np.argsort(((emb - emb[i]) ** 2).sum(1))[1:k + 1].tolist()) for i in range(len(emb))]


def main():
    print(f"=== R-RBS-LM-XORNATIVE — learning is the XOR-delta from the_one-native, not a blank slate  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, _Vd = (sup.build(seq))[:4]
    N = len(vocab)
    K = 6

    # data edges (the knowledge to be learned)
    data_set = set()
    for i, w in enumerate(vocab):
        for u in nb[w]:
            j = idx[u]
            if j != i:
                data_set.add((min(i, j), max(i, j)))
    data_edges = sorted(data_set)
    rng = np.random.default_rng(0)
    data_edges = [data_edges[t] for t in rng.permutation(len(data_edges))]
    M = len(data_edges)

    # the_one NATIVE base: node-slots on the_one's theta-circle (the SHARED substrate prior)
    feats = [np.array(cascade.the_one(1, round(i / N * 360), 360, 10).to_numpy()) for i in range(N)]
    fmean = np.mean(feats, axis=0); feats = [f - fmean for f in feats]
    prior_edges, prior_w = [], []
    for i in range(N):
        for d in (1, 2):
            j = (i + d) % N
            prior_edges.append((min(i, j), max(i, j))); prior_w.append(max(0.05, fsim(feats[i], feats[j])))

    native_edges = {e for e in prior_edges}                      # the newborn = the_one (the SHARED base), as an edge set
    data_set2 = set(data_edges)

    print(f"corpus N={N}; the_one native = {len(native_edges)} edges (SHARED, not stored per-individual); knowledge = {M} co-occurrence edges.")
    print(f"storage measured at the EDGE level (stable; the 2D-embedding NN metric is too brittle — tiny kernel changes reshuffle it).\n")
    print(f"{'learning p':>10} {'decay α':>8} | {'ADDITIVE (keep native): δ/abs':>30} | {'REPLACE (discard native): δ/abs':>32} | recon")
    print("-" * 100)
    for p in [0.0, 0.05, 0.20, 0.50, 1.0]:
        m = int(p * M)
        ds = 30.0 / (30.0 + m)                                    # F543 decay-alpha (the keep<->replace knob)
        learned = set(data_edges[:m])
        # ADDITIVE: knowledge keeps the native scaffold + adds experience. store only the additions.
        know_add = native_edges | learned
        delta_add = know_add ^ native_edges                       # = learned - native (the additions)
        recon_add = (native_edges ^ delta_add) == know_add        # sym-diff is its own inverse -> exact
        ra = f"{len(delta_add)}/{len(know_add)} = {len(delta_add)/max(1,len(know_add)):.0%}"
        # REPLACEMENT: knowledge replaces native (F543 high-decay). store the diff from the generic native.
        know_rep = learned
        delta_rep = know_rep ^ native_edges
        recon_rep = (native_edges ^ delta_rep) == know_rep
        rr = f"{len(delta_rep)}/{max(1,len(know_rep))} = {len(delta_rep)/max(1,len(know_rep)):.0%}" if m else "0/0 = (newborn)"
        ok = "EXACT" if (recon_add and recon_rep) else "FAIL"
        print(f"{p:>9.0%} {ds:>8.2f} | {ra:>30} | {rr:>32} | {ok}")

    print()
    print("VERDICT:")
    print(f"  • IT DOES NOT START BLANK — it starts as the_one. At p=0 (newborn) the stored delta is EMPTY: knowledge ==")
    print(f"    the native the_one base, nothing learned yet. (A blank slate stores everything from scratch; a the_one slate")
    print(f"    stores nothing until experience writes a delta.) And reconstruction native△delta==knowledge is EXACT throughout.")
    print(f"  • THE EFFICIENCY DEPENDS ON KEEP-vs-REPLACE (honest, with a real tradeoff):")
    print(f"      ADDITIVE (learning KEEPS the native scaffold, only adds): stored delta < absolute — you store just your")
    print(f"        additions, and the the_one native is SHARED (computed once, amortised across all individuals, never")
    print(f"        re-stored). THIS is the storage win, and it is the biological reading (keep the substrate, add specifics).")
    print(f"      REPLACEMENT (learning DISCARDS native — the F543 high-decay regime): the delta EXCEEDS the absolute,")
    print(f"        because the_one's GENERIC edges are not the SPECIFIC knowledge. The_one is a great cold-start PRIOR (F543)")
    print(f"        but a poor compressor if you throw it away.")
    print(f"  • SO THE DECAY-α IS THE KNOB ON A TRADEOFF: high decay = no bias on the converged shape (F543 'prior not bias')")
    print(f"    BUT big delta (poor storage); low decay = small delta (keep the scaffold, cheap storage) BUT the native")
    print(f"    biases the shape. Biology likely sits where the native is KEPT enough to store cheap — learning is the XOR")
    print(f"    that reshapes the substrate-native rules into etak-shaped (moving-frame) rules. 'Where we see circles we")
    print(f"    have seen loops': the wet base is the_one (a loop, held even happily, F544); learning is the kept-native XOR.")
    print(f"    Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
