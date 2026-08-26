r"""R-RBS-LM-DIRCOOCCUR (F1226 / #1390 item 1) — PROTOTYPE `cooccurrence_edges(..., directed=True)`.

srmech-upstream candidate #1 (already filed UPSTREAM §, F1210), now ESCALATED to a working reference impl that
demonstrates the op the way we USE the data — as the FRONT of the pipeline whose back (items 2/3/4) is prototyped:

    text -> tokenize -> cooccurrence_edges(directed=True) -> (n, edges, METRIC, CHARGE)
         -> magnetic_laplacian (the directed Hermitian L)   [shipped]
         -> graph_to_kernel -> genome_save/load -> kernel_to_graph   [item 2]
         -> recover_check confirms op+operand+responsion+CURVATURE   [item 4]

`text.cooccurrence_edges(docs, *, window, vocab)` folds direction (canonical i<j) -> `(n, edges, weights)`. The ask:
add `directed=False`; when True return the SAME edges + **metric** (w_fwd+w_bwd, == today's weights — a strict
superset, backward-compatible) + **charge** (w_fwd-w_bwd, the direction the fold discards). Proven here:
  (A) directed=False reproduces the shipped op byte-for-byte (drop-in);
  (B) directed=True: metric == the shipped weights, charge is the new axis, and REVERSING the corpus FLIPS the charge
      (the base's word==reverse blindness, F1211, fixed at token scale);
  (C) the directed output flows straight into magnetic_laplacian + item-2 codec + item-4 recover_check (curvature present).

srmech 0.9.0rc241; exact ints; no numpy; no abs-builtin (charge sign is Class-K). Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-DIRCOOCCUR_...py

ADOPTED UPSTREAM (F1286): `cooccurrence_edges` now ships in `srmech.amsc.text`. This file is the PROTOTYPE RECORD and is
kept as-run, but NEW code must call the shipped op — copying the local definition forward
means maintaining a second, less-tested implementation of a supported surface.
"""
import importlib.util
import shutil
import sys
from pathlib import Path

from srmech.amsc import genome as G
from srmech.amsc import laplacian as L
from srmech.amsc import text as T

HERE = Path(__file__).parent


# ------------------------------------------------------------------------------------------------------------------
# THE PROPOSED srmech OP (prototype). The `directed=` flag added to text.cooccurrence_edges.
#   cooccurrence_edges(docs, *, window, vocab, vocab_size, directed=False)
#     directed=False -> (n, edges, weights)                 # UNCHANGED (today's return)
#     directed=True  -> (n, edges, metric, charge)          # metric == weights; charge = w_fwd - w_bwd
# Canonical edges (i<j); a windowed pair earlier->later at ids (u,v): u<v is FORWARD on (u,v), u>v is BACKWARD.
# ------------------------------------------------------------------------------------------------------------------
def cooccurrence_edges(docs, *, window=2, vocab=None, vocab_size=None, directed=False):
    if vocab is None:                                              # infer vocab (first-seen order) if not supplied
        vocab = []
        for doc in docs:
            for t in doc:
                if t not in vocab:
                    vocab.append(t)
    idx = {t: i for i, t in enumerate(vocab)}
    fwd, bwd = {}, {}
    for doc in docs:
        ids = [idx.get(t) for t in doc]                            # None = out-of-vocab token (skipped)
        for a in range(len(ids)):
            if ids[a] is None:
                continue
            for b in range(a + 1, min(a + window + 1, len(ids))):
                if ids[b] is None:
                    continue
                u, v = ids[a], ids[b]
                if u == v:
                    continue                                        # matches the shipped op: canonical i<j, no self-loops
                lo, hi = (u, v) if u < v else (v, u)
                if u < v:
                    fwd[(lo, hi)] = fwd.get((lo, hi), 0) + 1
                else:
                    bwd[(lo, hi)] = bwd.get((lo, hi), 0) + 1
    edges = sorted(set(fwd) | set(bwd))
    n = vocab_size if vocab_size is not None else len(vocab)
    metric = [fwd.get(e, 0) + bwd.get(e, 0) for e in edges]
    if not directed:
        return n, edges, metric                                    # == today's (n, edges, weights)
    charge = [fwd.get(e, 0) - bwd.get(e, 0) for e in edges]         # w_fwd - w_bwd (the discarded direction)
    return n, edges, metric, charge


