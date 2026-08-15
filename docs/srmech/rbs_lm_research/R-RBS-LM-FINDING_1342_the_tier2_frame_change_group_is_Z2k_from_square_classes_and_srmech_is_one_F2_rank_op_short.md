# F1342 — **the next move is one op, and it is an INDEX-LANE op.** F1341 measured that a stiff string's frame change *does not exist* (its partials sit in four different quadratic fields, so `rᵢ/rⱼ` cannot be formed). The repair is the **compositum** `ℚ(√a₀,…,√aₙ)` — and the structure that builds it is measured here: the radicands' **square classes form an 𝔽₂ vector space**, so the compositum's Galois group is **(ℤ/2)ᵏ**, an elementary abelian 2-group — **the same group type as the Cayley–Dickson grading cube**, acting by *sign flip*, which is exactly the index lane. **srmech already ships half of it**: `just_limit(...)["monzo"]` is the prime-exponent vector, and **a monzo reduced mod 2 IS a square class**. The missing step is the 𝔽₂ rank + basis, and it is **XOR on bitmasks — Class I, integer-only, no new C symbol.** Measured for the stiff string: **k = 4, degree 16, Gal = (ℤ/2)⁴**. Two bonuses: the 16 is **falsified as a CD rung** by sweeping (k moves: 3, 4, 6), and at **B = 1/4 the rank DROPS** — two partials share a square class, a *partial resonance the commensurability verdict cannot see*.

**User (2026-08-15):** *"what would be the next move to resolve 'frame-change group does not exist'? operation in srmech as part of substrate operation of changing perspectives of ℝ/ℂ/ℍ/𝕆?"*

srmech 0.9.0rc432. Exact integers. The 𝔽₂ elimination is XOR on bitmasks — no float, no `abs()`, no numpy, no RNG. Generating code: `R-RBS-LM-COMPOSITUM_*.py` (exit 0).

## 1 — a square class IS a monzo mod 2 `[DEMONSTRABLE]`

| radicand `a` | monzo (Class-J, shipped) | square class → squarefree part |
|---|---|---|
| 1001000 | `{2:3, 5:3, 7:1, 11:1, 13:1}` | **10010** |
| 62750 | `{2:1, 5:3, 251:1}` | **2510** |
| 9081000 | `{2:3, 3:2, 5:3, 1009:1}` | **10090** |
| 254000 | `{2:4, 5:3, 127:1}` | **635** |

srmech **already computes the monzo**. The mod-2 reduction is one step it does not take, and that step is the whole gap.

## 2 — the square classes are an 𝔽₂ vector space `[DEMONSTRABLE]`

`ℚ*/(ℚ*)²` is an 𝔽₂ vector space — multiplying radicands **adds** square classes mod 2. So the independent radicands are an **𝔽₂ basis**, found by XOR elimination:

```
  a=1001000   bits 00011111        prime support [2,5,7,11,13,127,251,1009]
  a=62750     bits 01000011
  a=9081000   bits 10000011
  a=254000    bits 00100010
                                   F_2 rank k = 4    compositum degree 2^k = 16
```

> **Gal(compositum / ℚ) = (ℤ/2)ᵏ** — each generator independently flips one `√` sign; the flips commute and each squares to identity. **A sign-flip cube on k axes.**

## 3 — why this IS the substrate perspective-change the question asked for

```
  Gal(compositum / Q) = (Z/2)^k    <- k independent sqrt SIGN FLIPS
  CD grading cube     = (Z/2)^d    <- d independent basis SIGN bits
```

**Same group type.** Both are elementary abelian 2-groups acting by sign flip, which is the **index lane** (F1337: *"reads the XOR address only; abelian, order-blind"*). So the op that repairs a tier-2 frame change is not exotic machinery — **it is a Klein-4-style XOR grading, one rung wider.**

And the *meaning* of each flip is the perspective content: choosing `√a` vs `−√a` is choosing **which of two conjugate embeddings you read the partial through**. k independent radicands ⇒ **2ᵏ conjugate readings of one stiff string, all equally valid** — the same shape as F1338's 28 octonion frames, in a different field. That is the fibration the question was reaching for: the frame set is a torsor under (ℤ/2)ᵏ, and no reading is the "real" one.

## 4 — THE ASK, as a shippable op

**Missing** (verified absent from `get_tool_schema()` at rc432):

