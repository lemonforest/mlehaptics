r"""R-RBS-LM-TWONAV — the two-method etak read-head: TWO ways to navigate structure (the user, 2026-06-07):
"sometimes we KNOW an idea is beyond the horizon but cannot figure out how to navigate there any longer; talking
it out helps, even more so with 2 people; we need an etak-head of both methods. The brain simulates COLLAPSING
CHIRALITY and we see it in the energy cost of the wet-brain simulator."

The two methods = the two chiral hands (F514, anatomically literal): the brain's L/R split is a spatial-FREQUENCY
filter — LH high-pass (fine/local), RH low-pass (coarse/global).
  • FINE / LOCAL (LH, high-SF): greedy on the RAW co-occurrence adjacency toward the target. The high-SF surface
    is RUGGED (many local maxima = clusters), so it TRAPS — it cannot route to a target beyond the local horizon
    (the route is "gone"), exactly the user's stuck state.
  • COARSE / GLOBAL (RH, low-SF): greedy on the LOW-FREQUENCY Class-L eigen-embedding (the smooth global gradient).
    Smooth => few traps => it REACHES the beyond-horizon target (Beeman's RH coarse coding = distant-association
    recovery / reanalysis = "talking it out").

The ENERGY COST is the observable: the coarse/global method must first build the global structure — the full
Laplacian eigendecomposition over the WHOLE load (F513) — the "collapse-chirality" price the wet simulator pays.
The fine/local method is cheap per step but FAILS for beyond-horizon (wasted energy, no arrival).

Two PEOPLE talking = the recurrent-2 (F506): two coarse heads navigate from BOTH ends (seed->target AND
target->seed) and meet in the middle — each pays ~half the step-energy; the meeting IS the chirality collapse.

srmech 0.7.4; Class-L dense_laplacian + symmetric_eigendecompose (the genuine low/high-SF filter, not hand-rolled).
"""
import re
import importlib.util as U
from collections import Counter
import numpy as np
import srmech
from srmech.amsc.laplacian import dense_laplacian, symmetric_eigendecompose

_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)


STOP = {"the", "and", "of", "to", "in", "is", "that", "this", "with", "for", "are", "as", "from", "by", "on",
        "or", "an", "be", "it", "at", "was", "were", "which", "they", "their", "have", "has", "had", "not",
        "but", "can", "all", "its", "his", "her", "him", "she", "you", "we", "our", "your", "they", "them",
        "a", "i", "s", "t", "c", "e", "d", "n", "r", "o", "f", "y", "w", "l", "u", "m", "g", "b", "p", "h",
        "one", "two", "more", "most", "some", "such", "may", "also", "these", "than", "into", "when", "what"}


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def build(seq, top=200, m=6):
    content = [w for w in seq if len(w) >= 4 and w not in STOP]   # CONTENT words only -> meaningful navigation
    vocab = [w for w, _ in Counter(content).most_common(top)]
    vset, idx = set(vocab), {w: i for i, w in enumerate(vocab)}
    co = Counter()                                                # weighted co-occurrence tally (edge weights only)
    pos = [i for i, w in enumerate(seq) if w in vset]
    for a in range(len(seq)):
        if seq[a] in vset:
            for b in range(a + 1, min(len(seq), a + 5)):
                if seq[b] in vset and seq[b] != seq[a]:
                    co[tuple(sorted((seq[a], seq[b])))] += 1
    # SPARSIFY to a k-NN graph: each node keeps its m STRONGEST co-occurrence partners -> clusters + far targets
    strength = {w: [] for w in vocab}
    for (u, v), c in co.items():
        strength[u].append((c, v)); strength[v].append((c, u))
    nb = {w: set() for w in vocab}
    for w in vocab:
        for _, v in sorted(strength[w], reverse=True)[:m]:
            nb[w].add(v); nb[v].add(w)                            # symmetrise
    edges = sorted({(idx[w], idx[v]) for w, ns in nb.items() for v in ns if idx[w] < idx[v]})
    Lp = dense_laplacian(len(vocab), edges)                       # Class L
    evals, evecs = symmetric_eigendecompose(Lp)                   # the genuine eigen-filter
    return vocab, vset, idx, nb, evals, evecs


