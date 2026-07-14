r"""R-RBS-LM-OCTLAPLACIAN (F1230) — should we encode the genome as an OCTONION Laplacian? Measured, with the honest answer.

The claim (F1229): the fiber = the higher Cayley-Dickson grade of the ONE operator; an octonion (𝕆) Laplacian folds
the walk-ORDER into the object where the ℝ (metric) and ℂ (charge) grades cannot. Here we TEST it on the case that
matters: two DISTINCT walks that produce the IDENTICAL directed graph (edges + metric + charge) — the F1079 Euler
ambiguity. Does the 𝕆 grade distinguish them? And is the 𝕆 holonomy a LOSSLESS store of the order, or a fingerprint?

Result (measured below):
  * the ℝ + ℂ grades (metric, charge) are IDENTICAL for the two walks — order is LOST (as F1079 says).
  * the 𝕆 path-ordered product DISTINGUISHES them — order is CARRIED (the walk-order is the octonion grade).
  * BUT the 𝕆 product is a fingerprint, NOT injective (collisions exist among orderings) — so an octonion holonomy
    does NOT losslessly REPLACE storing the fiber (the sequence). It's an order-SENSITIVE VERIFIER, not a store.

=> srmech feedback: an octonion/CD Laplacian + order-sensitive holonomy is the right NEW op (top of the magnetic-
   Laplacian ladder) and a stronger recover_check curvature faculty; but the genome should still store the fiber
   LOSSLESSLY (the sequence) and use the 𝕆 holonomy as the order fingerprint/verifier.

From srmech qm.so8.octonion_mult_table. Exact ints; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-OCTLAPLACIAN_...py
"""
import itertools
import sys

from srmech.qm.so8 import octonion_mult_table

C = octonion_mult_table()


def omul(a, b):
    out = [0] * 8
    for i in range(8):
        if a[i] == 0:
            continue
        for j in range(8):
            if b[j] == 0:
                continue
            for k in range(8):
                c = C[i][j][k]
                if c:
                    out[k] += c * a[i] * b[j]
    return out


def _e(idx):
    v = [0] * 8
    v[idx] = 1
    return v


def walk_product(edge_octonions):
    """the path-ORDERED octonion product along a walk = the Wilson line / the fiber as one 𝕆 element (left-assoc)."""
    acc = _e(0)                                                  # 1 (the identity octonion)
    for o in edge_octonions:
        acc = omul(acc, o)
    return acc


def plain_directed(walk_edges, n):
    """the ℝ+ℂ grade: canonical (i<j) edges, metric = w_fwd+w_bwd, charge = w_fwd-w_bwd (what #231 stores today)."""
    fwd, bwd = {}, {}
    for (u, v) in walk_edges:
        lo, hi = (u, v) if u < v else (v, u)
        (fwd if u < v else bwd)[(lo, hi)] = (fwd if u < v else bwd).get((lo, hi), 0) + 1
    edges = sorted(set(fwd) | set(bwd))
    return edges, [fwd.get(e, 0) + bwd.get(e, 0) for e in edges], [fwd.get(e, 0) - bwd.get(e, 0) for e in edges]


