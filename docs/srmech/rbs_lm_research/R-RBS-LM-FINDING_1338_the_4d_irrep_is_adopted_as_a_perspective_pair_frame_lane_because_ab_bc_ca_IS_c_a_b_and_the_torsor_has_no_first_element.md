# F1338 — **the 4D irrep is ADOPTED, as a `(frame, lane)` PERSPECTIVE PAIR and never as the carrier.** Five of the user's claims turned into measurements through shipped rc432 ops, all passing. The load-bearing one: **`ab:bc:ca || c:a:b` is an IDENTITY, not an analogy** — on all **7/7** Fano lines the product of a PAIR lands exactly on the complementary SINGLE, up to a Class-K sign (`ab→c`, `bc→a`, `ca→b`; 5 lines `+`, and lines `167`/`356` `−`, matching the shipped φ=−1 rows). So **naming any two names the third**, and the ternary object is structurally never "one thing at a time." The perspective claim is equally sharp: **28 frames give 28 DISTINCT reads of ONE octonion, with ONE invariant norm** — so the 4-cube is what a perspective *hands* you, never what the thing *is*. And the torsor makes "project out of the relational way" exact: the label **SET** is basepoint-invariant (always the whole group), the **ASSIGNMENT** is basepoint-dependent (8 basepoints → 8 distinct labelings), and **every basepoint labels itself `0`**.

**User (2026-08-14):** *"adopt the 4D irrep now that the lane surface answers it, but only as a perspective. what we cannot deny is that irreps vary per perspective … we never leave a tower rung, we nest it, and S rung is only ever about holding two instances of an O, and perhaps this is how a triality generator works, never one thing at a time until we project out of the relational torsor way of describing a thing."*

srmech 0.9.0rc432. Exact-ℚ throughout. No `abs()` — sign is a Class-K pin (equality against the negation), magnitude is `cd_norm_sq`. No numpy, no RNG. Generating code: `R-RBS-LM-PERSPECTIVE4D_*.py` (exit 0).

## 1 — `ab:bc:ca || c:a:b` is an identity `[DEMONSTRABLE]`

On each Fano line `{a,b,c}`, is the pair-product the remaining single?

| line | `ab→c` | `bc→a` | `ca→b` |
|---|---|---|---|
| `(1,2,3)` `(1,4,5)` `(2,4,6)` `(2,5,7)` `(3,4,7)` | **+** | **+** | **+** |
| `(1,6,7)` `(3,5,6)` | **−** | **−** | **−** |

```
  every Fano line: ab:bc:ca lands exactly on c:a:b (Class-K sign)  : 7 / 7
  phi is Z/3-cyclic and NONZERO on every line                     : 7 / 7
  transposition phi(b,a,c) == -phi(a,b,c)  [Class-K sign only]    : 7 / 7
```
The two negative lines are exactly the notebook's φ = −1 rows (`167`, `356`) — an independent cross-check that this measurement and §3.46.11 are reading the same object.

> **`ab` is not a pair that POINTS AT `c` — it IS `c`, up to orientation.**

That is the user's `||` as an equals sign. The sign is the *only* content the two readings differ by, and a sign is Class-K. **This is what makes "never one thing at a time" structural rather than stylistic:** a Fano triple has 3 slots and 2 degrees of freedom, so you cannot hold one without implying the third.

## 2 — irreps vary per perspective `[DEMONSTRABLE]`

A frame is the **`(Fano line, splitting unit)` PAIR** — 7 lines × 4 units = **28** (rc421).

```
  well-posed frames enumerated                          : 28
  DISTINCT reads of the SAME octonion                   : 28   <- the perspective really moves it
  the Class-N squared norm across all 28 perspectives   : 1 value  (norm_sq = 88)
```
**28 perspectives, 28 different reads, one invariant.** Adopting the 4-cube as *the* carrier would be adopting frame 1 of 28 and calling it the object.

## 3 — we never leave a rung, we nest it `[DEMONSTRABLE]`

```
  g2                        14        der_sedenion              14
  spin9                     36        spin9_cap_der_sedenion    14
  individual spin(9) generators that are sedenion derivations :  0
  all 14 g2 lifts ARE exact derivations (Leibniz residual 0.0) : True
```
Climbing ℝ→ℂ→ℍ→𝕆 **grew** the symmetry; climbing 𝕆→𝕊 does **not**. And srmech's own tier text for the op says it outright:

> *"dim Δ₉ = 16 = dim_ℝ 𝕊 (**both are 𝕆 ⊕ 𝕆**) — a shared carrier, NOT a Spin(9) action by sedenion automorphisms"*

## 4 — the 𝕊 rung holds two instances of an 𝕆 `[DEMONSTRABLE]`

```
  lower half (e0..e7) closes on itself -- it IS an O subalgebra   : 49 / 49
  upper x upper lands back in the LOWER half (a coset, never a subalgebra) : 64 / 64
```
𝕊 is not 16 new directions. It is **one 𝕆 that closes, plus one 𝕆-shaped coset that does not** — the second copy has no identity of its own. Exactly the user's claim, and it is the same shape as §5 one rung down.

## 5 — the relational torsor, and what "project" costs `[DEMONSTRABLE — the sharpest result]`

