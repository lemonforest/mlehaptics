# F1322 — **working the tower BACKWARDS: the abelian shadow ladder is FORCED by ℍ's own structure, and the piece lost at each projection is a GAUGE CHOICE whose CLASS is invariant.** Deconstructing the completed ℍ (Q₈, all 6 subgroups, all 6 quotients, exhaustive) yields **exactly three abelian quotients — 1, ℤ₂, V₄ — all elementary-abelian 2-groups.** The ℤ₂ⁿ shadow ladder is not a modelling choice; it is the **complete list of abelian projections ℍ admits.** Climbing back up, **every rung is a NON-SPLIT ℤ₂ extension** (0/8 sections are homomorphisms), so the lost bit **cannot** be a flat lift — it is a **gauge choice**, and the gauge-invariant residue is the **2-cocycle class** (nonzero, one class, never a coboundary). At 𝕆 the shape **breaks**: the 2-cocycle identity fails on **168/512 triples — exactly the associator-defect set** (set equality, not just count) — which is exactly the **7·6·4 = 168** triples that leave a single ℍ subalgebra. The payoff is an instrument: under **all 256** fiber-seat re-labellings, the **absolute sign is gauge-DEPENDENT**, while the **commutator (order) and associator (richness) are gauge-INVARIANT** — and so is any walk where each axis appears an even number of times. **Holonomy is precisely the part of the winding that survives re-gauging.**

**User (2026-07-25):** *"why can't we work it backwards … find which shadow projections satisfy our abelian math from the deconstruction itself … and then when we try to go back up the tower … find the gauge dependent pieces that end up lost, in the same way that we lose image of B/H/N in the 11D perspective."*

All measured on srmech 0.9.0rc336, exhaustive (not sampled), pure integer — no float, no `abs()`, no numpy, no RNG.

## 1 — DECONSTRUCTION: every subgroup of the completed ℍ `[DEMONSTRABLE]`
```
  |S|=1  [0]                 abelian=True  normal=True   trivial
  |S|=2  [0,4]               abelian=True  normal=True   Z2  = the REAL axis +-1 = the CENTER
  |S|=4  [0,1,4,5]           abelian=True  normal=True   Z4  = a C rung INSIDE H  (the i axis)
  |S|=4  [0,2,4,6]           abelian=True  normal=True   Z4  = a C rung INSIDE H  (the j axis)
  |S|=4  [0,3,4,7]           abelian=True  normal=True   Z4  = a C rung INSIDE H  (the k axis)
  |S|=8  [0..7]              abelian=False normal=True   Q8 = H itself
```
ALL subgroups normal (Q₈ is Hamiltonian). Element orders `[1,2,4,4,4,4,4,4]` — **exactly one involution**, and it is `−1`.

**ℂ has two faces inside ℍ, and they are different objects:** as a **SUBgroup** it is ℤ₄ and there are **three** of them (the i/j/k axes — the 3 of the 1:3:7:3); as a **QUOTIENT** it is ℤ₂. Sub ≠ quotient, and conflating them is easy.

## 2 — which shadow projections ℍ FORCES `[DEMONSTRABLE — the direct answer]`
```
  kernel |K|=1 -> quotient order 8  abelian=False        Q8 (H itself)
  kernel |K|=2 -> quotient order 4  abelian=True  [1,2]  V4 = Z2xZ2
  kernel |K|=4 -> quotient order 2  abelian=True  [1,2]  Z2      (x3, one per C rung)
  kernel |K|=8 -> quotient order 1  abelian=True  [1]    trivial
```
**Abelian quotient orders available: {1, 2, 4}. Every element order in every abelian quotient is 1 or 2.** So every abelian shadow of ℍ is an **elementary-abelian 2-group** — there is no ℤ₄ shadow, no ℤ₃, nothing else.

> **The ladder ℤ₂⁰ ⊂ ℤ₂¹ ⊂ ℤ₂² is the COMPLETE list of abelian projections the completed ℍ admits. Nothing else fits.**

This is the answer to *"find which shadow projections satisfy our abelian math from the deconstruction itself"*: we did not choose ℤ₂ⁿ addressing — **ℍ hands it to us and permits no alternative.** F1317's shadow ladder stops being a design decision and becomes a derived fact.

