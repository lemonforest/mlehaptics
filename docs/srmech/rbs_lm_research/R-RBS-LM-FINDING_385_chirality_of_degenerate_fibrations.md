# R-RBS-LM Finding 385 — capture the chirality of the degenerate fibrations: it's the left/right handedness = the left/right/two-sided QFT

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (…F382→F383→F384→**F385**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R27_chirality_of_degenerate_fibrations.py` → `R-RBS-LM-R27_results.json`
**Composes:** F384 (the Hopf 1+2 split) · F380/F381 (ℍ non-commutativity → left/right/two-sided QFT) · F129 (4:3 vs 3:4 chirality-dual) · F130 (γ₅/iω₇ axes) · F357 (`octonion_left_mult`/`octonion_right_mult`) · Class C

---

## The user's point (2026-06-04)
> "and we have to capture the chirality of our degenerate fibrations"

Correct — and it is *load-bearing*, not decoration. F384 fibered the symmetric "3" of (4:3)=ℍ as 1 (fiber) + 2 (base) by **choosing** a complex structure (which imaginary is the fiber). That choice **breaks the SO(3)/triality symmetry of the 3** — *the degeneration* (the three were symmetric/equivalent; picking a fiber degenerates them to a preferred axis). What the choice leaves behind is a **handedness**, and you must capture it.

## The chirality IS the left/right handedness (srmech-native)
Because ℍ is **non-commutative**, the chosen fiber can act on the base by **left** or **right** multiplication, and the two are **mirror** fibrations:
```
LEFT   i·j = +k      RIGHT  j·i = −k       → mirror images (same axis, opposite sign)
octonion_left_mult(i)·j  = +k       octonion_right_mult(i)·j = −k     (named-op confirmation)
```
That residual **Z₂** is the chirality:
- = **γ₅ / iω₇** (F130, the two chirality axes)
- = the **(4:3) vs (3:4) chirality-dual** (F129)
- = the **left / right / two-sided QFT** the literature defines (F380/**F381**)

So the user's geometric intuition (the fibration has a handedness), the algebraic fact (ℍ left ≠ right), the framework's chirality axes (γ₅/iω₇), and the literature's QFT forms are **all the same Z₂**. The left/right QFT *is* the captured chirality of the degenerate fibration.

## Why "we have to capture it"
Dropping the handedness collapses left and right into one — exactly the **flat shadow** (F380), which loses the γ₅/iω₇ that made the object quaternionic in the first place. So:
- the **QDFT/ODFT descriptors** (F380/F381) must carry the **`form=` left/right/two-sided** tag (they do);
- the **(4:3)-native substrate** (F383) must carry a **handedness tag** alongside the fiber/base split;
- operationally the tag is **Class C `net_chirality`** (the cascade-orientation class) on every fibration choice.

## Verdict
Fibering the symmetric 3 (choosing a complex structure) **degenerates** its SO(3)/triality symmetry; the residue is a **handedness** = left-vs-right multiplication = the γ₅/iω₇ chirality = the (4:3)/(3:4) dual = the left/right/two-sided QFT (F381). **Capture it (carry the left/right / Class-C tag) on every fibration, or collapse to the flat shadow.** The chirality is not a property *of* the fibration to note afterward — it is the data the degeneration *produces*, and the thing the whole (4:3)-vs-(2:1)-shadow distinction rests on.
