"""siona.story — classify character ARCHETYPES by their structural signature in a story's interaction graph
(F1078). The same move as the whole Form-space arc (F1075/F1076/F1077): a character's archetype FALLS OUT of
its configuration — here, its structural signature in the graph of who-interacts-with-whom:

  * ``centrality``  — degree fraction: importance / how much the story turns on this character.
  * ``curvature``   — clustering coefficient (F1077): tight consensus-cluster (support) vs bridge (mediator).
  * ``community``   — Class-L sign-code (F1050): which "side" the character sits on.
  * ``span``        — how many communities the character touches: a bridge spans many.

Named regions of that signature-space are the ROLES (protagonist-hub / antagonist-hub / bridge / support /
minor) — the Plato-Forms move (F1076) applied to characters. Finer archetypes (mentor vs trickster; the full
Jungian / D&D set) need the further Form-space axes (chirality / valence, F1073) — flagged, not faked.

srmech-native: Class-L ``dense_laplacian`` + ``symmetric_eigendecompose`` for the communities; the rest is
integer graph structure. numpy-free.
"""
from srmech.amsc import laplacian as _L

__all__ = ["character_signatures", "classify_story"]


def character_signatures(nodes, edges):
    """Per-character structural signature from the interaction graph (``nodes``: labels; ``edges``: (a, b) pairs)."""
    n = len(nodes)
    idx = {c: i for i, c in enumerate(nodes)}
    und = {i: set() for i in range(n)}
    for a, b in edges:
        i, j = idx[a], idx[b]
        if i != j:
            und[i].add(j); und[j].add(i)
    deg = [len(und[i]) for i in range(n)]
    maxd = max(deg) or 1
    curv = []                                                  # curvature = clustering (F1077)
    for i in range(n):
        nb = list(und[i])
        if len(nb) < 2:
            curv.append(0.0)
        else:
            links = sum(1 for a in range(len(nb)) for b in range(a + 1, len(nb)) if nb[b] in und[nb[a]])
            curv.append(links / (len(nb) * (len(nb) - 1) / 2.0))
    edge_set = sorted({(min(idx[a], idx[b]), max(idx[a], idx[b])) for a, b in edges if idx[a] != idx[b]})
    evals, evecs = _L.symmetric_eigendecompose(_L.dense_laplacian(n, edge_set, [1.0] * len(edge_set)))
    sb = lambda x: 1 if x > 0 else 0                           # Class-K sign-branch → the community sign-code
    code = [(sb(evecs[i, 1]) << 1) | sb(evecs[i, 2]) for i in range(n)]   # Class-L community (F1050)
    span = [len(set(code[j] for j in und[i]) | {code[i]}) for i in range(n)]
    return {c: {"centrality": deg[i] / maxd, "curvature": curv[i], "community": code[i],
                "span": span[i], "degree": deg[i]} for i, c in enumerate(nodes)}


def _betweenness(nodes, edges):
    """Betweenness centrality (Brandes, unweighted) — the discriminator naive degree/curvature/span misses
    (F1078): a BRIDGE (mentor/trickster) has high betweenness + low degree; a HUB (hero/shadow) has high degree.
    Heroes are also high-SPAN, so span alone mislabels them as bridges — betweenness is what separates them."""
    n = len(nodes); idx = {c: i for i, c in enumerate(nodes)}
    und = {i: set() for i in range(n)}
    for a, b in edges:
        i, j = idx[a], idx[b]
        if i != j:
            und[i].add(j); und[j].add(i)
    bet = [0.0] * n
    for src in range(n):
        dist = [-1] * n; sigma = [0] * n; pred = [[] for _ in range(n)]
        dist[src] = 0; sigma[src] = 1; queue = [src]; order = []; qi = 0
        while qi < len(queue):
            v = queue[qi]; qi += 1; order.append(v)
            for w in und[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1; queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]; pred[w].append(v)
        delta = [0.0] * n
        for w in reversed(order):
            for v in pred[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != src:
                bet[w] += delta[w]
    norm = ((n - 1) * (n - 2)) if n > 2 else 1
    return {c: bet[i] / norm for i, c in enumerate(nodes)}


def _role(s, betw, majority, hub_deg, bet_floor):
    """Named region of the (degree, betweenness, curvature, community) signature-space → a structural ROLE
    (F1078). Finer archetype (mentor vs trickster) needs an added axis (chirality/valence) — flagged, not faked."""
    if s["degree"] <= 1:
        return "minor"
    if s["degree"] >= hub_deg:                                 # a HUB (identified by degree, not span)
        return "protagonist-hub" if s["community"] == majority else "antagonist-hub"
    if betw >= bet_floor and s["curvature"] < 0.5:             # high betweenness + not a tight cluster = a BRIDGE
        return "bridge"                                        # (mentor vs trickster: needs chirality/valence axis)
    if s["curvature"] >= 0.5:
        return "support"                                       # tight consensus-cluster with a hub
    return "minor"


def classify_story(nodes, edges):
    """Classify every character's ROLE from its structural signature. Returns ``(roles: {char: role}, sigs)``.
    Uses degree to find the two HUBS (protagonist + antagonist) and betweenness to find the BRIDGES —
    the naive degree/curvature/span classifier fails because hubs are high-span too (F1078)."""
    sig = character_signatures(nodes, edges)
    betw = _betweenness(nodes, edges)
    for c in nodes:
        sig[c]["betweenness"] = betw[c]
    prot = max(nodes, key=lambda c: (sig[c]["degree"], sig[c]["centrality"]))
    majority = sig[prot]["community"]
    degs = sorted((sig[c]["degree"] for c in nodes), reverse=True)
    hub_deg = degs[1] if len(degs) > 1 else degs[0]            # the two highest-degree nodes are the hubs
    nonhub_bet = sorted((betw[c] for c in nodes if sig[c]["degree"] < hub_deg), reverse=True)
    bet_floor = (nonhub_bet[0] * 0.5) if nonhub_bet else 1e9   # bridges = the high-betweenness non-hubs
    return {c: _role(sig[c], betw[c], majority, hub_deg, bet_floor) for c in nodes}, sig


def sandroing_strokes(nodes, edges):
    """Can this noun-graph be drawn as ONE sandroing? The ATTESTED rule (UNESCO 00073, Vanuatu sand drawings):
    a unicursal line that STARTS AND ENDS AT THE SAME POINT and NEVER TAKES THE SAME PATH TWICE = an EULERIAN
    CIRCUIT — exists iff the graph is connected and EVERY node has EVEN degree (Euler's theorem). This is the
    precise, measurable answer to "can sandroing capture a story of multiple nouns" (F1080, refines F1079):
    the minimum # of continuous strokes = ``max(1, odd_degree_count // 2)``. Returns
    ``{"strokes": k, "odd_degree_nodes": [...], "one_sandroing": bool}`` — k=1 iff a single closed sandroing draws it."""
    idx = {c: i for i, c in enumerate(nodes)}
    deg = {c: 0 for c in nodes}
    for a, b in edges:
        if idx[a] != idx[b]:
            deg[a] += 1; deg[b] += 1
    odd = [c for c in nodes if deg[c] % 2 == 1]
    strokes = max(1, len(odd) // 2)                            # k disjoint strokes cover k pairs of odd ends
    return {"strokes": strokes, "odd_degree_nodes": odd, "one_sandroing": (len(odd) == 0)}