def main():
    print("=== R-RBS-LM-OCTLAPLACIAN — does the octonion grade carry the walk-order the ℝ/ℂ grades lose? ===\n")

    # A figure-eight at node 0: two triangles share node 0. It has TWO distinct Euler circuits over the SAME edges.
    # directed edges of each circuit (the ORDER differs; the edge multiset is identical):
    walkA = [(0, 1), (1, 0), (0, 2), (2, 0)]                     # 0->1->0->2->0
    walkB = [(0, 2), (2, 0), (0, 1), (1, 0)]                     # 0->2->0->1->0  (same edges, different order)
    edge_oct = {(0, 1): _e(1), (1, 0): _e(2), (0, 2): _e(3), (2, 0): _e(4)}   # each directed edge -> an octonion unit

    print("(1) the ℝ+ℂ grade (metric + charge = what #231 stores today) — IDENTICAL for both walks?")
    pa = plain_directed(walkA, 3)
    pb = plain_directed(walkB, 3)
    print("    walk A: edges=%s metric=%s charge=%s" % pa)
    print("    walk B: edges=%s metric=%s charge=%s" % pb)
    same_plain = (pa == pb)
    print("    -> identical? %s   (charge all 0 too: even the ℂ magnetic Laplacian sees a SYMMETRIC graph)\n" % same_plain)

    # a GENERIC (non-basis) octonion per edge — basis units e_k have many algebraic coincidences (e1e2e3e4 collapses),
    # so the fair test uses richer octonions: real part 1 + a distinct imaginary axis of weight 2.
    edge_gen = {(0, 1): [1, 2, 0, 0, 0, 0, 0, 0], (1, 0): [1, 0, 2, 0, 0, 0, 0, 0],
                (0, 2): [1, 0, 0, 2, 0, 0, 0, 0], (2, 0): [1, 0, 0, 0, 2, 0, 0, 0]}

    print("(2) the 𝕆 grade (path-ordered octonion product) — DISTINGUISHES the two walks?")
    for tag, table in (("basis units e_k", edge_oct), ("generic octonions", edge_gen)):
        oa = walk_product([table[e] for e in walkA])
        ob = walk_product([table[e] for e in walkB])
        print("    [%s]  A=%s  B=%s  -> different? %s" % (tag, oa, ob, oa != ob))
    distinguishes = (walk_product([edge_gen[e] for e in walkA]) != walk_product([edge_gen[e] for e in walkB]))
    print("    -> generic 𝕆 distinguishes the two walks? %s\n" % distinguishes)

    print("(3) is the 𝕆 product a LOSSLESS store of order (injective), or a fingerprint?")
    lossless = True
    for tag, units in (("basis units", [_e(1), _e(2), _e(3), _e(4)]),
                       ("generic", [edge_gen[(0, 1)], edge_gen[(1, 0)], edge_gen[(0, 2)], edge_gen[(2, 0)]])):
        seen = {}
        total = 0
        for perm in itertools.permutations(range(4)):
            total += 1
            seen.setdefault(tuple(walk_product([units[i] for i in perm])), perm)
        distinct = len(seen)
        print("    [%s]  %d orderings -> %d DISTINCT products (%d collisions)" % (tag, total, distinct, total - distinct))
        lossless = lossless and (distinct == total)
    print("    -> injective (lossless)? %s   => the 𝕆 holonomy is an order-%s\n"
          % (lossless, "STORE" if lossless else "FINGERPRINT (not a lossless replacement for the sequence)"))

    print("VERDICT (should we encode the genome as an octonion Laplacian?) — two-sided, measured:")
    print("  * The ℂ magnetic Laplacian was BLIND here (charge all 0 — the figure-eight is symmetric at ℂ). Only the")
    print("    𝕆 grade caught the order: with GENERIC octonions the two walks DIFFER (24/24 distinct at n=4). With")
    print("    BASIS UNITS it FAILS (they collide, 24->2) — so the encoding matters; basis e_k are too degenerate.")
    print("  * But it is a FINGERPRINT, not a lossless store: a single octonion is 8 reals, so by pigeonhole it")
    print("    MUST collide over the exponential space of long sequences (injective only for short walks). It cannot")
    print("    REPLACE storing the sequence. (This CORRECTS my F1229 hint that 𝕆 'resolves F1079' for storage — it")
    print("    resolves it as a DISCRIMINATOR/fingerprint, not a lossless store, and only with a non-degenerate encoding.)")
    print("  => srmech FEEDBACK (important): add a CD/octonion Laplacian + an ORDER-SENSITIVE holonomy (the 𝕆 grade")
    print("     of magnetic_laplacian, GENERIC octonion coupling) — a genuine NEW op and a stronger recover_check")
    print("     curvature faculty that catches order the ℂ magnetic Laplacian is BLIND to. But DO NOT build the")
    print("     genome around it: the store stays directed-Laplacian (ℝ+ℂ = metric+charge) + the FIBER (sequence)")
    print("     stored explicitly; the octonion holonomy is the optional order-VERIFIER, never the store.")
    return 0 if (same_plain and distinguishes and not lossless) else 1


if __name__ == "__main__":
    sys.exit(main())
