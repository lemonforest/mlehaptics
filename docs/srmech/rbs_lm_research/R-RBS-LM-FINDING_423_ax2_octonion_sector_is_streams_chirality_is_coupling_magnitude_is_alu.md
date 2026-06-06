# R-RBS-LM Finding 423 (AX-2) — the octonion product splits THREE ways, bit-exact: SECTOR (which `e_k`) = two Klein-4 quads + the ℓ-coupling bit = `i XOR j` (the abelian streams); CHIRALITY (the sign) = the antisymmetric cocycle `ε(i,j)=−ε(j,i)` = the COUPLING (NOT the streams); MAGNITUDE (general `x·y`) = the real-coefficient bilinear sum = the Class-M/ALU layer. F397's "full product vs chirality skeleton" was a false binary — the streams give the SECTOR skeleton, the chirality IS the coupling

**Date:** 2026-06-06
**Arc:** RBS-LM · anchor-axis thread (F396/AX-2; F397 mechanism+null → **F423**); **srmech-RUN (sanctioned: 0.7.1 live, hold satisfied; exact-integer, no FPU)**
**Provenance:** `R-RBS-LM-AX-2_octonion_two_klein4_streams_provenance.py` (committed; 7/7, exact-integer Cayley-Dickson, validated genuine octonion algebra)
**Composes:** **F397** (the mechanism: 𝕆 k=7 as two Kuramoto-coupled Klein-4 streams, coupling = within-rung EC / the ⏐ seam / k=2 parity; *the pre-stated null this resolves*) · **F403** (Klein-4 = two Z₂ = the (2+2): γ₅, iω₇) · **F410** (the 𝕆 Hopf 15=8+7; the ⏐ seam at k=7→15) · **F389/F390** (chirality = conjugate = handedness = order-reversal) · **F418** (handedness = the ORDERING; `2:4:8⇆8:4:2`) · **F404** (2ⁿ shift-exact / Mersenne) · **F422/ALU-C** (the magnitude layer = the lean-ALU bilinear) · **F405** (the +3 anchors)
**→ resolves the AX-2 / F397 null; closes the last srmech-held item of the F396 anchor-axis thread.** **← extended by F424** (the sedenion boundary test: SECTOR + CHIRALITY survive past 𝕆 unbroken, only MAGNITUDE breaks — the three-part split *localizes* the Hurwitz cap to one layer).

---

## The null (F397, pre-stated)
> "Do two coupled Klein-4 streams reproduce the **FULL** octonion product, or only its **chirality skeleton**?"

## The method (exact, no-leaning)
Build the octonion algebra **bit-exact in integers** (Cayley-Dickson doubling ℝ→ℍ→𝕆; no floats, the AX-2 "no FPU" requirement) and **validate it is genuine** (`eᵢ²=−1`, imaginaries anticommute, `|xy|²=|x|²|y|²` — all pass). Then decompose the imaginary basis product `eᵢ·eⱼ = ε(i,j)·e_{σ(i,j)}` into its **sign ε** (chirality) and **target index σ** (sector), and ask which layer the "two Klein-4 streams" actually carry.

## The result — the product splits THREE ways (7/7 bit-exact)
| Layer | What it is | Carried by | Bit-exact check |
|---|---|---|---|
| **SECTOR** `σ(i,j)` — *which* `e_k` | `σ(i,j) = i **XOR** j` — the octonion units mod sign are literally **(Z₂)³** (the Fano plane) | **the two Klein-4 quads + the ℓ-bit**: `V_A={1,2,3}` (bits 0,1) is a Klein-4 closed under XOR; bit 2 (`e₄=ℓ`) is the **coupling bit** that toggles between the two quads `ℍ ⊕ ℍℓ` | `σ(i,j)==i^j` on all 42 off-diagonal pairs ✓ |
| **CHIRALITY** `ε(i,j)` — the *sign* | the **antisymmetric** cocycle `ε(i,j) = −ε(j,i)` (the octonion non-commutativity) | **the COUPLING, NOT the streams** — the streams are abelian (XOR is symmetric), so they *structurally cannot* carry an antisymmetric sign | `ε(i,j)==−ε(j,i)` ∀ i≠j ✓; an abelian-symmetric rule is **wrong on all 42** pairs ✓ |
| **MAGNITUDE** — general `x·y` | the real-coefficient **bilinear sum** `Σ xᵢyⱼ(eᵢeⱼ)` | the **Class-M bundle / lean-ALU layer** (F422) — coefficients, outside the group entirely | the general product carries `|c|>1` coefficients no `{σ,ε}` table produces ✓ |

