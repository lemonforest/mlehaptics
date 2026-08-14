# F1339 — **the generator is a Class-I `lcm` over denominators, the INHARMONIC partial is the irreplaceable one, and the period is a per-frame READ.** The tuned bell ships as attested TIER-1 data and already *is* the user's structure: **hum `1/2` is a subharmonic**, **tierce `6/5` is inharmonic** in the acoustician's sense, and the whole spectrum is **commensurable with period 10 = 2 × 5**. Neither shape alone has that period. But the symmetric reading is **wrong, and the ablation is the result**: dropping the hum changes **nothing** (the quint `3/2` also carries a 2), while dropping the tierce **collapses the period 10 → 2**. **Exactly one partial of five is load-bearing, and it is the inharmonic one.** Under the F1338 `(frame, lane)` contract the bell then behaves exactly as predicted in a *second substrate*: re-referencing to each of its 5 partials leaves `verdict` / `rational_rank` / `field_degrees` **invariant** while the period reads **5, 10, 12, 15, 20** — five observers of one bell, five repeat lengths, all correct.

**User (2026-08-14):** *"how a thing like a subharmonic and inharmonic are what go into a generator and harmonic comes out. the resonance is between the two dissimilar shapes is what this generator must create. let's try the new (frame, lane) way test too."*

srmech 0.9.0rc432, `srmech.music.*`. Exact-ℚ / exact-algebraic. **No `best_rational` on a spectrum** — the shipped explanation warns it does not *approximate* an inharmonic spectrum, it **CONVERTS** it into a harmonic one. No `abs()`, no numpy, no RNG. Generating code: `R-RBS-LM-GENERATOR_*.py` (exit 0).

## 1 — two senses of one word, separated by the shipped op `[DEMONSTRABLE]`

| | verdict | `integer_series` | `rational_rank` | `field_degrees` | period |
|---|---|---|---|---|---|
| **bell** (TIER 1) | `harmonic` | **False** | 5 / 5 | `(1,1,1,1,1)` | **10** |
| **stiff string** (TIER 2) | `inharmonic` | False | **0** / 6 | `(2,2,2,2,2)` | — |

**A tuned bell is `'harmonic'` and NOT an integer series.** `commensurability_verdict` answers *commensurable?*; `integer_series` answers the acoustician's *are the ratios 1,2,3…?*. Conflating them is the whole confusion in the word "harmonic."

**The lane reading is not an analogy here — it is what the op computes.** The invariant is **rational rank**: ℚ-membership inside ℚ[x]/(m), field-theoretic and **basis-free**. Basis-free and order-blind is the **index lane**. A `field_degree > 1` is the algebraic extension ℚ cannot see — the **sign/twist lane**. The bell is pure index lane (rank 5, all degrees 1) so a period exists; the stiff string is pure extension (rank 0, all degrees 2) so no period can exist.

## 2 — the generator `[DEMONSTRABLE]`

`period = lcm(reduced denominators)` — a Class-I `lcm`, nothing more exotic.

| part | ratios | period alone |
|---|---|---|
| SUBHARMONIC | `1/2` | **2** |
| INHARMONIC | `6/5`, `3/2` | **10** |
| integer | `1`, `2` | **1** — inert |
| **all five** | | **10** |

`period(whole) == lcm(period(sub), period(inh))` ✓. **The integer partials — the ones that look most "harmonic" — generate nothing**, because an integer ratio has denominator 1 and `lcm(1, x) = x`.

### The ablation, which corrects the symmetric reading `[DEMONSTRABLE — the result]`

```
  without hum       -> period 10   no change
  without prime     -> period 10   no change
  without tierce    -> period  2   PERIOD COLLAPSES
  without quint     -> period 10   no change
  without nominal   -> period 10   no change
```

> **Exactly one of five partials is load-bearing, and it is the INHARMONIC tierce.**

The prime **2 is supplied redundantly** — by the subharmonic hum `1/2` *and* by the quint `3/2` — so removing the hum costs nothing. The prime **5 has a single source**: the tierce. Remove it and the period falls back to what the subharmonic already gave alone.

**So the generator is not a balanced `sub ⊗ inh` pair.** It is: *the inharmonic partial is irreplaceable, and the subharmonic supplies a prime the rest of the spectrum was going to supply anyway.* What the bell needs, it needs **from the tierce** — the partial a naïve harmonic reading would call the defect.

## 3 — the `(frame, lane)` test, in a second substrate `[DEMONSTRABLE]`

A **frame** here = which partial you call `f₀`. Re-reference all five ways:

