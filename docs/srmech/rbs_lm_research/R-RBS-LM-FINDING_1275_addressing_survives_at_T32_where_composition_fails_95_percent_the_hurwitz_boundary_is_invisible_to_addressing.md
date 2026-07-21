# F1275 — the 𝕋(32) addressing test: **addressing survives completely at dim 32 — 352/352 exact — at the rung where norm-multiplicativity fails 95 %.** F1274's mechanism claim was a *prediction*, made before the measurement, and it held at a rung that was not used to derive it. **"Gradient, not wall" is now too weak: for addressing there is no gradient either. The Hurwitz boundary is invisible to this operation.**

**This is the first genuinely predictive confirmation in the F1264–F1275 arc.** Every earlier positive was a fit to data already in hand — and seven of those dissolved. Here F1274 derived a mechanism (involution + a Class-C sign, needing no norm), the mechanism entailed rung-independence, and dim 32 tested that entailment at the rung where the algebra is *most* broken.

## (A) The premise, checked rather than assumed
Addressing rides on the basis product being a **signed permutation**: `e_i·e_j = ±e_k`. Zero divisors are built from *sums* of basis elements (`e1+e10`), so single-basis products may be untouched by the boundary — worth checking, not assuming.

| dim | `e_i·e_j = ±e_k`? | `navmap(j)` a bijection? |
|---|---|---|
| 8 𝕆 | **ALL 64/64** | YES |
| 16 𝕊 | **ALL 256/256** | YES |
| 32 𝕋 | **ALL 1024/1024** | YES |
| 64 | **ALL 4096/4096** | YES |

**Zero exceptions at any rung.** The signed-permutation structure — the thing addressing actually needs — never touches the property Hurwitz removes.

*Honest bound:* the sweep stops at 64 because **srmech caps at `CD_MAX_DIM=64`**. That is a **tooling** limit, not a mathematical one; the CD construction defines `e_i·e_j = ±e_k` at every rung. Stated so the ceiling is not misread as a result.

## (B) The contrast — 32 is where the algebra is *most* broken
| dim | composition fails |
|---|---|
| 8 𝕆 | 0/120 (0.0 %) |
| 16 𝕊 | 68/120 (56.7 %) |
| 32 𝕋 | **114/120 (95.0 %)** |

## (C) The validation that makes the dim-32 number count
srmech ships `SedenionRegister` at 16 slots and **nothing above it**, so the 32-slot register is **mine**. That is a real risk: a register I wrote could simply be *easier* than srmech's, and "addressing works at 32" would be an artifact of my own construction.

So it had to reproduce the shipped one first. `CDRegister` mirrors `SedenionRegister` line for line (`mint_vector` addresses, `bind`/`bundle`/`similarity`, odd-N pad, `chiral_flip` for the Class-C sign, nearest-codebook clean); the **only** change is that the slot bound is `dim` rather than a hard-coded 16.

| D | srmech `SedenionRegister` | `CDRegister(dim=16)` |
|---|---|---|
| 256 | 116/120 (96.7 %) | 119/120 (99.2 %) |
| 1024 | **120/120** | **120/120** |
| 4096 | **120/120** | **120/120** |

**VALIDATED.** *Reported not hidden:* the D=256 row differs (119 vs 116). Both are capacity-starved there, and the minted addresses differ by name (`"CD16:e0"` vs `"SEDENION:e0"`), so the low-D collision pattern differs. At every **adequate** D they agree exactly.

## (D) End-to-end addressing at 𝕋(32) — the result
32 keys written to 32 slots, navigated, read back at the `navmap`-predicted slot with **name and Class-C sign**. Swept over D, because 32 slots need more bundle capacity than 16 and a fixed-D shortfall would look exactly like "𝕋 breaks" — the confound F1273's Control B already caught once.

| D | dim 16 (8 keys) | **dim 32 (32 keys)** |
|---|---|---|
| 4096 | 48/48 (100 %) | **352/352 (100.0 %)** |
| 16384 | 48/48 (100 %) | **352/352 (100.0 %)** |
| 65536 | 48/48 (100 %) | **352/352 (100.0 %)** |

