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
import os
import struct
from pathlib import Path

from srmech.biology import genome as _G
from srmech.math import hdc as _H
from srmech.math import laplacian as _L          # NATIVE Class-L recursion: recursive_cut / fiedler_sparse (srmech gh#1097 / §52)

LEAF = 64
# F1304: the coupling is the SANDROING/UNESCO-00073 SOURCE — so it is content-addressed (the "knowledge it
# contains"), NOT a random seed. Was klein4_random(LEAF, seed=1080): a DRAWN magic number (F1259) AND
# klein4_random is DELETED at rc297. klein4 is a CARRIER; its shape comes from the_One or from content, never
# a seed (user direction 2026-07-22). This de-magicks 1080 to a Class-A content-address, resonant + stable.
COUPLE = _H.klein4_encode_bytes(b"UNESCO-ICH-00073:vanuatu-sand-drawings", LEAF)
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
MAXTOME = 12            # a clump becomes a leaf tome at this size (recursive_cut max_tome)


def load(genome_dir, the_one=None):
    """Decode the whole genome -> (vocab, graph). The CANONICAL read (no external metadata; self-describing format
    stops at n_edges; vocab tail trimmed to vocab_size). Heavy at corpus scale — used to BUILD reads/, then not again."""
    the_one = COUPLE if the_one is None else the_one
    chg, _c, _l = _G.genome_load(str(genome_dir), labels=["graph"], coupling=the_one)
    n = len(list(_G.kernel_unpack(chg, the_one)))
    graph = _G.kernel_to_graph(chg, the_one, n)
    chv, _c2, _l2 = _G.genome_load(str(genome_dir), labels=["vocab"], coupling=the_one)
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


