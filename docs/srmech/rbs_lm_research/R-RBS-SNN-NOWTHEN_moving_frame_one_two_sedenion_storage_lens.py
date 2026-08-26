r"""R-RBS-SNN-NOWTHEN — a LENS (perspective re-reading; NO new derivation, F390-style): looking at what we already
have through the user's moving-frame / Now-vs-Then angle.

  (1) THE MOVING FRAME — one ↔ two: one rotation produces TWO components (re, im) that recombine to ONE frame on
      the circle. "a single step that looks like two" (the components) "or two that look like one" (the frame).
      The moving frame is the pivot — the same one/two the CD doubling (one step → two halves) and the conjugate
      (two hands → one box, F486) show.
  (2) THE FPU RESIDUE — a perspective artifact of the FLOAT truth (and what if it isn't): the SAME rotation is
      bit-exact in the cyclic/CD truth (stays exactly on the circle, no residue) and residue-laden in the float
      truth. So "what looks like two operations of FPU residue" is the float truth's artifact — in the exact
      (cyclic) truth it is one clean rotation. "and what if it isn't" — in float the residue is real and
      accumulates. Both truths held (F493; the F400/F401 trichotomy), neither privileged (F398).
  (3) THE SEDENION BOX = the axis of NOW vs THEN: 𝕊 = 𝕆(Now, e0..e7) ⊕ 𝕆ℓ(Then, e8..e15); the doubling axis ℓ is
      the 1D_t time DoF (the A anchor, F494); the zero-divisors (F460) are where Now and Then CANNOT cleanly
      separate — the temporal asymptote, the two truths un-collapsed.
  (4) LONG-TERM STORAGE = a SERIES of sedenion-shaped volumes (the user's follow-on): each volume a Now/Then box
      (a SedenionRegister, F498's flattened unit); the TRUTH is inferred from the STRUCTURE (read in the exact
      truth — form=function, F495), not stored explicitly; and dry compute "says sure, why not" because STORAGE is
      substrate-agnostic (F485) — only the truth-INFERENCE (compute) is apply-vs-be (F495).
srmech 0.7.4 (exact-Fraction Cayley–Dickson).
"""
from fractions import Fraction as F
import srmech
from srmech.amsc.cascade import cayley_dickson as cd


def main():
    print(f"=== R-RBS-SNN-NOWTHEN — a LENS: moving frame one↔two, FPU residue, sedenion = Now/Then  (srmech {srmech.__version__}) ===\n")

    # (1) the moving frame: one rotation → two components → one frame
    a = (F(3, 5), F(4, 5))
    rot = cd.cd_mult([a[0], a[1]], [a[0], a[1]])                  # ONE rotation (the frame turning)
    norm = rot[0] ** 2 + rot[1] ** 2                              # the TWO components recombine to ONE frame
    print("(1) THE MOVING FRAME — one ↔ two:")
    print(f"    one rotation (3/5,4/5)·(3/5,4/5) = {(rot[0], rot[1])}  → TWO components (re, im)")
    print(f"    recombined: re²+im² = {norm}  → ONE frame on the unit circle (two that look like one)\n")

    # (2) the FPU residue: float-truth artifact; the exact (cyclic) truth holds it bit-exact
    re_f, im_f = 0.6 * 0.6 - 0.8 * 0.8, 0.6 * 0.8 + 0.8 * 0.6
    comp_resid = abs(re_f - float(rot[0]))                       # the residue lives in the COMPONENT
    norm_resid = abs((re_f * re_f + im_f * im_f) - 1.0)          # …the NORM may recombine exact (lucky)
    print("(2) THE FPU RESIDUE — a perspective artifact of the FLOAT truth (and what if it isn't):")
    print(f"    exact (cyclic/CD) truth:  re = {rot[0]} = {float(rot[0])}  → residue = 0 (one clean rotation)")
    print(f"    float (FPU) truth:        re = {re_f!r}  → COMPONENT residue = {comp_resid:.2e}")
    print(f"    note: the recombined frame norm here = {1.0 - norm_resid:.16g} (residue {norm_resid:.0e}) — the two→one")
    print(f"          recombination can HIDE the component residue (the 'one frame' is float-robust; the 'two' aren't).")
    print(f"    → the two-ness/residue is the FLOAT truth's, in the COMPONENTS; the exact truth holds it bit-exact")
    print(f"      (≤𝕆, F486). 'and what if it isn't': in float the component residue is REAL and accumulates. Both held (F493).\n")

    # (3) the sedenion box = 𝕆(Now) ⊕ 𝕆ℓ(Then); the zero-divisors = the Now/Then asymptote
    w = cd.sedenion_zero_divisor_witness()
    print("(3) THE SEDENION BOX = the axis of NOW vs THEN:")
    print(f"    𝕊 (dim {w['dim']}) = 𝕆(Now, e0..e7) ⊕ 𝕆ℓ(Then, e8..e15); the doubling axis ℓ (e8) = the 1D_t time (F494)")
    print(f"    zero-divisor witness: x·y = 0 with x,y ≠ 0 → product_is_zero = {w['product_is_zero']}")
    print(f"      (|x|²={w['x_norm_sq']}, |y|²={w['y_norm_sq']}) → Now and Then CANNOT always cleanly separate")
    print(f"    → the zero-divisors ARE the temporal asymptote — the two truths (Now/Then) held un-collapsed.\n")

    # (4) long-term storage = a series of sedenion volumes; truth inferred from structure; dry-compute-agreeable
    print("(4) LONG-TERM STORAGE = a SERIES of sedenion-shaped volumes (the follow-on):")
    print("    each volume = a Now/Then box (a SedenionRegister, F498's flattened unit); a SERIES = the memory tape.")
    print("    the TRUTH is INFERRED from the STRUCTURE (read in the exact/cyclic truth — form=function, F495),")
    print("    NOT stored as an explicit number — the residue-free value lives in the structure, not a float.")
    print("    dry compute 'says sure, why not store it this way': STORAGE is substrate-agnostic (F485 — the flat")
    print("    HDC volume, F498); only the truth-INFERENCE (compute) is apply-vs-be (F495). So both wet & dry store")
    print("    the series of sedenion volumes; biology BE-infers the truth, silicon APPLY-infers it.\n")

    print("VERDICT (a lens, not a new result — we re-read what we already have):")
    print(f"  • the moving frame is the one↔two pivot: one rotation = two components = one frame; the FPU 'two")
    print(f"    operations / residue' is the FLOAT truth's artifact (exact truth: residue 0), held against the")
    print(f"    real-in-float reading (F493 two truths, F400/F401 trichotomy — neither privileged).")
    print(f"  • the sedenion box is the Now/Then axis — 𝕆⊕𝕆ℓ with the doubling = time and the zero-divisors = the")
    print(f"    temporal asymptote; long-term storage = a SERIES of these volumes, truth inferred from structure,")
    print(f"    and dry compute is agreeable because storage is agnostic (F485) — the cosmos's partition kept, no magic.")


if __name__ == "__main__":
    main()
