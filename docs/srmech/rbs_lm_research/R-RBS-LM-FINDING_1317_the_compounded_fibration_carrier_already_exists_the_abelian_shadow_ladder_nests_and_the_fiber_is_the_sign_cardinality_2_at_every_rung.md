# F1317 — the **compounded fibration carrier already exists in the shipped encoding**: each rung projects to its elementary-abelian shadow **ℤ₂ⁿ by XOR** (ℍ→ℤ₂² and 𝕆→ℤ₂³, **0 violations each**), and **the shadows NEST by truncation** (`(𝕆-shadow)&3 == (ℍ-shadow)`, 0 violations) — so **ONE symbol read at mask-width n IS the rung-n abelian address**, the tower **internal** rather than side-by-side. And the falsifiable next step MFO §VIII.31.18 named is now **closed**: the non-abelian range over an abelian shadow is **DISCRETE, cardinality exactly 2 at every rung** — the fiber is **the SIGN**. Shadow = *which axis* (abelian, nests); fiber = *which way* (the sign the shadow discards). The user's **(4+3) internal middle** is confirmed: `Im(𝕆)=7 = 4 (doubling copy e₄..e₇) + 3 (old ℍ imaginaries e₁,e₂,e₃)` — the split **is** the Cayley–Dickson step, so "ℍ is the middle rung" and "(4+3) is the middle split" are one structure seen side-by-side vs internally.

**User (2026-07-25):** *"can we do compounded fibration carrier? … our carrier needs to treat the tower internal, not side-by-side … any fibration is asymptotic, chosen by the excitation or projection … what if it actually means (4+3) is middle ground, i.e. the addressing is fractal too."*

All measured on srmech 0.9.0rc336 (native), shipped ops only.

## 1 — The shadow ladder nests `[DEMONSTRABLE]`
```
  H rung -> Z2^2 (V4):  q8_mult(a,b)&3  == (a&3)^(b&3)      0/64  violations
  O rung -> Z2^3     :  oct_mult(a,b)&7 == (a&7)^(b&7)      0/256 violations   <- NEW
  nesting            :  ((a&7)^(b&7))&3 == (a&3)^(b&3)      0/256 violations
```
The 𝕆→ℤ₂³ homomorphism is the new measurement; the ℍ→V₄ one was known (F1307). The third line is the load-bearing one: **the shadows themselves nest by truncation**, so the ladder is ℤ₂ ⊂ ℤ₂² ⊂ ℤ₂³ and a single symbol carries all of them at once.

```
   ONE 4-BIT SYMBOL, READ AT ANY RUNG (the compounded carrier)

     bit   3       2   1   0
         [sign |  basis index  ]
            |         |
            |         +-- & 1  ->  Z2      (C  shadow)
            |         +-- & 3  ->  Z2^2=V4 (H  shadow)   <- klein4 genome reads HERE
            |         +-- & 7  ->  Z2^3    (O  shadow)
            +------------ the FIBER: which-way, cardinality 2, discarded by every shadow

   the fibration is not built -- it is CHOSEN BY THE MASK WIDTH at read time.
```
**This is the user's "any fibration is asymptotic, chosen by the excitation or projection," made literal:** the read width *is* the choice of rung. Nothing needs to be re-encoded to change rung-perspective; you mask differently.

## 2 — Per-rung fiber cardinality: the §VIII.31.18 open question, CLOSED `[DEMONSTRABLE]`
MFO §VIII.31.18 posed the constructor (`the_one` as abelian-shadow → non-abelian-range solver) with an explicit honest bound: *"whether the range is a clean finite 'only Y' or a continuous family **depends on the rung** — characterising that (per-rung fiber cardinality) is the falsifiable next step."*

**Measured:**
| rung | shadow classes | fiber sizes | fiber members differ in |
|---|---|---|---|
| ℍ (Q₈ → V₄ = ℤ₂²) | 4 | **[2]** | **only the sign bit** |
| 𝕆 (O₁₆ → ℤ₂³) | 8 | **[2]** | **only the sign bit** |