def _load_attest(genome_dir):
    """The genome's ATTESTATION + rendering, read from its manifest.json (the AMSC provenance sidecar). Returns
    ``{"attestation": {...}, "rendering": {...}}`` or None. Siona CITES this on a corpus read — an attested genome
    (MPM): the read points at its source, exactly like an attested knowledge kernel does."""
    mp = Path(genome_dir) / "manifest.json"
    if not mp.exists():
        return None
    try:
        m = json.loads(mp.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return {"attestation": m.get("attestation", {}), "rendering": m.get("rendering", {})}


def cite(h):
    """The one-line CITATION for the corpus genome (its manifest attestation), or None: the rendering's ``cite_as``
    if present, else the source_url (+ license). Appended to a corpus read so the answer is attested to its source."""
    a = h.get("attest")
    if not a:
        return None
    r, at = a.get("rendering", {}), a.get("attestation", {})
    if r.get("cite_as"):
        return r["cite_as"]
    src, lic = at.get("source_url"), at.get("license")
    return ("%s%s" % (src, ", %s" % lic if lic else "")) if src else None


def _attach_bodies(h, genome_dir):
    """Attach the FULL-BODY RBS-HDC instrument (#227, F805/F818) — the article TEXT (the DEFINITIONS: 'what it IS'),
    a sibling of the co-occurrence genome — so `body_lead` can recall a topic's lead. The co-occurrence genome is
    relational ('what it's LIKE'); the body instrument is the missing DEFINITION read (F1241). Env SIONA_BODIES
    overrides; else the first ``*fullbody_instrument.ndjson`` next to the genome, with its ``*_index.json``."""
    instr = os.environ.get("SIONA_BODIES")
    if not instr:
        sib = sorted(Path(genome_dir).parent.glob("*fullbody_instrument.ndjson"))
        instr = str(sib[0]) if sib else None
    if instr and Path(instr).exists():
        idx = instr.replace("_instrument.ndjson", "_index.json")
        if Path(idx).exists():
            h["bodies"] = {"instrument": instr, "index": idx}
    return h


_COPULA = frozenset({"is", "are", "was", "were", "refers", "means", "describes", "denotes"})
# the full-body encode stripped punctuation, so a fixed-length lead can end mid-clause; trim trailing dangling
# connectors so the definition reads as a clean sentence (best effort — no sentence boundaries survive the encode).
_DANGLE = frozenset(("and or of is are was to a an the in with made but that which for as by on at from it its this "
                     "these those into over between about after before also such can may will would").split())


def body_lead(h, token, n=30):
    """The DEFINITION of `token` — its article's OPENING definition ('<token> is …'), recalled from the #227
    full-body RBS-HDC instrument via the de Bruijn fiber walk (bridge.recall, F805/F818). This is 'what it IS' (the
    read the co-occurrence store cannot give). Pivots to the first '<token> is/are/…' so the leading image-caption
    markup is skipped and the definition comes through clean (a leading a/an/the is kept). Returns the lead tokens,
    or None if there is no article body / no definitional pivot within the recalled span."""
    bod = h.get("bodies")
    if not bod:
        return None
    from . import bridge
    rec = bridge.recall(token, bod["instrument"], bod["index"])
    if not rec or not rec.get("tokens"):
        return None
    toks = rec["tokens"]
    for i in range(len(toks) - 1):
        if toks[i] == token and toks[i + 1] in _COPULA:               # the definitional pivot: '<token> is …'
            start = i - 1 if (i > 0 and toks[i - 1] in ("a", "an", "the")) else i
            span = toks[start:i + n]
            while len(span) > 4 and span[-1] in _DANGLE:               # trim a trailing dangling connector
                span = span[:-1]
            return span
    return None                                                        # no clean '<token> is …' -> no definition span


def _attach_tree(h, genome_dir):
    """Attach the tome-tree (if built) to a handle: h['tree'] for find/ride/web-hop, h['hub_ids'] for the ride
    de-lens; h['attest'] = the genome's MPR provenance (manifest.json) for citing reads; h['bodies'] = the full-body
    instrument for the DEFINITION read. Additive — no tree means plain rides; no manifest means no citation; no
    body instrument means the relational read only (no definition)."""
    tr = _open_tree(genome_dir, h["vindex"])
    if tr is not None:
        h["tree"] = tr
        h["hub_ids"] = tr["hub_ids"]
    h["attest"] = _load_attest(genome_dir)
    return _attach_bodies(h, genome_dir)


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
def _write_tree(genome_dir, vocab, content_ids, cand, hub_ids, degmap, k_nbr):
    """Shared tail: sparsify the candidate content graph -> the NATIVE srmech `laplacian.recursive_cut` (out-of-core
    recursive normalized-cut spectral partition into community TOMES, gh#1097/§52 — the C-dispatched op, not a
    hand-rolled Python Fiedler) -> the leaf tomes + word->tome map + inter-tome web, written under <genome_dir>/tree/.
    `degmap` (id -> importance) orders the tome labels."""
    adj = {p: {} for p in range(len(content_ids))}
    edges, weights = [], []
    for p in range(len(content_ids)):
        for q, ww in sorted(cand[p].items(), key=lambda kv: kv[1], reverse=True)[:k_nbr]:
            adj[p][q] = ww
            adj[q][p] = ww
    for p in range(len(content_ids)):
        for q, ww in adj[p].items():
            if p < q:
                edges.append((p, q))
                weights.append(ww)
    part = _L.recursive_cut(len(content_ids), edges, weights, max_tome=MAXTOME)   # NATIVE recursion (srmech Class-L)
    import shutil
    shutil.rmtree(part.get("work_dir", "") or ".", ignore_errors=True)            # clean the out-of-core disk spill
    leaves = part["tomes"]                                                        # list of content-position lists
    tome_of = {p: t for t, mem in enumerate(leaves) for p in mem}
    tomes, word_tome = [], {}
    for t, mem in enumerate(leaves):
        mem_words = sorted((content_ids[p] for p in mem), key=lambda i: -degmap.get(i, 0))
        tomes.append({"label": [vocab[i] for i in mem_words[:8]], "size": len(mem)})
        for i in mem_words:
            word_tome[vocab[i]] = t
    web = {}
    for p in range(len(content_ids)):
        for q, ww in adj[p].items():
            tp, tq = tome_of.get(p), tome_of.get(q)
            if p < q and tp is not None and tq is not None and tp != tq:
                key = "%d-%d" % (min(tp, tq), max(tp, tq))
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
    t = tr["word_tome"].get(token)
    if t is None:                                          # not in the band -> its strongest in-band neighbour's tome
        ti = h["vindex"].get(token)
        if ti is None:
            return None
        for (j, w, c) in _records(h, ti, _SCAN):
            nb = tr["word_tome"].get(h["vocab"][j])
            if nb is not None:
                return {"tome": nb, "label": tr["tomes"][nb]["label"], "size": tr["tomes"][nb]["size"],
                        "via": h["vocab"][j]}
        return None
    return {"tome": t, "label": tr["tomes"][t]["label"], "size": tr["tomes"][t]["size"]}


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
