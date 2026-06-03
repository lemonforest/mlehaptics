# R-RBS-LM Finding 342 — #855 R2: the "(4+3) projection chain" is NOT a single restriction — it crosses F196's TWO-RUNG nesting (store rung: bipolar ⊂ Klein-4; fiber rung: 7=4+3 Hopf where loop-bind lives)

**Date:** 2026-06-03 · **srmech:** 0.7.0rc25 (anchors verified) · **#855 block:** R2 (the "keep both" = (4+3) fiber bundle) · **grounds:** F124 (quaternionic Hopf), F196 (chirality is nested), F197/F126 (G₂⊃SU(3) 14=8+3+3̄), F200 (Klein-4 = order-2 store rung), F186 (28=14+7+7 bounded), F341 (R1: loop=fiber, Klein-4=store)

## What R2 had to verify (and the flag I set)

#855 R2 stated: "keep both" is the **(4+3) fiber bundle** — bipolar = base-projection, Klein-4/native = total space, fiber = spatially-absent chirality; quaternionic Hopf `7 = 4 + 3` (F124). I explicitly flagged the rung-to-rung bookkeeping as **verify-before-asserting**: do not claim a literal single restriction chain `28 → 7=(4+3) → Klein-4(4) → bipolar(γ₅)` unchecked, because the Klein-4 store and the Hopf split may live at different levels of F196's nesting. **They do.** This finding records the verified, refined structure.

## srmech rc25 dimension anchors (all confirmed)

| object | srmech (rc25) | reading |
|---|---|---|
| `so8.so8_adjoint_basis()` | **28** | the full chirality algebra 𝔰𝔬(8) (F158 bi-axial 28D) |
| `so8.g2_subalgebra()` | **14** | G₂ = Der(𝕆) = Fix(τ) (the A–N invariant core) |
| `so8.an_embedding()` | su3=**8**, triplet=**3**, antitriplet=**3** | G₂ ⊃ SU(3): **14 = 8 ⊕ 3 ⊕ 3̄** (algebra-level chirality-dual, F197/F126) |
| `triality.triality_automorphism()` | **τ³=I** (3.66e-15) | the algebra chirality is **order-3** |
| Klein-4 (`KLEIN4_STATES`, F200) | **4** sectors (γ₅ × iω₇) | the store chirality is **order-2** (Z₂×Z₂) |
| Hopf (F124, attested) | `S³ → S⁷ → S⁴` = **3 + 4 = 7** | the 7 octonion-imaginary dirs split fiber-3 + base-4 |
| `28 = 14 ⊕ 7 ⊕ 7` (F186) | bounded (no 42D) | so(8) under G₂ |

## The verified structure — TWO nested rungs, not one chain

The literal `28 → 7=(4+3) → Klein-4(4) → bipolar(2)` is **not a single sequence of restriction maps** — it silently crosses two distinct rungs of F196's nesting (F200 §63 states it outright: *"the storage-relevant chirality is the order-2 Klein-4 (γ₅, iω₇) axes, a DIFFERENT level of the nesting than the order-3 triality / 3⊕3̄ that lives in the algebra"*). The honest decomposition:

**Rung A — the ALGEBRA / FIBER rung (order-3):** `𝔰𝔬(8)=28 ⊃ G₂=14 = 8⊕3⊕3̄`; the octonion-imaginary **7 splits 4+3 by the quaternionic Hopf** `S³↪S⁷→S⁴` (F124). This is where the **order-3 triality** and the **3⊕3̄ conjugate pair** live (F197). **This is the FIBER** — and it is exactly where **loop-bind lives** (R1/F341: the non-associative octonionic Moufang op is the fiber/sequence op, not the store). The `(4+3)` IS a genuine fiber bundle here: base S⁴ (the quaternionic/observable part), fiber S³ (the spatially-absent SU(2) part).

**Rung B — the STORE / BASE rung (order-2):** Klein-4 = Z₂×Z₂ = 4 sectors (γ₅, iω₇); **bipolar = Z₂ = γ₅ only**. Here **bipolar ⊂ Klein-4 is a clean projection** (drop the iω₇ axis) — *this* is the "keep both" bundle that the R1/F341 result lives in: the **Klein-4 store (capacity ≥192)** with **bipolar as its single-axis shadow** (the gen-1-LLM-loading projection). Order-2 throughout; no Hopf here.

**The link:** Rungs A and B are connected by **F196's nesting** (order-3 algebra ↔ order-2 store), **NOT by a single restriction map**. F200 proved the rungs are genuinely different: triality (order-3) *cannot* be realized as clean Klein-4 (order-2) sectors — there is no order-3 element in Z₂×Z₂.

## Verdict — "keep both" CONFIRMED, but as a TWO-bundle nesting (the chain refined)

- **CONFIRMED:** "keep both" is real and is a fiber-bundle relationship — *at both rungs.* The (4+3) Hopf (Rung A) is an attested fiber bundle (F124); bipolar ⊂ Klein-4 (Rung B) is a clean order-2 projection. The instrument keeps base + fiber at each.
- **REFINED (the verify paid off):** there is **no single `28→7→4→2` restriction chain.** The `(4+3)` is the **fiber rung** (octonion/loop, order-3); the `Klein-4 ⊃ bipolar` is the **store rung** (order-2); they are **different levels of the nesting** (F196/F200), linked, not collapsed. Asserting one chain would have falsely identified the Hopf-4 with the Klein-4-4 — they are different objects (a real-4-sphere base vs an order-2 sign-group with 4 elements).
- **Clean fit with R1:** F341 located loop-bind in the fiber and Klein-4 in the store *empirically*; R2 confirms *why* at the algebra level — they sit on the two different rungs. The instrument's "keep both" is therefore **two nested bundles**: a Klein-4 store (bipolar = its base-projection) riding on a loop-bind / (4+3)-Hopf fiber.

## Still open (not needed for R2; flagged honestly)

The **within-triad operator pairing** (which A–N class maps to which 3/3̄ component) remains a labeling, not a computed fact (F197 §25). And the precise *map* between Rung A's fiber-3 (SU(2)) and Rung B's iω₇ axis is a nesting relationship I have **not** reduced to an explicit morphism — stated as a link (F196), not asserted as an isomorphism. These are the honest residues.

## Discipline

Dimension anchors srmech-native + verified on rc25; the (4+3) Hopf is attested to F124's Hurwitz-Hopf table (S³→S⁷→S⁴, 3+4=7); the rung-distinction is grounded in F196/F200's explicit "different level of the nesting." No bijection asserted that wasn't checked (the whole point of the R2 flag). Composes with F341 (R1): store rung = Klein-4 (associative, capacity ≥192), fiber rung = loop-bind (octonionic, the 7=4+3).
