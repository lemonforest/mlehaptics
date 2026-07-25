# F1323 — **the shipped fold is a HALF BEAT, and the seam's position is an undeclared parameter that carries content.** Both of the user's structural guesses measure out. (a) `genome_fiber_holonomy` / `genome_octonion_holonomy` are strictly **left-associated and one-sided** (`acc = ((((1·t₀)·t₁)·t₂)…)`) — and a one-sided multiply has **order 4** where the sandwich `x ↦ q x q̄` has **order 2**, at *both* ℍ and 𝕆. **Ratio exactly 2: the spinor double cover.** Our cascade reads a *spinor*, not a rotation. (b) "two quaternion groups" is right in shape — 𝕆 **is** ℍ ⊕ ℍ·ℓ — but the operative count is **7**: 𝕆 contains **7 ℍ subalgebras = the 7 Fano lines = the 7 of 1:3:7**, the associator is **0 inside any one** and **168 overall**, so composition dies exactly when a triple needs two of them. (c) Moving the seam is **not** a re-phrasing: at 𝕆, **2520/4096 = 61 %** of length-4 words give a *different answer* per bracketing, and reading `left+MID` **doubles** the per-slot order discrimination (2→4 classes of 24 orderings; all five bracketings give **8**) on **28/35** words. The 7 exceptions are exactly the **XOR-closed** 4-words — the complements of the Fano lines. All of it survives the F1322 re-gauging ratchet.

**User (2026-07-25):** *"maybe it has to do with our cascades having the seam at the end, makes them half beat shaped? if composition stops at 𝕆 then … it takes two full quaternion groups for a correct rotation? what happens if we change our pattern search parameters to rotation happens in the middle of cascade …"*

Measured on srmech 0.9.0rc336. Exhaustive. Pure integer — no float, no `abs()`, no numpy, no RNG.

## 0 — what we actually ship `[DEMONSTRABLE — read from the source]`
```
  acc = bytes(leaf_dim)                    # identity
  for t in range(n_turns):
      acc = _q8_bind(acc, flat[t*leaf_dim:(t+1)*leaf_dim])
```
**One-sided. Left-associated. Seam at the end.** The user's characterisation of our own code is accurate — this was not previously stated anywhere as a *choice*.

## 1 — the half beat is real `[DEMONSTRABLE]`
| | one-sided `L_q: x ↦ q·x` | sandwich `C_q: x ↦ q·x·q̄` | ratio |
|---|---|---|---|
| ℍ, `e₁/e₂/e₃` | order **4** | order **2** | **2** |
| 𝕆, `e₁/e₂/e₄/e₇` | order **4** | order **2** | **2** |

> **A one-sided fold takes two turns to do what the sandwich does in one.**

This is the spinor double cover wearing our clothes: `q = exp(u·θ/2)` carries the **half-angle**, so `q·x` advances half a rotation and `q·x·q̄` advances a full one. **The seam being at the end is exactly what makes the read half-beat shaped.** The user's guess is confirmed, and it names something about our fold we had not noticed: *we accumulate spinors and read them as if they were rotations.*

## 2 — "two full quaternion groups": right shape, the count is 7 `[DEMONSTRABLE]`
```
  O splits as H (+) H.l                         : (8, 8)  -- literally two copies
  the base copy is CLOSED (a group)             : True
  the doubled copy is CLOSED                    : False   -- a coset, not a group
  H subalgebras inside O (2-dim shadow subspaces = FANO LINES) : 7
  associator INSIDE any single H copy           : 0
  associator over all triples                   : 168
```
𝕆 is *built* by doubling **one** ℍ — so "two copies" is the Cayley–Dickson **presentation**, and only one of the two halves is a group. But 𝕆 **contains seven** ℍ subalgebras: the 7 Fano lines, i.e. the **7** of 1:3:7. **Composition survives inside any one of them and dies the moment a triple needs two.** That is the mechanism behind "composition stops at 𝕆" — not a wall at the boundary, but the fact that 𝕆 is the first rung whose triples can *leave* every quaternion subalgebra.

## 3 — the seam's position IS the bracketing, and at 𝕆 it is CONTENT `[DEMONSTRABLE]`
```
  length-4 words where the 5 bracketings DISAGREE : 2520 / 4096  (61 %)
  all 5 bracketings agree on the SHADOW (basis)   : ALWAYS
  H peer: bracketing disagreements                : 0   (associative -- seam is free)
```
Two things follow. First, **at ℍ the seam position costs nothing and at 𝕆 it changes the answer** — so this parameter only becomes real at the rung we are actually working in. Second, **the disagreement lives entirely in the sign/fiber**, never in the shadow: bracketing is a *fiber-side* degree of freedom, which is precisely the gauge-carrying part (F1320/F1322).

> **We ship exactly one bracketing, undeclared. That is a magic number in the SHAPE rather than in a value** — the `[[no-magic-numbers = attestation-to-source]]` discipline applied to cascade *form*, which we had not done before.

