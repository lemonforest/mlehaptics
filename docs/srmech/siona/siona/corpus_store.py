"""siona.corpus_store — the directed Class-L corpus genome as Siona's RELATIONAL read, DEMAND-LOADED (#231, F1233/F1235).

The genome is the DNA (the store — the directed Laplacian: metric + charge, F1216/F1221). Reading it is GENE-EXPRESSION
(EPH / F1095/F1112): a query EXPRESSES only the queried token's neighbourhood on demand, it does NOT inflate all 39M
edges into RAM at startup. So we build ONCE a mmap-able per-token expression layer under <genome_dir>/reads/ —
  adj.bin : per-token neighbour records (int32 neighbour_id, metric, charge), sorted by metric desc, mmap'd
  adj.idx : token_id -> (byte_offset, count)          vocab.txt : the token strings
— then open() is INSTANT (mmap, no decode) and read(token) pages in only that token's bytes. The store stays the
genome; reads/ is a derived, recomputable READ accelerator (top-K is a query read, never a storage cut — F708/F748).

Native srmech rc253; no numpy; store = the Laplacian + fiber, not Klein-4 HVs.
"""
import json
import mmap
import struct
from pathlib import Path

from srmech.amsc import genome as _G
from srmech.amsc import hdc as _H
from srmech.amsc import cascade as _K            # Class-K magnitude (never the ALU magnitude-builtin) for Fiedler
from srmech.amsc import rational as _R           # rational.sqrt for the normalized-cut Fiedler (stay-rational)

LEAF = 64
COUPLE = _H.klein4_random(LEAF, seed=1080)          # the store's canonical coupling (the sandroing/UNESCO 00073 seed)
_REC = struct.Struct("<iii")                         # a neighbour record: (neighbour_id, metric, charge-from-this-view)
_IDX = struct.Struct("<QI")                          # an index record: (byte_offset uint64, count uint32)

# --- the tome-TREE de-lens band (F782/F786 ETAKNAV, at corpus scale): drop the top-df HUBS (function-words /
#     markup), keep a CONTENT band, IDF-weight + sparsify, then recursive sparse-Fiedler bisection = clumps-of-clumps.
H_DROP = 250            # the RIDE de-lens: skip the top-count hubs (markup + function words) DURING a ride
TREE_DROP = 40          # the TREE band drops only the EXTREME markup hubs, so frequent CONTENT topics (water /
                        #   music / country) stay navigable — count alone can't tell a frequent content word from a
                        #   function word (F983), so keep them in the tree; the ride still skips the full H_DROP set
K_KEEP = 5000           # the content band the tome-tree is built over (wider -> rarer topics like vanuatu land in it)
K_NBR = 20              # sparsify each content node to its top-K_NBR IDF-weighted edges (genuine sparsity)
MAXTOME = 12            # a clump becomes a leaf tome at this size
T_ITERS = 150           # Fiedler power-iteration cap


def load(genome_dir, the_one=None):
    """Decode the whole genome -> (vocab, graph). The CANONICAL read (no external metadata; self-describing format
    stops at n_edges; vocab tail trimmed to vocab_size). Heavy at corpus scale — used to BUILD reads/, then not again."""
    the_one = COUPLE if the_one is None else the_one
    chg, _c, _l = _G.genome_load(str(genome_dir), labels=["graph"], the_one=the_one)
    n = len(list(_G.kernel_unpack(chg, the_one)))
    graph = _G.kernel_to_graph(chg, the_one, n)
    chv, _c2, _l2 = _G.genome_load(str(genome_dir), labels=["vocab"], the_one=the_one)
    vs = list(_G.kernel_unpack(chv, the_one))
    b = bytearray()
    for i in range(0, len(vs) - 3, 4):
        b.append(vs[i] + (vs[i + 1] << 2) + (vs[i + 2] << 4) + (vs[i + 3] << 6))
    vocab = b.decode("utf-8", errors="ignore").split("\n")[:graph["vocab_size"]]
    return vocab, graph


def _adjacency(edges, weights, charges):
    adj = {}
    for (i, j), w, c in zip(edges, weights, charges):
        adj.setdefault(i, []).append((j, w, c))
        adj.setdefault(j, []).append((i, w, -c))     # from j's view the direction (charge) flips
    return adj