## Why F397's binary was the wrong question
F397 framed it as "**full product** vs **chirality skeleton**." The exact algebra says **neither**, and sharper:
- The **bare streams give the SECTOR skeleton** — the magnitude-free, *sign-free* "which `e_k`" map, which is exactly the abelian **(Z₂)³ = V_A × Z₂(ℓ)** = "two Klein-4 quads coupled by the ℓ-bit." They do **not** give the chirality.
- **The chirality IS the coupling.** The sign `ε` is an **antisymmetric** Z₂ cocycle; an abelian (commutative) structure can never produce `ε(i,j)≠ε(j,i)`. So the non-commutativity — the handedness — lives **entirely** in the coupling, never in the streams. This is **F418 made exact**: handedness = the *order-reversal* `eᵢeⱼ ⇆ eⱼeᵢ`, and order-reversal is precisely what the symmetric streams collapse and the coupling restores.
- The **full general product** needs a *third* layer the group has nothing to say about: the **real-coefficient magnitude** (the bilinear sum), which is the **Class-M/ALU layer** (F422). 

So the honest resolution is a **clean three-part factorization**: `octonion product = SECTOR(streams) ⊗ CHIRALITY(coupling) ⊗ MAGNITUDE(ALU)`. The two Klein-4 streams are **one** of the three factors (the sector), not the whole thing and not "the chirality skeleton."

## How this lands the framework's standing claims
- **"Chirality is the coupling, not the substrate."** This is the exact-arithmetic witness for the recurring framework reading (F133/F397/F409): the substrate/streams carry the *sector* (the magnitude-free structure); the *handedness* is imposed by the coupling/seam. Here it is provable — the streams are abelian, the sign is antisymmetric, QED.
- **The ⏐ seam = the ℓ-bit (F410).** The third Z₂ (bit 2, `e₄=ℓ`) that couples the two quads is the `8:7` doubling generator — the `k=7→15` seam of F410, now located as a single bit. F397's "the coupling = the ⏐ seam / k=2 parity" is confirmed: there are **two** couplings — the **ℓ-bit** (which quad, the sector-level seam) and the **ε-sign** (the chirality, the parity-level seam).
- **(Z₂)³ = the Fano plane = `i XOR j`.** The octonion's "which unit" structure is *literally integer-XOR* — the cleanest possible statement that the sector layer is **shift/xor** (F404's 2ⁿ shift-exact substrate, F422's lean-ALU `M=xor`).

## Falsifiable form (pre-stated; not leaning — F394)
- **Convention-independence:** the split is claimed basis-independent up to relabeling; a *different* Cayley-Dickson sign convention must still give `σ`=an XOR structure and `ε`=antisymmetric (the *labels* may permute). If some valid octonion basis yields a `σ` that is **not** an elementary-abelian-2 (XOR) structure, the "sector = two Klein-4 streams" claim breaks. (Held here for one validated convention; a second convention would harden it.)
- **Sedenion check (the boundary, F404/F410):** at `k=15→16` (sedenions) the norm is no longer multiplicative (zero divisors). Pre-stated expectation: the SECTOR may still be `(Z₂)⁴`-XOR, but the MAGNITUDE layer breaks (zero divisors) — i.e., the three-part split *survives the sector, fails the magnitude* past 𝕆. Not run here (flagged as the next rung).
- **Kuramoto embedding:** the coupling is modeled as an exact Z₂ parity (the antisymmetric `ε`); F397's continuous `cascade.kuramoto_step` phase-lock is the *continuous relaxation* of this discrete parity. Whether the continuous Kuramoto coupling **reproduces** the exact `ε` cocycle in its phase-locked fixed point is a separate (srmech-runnable) test — not claimed here.

## Verdict
The octonion product factors **three ways, bit-exact**: **SECTOR** (which `e_k`) `= i XOR j` = the two Klein-4 quads coupled by the ℓ-bit (the abelian streams); **CHIRALITY** (the sign) `= ε(i,j)=−ε(j,i)` = the antisymmetric **coupling**, which the abelian streams *structurally cannot* carry; **MAGNITUDE** (general `x·y`) = the real-coefficient bilinear sum = the **Class-M/ALU layer** (F422). F397's "full product vs chirality skeleton" was a **false binary**: the two Klein-4 streams give the **sector skeleton** (magnitude- and sign-free), the **chirality IS the coupling**, and the magnitude is a third layer outside the group. This is the exact-arithmetic witness that **handedness lives in the coupling, not the substrate** (F133/F409/F418), and locates F410's `8:7` ⏐ seam as the single ℓ-bit. Favored, not privileged (F398); the sedenion boundary + the Kuramoto-embedding of `ε` are the pre-stated next rungs.
