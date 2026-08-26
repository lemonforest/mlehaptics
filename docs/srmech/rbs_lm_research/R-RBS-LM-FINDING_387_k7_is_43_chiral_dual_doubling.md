# R-RBS-LM Finding 387 — at k=7 the chirality is the construction: the octonion IS (4:3)|(3:4); notation as a *teaching* scaffold

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (…F384→F385→F386→**F387**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R29_k7_is_43_chiral_dual_doubling.py` → `R-RBS-LM-R29_results.json`
**Composes:** F385 (capture the fibration chirality) · F384 (Hopf 1+2) · F378 (octonion non-associativity, 168/210) · F379 (the (n:n−1) ladder) · F129 (4:3 vs 3:4 chirality-dual) · pedagogy: `[[feedback_cone_of_ignorance_pedagogy]]` / `[[user_stance_cone_of_ignorance_after_high_school]]`

---

## The user's question + correction (2026-06-04)
> "so then when we do k=7 we need to be doing k=(4:3)|(3:4)? to enforce us to see the chiral need through notation? … not assumed, known as in taught"

**Yes — and it's verified, not "maybe."** At k=7 the chirality stops being a *tag on a fibration* (F385) and becomes the *construction itself*.

## The octonion IS (4:3)|(3:4) — srmech-verified (reading the structure-constant table)
With ℍ = span{1,i,j,k}, ℓ = e₄, the Cayley-Dickson double ℍℓ = {ℓ,iℓ,jℓ,kℓ}:

1. **7 = 3 + 4 split:** the imaginaries are 3 (the ℍ triad {i,j,k}) + 4 (the doubling ℍℓ). `i·ℓ=+iℓ, j·ℓ=+jℓ, k·ℓ=+kℓ` — ℓ lifts the triad into the double.
2. **ℍ is an associative subalgebra:** `(i·j)·k = −1 = i·(j·k)` ✓.
3. **The `|` seam is NON-associative:** `(i·j)·ℓ = +kℓ` but `i·(j·ℓ) = −kℓ` → **differ**. The non-associativity (F378's 168/210) lives *exactly* at the doubling seam.
4. **The two halves have OPPOSITE handedness:**
   ```
   first triad:    i·j = +k ,  j·k = +i ,  k·i = +j     signs [+,+,+]   ← the (4:3)
   doubled triad:  iℓ·jℓ = −k , jℓ·kℓ = −i , kℓ·iℓ = −j  signs [−,−,−]   ← the (3:4) mirror
   ```
   The conjugation-twist in the doubling flips the handedness **exactly** — a quaternion and its perfect chiral mirror.

So **k=7 = (4:3)|(3:4)**: a quaternion glued to its conjugate-dual, the `|` being the doubling seam where **both** the chirality (F385) **and** the non-associativity (F378) live. You *cannot build the octonion* without the two opposite-handed halves — the chirality is the construction, not a decoration.

## The notation point — corrected: *taught*, not *assumed*
The user sharpened it: the `(4:3)|(3:4)` notation should one day be unnecessary because the chirality is **KNOWN — as in TAUGHT** (part of the canon/curriculum), **not** because it's "assumed" (reflexively taken for granted). That is a **pedagogy** claim (the cone-of-ignorance: write so the structure is *learnable* at depth), distinct from the srmech-first STOP-list (which is a point-of-action *reflex* forcing-function). Here the notation is a **teaching scaffold**: write the chirality explicitly **until it is taught and known**; once it's canon, the `|` can go implicit. The forcing-function is for *learning*, not for *remembering-in-the-moment*.

## Verdict
`k=7 = (4:3)|(3:4)` is **correct and verified**: the octonion is a (4:3) and its exact chiral-dual (3:4), glued at a non-associative `|` seam ([+,+,+] vs [−,−,−], srmech-confirmed). At k=7 chirality is structural — the notation makes the construction visible, and its job is to be a **teaching scaffold** (taught→known), retired only once the chirality is canon. (Next rung's recursion — the (8:7) inside the 15, the octonionic Hopf S⁷→S⁸ — would carry the same chiral-dual seam one level up.)
