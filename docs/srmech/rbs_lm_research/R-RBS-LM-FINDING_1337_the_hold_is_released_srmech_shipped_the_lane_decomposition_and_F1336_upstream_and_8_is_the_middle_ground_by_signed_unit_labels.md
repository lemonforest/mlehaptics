# F1337 — **the HOLD is released: srmech rc432 shipped the thing we were waiting for.** The user parked the 4D-irrep carrier direction pending *"the next srmech batch of rcN that help tighten this loop"* (2026-08-07). rc354–rc432 is that batch, and it closes the loop from the other side: srmech now ships **`describe()["lanes"]`** — a per-op, adversarially-verified declaration of whether an op reads the **index lane** (the XOR address; *"Abelian, order-blind, unbounded"*), the **sign lane** (the cocycle; *"Order-carrying; **every published ceiling lives here**"*), or **both**. That is F1336's sign/index split promoted from our finding to a queryable property of 9 shipped ops. And **F1336 is cited by name in the shipped payload** (`granularity.collision_note`, "A FOURTH sense (rc354, F1336)"), re-derived and checked at **six rungs (2/4/8/16/32/64)** where we measured fewer. The #1535 question — *"is there an object that describes both 4-real-dimensional space and the 16-vertex tesseract, with something related to 8 as the middle ground?"* — now has srmech's own answer: **yes, 𝕆**, because an algebra of real dim `n` has `2n` **signed** units needing `log₂(n)+1` bits, so **𝕆 (dim 8) has 16 signed units = a 4-cube**, and 𝕆 contains ℍ seven times. Marked upstream as a **DESIGN argument, not a measurement** — and we must carry that bound.

srmech 0.9.0rc432 (native True, **ABI 14**, 655 registered ops). Everything below is read off the shipped `describe()` payload, not re-derived here.

## 1 — the lane decomposition, as shipped `[DEMONSTRABLE — upstream]`

```
  index : reads the XOR address only. Moves under an index relabel, UNCHANGED by a sign flip.
          "Abelian, order-blind, unbounded"
  sign  : reads the cocycle only. Moves under a sign flip, UNCHANGED by an index relabel.
          "Order-carrying; every published ceiling lives here"
  both  : reads address AND cocycle — the mixer case
```
Population: `both` 6, `index` 2, `sign` 1, over two INPUT kinds (`algebra` 8, `geometry` 2).

**The verification rule is the one we would have asked for**: *"a declared lane must MOVE under its own perturbation and NOT move under the other; **swept, never sampled**"* — gated by `tests/test_op_lane_rc347.py`. The algebra-side perturbations are exactly our two: XOR the Q₈ centre bit (`q ^ 4`) for sign; relabel the V₄ coset by an element of `Aut(V₄) = S₃` for index.

## 2 — the one sentence that settles the ceiling arc `[DEMONSTRABLE — upstream claim]`

> **sign lane: *"Order-carrying; every published ceiling lives here."***
> **index lane: *"Abelian, order-blind, **unbounded**."***

Every ceiling we have chased — `CD_TURN_MAX_DIM=4`, `CD_COMPOSE_MAX_DIM=8`, the 168-triple associator support, the 61%-of-length-4-words bracketing disagreement — is now located, upstream and by construction, in **one lane**. And the other lane is stated to have **no ceiling at all**. That is a much sharper statement than "the shadow loses the fiber": it says *which half of the carrier the boundedness is a property of*, and that the abelian half we can compute cheaply is exactly the half that never runs out.

It also re-reads F1335 (our carrier is D parallel scalar chains): D parallel chains is an **index-lane-only** object. The thing we measured ourselves to be missing is precisely the lane the ceilings live in.

## 3 — the worked example is our own shape, in a wet system `[DEMONSTRABLE — upstream]`

`cwf_consistency_mod2`, 3000 trials, three reads:

| read | lane | input | responds to sign-flip | responds to index-relabel |
|---|---|---|---|---|
| `Tw` (twist) | sign | algebra | **3000/3000** | 0 |
| `Wr` (writhe) | sign | geometry | 0 (algebra) / **3000** (geometry) | 0 |
| `Lk` (linking) | **both** | algebra | 735 | **182** |

> *"Lk is the ONLY one of the three that responds to an index relabel — the only mixer. Tw and Wr share the SIGN lane over different INPUTS."*

`Lk = Tw + Wr` is the one op that mixes. This is the k=2-detect / k=3-correct boundary (F1325/F291) showing up as a lane fact: the two sign-lane reads are each blind to the address, and only their **ordered non-abelian Q₈ bind** sees both.

## 4 — why 8 is the middle ground `[DEMONSTRABLE derivation; DESIGN argument for the conclusion]`

The user's #1535 question, answered by a distinction we did not have:

- a **grading cube** `(ℤ/2)^log₂(n)` has `n` vertices — one per basis **DIRECTION**;
- a **unit-label cube** has `2n` vertices — one per **SIGNED** unit, because *an algebra of real dim `n` does not have `n` units, it has `2n`* (`±e₀ … ±e_{n-1}`), needing `log₂(n)` index bits **+ one sign bit**.

So there are **two different 16s**, and conflating them is the whole ambiguity:

| object | algebra | real dim | 16 vertices count… |
|---|---|---|---|
| 𝕊 grading cube | 𝕊 | 16 | basis **directions** |
| **𝕆 unit-label cube** | **𝕆** | **8** | signed **units** |

> **"That is why 8 is the middle ground: 𝕆 addresses 16 units in 4 bits AND contains ℍ seven times (the seven Fano lines, each `{0,a,b,c}` verified closed under the product)."**

ℍ (dim 4) → 8 signed units → a **3-cube**. 𝕆 (dim 8) → 16 signed units → a **4-cube / tesseract**. So the tesseract our carrier wants is **𝕆's unit-label cube**, not 𝕊's grading cube — same 16 vertices, different object. And the third object, *"the tesseract that lives IN ℍ"* — the 16 half-integer Hurwitz unit POINTS of ℝ⁴ — is explicitly **not a grading**: **128 of their 256 products leave the set** (measured 2026-07-28), so no sign-bit XOR grades them.

## 5 — and the flat cube is still wrong, now to six rungs `[DEMONSTRABLE — upstream, extends F1336]`

Under a flat `(log₂(n)+1)`-bit XOR label on `cd_basis_product`: the **low index bits XOR EXACTLY — 0 violations at every rung.** The **top (sign) bit does not.**

```
  violations = 2·dim·(dim−1)
  dim :      2     4     8     16     32     64
  viol:      4    24   112    480   1984   8064
  frac: (dim−1)/(2·dim) = 1/4, 3/8, 7/16, 15/32, 31/64, 63/128  ->  1/2
```
> **"THE FLAT HYPERCUBE IS WRONG EXACTLY WHERE THE ALGEBRA ANTICOMMUTES, and it worsens up the ladder."**

This is F1336 verbatim, independently re-derived, and **extended from our rung set to six rungs**. The index half of the hypercube is exact; only the sign bit fails. Which is the same statement as §2 from the other direction — **the cube is a faithful address and an unfaithful cocycle.**

## 6 — the 8:4:2 widths are shipped, and they carry the H/He bit `[DEMONSTRABLE — upstream]`

F1328 read `8ℝ : 4ℂ : 2ℍ` as a shadow coset lattice. srmech ships exactly that as `granularity.widths`, with the invariant stated:

> **"1 anchor + (n−1) torsors at every width: the identity sits in exactly ONE slot and only that slot closes under the product"**

| over | slots | real dims/slot | index bits | anchor | torsors | closes |
|---|---|---|---|---|---|---|
| ℝ | 8 | 1 | 3 | 1 | 7 | only `R_0` |
| ℂ | 4 | 2 | 2 | 1 | 3 | only `C_LL` |
| ℍ | 2 | 4 | 1 | 1 | 1 | only `H_L` |