# ------------------------------------------------------------------------------------------------------------------
def _load(stem):
    p = HERE / stem
    spec = importlib.util.spec_from_file_location(stem.split("_")[0].replace("-", ""), str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    print("=== R-RBS-LM-DIRCOOCCUR — cooccurrence_edges(directed=True): metric + charge, item 1 escalation ===\n")
    GK = _load("R-RBS-LM-GRAPH2KERNEL_prototype_general_directed_signed_graph_genome_codec.py")
    RC = _load("R-RBS-LM-RECOVERCHECK_prototype_general_class_l_genome_recover_check_four_faculties.py")

    vocab = ["alpha", "beta", "gamma", "delta"]
    docs = [["alpha", "beta", "gamma", "alpha", "beta", "delta", "gamma"]]

    # (A) BACKWARD-COMPAT: directed=False reproduces the shipped op byte-for-byte
    mine = cooccurrence_edges(docs, window=2, vocab=vocab, directed=False)
    ship = T.cooccurrence_edges(docs, window=2, vocab=vocab)
    a_ok = (mine == ship)
    print("  (A) backward-compat (directed=False == shipped op):")
    print("      shipped : %s" % (ship,))
    print("      proto   : %s   -> %s\n" % (mine, "MATCH" if a_ok else "DIFF"))

    # (B) directed=True: metric == shipped weights (superset); charge is the new axis; reversal FLIPS charge
    n, edges, metric, charge = cooccurrence_edges(docs, window=2, vocab=vocab, directed=True)
    rn, redges, rmetric, rcharge = cooccurrence_edges([list(reversed(docs[0]))], window=2, vocab=vocab, directed=True)
    b_metric = (metric == ship[2] and edges == ship[1])
    b_charge_nonzero = any(c != 0 for c in charge)
    b_flip = (redges == edges and rmetric == metric and rcharge == [-c for c in charge])
    print("  (B) directed=True (metric superset + charge axis + reversal flips):")
    print("      edges   : %s" % edges)
    print("      metric  : %s   (== shipped weights? %s)" % (metric, metric == ship[2]))
    print("      charge  : %s   (nonzero? %s)" % (charge, b_charge_nonzero))
    print("      reversed: charge %s   (== -charge? %s)\n" % (rcharge, rcharge == [-c for c in charge]))

    # (C) the way we USE the data: directed output -> magnetic_laplacian + item-2 codec + item-4 recover_check
    print("  (C) pipeline (the way we use the data): directed edges -> magnetic_laplacian -> genome -> recover_check:")
    Lm = L.magnetic_laplacian(n, edges, [float(w) for w in metric], charges=[float(c) for c in charge])
    strand, n_syms = GK.graph_to_kernel(n, edges, metric, charge, leaf_dim=GK.LEAF, label="dircooccur", the_one=GK.COUPLE)
    d = Path("/tmp/dircooccur_proto/corpus.genome")
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.parent.mkdir(parents=True, exist_ok=True)
    G.genome_save(strand, str(d), GK.COUPLE, labels=["dircooccur"])
    chroms, _c, _l = G.genome_load(str(d), labels=["dircooccur"], the_one=GK.COUPLE)
    g = GK.kernel_to_graph(chroms, GK.COUPLE, n_syms)
    codec_ok = (g["vocab_size"] == n and g["edges"] == edges and g["weights"] == metric and g["charges"] == charge)
    v = RC.recover_check(g["vocab_size"], g["edges"], g["weights"], g["charges"])
    print("      magnetic_laplacian built: %dx%d Hermitian" % (n, n))
    print("      genome round-trip codec-exact? %s" % codec_ok)
    print("      recover_check -> ok=%s (op=%s operand=%s responsion=%s) curvature=%s"
          % (v["ok"], v["op"], v["operand"], v["responsion"], v["curvature"]["verdict"]))
    c_ok = codec_ok and v["ok"] and v["curvature"]["directed"]

    verdict = a_ok and b_metric and b_charge_nonzero and b_flip and c_ok
    print("\nVERDICT: %s — cooccurrence_edges(directed=True) is a backward-compatible SUPERSET (metric == today's\n"
          "         weights, %s), adds the CHARGE axis the fold discards (nonzero, flips under corpus reversal),\n"
          "         and flows straight into the shipped magnetic_laplacian + the item-2 codec + item-4 recover_check\n"
          "         (curvature present). The whole #1390 pipeline runs end-to-end from raw text. Ready to escalate\n"
          "         item 1 to a concrete directed= patch (with a C mirror on the text op)."
          % ("PASS" if verdict else "FAIL — investigate", "drop-in" if a_ok else "DIFF"))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
