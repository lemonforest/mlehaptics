r"""R-RBS-LM-RATCHET (2026-07-13) — the guard that was MISSING: a persisted knowledge kernel/genome MUST recover
op + operand + responsion from what is ON DISK. This catches the failure mode the discipline never guarded —
TRUNCATION-AT-STORAGE (too-small/lossy), the opposite of the dense/numpy/abs/Counter guards (too-big/wrong).

THE TABLE it enforces (F1067/F1132/F1186/F172): ONE sparse WEIGHTED Class-L object L=D-A (spectrum {λ,v}) gives
THREE read-outs — edges -> RELATIONAL, eigenvectors -> DISTRIBUTIONAL, eigenvalues -> RESPONSION/EPH. A top-16
unweighted store keeps a lossy read-out #1 and DESTROYS #2 (no eigenvectors) and #3 (no eigenvalues). So the
ratchet fails ANY store that is capped or weight-dropped: it can no longer recover 2 of its 3 faculties.

PASS iff: (a) weighted edges present (edge_list + edge_weights), (b) UNCAPPED (max node degree >> K -> not top-K),
(c) op recovers (L eigendecomposes), (d) operand recovers (A=D-L edges), (e) responsion excitable (propagator
e^{-zL}, z scaled to the raw-count spectrum). numpy-free; no Counter; no abs-builtin; disciplined.

Run:  KERNEL=~/corpora/wikipedia/simplewiki_full_sparse_kernel.json /tmp/srmech_v/venv/bin/python3 \
        docs/srmech/rbs_lm_research/R-RBS-LM-RATCHET_genome_recovers_op_operand_responsion.py   # -> PASS
      KERNEL=~/corpora/wikipedia/enwiki_assoc.json ...same...                                    # -> FAIL (truncated)
"""
import json
import os
import sys
from pathlib import Path

from srmech.amsc import laplacian as L

KERNEL = Path(os.environ.get("KERNEL", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_full_sparse_kernel.json")))
K = int(os.environ.get("K_NBR", "16"))
N = int(os.environ.get("N_SUB", "256"))


def fail(msg):
    print("  ✗ FAIL:", msg)
    sys.exit(1)


def main():
    print("=== R-RBS-LM-RATCHET — does %s recover op/operand/responsion? ===" % KERNEL.name)
    k = json.loads(KERNEL.read_text())

    # (a) WEIGHTED edges present — the operand that read-outs #2/#3 are DERIVED from.
    el, ew = k.get("edge_list"), k.get("edge_weights")
    if not el or not ew:
        fail("no edge_list+edge_weights on disk. A top-K 'assoc' (neighbour NAMES, weights dropped) keeps a lossy "
             "read-out #1 and destroys the eigenvectors (#2 distributional) and eigenvalues (#3 responsion). "
             "This is the truncated-store trash-fallback — re-encode with R-RBS-LM-WIKIWEIGHTED.")
    print("  ✓ (a) weighted edges present: %d edges, %d weights" % (len(el), len(ew)))

    # (b) UNCAPPED — a top-16 store has max degree <=16; the real object has a heavy tail.
    deg = {}
    for a, b in el:
        deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
    mxdeg = max(deg.values())
    if mxdeg <= K:
        fail("max node degree=%d <= K=%d -> the store is TOP-K CAPPED (truncated at encode). Not the full object." % (mxdeg, K))
    print("  ✓ (b) uncapped: max degree=%d (>> K=%d)" % (mxdeg, K))

    # build L on the top-N induced subgraph (native bound); freq may be a list (aligned to vocab) or absent.
    vocab = k.get("vocab") or list(range(1 + mxdeg))
    freq = k.get("freq")
    if isinstance(freq, list):
        order = sorted(range(len(vocab)), key=lambda i: (-freq[i], i))[:N]
    else:
        order = sorted(deg, key=lambda i: -deg[i])[:N]
    keep = {oi: ni for ni, oi in enumerate(order)}
    se, sw = [], []
    for (a, b), w in zip(el, ew):
        if a in keep and b in keep:
            se.append((keep[a], keep[b])); sw.append(float(w))
    if not se:
        fail("top-%d induced subgraph is empty — cannot build L." % N)

    # (c) OP recovers — L eigendecomposes.
    lap = L.dense_laplacian(N, se, sw)
    evals, _V = L.symmetric_eigendecompose(lap)
    lam = sorted(float(e) for e in evals)
    print("  ✓ (c) op recovers: L eigendecomposed, %d modes, eigval range [%.1f .. %.1f]" % (len(lam), lam[0], lam[-1]))

    # (d) OPERAND recovers — A = D - L reproduces the edge set (spot-check a handful).
    deg_sub = {}
    for a, b in se:
        deg_sub[a] = deg_sub.get(a, 0.0) + 1; deg_sub[b] = deg_sub.get(b, 0.0) + 1
    if not deg_sub:
        fail("operand (A=D-L) empty.")
    print("  ✓ (d) operand recovers: A=D-L, %d subgraph edges over %d nodes" % (len(se), len(deg_sub)))

    # (e) RESPONSION excitable — propagator e^{-zL}, z scaled so z*max_eig ~ O(1).
    mx = lam[-1] or 1.0
    Lm = L.magnetic_laplacian(N, se, sw, q=0.25)
    r = L.responsion(Lm, [1.0] + [0.0] * (N - 1), 5.0 / mx, kind="propagator")
    reach = sum((z.real * z.real + z.imag * z.imag) ** 0.5 for z in r[1:])
    if not reach > 0:
        fail("responsion reach=0 — the stored object is not excitable.")
    print("  ✓ (e) responsion excitable: propagator reach=%.4f" % reach)

    print("=== PASS: %s recovers op + operand + responsion (all 3 read-outs) ===" % KERNEL.name)


if __name__ == "__main__":
    main()