def build_reads(genome_dir, *, vocab=None, edges=None, weights=None, charges=None, the_one=None):
    """Build the demand-load expression layer <genome_dir>/reads/ ONCE. Pass the (vocab, edges, weights, charges)
    arrays for speed (e.g. straight from the source), or omit them to decode the genome (canonical). Returns |vocab|."""
    if edges is None:
        vocab, graph = load(genome_dir, the_one)
        edges, weights, charges = graph["edges"], graph["weights"], graph["charges"]
    adj = _adjacency(edges, weights, charges)
    rd = Path(genome_dir) / "reads"
    rd.mkdir(parents=True, exist_ok=True)
    with open(rd / "adj.bin", "wb") as fb, open(rd / "adj.idx", "wb") as fi:
        off = 0
        for t in range(len(vocab)):
            recs = sorted(adj.get(t, ()), key=lambda x: -x[1])       # metric desc so the top-of-read is the file prefix
            fi.write(_IDX.pack(off, len(recs)))
            for (j, w, c) in recs:
                fb.write(_REC.pack(j, w, c))
                off += _REC.size
    (rd / "vocab.txt").write_text("\n".join(vocab), encoding="utf-8")
    return len(vocab)


def _attach_tree(h, genome_dir):
    """Attach the tome-tree (if built) to a handle: h['tree'] for find/ride/web-hop, h['hub_ids'] for the ride
    de-lens. Additive — no tree means plain rides (no de-lens), navigation returns None."""
    tr = _open_tree(genome_dir, h["vindex"])
    if tr is not None:
        h["tree"] = tr
        h["hub_ids"] = tr["hub_ids"]
    return h


def open_demand(genome_dir):
    """Open the reads/ layer INSTANTLY: load the small idx + vocab, mmap adj.bin (no decode; pages in per query)."""
    rd = Path(genome_dir) / "reads"
    vocab = (rd / "vocab.txt").read_text(encoding="utf-8").split("\n")
    idx = (rd / "adj.idx").read_bytes()
    fb = open(rd / "adj.bin", "rb")
    mm = mmap.mmap(fb.fileno(), 0, access=mmap.ACCESS_READ)
    return _attach_tree({"mode": "demand", "vocab": vocab, "vindex": {t: n for n, t in enumerate(vocab)},
                         "idx": idx, "mm": mm, "_fb": fb}, genome_dir)


def prepare(genome_dir):
    """Return a read handle. reads/ present -> DEMAND-LOAD (instant open, gene_express per query). Else (a small
    corpus) -> full in-RAM (cheap). Same read() API either way. The tome-tree (tree/) is attached if built."""
    if (Path(genome_dir) / "reads" / "adj.idx").exists():
        return open_demand(genome_dir)
    vocab, graph = load(genome_dir)
    return _attach_tree({"mode": "ram", "vocab": vocab, "vindex": {t: n for n, t in enumerate(vocab)},
                         "adj": _adjacency(graph["edges"], graph["weights"], graph["charges"])}, genome_dir)


def read(h, token, k=6):
    """The RELATIONAL read, gene-expressed: what co-occurs with `token`, top-k by metric, with direction (-> / <-).
    DEMAND mode pages in only this token's bytes from the mmap (records are metric-sorted, so the first k ARE the top)."""
    ti = h["vindex"].get(token)
    if ti is None:
        return []
    return [(w, "->" if c >= 0 else "<-", h["vocab"][j]) for (j, w, c) in _records(h, ti, k)]


def _records(h, ti, limit):
    """Up to `limit` STRONGEST neighbour records (neighbour_id, metric, charge) for token-id ti, metric-desc.
    Bounded — the etak RIDE follows STRONG coupling, i.e. the top edges (a read, never the whole node degree, so a
    hub token doesn't page its entire adjacency). DEMAND pages the slice from the mmap; RAM sorts the in-core list."""
    if h["mode"] == "demand":
        off, cnt = _IDX.unpack_from(h["idx"], ti * _IDX.size)
        return [_REC.unpack_from(h["mm"], off + m * _REC.size) for m in range(min(cnt, limit))]
    return sorted(h["adj"].get(ti, []), key=lambda t: -t[1])[:limit]