At the 𝕆 rung, ℍ acts on the seam coset `T = {±e₄..±e₇}`:

```
  elements of T that act as an identity on T                 : 0
  every ordered (t1,t2) has EXACTLY ONE g in H carrying t1->t2 : 64 / 64
  the label SET is the SAME for every basepoint               : 1   (always all of H)
  the ASSIGNMENT differs for every basepoint                  : 8 / 8 distinct
```

| basepoint | assignment, in T's order |
|---|---|
| `e4` | `(0, 9, 10, 11, 8, 1, 2, 3)` |
| `e5` | `(1, 0, 3, 10, 9, 8, 11, 2)` |
| `e6` | `(2, 11, 0, 1, 10, 3, 8, 9)` |
| `e7` | `(3, 2, 9, 0, 11, 10, 1, 8)` |

**Read the diagonal: every basepoint labels itself `0`.** The identity is not a property of `T` — it is manufactured by the choice, and every element is equally entitled to it.

The two facts must be kept apart, because they say opposite things:
- the **group** is intrinsic (the label set is always all of `H` — a perspective cannot change *what labels exist*);
- the **labelling** is a choice (the matching is basepoint-dependent — a perspective decides *which thing gets which*).

> **"Never one thing at a time until we project" = the relation is primary; the labelled thing is what falls out once a perspective is fixed.**

## 6 — THE ADOPTION, as a contract

A carrier that adopts the 4D irrep **as a perspective** declares a **pair**, not a basis:

```
    (frame, lane)     frame in 1..28   which (Fano line, splitting unit)
                      lane  in {index, sign, both}   which half it reads
```

Under that contract:

1. **the 4-cube is a READ-OUT, produced per frame — never the storage.** §2 is the reason: storing one frame's coordinates stores one of 28 equally-valid answers.
2. **only invariants may carry a cross-perspective claim.** `norm_sq` and φ survive a frame change (§2); a base does not. Any claim of the form "this strand *is* X" must be phrased in an invariant or it is a claim about the frame.
3. **the sign lane is where every ceiling lives; the index lane is unbounded** (F1337). A carrier storing only the index lane has stored the unbounded *shadow* — which is cheap and useful, and must be labelled as such.
4. **naming any two of a triple names the third** (§1). The third is not extra storage; it is implied. A carrier that stores all three of a Fano triple has stored a redundancy, not a fact.
5. **an address is basepoint-relative** (§5). Two carriers can disagree on every label and still be the same object; agreement must be tested on the invariant, never on the labels.

## Honest scope

- `[DEMONSTRABLE]`: §1–§5, exhaustive over all 7 Fano lines, all 28 well-posed frames, all 7×7 and 8×8 half-products at 𝕊, and all 64 ordered torsor pairs. All through shipped ops.
- **§6 is a CONTRACT, not a measurement.** Nothing is built. No strand has been encoded under it, no carrier changed. It is a design statement derived from §1–§5 and F1337, and it should be read as the thing to falsify next, not as a result.
- **§3 relays a `PARTIAL` verdict.** `sedenion_holonomy_conjecture()` returns `verdict: PARTIAL`; the 14 is measured and the "no new symmetry" reading is upstream's DERIVED tier, not a proof that `Aut(𝕊) = G₂`. `aut_sedenion_approx` is named *approx* in the payload and I am not treating it as exact.
- **§1's identity is about BASIS units on Fano lines**, not arbitrary octonions. `ab = ±c` holds for the seven triples; it does not say a general product of two octonions is a basis unit.
- **The triality tie stays FORM-only.** §3.46.11 flags "a→b→c cycling = which-pair-is-nested-first" as an order-3 **analogy**, not a measured identity — `triality_automorphism` is `τ³=I` on 𝔰𝔬(8), not a permutation of an octonion triple. §1 measures φ's ℤ/3 cycle and the pair↔single identity; it does **not** promote the triality tie, and the user's *"perhaps this is how a triality generator works"* remains **[SPECULATIVE]**.
- **One correction, and it is on-theme.** My first §5(d) asserted "different basepoints give different labelings" and measured **False** — because I `sorted()` the labels, and sorting is an order-blind (**index-lane**) read that destroys precisely the datum that varies. Applying an abelian read to a question about order is the exact failure mode F1337 warns about, committed while writing up F1337. The corrected measurement splits it into the invariant SET and the varying ASSIGNMENT, which is a stronger statement than the one I set out to make. *(Two earlier bugs were mine too and are not results: a guessed dict key, and using 4 bare indices where the torsor takes 8 SIGNED bytes — the arithmetic was right, the operand set was half the object.)*

Composes **F1337** (the lane surface; index unbounded / sign ceiling-bearing — *supplies the second half of the pair*), **F1336** (the cube is a shadow), **F1326** (3+1+3 and the borrowed anchor — *§5's "no first element" is that anchor's torsor form*), **F1328** (8:4:2 widths), **F1322** (`ker(π) = {±1}`), srmech notebook **§3.46.11** (φ IS the `ab:bc:ca` ternary object; `stab(φ) = G₂`; 168 four ways) and **§3.43** (Der stays g₂ above 𝕆), gh **#1535** (the parked ask, now answered and adopted), `[[user_stance_observation_is_a_shadow_irrep_under_perspective_shift]]`.
