# F1336 — **yes on both: the flat hypercube is ITSELF a shadow, and 8 is the middle ground — it is 𝕆.** The cube's XOR fails at every rung, and it fails for an exact reason with an exact size: **`violations = 2·dim·(dim−1)`**, matched at dims 2/4/8/16 and *derived* — for `i ≠ j`, `eᵢeⱼ = −eⱼeᵢ`, so **antisymmetry forces exactly one of the ordered pair `(i,j),(j,i)` to carry the sign.** So **the flat cube is wrong exactly where the algebra anticommutes**, and that fraction is `(dim−1)/(2·dim) → 1/2`: **the flat reading becomes wrong on asymptotically half of all pairs as you climb.** And the second half — an algebra of dim `n` has `2n` units labelled by `log₂n + 1` bits, so **𝕆 (dim 8) has 16 units labelled by exactly 4 bits: a tesseract.** 𝕆 simultaneously **contains ℍ** (7 copies, the Fano lines) **and is labelled by a 16-vertex 4-cube.** The "4-real-dimensional space" and the "16-vertex tesseract" are **one object read two ways — subalgebra vs unit-label — and 8 is where they meet.**

**User (2026-07-28):** *"what are the chances that even the thing we call hypercube even only gives us shadows? … is it possible that there is an object that does describe 4-real-dimensional space and 16-vertex tesseract by where something related to 8 is the middle ground?"*

## 1 — the ladder `[DEMONSTRABLE]`
```
  algebra dim | units | label bits | FULL-cube XOR | BASIS-only XOR
  C        2  |   4   |     2      |    4 viol     |    EXACT
  H        4  |   8   |     3      |   24 viol     |    EXACT
  O        8  |  16   |     4      |  112 viol     |    EXACT
  S       16  |  32   |     5      |  480 viol     |    EXACT
```
**An algebra of dimension `n` has `2n` units, labelled by `log₂n + 1` bits.** The low `log₂n` bits (the basis) XOR **exactly**; the top bit — the sign — **does not**. So the object is always a cube with **one twisted extra dimension**, and the flat cube is what you get by forgetting the twist.

## 2 — the closed form, derived not fitted `[DEMONSTRABLE]`
```
  violations == 2·dim·(dim−1)      matched at dim 2, 4, 8, 16
```
**Why:** the sign discrepancy depends only on the *basis* pair (the unit signs cancel between the product and the XOR). For `i ≠ j`, `eᵢeⱼ = −eⱼeᵢ`, so **antisymmetry forces exactly one of `(i,j)` and `(j,i)` to carry a sign** — half of the `dim(dim−1)` ordered distinct pairs. Each basis pair covers 4 signed-unit pairs: `4 · dim(dim−1)/2 = 2·dim·(dim−1)`. ∎

**Fraction the flat cube gets wrong** `= (dim−1)/(2·dim)`:
```
  dim  2 -> 1/4      dim  8 -> 7/16      dim 32 -> 31/64
  dim  4 -> 3/8      dim 16 -> 15/32     -> 1/2
```
> **The flat hypercube is wrong exactly where the algebra anticommutes — asymptotically half of all pairs. It is a shadow, and it gets worse the higher you climb.**

That is the direct answer to *"does even the hypercube only give shadows?"* — **yes**, and now with a mechanism (it forgets anticommutativity) and a size (`(dim−1)/(2·dim)`).

## 3 — 8 is the middle ground `[DEMONSTRABLE]`
| the reading | the object | labels |
|---|---|---|
| "ℍ = 4-real-dimensional space" | dim 4 | 8 units → a **3**-cube |
| "the 16-vertex tesseract" | a **4**-cube | 16 labels |
| **what has exactly 16 units?** | **𝕆, dim 8** | 16 units → **4 bits, a tesseract** |

**𝕆 simultaneously contains ℍ** — 7 copies, the Fano lines (F1326) — **and carries a 4-bit tesseract of unit labels.** So the two readings are not competitors and not a size mismatch: they are **the same object seen from two sides**, and **8 is exactly where they meet.** The user's guess was right on the number and right on the role.

## 4 — this RESOLVES the ambiguity parked on gh #1535
That issue asked which "4D hypercube" we meant — ℍ as a 4-real-dimensional space (4 coefficients) or ℤ₂⁴ as a 16-vertex tesseract (16 coefficients) — and warned the reading must be declared, not inferred from the number.

**Answer: neither alone, and both, at 𝕆.** A carrier over 𝕆 is a 4-cube of *unit labels* whose *content* lives in a dim-8 algebra containing ℍ. **But per §2 the flat 4-cube is a shadow of that** — the correct object is the 4-cube **with the sign dimension twisted by the cocycle**, not a free ℤ₂⁴. Any carrier that treats the 4th bit as a free XOR axis is building the shadow on purpose.

## Honest scope
- `[DEMONSTRABLE]`: §1–§3, exhaustive over all signed-unit pairs at dims 2/4/8/16 on rc349.
- The closed form is **derived** (antisymmetry) and **checked** at four rungs — I did not prove it for all `n`, but the derivation does not depend on `n`.
- **§3 is a correspondence of counts plus a containment, not a theorem that 𝕆 is "the" right carrier.** That 𝕆 has 16 units *and* contains ℍ is measured; that this makes it the correct choice for our carrier is **a design argument, not a measurement.**
- Nothing built. **The srmech-side hold stands** — this answers a question, it does not start work.
- The `(dim−1)/(2·dim) → 1/2` reading is about *basis-pair products*, not about how often a real strand would be misread; **no corpus claim is made.**

Composes **F1322** (the non-split extension — *the twist in the top bit is that cocycle*), **F1326/F1328** (𝕆 ⊃ 7 copies of ℍ; the shadow ladder), **F1335** (we use the cube as a label, not a basis — *and now: even the label's flat reading is a shadow*), **F1319** (the addressing lane). Generating code: `R-RBS-LM-CUBESHADOW_*.py` (exit 0, rc349).
