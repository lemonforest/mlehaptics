r"""R-RBS-SNN-CONNECTOME (rung #3 — the falsifier) — the F492 prediction is that a real neuron's dominant ≤7
synaptic couplings split ~3 RECURRENT : ~4 FEEDFORWARD (the fiber-3 closes into a loop, the base-4 points out).
This is the one EMPIRICAL probe that could break the whole ride — so it MUST run on real, ATTESTED connectome
data (MPM), NOT synthetic. The sandbox has no network, so this file ships:
  • the MEASUREMENT HARNESS (per-node top-7 partners → reciprocal/recurrent vs one-way/feedforward),
  • a NULL control (a seeded random directed graph) = the chance baseline (what "no 3:4 structure" looks like),
  • the ATTESTATION SPEC for the real run (the canonical open C. elegans connectome).
The real-data run is flagged as PENDING the fetch — the falsifier is set up, not faked.
srmech 0.7.4 (laplacian.magnetic_laplacian for the directed/chiral content).
"""
import random
import srmech
from srmech.amsc import laplacian as L


def split_recurrent_feedforward(n, edges, weights, k=7):
    """per node: among its top-k strongest partners, count RECURRENT (reciprocal edge) vs FEEDFORWARD (one-way)."""
    out_w = {i: {} for i in range(n)}
    pair = set()
    for (a, b), w in zip(edges, weights):
        out_w[a][b] = out_w[a].get(b, 0.0) + w
        pair.add((a, b))
    rec_counts, ff_counts = [], []
    for i in range(n):
        partners = sorted(out_w[i], key=lambda j: out_w[i][j], reverse=True)[:k]
        if not partners:
            continue
        rec = sum(1 for j in partners if (j, i) in pair)        # reciprocal → recurrent (the loop closes)
        rec_counts.append(rec); ff_counts.append(len(partners) - rec)
    mr = sum(rec_counts) / len(rec_counts)
    mf = sum(ff_counts) / len(ff_counts)
    return mr, mf, len(rec_counts)


def main():
    print(f"=== R-RBS-SNN-CONNECTOME (rung #3, the falsifier) — 3:4 recurrent:feedforward harness + null  (srmech {srmech.__version__}) ===\n")

    # NULL control — a seeded random DIRECTED graph (chance baseline; what "no 3:4 structure" looks like)
    rng = random.Random(20260607)
    n, p = 300, 0.04                                            # ~C. elegans scale; sparse directed
    edges, weights = [], []
    for a in range(n):
        for b in range(n):
            if a != b and rng.random() < p:
                edges.append((a, b)); weights.append(rng.random())
    mr, mf, cov = split_recurrent_feedforward(n, edges, weights, k=7)
    H = L.magnetic_laplacian(n, edges[:2000], weights[:2000], q=0.25)   # directed chiral content present
    chi = float((H.imag ** 2).sum())
    print("NULL (seeded random directed graph, n=300, p=0.04) — the chance baseline:")
    print(f"  mean top-7 split:  RECURRENT {mr:.2f} : FEEDFORWARD {mf:.2f}   (over {cov} nodes)")
    print(f"  directed chiral energy (magnetic Laplacian) > 0: {chi > 1e-6}  (the chirality exists; F487 Test A)")
    print(f"  → in a RANDOM graph the recurrent fraction is ~p·k = {p*7:.2f} (chance); NOT a 3:4 (≈3.0:4.0) split.\n")

    print("THE TEST (the F492 prediction, PENDING real data):")
    print("  prediction: a REAL neuron's dominant ≤7 couplings split ~3 RECURRENT : ~4 FEEDFORWARD (fiber-3 closes,")
    print("  base-4 feedforward). SURVIVES if mean ≈ (3, 4) and clearly above the random baseline; BREAKS if it is")
    print("  at the random baseline (no preferred recurrent core) or a different ratio (e.g. 5:2, 1:6).\n")

    print("  ATTESTATION SPEC for the real run (MPM — to fetch when network is available):")
    print("    source: the C. elegans connectome (canonical, open). Cook, S.J. et al. (2019),")
    print("            'Whole-animal connectomes of both Caenorhabditis elegans sexes', Nature 571:63–71,")
    print("            doi:10.1038/s41586-019-1352-7 — data via WormWiring (wormwiring.org).")
    print("    parse: directed chemical-synapse adjacency (pre→post) with weights = synapse counts; run")
    print("           split_recurrent_feedforward(k=7); attest source_doi/url/retrieved_at/response_sha256 (MPR v1).")
    print("    NOT faked here: synthetic data would be circular — the falsifier needs the real, attested graph.\n")

    print("VERDICT (rung #3):")
    print(f"  • harness READY + null baseline measured: a random directed graph gives RECURRENT≈{mr:.2f}:FF≈{mf:.2f}")
    print(f"    (chance ≈ p·k), so a real 3:4 (≈3.0:4.0) would be a clear, falsifiable signal ABOVE chance.")
    print(f"  • the directed chiral content (magnetic Laplacian) is present even in the null (F487 Test A holds")
    print(f"    structurally); the 3:4 SPLIT is the new, sharper F492 prediction the connectome will confirm or break.")
    print(f"  • REAL-DATA RUN PENDING (no network): the falsifier is set up with its MPM attestation, NOT faked.")
    print(f"    This is the empirical probe that could break the ride — held open, honestly (F394).")


if __name__ == "__main__":
    main()