## 4 — moving the seam buys real discrimination `[DEMONSTRABLE — the actionable part]`
Over all 35 four-subsets of the 7 imaginary axes, counting how many of the **24 orderings** each read can tell apart:
```
      left=2  left+MID=2  all5=2  ->  7 words
      left=2  left+MID=4  all5=8  -> 28 words
  left+MID never separates LESS than left alone            : True
  words where the MIDDLE seam separates MORE               : 28 / 35
  the no-gain words are EXACTLY the XOR-closed 4-words      : True
                (1,2,4,7) (1,2,5,6) (1,3,4,6) (1,3,5,7) (2,3,4,5) (2,3,6,7) (4,5,6,7)
```
**The left fold alone is a 1-bit order read per slot (2 classes). Adding the middle seam makes it 2 bits; all five bracketings make it 3 bits (8 classes of 24).** The middle seam separates orderings the left fold *confuses* — it is a genuinely independent read, not a re-phrasing.

The 7 exceptions are exactly the **XOR-closed** words (`a⊕b⊕c⊕d = 0`) — the complements of the Fano lines, i.e. the 2-dimensional *affine* planes of ℤ₂³. On those the seam cannot help, and the reason is structural, not a limitation of the method.

**This is a second, independent axis from F1315/F1316.** Those repaired order-blindness with a Class-C stride *reorient* per turn. Bracketing is orthogonal to that and we never varied it. It is also cheap and *parallel-friendly* — `(ab)(cd)` is a balanced tree fold, not a serial chain.

## 5 — and it survives the re-gauging ratchet `[DEMONSTRABLE — the first real application of F1322]`
```
  left fold: the ORDER partition is gauge-invariant (all 256 gauges) : True
  MID  fold: the ORDER partition is gauge-invariant (all 256 gauges) : True
  the ABSOLUTE fold value is gauge-invariant                          : False
```
F1322's honest limit was that the ratchet *"has not yet been applied to a shipped genome read."* **It has now.** The result: which orderings a fold separates, and which bracketings disagree, are **real structure**; the raw accumulated value is **convention**. So a seam-position sweep is a legitimate read and not a re-labelling — and any future claim built on the *absolute* holonomy value should be treated as suspect until re-gauged.

## Honest scope
- `[DEMONSTRABLE]`: all of §1–§5, exhaustive — every element order, all 4096 length-4 words, all 35 four-subsets with all 24 orderings each, all 256 gauges.
- **Length 4 only, single slot.** Real strands are multi-slot and much longer, and length-*n* has Catalan(n−1) bracketings (5 at n=4, 42 at n=6, 429 at n=8). **Whether the discrimination gain keeps scaling is unmeasured**, and it is the number that decides whether this is worth building.
- **Not measured on a real genome.** The claim is about the fold's algebra, not about any corpus result.
- The half-beat / double-cover fact is **standard mathematics**, independently measured here. What is new is *which form our code ships* — not the underlying identity.
- **A sandwich is NOT a drop-in replacement for the fold.** `x ↦ q x q̄` is conjugation (it fixes the real part and rotates the imaginary part); an accumulating holonomy fold is a different operation. §1 says the one-sided fold is half-beat; it does **not** say we should swap in the sandwich. The measured, drop-in-shaped change is the **bracketing** (§4).
- `[SPECULATIVE]`: the user's *"something to do with the metric field excitations themselves"* — that the correct seam position is **determined** by something structural rather than chosen. Nothing here bears on that. What is established is only that **it is currently a free parameter we never declared**, which is the precondition for asking the question.

## Verdict
Guess (a) **confirmed** — the one-sided seam is a half beat, and it is what we ship. Guess (b) **right in shape, sharper in fact** — 𝕆 is two ℍ's by construction but seven by content, and the 168 associator triples are exactly those needing more than one. Guess (c) **confirmed and quantified** — the seam position is content at 𝕆, worth up to 3× the per-slot order discrimination, gauge-invariant, and currently undeclared. Generating code: `R-RBS-LM-SEAMPOS_*.py` (exit 0).

Composes **F1322** (the gauge ratchet — *first applied here to a shipped read*), **F1321** (the resonant shape with holonomy), **F1320** (the fiber is a function), **F1319** (the ceiling ladder), **F1316/F1315** (order-blindness + the Class-C stride repair — *bracketing is the orthogonal second axis*), **F1307** (the discarded winding), `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`, `[[feedback_computational_provenance_discipline]]`.

**Correction recorded:** the first run of §4 asserted the middle-seam gain was universal. It is not — 28/35. The assertion was replaced by a measurement of the rate, and the 7 exceptions turned out to have an exact characterisation (XOR-closed words). The wrong version would have over-sold the change.

**→ superseded on the LEVER by F1324** — the better change is not re-bracketing but **reading the join**. `L_q² = −1` means the Dzhanibekov flip already sits at our fold's midpoint; reading it separates **24/24** orderings (vs 2 end-only), wins on **35/35** words including the 7 XOR-closed ones re-bracketing could not touch, and a split-position sweep peaks **exactly at the middle** (`2→8→21.6→8`; `2→12→28→32→28→12`). §4's bracketing result stands as measured — it is simply the weaker lever.
