r"""R-RBS-LM-GRAPH2KERNEL (F1222 / #1390 item 2) — PROTOTYPE the `graph_to_kernel` / `kernel_to_graph` codec.

This is the srmech-upstream candidate #2: a DOMAIN-FREE codec that serializes a sparse SIGNED INTEGER graph
(the directed Class-L Laplacian — vocab_size + edge_list + int weights[metric] + signed charges[direction]) into a
Klein-4 symbol stream for `kernel_pack`, and inverts it BYTE-EXACT. Today we hand-roll this in EVERY directed
encoder (R-RBS-LM-NIVDIRECTED `_ints_to_syms`/`kernel_to_ints`, R-RBS-LM-NOWCURVATURE). Here it is abstracted once,
general (any directed signed graph), and PROVEN against the REAL directed word kernels (`word_to_kernel`).

The codec is the "store the directed Laplacian as a genome" primitive #231 needs — it makes the corpus store a
library call instead of a hand-roll. Klein-4 is used ONLY as the 2-bit on-disk ALPHABET (the content is relational;
no bind/bundle HV object is stored — F1221 disk rule).

srmech 0.9.0rc241; exact ints; no numpy; no abs-builtin (sign is Class-K zig-zag). Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-GRAPH2KERNEL_...py
"""
import importlib.util
import os
import shutil
import sys
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import hdc

HERE = Path(__file__).parent
OUTDIR = Path(os.environ.get("OUT", "/tmp/graph2kernel_proto"))
LEAF = 64
COUPLE = hdc.klein4_random(LEAF, seed=1080)          # same coupling as NIVDIRECTED (the sandroing/UNESCO 00073 seed)


# ------------------------------------------------------------------------------------------------------------------
# THE PROPOSED srmech OP FAMILY (prototype). Signature drafted for #1390 item 2.
#   graph_to_kernel(vocab_size, edges, weights, charges=None, *, node_ids=None, extras=(), leaf_dim, label, the_one)
#     -> strand                         # a packed genome chromosome (Klein-4 leaves); persist via genome_save
#   kernel_to_graph(chroms, the_one)    -> {vocab_size, edges, weights, charges, node_ids, extras}
# The format is SELF-DESCRIBING (count headers), so undirected (charges=None), unlabeled (node_ids=None), and
# metadata-free (extras=()) graphs all round-trip without the caller tracking widths. Class-K sign via zig-zag.
# ------------------------------------------------------------------------------------------------------------------
def _zig(n):
    return (n << 1) if n >= 0 else ((-n) << 1) - 1       # Class-K pin-slot: signed int -> non-negative (not the builtin)


def _unzig(z):
    return (z >> 1) if (z & 1) == 0 else -((z + 1) >> 1)


def _ints_to_syms(ints):
    """flat non-negative int list -> Klein-4 symbols {0,1,2,3}: each int as base-4 digits behind a 2-symbol length
    header (<=15 base-4 digits/int). The discrete, JSON-free codec so the packed object is genome-native."""
    syms = []
    for n in ints:
        digs = []
        x = n
        while True:
            digs.append(x & 3)
            x >>= 2
            if x == 0:
                break
        assert len(digs) <= 15, "int too wide for the 2-symbol length header"
        syms.append(len(digs) & 3)
        syms.append((len(digs) >> 2) & 3)
        syms += digs
    return syms


def _syms_to_ints(syms):
    ints, i = [], 0
    while i + 2 <= len(syms):
        ln = syms[i] + (syms[i + 1] << 2)
        i += 2
        if ln == 0 or i + ln > len(syms):
            break
        v = 0
        for k in range(ln):
            v |= syms[i + k] << (2 * k)
        ints.append(v)
        i += ln
    return ints


def graph_to_kernel(vocab_size, edges, weights, charges=None, *, node_ids=None, extras=(), leaf_dim, label, the_one):
    """Serialize a directed SIGNED integer graph -> a packed genome chromosome (Klein-4 leaves).
    edges: [(i,j),...]; weights: [int,...] (metric); charges: [signed int,...] or None (direction);
    node_ids: [int,...] or None (a label table, e.g. glyph ids); extras: (int,...) caller metadata (e.g. start)."""
    assert len(edges) == len(weights), "edges/weights length mismatch"
    ch = charges if charges is not None else [0] * len(edges)
    assert len(ch) == len(edges), "charges length mismatch"
    nid = list(node_ids) if node_ids is not None else []
    ex = list(extras)
    payload = [vocab_size, len(nid)] + nid + [len(ex)] + ex + [len(edges)]
    for (i, j), w, c in zip(edges, weights, ch):
        payload += [i, j, w, _zig(c)]                   # per-edge: from, to, metric, zig(direction)
    syms = _ints_to_syms(payload)
    return G.kernel_pack(syms, leaf_dim=leaf_dim, label=label, the_one=the_one), len(syms)


