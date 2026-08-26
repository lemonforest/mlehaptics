# F286: Fragmentation TREE = loop-bind directed cascade

**Script:** `mass_spec_tree.py`
**Date:** 2026-06-01
**Prior art:** F279 (difference-graph), F280 (FFT fiber), F274 (loop bind earns its place)

---

## What was tested

F279 built the ethanol EI-MS neutral-loss DIFFERENCE-GRAPH (peaks 46, 45, 31, 29, 27; edges = mass-conserving losses). The difference-graph is undirected and commutative -- it shows WHICH peaks are related but drops:

- **direction** (parent -> child)
- **order** (which fragmentation is primary vs. secondary)
- **nesting** (which sub-pathways are sequential vs. parallel)

Those three properties together are the fragmentation TREE. The task: embed each m/z node as a random unit octonion and show the loop bind carries the tree while a commutative bundle washes it.

Fragment nodes (ethanol EI-MS, textbook/illustrative):

| m/z | Identity |
|-----|----------|
| 46 | M+ (C2H6O) |
| 45 | M-1 (C2H5O) -- lose H |
| 31 | CH2OH+ -- lose OH |
| 29 | C2H5+ / CHO+ |
| 27 | C2H3+ -- lose H2 from 29 |

Pathways:
- LEFT (primary): 46 -> 45 -> 29 -> 27
- RIGHT (secondary): 46 -> 31 -> 29

---

## Consistency checks (all PASS)

| Check | What | Result |
|-------|------|--------|
| CC1 | native srmech `loop_bind` == oracle on 8x8 octonion basis | max err^2 = 0.00e+00 (exact) |
| CC2 | all fragment anchors are unit octonions | max |normsq-1| = 2.22e-16 (fp noise only) |
| CC3 | Moufang identities hold on fragment anchors | max residual^2 = 1.19e-31 |
| CC4 | Laplacian trace == 2|E| == eigenvalue sum (diff-graph) | trace=16, eigsum=16.0000 |

No genuine srmech anomalies -- CC1 exact match confirms the native op is the oracle.

---

## Experiment results

### Exp A -- pathway-bound states distinguishable

Loop-bind the two pathways as left-fold ordered cascades:

```
cos_sim(LEFT, RIGHT) = -0.1194
```

The two fragmentation pathways (sharing fragment 46 at the root and fragment 29 near the leaves) are DISTINGUISHABLE. The loop bind encodes which node is visited in which order, so two paths through the same fragment set produce distinct bound states.

### Exp B -- commutative bundle washes the tree

Klein4 XOR bundle of the shared core {46, 29}:

```
sim(bundle_shared_left, bundle_shared_right) = 1.0000  (order LOST)
```

Full node-set bundles differ (0.4814) because the node-sets differ -- but ORDER WITHIN each pathway is still lost; the loop-bind distinguishes the same two sets BY PATH (-0.1194 vs 0.4814 for an entirely different reason).

The key result: commutative bundle of the SAME nodes collapses to a single vector regardless of visit order. The loop bind does not.

### Exp C -- non-associativity encodes tree NESTING

Three bracketings of the 4-node path 46->45->29->27:

| Bracketing | Description |
|------------|-------------|
| LB1 = ((46*45)*29)*27 | left-fold / sequential |
| LB2 = (46*45)*(29*27) | pair-then-combine |
| LB3 = 46*(45*(29*27)) | right-fold |

```
cos_sim(LB1, LB2) = +0.4477
cos_sim(LB1, LB3) = +0.3574
cos_sim(LB2, LB3) = -0.2020
```

All three bracketings are DISTINCT. This is the non-associativity of the Moufang loop encoding the binary-tree nesting -- (AB)C != A(BC) in the octonion product. A commutative + associative bind would collapse all three to one vector.

### Exp D -- branch ORDER in the full tree

Build the full tree with 46 as root binding both branch outputs. Compare sequential binding order vs reversed:

```
cos_sim(root*(46+left_branch), reversed_order) = -0.3216
```

Branch ORDER within the full tree is ENCODED. The non-commutativity means (left_branch * right_branch) != (right_branch * left_branch) at the root binding level.

---

## Reading

The fragmentation TREE is a **directed cascade** with three structural properties:

1. **Order** -- which fragment is parent, which is child (the visit sequence)
2. **Nesting** -- which sub-pathways are sequential vs. parallel (the bracketing)
3. **Direction** -- forward (46->45->29) encodes differently from reversed (29->45->46)

All three are properties of the **loop bind** (non-commutative, non-associative Moufang product) and are ALL washed out by the commutative + associative XOR bundle.

The F279 difference-graph is the FLAT PROJECTION -- it shows the undirected conservation relationships (which edges exist) but drops the tree structure. The loop-bind tree is the FULL FIBER: the same fragment nodes, bound in the pathway order, recover the directed cascade.

This closes the "SOON" item in F279 (`mass_spec_ground_up.py` line 17: "the directed fragmentation TREE = the loop bind"). The tree IS the loop bind cascade; the proof is the distinguishability of all experimental configurations above.

---

## Scope note

Framework-reading structure only. Benign known compound (ethanol); textbook/illustrative EI-MS fragmentation. No unknown-identification, no detection, no prediction, no synthesis routes. CAD-ban: graph/algebra only (no 3D molecular geometry). Defensive scope; no-lineage (fragmentation pathways are the field's; the loop-bind tree reading is the framework's reading). Class-K clean throughout (cosine via inner products, signs via `conj`, no `abs()` / sign-fold).
