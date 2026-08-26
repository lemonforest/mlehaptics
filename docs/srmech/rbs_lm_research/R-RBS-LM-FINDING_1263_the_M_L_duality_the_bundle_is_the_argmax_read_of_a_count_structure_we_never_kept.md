# F1263 — the Class-M / Class-L duality, made concrete and measured: **`klein4_bundle` is the argmax READ of a per-coordinate COUNT structure we never stored.** Keeping the counts lifts recall **11× at N=1200** (0.040 → 0.440) and holds **1.000 at N=256** where the bundle has already fallen to 0.731. The loss was never "Class-M is lossy" — it was **compression**, exactly as `[[project_class_L_store_class_M_working_memory_reversible_spectral_bridge]]` already stated. The count matrix IS the Class-L-side object; the bundle is its transient distributional read.

**User (2026-07-20):** *"the desire to at least test the simulation is if we can find the duality of class-M and class-L — class-M doesn't have to be lossy anymore, like we're forgetting or dropping some value we could keep, maybe to make the math over class-M work over more than just the local horizon … for the many-at-once thing."*

## The dropped value, named
`klein4_bundle` takes N vectors and emits a **majority sector per coordinate**. It discards **how many voted** — the per-coordinate histogram over the 4 Klein-4 sectors. That histogram is the whole superposition; the bundle is one projection of it.

So a bundle is not a *store*. It is an **argmax read of a store that was never written**.

Our own record already said this and we did not act on it: *"bridge = reversible basis-change; **reversibility in change-of-basis, loss in compression**; distributional is always a transient READ of the relational store"* (F1216). The bundle IS the transient read. **We have been storing the read instead of the store** — the same shape as `[[feedback_sparse_complete_never_top_k_truncation_at_storage]]` ("top-K is a read, never a storage cut"), one layer down.

## Measured (D=4096, key-bound pairs, nearest-candidate recall@1)
| N | `klein4_bundle` | count-preserving | lift |
|---|---|---|---|
| 64 | 1.000 | 1.000 | — |
| 256 | 0.731 | **1.000** | +0.269 |
| 512 | 0.538 | **0.962** | +0.424 |
| 1200 | 0.040 | **0.440** | **11×** |

**The horizon moves a long way out.** At N=256 the bundle has already lost a quarter of its recall while the count structure is still perfect; at N=1200 the bundle is effectively dead and the counts still work.

## But it is NOT lossless — and the residue names the next problem
Count-preserving recall still decays (1.000 → 0.962 → 0.440). Two losses were superposed and only one is removed:

1. **Quantization loss** — the majority vote discarding margins. **Removed** by keeping counts. This is the 11×.
2. **Code-collision loss** — random carriers are only *quasi*-orthogonal, so votes from non-target items genuinely accumulate. **Not removed**, and not removable by storage: it is the **sidelobe** of the code family, i.e. exactly the F1259 question (drawn family vs designed family, worst-case sector agreement).

So the honest chain is: **counts remove the compression loss; a designed carrier family would be what attacks the remaining collision loss.** F1259's negative (Weyl and Walsh both lose to the RNG on worst-case sector agreement) is therefore not a dead end — it is the *next* lever on this same curve, and now it has a measured reason to exist.

## The duality, stated
| | object | character |
|---|---|---|
| **Class-L side** | the count matrix `C[coordinate][sector]` | a **weighted bipartite structure** — exact, additive, GROWS with content |
| **Class-M side** | `klein4_bundle(...)` | the **argmax projection** of that structure — bounded, fuzzy, decaying |

The count matrix is a weighted adjacency: coordinate × sector with integer weights. That **is** a Class-L object. So the M/L duality at the carrier layer is not an analogy — the bundle is literally a lossy read of a Class-L object, and the "reversible bridge" F1216 describes is the identity map onto the counts, with the argmax as the only lossy step.

This also re-reads the melange discipline (F1205) consistently: **you couple L-side objects and discard the coupling; you do not merge M-side reads.** Many-at-once belongs on the L side by construction.

## Costs, stated honestly
- **Storage:** bundle = D bytes; counts = D×4 integers (~4–16× depending on width). Likely compressible — most coordinates concentrate — but that is unmeasured.
- **Read cost:** the counts read scores each candidate against the full count matrix, O(N·D) per probe versus the bundle's single unbind-then-compare. **The count read is materially more expensive**, and this measurement did not optimise it. A sparse or indexed read is the obvious next step and is untested.
- **Not a drop-in replacement:** this changes what is *stored*, so any existing bundle-based store would need rebuilding.

## Verdict / next
**The user's hypothesis is confirmed and the mechanism is named:** Class-M is not inherently lossy; `klein4_bundle` compresses, and the compression is where the local horizon comes from. Keeping the per-coordinate counts is a **storage change, not a math change**, and it buys an 11× recall lift at N=1200.

**NEXT:** (1) push N to 10⁴–10⁵ to find where the count structure's *own* horizon sits; (2) measure sparsity of the count matrix — if concentrated, the 4× storage claim is pessimistic; (3) an indexed/sparse read to kill the O(N·D) probe cost; (4) re-open F1259's designed-family question against the residual **collision** loss, which is now the dominant term rather than a theoretical nicety.

Composes **F1216** (`[[project_class_L_store_class_M_working_memory_reversible_spectral_bridge]]` — which stated "loss in compression" and is here made concrete), **F1259** (the sidelobe/designed-family question, now with a measured motivation), **F1261** (the bundle-width measurement that raised the horizon question), **F1205/#263** (melange — couple on the L side), `[[feedback_sparse_complete_never_top_k_truncation_at_storage]]`, `[[feedback_relational_not_dense_distributional_not_sparse]]`, `[[feedback_read_independent_structure_check_first]]`, #231/PKG-3.
