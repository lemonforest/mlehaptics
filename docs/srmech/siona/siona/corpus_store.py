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
import mmap
import struct
from pathlib import Path

from srmech.amsc import genome as _G
from srmech.amsc import hdc as _H

LEAF = 64
COUPLE = _H.klein4_random(LEAF, seed=1080)          # the store's canonical coupling (the sandroing/UNESCO 00073 seed)
_REC = struct.Struct("<iii")                         # a neighbour record: (neighbour_id, metric, charge-from-this-view)
_IDX = struct.Struct("<QI")                          # an index record: (byte_offset uint64, count uint32)


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


def open_demand(genome_dir):
    """Open the reads/ layer INSTANTLY: load the small idx + vocab, mmap adj.bin (no decode; pages in per query)."""
    rd = Path(genome_dir) / "reads"
    vocab = (rd / "vocab.txt").read_text(encoding="utf-8").split("\n")
    idx = (rd / "adj.idx").read_bytes()
    fb = open(rd / "adj.bin", "rb")
    mm = mmap.mmap(fb.fileno(), 0, access=mmap.ACCESS_READ)
    return {"mode": "demand", "vocab": vocab, "vindex": {t: n for n, t in enumerate(vocab)},
            "idx": idx, "mm": mm, "_fb": fb}


def prepare(genome_dir):
    """Return a read handle. reads/ present -> DEMAND-LOAD (instant open, gene_express per query). Else (a small
    corpus) -> full in-RAM (cheap). Same read() API either way."""
    if (Path(genome_dir) / "reads" / "adj.idx").exists():
        return open_demand(genome_dir)
    vocab, graph = load(genome_dir)
    return {"mode": "ram", "vocab": vocab, "vindex": {t: n for n, t in enumerate(vocab)},
            "adj": _adjacency(graph["edges"], graph["weights"], graph["charges"])}


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
    path, seen, cur = [token], {ti}, ti
    for _ in range(steps):
        nxt = None
        for (j, w, c) in _records(h, cur, _SCAN):       # metric-desc: first admissible IS the strongest coupling
            if (c >= 0) == want_fwd and j not in seen:   # Class-C chirality sign = the which-way (no abs)
                nxt = j
                break
        if nxt is None:
            break
        seen.add(nxt)
        path.append(h["vocab"][nxt])
        cur = nxt
    return path
