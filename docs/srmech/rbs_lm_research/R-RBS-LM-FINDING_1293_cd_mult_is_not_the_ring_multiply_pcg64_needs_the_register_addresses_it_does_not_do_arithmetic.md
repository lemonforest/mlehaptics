# F1293 — **no: the Cayley-Dickson product is a different operation than the ring multiply PCG64 needs, and the CDRegister addresses slots — it does not do arithmetic.** Measured: `cd_mult((hi,lo),(mh,ml))` and the modular multiply `(state·mult mod 2¹²⁸)` give **different results** — the ℂ-product carries a `−bd` cross-term and no reduce, while the ring multiply has inter-limb carries and reduces mod 2¹²⁸. So a CD-based RNG would be a **different stream**, breaking the bit-exactness that was the entire point. The 128-bit state's `(hi,lo)` *shape* is a valid dim-2 CD coordinate for **storage/addressing** — but the **dynamics** are ring arithmetic, not the CD algebra. Storage-shape ≠ operation-algebra (F1132/F1216 again).

**User (2026-07-21):** *"then why can't we do the cayley-dickson form of the math and use our cdregister?"*

Good instinct — the register is our general hypercomplex instrument, and a 128-bit state *is* two 64-bit halves, which looks CD-shaped. So the question is whether PCG64's multiply is secretly a CD product. Measured, it is not.

## (1) `cd_mult` is not the ring multiply — measured
Split the 128-bit state into `(hi, lo)`, the ℂ-shaped 2-coordinate:

| | first coord |
|---|---|
| **ring multiply** `state·mult mod 2¹²⁸`, hi | `11613906214716028088` |
| **`cd_mult((hi,lo),(mh,ml))`** | `−170210993351517534803505` |

**Not the same operation.** The ℂ-product of `(a,b)·(c,d)` is `(ac − bd, ad + bc)` — a specific bilinear form with a **`−bd` cross-term** and **no carry, no reduce**. The ring multiply is full-width schoolbook multiplication with **inter-limb carries**, then a reduce mod 2¹²⁸. Different algebra: ℤ/2¹²⁸ (a commutative ring) is *not* ℂ over ℤ/2⁶⁴ (a Gaussian-integer-like structure, `i² = −1`). They are not isomorphic, so one cannot stand in for the other.

## (2) The CDRegister addresses; it does not compute
Its ops are `write` / `navigate` / `read` (F1275) — and `navmap` is a **signed permutation**, verified. It is the *navigate, don't divide* instrument: it routes content across slots. **There is no ring-multiply, no mod-reduce, no carry anywhere in its surface.** An LCG step *is* arithmetic in ℤ/2¹²⁸, so the register is the wrong tool for the step — not because it is weak, but because it is a **different kind of thing**.

## (3) The real distinction underneath — and it is one the framework already teaches
The `(hi, lo)` *shape* of a 128-bit integer genuinely IS a dim-2 CD coordinate, and the register could **hold and route** it. What it cannot do is **run the step**. That is exactly the **storage-shape vs operation-algebra** split:

- **F1132**: relational-vs-distributional is an *encoding-type* axis, separate from *storage*.
- **F1216**: Class-L store vs Class-M working-memory — *which structure you keep* is separate from *what you compute with it*.

Here: **storage-shape** (a 2-limb CD coordinate — fine) is a different axis from **operation-algebra** (ring multiply mod 2¹²⁸ — required). Reaching for `cd_mult` because the *state* is CD-shaped is the same category slip the framework's own vocabulary discipline warns against — using a storage resemblance to pick an operation.

## (4) There would be no motive even if it worked
F1292 already showed the ring multiply is **directly available** — `bigint_mul_c` handles the 128-bit product and the reduce is a Class-K mask. So even setting aside that `cd_mult` gives the wrong answer, **there is no capacity gap for CD to fill.** The arithmetic PCG64 needs is shipped and works.

## The honest both-sides
- **For the stated goal (bit-exact with numpy → Tier 3 becomes a rename): no.** A `cd_mult`-based generator produces a stream that is not PCG64, so every Tier-3 file would still change its numbers — the exact re-run F1290 was trying to avoid. CD *defeats* the purpose here.
- **As its own research direction: genuinely interesting, and separately.** A generator built from `cd_mult` + the register's navigate would be a **framework-native RNG** — order-sensitive above ℍ, addressable, no numpy. But it is a *new* generator with *no reference*, so it only makes sense if we ever accept re-running the corpus under a native RNG. That is a real question, just not *this* question. It does not make Tier 3 a rename.

So the PCG64 path stays as F1292 left it: the arithmetic is ring-multiply (shipped, works), and the only remaining gates are the *correctness* ones — attested constants and a reference stream. CD is the right instrument for **addressing** (F1275, confirmed to dim 256) and the wrong one for **modular arithmetic**, and keeping those apart is the finding.

Composes **F1292** (the ring multiply already works — so no capacity motive), **F1275** (the register is an addressing instrument), **F1132/F1216** (storage-shape vs operation-algebra), **F1290/F1291** (Tier 3), `[[feedback_reach_for_the_one_for_phase_crank_navigation]]` (θ-crank is abelian addressing; walk-order is cd_mult — neither is ring arithmetic).