_SCAN = 48                                              # per-hop read window (the strongest coupling sits at the top)


def etak_walk(h, token, steps=6, sense="fwd"):
    """The ETAK RIDE (F786/F791 navigation, at demand-load scale) — NAVIGATE the directed store by MOVING THE
    REFERENCE FRAME: from `token`, hop to the strongest chirality-consistent neighbour, `steps` times, riding the
    directed coupling. This is the store's REASON FOR BEING (metric + directed CHARGE); a flat 1-hop read() throws
    the charge axis away after one step. `sense='fwd'` follows the forward charge (c>=0 : what this token LEADS TO);
    `'bwd'` follows the backward charge (c<0 : what LEADS HERE) — the two chiral fronts (F990, overtone/undertone).
    Returns the path of DISTINCT tokens [token, w1, w2, ...]; a visited-set halts the co-occurrence loop. The charge
    sign IS the Class-C which-way (never the ALU magnitude-builtin); metric-desc records mean the first admissible
    hop is the strongest. Pure-Python, srmech-native store; the fuller tome-TREE find->ride->web-hop (Fiedler,
    ETAKNAV) is the heavier OFFLINE extension over a clustered store."""
    ti = h["vindex"].get(token)
    if ti is None:
        return [token]
    want_fwd = (sense == "fwd")
    hubs = h.get("hub_ids") or frozenset()               # the tome-tree's de-lens band: skip markup / function-word hubs
    path, seen, cur = [token], {ti}, ti
    for _ in range(steps):
        nxt = None
        for (j, w, c) in _records(h, cur, _SCAN):       # metric-desc: first admissible IS the strongest coupling
            if j in seen or j in hubs:                   # skip visited + de-lensed hubs (markup / function words)
                continue
            if (c >= 0) == want_fwd:                      # Class-C chirality sign = the which-way (no abs)
                nxt = j
                break
        if nxt is None:
            break
        seen.add(nxt)
        path.append(h["vocab"][nxt])
        cur = nxt
    return path


# ============================================================================================================
# The tome-TREE find -> ride -> web-hop navigation (F786/F791 ETAKNAV, cached like reads/): a de-lensed Fiedler
# bisection over the content band = clumps-of-clumps (the TREE); the cut edges between leaf tomes = the WEB. Built
# ONCE offline (build_tree), then FIND (descend the tree to a token's tome), RIDE (the tome's coherent members),
# WEB-HOP (cross the strongest bridge to an adjacent tome) are cheap reads. Navigate by MOVING THE REFERENCE FRAME.
# ============================================================================================================
def fiedler_sparse(nodes, adj, t_iters=T_ITERS):
    """Normalized-cut power-iteration Fiedler vector (ETAKNAV; verified 100% vs the dense normalized Fiedler,
    F785). srmech-native: rational.sqrt for the degree-normalization, Class-K magnitude for the pin (never abs).
    `adj`: {node: {nbr: weight}}. Returns the Fiedler component per node (its SIGN is the bisection)."""
    n = len(nodes)
    if n < 2:
        return [0.0] * n
    pos = {g: i for i, g in enumerate(nodes)}
    nbr = [[] for _ in range(n)]
    deg = [0.0] * n
    for i, g in enumerate(nodes):
        for h2, w in adj[g].items():
            j = pos.get(h2)
            if j is not None:
                nbr[i].append((j, w))
                deg[i] += w
    # coerce the Class-N sqrt into the NUMERICAL spectral layer (float). The Fiedler vector is a real-valued
    # eigenvector — the "continuous" projection of the discrete Laplacian, exactly what srmech's own
    # symmetric_eigendecompose returns as float. Keeping rational.sqrt's exact Q through the 150-iteration power
    # loop makes every op unbounded big-integer arithmetic (denominators explode -> the O(minutes) hang).
    s = [(1.0 / float(_R.sqrt(deg[i]))) if deg[i] > 0 else 0.0 for i in range(n)]
    p = [float(_R.sqrt(deg[i])) for i in range(n)]
    pn2 = sum(x * x for x in p)
    if pn2 <= 0:
        return [0.0] * n
    pnorm = float(_R.sqrt(pn2))
    p = [x / pnorm for x in p]
    v = [((k * 1103515245 + 12345) % 2147483648) / 2147483648.0 - 0.5 for k in range(n)]   # order-independent (F791.1)
    dot = sum(v[i] * p[i] for i in range(n))
    v = [v[i] - dot * p[i] for i in range(n)]
    prev_sign, stable = None, 0
    for it in range(t_iters):
        tmp = [s[j] * v[j] for j in range(n)]
        u = [v[i] + s[i] * sum(w * tmp[j] for j, w in nbr[i]) for i in range(n)]
        dot = sum(u[i] * p[i] for i in range(n))
        u = [u[i] - dot * p[i] for i in range(n)]
        # L-inf magnitude = the Class-K pin-slot |·| via the SIGN-PARTITION (max of the +side and the negated
        # -side) — ONCE per iteration, not a per-element cascade call (that was 7.6M calls -> the O(N) hot-loop
        # bottleneck). No ALU magnitude-builtin; the sign split IS the pin-slot-at-zero + reorient composition, batched.
        mx = max(max(u, default=0.0), -min(u, default=0.0))
        if mx <= 0:
            break
        v = [x / mx for x in u]
        sign = tuple(1 if x >= 0 else 0 for x in v)
        if sign == prev_sign and it >= 20:
            stable += 1
            if stable >= 5:
                break
        else:
            stable = 0
        prev_sign = sign
    return v


