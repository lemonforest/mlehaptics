r"""R-RBS-LM-SUPERPOSITION — answering two leads at once + the user's reframing (2026-06-07):

(1) "a person's knowledge is held in SUPERPOSITION — different words for what we already said." YES: the latent
    structure is the superposition; the Class-L eigen-modes are its BASIS; the F517 availability-gate is a
    MEASUREMENT/PROJECTION onto a subspace (the fiber spatially-absent-until-projected = the un-measured modes).
(2) F517's next lead: replace the UNIFORM-RANDOM gate with a STRUCTURED one — gate by spectral BAND, i.e. project
    out the GLOBAL (low-frequency, coarse, RH) band vs the LOCAL (high-frequency, fine, LH) band — and ask WHICH
    band biology dropping breaks self-recovery. (F514's coarse/fine split as the measurement basis.)

So the gate is now a PROJECTION onto an eigen-subspace (a measurement of the superposition). Concretely we classify
each edge as a GLOBAL bridge (its endpoints are FAR in the coarse low-frequency embedding = a long-range,
cross-cluster connection) or LOCAL detail (endpoints CLOSE = within-cluster), then test two structured projections:
  • GATE-GLOBAL : drop most global bridges, keep local detail  (the GLOBAL/RH hand un-projected)
  • GATE-LOCAL  : drop most local detail, keep global bridges   (the LOCAL/LH hand un-projected)
self-mirror = one projection (your state); genuine-other = two projections unioned (a 2nd person/state).

Prediction: dropping the GLOBAL band fragments the structure -> self-mirror recovery collapses, the genuine other
(different bridges) restores it most; dropping the LOCAL band keeps the global skeleton -> self-mirror survives.
That says WHICH knowledge biology gating costs you the second person for.

srmech 0.7.4; Class-L dense_laplacian + symmetric_eigendecompose (the superposition basis). No abs(); no CAD.
"""
import re
import importlib.util as U
from collections import Counter, deque
import numpy as np
import srmech
from srmech.amsc.laplacian import dense_laplacian, symmetric_eigendecompose

_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)

STOP = {"the", "and", "of", "to", "in", "is", "that", "this", "with", "for", "are", "as", "from", "by", "on",
        "or", "an", "be", "it", "at", "was", "were", "which", "they", "their", "have", "has", "had", "not",
        "but", "can", "all", "its", "his", "her", "him", "she", "you", "we", "our", "your", "them", "one", "two",
        "more", "most", "some", "such", "may", "also", "these", "than", "into", "when", "what", "a", "i"}


def build(seq, top=200, m=6):
    content = [w for w in seq if len(w) >= 4 and w not in STOP]
    vocab = [w for w, _ in Counter(content).most_common(top)]
    vset, idx = set(vocab), {w: i for i, w in enumerate(vocab)}
    co = Counter()
    for a in range(len(seq)):
        if seq[a] in vset:
            for b in range(a + 1, min(len(seq), a + 5)):
                if seq[b] in vset and seq[b] != seq[a]:
                    co[tuple(sorted((seq[a], seq[b])))] += 1
    strength = {w: [] for w in vocab}
    for (u, v), c in co.items():
        strength[u].append((c, v)); strength[v].append((c, u))
    nb = {w: set() for w in vocab}
    for w in vocab:
        for _, v in sorted(strength[w], reverse=True)[:m]:
            nb[w].add(v); nb[v].add(w)
    edges = sorted({(idx[w], idx[v]) for w, ns in nb.items() for v in ns if idx[w] < idx[v]})
    Lp = dense_laplacian(len(vocab), edges)
    evals, evecs = symmetric_eigendecompose(Lp)          # the SUPERPOSITION BASIS (eigen-modes of the knowledge)
    return vocab, idx, nb, evecs, edges


def connected(seed, target, nbs):
    seen, q = {seed}, deque([seed])
    while q:
        x = q.popleft()
        if x == target:
            return True
        for nb in nbs:
            for y in nb.get(x, ()):
                if y not in seen:
                    seen.add(y); q.append(y)
    return False


def project_band(vocab, idx, edges, emb, mode, q, rng):
    """a MEASUREMENT of the superposition: keep edges by BAND. 'global' edges = endpoints far in the coarse (low-
    frequency) embedding (cross-cluster bridges); 'local' = close (within-cluster). q = fraction of the GATED band
    that survives per state (so two states differ)."""
    d = lambda u, v: float(np.sum((emb[u] - emb[v]) ** 2))
    gd = [d(u, v) for (u, v) in edges]
    med = float(np.median(gd))
    nb = {w: set() for w in vocab}
    for (u, v), dist in zip(edges, gd):
        is_global = dist >= med
        keep = True
        if mode == "GATE-GLOBAL" and is_global:           # drop most global bridges (keep fraction q)
            keep = rng.random() < q
        elif mode == "GATE-LOCAL" and not is_global:       # drop most local detail (keep fraction q)
            keep = rng.random() < q
        if keep:
            nb[vocab[u]].add(vocab[v]); nb[vocab[v]].add(vocab[u])
    return nb