def kernel_to_graph(chroms, the_one, n_syms):
    """Inverse: a packed chromosome (strand of Klein-4 leaves) -> the directed signed graph dict. n_syms trims the
    leaf-dim padding kernel_unpack adds (D = n_leaves x leaf_dim)."""
    syms = list(G.kernel_unpack(chroms, the_one))[:n_syms]
    it = _syms_to_ints(syms)
    p = 0
    vocab_size = it[p]; p += 1
    n_nid = it[p]; p += 1
    node_ids = it[p:p + n_nid]; p += n_nid
    n_ex = it[p]; p += 1
    extras = it[p:p + n_ex]; p += n_ex
    ne = it[p]; p += 1
    edges, weights, charges = [], [], []
    for _ in range(ne):
        i, j, w, zc = it[p], it[p + 1], it[p + 2], it[p + 3]; p += 4
        edges.append((i, j)); weights.append(w); charges.append(_unzig(zc))
    return {"vocab_size": vocab_size, "edges": edges, "weights": weights,
            "charges": charges, "node_ids": list(node_ids), "extras": list(extras)}


# ------------------------------------------------------------------------------------------------------------------
def _load_nivdirected():
    """Load the REAL directed word encoder (hyphenated filename -> importlib by path)."""
    p = HERE / "R-RBS-LM-NIVDIRECTED_word_as_directed_glyph_graph_genome_native.py"
    spec = importlib.util.spec_from_file_location("nivdirected", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _persist_roundtrip(strand, n_syms, the_one, label):
    d = OUTDIR / (label + ".genome")
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    info = G.genome_save(strand, str(d), the_one, labels=[label])
    chroms, _cpl, _lbls = G.genome_load(str(d), labels=[label], the_one=the_one)
    size = sum(fl.stat().st_size for fl in d.rglob("*") if fl.is_file())
    return kernel_to_graph(chroms, the_one, n_syms), info.get("body_sha256"), size


def main():
    print("=== R-RBS-LM-GRAPH2KERNEL — prototype graph_to_kernel/kernel_to_graph vs the REAL directed word kernels ===\n")
    N = _load_nivdirected()
    words = ["banana", "mississippi", "level", "abracadabra", "sandroing", "vanuatu", "reappear", "committee"]
    ok_struct = ok_word = ok_persist = 0
    for w in words:
        k = N.word_to_kernel(w)                          # the REAL directed glyph Class-L kernel
        edges = [(i, j) for i, j in k["edge_list"]]
        # map the domain kernel onto the GENERAL codec: node_ids = the glyph ids; extras = [start anchor]
        node_ids = [N.GI[c] for c in k["vocab"]]
        strand, n_syms = graph_to_kernel(len(k["vocab"]), edges, k["edge_weights"], k["edge_charge"],
                                         node_ids=node_ids, extras=[k["start"]], leaf_dim=LEAF, label=w, the_one=COUPLE)
        # (a) in-memory round-trip
        g = kernel_to_graph(strand, COUPLE, n_syms)
        struct = (g["vocab_size"] == len(k["vocab"]) and g["edges"] == edges
                  and g["weights"] == k["edge_weights"] and g["charges"] == k["edge_charge"]
                  and g["node_ids"] == node_ids and g["extras"] == [k["start"]])
        ok_struct += struct
        # (b) genome-native persist round-trip (content-addressed dir -> load -> unpack -> decode)
        gp, sha, size = _persist_roundtrip(strand, n_syms, COUPLE, w)
        persist = (gp == g)
        ok_persist += persist
        # (c) the whole chain still reconstructs the WORD via Hierholzer (rebuild the kernel dict, run eulerian_word)
        rebuilt = {"vocab": [N.GLYPHS[t] for t in gp["node_ids"]], "start": gp["extras"][0],
                   "edge_list": [list(e) for e in gp["edges"]], "edge_weights": gp["weights"],
                   "edge_charge": gp["charges"]}
        recon = N.eulerian_word(rebuilt)
        # the encoder is glyph-set + directed-walk exact for consecutive (window=1); compare on the glyph alphabet
        expect = "".join(c for c in w.lower() if c in N.GI)
        wordok = (sorted(recon) == sorted(expect))       # Eulerian circuit: same multiset; F1079 closure may rotate
        ok_word += wordok
        print("  %-12s vocab=%d edges=%2d syms=%3d  genome=%dB sha=%s..  struct=%s persist=%s word=%s (%r)"
              % (w, len(k["vocab"]), len(edges), n_syms, size, (sha or "----")[:8],
                 "OK" if struct else "XX", "OK" if persist else "XX", "OK" if wordok else "XX", recon))
    n = len(words)
    print("\nRATCHET: struct round-trip %d/%d | genome-native persist %d/%d | word reconstruct %d/%d"
          % (ok_struct, n, ok_persist, n, ok_word, n))
    verdict = (ok_struct == n and ok_persist == n)
    print("VERDICT: %s — graph_to_kernel/kernel_to_graph is a faithful, domain-free, byte-exact replacement for the\n"
          "         hand-rolled codec; the general (self-describing) format round-trips real directed word kernels\n"
          "         AND persists genome-native. Ready to propose as #1390 item 2 (with a C mirror)."
          % ("PASS" if verdict else "FAIL — investigate"))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