def _cluster(nodes, adj, depth=0):
    """Recursive sparse-Fiedler bisection -> the tome TREE (clumps-of-clumps, F780). BALANCED: if the Fiedler
    sign-cut is very unbalanced (degenerate on a poorly-connected content graph), split at the MEDIAN of the
    Fiedler value instead, so every split is >=~half -> O(N log N) recursion (guards the peel-one-node O(N^2)
    pathology). A node dict is {members, children|None}; a leaf (<=MAXTOME or depth cap) has children=None."""
    if len(nodes) <= MAXTOME or depth > 60:
        return {"members": nodes, "children": None}
    fv = fiedler_sparse(nodes, adj)
    left = [nodes[i] for i in range(len(nodes)) if fv[i] < 0]
    right = [nodes[i] for i in range(len(nodes)) if fv[i] >= 0]
    if min(len(left), len(right)) < max(2, len(nodes) // 10):     # too unbalanced -> a ~50/50 median cut
        order = sorted(range(len(nodes)), key=lambda i: fv[i])
        mid = len(nodes) // 2
        left = [nodes[order[i]] for i in range(mid)]
        right = [nodes[order[i]] for i in range(mid, len(nodes))]
    if not left or not right:
        return {"members": nodes, "children": None}
    return {"members": nodes, "children": [_cluster(left, adj, depth + 1), _cluster(right, adj, depth + 1)]}


def _write_tree(genome_dir, vocab, content_ids, cand, hub_ids, degmap, k_nbr):
    """Shared tail: sparsify the candidate content graph -> recursive Fiedler bisection (tree) -> leaves (tomes) +
    word->tome map + inter-tome web, written under <genome_dir>/tree/. `degmap` (id -> importance) orders labels."""
    adj = {p: {} for p in range(len(content_ids))}
    for p in range(len(content_ids)):
        for q, ww in sorted(cand[p].items(), key=lambda kv: kv[1], reverse=True)[:k_nbr]:
            adj[p][q] = ww
            adj[q][p] = ww
    import sys
    sys.setrecursionlimit(100000)
    tree = _cluster(list(range(len(content_ids))), adj)
    leaves = []

    def _collect(node, depth, path):
        if node["children"] is None:
            leaves.append({"members": node["members"], "depth": depth, "path": path})
        else:
            _collect(node["children"][0], depth + 1, path + "L")
            _collect(node["children"][1], depth + 1, path + "R")
    _collect(tree, 0, "")
    tome_of = {}
    for t, leaf in enumerate(leaves):
        for p in leaf["members"]:
            tome_of[p] = t
    tomes, word_tome = [], {}
    for t, leaf in enumerate(leaves):
        mem_words = sorted((content_ids[p] for p in leaf["members"]), key=lambda i: -degmap.get(i, 0))
        tomes.append({"label": [vocab[i] for i in mem_words[:8]], "size": len(leaf["members"]), "path": leaf["path"]})
        for i in mem_words:
            word_tome[vocab[i]] = [t, leaf["path"]]
    web = {}
    for p in range(len(content_ids)):
        for q, ww in adj[p].items():
            if p < q and tome_of[p] != tome_of[q]:
                key = "%d-%d" % (min(tome_of[p], tome_of[q]), max(tome_of[p], tome_of[q]))
                e = web.setdefault(key, {"weight": 0.0, "bridge": None, "bw": -1.0})
                e["weight"] += ww
                if ww > e["bw"]:
                    e["bw"] = ww
                    e["bridge"] = [vocab[content_ids[p]], vocab[content_ids[q]]]
    rd = Path(genome_dir) / "tree"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "hubs.txt").write_text("\n".join(vocab[i] for i in hub_ids), encoding="utf-8")
    (rd / "tomes.json").write_text(json.dumps(tomes), encoding="utf-8")
    (rd / "word_tome.json").write_text(json.dumps(word_tome), encoding="utf-8")
    (rd / "web.json").write_text(json.dumps(web), encoding="utf-8")
    return {"tomes": len(tomes), "hubs": len(hub_ids), "words": len(word_tome)}


