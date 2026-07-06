"""siona.graft — the Class-L LAPLACIAN graft-candidate scan (F1133): the passive SPECTRAL coherence detector.

Take a concept's relationship neighborhood, build the INDUCED subgraph among its neighbors (edges *between*
neighbors, not through the seed), and read the srmech Class-L Laplacian:

  * near-zero eigenvalues  → disconnected ISLANDS = missing-bridge graft candidates
  * algebraic connectivity λ₂ (low = near-split) + the FIEDLER vector → the weakest-bridge SEAM: the sense/topic
    fault-line, where a surgical graft belongs (measured: `bank` splits money↔place, `light` splits illumination↔physics)

The Fiedler COMMUNITY STRUCTURE is also the reference against which a CONTEXT-SHIFTING / epistatic mutation
(F1133) is detected: such a mutation re-coheres its NEIGHBORS so the whole re-coheres around it — invisible to a
local round-trip (the context moved with it), but visible HERE as a DRIFT of the community partition (and exposed
by the k=3 independent perspectives that did NOT drift together, F1131).

srmech-native Class-L (`dense_laplacian` / `jacobi_eigvals` / `fiedler_vector`). Pass any neighbor-lookup; the
co-occurrence graph (`relate.neighbors`, dense) gives cleaner communities than the star-shaped typed graph.
"""
from srmech.amsc import laplacian as L

__all__ = ["scan"]


def scan(seed, neighbors_of, K=40):
    """Class-L graft scan around ``seed`` using ``neighbors_of(word) -> iterable-of-words``. Returns the induced
    community structure: ``components`` (islands), ``alg_conn`` (λ₂; low = graft seam), ``islands`` (missing-bridge
    candidates), and the two Fiedler ``community_a``/``community_b`` (the sense/topic fault-line). ``None`` if the
    neighborhood is too small."""
    nbrs = list(neighbors_of(seed))[:K]
    if len(nbrs) < 4:
        return None
    idx = {w: i for i, w in enumerate(nbrs)}
    n = len(nbrs)
    edges = set()
    for w in nbrs:                                          # induced subgraph AMONG the neighbors
        for m in neighbors_of(w):
            if m in idx and idx[m] != idx[w]:
                a, b = idx[w], idx[m]
                edges.add((min(a, b), max(a, b)))
    edges = list(edges)
    lap = L.dense_laplacian(n, edges)
    evs = sorted(float(x) for x in L.jacobi_eigvals(lap))
    fied = [float(x) for x in L.fiedler_vector(lap)]
    deg = [0] * n
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    return {
        "seed": seed, "n": n, "edges": len(edges),
        "components": sum(1 for e in evs if e < 1e-6),      # disconnected islands
        "alg_conn": evs[1] if n > 1 else 0.0,               # λ₂ — low = near-split = graft seam
        "islands": [nbrs[i] for i in range(n) if deg[i] == 0],
        "community_a": [nbrs[i] for i in range(n) if fied[i] >= 0],
        "community_b": [nbrs[i] for i in range(n) if fied[i] < 0],
    }
