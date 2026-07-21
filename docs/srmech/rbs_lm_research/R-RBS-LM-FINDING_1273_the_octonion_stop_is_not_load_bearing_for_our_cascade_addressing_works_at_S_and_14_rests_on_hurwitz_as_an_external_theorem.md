# F1273 — the 𝕊-boundary probe (queued by F1270): **the 𝕆 stop is NOT load-bearing for our cascade.** Addressing works at 𝕊 — **120/120 exact write→navigate→read round-trip** at the rung where the algebra is "broken" — so **no operation of ours needs the division property 𝕊 loses**, and the 14 = 1+3+7+3 boundary rests on **Hurwitz as an EXTERNAL theorem**, not on our own machinery. Two failures were also being conflated under "the algebra breaks": **losing the norm is COMMON (57 % of generic pairs at 𝕊); losing invertibility is RARE (0/180 — it needs a special basis alignment).** Measured on our own multiplication table, exact rationals, both controls run.

**The question, stated so it could fail:** every number in F1270 — 14 total, 11 imaginary (1+3+7), 3 reals (B/H/N) — depends on the Cayley–Dickson ladder stopping at 𝕆. Admit 𝕊(16) and it is 30 / 26 / 4. So the partition **is** the boundary. The honest question is *not* "does Hurwitz hold" (it does; it is a theorem) but **"does anything we ACTUALLY DO depend on the property 𝕊 loses?"** If not, stopping at 𝕆 is us liking where the numbers land — the exact failure mode that killed seven fitted results across F1264–F1271.

## (A) The loss ladder — measured on our own `cascade.cd_mult`, not cited
Violation rate over 60 derived trials × 3 declared integer rules. Exact rationals, so "is it zero" is **exact**, not a tolerance.

| rung | commut | assoc | alternat | norm-mult |
|---|---|---|---|---|
| 1 ℝ | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 ℂ | 0.000 | 0.000 | 0.000 | 0.000 |
| 4 ℍ | **0.978** | 0.000 | 0.000 | 0.000 |
| 8 𝕆 | 0.978 | **0.956** | 0.000 | 0.000 |
| 16 𝕊 | 0.978 | 0.978 | **0.978** | **0.567** |
| 32 𝕋 | 0.978 | 0.978 | 0.978 | 0.950 |

Commutativity dies at 4, associativity at 8, **alternativity and norm-multiplicativity BOTH at 16.**

**The rungs are not uniform.** ℍ loses one property, 𝕆 loses one, **𝕊 loses two at once.** The boundary has a different *character* from the intermediate steps — it is not "one more rung of the same ladder."

## (B) Two different failures, previously conflated
| at 𝕊 (dim 16) | rate | reading |
|---|---|---|
| norm-multiplicativity `N(xy) = N(x)N(y)` fails | **102/180 (57 %)** | **COMMON** — most generic pairs |
| generic `x·y = 0` (zero divisor) | **0/180 (0 %)** | **RARE** — needs special basis alignment |

The structured witness srmech exhibits from its own table: `x = e1 + e10`, `y = e4 − e15`, both with `|·|² = 2 ≠ 0`, and `x·y = 0` exactly.

**"The algebra breaks at 16" is doing two jobs and they have opposite magnitudes.** Losing the *norm* is the common case; losing *invertibility* is the rare, structured one. Any argument that leans on "𝕊 is broken" has to say which. **This distinction is what makes the addressing stance viable** — you cannot route around a 57 % failure, but you absolutely can route around a measure-zero one.

## (C) The load-bearing test — does OUR addressing break at 𝕊?
**CONTROL A — does the gate discriminate?** A stuck-`True` `is_navigable` would void every number here.
- known zero divisor `e1 + e10` → navigable **False**
- known zero divisor `e4 − e15` → navigable **False**
- zero vector → navigable **False**
- **The gate rejects exactly the broken directions.** It is measuring, not rubber-stamping.

**The measurements:**
- generic derived directions navigable: **180/180 (100 %)**
- end-to-end **write → navigate → read back**, content recovered at the `navmap`-predicted slot with the correct **name AND Class-C sign**:

| D | round-trip |
|---|---|
| 256 | 116/120 (96.7 %) |
| 1024 | **120/120 (100 %)** |
| 4096 | **120/120 (100 %)** |
| 16384 | **120/120 (100 %)** |

**CONTROL B caught a would-be false result.** At D=256 the round-trip was 96.7 %, and a 3.3 % shortfall at 𝕊 is exactly the shape of "look, the sedenion boundary bites." It does not: it is **register capacity** (8 keys in a small bundle), and it vanishes at D≥1024. **Without the D-sweep I would have reported my own dimension choice as a property of 𝕊** — the same class of error as the length confound in the gauge arc.

## (D) What the partition becomes if 𝕊 is admitted (arithmetic only)
| ladder | total | imaginary | reals |
|---|---|---|---|
| ℂ(2)+ℍ(4)+𝕆(8) **[ours]** | **14** | **11 = 1+3+7** | **3** |
| + 𝕊(16) | 30 | 26 = 1+3+7+15 | 4 |
| + 𝕋(32) | 62 | 57 = 1+3+7+15+31 | 5 |

## Verdict
**Addressing at 𝕊 works completely.** Content written, navigated and read back exactly — name and sign — at the rung where the algebra is supposedly broken. **No operation exercised here needs the division property.**

Two consequences, and the second is the uncomfortable one:

1. **It CONFIRMS `[[feedback_sedenion_no_division_is_the_addressing_feature]]`** — and shows *why*: non-division is not an obstacle **because addressing never divides**, and the navigability gate **routes around** the measure-zero broken set rather than being stopped by it. Navigate, don't divide, is a working strategy and now a measured one.

2. **The 14 boundary does NOT rest on our cascade needing division.** It rests on **Hurwitz as an external theorem**. That is a legitimate place to stand — Hurwitz is true and the stop is real — **but it must be SAID, not implied by the numbers landing on 14.** We do not get to point at our own machinery as the reason for the boundary, because our machinery demonstrably keeps working past it.

**This is the third structural result that HELD** (F1270 B/H/N as DC anchors; F1272 the perpendicular axes; F1273 here), against seven fitted results that dissolved under proper measurement (F1264–F1271). The pattern is now hard to ignore: **derivations survive, fits do not** — and the two controls in (C) are the reason this one is a derivation rather than an eighth casualty.

## Next
(a) The honest follow-up is **not** "is 14 right" but **what DOES our cascade need?** — enumerate which A–N operations touch a normed/division property at all. On this evidence the answer may be *none*, which would make the 1:3:7:3 reading a statement about the **substrate we are modelling**, not about our tooling's limits. (b) If addressing works at 𝕊, the open question is whether it keeps working at 𝕋(32) where norm-multiplicativity fails 95 % — that is where "gradient, not wall" becomes testable.

Composes **F1270** (which queued this — *→ extended by F1273*), **F1272** (the perpendicular axes), **F1271** (the fitted results that did not survive), `[[feedback_sedenion_no_division_is_the_addressing_feature]]` (*confirmed, with the mechanism*), `[[feedback_three_things_called_random_derived_drawn_stochastic]]` (elements DERIVED by three declared rules; no RNG), `[[feedback_read_independent_structure_check_first]]`, DUALITY.md / TRIALITY.md, #231/PKG-3.
