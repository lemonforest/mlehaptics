# F1350 — **the operator exists, it was shipped all along, and it is NOT an m×n transform.** F1349 recorded *"no operator has been exhibited that performs the change of basis"* from `2:4:8` to `1+1:1+3:1+7`. That is now **superseded**: the operator is **`cd_conjugate`**, the ladder's own **Class-K involution**, whose eigensplit is **`(1, n−1)` at every rung — (1,1), (1,3), (1,7), (1,15)**, fixed + anti-fixed covering the whole basis. So `2:4:8` and `1+1:1+3:1+7` are **the same rung list read before and after the conjugation eigensplit** — one object, two reads, no new information. The "m×n transform" intuition names a **different law**: the tensor product (Furey's ℝ⊗ℂ⊗ℍ⊗𝕆), and it is measurably not ours — **ℂ⊗ℍ is dim 8 like 𝕆 but associates 512/512 where 𝕆 fails 168/512, and it HAS zero divisors where 𝕆 has none.** The two laws trade away **opposite** Hurwitz properties at dimension 8.

**User (2026-08-15):** *"when a part is falsified, look at the part that isn't to understand how to reshape our words into what is actually true."*

srmech 0.9.0rc434. Built by a fable subagent; **every headline re-verified by me** before landing. Exact integers / exact ℚ. Generating code: `R-RBS-LM-TENSORVSCD_ladder_vs_tensor_product.py` (40 checks, exit 0).

## 1 — the operator, exhibited `[DEMONSTRABLE — re-verified independently]`

```
  dim  2   FIXED 1   ANTI-FIXED  1    -> (1,  1)   covers the whole basis
  dim  4   FIXED 1   ANTI-FIXED  3    -> (1,  3)   covers the whole basis
  dim  8   FIXED 1   ANTI-FIXED  7    -> (1,  7)   covers the whole basis
  dim 16   FIXED 1   ANTI-FIXED 15    -> (1, 15)   covers the whole basis
```

`cd_conjugate` fixes exactly the real anchor and negates exactly the imaginaries — so its eigenspaces **are** `1 + (n−1)`. It is an anti-automorphism on every basis pair (4/4, 16/16, 64/64, 256/256).

> **The change from even-count to odd-anchored is an EIGENSPACE SPLIT, not a dimension-composing product.** We were looking for a transform that *builds* something; the operator we needed *reads* what was already there.

That is why F1349 could not find it: it was searching the wrong **kind** of operation.

## 2 — the m×n reading names a different law, and the law is measurably not ours `[DEMONSTRABLE]`

`dim(ℂ⊗ℍ) = 2 × 4 = 8 = dim(𝕆)`. **Not isomorphic**, on two independent grounds:

| | ℂ⊗ℍ | 𝕆 |
|---|---|---|
| ordered basis triples that **associate** | **512 / 512** | **344 / 512** (168 fail) |
| zero divisors | **present** — `u = 1⊗1 + i⊗i`, `v = 1⊗1 − i⊗i`, `u·v = v·u = 0` | **none** (`cd_zero_divisor_witness(8) → None`) |
| `Der` dimension | **6** | **14** (g₂) |

**The mechanism, measured:** `(i⊗i)² = +1` — a **non-central square root of 1**. On the ladder *every* imaginary unit squares to −1, so `1 − x² = 2` and never vanishes. The tensor product manufactures the zero divisor at its **first** application; the ladder does not reach one until 𝕊.

> **The two laws sacrifice OPPOSITE Hurwitz properties at dimension 8.** ⊗ keeps associativity and loses division. CD keeps division and loses associativity. And the ladder *grows* exceptional symmetry (Der = 14 = g₂) where an associative tensor product only ever has what its own commutators generate (Der = 6).

## 3 — and the tensor product CANNOT produce odd-anchored counts `[DEMONSTRABLE + one inferred step]`

The tensor product's natural involution is `conj ⊗ conj`, and its eigensplit **multiplies**:

```
  (p, q) (x) (p', q')  ->  (p p' + q q',  p q' + q p')
  C (x) H  ->  (4, 4)          C (x) O  ->  (8, 8)        EVEN at every application
```

**Once both factors have `q ≥ 1`, `(p p' + q q', p q' + q p')` can never be `(1, n−1)`.** So the m×n law is not merely a *different* route to the odd-anchored split — it is **structurally barred from it**. *(The census is measured; the "never" is a one-line inference from the product law, stated as such.)*

## 4 — the reshaped claim

**Falsified and retired:** *fibration is an m×n transform taking 2:4:8 → 1+1:1+3:1+7.*

**Un-falsified and now exhibited:** *`2:4:8` and `1+1:1+3:1+7` both belong to the **ladder**. They are one rung list read before and after the eigensplit of the ladder's intrinsic conjugation — `cd_conjugate`, Class K, shipped.*

And the two arithmetics were being conflated:

| operation | on the rung list | gives |
|---|---|---|
| **nesting / additive** (ours) | `2 + 4 + 8` | **14** — `BLOCK_DIMS`, the A–N count |
| **tensoring / multiplicative** (Furey's) | `2 × 4 × 8` | **64** — the ℂ⊗𝕆 dimension in the verified abstract |

**Both are real operations on the same list.** The falsified sentence used one word ("transform") for both.

## Honest scope

- `[DEMONSTRABLE]`: §1's eigensplit, §2's associativity censuses and the zero-divisor witness — **all three re-verified by me directly**, not taken from the subagent's report. §3's eigencounts and §2's Der figures are the subagent's, run in the same script (40 checks, exit 0), and I did **not** independently re-derive the Der = 6 pinch.
- **`Der(ℂ⊗ℍ) = 6` is a two-sided argument, not a single measurement**: GF(p) nullity 6 at two primes gives ≤ 6, and 6 explicit independent inner derivations give ≥ 6. The instrument was cross-checked against the shipped `g2_subalgebra` answer (14) before being trusted. Sound, but it is an assembled result.
- **INFERRED, not run**: that basis-triple associativity decides algebra associativity (bilinearity); that rank mod p ≤ rank over ℚ; that the even-split law forbids `(1, n−1)`.
- **NOT decided: whether ℂ⊗𝕆 ≅ 𝕊.** Both are dim 16, non-associative, with zero divisors. The (8,8)-vs-(1,15) split and the centre counts are *presentation-level* reads, not an isomorphism decision. **Do not report this as settled.**
- **Nothing here touches Furey's physics claims** — only the composition law, and only as verified in the abstract (attestation: `R-RBS-LM-ATTEST_furey_1611_09182.md`, arXiv:1611.09182v1). The body is still unread.
- **What would falsify the tensor-product reading itself:** exhibit an m×n law (`dim A∘B = dim A × dim B`) whose involution is *not* the product of the factors' involutions and which lands on the odd-anchored split. The measurement closes the **product-involution** door specifically, not every conceivable door. And the per-rung `(1, n−1)` claim is falsifiable at each new rung by the same two-line check — dim 32 is one call away.

**Supersedes F1349's §4 "NOT ESTABLISHED" first bullet.** The correspondence is now a mechanism; it is simply a different mechanism than the one that was sought. Composes **F1349**, **F1326** (3+1+3 — *the "+1" is this fixed space*), **F1338**, **F1337**, and the Furey attestation.
