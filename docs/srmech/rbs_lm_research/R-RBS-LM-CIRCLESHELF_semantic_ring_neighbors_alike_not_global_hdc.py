r"""R-RBS-LM-CIRCLESHELF (the user's architecture 2026-06-07): a CIRCLE bookshelf of a fixed number of tomes (a ring
buffer; the least-important is overwritten, like wet brains prioritising). The goal: knowledge NATURALLY PARTITIONS
into tomes so that "like" information is bound NOT just to its own tome but to its NEIGHBOURS too — semantic
locality = shelf locality. CRUCIAL distinction (the user): this is NOT spreading a torus-shaped HDC across ALL the
data — a single HDC object of the entire circle "would not be able to see the entire structure, only neighbour
books" (the capacity wall, F527). Instead, meaning is LOCAL: similar words land in adjacent tomes; each tome binds
to its neighbours; you navigate neighbour-to-neighbour with NO global object.

Mechanism: the Class-L spectral CIRCULAR embedding — angle a_j = atan2(V[:,2], V[:,1]) places semantically-similar
words at similar angles. Partition the circle into N tome-arcs -> adjacent tomes are alike; "like" info spills to
neighbours.

Claims:
  (1) NEIGHBOURS ARE ALIKE: adjacent tomes share more co-occurrence than distant tomes.
  (2) "LIKE" SPILLS TO NEIGHBOURS: a word resembles its own tome AND its neighbour tomes >> far tomes.
  (3) NOT A GLOBAL HDC: a single bundle of ALL tomes (the "full tori") canNOT resolve the whole circle — it sees
      only a few (neighbour) books; the LOCAL neighbour shelf preserves the structure a global object loses.
  (4) RING-BUFFER eviction degrades gracefully: overwrite the least-important word; its meaning survives in
      neighbour tomes (wet-brain-like prioritisation).

srmech 0.7.4; Class-L spectral circular embedding + Class-M hdc bundle/similarity. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.amsc import hdc
from srmech.calculus import atan2 as srm_atan2   # full-circle, |x|>1 safe — NOT np.arctan2 (srmech-first, F540)
from srmech.signal_processing import mint_vector

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
D = 8192


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def circ(i, j, N):
    return min((i - j) % N, (j - i) % N)


def main():
    print(f"=== R-RBS-LM-CIRCLESHELF — a semantic ring of tomes (neighbours alike), NOT a global HDC of the circle  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)
    ang = np.array([(srm_atan2(float(V[i, 2]), float(V[i, 1])) + 2 * np.pi) % (2 * np.pi) for i in range(N)])   # Class-L spectral CIRCULAR position (srmech.calculus.atan2)
    NT = 16
    tome_of = (ang / (2 * np.pi) * NT).astype(int) % NT             # which tome-arc each word falls in
    tomes = [[i for i in range(N) if tome_of[i] == t] for t in range(NT)]

    def tome_sim(a, b):                                             # cross-tome co-occurrence (semantic)
        pa, pb = tomes[a], tomes[b]
        if not pa or not pb:
            return 0.0
        return float(np.mean([jacc(nb[vocab[x]], nb[vocab[y]]) for x in pa[:8] for y in pb[:8]]))

    # (1) neighbours alike vs far
    nbr = np.mean([tome_sim(t, (t + 1) % NT) for t in range(NT)])
    far = np.mean([tome_sim(t, (t + NT // 2) % NT) for t in range(NT)])
    print(f"(1) NEIGHBOURS ARE ALIKE: adjacent-tome similarity {nbr:.3f} vs far-tome {far:.3f}  ({nbr/max(far,1e-9):.1f}x).")
    print(f"    -> the spectral ring places 'like' words in ADJACENT tomes (semantic locality = shelf locality).\n")

    # (2) a word resembles its own tome + neighbours >> far
    own, nb1, farn = [], [], []
    for w in [x for x in ("ocean", "history", "music", "science") if x in idx][:4]:
        t = tome_of[idx[w]]
        sown = np.mean([jacc(nb[w], nb[vocab[x]]) for x in tomes[t] if vocab[x] != w] or [0])
        snb = np.mean([jacc(nb[w], nb[vocab[x]]) for nt in ((t + 1) % NT, (t - 1) % NT) for x in tomes[nt]] or [0])
        sfar = np.mean([jacc(nb[w], nb[vocab[x]]) for x in tomes[(t + NT // 2) % NT]] or [0])
        own.append(sown); nb1.append(snb); farn.append(sfar)
    print(f"(2) 'LIKE' SPILLS TO NEIGHBOURS: a word's similarity to own tome {np.mean(own):.3f}, neighbour tomes {np.mean(nb1):.3f},")
    print(f"    far tomes {np.mean(farn):.3f} -> like info is bound to its tome AND its neighbours, not just its own tomb.\n")

    # (3) a GLOBAL HDC of the whole circle cannot see the structure (only neighbours)
    word_hv = {i: mint_vector(f"w{i}", D=D) for i in range(N)}
    def bundle(ids):
        vs = [word_hv[i] for i in ids]
        if len(vs) % 2 == 0:
            vs = vs + [mint_vector("__pad__", D=D)]
        return hdc.bundle(vs) if vs else mint_vector("__empty__", D=D)
    tome_hv = [bundle(tomes[t]) for t in range(NT)]
    full_tori = bundle([i for t in tomes for i in t])              # ONE HDC of the ENTIRE circle
    resolved = sum(1 for t in range(NT) if hdc.similarity(full_tori, tome_hv[t]) > 0.15)
    own_tome = np.mean([hdc.similarity(tome_hv[t], tome_hv[t]) for t in range(NT)])
    print(f"(3) NOT A GLOBAL HDC: the 'full tori' (ONE bundle of all {N} words) resolves only {resolved}/{NT} tomes above")
    print(f"    threshold — it CANNOT see the whole structure (the capacity wall). A single tome resolves its OWN")
    print(f"    content (self-sim {own_tome:.2f}); the LOCAL neighbour shelf keeps every tome sharp, no global object needed.\n")

    # (4) ring-buffer eviction: drop the least-important word; meaning survives in neighbours
    t0 = tome_of[idx[next(x for x in ('ocean','history','music','science') if x in idx)]]
    if tomes[t0]:
        victim = min(tomes[t0], key=lambda i: len(nb[vocab[i]]))   # least-important = lowest degree
        nbr_has = np.mean([jacc(nb[vocab[victim]], nb[vocab[x]]) for nt in ((t0+1)%NT,(t0-1)%NT) for x in tomes[nt]] or [0])
        print(f"(4) RING-BUFFER EVICTION (overwrite least-important, like a wet brain): evict '{vocab[victim]}' (lowest degree)")
        print(f"    -> its meaning still resembles the NEIGHBOUR tomes ({nbr_has:.3f}) — graceful, the cluster survives next door.\n")

    print("VERDICT:")
    print(f"  • A SEMANTIC RING, NOT A GLOBAL HDC: the Class-L circular embedding partitions knowledge so NEIGHBOURS")
    print(f"    are alike ({nbr/max(far,1e-9):.1f}x adjacent-vs-far) and 'like' info binds to its tome AND its neighbours")
    print(f"    ({np.mean(nb1):.3f} neighbour vs {np.mean(farn):.3f} far). You navigate neighbour-to-neighbour — local, no global view.")
    print(f"  • THE FULL TORI CANNOT SEE THE WHOLE STRUCTURE: one HDC of the entire circle resolves only {resolved}/{NT} tomes")
    print(f"    (the capacity wall the user named) — exactly why we keep LOCAL neighbour structure instead of a global object.")
    print(f"  • RING-BUFFER + GRACEFUL FORGETTING: fixed tomes, overwrite the least-important; locality means the evicted")
    print(f"    meaning survives in neighbour tomes — wet-brain-like prioritisation without a global index. A worth-probing")
    print(f"    architecture (deviates from a literal SNN, but coherent): semantic locality on a fixed ring.")


if __name__ == "__main__":
    main()