def build_tree(genome_dir, *, vocab, edges, weights, h_drop=H_DROP, k_keep=K_KEEP, k_nbr=K_NBR):
    """Build the de-lensed Fiedler tome-TREE + WEB from raw (vocab, edges, weights) (F786). De-lens: rank vocab by
    WEIGHTED degree, DROP the top-`h_drop` hubs, KEEP the next `k_keep` content words, IDF-weight edges by endpoint
    rarity. (For a corpus-scale genome prefer build_tree_from_store — it avoids materialising the whole edge list.)"""
    deg = {}
    for (a, b), w in zip(edges, weights):
        deg[a] = deg.get(a, 0.0) + w
        deg[b] = deg.get(b, 0.0) + w
    ranked = sorted(deg, key=lambda i: -deg[i])
    hub_ids = set(ranked[:h_drop])
    content_ids = [i for i in ranked[h_drop:h_drop + k_keep] if i < len(vocab)]
    cset = set(content_ids)
    cpos = {i: p for p, i in enumerate(content_ids)}
    maxdeg = max((deg[i] for i in content_ids), default=1.0) or 1.0
    idf = {i: 1.0 - deg[i] / (maxdeg * 1.0001) for i in content_ids}
    cand = {p: {} for p in range(len(content_ids))}
    for (a, b), w in zip(edges, weights):
        if a in cset and b in cset and a != b:
            pa, pb = cpos[a], cpos[b]
            ww = w * idf[a] * idf[b]
            if ww > cand[pa].get(pb, 0.0):
                cand[pa][pb] = ww
                cand[pb][pa] = ww
    return _write_tree(genome_dir, vocab, content_ids, cand, hub_ids, deg, k_nbr)