**The range is DISCRETE and the cardinality is exactly 2 at every rung — never a continuous family.** Over a D-slot leaf the fiber is 2^D: still finite, still exactly characterised. So the constructor is a *well-posed finite lift*, not an under-determined search:

> **shadow = WHICH AXIS (abelian, nests, free). fiber = WHICH WAY (the sign, 1 bit, must be supplied).**

That is why `the_one` is the right supplier and why F1307's `_coupler_q8` had exactly the right shape without knowing this: it built the V₄ coset from `klein4_from_one` (the shadow) **and** the sign from an independent Class-A channel (the fiber). The construction was correct *because* the fiber is one resonantly-suppliable bit per slot.

## 3 — The (4+3) internal middle `[DEMONSTRABLE + the reading]`
```
  H-block {0,1,2,3} closed under oct_mult (mod sign)   : True
  H * e4 lands in the doubling copy {4,5,6,7}          : True
  => Im(O) = 7 = 4 (doubling copy e4..e7) + 3 (old H imaginaries e1,e2,e3)
```
The user's `2:4:8 = 1+1 : 1+3 : 1+7 = 1+(1+0) : 1+(2+1) : 1+(4+3)` is exactly the CD recurrence written out: **new-imaginaries = previous-dim + previous-imaginaries** (`1=1+0`, `3=2+1`, `7=4+3`). And all four of the user's k=7 forms — `(4+3)`, `{(1+(2+1))+(2+1)}`, `{(4+(2+1))}`, `{(1+3)+(3)}` — evaluate to 7 by different nesting paths. **That is the fractal-addressing claim, and it is arithmetically exact:** the same 7 is addressable through several nesting routes, and which route you use is a perspective choice, not a different object.

**On "is 4 the middle, or (4+3)?" — both, and they are one structure.** MFO §VIII.31.19 §4 establishes **ℍ is the binding pivot** (middle of 2:4:8; the unique rung that is *first non-abelian* AND *last associative*). The user's (4+3) is that same fact read **internally**: 𝕆 = ℍ ⊕ ℍe₄, so the (4+3) split *inside* 𝕆 is literally where ℍ sits. **Side-by-side view → "ℍ is the middle rung"; internal view → "(4+3) is the middle split."** The internal view is the one that makes the compounded carrier work — which is precisely the user's "treat the tower internal, not side-by-side."

## 4 — What this does NOT give (the honest bound that matters most)
**The compounded carrier is an ADDRESSING result, not a TURN result.** MFO §VIII.31.19 §3 already fenced this as standard math: turns need a *group*, the only sphere Lie-groups are `S¹` and `S³`, `S⁷` is a non-associative Moufang loop, so **turn-composability tops out at ℍ while addressing goes higher** — *"two different ceilings."*

**F1316 measured exactly that ceiling independently, and did not know it was predicted.** The 𝕆 associator adds **zero** order information (bit-for-bit identical collisions to the plain holonomy) — i.e. the octo-turn's ordered product is bracketing-ambiguous and the associator is a *defect*, not a finer turn. So:
- **empirical (F1316, measured):** the associator is not an order read;
- **structural (§VIII.31.19 §3, standard math):** turns top out at ℍ because `S⁷` is not a group.

**Same wall, reached from two directions, independently.** That convergence is worth more than either alone, and it bounds the compounded carrier precisely: *address* at any rung; *turn* only at ℍ or below.

## 5 — What a compounded-carrier genome would therefore be `[SPECULATIVE — the design that follows]`
Not three side-by-side `element_type`s (the current shipped shape: klein4 / Q₈ / 𝕆 as separate carriers with separate markers), but **one widest-rung symbol whose read width selects the rung**:
- **store** at the widest rung the content needs (4-bit 𝕆 symbols);
- **address / index** at any narrower rung by masking — free, no re-encode, and the shadows provably agree;
- **couple / turn** at ℍ (the group ceiling) — the sign channel is the fiber and `the_one` supplies it;
- **the fibration is chosen at read time**, which is the "asymptotic, chosen by the excitation" property.

