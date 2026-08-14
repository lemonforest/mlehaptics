# F1340 — **the ablation is FLAT on all three substrates, which means F1339's result was about a READ, not about the object.** Running the same ablation on the 1-D stiff string and the 2-D membrane hits an obstacle that turns out to be the finding: `common_period` **raises** for both, because a period only exists for a commensurable spectrum. Taken instead on the **invariant** (`verdict`, full-rank?, which degrees occur) — which exists at every tier — **no partial is load-bearing on any of the three.** So the bell's dramatic 10 → 2 collapse is entirely a **period** effect, and the period is the frame-dependent read. Three further measured results: **dimension does not set the tier** (1-D→2, 2-D→3, 3-D→1, non-monotone — a *tuner*, not geometry, sets it); the stiffness sweep is a **step function, not a slope** (B = 10⁻¹² is exactly as inharmonic as B = 1/10; only B = 0 is in ℚ); and the membrane, whose ratios are fixed-point rationals, returns a **FALSE `'harmonic'` with full rank 9/9** if you omit the `open_partials=` declaration — caught downstream only by a **39-digit denominator**.

**User (2026-08-14):** *"now try the same ablation on membrane and stiff string partials … these are instances of the same process on varying substrate and perspective, so the thing we're looking for needs to describe from string to 3D asymmetric and tuned box … on up to this hypercomplex object, that when fibrated downward still describes the 2d string and 3d box/body resonators."*

srmech 0.9.0rc432, `srmech.music.*`. Exact-ℚ / exact-algebraic. Never `best_rational` on a spectrum. No `abs()`, numpy, RNG. Generating code: `R-RBS-LM-TIERABLATE_*.py` (exit 0).

## 1 — one process, three substrates `[DEMONSTRABLE]`

| substrate | dim | tier | verdict | rank | degrees |
|---|---|---|---|---|---|
| **bell** — cast metal, TUNED | **3-D** | **1** rational | `harmonic` | 5/5 | all 1 |
| **stiff string** — wire + stiffness | **1-D** | **2** algebraic | `inharmonic` | 0/6 | all 2 |
| **membrane** — drumhead | **2-D** | **3** open | `open` | 0/9 | all 1 † |

† the membrane's degrees read 1 because its ratios are fixed-point rationals at a declared precision — see §4.

> **DIMENSION DOES NOT SET THE TIER.** 1-D → 2, 2-D → 3, 3-D → 1. Non-monotone in both directions.

The most geometrically complex object here — a cast bronze bell — has the **simplest** spectrum, because a founder **tuned it back into ℚ**. The simplest object — a wire — sits a tier *above* it, because stiffness is physics and nobody removed it. **What sets the tier is whether something forced commensurability, not how many dimensions vibrate.** That is the direct answer to *"varying substrate and perspective"*: the substrate does not determine the algebra; an *intervention* does.

## 2 — the ablation, generalised `[DEMONSTRABLE — the correction to F1339]`

| substrate | invariant-ablation | period-ablation |
|---|---|---|
| bell | **NONE move** | period 10, load-bearing `[2]` (the tierce) |
| stiff string | **NONE move** | period **UNDEFINED** (raises) |
| membrane | **NONE move** | period **UNDEFINED** (raises) |

**Removing a partial never changes what KIND of spectrum it is.** F1339's *"the inharmonic tierce is irreplaceable"* remains true **and is now correctly scoped**: it is a statement about a **read-out**, not about the object's identity. A bell with its tierce removed is still a tier-1 rational spectrum; it just repeats sooner.

> **New rule the `(frame, lane)` contract did not have: an ABLATION INHERITS THE FRAME-DEPENDENCE OF WHATEVER IT ABLATES.**
> Ablate a **read** → you learn about the frame. Ablate an **invariant** → you learn about the object. Both are useful; conflating them is how a frame artifact gets published as a property.

## 3 — continuous substrate, discrete invariant `[DEMONSTRABLE]`

```
  B = 1/10          inharmonic  rank 0/4  degrees (2,2,2,2)
  B = 1/100         inharmonic  rank 0/4  degrees (2,2,2,2)
  B = 1/1000        inharmonic  rank 0/4  degrees (2,2,2,2)
  B = 1/10^6        inharmonic  rank 0/4  degrees (2,2,2,2)
  B = 1/10^12       inharmonic  rank 0/4  degrees (2,2,2,2)
  B = 0             HARMONIC    rank 4/4  degrees (1,1,1,1)
```

**A step function, not a slope.** `B = 10⁻¹²` is exactly as inharmonic as `B = 1/10`. Only `B = 0` **exactly** is in ℚ. The physical parameter is continuous; the invariant it controls is **discrete**. *"Nearly in ℚ"* is not a state the invariant can occupy.

