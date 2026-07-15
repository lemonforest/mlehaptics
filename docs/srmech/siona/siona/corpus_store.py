"""siona.corpus_store — the directed Class-L corpus genome as Siona's RELATIONAL read (#231/PKG-3, F1233).

The STORE side of F1216 (relational, on disk) that F1219 showed Siona's read path was missing: `define`/`answer`
grounded to srmech TOOLS (water -> z_boson_mass), never to a corpus. This loads a directed corpus genome — built by
`srmech.amsc.genome.graph_to_kernel` (the directed Laplacian: metric + charge) + a vocab string chromosome
(#231) — and answers "what is X seen-with" as the relational read-out (co-occurrence metric + the charge/direction).

Loads WITHOUT any external metadata: the graph format is self-describing (stops at n_edges), and the vocab tail
padding is trimmed to `vocab_size`. Native srmech rc253; no numpy; store = the Laplacian + fiber, not Klein-4 HVs.
"""
from srmech.amsc import genome as _G
from srmech.amsc import hdc as _H

LEAF = 64
COUPLE = _H.klein4_random(LEAF, seed=1080)          # the store's canonical coupling (the sandroing/UNESCO 00073 seed)


def load(genome_dir, the_one=None):
    """Load a directed corpus genome -> (vocab, graph). No stored n_syms/n_vsyms needed (self-describing format)."""
    the_one = COUPLE if the_one is None else the_one
    chg, _c, _l = _G.genome_load(str(genome_dir), labels=["graph"], the_one=the_one)
    n = len(list(_G.kernel_unpack(chg, the_one)))                 # unpack all; the decode stops at n_edges
    graph = _G.kernel_to_graph(chg, the_one, n)
    chv, _c2, _l2 = _G.genome_load(str(genome_dir), labels=["vocab"], the_one=the_one)
    vs = list(_G.kernel_unpack(chv, the_one))
    b = bytearray()
    for i in range(0, len(vs) - 3, 4):
        b.append(vs[i] + (vs[i + 1] << 2) + (vs[i + 2] << 4) + (vs[i + 3] << 6))
    vocab = b.decode("utf-8", errors="ignore").split("\n")[:graph["vocab_size"]]   # trim the padding tail
    return vocab, graph


def index(graph):
    """token id -> [(neighbor_id, metric, charge_from_this_node's_view), ...]. O(degree) lookup, not O(edges) scan.
    Charge flips for the mirror endpoint: on edge (i<j) charge c means i precedes j (c>0); from j's view it is -c."""
    adj = {}
    for (i, j), w, c in zip(graph["edges"], graph["weights"], graph["charges"]):
        adj.setdefault(i, []).append((j, w, c))
        adj.setdefault(j, []).append((i, w, -c))
    return adj


def prepare(genome_dir, the_one=None):
    """Load + build the vocab index + adjacency index -> (vocab, graph, vindex, adj), ready for `neighbors`."""
    vocab, graph = load(genome_dir, the_one)
    vindex = {t: n for n, t in enumerate(vocab)}
    return vocab, graph, vindex, index(graph)


def neighbors(vocab, vindex, adj, token, k=6):
    """The RELATIONAL read: what co-occurs with `token`, ranked by metric, with the direction (charge sign).
    Returns [(metric, sense, word), ...] where sense '->' = token precedes word, '<-' = word precedes token."""
    ti = vindex.get(token)
    if ti is None:
        return []
    top = sorted(adj.get(ti, []), key=lambda t: -t[1])[:k]
    return [(w, "->" if c >= 0 else "<-", vocab[j]) for (j, w, c) in top]