The honest cost: the shipped genome already commits to per-rung markers (`0x51`/`0x38`/`0x39`) with different *bit-packings* (2/3/4-bit), so the on-disk format is currently side-by-side even though the *algebra* nests. A compounded carrier would store 4-bit and mask on read — trading ~2× space at the V₄ rung for rung-freedom. **That is a real trade, not a free win, and it is the srmech design question to put in the issue.**

## Honest scope
- `[DEMONSTRABLE]`: every homomorphism/nesting/cardinality number above, on shipped ops, exhaustive over the full 8×8 and 16×16 product tables (not sampled).
- **Correction to my own first probe:** I initially tested `oct_mult(a,b)&7 == q8_mult(a&7,b&7)` and got **96/256 violations** — that comparison was **wrong**, not a real failure. It compared 𝕆's *basis index* against Q₈'s *signed algebra* (Q₈ packs sign at bit 2, 𝕆 at bit 3 — different semantics). The correct comparison is each rung against its own ℤ₂ⁿ XOR shadow, which passes cleanly. Recorded because the wrong version would have "refuted" the carrier.
- `[SPECULATIVE]`: §5's design, and the reading that the mask-width choice *is* the excitation/projection choice.
- Not addressed: 𝕊 (dim 16 / ℤ₂⁴) — the zero-divisor rung, where the unit set is still a loop but division fails (F451/F424); whether the shadow ladder continues is untested and the Hurwitz wall makes it a different question.

## Verdict / next
The carrier the user asked for is **not a thing to build — it is a property the shipped encodings already have**, provable in three exhaustive checks. What is *not* free is turn-composability above ℍ (two ceilings, now confirmed both empirically and structurally). The genome's current side-by-side `element_type` design is therefore an **on-disk** choice, not an algebraic necessity — which is exactly the srmech issue to raise.

Composes **F1316** (the 𝕆 order-integrity result whose associator negative is this finding's turn-ceiling, reached independently), **F1315/F1314** (the responsion arc), **F1307** (`_coupler_q8` — shadow + sign, correct in shape because the fiber is one bit), **F1310/F1311** (the 3+1+3 / the (4+3) split), **F451/F424** (the Hurwitz wall), MFO **§VIII.31.18** (*the loss IS the fiber; missing reals complete 1:3:7→2:4:8*; the constructor whose per-rung-cardinality question this **closes**) and **§VIII.31.19** (ℍ as binding pivot; the two-ceilings fence this confirms), `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` (the shadow/fiber split, now with an exact fiber count).

**→ extended by F1318** — the constructor question is answered by separating two uniqueness levels: the 𝕆 **ALGEBRA** is forced by ℍ's (CD doubling, **64/64 exact on the rational `Q` carrier**), but an 𝕆 **ELEMENT** is not (fiber = 2, this finding) — so `the_one` is a **fiber-CLOSER**, not a deriver, and `shadow + the_one → E` round-trips exactly with a different `the_one` landing on the other seat. F1318 also records two scope corrections: **ℍ is not abelian** (the abelian information is the SHADOW, not the algebra), and **GR is out of the ℂ/ℍ/𝕆 → U(1)/SU(2)/SU(3) chain** (internal gauge symmetry ≠ spacetime geometry).

**→ EXTENDED PAST HURWITZ by F1319** — the ℤ₂ⁿ addressing shadow is **not Hurwitz-bounded**: `basis(a·b) == basis(a) XOR basis(b)` is exact at **𝕊 (dim 16, 0/256)** and **dim 32 (0/1024)**, where *division* is already dead. So the ladder continues ℤ₂ ⊂ ℤ₂² ⊂ ℤ₂³ ⊂ ℤ₂⁴ ⊂ ℤ₂⁵…, confirming F1274/F1275 (addressing needs only a signed permutation, never division) and separating THREE ceilings: addressing (unbounded, measured to dim 32) / composition (stops at 𝕆, Hurwitz) / turns (stops at ℍ, S⁷ is not a group).
