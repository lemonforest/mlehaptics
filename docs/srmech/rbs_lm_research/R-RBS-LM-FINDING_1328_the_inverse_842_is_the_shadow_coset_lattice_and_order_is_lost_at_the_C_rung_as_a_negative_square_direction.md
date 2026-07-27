# F1328 — **the inverse 8:4:2 is the SHADOW's coset lattice, not a subalgebra partition — and order IS lost at the ℂ rung, as a negative-square direction (= chirality), confirmed on srmech's own new instrument.** Read naively, `8×1 = 4×2 = 2×4 = 8` is arithmetic on the dimension and **not a finding** — rc349 warns about exactly this trap (*"reading the shipped ladder is reading the dimension"*). What *is* structural: **8:4:2 is the coset lattice of the ℤ₂³ addressing shadow** (subgroups of order 1/2/4 give 8/4/2 cosets). The **subalgebra** reading fails and F1326 says why — there are **7** ℂ-subalgebras inside 𝕆, not 4, because every one contains the *same* real; and the "second ℍ" is a **coset, not a subalgebra**. So 8:4:2 counts **address slots**. Inside one address space the beat is `1(anchor) + 3(triad) + 1(join) + 3(mirror)` — and **the join `e₄` is the doubled copy's own anchor, demoted to an imaginary of 𝕆**, which is F1326's borrowed anchor seen from the other side. Separately: srmech rc349's new `inertia_signature` confirms the user's ℂ-rung reading — **ℝ has no negative direction and no witness; ℂ is the first rung that does, with witness `[0,1] = i`**, and `witness_certifies_nonorderable` first fires there. **But that row is DEFINITIONAL (Hurwitz), not a discovery.**

**User (2026-07-27):** *"new look at inverse order 8:4:2 as addressing full beat of 8ℝ:4ℂ:2ℍ for one octonion address space where a beat should look like 3+1+3 … order apparently does live at C rung as chirality."*

srmech **0.9.0rc349** (clean venv outside the source tree; `HAS_NATIVE=True`, ABI 10). Exhaustive, pure integer.

## 0 — the trivial reading, named so it cannot be mistaken for a result
`8×1 = 4×2 = 2×4 = 8`. This is the dimension restated three ways. rc349's own headline grades this class of row **DEFINITIONAL** and notes `n₋ = dim − 1` exactly on the shipped ladder. Nothing below rests on it.

## 1 — the structural reading `[DEMONSTRABLE]`
```
  subgroups of order 1 :  1  ->  8 cosets   = the R-slot count
  subgroups of order 2 :  7  ->  4 cosets   = the C-slot count
  subgroups of order 4 :  7  ->  2 cosets   = the H-slot count
  subgroups of order 8 :  1  ->  1 coset    = the O itself
```
**8:4:2 is the coset lattice of the ℤ₂³ addressing shadow.** That is a real lattice statement, and it is on the *addressing* side — the side F1319 measured as unbounded and rc349 now ships as `CD_ADDRESS_VERIFIED_DIM = 64`.

## 2 — and the SUBALGEBRA reading fails `[DEMONSTRABLE]`
```
  distinct C-subalgebras inside O            : 7   (not 4)
  their common intersection                  : {+1, -1}   -- the SAME real, in every one
  the base H copy is CLOSED                  : True
  the doubled half is closed                 : False      -- a coset, not a subalgebra
```
The subalgebra count over-counts precisely because **the real anchor is shared** (F1326). So `4ℂ` and `2ℍ` are **address slots**, not algebras — the inverse ladder lives on the shadow, not on the tower.

## 3 — the beat inside one address space `[DEMONSTRABLE]`
```
  e4·e1 -> e5 ,  e4·e2 -> e6 ,  e4·e3 -> e7        (the CD doubling)
  8  =  1 (anchor) | 3 (triad) | 1 (JOIN) | 3 (mirror)      imaginary read = 3+1+3
```
Matches F1326 exactly, and the middle **1 is the join** F1324 says to read at.