## 3 — CLIMBING BACK: the lost piece is a GAUGE CHOICE `[DEMONSTRABLE]`
`ker(π: Q₈ → V₄) = {+1, −1}` — **the real axis**, and `π` is exactly the shipped `q8_project_v4`.

```
  normalized sections s: V4 -> Q8 examined            : 8
  sections that are HOMOMORPHISMS (a flat/split lift) : 0        <- NONE
  non-homomorphic pairs per section                   : [6,6,6,6,6,6,6,6]
```
**Q₈ has a unique involution, so it contains no V₄ subgroup — the extension `1 → ℤ₂ → Q₈ → V₄ → 1` is NON-SPLIT.** There is no way to lift the shadow back to ℍ homomorphically. **ℝ→ℂ is non-split too** (ℤ₄ has one involution), so this is uniform, not a Q₈ quirk.

The obstruction is the 2-cocycle `f(u,v) ∈ ℤ₂` with `s(u)s(v) = f(u,v)·s(u⊕v)`:
```
  f lands in the kernel Z2 for every section+pair      : True
  2-cocycle identity f(u,v)+f(uv,w) == f(v,w)+f(u,vw)  : True  (all sections)
  distinct cocycles reachable by re-gauging            : 2
  any reachable cocycle is a COBOUNDARY (splittable)   : False <- the obstruction
  all reachable cocycles differ by a coboundary        : True  (ONE class)
```
> **The lift (the fiber bit) is GAUGE-DEPENDENT. The cocycle CLASS is GAUGE-INVARIANT and NONZERO.**

That is the precise statement of "the gauge-dependent piece that ends up lost."

## 4 — at 𝕆 the shape BREAKS, and the break is exactly the associator `[DEMONSTRABLE — the sharpest result]`
```
  O basis product IS the Z2^3 XOR shadow                      : 0/256 violations
  O signed units are NOT associative (a loop, not a group)    : True
  2-cocycle identity FAILS at O                               : 168 / 512 triples
  associator defect                                           : 168 / 512 triples
  SAME SET (not merely the same count)                        : True
  == exactly the triples spanning all 3 shadow axes (7*6*4)   : True
```
**The two 168s are the same triples.** So `ℍ→𝕆` is **not a group extension at all** — and it fails to be one **exactly where the triple leaves a single ℍ subalgebra**. The 2-dimensional shadow subspaces **are** the ℍ rungs; stay inside one and everything is a clean group extension, step outside and there is no cocycle to speak of.

**The ceiling ladder gets its reason.** F1319 listed three ceilings empirically; this says *why*:

| level | stops at | because |
|---|---|---|
| addressing (ℤ₂ⁿ shadow) | never (exact to dim 32) | basis products are a signed permutation |
| **group extension / cocycle** | **ℍ (dim 4)** | **associativity — 168 triples break the identity at 𝕆** |
| composition (division) | 𝕆 (dim 8) | Hurwitz |

## 5 — THE INSTRUMENT: what survives re-gauging `[DEMONSTRABLE — exhaustive, all 256 gauges]`
Re-gauging = re-labelling which of the two fiber seats is "positive," i.e. `s'(u) = ε(u)·s(u)` for any `ε: ℤ₂³ → {±1}`. **All 256 tested at 𝕆, all 16 at ℍ:**

| quantity | gauge-invariant? | what it is |
|---|---|---|
| **ABSOLUTE sign** of one product `s(u)s(v)` | **NO** | a convention — **not structure** |
| **COMMUTATOR** — two ORDERS of one pair | **YES** | the genuine **order** read (k=2) |
| **ASSOCIATOR** — two BRACKETINGS of one triple | **YES** | the genuine **richness** read (k=3) |
| walk with each axis an **even** number of times | **YES** | a **holonomy** |
| open word (each axis once) | **NO** | gauge artifact |

At ℍ the commutator is invariant across all 16 gauges and **non-trivial (6 anticommuting pairs)** — the order read is real structure, not bookkeeping.

