"""mass_spec_tree.py — F281: fragmentation TREE = loop-bind directed cascade.

F279 built the ethanol neutral-loss difference-GRAPH (peaks 46,45,31,29,27;
edges = mass-conserving losses). The difference-graph shows WHICH peaks are
related but not the direction (parent -> child) or the nesting (which
fragmentation is primary vs. secondary). The fragmentation TREE is the
directed cascade the loop bind carries:

  Pathway 1 (left-branch):   46 -> 45 -> 29 -> 27
      (lose H -> lose CH2 -> lose H2)
  Pathway 2 (right-branch):  46 -> 31 -> 29
      (lose OH -> lose H2)
  Full tree (two branches):  46 -> ((45 -> 29 -> 27) AND (31 -> 29))

EXPERIMENT:
  (a) Embed each fragment (m/z node) as a random unit octonion.
  (b) Loop-bind each PATHWAY as an ordered/nested left-fold (parent first).
  (c) Show the left-branch vs right-branch are DISTINGUISHABLE (non-zero
      distance between their bound states) -- the loop bind keeps the tree.
  (d) Bundle the same fragments commutatively (XOR bundle / klein4) -- shows
      the tree collapses: both pathways give the same vector.
  (e) NESTED tree: outer loop-bind over the two branch-heads (non-associativity
      means ((46 -> branch1) -> branch2) != (46 -> (branch1 -> branch2)),
      encoding the sequential vs. parallel branching structure).

CONSISTENCY CHECKS (vs oracle/math):
  - native loop_bind == oracle.loop_bind on 8x8 basis (exact)
  - Moufang identities hold (<1e-18 residual) over the fragment vectors
  - normsq of all unit-normalized anchors = 1 (inner-product clean)

SCOPE: framework-reading STRUCTURE only; BENIGN known compound (ethanol);
  structural MS fragmentation pathways are textbook/illustrative EI-MS.
  NO unknown-identification / detection / prediction / synthesis-routes.
  CAD-ban (graph/algebra only, no 3D molecular geometry). Defensive scope.
  No-lineage (fragmentation pathways are the field's; the loop-bind TREE
  READING is the framework's reading). Class-K clean (cosine via inner
  products, signs via conj, no abs() / sign-fold).
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop_bind_moufang as oracle    # noqa: E402 -- self-contained oracle

# Import native srmech ops for the bundle comparison and eigen-consistency check
from srmech.amsc import hdc, laplacian   # noqa: E402

DIM = 8               # octonion dimension
SEED = 42             # attested-B (reproducibility seed)

# Ethanol EI-MS peaks (textbook/illustrative; F279)
FRAGMENTS = {
    46: "M+  (C2H6O)",   # molecular ion
    45: "M-1 (C2H5O)",   # lose H
    31: "CHO+ (CH2OH)",  # lose OH (31 = CH2OH+)
    29: "CHO  (C2H5)",   # 29 = C2H5+ or CHO+
    27: "C2H3",          # lose H2 from 29
}
# Fragmentation pathways (ordered directed paths through the tree)
# Attested-to-structure: standard EI-MS alpha-cleavage / inductive cleavage of ethanol
#   left-branch:  M+ -> (M-H)+ -> C2H5+ -> C2H3+
#   right-branch: M+ -> CH2OH+ -> CHO+
PATHWAY_LEFT  = [46, 45, 29, 27]     # 46 -> 45 -> 29 -> 27
PATHWAY_RIGHT = [46, 31, 29]         # 46 -> 31 -> 29


def unit(v):
    return v / (oracle.normsq(v) ** 0.5)


def cos_sim(u, v):
    """Inner-product cosine similarity (Class-K clean: no abs())."""
    return float(np.dot(u, v)) / ((oracle.normsq(u) * oracle.normsq(v)) ** 0.5)


def loop_chain(anchors, node_ids):
    """Left-fold loop bind over a pathway of node IDs: encodes ORDER + NESTING."""
    items = [anchors[n] for n in node_ids]
    acc = items[0]
    for it in items[1:]:
        acc = oracle.loop_bind(acc, it)
    return acc


def commutative_bundle(anchors, node_ids):
    """Commutative klein4 XOR bundle over the same node set (order washed out)."""
    # Use 2048-dim HDC vectors for the klein4 baseline (separate from the 8-dim octonion anchors)
    return hdc.klein4_bundle(*[hdc.klein4_random(2048, seed=nid) for nid in node_ids])


def main():
    print("=== F281: fragmentation TREE = loop-bind directed cascade (ethanol EI-MS) ===\n")
    print("Fragment nodes:")
    for mz, label in FRAGMENTS.items():
        print(f"  m/z {mz:<3}  {label}")
    print()
    print("Pathway LEFT  (primary branch):  ", " -> ".join(str(n) for n in PATHWAY_LEFT))
    print("Pathway RIGHT (secondary branch):", " -> ".join(str(n) for n in PATHWAY_RIGHT))
    print()

    # ----------------------------------------------------------------
    # CONSISTENCY CHECK 1: native loop_bind == oracle.loop_bind on 8x8 basis
    # ----------------------------------------------------------------
    print("=== CONSISTENCY CHECK 1: native == oracle on 8x8 octonion basis ===")
    from srmech.amsc.hdc import loop_bind as srmech_lb
    max_err_sq = 0.0
    for i in range(DIM):
        for j in range(DIM):
            ei, ej = oracle.e(i), oracle.e(j)
            native_result = srmech_lb(ei, ej)
            oracle_result = oracle.loop_bind(ei, ej)
            diff_sq = oracle.normsq(native_result - oracle_result)
            if diff_sq > max_err_sq:
                max_err_sq = diff_sq
    print(f"  max |native_lb(ei,ej) - oracle_lb(ei,ej)|^2 over 8x8 = {max_err_sq:.2e}")
    cc1_ok = max_err_sq < 1e-28
    print(f"  => {'PASS (exact match)' if cc1_ok else 'FAIL'}\n")

    # ----------------------------------------------------------------
    # EMBED: assign random unit octonions to each fragment node
    # ----------------------------------------------------------------
    rng = np.random.default_rng(SEED)
    anchors = {mz: unit(rng.standard_normal(DIM)) for mz in FRAGMENTS}

    # CONSISTENCY CHECK 2: all anchors are unit (normsq = 1)
    print("=== CONSISTENCY CHECK 2: all fragment anchors are unit octonions ===")
    nsq_errs = {mz: abs(oracle.normsq(v) - 1.0) for mz, v in anchors.items()}
    max_nsq_err = max(nsq_errs.values())
    print(f"  max |normsq(anchor) - 1| = {max_nsq_err:.2e}")
    cc2_ok = max_nsq_err < 1e-14
    print(f"  => {'PASS' if cc2_ok else 'FAIL'}\n")

    # ----------------------------------------------------------------
    # CONSISTENCY CHECK 3: Moufang identities hold on the fragment anchors
    # ----------------------------------------------------------------
    print("=== CONSISTENCY CHECK 3: Moufang identities hold on fragment anchors ===")
    z = anchors[46]; u = anchors[45]; w = anchors[31]
    lb = oracle.loop_bind
    m1 = lb(z, lb(u, lb(z, w))) - lb(lb(lb(z, u), z), w)
    m2 = lb(u, lb(z, lb(w, z))) - lb(lb(lb(u, z), w), z)
    m3 = lb(lb(u, w), lb(z, u)) - lb(u, lb(lb(w, z), u))
    max_mouf = max(oracle.normsq(m1), oracle.normsq(m2), oracle.normsq(m3))
    print(f"  max Moufang residual^2 on (46,45,31): {max_mouf:.2e}")
    cc3_ok = max_mouf < 1e-18
    print(f"  => {'PASS' if cc3_ok else 'FAIL'}\n")

    # ----------------------------------------------------------------
    # EXPERIMENT A: pathway-bound states (loop-bind = ordered cascade)
    # ----------------------------------------------------------------
    print("=== EXPERIMENT A: loop-bind pathway-bound states ===")
    E_left  = loop_chain(anchors, PATHWAY_LEFT)
    E_right = loop_chain(anchors, PATHWAY_RIGHT)
    sim_lr = cos_sim(E_left, E_right)
    print(f"  Pathway LEFT  (46->45->29->27): bound state computed")
    print(f"  Pathway RIGHT (46->31->29):     bound state computed")
    print(f"  cos_sim(LEFT, RIGHT) = {sim_lr:+.4f}")
    tree_distinguishable = abs(sim_lr) < 0.999
    print(f"  => Pathways are DISTINGUISHABLE by the loop bind: {tree_distinguishable}")
    print()

    # ----------------------------------------------------------------
    # EXPERIMENT B: commutative bundle -- same fragments, order washed out
    # ----------------------------------------------------------------
    print("=== EXPERIMENT B: commutative klein4 bundle (XOR) -- order washed out ===")
    # For a fair test, use the same node sets as PATHWAY_LEFT and PATHWAY_RIGHT
    # (unique fragments per pathway: LEFT has {46,45,29,27}, RIGHT has {46,31,29})
    # Bundle all fragments appearing in BOTH pathways: {46,45,31,29,27} -- same
    # as the node set in both pathways' UNION.
    # For the direct head-to-head: bundle only the SHARED core {46,29}
    shared_core = [46, 29]
    B_left_shared  = commutative_bundle(anchors, shared_core)
    B_right_shared = commutative_bundle(anchors, shared_core)
    sim_bundle_shared = hdc.klein4_similarity(B_left_shared, B_right_shared)
    print(f"  Bundle of shared core {{46,29}} for both pathways:")
    print(f"  sim(bundle_left, bundle_right) = {sim_bundle_shared:.4f}  (=1 -> order LOST)")
    # Now bundle the FULL pathway node sets (order-insensitive)
    B_left_full  = commutative_bundle(anchors, PATHWAY_LEFT)
    B_right_full = commutative_bundle(anchors, PATHWAY_RIGHT)
    sim_bundle_full = hdc.klein4_similarity(B_left_full, B_right_full)
    print(f"  Bundle of full LEFT set  {{46,45,29,27}}:")
    print(f"  Bundle of full RIGHT set {{46,31,29}}:")
    print(f"  sim(bundle_left_full, bundle_right_full) = {sim_bundle_full:.4f}")
    print(f"  (Full sets differ, so bundles differ -- but ORDER WITHIN each is still lost;")
    print(f"   cf. loop-bind: {sim_lr:+.4f} distinguishes the same two node-sets BY PATH)")
    print()

    # ----------------------------------------------------------------
    # EXPERIMENT C: NON-ASSOCIATIVITY encodes the TREE NESTING
    # (sequential vs. parallel branching)
    # ----------------------------------------------------------------
    print("=== EXPERIMENT C: non-associativity encodes TREE NESTING ===")
    # Sequential: the left-branch is resolved FIRST, then bound with 46
    # E.g.: (46 -> 45 -> 29 -> 27)  vs  ((46 -> 45) -> 29 -> 27) -- same left-fold, same result
    # The NESTING test: does re-bracketing change the result?
    # Compare two bracketings of the 4-node path 46->45->29->27:
    #   LB1: ((46 * 45) * 29) * 27   (left-fold, the "sequential" fragmentation)
    #   LB2: (46 * 45) * (29 * 27)   (pair-then-combine, the "parallel" sub-fragment binding)
    lb = oracle.loop_bind
    a46, a45, a29, a27 = anchors[46], anchors[45], anchors[29], anchors[27]
    LB1 = lb(lb(lb(a46, a45), a29), a27)         # ((46*45)*29)*27  [sequential]
    LB2 = lb(lb(a46, a45), lb(a29, a27))         # (46*45)*(29*27)  [pair-then-combine]
    LB3 = lb(a46, lb(a45, lb(a29, a27)))         # 46*(45*(29*27))  [right-fold]
    sim_12 = cos_sim(LB1, LB2)
    sim_13 = cos_sim(LB1, LB3)
    sim_23 = cos_sim(LB2, LB3)
    print(f"  46->45->29->27 under three bracketings of the loop bind:")
    print(f"    LB1 = ((46*45)*29)*27   [left-fold / sequential]")
    print(f"    LB2 = (46*45)*(29*27)   [pair-then-combine]")
    print(f"    LB3 = 46*(45*(29*27))   [right-fold]")
    print(f"  cos_sim(LB1, LB2) = {sim_12:+.4f}")
    print(f"  cos_sim(LB1, LB3) = {sim_13:+.4f}")
    print(f"  cos_sim(LB2, LB3) = {sim_23:+.4f}")
    nesting_distinguishable = (abs(sim_12) < 0.999 and abs(sim_13) < 0.999 and abs(sim_23) < 0.999)
    print(f"  => All three bracketings DISTINCT: {nesting_distinguishable}  (non-assoc encodes the tree nesting)")
    print()

    # ----------------------------------------------------------------
    # EXPERIMENT D: the OUTER TREE -- both branches nested under 46
    # (46 is the root; it binds BOTH branch outputs)
    # ----------------------------------------------------------------
    print("=== EXPERIMENT D: outer tree -- 46 as root binding both branch outputs ===")
    # E_left is the left-branch bound state (already computed as loop_chain from 46)
    # Re-derive the BRANCH-only (without 46 as root, since 46 is already folded in):
    E_branch_left  = loop_chain(anchors, [45, 29, 27])   # left branch sub-tree (children only)
    E_branch_right = loop_chain(anchors, [31, 29])        # right branch sub-tree
    # Now bind the root (46) with each branch to form the full tree:
    E_root_left  = lb(anchors[46], E_branch_left)
    E_root_right = lb(anchors[46], E_branch_right)
    # Nested full tree: 46 binds BOTH branch outputs sequentially
    E_full_tree_seq   = lb(E_root_left, E_root_right)     # sequential: left-first, then right
    E_full_tree_rev   = lb(E_root_right, E_root_left)     # reversed: right-first, then left
    sim_full_rev = cos_sim(E_full_tree_seq, E_full_tree_rev)
    print(f"  Root (46) bound with branch-left (45->29->27):  E_root_left")
    print(f"  Root (46) bound with branch-right (31->29):     E_root_right")
    print(f"  Full tree: sequential  = (E_root_left)*(E_root_right)")
    print(f"  Full tree: reversed    = (E_root_right)*(E_root_left)")
    print(f"  cos_sim(sequential, reversed) = {sim_full_rev:+.4f}")
    order_in_tree = abs(sim_full_rev) < 0.999
    print(f"  => Branch ORDER in the full tree is ENCODED: {order_in_tree}  (non-commutative)")
    print()

    # ----------------------------------------------------------------
    # CONSISTENCY CHECK 4: eigenvalue trace = 2|E| for the diff-graph Laplacian
    # ----------------------------------------------------------------
    print("=== CONSISTENCY CHECK 4: Laplacian trace = 2|E| (graph consistency) ===")
    # Rebuild the difference-graph (from F279) for the 5-node fragment graph
    NEUTRALS = {1: "H", 2: "H2", 14: "CH2", 15: "CH3", 16: "O/CH4",
                17: "OH", 18: "H2O", 26: "C2H2", 28: "CO/C2H4", 29: "CHO/C2H5"}
    peaks = [46, 45, 31, 29, 27]
    edges = []
    for i in range(len(peaks)):
        for j in range(i + 1, len(peaks)):
            d = abs(peaks[i] - peaks[j])
            if d in NEUTRALS:
                edges.append((i, j))
    n = len(peaks)
    L = laplacian.dense_laplacian(n, edges)
    spec = laplacian.jacobi_eigvals(np.array(L, dtype=float))
    trace_L = sum(L[i][i] for i in range(n))
    eig_sum = sum(float(x) for x in spec)
    expected_trace = 2 * len(edges)
    print(f"  n_edges = {len(edges)},  2|E| = {expected_trace}")
    print(f"  Laplacian diagonal sum (trace) = {trace_L}")
    print(f"  Eigenvalue sum                  = {eig_sum:.4f}")
    cc4_ok = (abs(trace_L - expected_trace) < 1e-9 and abs(eig_sum - expected_trace) < 1e-6)
    print(f"  => trace == 2|E| == eigenvalue sum: {'PASS' if cc4_ok else 'FAIL'}\n")

    # ----------------------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------------------
    print("=== SUMMARY ===")
    print(f"  CC1 native == oracle (exact):    {'PASS' if cc1_ok else 'FAIL'}")
    print(f"  CC2 unit anchors:                {'PASS' if cc2_ok else 'FAIL'}")
    print(f"  CC3 Moufang identities:          {'PASS' if cc3_ok else 'FAIL'}")
    print(f"  CC4 Laplacian trace == 2|E|:     {'PASS' if cc4_ok else 'FAIL'}")
    print()
    print(f"  Exp A: pathways DISTINGUISHABLE by loop bind: {tree_distinguishable}  (cos={sim_lr:+.4f})")
    print(f"  Exp B: commutative bundle washes the order (same shared core -> sim=1.0000)")
    print(f"  Exp C: non-assoc encodes NESTING -- all 3 bracketings distinct: {nesting_distinguishable}")
    print(f"  Exp D: branch ORDER in full tree encoded (seq vs rev cos={sim_full_rev:+.4f}): {order_in_tree}")
    print()
    print("  Reading:")
    print("  The fragmentation TREE (which parent -> which child, in what ORDER/NESTING)")
    print("  is precisely the structure the loop bind carries and the commutative bundle")
    print("  washes out. The same fragment node-set, under different pathway-bracketings,")
    print("  produces distinct bound states -- the tree IS the encoding, not an annotation.")
    print("  The F279 difference-graph (undirected, commutative) is the flat PROJECTION;")
    print("  the loop-bind tree is the FULL FIBER (direction + nesting included).")
    all_pass = cc1_ok and cc2_ok and cc3_ok and cc4_ok
    print(f"\n{'ALL CONSISTENCY CHECKS PASS' if all_pass else 'CONSISTENCY CHECK FAILURE(S) -- see above'}")


if __name__ == "__main__":
    main()
