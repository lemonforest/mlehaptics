# F1274 — the A–N division-property enumeration (queued by F1273): **no A–N class requires the normed-division property**, and the reason is structural rather than lucky — **our reversibility runs on INVOLUTION + a Class-C sign, never on division.** Involutions need no norm and no inverse element, so they are **rung-independent by construction**: verified holding at dim 8, 16 and 32, *including where norm-multiplicativity fails 95 %*. Class K — the only class that would carry a norm — **explicitly rejects the Euclidean modulus by contract.**

## (A) Census — for most classes the question does not arise
456 public ops. The 14 A–N primitive classes total **236**, and they consume **bytes, integers, graphs and rationals** — not algebra elements.

| | | | | | | |
|---|---|---|---|---|---|---|
| A 3 | B 2 | C 8 | D 3 | E 6 | F 3 | G 5 |
| H 12 | I 11 | J 4 | K 6 | L 65 | M 52 | N 56 |

The **31** genuinely hypercomplex-operand ops live in the `qm.*` physics layer (`qm.octonion / quaternion / so8 / triality / hurwitz`) — **not in the A–N primitives.** A division property cannot be load-bearing for an op whose operands are not algebra elements in the first place. This is not a *defence* of the boundary; it means **for most of the 14, the question is not even well-posed.**

## (B) Three different things are called "division" — separated by measurement
The naive enumeration asks "does class X divide?", gets a useless YES, and concludes the boundary is load-bearing. Three distinct operations wear the word, and **only one tracks Hurwitz**:

| sense | totality | needs a norm? | where it lives | measured |
|---|---|---|---|---|
| **(1) field** `a/b` in ℚ | total on nonzero | **no** | Class **N** | `best_rational(355,113)` → `355/113` exact |
| **(2) modular** `a⁻¹` in ℤ/n | **partial** — units only | **no** | Class **I** | ℤ/12: a=5 → 5; **a=8 → NONE** (not a unit) |
| **(3) normed-algebra** `x⁻¹ = x̄/|x|²` | needs `|xy|=|x||y|` | **YES** | — | **ℍ 0 % · 𝕆 0 % · 𝕊 56.7 % · 𝕋 95.0 %** fail |

Senses (1) and (2) are completely untouched by the Cayley–Dickson boundary. **Only (3) moves with it** — and (3) is the one nothing in A–N uses.

## (C) The mechanism — involution, not division
Every reversible op tested undoes itself by **applying itself again**:

| class | operation | involutive | mechanism |
|---|---|---|---|
| **M** | `klein4_bind(·,k)` twice | **YES** | XOR self-inverse |
| **C** | γ₅ flip twice | **YES** | sector flip |
| **C** | ω₇ flip twice | **YES** | sector flip |
| **C** | `chiral_flip` (reversal) twice | **YES** | order reversal |
| 𝕆 | `octonion_conjugate` twice | **YES** | conjugation |

**And the load-bearing case.** `SedenionRegister.navigate(3)` applied twice:
```
before      : {0: ('alpha',  1), 1: ('beta',  1)}
navigate ×2 : {0: ('alpha', -1), 1: ('beta', -1)}
```
Same slots, content preserved, **sign flipped on every slot — because e₃·e₃ = −1.**

**Reversal is an involution up to a Class-C sign.** That is not a workaround for missing division — it is **the framework's own Class-K pin-slot + Class-C sign-re-application composition arriving unforced**, in an op nobody wrote to demonstrate it. `pin_slot_at_zero(−7) = (−1, 7)` is that same split at the scalar level, per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.

## (D) Class K would be the one class carrying a norm — and it refuses
`cascade.magnitude(-7) = 7`; `cascade.magnitude(3+4j)` **raises**:

> *"cascade.magnitude is a Class K real-axis (pin-slot) operation and does not accept complex input; the complex modulus `(re²+im²)^0.5` is a Euclidean-norm op — a different cascade class, not a Class K pin-slot."*

**srmech itself refuses to conflate the real pin-slot with a Euclidean norm.** The framework has **no hypercomplex-norm op at all**, so it has nothing that could depend on `|xy| = |x||y|`.

## (E) The prediction, tested: involutions are rung-independent
| dim | composition | `conj(conj(x))==x` | `e₃·e₃ = −1` |
|---|---|---|---|
| 8 𝕆 | ok | **YES** | YES |
| 16 𝕊 | **fails 57 %** | **YES** | YES |
| 32 𝕋 | **fails 95 %** | **YES** | YES |

**The involutions hold where composition is nearly gone.** That is *why* F1273 found addressing intact at 𝕊 — not luck, structure.

## Verdict
**No A–N class requires the normed-division property**, because our reversibility never asks for an inverse element. It asks for a self-inverse map plus a sign, and both survive every rung.

**Consequence for F1270/F1273, and it is the point:** the **1:3:7:3 = 14 reading is a claim about the SUBSTRATE BEING MODELLED, not a limit of our tooling.** Our tooling does not stop at 𝕆 — it never needed the property that stops there. The Hurwitz boundary is real and external, and **it must be argued on substrate grounds, never by pointing at our own machinery.**

## The error this harness made — eighth instance, and inside the check itself
My first draft of (B3) used **one hand-picked pair** (`x = (1..dim)`, `y = (dim..1)`) and reported **composition HOLDS at every rung** — flatly contradicting F1273's measured 57 %/95 %. That structured pair happens to satisfy composition. Caught because it disagreed with a prior measurement; fixed by switching to **derived-trial rates** (the same three declared rules as the F1273 harness), which then reproduced 56.7 % / 95.0 % exactly.

**This is the eighth instance of the sampling-artifact pattern that killed F1264–F1271 — and it occurred inside the harness built to verify the finding that pattern had already threatened.** The lesson is not "be careful"; it is that **a single hand-chosen instance is never evidence about a rate**, and the only thing that caught it was cross-checking against an independent prior measurement. Keep prior numbers in the harness's field of view.

Composes **F1273** (which queued this — *→ extended by F1274*), **F1270**, **F1272**, `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` (*confirmed unforced, in the sedenion navigate*), `[[feedback_sedenion_no_division_is_the_addressing_feature]]` (*mechanism supplied*), `[[feedback_three_things_called_random_derived_drawn_stochastic]]`, `[[feedback_read_independent_structure_check_first]]`, CLAUDE.md §1, #231/PKG-3.