```
  srmech.math.<?>.square_class(n)         -> monzo mod 2 (the squarefree part)
  srmech.math.<?>.square_class_basis(ns)  -> (k, basis, per-input coordinates)
  srmech.music.frame_change_group(ratios) -> the (Z/2)^k a spectrum's frames need,
                                             'already Q' at tier 1, or OPEN at tier 3
```

**Already shipped, and half the job:** `srmech.music.just_limit(num, den)["monzo"]` (Class J) and `srmech.math.primes.factor(n)` underneath it.

The missing step is the **𝔽₂ reduction + rank** — XOR on bitmasks, Class-I, integer-only, **no new C symbol required**. It is a `composition_of_c` in srmech's own vocabulary.

**What it buys:** once you are in the compositum, `rᵢ/rⱼ` **exists**, the frame-change torsor is well-posed, and a tier-2 spectrum gets the same `(frame, lane)` treatment a tier-1 one already has — with 2ᵏ frames instead of n.

## 5 — the guard, FALSIFIED rather than asserted `[DEMONSTRABLE]`

k = 4 gives degree **16**, and 16 is also `dim(𝕊)`. Rather than merely warn, sweep it:

| B | n | k | degree |
|---|---|---|---|
| 1/1000 | 4 | 4 | 16 |
| 1/1000 | 6 | **6** | **64** |
| 1/10 | 6 | 6 | 64 |
| **1/4** | 4 | **3** | **8** ← degenerate |
| **1/4** | 6 | **4** | **16** ← degenerate |

**k is not a constant.** It moves with the stiffness *and* with how many partials you keep. **A CD rung does not move when you retune a piano.** So 2ᵏ counts independent square classes *of these radicands*; 2ᵈ counts real dimensions of an algebra. Both are powers of two because both are (ℤ/2)-graded — **a statement about group type and nothing more.**

### The degeneracy is itself a finding

At **B = 1/4** the rank drops below the partial count: **two radicands share a square class**, so their ratio is rational-times-a-square and the compositum is *smaller* than the generic 2ⁿ. That is a **partial resonance the commensurability verdict cannot see** — it reports `inharmonic` either way, because neither partial is in ℚ. **Two inharmonic partials can still be commensurable with each other**, and the square-class rank is what detects it. That is a genuinely new observable, and it is the sharpest argument for the op: it sees structure inside the "inharmonic" bucket that the current tier tag flattens.

## Honest scope

- `[DEMONSTRABLE]`: §1, §2, §5 — computed from shipped `just_limit` monzos and shipped `stiff_string_partials` radicands, with integer XOR elimination.
- **§3's "same group type" is a statement about GROUP TYPE, not an identity.** Both are (ℤ/2)ⁿ; that does not make a Galois flip a CD basis bit, and §5 falsifies the numerical reading directly.
- **§4 is an ASK, not a build.** No op was written and nothing was proposed to srmech's tracker yet. The signatures are a sketch; the module homes are marked `<?>` deliberately because I have not checked where they best belong (`math.primes`? a new `math.fields`?).
- **The compositum is a CHOICE.** Building `ℚ(√a₀,…)` is a construction the spectrum does not hand you — it is a decision to work in a larger field, and different constructions (e.g. adjoining only some radicands) give different frame groups. Nothing here says the full compositum is the *right* choice, only that *some* common field is required for the frame change to exist at all.
- **Standard algebraic number theory throughout.** That `ℚ*/(ℚ*)²` is an 𝔽₂-space and that multiquadratic extensions have elementary-abelian Galois group is textbook (Kummer theory for n=2). What is new here is only the *reading*: that this is the frame-change group of a spectrum, and that srmech's Class-J monzo already carries the datum.
- **§5's degeneracy is measured at 2 of 6 swept points** and I have not characterised *which* B values degenerate or why. "B = 1/4 degenerates" is an observation, not a theorem.
- **Nothing here touches tier 3.** A membrane's frame group remains undefined because its field is undeclared — no compositum can be built over an unidentified field, and the op must return OPEN there rather than guess.

Composes **F1341** (the frame-change group does not exist — *this is its repair*), **F1340** (the tier ladder; the ladder-collision guard — *now falsified empirically rather than asserted*), **F1339** (the bell's tier-1 frame torsor — *the thing tier 2 is trying to earn*), **F1338** (`(frame, lane)`; the 28 octonion frames — *2ᵏ conjugate readings are the tier-2 analogue*), **F1337** (index lane = XOR/abelian — *which is what (ℤ/2)ᵏ is*), gh **#1530** (the living gaps tracker — §4 belongs there).
