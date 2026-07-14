r"""R-RBS-LM-OCTRECOVER (F1231 / #1390 item-4 upgrade) — the OCTONION ORDER FACULTY for recover_check.

The 5th faculty (on top of op/operand/responsion/ℂ-curvature, F1225): an ORDER-sensitive check that catches a
walk-order corruption the graph-level faculties are BLIND to (F1230: two orders can share the identical directed
graph — the F1079 ambiguity; the ℂ magnetic Laplacian sees a symmetric graph and passes them both).

Mechanism (F1229/F1230): a compact `order_fingerprint(fiber)` = the path-ordered product of a GENERIC octonion per
node along the walk (basis units are degenerate — F1230). 8 ints, independent of walk length. Store it beside the
genome; on recall, recompute from the recovered fiber and compare:
  * match   -> the walk-ORDER survived the round-trip (or the graph uniquely determined it).
  * mismatch-> the order is wrong / not recoverable from the graph alone (F1079) -> the fiber MUST be stored explicitly.
It is a VERIFIER (a lossy fingerprint, F1230), never a store — exactly the srmech-feedback role.

srmech 0.9.0rc241 (qm.so8.octonion_mult_table). Exact ints; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-OCTRECOVER_...py
"""
import importlib.util
import sys
from pathlib import Path

from srmech.qm.so8 import octonion_mult_table

HERE = Path(__file__).parent
C = octonion_mult_table()


def _omul(a, b):
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


def node_octonion(node_id):
    """A deterministic GENERIC octonion per node — real part 1 + seven DISTINCT-per-axis id-derived imaginary parts.
    Each axis uses its own multiplier+offset+modulus so the components do NOT collapse to a uniform value (the
    `node_id % m` form degenerates for small ids: 1%m==1 ∀m -> [1,2,2,2,2,2,2,2], as bad as a basis unit — F1230)."""
    out = [1]
    for k in range(7):
        out.append(1 + ((node_id * (2 * k + 3) + (5 * k + 1)) % (11 + 2 * k)))
    return out


def order_fingerprint(fiber_ids):
    """The path-ORDERED octonion product along the walk = an order-sensitive fingerprint of the fiber (8 ints,
    length-independent). Class-K/-C composition of Class-A node atoms; the ℍ/𝕆 grade of the walk (F1229)."""
    acc = [1, 0, 0, 0, 0, 0, 0, 0]
    for nid in fiber_ids:
        acc = _omul(acc, node_octonion(nid))
    return acc


# ---------- the faculty ----------
def recover_check_order(true_fingerprint, recovered_fiber_ids):
    """PASS iff the recovered fiber reproduces the stored order fingerprint. Catches an order corruption / F1079
    graph-ambiguity that op/operand/responsion/ℂ-curvature all pass."""
    return order_fingerprint(recovered_fiber_ids) == list(true_fingerprint)


def _load(stem):
    p = HERE / stem
    spec = importlib.util.spec_from_file_location(stem.split("_")[0].replace("-", ""), str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    print("=== R-RBS-LM-OCTRECOVER — the octonion ORDER faculty for recover_check (item-4 upgrade) ===\n")
    N = _load("R-RBS-LM-NIVDIRECTED_word_as_directed_glyph_graph_genome_native.py")
    RC = _load("R-RBS-LM-RECOVERCHECK_prototype_general_class_l_genome_recover_check_four_faculties.py")

    # (A) the HEADLINE: an order corruption the graph-level faculties are BLIND to, the octonion faculty CATCHES.
    #     figure-eight: two walks, IDENTICAL directed graph (charge 0 -> even the ℂ magnetic Laplacian is blind).
    print("(A) order corruption that shares the SAME graph (F1079 / F1230) — graph faculties blind, order faculty catches:")
    walkA = [0, 1, 0, 2, 0]                                       # 0->1->0->2->0
    walkB = [0, 2, 0, 1, 0]                                       # a graph-preserving reorder (the 'corruption')
    edges = [(0, 1), (0, 2)]
    metric = [2, 2]
    charge = [0, 0]                                               # symmetric -> the ℂ curvature faculty sees nothing
    graph_v = RC.recover_check(3, edges, metric, charge)          # the 4 graph-level faculties on the shared graph
    fpA = order_fingerprint(walkA)                                # stored (true) order fingerprint
    order_ok_true = recover_check_order(fpA, walkA)               # honest recall of the right order
    order_ok_corrupt = recover_check_order(fpA, walkB)            # the graph-preserving reorder
    print("    graph-level recover_check (op/operand/responsion/ℂ-curvature): ok=%s curvature=%s"
          % (graph_v["ok"], graph_v["curvature"]["verdict"]))
    print("    -> the graph faculties PASS both walks (blind to order).")
    print("    octonion ORDER faculty: true-order recall PASS=%s ; graph-preserving REORDER PASS=%s"
          % (order_ok_true, order_ok_corrupt))
    print("    -> the octonion faculty CATCHES the reorder (%s) the ℂ curvature (%s) missed.\n"
          % ("caught" if not order_ok_corrupt else "MISSED", "blind" if not graph_v["curvature"]["directed"] else "saw it"))

    # (B) OPERATIONAL use on real word kernels: does the graph alone determine the order? (F1079 flag)
    print("(B) real word kernels — recover the graph, Eulerian-walk it, does the order fingerprint match the true walk?")
    print("    (match => graph determined the order; MISMATCH => order-ambiguous, the fiber MUST be stored explicitly)")
    words = "cat level committee banana mississippi vanuatu".split()
    for w in words:
        k = N.word_to_kernel(w)
        true_ids = [N.GI[c] for c in w.lower() if c in N.GI]     # the TRUE fiber (the word's glyph sequence)
        fp = order_fingerprint(true_ids)                         # the stored fingerprint (8 ints, tiny)
        recon = N.eulerian_word(k)                               # the order recovered from the GRAPH alone
        recon_ids = [N.GI[c] for c in recon if c in N.GI]
        ok = recover_check_order(fp, recon_ids)
        print("    %-12s graph-recovered order %r -> fingerprint %s true"
              % (w, recon, "==" if ok else "!= (AMBIGUOUS -> store the fiber)"))

    print("\n(C) the faculty is a compact VERIFIER, not a store: the fingerprint is 8 ints regardless of walk length")
    print("    (fp('mississippi') and fp('cat') are both 8 ints) — lossy by pigeonhole (F1230), so it verifies order,")
    print("    it does not store it. The fiber stays the store; this is the order-integrity guard on top.")

    verdict = (graph_v["ok"] and order_ok_true and not order_ok_corrupt)
    print("\nVERDICT: %s — recover_check_order is the 5th faculty: a generic-octonion order fingerprint that CATCHES a"
          % ("PASS" if verdict else "FAIL — investigate"))
    print("         graph-preserving reorder the op/operand/responsion/ℂ-curvature faculties are blind to, and")
    print("         operationally FLAGS the F1079-ambiguous words where the fiber must be stored. A stronger")
    print("         recover_check curvature tier (the 𝕆 grade), VERIFIER-only. Ready as the #1390 item-4 upgrade.")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