`index_bit_map` = `{bit2: "H vs He", bit1: "C vs Cj", bit0: "1 vs i"}` — the **H(+)He full-beat** naming the user reached for is in the shipped bit map. Note the reading label `one_algebra_three_widths`: this is **ONE algebra (𝕆) re-addressed at three widths**, explicitly *not* `BLOCK_DIMS = (2,4,8)`, which are the real dims of **three** algebras (ℂ, ℍ, 𝕆). Same three numbers, different objects — the payload carries its own collision warning, and `11D = 1+3+7` has no such collision.

## 7 — the second new surface: `frames` `[DEMONSTRABLE — upstream]`

21 ops declare a **frame** (`modulus` axis; `parametric` 15 / `fixed` 6), verified by sweeping rather than sampling. What matters for us is that it ships an explicit **`cannot_express`** blind-spot list — including *"an op with no frame datum declares NOTHING, so a carrier-level op and an op with no frame concept at all are indistinguishable here. **Absent is not a verdict**"* — and a third blind spot, `base_argument_dependence`, added at rc428 after a probe's verdict was found to track its ARGUMENTS rather than the op. A surface that publishes what it cannot see is doing the thing we ask of our own findings.

## Honest scope

- **Almost nothing here is our measurement.** §1–§7 are read off srmech's shipped `describe()` payload and its cited generating code (`notes/op_lane_axis_rc347.py`, `notes/unit_label_cube_rc354.py`). Our contribution is F1336, which upstream credits and extended. I have NOT independently re-run the six-rung sweep.
- **Carry upstream's own bounds, which are explicit and which I will not soften:** the closed form `2·dim·(dim−1)` is **DERIVED and CHECKED at six rungs, NOT proved for all n**; *"𝕆 is THE right carrier"* is a **DESIGN argument, not a measurement**; and `(dim−1)/(2·dim)` is about **basis-pair products under a flat label** — it is **NOT a strand-misread rate and must not enter an error budget.** That last clause is aimed at exactly the mistake we would otherwise make.
- **The lane surface covers 9 ops of 655.** `by_lane` totals 9. It is a real, verified, load-bearing 9 — not a census. Do not read "the lane decomposition ships" as "every op declares a lane."
- **§2's ceiling claim is upstream's sentence, not a theorem I checked.** *"Every published ceiling lives here"* is a strong claim; it is srmech's, stated in the definitions block, and I am relaying it as such.
- The `Lk`/`Tw`/`Wr` reading in §3 is upstream's worked example; the k=2/k=3 connection in the last line is **mine and [SPECULATIVE]**.

## What this releases, and what it does not

**Releases:** the HOLD. The user parked on *"not do we adopt hypercube, but how to adopt the correct 4D irrep."* The answer that arrived is that the correct object is **𝕆's unit-label cube** (16 signed units, 4 bits), the flat version of it is exact on the index bits and fails on the sign bit at a known rate, and the sign bit is where every ceiling lives. That is enough to design against.

**Does not release:** nothing is built. We have not adopted the carrier, not re-encoded anything, and not measured a single strand under the new reading. The open question from #1535 — **what actually READS the 2-dimensional irrep** — is still open; the lane surface *names* the sign lane but does not hand us a read-out that recovers it.

Composes **F1336** (the cube is itself a shadow — *now shipped upstream, extended to six rungs*), **F1335** (D parallel scalar chains — *now identifiable as index-lane-only*), **F1328** (8:4:2 — *now the shipped `widths` table*), **F1326** (3+1+3 and the borrowed anchor — *the "1 anchor + (n−1) torsors" invariant*), **F1322** (`ker(π) = {±1}` — *the sign lane IS that kernel, promoted to a lane*), **F1325/F291** (k=2 detects, k=3 corrects — *§3's mixer reading*), **gh #1535** (the parked hypercube ask — *§4 answers it*), **gh #1530** (the living gaps tracker).