def build_tree_from_store(genome_dir, *, h_drop=H_DROP, tree_drop=TREE_DROP, k_keep=K_KEEP, k_nbr=K_NBR):
    """Build the tome-tree straight from the DEMAND-LOAD store (reads/) — memory-light (mmap), NO 960 MB source
    json.load. De-lens by NEIGHBOUR-COUNT (the unweighted degree, read directly from adj.idx: hubs = the
    many-neighbour function / markup tokens); build the content sub-graph from the content tokens' mmap records
    (IDF-weighted by rarity); recursive sparse-Fiedler bisection -> the tree. The corpus-scale build path.
    `hub_ids` (top `h_drop`) is the RIDE de-lens; the tree BAND drops only the top `tree_drop` so frequent content
    topics stay navigable (find() also falls back to a content neighbour's tome for anything not in the band)."""
    h = open_demand(genome_dir)
    vocab = h["vocab"]
    nrec = len(h["idx"]) // _IDX.size
    counts = [_IDX.unpack_from(h["idx"], t * _IDX.size)[1] for t in range(nrec)]   # neighbour count = unweighted degree
    ranked = sorted(range(nrec), key=lambda t: -counts[t])
    hub_ids = set(ranked[:h_drop])
    content_ids = [t for t in ranked[tree_drop:tree_drop + k_keep] if t < len(vocab)]
    cset = set(content_ids)
    cpos = {i: p for p, i in enumerate(content_ids)}
    maxc = max((counts[i] for i in content_ids), default=1) or 1
    idf = {i: 1.0 - counts[i] / (maxc * 1.0001) for i in content_ids}
    cand = {p: {} for p in range(len(content_ids))}
    for i in content_ids:
        pa = cpos[i]
        for (j, w, _c) in _records(h, i, 200):     # this content token's strongest neighbours (mmap slice)
            if j in cset and j != i:
                ww = w * idf[i] * idf[j]
                pb = cpos[j]
                if ww > cand[pa].get(pb, 0.0):
                    cand[pa][pb] = ww
                    cand[pb][pa] = ww
    return _write_tree(genome_dir, vocab, content_ids, cand, hub_ids, {i: counts[i] for i in content_ids}, k_nbr)


def _open_tree(genome_dir, vindex):
    """Load tree/ (small JSON) into the handle if present; None otherwise. Resolves hub words -> ids (for the ride
    de-lens) via the store's vindex. Cheap: the tree is a few thousand content words + labels + bridges."""
    rd = Path(genome_dir) / "tree"
    if not (rd / "tomes.json").exists():
        return None
    hub_words = (rd / "hubs.txt").read_text(encoding="utf-8").split("\n")
    return {"tomes": json.loads((rd / "tomes.json").read_text(encoding="utf-8")),
            "word_tome": json.loads((rd / "word_tome.json").read_text(encoding="utf-8")),
            "web": json.loads((rd / "web.json").read_text(encoding="utf-8")),
            "hub_ids": frozenset(vindex[w] for w in hub_words if w in vindex)}


def find(h, token):
    """FIND: descend the tome-tree to `token`'s tome -> {tome, path, depth, label[, via]} or None. If `token` is
    not itself in the content band (a hub, or a rare token), FALL BACK to the tome of its strongest content
    NEIGHBOUR (via the store) so any topic still navigates. Needs a built tree (prepare over a genome with tree/)."""
    tr = h.get("tree")
    if not tr:
        return None
    wt = tr["word_tome"].get(token)
    if wt is None:                                          # not in the band -> its strongest in-band neighbour's tome
        ti = h["vindex"].get(token)
        if ti is None:
            return None
        for (j, w, c) in _records(h, ti, _SCAN):
            nb = tr["word_tome"].get(h["vocab"][j])
            if nb is not None:
                t, path = nb
                return {"tome": t, "path": path, "depth": len(path), "label": tr["tomes"][t]["label"],
                        "via": h["vocab"][j]}
        return None
    t, path = wt
    return {"tome": t, "path": path, "depth": len(path), "label": tr["tomes"][t]["label"]}


def ride_tome(h, tome_id, k=8):
    """RIDE: the tome's coherent neighbourhood — its highest-degree content words (the tome LABEL is exactly this
    ridge). Returns up to k words."""
    tr = h.get("tree")
    if not tr or tome_id >= len(tr["tomes"]):
        return []
    return tr["tomes"][tome_id]["label"][:k]


def web_hop(h, tome_id):
    """WEB-HOP: cross the strongest bridge from `tome_id` to an adjacent tome -> {to, label, bridge} or None. The
    web is the cut-edge graph between leaf tomes (F780) — the cross-tome relationships one tome alone cannot see."""
    tr = h.get("tree")
    if not tr:
        return None
    best, bw = None, -1.0
    for key, e in tr["web"].items():
        a, b = (int(x) for x in key.split("-"))
        if tome_id in (a, b) and e["weight"] > bw:
            bw = e["weight"]
            other = b if a == tome_id else a
            best = {"to": other, "label": tr["tomes"][other]["label"], "bridge": e["bridge"]}
    return best