**This retro-explains F1316.** "The associator is a richness read, not an order read" now has its reason: *same multiset, two **orderings** = commutator = order (k=2); same multiset, two **bracketings** = associator = richness (k=3).* Both are gauge-invariant because the ε's cancel in a ratio of two arrangements of the same word. They measure different things because k=2 and k=3 are different.

**And it validates F1321 structurally.** A closed / even-multiplicity walk cancels every ε; an open word does not. So **holonomy is precisely the gauge-invariant part of the winding** — which is why "the resonant shape of the cascade *with holonomy*" is the right object and a bare absolute sign is not. F1321 measured that `klein4_from_one` drops the winding; this says the part worth keeping is specifically the **holonomy**, not the raw sign.

**Usable as a ratchet:** *any claimed structure in our encodings must be invariant under re-choosing which fiber seat is positive.* If a number moves when you re-gauge, it is a gauge artifact, not a finding. This is a cheap, mechanical falsification test we did not previously have.

## 6 — the B/H/N analogy is EXACT, not loose `[DEMONSTRABLE]`
```
  what Q8 -> V4 loses          : {+1,-1}  = the REAL axis
  what the V4 shadow retains   : {i,j,k}  = the IMAGINARY directions only
```
**14 → 11D loses the 3 REAL grammar anchors (B, H, N). Q₈ → V₄ loses the 1 REAL anchor (±1).** Same move at different rungs: **the abelian shadow keeps the imaginaries and drops the real/scalar part — and the real part is exactly what carries the which-way.** The user's analogy is not a metaphor; it is the same projection, and F1321's A–N slot tagging (`grammar_slots = ('B','H','N')` = the three reals) is what makes them literally comparable.

## Honest scope
- `[DEMONSTRABLE]`: everything above is **exhaustive**, not sampled — all 256 subsets of Q₈ for the subgroup lattice, all 6 quotients, all 8 normalized sections, all 512 𝕆 triples, all 256 gauge re-labellings at 𝕆 and all 16 at ℍ.
- **"Gauge" here means the ℤ₂ fiber-seat re-labelling** (a section change in a ℤ₂ extension). It is *not* a continuous gauge group, and no claim is made that it is the gauge freedom of any physical theory. The word is used because the structure is literally a choice of section with an invariant class — do not let it drift into a physics claim.
- The ℂ→U(1) / ℍ→SU(2) / 𝕆→G₂ chain is **not** revisited here; F1318 already fenced it (and fenced GR out of it).
- `[SPECULATIVE]`: that the re-gauging ratchet will actually catch a live defect in our encodings. It is a sound test and cheap to run; **it has not yet been applied to any shipped genome read.** That is the concrete next step, and it is the honest limit of this finding.
- Not addressed: what replaces the cocycle at 𝕆. A loop extension has no `H²` in the group sense; the associator is the invariant, but whether it assembles into a usable "class" is **unmeasured**.

## Verdict
Working backwards **works**, and it converts three things from choices into consequences: the **ℤ₂ⁿ shadow ladder is forced** by ℍ alone; the **lost bit is necessarily a gauge choice** (no rung splits); and the **gauge-invariant residue** is the cocycle class at ℍ and the associator at 𝕆. The by-product — a mechanical re-gauging test that separates structure from convention — is the most immediately useful thing here. Generating code: `R-RBS-LM-BACKWARDS_*.py` (exit 0).

Composes **F1321** (the resonant cascade shape with holonomy — *its direction is validated: holonomy is exactly what survives re-gauging*), **F1320** (the fiber is a function — *the cocycle is now identified as the gauge-invariant residue*), **F1319** (the three ceilings — *the middle one gets its reason: the 168 associator triples*), **F1318** (algebra forced / element not — *"forced" is now proved at the shadow level too*), **F1317** (the shadow ladder — *promoted from design to derivation*), **F1316** (associator = richness not order — *explained: bracketings vs orderings*), **F1307** (klein4 discards the winding), **F451/F424** (the Hurwitz wall), `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` (*sharpened: the bit-exact shadow is the **gauge-fixed** projection*), `[[feedback_computational_provenance_discipline]]`.
