"""siona.dataset — the DATASET-AGNOSTIC describe (F1167/F1168): couple()'s residue applied to ANY statistical
relational dataset, not just language.

`couple()`'s residue-read is pure spectral structure (signed Class-L over edges + weights, `srmech.amsc.laplacian`);
it does not know what "language" is. So a language is just a special case of a relational dataset, and the SAME
read gives the SPINE (structurally-central items) and the COMMUNITIES (clusters) of any dataset expressible as a
co-incidence / correlation / similarity graph — gene co-expression, citation networks, planetary physics, market
baskets. Proven: the same residue recovers planted clusters from an abstract graph (F1167) and splits the solar
system by physical structure (F1168).

The split that matters for what-goes-upstream: the ENGINE (build a signed graph → one eigendecomposition → spine +
communities) is domain-free MATH; the FEATURE-ENCODING (how a dataset becomes a coupling graph) is DOMAIN
KNOWLEDGE and stays in the consumer. This module carries the general feature→graph→describe consumer glue; the
engine underneath is srmech Class-L (a candidate to live upstream — see the research notebook's srmech-upstream note).

Sparse, numpy-free, srmech-native (signed Class-L).
"""
__all__ = ["residue", "describe"]


def _znorm(cols):
    out = []
    for col in cols:
        mu = sum(col) / len(col)
        sd = (sum((x - mu) ** 2 for x in col) / len(col)) ** 0.5 or 1.0
        out.append([(x - mu) / sd for x in col])
    return [list(r) for r in zip(*out)]                     # back to row-per-item


def residue(items, features, *, spine_k=3):
    """The couple()-style RESIDUE over a statistical dataset (F1168): ``items`` = names, ``features`` = a dict
    ``name -> [feature…]`` (numeric). Z-normalises the columns, couples SIMILAR items (+1) and REPELS very-
    DIFFERENT ones (−1, the same chirality sign as a case-role or an antonym), runs ONE `symmetric_eigendecompose`
    of the signed Class-L graph, and reads the SPINE (dominant-mode central items) + COMMUNITIES (Fiedler split)
    off the residue — the SAME read as `couple()`/`analytic.residue`, sourced from feature-similarity. Returns
    ``{"spine", "communities"}`` or ``None`` (< 3 items)."""
    from srmech.amsc import laplacian as L
    n = len(items)
    if n < 3:
        return None
    cols = list(zip(*[features[it] for it in items]))
    Z = _znorm(cols)

    def dist(i, j):
        return sum((Z[i][k] - Z[j][k]) ** 2 for k in range(len(Z[i]))) ** 0.5

    ds = sorted(dist(i, j) for i in range(n) for j in range(i + 1, n))
    lo, hi = ds[len(ds) // 4], ds[3 * len(ds) // 4]         # quartile thresholds (attested to the data, not tuned)
    edges, weights = [], []
    for i in range(n):
        for j in range(i + 1, n):
            d = dist(i, j)
            if d < lo:
                edges.append((i, j)); weights.append(1.0)   # similar → attract
            elif d > hi:
                edges.append((i, j)); weights.append(-1.0)  # very different → repel (chirality)
    if not edges:
        return None
    lap = L.signed_laplacian(n, edges, weights)
    evals, evecs = L.symmetric_eigendecompose(lap)
    evals = [float(x) for x in evals]
    order = sorted(range(n), key=lambda i: evals[i])
    fied = order[1]                                          # Fiedler split = the communities (residue)
    comm = {0: [], 1: []}
    for i in range(n):
        comm[0 if float(evecs[i][fied]) >= 0 else 1].append(items[i])
    dom = order[-1]                                          # dominant mode = the structurally-central spine
    spine = [items[i] for i in sorted(range(n), key=lambda r: -(float(evecs[r][dom]) ** 2))[:spine_k]]
    return {"spine": spine, "communities": [comm[0], comm[1]]}


def describe(items, features, *, label="dataset"):
    """A first structured description of a statistical dataset's STRUCTURE from its relational residue (F1168):
    the SPINE = structurally-central items, the COMMUNITIES = the clusters. Domain-free — the caller supplies the
    feature-encoding (the domain knowledge); the residue read is universal. ``None`` if < 3 items."""
    r = residue(items, features)
    if not r:
        return None
    out = ["This %s clusters into two groups by structure." % label]
    for g in r["communities"]:
        if g:
            out.append("One group: %s." % ", ".join(g))
    out.append("Structurally central: %s." % ", ".join(r["spine"]))
    return " ".join(out)