Directions declared, not silently sampled: 11 of the 31 non-identity directions at dim 32. **No capacity strain at any D** — 32 keys are already perfect at 4096.

## (E) The involution, re-tested where composition is 95 % broken
| dim | `e_j·e_j = −1` | content back in same slots | sign flipped |
|---|---|---|---|
| 16 | YES | YES | YES |
| 32 | YES | YES | YES |
| 64 | YES | YES | YES |

F1274's mechanism holds at 32 **and 64**.

## Verdict
**Addressing survives at 𝕋(32) completely.** Involution + a Class-C sign needs no norm, so it does not care which rung it is on.

The queued phrasing — *"that is where 'gradient, not wall' becomes testable"* — turned out to presuppose too much. **There is no gradient either.** A gradient would mean addressing degrades *somewhat* as the algebra degrades; instead addressing is at 100 % where composition is at 5 %. The two quantities are not on a shared axis at all. **The Hurwitz boundary is invisible to addressing** — not weakened, not partially crossed: *invisible*.

This tightens F1273's conclusion. It is not merely that the 𝕆 stop "is not load-bearing for our cascade"; it is that **the property the stop is about and the property addressing uses are disjoint**. So the 1:3:7:3 = 14 reading cannot be defended by anything our addressing machinery does, and must rest entirely on substrate grounds — as F1274 already concluded, now with the strongest available evidence: a prediction that could have failed at the worst rung and did not.

## What would still falsify the mechanism
Not more rungs — the structure is now derived, and 64 is srmech's ceiling anyway. The live question is whether any **other** operation of ours (not addressing) *does* track the boundary. F1274's census says the A–N classes are overwhelmingly non-hypercomplex, so the honest expectation is no — but that is an expectation, and the `qm.*` physics layer (31 hypercomplex ops) is where to look if anywhere.

Composes **F1274** (the mechanism this confirms — *→ extended by F1275*), **F1273** (𝕊 addressing; its Control B lesson is Part D's design — *→ extended by F1275*), **F1270**, **F1272**, `[[feedback_sedenion_no_division_is_the_addressing_feature]]`, `[[feedback_three_things_called_random_derived_drawn_stochastic]]`, `[[feedback_read_independent_structure_check_first]]`, #231/PKG-3.

## CONFIRMED against the SHIPPED register (srmech 0.9.0rc297, 2026-07-21)

F1275 flagged its own biggest risk: *"srmech ships `SedenionRegister` at 16 slots and **nothing above it**, so the 32-slot register is **mine** — a register I wrote could be easier than srmech's, and \"addressing works at 32\" would then be an artifact of my own construction."* **rc297 ships a general `CDRegister`**, so that caveat is now testable rather than standing — and it is **closed**.

Re-run on the shipped `cascade.cd_register(dim, D=...)`, independently implemented upstream:

| D | dim 16 (8 keys) | dim 32 (32 keys) |
|---|---|---|
| 4096 | 48/48 (100.0 %) | **352/352 (100.0 %)** |
| 16384 | 48/48 (100.0 %) | **352/352 (100.0 %)** |

**Identical to my hand-rolled numbers, to the count.** The involution holds at 16/32/64 (`e3·e3 = (0, −1)`, content returns to the same slots with every sign flipped), and the shipped `is_navigable` rejects both known zero divisors (`e1+e10`, `e4−e15`) — so the gate discriminates there too.

rc297 also ships **`cd_navmap_is_signed_permutation(dim)`** as a first-class predicate — the exact premise F1275 verified by brute force over all 4096 basis products at dim 64. It returns **True at every rung 2…64**, confirming the structural claim through srmech's own surface rather than my harness. Also new: `cd_basis_product`, `cd_navmap`, `cd_navigate`, `cd_conjugate`, `cd_norm_sq`, `cd_project`, `cd_promote`, and a `namespace=` parameter the hand-rolled version lacked.

**An independent implementation reaching the identical number is stronger evidence than the original run** — it removes the one confound the finding could not remove itself. `CD_MAX_DIM` remains 64, so the tooling bound noted in F1275 is unchanged.