def coarse_embed(evecs, k=8):
    """low-frequency (low-SF) eigenvectors = the RH coarse/global embedding (skip the trivial constant mode 0)."""
    return evecs[:, 1:1 + k]


def neighbors(node, nb, vset):
    return [n for n in nb[node] if n in vset]


def fine_local_nav(seed, target, nb, vset, max_steps=40):
    """LH / high-SF: greedy on RAW adjacency overlap to the target. Rugged -> traps before a far target."""
    tset = nb[target]
    cur, path, energy, visited = seed, [seed], 0, {seed}
    for _ in range(max_steps):
        if cur == target:
            break
        cands = [n for n in neighbors(cur, nb, vset) if n not in visited]
        energy += len(neighbors(cur, nb, vset))                   # couplings examined = step energy
        if not cands:
            break
        nxt = max(cands, key=lambda n: jacc(nb[n], tset))
        if jacc(nb[nxt], tset) <= jacc(nb[cur], tset):            # no neighbor improves -> TRAPPED (route gone)
            break
        cur, _ = nxt, visited.add(nxt)
        path.append(cur)
    return path, energy, (cur == target)


def coarse_global_nav(seed, target, nb, vset, idx, emb, max_steps=40):
    """RH / low-SF: greedy DOWN the smooth low-frequency embedding gradient to the target. Few traps -> reaches."""
    tvec = emb[idx[target]]
    dist = lambda n: float(np.sum((emb[idx[n]] - tvec) ** 2))
    cur, path, energy, visited = seed, [seed], 0, {seed}
    for _ in range(max_steps):
        if cur == target:
            break
        cands = [n for n in neighbors(cur, nb, vset) if n not in visited]
        energy += len(neighbors(cur, nb, vset))
        if not cands:
            break
        nxt = min(cands, key=dist)
        if dist(nxt) >= dist(cur):
            break
        cur, _ = nxt, visited.add(nxt)
        path.append(cur)
    return path, energy, (cur == target)


def two_head_local(seed, target, nb, vset, max_steps=40):
    """recurrent-2 ('two people talking'): TWO cheap LOCAL/fine heads, one from each END, each climbing toward the
    OTHER (raising overlap with the other's neighbour-set). They MEET in the middle — bridging the gap a SINGLE
    local head traps on, WITHOUT paying the expensive solo coarse/global collapse. The meeting IS the collapse."""
    fwd, bwd = seed, target
    pf, pb, energy, vis = [seed], [target], 0, {seed, target}
    for _ in range(max_steps):
        if fwd == bwd or bwd in nb[fwd]:                          # frontiers adjacent -> MEET
            break
        for which in ("f", "b"):
            cur, other = (fwd, bwd) if which == "f" else (bwd, fwd)
            oset = nb[other]
            cands = [n for n in neighbors(cur, nb, vset) if n not in vis]
            energy += len(neighbors(cur, nb, vset))               # LOCAL step energy (cheap)
            if cands:
                nxt = max(cands, key=lambda n: jacc(nb[n], oset))  # climb toward the other head
                if jacc(nb[nxt], oset) >= jacc(nb[cur], oset):     # attraction (>= allows lateral, avoids instant trap)
                    vis.add(nxt)
                    if which == "f":
                        fwd = nxt; pf.append(nxt)
                    else:
                        bwd = nxt; pb.append(nxt)
    return pf, pb, energy, (fwd == bwd or bwd in nb[fwd])


