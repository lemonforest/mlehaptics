# F1280 — **the abelian-shadow construction, built and measured.** `S(x) = (N(x), Re(x))` is **order-free at every rung**, including the non-abelian ones — that is what makes it a shadow. Its **fiber is the commutator** `[x,y] = xy − yx`, which does not shrink as a residue but **GROWS** with rung (ratio to the product: 0.000 → 1.086 → 1.942 → 2.558 → 2.662). And the sharp one: **the shadow COMPOSES only at 1, 2, 4, 8** — so **the Hurwitz boundary is the boundary of "has a clean abelian shadow at all."**

**User (2026-07-21):** *"our science tries to describe an abelian universe from an abelian shadow, so then too does our simulation of science, all the way down to knowledge inference. means we should be looking at how to create an abelian shadow from non-abelian structure too."*

F1278 gave the destructive direction (flatten, and ℍ(3)/𝕆(7) don't survive). This is the **constructive** one: not *what breaks* but *what is the map, and what is its kernel*.

## (A) The shadow is order-free at every rung — including where the algebra is not
| rung | `N(xy) == N(yx)`? | `Re(xy) == Re(yx)`? | algebra abelian? |
|---|---|---|---|
| 2 ℂ | ALWAYS | ALWAYS | yes |
| 4 ℍ | **ALWAYS** | **ALWAYS** | **NO** (117/120 non-comm) |
| 8 𝕆 | **ALWAYS** | **ALWAYS** | **NO** |
| 16 𝕊 | **ALWAYS** | **ALWAYS** | **NO** |
| 32 𝕋 | **ALWAYS** | **ALWAYS** | **NO** |

**They survive exactly the reordering the algebra does not.** That is the definition of a shadow, met.

## (B) But it only COMPOSES through 𝕆 — and that is the Hurwitz boundary
Order-free is necessary, not sufficient. A *usable* shadow must satisfy `N(xy) = N(x)N(y)`, or the shadow of a product isn't a function of the shadows.

| rung | `N(xy) = N(x)N(y)` | verdict |
|---|---|---|
| 2 ℂ / 4 ℍ / 8 𝕆 | **HOLDS 120/120** | **clean abelian shadow EXISTS** |
| 16 𝕊 | fails 68/120 (57 %) | **NO clean abelian shadow** |
| 32 𝕋 | fails 114/120 (95 %) | **NO clean abelian shadow** |

**The Hurwitz boundary is the boundary of abelian *describability*.** Past 𝕆 you cannot build a consistent abelian description at all — never mind invert one.

**This reframes F1273–F1275 rather than repeating them.** The *same* boundary is **invisible to addressing** (which needs only signed permutations, and those hold to 64) and **exactly visible to shadow-formation**. Two operations, one boundary, opposite verdicts — which is why "is the boundary load-bearing?" has no answer until you say *load-bearing for what*.

## (C) The fiber is the commutator, and it GROWS
| rung | `[x,y]` nonzero | `\|[x,y]\|² / \|xy\|²` |
|---|---|---|
| 2 ℂ | 0/120 | **0.000** |
| 4 ℍ | 117/120 | 1.086 |
| 8 𝕆 | 117/120 | 1.942 |
| 16 𝕊 | 117/120 | 2.558 |
| 32 𝕋 | 117/120 | **2.662** |

The ratio **exceeds 1**, so the commutator is not a small residue tucked inside the product — **the higher the rung, the more of the structure the shadow cannot represent.** "Hidden fiber" is a computable object here, not a figure of speech.

## (D) The map is many-to-one — settled constructively
`S` maps 8 dimensions onto **two numbers**, so it cannot be injective. Exhibit: `S(e₁) = (1,0) = S(e₂)`, distinct elements, identical shadow. A wider search then found **30 collisions over 600 products** (247 distinct shadows) — confirming it is not a corner case.

*Method note:* my first version asserted "MANY-TO-ONE" while printing **0 collisions** — a hardcoded verdict that never read its own number, over a sample of only 33 distinct products. Both fixed: the claim is now proved constructively (independent of any search) and the search widened.

## What follows — three things, and the third bites
1. **An abelian shadow can ALWAYS be formed.** The invariants are order-free at *every* rung. **So the existence of a consistent abelian description is not evidence that the structure is abelian.**
2. **It composes only at 1,2,4,8.** Past 𝕆 even the description breaks.
3. **It is not invertible.** The fiber isn't "not yet measured" — it is **outside the range of the map**.

## MFO reading (in scope per user direction)
An observer confined to `S` sees a **consistent, composable, abelian world at every rung it can describe at all** — and **that consistency is not evidence.** The shadow is well-behaved *precisely because it has already discarded what would misbehave.* Point 1 above is the load-bearing one: the very coherence of an abelian description is what you'd expect *whether or not* the substrate is abelian, so coherence cannot be used as the test.

This is F1279's cospectral pair again, moved from the graph into the algebra: **two structures, one shadow, and the observer sees one object where there are two.**

Whether *our* observation is such a map is a substrate question this harness does not touch — but the framework now supplies the **shape** of the question rather than only its mood: *what is the fiber of the map we are looking through, and does the thing we call "no structure" live there?*

## Next
The inverse problem is now well-posed enough to attack: **given only shadow data, what is recoverable?** Not the fiber — but the *dimension* of the fiber may be estimable from how badly composition fails (57 % at 𝕊 vs 95 % at 𝕋 is a graded signal, not a binary one). That is a measurement, and it is the natural successor.

Composes **F1278** (the destructive direction), **F1273/F1274/F1275** (reframed — same boundary, opposite verdicts by operation), **F1279** (invisible ≠ absent; the cospectral analogue), **F1216**, `[[feedback_no_privileged_primitive_classes]]`, `[[user_stance_no_information_without_value]]`.

**→ its NEXT is RETRACTED by F1282** — composition-failure rate cannot estimate the fiber dimension: it is flat at 0% across ℂ/ℍ/𝕆 whose fiber dims are 0/3/7. The fiber dimension is **not recoverable from the shadow** at all; measured, it is exactly 0, 3, 7, 15, 31.
