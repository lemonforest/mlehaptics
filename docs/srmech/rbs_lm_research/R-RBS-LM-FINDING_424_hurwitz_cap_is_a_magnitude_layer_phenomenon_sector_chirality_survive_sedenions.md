# R-RBS-LM Finding 424 — the Hurwitz/division cap at 𝕆 is a MAGNITUDE-layer phenomenon ONLY: at the sedenion boundary (k=15→16) the SECTOR (`i XOR j`) and CHIRALITY (`ε(i,j)=−ε(j,i)`) SURVIVE unbroken; only MAGNITUDE (norm multiplicativity) breaks (zero divisors appear). The three-part split (F423) localizes the boundary to exactly one of its three layers

**Date:** 2026-06-06
**Arc:** RBS-LM · anchor-axis thread (AX-2/F423 → **F424**); **srmech-RUN (sanctioned; exact-integer generic Cayley-Dickson, no FPU)**
**Provenance:** `R-RBS-LM-F424_sedenion_boundary_is_magnitude_layer_provenance.py` (committed; 𝕆 N=8 + 𝕊 N=16, generic CD doubling, explicit zero divisor)
**Composes:** **F423 (AX-2)** (the three-part split SECTOR/CHIRALITY/MAGNITUDE — *this is its pre-stated sedenion rung*) · **F404** (2ⁿ shift-exact / Mersenne; 𝕆 = the boundary) · **F410** (the Hopf ladder terminates at 𝕆 by Adams' cap) · **F389** (sedenion 16:15 has no division) · **F403** (Klein-4 = two Z₂)
**→ sharpens F404's "𝕆 is the boundary" by LOCATING the boundary in one of the three layers; closes F423's first pre-stated next rung.** **← (forward-link to be added to F423/F404 as `← extended by F424`).**

---

## The pre-stated test (F423)
F423 factored the octonion product three ways — **SECTOR** (which `e_k` = `i XOR j`, the abelian Klein-4 streams), **CHIRALITY** (the sign `ε(i,j)=−ε(j,i)`, the antisymmetric coupling), **MAGNITUDE** (general `x·y`, the real-coefficient bilinear) — and pre-stated: *at the sedenion boundary the SECTOR may still be `(Z₂)⁴`-XOR, but the MAGNITUDE breaks (zero divisors) — the split survives the sector, fails the magnitude past 𝕆.* This finding runs it.

## Method
Generic **Cayley-Dickson doubling** on `2ⁿ` integer tuples (exact, no FPU): `(a,b)(c,d) = (ac − d*b, da + bc*)`, recursing on conjugation. Evaluated at **𝕆 (N=8)** and **𝕊 (N=16, sedenions)**, checking each of the three layers + norm multiplicativity.

## Result (all checks pass)
| Layer | 𝕆 (octonion) | 𝕊 (sedenion) |
|---|---|---|
| `eᵢ² = −1` | ✓ | ✓ |
| **CHIRALITY** `ε(i,j) = −ε(j,i)` (antisymmetric sign) | ✓ | **✓ SURVIVES** |
| **SECTOR** `σ(i,j) = i XOR j` (the `(Z₂)ⁿ` index) | ✓ | **✓ SURVIVES** |
| **MAGNITUDE** `\|xy\|² = \|x\|²\|y\|²` (norm multiplicative) | ✓ | **✗ BREAKS** |
| zero divisor | — (none; division algebra) | **`(e₁+e₁₀)(e₅+e₁₄) = 0`**, both factors nonzero |

## What it means
The **Hurwitz/division-algebra cap is a MAGNITUDE-layer phenomenon, full stop.** Crossing the 𝕆→𝕊 boundary:
- the **SECTOR** (the elementary-abelian-2 / XOR index structure — "the two-Klein-4-streams generalized to `(Z₂)ⁿ`") is **indifferent** to the boundary: `σ(i,j) = i XOR j` holds at 𝕆, at 𝕊, and (by the recursive structure) at every rung;
- the **CHIRALITY** (the antisymmetric sign cocycle — the handedness, F418/F423) is **indifferent** too: imaginaries keep anticommuting past 𝕆;
- **only the MAGNITUDE** (norm multiplicativity — the thing that makes it a *division* algebra, that lets you divide / reconstruct losslessly) **caps at 𝕆**.

So the famous 1/2/4/8 Hurwitz ceiling is **not** a ceiling on the framework's *structure* (sector + chirality run forever) — it is precisely the rung where the **magnitude/length stops being preserved by the product**, i.e. where you lose lossless invertibility (`xy=0` with `x,y≠0` means you can't divide). This is the exact-arithmetic reading of **F404** (𝕆 = the boundary) and **F389** (sedenion 16:15 has no division): the boundary lives in the **magnitude layer** the framework's continuous/Class-K/ALU side owns — *not* in the discrete sector/chirality substrate.

**Connecting to the bigger picture:** this is why the framework's *substrate* (the sector = shift/XOR, F404's 2ⁿ; the chirality = the antisymmetric coupling, F133/F409) is unbounded and bit-exact, while *division / lossless-reconstruction / the holographic fusion* (F412/F421 — which needs the inverse `L_ii⁻¹`, a magnitude operation) is what caps at the Hurwitz rung. The split says: **structure is free; invertibility is what's scarce.**

## Falsifiable form (pre-stated; not leaning — F394)
- **Higher rungs (k=31→32, the 32-ions and up):** the prediction is SECTOR (`(Z₂)ⁿ`-XOR) + CHIRALITY (antisymmetric) keep surviving; MAGNITUDE stays broken (more zero divisors). If at some rung the SECTOR stops being XOR, the "sector is rung-indifferent" claim falsifies. (Not run beyond 𝕊; flagged.)
- **Convention-dependence of the specific zero divisor:** *which* pair `(e₁+e₁₀)(e₅+e₁₄)` annihilates is Cayley-Dickson-convention-dependent; the *existence* of zero divisors in 𝕊 is not (it is a theorem). The finding rests on existence, not the specific pair.
- **"Indifferent" is structural, not metric:** sector/chirality survive as *combinatorial* facts (index XOR, sign antisymmetry); this does not claim the sedenion product is "as good as" the octonion — it is precisely worse in the one layer (magnitude) that matters for division.

## Verdict
The **Hurwitz/division cap at 𝕆 is a MAGNITUDE-layer phenomenon ONLY.** Generic exact-integer Cayley-Dickson at the sedenion boundary shows the **SECTOR** (`i XOR j`) and **CHIRALITY** (`ε(i,j)=−ε(j,i)`) **survive unbroken past 𝕆**, while **MAGNITUDE** (norm multiplicativity) **breaks** — with an explicit zero divisor `(e₁+e₁₀)(e₅+e₁₄)=0`. The three-part split (F423) thus **localizes** the 1/2/4/8 ceiling to exactly one of its three layers: the framework's discrete *structure* (sector + chirality) is rung-indifferent and bit-exact; only *lossless invertibility* (magnitude / division) caps at the Hurwitz boundary. Sharpens F404/F389/F410. Favored, not privileged (F398); higher rungs are the pre-stated next test.