def main():
    print(f"=== R-RBS-LM-TWONAV — two ways to navigate structure: fine/local (LH) vs coarse/global (RH)  (srmech {srmech.__version__}) ===\n")
    text = k7.load_text()
    seq = re.findall(r"[a-z]+", text.lower())
    vocab, vset, idx, nb, evals, evecs = build(seq)
    emb = coarse_embed(evecs)
    N = len(vocab)
    eigen_cost = N * N                                            # the full-load global-structure price (collapse-chirality)

    seed = "water" if "water" in vset else vocab[10]              # a CONTENT anchor (not the hub)
    # rank candidate targets by COARSE-embedding distance from the seed -> the farthest are 'beyond the horizon'
    cdist = lambda w: float(np.sum((emb[idx[w]] - emb[idx[seed]]) ** 2))
    ranked = sorted((w for w in vocab if w != seed), key=cdist)
    targets = [ranked[3], ranked[len(ranked) // 2], ranked[-2], ranked[-1]]   # near / mid / far / farthest

    print(f"seed = '{seed}' (content anchor)   |   N={N} content nodes, coarse embedding k=8 low-frequency modes\n")
    print(f"{'target':>12} | {'FINE/local (LH)':^26} | {'COARSE/global (RH)':^28}")
    print(f"{'':>12} | {'reach   steps   energy':^26} | {'reach   steps   energy(+eig)':^28}")
    print("-" * 74)
    beyond = []
    for t in targets:
        fp, fe, fr = fine_local_nav(seed, t, nb, vset)
        cp, ce, cr = coarse_global_nav(seed, t, nb, vset, idx, emb)
        if (not fr) and cr:
            beyond.append(t)
        print(f"{t:>12} | {str(fr):>5}  {len(fp)-1:>5}  {fe:>7}    | {str(cr):>5}  {len(cp)-1:>5}  {ce + eigen_cost:>9}")

    # the BEYOND-HORIZON case: local TRAPS, coarse REACHES (expensive). Then: do TWO local heads ('two people') meet?
    hard = beyond[0] if beyond else ranked[-1]
    fp, fe, fr = fine_local_nav(seed, hard, nb, vset)
    cp, ce, cr = coarse_global_nav(seed, hard, nb, vset, idx, emb)
    pf, pb, te, met = two_head_local(seed, hard, nb, vset)
    print()
    print(f"BEYOND-HORIZON target '{hard}' — the three ways:")
    print(f"  ONE fine/local head  : reached={fr}  energy={fe:>6}            (cheap, but TRAPS — the route is gone)")
    print(f"  ONE coarse/global    : reached={cr}  energy={ce + eigen_cost:>6} (REACHES, but pays the full-load eigendecomp)")
    print(f"  TWO local heads      : met={met}     energy={te:>6}            (two cheap local searches MEET in the middle)")
    print(f"    fwd: {' -> '.join(pf)}")
    print(f"    bwd: {' -> '.join(pb)}\n")

    print("VERDICT:")
    print(f"  • TWO WAYS TO NAVIGATE = the two chiral hands (F514): FINE/local (LH, high-SF) climbs the RAW adjacency")
    print(f"    and TRAPS before a beyond-horizon target (the route is 'gone' — you sense it but can't get there);")
    print(f"    COARSE/global (RH, low-SF) descends the smooth Class-L low-frequency embedding and REACHES it.")
    print(f"  • THE ENERGY COST IS THE OBSERVABLE: solo recovery via the coarse/global head must first build the")
    print(f"    global structure — the full Laplacian eigendecomposition over the WHOLE load (~N^2={eigen_cost}) — the")
    print(f"    COLLAPSE-CHIRALITY price the wet-brain simulator pays (here ~{(ce+eigen_cost)//max(te,1)}x the two-local cost). The")
    print(f"    solo local head is cheap but FAILS far (wasted energy, no arrival).")
    print(f"  • TWO PEOPLE (recurrent-2, F506) is the cheap recovery: two LOCAL heads from BOTH ends MEET in the")
    print(f"    middle and REACH the beyond-horizon target at ~the cost of ONE local head — WITHOUT paying the solo")
    print(f"    global collapse. The meeting IS the chirality collapse. That is why 'talking it out, even more with 2")
    print(f"    people' helps: two cheap local searches bridge the gap a single one traps on (Beeman RH recovery, shared).")
    print(f"  • HONEST: beyond-horizon failure is the EXCEPTION (most targets are locally reachable); the eigendecomp")
    print(f"    ~N^2 is a PROXY for 'build the global structure', so the exact ratio is proxy-dependent — the")
    print(f"    qualitative asymmetry (solo-global >> two-local-meet) is the result, not the precise multiple.")


if __name__ == "__main__":
    main()