| f₀ | ratios | verdict | rank | degrees | **PERIOD** |
|---|---|---|---|---|---|
| hum | `1, 2, 12/5, 3, 4` | harmonic | 5 | all 1 | **5** |
| prime | `1/2, 1, 6/5, 3/2, 2` | harmonic | 5 | all 1 | **10** |
| tierce | `5/12, 5/6, 1, 5/4, 5/3` | harmonic | 5 | all 1 | **12** |
| quint | `1/3, 2/3, 4/5, 1, 4/3` | harmonic | 5 | all 1 | **15** |
| nominal | `1/4, 1/2, 3/5, 3/4, 1` | harmonic | 5 | all 1 | **20** |

```
  VERDICT frame-INVARIANT                     : 1 distinct value
  rational_rank (INDEX lane) frame-INVARIANT  : 1
  field_degrees (SIGN lane)  frame-INVARIANT  : 1
  PERIOD frame-DEPENDENT                      : {5, 10, 12, 15, 20}
```

**This is F1338's contract holding in a substrate it was not derived from.** The lane data is the invariant — a cross-frame claim may be made of it. The period is the per-frame read-out. *"Is this thing harmonic?"* is frame-free; *"what is its period?"* is not, and two observers of the same bell will disagree and both be right.

## 4 — the generator's precondition, which is the honest half `[DEMONSTRABLE]`

Couple a rational subharmonic to a **degree-2 algebraic** partner:

```
  verdict=inharmonic  rank=2/4  degrees=(1,1,2,2)  incommensurable=(2,3)
  common_period REFUSED: "spectrum is INHARMONIC - partial indices [2, 3] are provably
                          NOT in the rational span"
```
The rational members **survive in the rank** (2 of 4 still lie in ℚ) and the op **names which partials broke it**.

> **The generator works when both shapes are COMMENSURABLE-BUT-DISSIMILAR — different denominators, same field ℚ. It does NOT bridge a field extension.**

A degree-2 partner does not resonate into a period; it refuses one, and srmech **refuses with it** rather than converting. That refusal is the designed behaviour: `common_period` raises, and the raise is the feature.

## What this says about the "note"

The user's framing — *the note is just a substrate* — comes out sharper than stated. A note's identity (`harmonic` / `inharmonic`, and its rank and degrees) is **frame-free substrate**. Its period — the thing you would *hear* as the repeat, the thing an instrument's body actually does — is a **perspective read**. And the partial that generates the richest period is the one furthest from integer: **inharmonicity is not the defect in the note, it is the generator of the note's structure.**

## Honest scope

- `[DEMONSTRABLE]`: §1–§4, all through shipped `srmech.music` ops on shipped attested TIER-1 data (Fletcher & Rossing, *The Physics of Musical Instruments*, 2nd ed., Springer 1998, §21.3 — the citation srmech ships with `bell_partials`).
- **ONE bell profile, five partials.** This is `fletcher_rossing_1998_sec_21_3`, the founder's tuning **TARGET**. It is not a survey of real bells, and a real casting deviates. The ablation result (tierce is load-bearing) is a fact about *this* profile — it would change under a different tuning where two partials share the prime 5.
- **§2's `lcm` is not a discovery**, it is what `common_period` documents itself to compute. What is measured here is the *ablation* — which partial the lcm actually needs — and that was not obvious.
- **§3's frames are re-references within ℚ**, which is why the verdict cannot move: dividing rationals by a rational stays rational. So the verdict-invariance is **structural, not surprising**; the informative half is the **period spread {5,10,12,15,20}**, which is real and is the thing a naïve reading would have called "the" period.
- **The tie to the 28 octonion frames of F1338 is an ANALOGY, not an identity.** Both are "a perspective is a choice, invariants survive, reads do not." This finding does **not** claim the 5 bell frames are octonion frames, or that acoustic re-referencing is a Fano-line change. Same *shape* of contract, different objects — `[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`.
- **Nothing about loudness, phase, or driven-dissipative behaviour is measured here** — the open items on gh #1534 and F1332 §4 are untouched. This is a spectrum-ratio result only.
- **One correction.** I first asserted `gcd(period(sub), period(inh)) == 1` ("the two shapes supply disjoint primes"). It is **False** — `gcd(2,10) = 2` — and it contradicted prose I had written two lines beneath it. Replaced with the ablation, which is the measurement that assertion was reaching for and which overturned the symmetric reading. *(Also mine: I guessed `.den` for the ℚ accessor; it is `.denominator`.)*

Composes **F1338** (the `(frame, lane)` contract — *§3 is its first out-of-domain confirmation*), **F1337** (index lane / sign lane — *§1 gives the acoustic realization: rational rank vs field degree*), **F1332 §4** (the resonator reading closed structurally), gh **#1534** (driven-dissipative, still open), tasks **#243 / #258** (the asymmetric-resonator subharmonic probe — *this is the first measurement that arc asked for*).