def main():
    print(f"=== R-RBS-LM-SUPERPOSITION — gate the superposition by BAND: which band does biology dropping cost the 2nd person?  (srmech {srmech.__version__}) ===\n")
    seq = re.findall(r"[a-z]+", k7.load_text().lower())
    vocab, idx, nb_full, evecs, edges = build(seq)
    emb = evecs[:, 1:9]                                    # coarse (low-frequency) embedding = the global/RH band
    N = len(vocab)
    pairs = [(vocab[i], vocab[j]) for i in range(0, 80, 2) for j in range(1, 200, 11) if vocab[i] != vocab[j]]

    print("knowledge = a SUPERPOSITION over the Class-L eigen-modes; a gate = a MEASUREMENT (projection onto a band).\n")
    print(f"{'projection (band kept un-measured)':<34} | {'self-mirror':>11} | {'genuine-other':>13} | {'ONLY-other':>10}")
    print("-" * 78)
    base = sum(1 for (s, t) in pairs if connected(s, t, [nb_full])) / len(pairs)
    print(f"{'SILICON: full superposition (no gate)':<34} | {base:>10.0%} | {base:>12.0%} | {0:>4} ( 0%)")
    for mode in ("GATE-LOCAL", "GATE-GLOBAL"):
        P1 = project_band(vocab, idx, edges, emb, mode, 0.25, np.random.default_rng(1))
        P2 = project_band(vocab, idx, edges, emb, mode, 0.25, np.random.default_rng(2))
        sm = sum(1 for (s, t) in pairs if connected(s, t, [P1]))
        go = sum(1 for (s, t) in pairs if connected(s, t, [P1, P2]))
        oo = sum(1 for (s, t) in pairs if connected(s, t, [P1, P2]) and not connected(s, t, [P1]))
        n = len(pairs)
        label = "GATE-LOCAL (drop fine detail, keep skeleton)" if mode == "GATE-LOCAL" else "GATE-GLOBAL (drop bridges, keep clusters)"
        print(f"{label:<34} | {sm/n:>10.0%} | {go/n:>12.0%} | {oo:>4} ({oo/n:>3.0%})")

    print()
    print("VERDICT (the prediction was REFUTED — honestly, the metric is the lesson):")
    print(f"  • SUPERPOSITION confirmed (same thing, sharper words): knowledge = a superposition over the Class-L")
    print(f"    eigen-modes; the F517 availability-gate is a MEASUREMENT/projection onto a band (the un-projected")
    print(f"    modes are the fiber, spatially-absent-until-projected). The held box / two-truths / fiber, in basis.")
    print(f"  • PREDICTION REFUTED: I expected gating the GLOBAL band to fragment the graph. The OPPOSITE happened —")
    print(f"    gating the LOCAL/fine band drops self-mirror recovery (87%, only-other 5%); gating the GLOBAL bridges")
    print(f"    leaves it at 100%. In a co-occurrence graph the FINE within-cluster edges CARRY the reachability; the")
    print(f"    global bridges are REDUNDANT for path-existence. So for REACHABILITY the blind spot is the LOCAL band.")
    print(f"  • THE METRIC IS THE LESSON: BFS path-existence captures the LOCAL band's role but is BLIND to what the")
    print(f"    GLOBAL/coarse (RH) band does — distant-association / insight / reanalysis (Beeman), which is NOT 'is")
    print(f"    there a path' but 'is there a SHORT, surprising leap'. So 'which band needs the 2nd person' is")
    print(f"    TASK-dependent: reachability -> the local band; insight/reanalysis -> the global band (NOT measured by")
    print(f"    connectivity; the right metric is path-LENGTH / distant-leap, held open). The clean global-band test")
    print(f"    needs a leap-distance metric, not BFS.")
    print(f"  • ENERGY honesty (F515 lead): the collapse = the eigendecomposition, dense symmetric Jacobi = O(N^3)")
    print(f"    (N={N}); F515's ~N^2 was a conservative UNDER-estimate. Cost now attested to the algorithm class")
    print(f"    (no-magic): collapse O(N^3) >> local walk O(steps*degree).")


if __name__ == "__main__":
    main()