## 4 — the join is a demoted anchor `[DEMONSTRABLE — the new part]`
```
  e4 · conj(e4) == +1     -> e4 acts as the doubled copy's identity
  e4 · e4       == -1     -> yet e4 is IMAGINARY in O
```
**Switch perspective to the doubled copy and `e₄` becomes its anchor; from 𝕆's standpoint it is just another imaginary axis.** That is "the 4 comes from the perspective" seen from the other side — the same element is *anchor* or *axis* depending on which triad you read from. This is the sharpest statement yet of why a perspective selector is the missing carrier field (F1326).

## 5 — order at the ℂ rung, on srmech's own new instrument `[ATTESTED — but DEFINITIONAL]`
`srmech.amsc.cascade.inertia_signature` (rc349) reads the Sylvester inertia of the trace form `q(x) = Re(x·x)` **off a multiplication table**:

| rung | dim | trace | norm | negative direction | certifies non-orderable |
|---|---|---|---|---|---|
| ℝ | 1 | `(1,0,0)` | `(1,0,0)` | **none** | False |
| **ℂ** | 2 | `(1,1,0)` | `(2,0,0)` | **`[0,1]` = i** | **True** |
| ℍ | 4 | `(1,3,0)` | `(4,0,0)` | `[0,1,0,0]` | True |
| 𝕆 | 8 | `(1,7,0)` | `(8,0,0)` | `[0,1,0,…]` | True |
| 𝕊 | 16 | `(1,15,0)` | `(16,0,0)` | `[0,1,0,…]` | True |

**ℝ has no negative direction at all; ℂ is the first rung that does, and the witness is `i`.** So "order lives at the ℂ rung as chirality" is **correct**: what is lost at ℝ→ℂ is orderability *in the field sense*, and the thing that loses it is a **negative-square direction** — which is exactly a Class-C chirality.

**Three fences, all from rc349's own text, and they bound this hard:**
- `n₋ = dim − 1` on every shipped-ladder rung, so **reading the ladder is reading the dimension**. The row is **DEFINITIONAL (Hurwitz), not a result.**
- `order_sense` is **`"field"`** and only that. ℂ *is* orderable as a set and as an additive group; what fails is compatibility with the **product** (`i² = −1`). Saying "ℂ is not ordered" unqualified is wrong about an object ordered in two of three senses.
- `n₋ == 0` does **not** mean orderable — **split-ℂ answers `(2,0,0)` with no negative direction yet has zero divisors** (`(1+j)(1−j) = 0`), so it carries no compatible total order. rc349 removed its own `ordered` key over exactly this.

## 6 — srmech independently reproduced two of our numbers `[cross-check]`
```
  rc349 CEILING_MECHANISMS sign_cocycle : "associative ... 344/512 at dim 8"
       512 - 344 = 168     ==     F1322 s4 / F1324 s2 associator defect = 168     MATCH
  rc349 index_xor : exact 4/4, 16/16, 64/64, 256/256, 1024/1024 at dims 2..32
       == F1319 sE: the Z2^n shadow exact, 0 violations at dims 4/8/16/32
```
And F1319's three ceilings are now **shipped constants**: `CD_TURN_MAX_DIM = 4`, `CD_COMPOSE_MAX_DIM = 8`, `CD_ADDRESS_VERIFIED_DIM = 64`. Arrived at independently on both sides.

## Honest scope
- `[DEMONSTRABLE]`: §1–§4, exhaustive over the 16-element octonion unit loop and the full ℤ₂³ subgroup lattice.
- `[ATTESTED, DEFINITIONAL]`: §5 — measured on the shipped op, but graded definitional by rc349 itself. **Do not carry it as a finding.**
- §3 uses one base-triad choice (`{e1,e2,e3}` with join `e4`); F1326 enumerated three of seven. Neither enumerated all seven.
- **`inertia_signature` does NOT pick a seam.** ℍ returns `(1,3,0)` — three negative directions, *indistinguishable from each other*. F1324 needs three **distinct** weights to break S₃; a sign-signature is coarser than that. The metric F1324 asks for is **still not shipped**.
- Nothing built. The perspective selector remains a proposal.

Composes **F1326** (3+1+3, the borrowed anchor — *§4 is its other side*), **F1324** (the join; the metric that picks the seam — *still missing*), **F1322** (`ker(π)` = the real axis; the 168), **F1319** (the three ceilings — *now shipped constants*), **F1325** (the mirror). Generating code: `R-RBS-LM-INVERSE842_*.py` (exit 0, rc349).
