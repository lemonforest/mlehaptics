# F1351 — **the thesis body states the tensor-product rule outright, and that rule DECIDES what F1350 left open: ℂ⊗𝕆 is NOT 𝕊.** Furey's ℝ⊗ℂ⊗ℍ⊗𝕆 is defined by one sentence — **the factors' imaginary units commute with each other** — printed twice in the body. That commuting `i` is exactly the hypothesis F1350's measurement rested on, and it was taken there from the general product law rather than from Furey; it is now **attested to the primary source**. Built in srmech from her stated rule, it forces `(i·e₁)² = +1` and hands you a zero divisor `(1 + i·e₁)(1 − i·e₁) = 0` in one line, **constructed, not searched**. And it separates the two dim-16 algebras on **two independent invariants**: the centre (**2 vs 1**) and the square roots of unity (**i·e₁ exists vs only ±1**). **AND: there are no scripts to convert. The thesis publishes no code at all** — verified, not assumed.

**User (2026-08-15):** *"pull the whole thesis body and attest the tensor product part. we will need to convert their scripts, if published, to use srmech imports."*

Full text extracted from the primary PDF (`pdftotext -layout`, 3541 lines). srmech 0.9.0rc434, exact ℚ. Generating code: `R-RBS-LM-FUREYALG_the_tensor_product_from_the_thesis_body_and_the_sedenion_decision.py` (13 checks, exit 0).

## 1 — the rule, verbatim from the body `[ATTESTED — primary source]`

> **§6.2, p. 37:** *"The generic element of ℂ⊗𝕆 is written ∑⁷ₙ₌₀ Aₙeₙ, where the Aₙ are complex coefficients. The eₙ are octonionic imaginary units (eₙ² = −1), apart from e₀ = 1, which multiply according to Figure 6.1. **The complex imaginary unit i commutes with the octonionic eₙ.**"*

> **§7.2, p. 52:** *"Readers should note that when multiplying elements constructed from ℝ⊗ℂ⊗ℍ⊗𝕆, **the quaternionic and octonionic imaginary units always commute with each other.**"*

> **§1, p. 4:** ℂ⊗𝕆 is *"the eight-complex dimensional algebra"* — i.e. **16 real dimensions**.

**That is the whole definition.** F1350 inferred the commuting rule from how a tensor product must work; the body states it, twice, as a thing the reader is explicitly asked to note. The inference was right and is now unnecessary.

## 2 — what the stated rule forces, built in srmech `[DEMONSTRABLE]`

An element is `a + i·b` with `a, b ∈ 𝕆` and `i` **central**; so `(a + ib)(c + id) = (ac − bd) + i(ad + bc)`. **No conjugation anywhere** — that *absence* is the entire difference from the Cayley–Dickson double, which conjugates.

| check | result |
|---|---|
| `i` commutes with all 8 octonionic units (§6.2) | **8/8** |
| …while the `eₙ` do **not** commute with each other | **42 of 49** pairs fail |
| `(i·e₁)² = +1`, and `i·e₁ ∉ {±1}` | ✔ |
| `(1 + i·e₁)(1 − i·e₁) = 0` | ✔ — **constructed, not found** |

> **The centre GROWS.** The tensor product glues on a **new commuting direction**; the CD double glues on an **anti-commuting** one. Same dimension jump, opposite character — and the commuting one manufactures a zero divisor at the *first* application, because `1 − x² = 0` exactly when `x² = +1`, and on the ladder every imaginary squares to −1 so `1 − x² = 2` and never vanishes.

## 3 — this DECIDES F1350's open item `[DEMONSTRABLE + one stated inference]`

F1350 said: *"**NOT decided:** whether ℂ⊗𝕆 ≅ 𝕊 … do not report this as settled."* Both are dim 16, non-associative, with zero divisors — those three agree. **Two invariants separate them:**

| | ℂ⊗𝕆 | 𝕊 |
|---|---|---|
| centre (basis directions) | **2** — `e₀` and `i·e₀` | **1** — `E₀` |
| square roots of `+1` | **`i·e₁` exists** | **only ±1** |
| all imaginary units square to −1 | no (`i·e₁` → +1) | **yes, 15/15** |

The second row closes by the **quadratic relation**, measured on **420/420** structured elements: `x² = 2·Re(x)·x − N(x)`. If `x² = +1` in 𝕊 then `2·Re(x)·x` is real, so either `Re(x) = 0` — and then `x² = −N(x) ≤ 0`, never `+1` — or `x` is real, giving `x = ±1`.

**An isomorphism preserves squares and preserves the centre. Therefore ℂ⊗𝕆 ≇ 𝕊** — settled by the rule *Furey states*, not by our ladder.

## 4 — the script conversion: NOT APPLICABLE, and verified so

**The thesis publishes no code.** Word-bounded search over the full extracted text for `code|software|program|compute[dr]|simulation|numerical|Maple|Sage|Mathematica|Fortran|C++|repository|supplementary` returns **zero** software references. No appendix, no computational section, no repository link. The only "code" is *"a fermionic binary code"* (§8.2) — the exterior-algebra ΛC⁵ **labelling scheme**, mathematics rather than software.

> **The absence is itself the finding:** every result in the thesis is hand-derived algebra with **no computational layer to port**. What converts is the *stated rule*, and §2 is that conversion.

*(A first pass mis-hit on `script` — it is a substring of "de**script**ion". Whole-word matching is what makes an absence claim checkable, and the absence claim is the deliverable here.)*

## Honest scope

- `[ATTESTED]`: §1's quotes are transcribed from the primary PDF, with section and page. Attestation record: `R-RBS-LM-ATTEST_furey_1611_09182.md` (arXiv:1611.09182v1, DOI `10.48550/arXiv.1611.09182`, **University of Waterloo PhD thesis, 2015**, arXiv posting 16 Nov 2016 — the uWaterloo LaTeX template and degree statement are both in the document).
- `[DEMONSTRABLE]`: everything in §2–§3, exact ℚ, 13 checks.
- **INFERRED, stated as such**: that commuting with every *basis* element implies commuting with everything (bilinearity); the one-line step from the quadratic relation to "no square root of +1 but ±1".
- **NOT established — nothing here touches Furey's PHYSICS.** This reads her multiplication rule and nothing else. The Standard-Model content — the Cl(6) ladder operators, the SU(3)c×U(1)em structure, the ΛC⁵ binary code — is **untouched and uncited**. Reading a stated algebra is not assessing a physics programme, and this finding must never be cited as if it were.
- **No claim that either algebra is "the right one"** for anything. Two objects, two laws, measured.
- **What would falsify §3:** exhibit an element of 𝕊 with `x² = +1` other than ±1 (would break the quadratic argument), or show the centre computation admits non-basis central elements the basis scan missed.

**Closes F1350's explicit NOT-DECIDED item.** Composes **F1350**, **F1349**, **F1338**, and the Furey attestation.