This is the substrate/shadow split in one measurement — **the continuous knob is the substrate; the discrete verdict is what survives projection.** It also explains why a piano is *audibly* a piano and not a mistuned harp: the ear hears the continuous knob, the algebra sees only the step.

## 4 — the trap `[DEMONSTRABLE]`

The membrane ships **fixed-point ratios at a declared precision**, so every one of them is *literally* a rational number:

```
  WITH  open_partials= :  verdict=open       rank=0/9
  WITHOUT              :  verdict=harmonic   rank=9/9    <-- FALSE
```

The tier **declaration** is what makes the verdict truthful; without it the op is confidently wrong. What catches the lie downstream is not a second opinion — it is **arithmetic scale**:

```
  period_unavailable: a partial's reduced denominator
  (409159866402341709953368674274527262992) exceeds the Class-I parity surface of 2**64-1
```

**A genuine rational has a small denominator; a truncated irrational has a 39-digit one.** So *"is the denominator absurd?"* is a usable smell test when a tier tag is missing — and it is **not a substitute for the tag**, because a coarser truncation would pass it.

## 5 — what fibrates downward, and what does not

The one description spanning wire → drumhead → bell is the **invariant triple** — the tier ladder ℚ / algebraic / open. It is **substrate-blind**: it never asks how many dimensions vibrate, only **which field the ratios live in**. That is why it reads a 1-D wire and a 3-D casting on one axis, and it is the honest form of the user's *"same process on varying substrate."*

⚠ **GUARD — two ladders that both count small integers upward, and they are NOT the same ladder:**

| ladder | what it counts |
|---|---|
| **tier** 1 / 2 / 3 | **field-extension degree** of the ratios |
| **CD / Hurwitz** ℝ / ℂ / ℍ / 𝕆 | **real dimension** of an algebra |

Nothing measured here identifies them, and this finding does **not** claim tier-3 "is" the octonion rung. What *is* shared is the **contract shape** — an invariant that survives a perspective, and a read that does not. This is the same collision srmech's own `describe()["lanes"]["granularity"]["collision_note"]` warns about for `(8,4,2)` vs `BLOCK_DIMS`, and the user's *"fibrated downward"* is exactly where it would bite.

## Honest scope

- `[DEMONSTRABLE]`: §1–§4, all through shipped `srmech.music` ops on shipped attested data (Fletcher & Rossing 1998 §21.3 for the bell, §3.2 + DLMF 10.21 for the membrane).
- **Three exemplars, one profile each.** One bell tuning target, one stiffness family, one membrane truncation. This is not a survey of instruments; §1's non-monotone dimension↔tier table is three points, and three points cannot establish "no relation" in general — they are enough to refute *monotone*, which is what was claimed.
- **The membrane's `tier 3` is a DECLARATION, not a proof.** srmech ships `transcendence_claim: "NONE. Whether Bessel zeros are transcendental or algebraic-irrational is OPEN in this project."` I am relaying that, not resolving it. "Open" means unknown, not "known to be worse than algebraic."
- **§3's step function is measured over 6 values of B**, all of the form 1/10ᵏ. The discreteness follows from the closed form (`n√(1+Bn²)` is rational only when the radicand is a perfect square), so the measurement illustrates a structural fact rather than establishing it empirically.
- **§5's ladder guard is a NEGATIVE claim stated as a caution**, not a measurement. I did not test whether tier and CD dimension correlate; I am flagging that they are different *kinds* of ladder so that a future session does not fuse them by name-similarity.
- **Nothing here touches loudness, phase, damping, or the driven-dissipative question** (gh #1534). Free-vibration ratios only. A real gong's *sound* is dominated by things this axis cannot see.
- **One correction, and it is instructive.** My first `invariant()` was `(verdict, rational_rank, field_degrees)` — which carries **cardinality**, so dropping any partial moved it trivially (rank 5/5 → 4/4; a 5-tuple → a 4-tuple) and every substrate reported "all partials matter." I had built a **size-dependent quantity, called it an invariant, and ablated it**, guaranteeing a meaningless result. Size-normalising to `(verdict, is-full-rank, which degrees OCCUR)` produced the real answer — flat on all three. The failure mode is worth naming: *an invariant that is not invariant under the operation you are about to apply will always tell you that operation matters.*

Composes **F1339** (the bell generator — *§2 rescopes its headline from the object to the read*), **F1338** (the `(frame, lane)` contract — *§2 adds the ablation rule to it*), **F1337** (index/sign lane), tasks **#243 / #258**, gh **#1534** (driven-dissipative, untouched).
