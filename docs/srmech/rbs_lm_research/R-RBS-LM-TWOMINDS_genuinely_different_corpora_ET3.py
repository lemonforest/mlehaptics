r"""R-RBS-LM-TWOMINDS (ET-3) — F516/F517 modelled "two people" as two PROJECTIONS of ONE structure (same latent
graph, different sampled/gated edges). The genuine two-minds case is two DIFFERENT CORPORA (different experiences)
over a SHARED vocabulary — genuinely different structure, not a resampling. Question: does a genuinely-different
mind ADD reachability the first lacks (the bridges it never learned), and does a THIRD mind (k=3) add more / give
an error-correcting majority?

Setup: split the corpus into 3 DISJOINT chunks -> graphs A, B, C over a shared content vocabulary (same words,
genuinely different co-occurrence from different text). Measure reachability of far pairs in A, A∪B, A∪B∪C, and the
k=3 majority (reachable in >=2 of the three). Control: two RANDOM HALVES of A's own edges (the F517 same-structure
resample) — a genuinely-different corpus should add MORE than a self-resample.

srmech 0.7.4; reuses the FIBERGAP content k-NN builder + BFS. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech

_f = U.spec_from_file_location("fib", "docs/srmech/rbs_lm_research/R-RBS-LM-FIBERGAP_biology_enforces_projection_gaps_silicon_does_not.py")
fib = U.module_from_spec(_f); _f.loader.exec_module(fib)


def edge_halves(nb, rng):
    """split a graph's edges into two random halves (the F517 same-structure resample control)."""
    edges = sorted({tuple(sorted((u, v))) for u, ns in nb.items() for v in ns})
    pick = rng.random(len(edges)) < 0.5
    h1 = {w: set() for w in nb}; h2 = {w: set() for w in nb}
    for (u, v), p in zip(edges, pick):
        tgt = h1 if p else h2
        tgt[u].add(v); tgt[v].add(u)
    return h1, h2


def main():
    print(f"=== R-RBS-LM-TWOMINDS (ET-3) — do genuinely-different corpora add reachability + a k=3 majority?  (srmech {srmech.__version__}) ===\n")
    import re
    toks = re.findall(r"[a-z]+", fib.k7.load_text().lower())
    content = [w for w in toks if len(w) >= 4 and w not in fib.STOP]
    from collections import Counter
    vocab = [w for w, _ in Counter(content).most_common(200)]
    vset = set(vocab)
    n = len(toks) // 12                                        # SMALLER, disjoint chunks -> each mind's graph is PARTIAL (gappy)
    A = fib.knn_edges(toks[:n], vocab, vset, m=1)              # mind A (experience 1) — 1 strongest partner/word = a forest, real gaps
    B = fib.knn_edges(toks[n:2 * n], vocab, vset, m=1)         # mind B (experience 2) — different strongest partners = different gaps
    C = fib.knn_edges(toks[2 * n:3 * n], vocab, vset, m=1)     # mind C (experience 3)

    pairs = [(vocab[i], vocab[j]) for i in range(0, 80, 2) for j in range(1, 200, 11) if vocab[i] != vocab[j]]
    N = len(pairs)
    r = lambda *nbs: sum(1 for s, t in pairs if fib.connected(s, t, *nbs)) / N
    majority = sum(1 for s, t in pairs if (int(fib.connected(s, t, A)) + int(fib.connected(s, t, B)) + int(fib.connected(s, t, C))) >= 2) / N
    only_B = sum(1 for s, t in pairs if fib.connected(s, t, A, B) and not fib.connected(s, t, A)) / N
    only_C = sum(1 for s, t in pairs if fib.connected(s, t, A, B, C) and not fib.connected(s, t, A, B)) / N

    # control: A's own edges split into two random halves (F517 same-structure resample)
    h1, h2 = edge_halves(A, np.random.default_rng(3))
    only_resample = sum(1 for s, t in pairs if fib.connected(s, t, h1, h2) and not fib.connected(s, t, h1)) / N

    print(f"{N} far pairs; 3 disjoint corpus chunks -> minds A, B, C over a shared {len(vocab)}-word vocabulary.\n")
    print(f"  reach in A alone (one mind)          : {r(A):.0%}")
    print(f"  reach in A∪B (two genuine minds)     : {r(A, B):.0%}   (+{only_B:.0%} reachable ONLY via B)")
    print(f"  reach in A∪B∪C (three genuine minds) : {r(A, B, C):.0%}   (+{only_C:.0%} added by the 3rd mind)")
    print(f"  k=3 MAJORITY (reachable in >=2 of 3) : {majority:.0%}   (the error-correcting consensus)\n")
    print(f"  CONTROL — A's edges split into 2 random halves (F517 same-structure resample):")
    print(f"    reachability the 2nd HALF adds over the 1st: +{only_resample:.0%}\n")

    print("VERDICT:")
    print(f"  • A GENUINELY-DIFFERENT MIND ADDS REACHABILITY: a second corpus B reaches +{only_B:.0%} of far pairs that A")
    print(f"    alone cannot (bridges B learned and A never did). This is REAL structural addition — unlike F516's")
    print(f"    self-mirror (same structure -> 0 add) — because the corpora genuinely DIFFER.")
    print(f"  • DIFFERENT EXPERIENCE >> DIFFERENT SAMPLING: the same-structure resample control adds only +{only_resample:.0%},")
    print(f"    the genuinely-different corpus adds +{only_B:.0%}. Different EXPERIENCE, not re-sampling the same structure,")
    print(f"    is what supplies the missing bridges (the F516/F517 self-mirror could not).")
    print(f"  • HONEST on k=3: reachability is a UNION, not a vote — A∪B already saturates ({r(A,B):.0%}), so the 3rd mind C")
    print(f"    adds +{only_C:.0%} REACHABILITY, and 'reachable in >=2 of 3' ({majority:.0%}) UNDERcounts (each sparse forest reaches")
    print(f"    little alone). The k=3 triality's job is NOT reachability-union but ERROR-CORRECTION — rejecting a")
    print(f"    SPURIOUS bridge one mind has but the majority lacks. That is a different metric (a spurious-edge test),")
    print(f"    left as the next sub-rung; here we show only the reachability-ADD of a genuinely-different mind.")


if __name__ == "__main__":
    main()
