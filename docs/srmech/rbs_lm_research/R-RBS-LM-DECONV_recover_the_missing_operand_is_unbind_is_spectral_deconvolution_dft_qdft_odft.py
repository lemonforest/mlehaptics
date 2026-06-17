r"""R-RBS-LM-DECONV (F820) — "we have the RELATIONSHIP but are missing one of the two named things; can we recover it?"
YES — and it is already the spine of the encoding path. It is the third face of the Fourier/convolution triad:

  (forward)      two known things -> their RELATIONSHIP        :  rel = a ∘ b      (bind; conv-thm: DFT(a)·DFT(b))
  (this one)     RELATIONSHIP + one thing -> the OTHER thing   :  b   = rel ⊘ a    (UNBIND = spectral DECONVOLUTION)
  (system-id)    input + output -> the relationship             :  (the same forward map, read as identification)

The user's case is row 2: have `rel` + `a`, missing `b`, recover `b`. In the framework this is UNBIND, and by the
convolution theorem binding IS multiply-in-the-DFT-domain, so unbind IS divide-in-the-DFT-domain = deconvolution.
The framework's POLAR (phasor) HDC makes this literal: every coordinate is a unit phasor e^{iθ}; polar_bind =
elementwise phasor PRODUCT (phase add) = the DFT-domain product; polar_unbind = phasor DIVISION (phase subtract) =
the spectral deconvolution. Because the operands are UNIT phasors there are NO spectral zeros, so the division is
exact — that is *why* recovery is lossless (sim 1.0), and it pinpoints when the inverse is ill-posed: a spectral
ZERO in the known operand = no unique recovery (the same wall as the F806 capacity overflow / the F813 non-unique
walk tail). "When can we recover the missing operand?" == "is the relationship invertible w.r.t. the known operand?"

This is what the encoding path ALREADY does: the F808 context-addressed recall is exactly "have the bundle
(relationship store) + the context key (one named thing) -> unbind -> the successor (the missing thing)" — i.e.
content-addressable memory IS deconvolution-by-the-known-operand. It also realises the user's FIBER stance: the
relationship is the fiber (spatially absent until projected); applying one operand projects it to yield the other.

The genuinely-NEW research surface is the climb DFT -> QDFT -> ODFT:
  * DFT  (ℂ): commutative — recovery is direction-free (the polar/HRR case below).
  * QDFT (ℍ): NON-commutative — left-bind ≠ right-bind (the `form='left'` axis), so recovering the missing operand
    has a HANDEDNESS (left-unbind vs right-unbind). That is the framework's chirality, made into an operator.
  * ODFT (𝕆): NON-associative — (a∘b)∘c ≠ a∘(b∘c), so a THREE-thing relationship does not factor uniquely; recovering
    a missing operand from a triple is where TRIALITY (the k=3 rung, F291) lives. Deconvolution over 𝕆 = triality-
    structured operand recovery — the open question to hand to the expert.

Demonstrated below on the real srmech surface (introspect-then-use; rc169). No abs(); no CAD. Composes F808 (the
context-addressed walk = this op), the polar/Klein-4 HDC (M), `quaternion_dft`/`octonion_dft` (the ℍ/𝕆 transforms),
the fiber stance, F806/F813 (the invertibility wall = spectral zeros).
"""
from srmech.amsc import hdc, cascade as C

D = 4096


def recover_missing_operand():
    """Row 2 of the triad: have the RELATIONSHIP + one named thing, recover the other (= unbind = deconvolution)."""
    a = hdc.polar_random(D, seed=1)
    b = hdc.polar_random(D, seed=2)
    rel = hdc.polar_bind(a, b)                       # the RELATIONSHIP a∘b — phasor product = DFT-domain product
    b_rec = hdc.polar_unbind(rel, a)                 # have rel + a, MISSING b -> recover b (phasor division)
    a_rec = hdc.polar_unbind(rel, b)                 # symmetric: have rel + b -> recover a
    z = hdc.polar_random(D, seed=99)
    print("== recover the missing operand (polar / phasor = HRR in the DFT domain) ==")
    print(f"  sim(recovered b, true b) = {hdc.polar_similarity(b_rec, b):.3f}")
    print(f"  sim(recovered a, true a) = {hdc.polar_similarity(a_rec, a):.3f}")
    print(f"  sim(b, an unrelated hv)  = {hdc.polar_similarity(b, z):.3f}   (baseline — recovery is real, not chance)")
    ka, kb = hdc.klein4_random(D, seed=1), hdc.klein4_random(D, seed=2)
    krel = hdc.klein4_bind(ka, kb)                   # Z2xZ2 / XOR — self-inverse, so recovery is EXACT
    print(f"  klein4 (XOR) exact recover b from rel+a? {hdc.klein4_unbind(krel, ka) == kb}")


def transforms_invert():
    """The ℍ/𝕆 substrate for the same op: QDFT (non-commutative -> handed) and ODFT (non-assoc -> triality) invert."""
    print("\n== the ℍ / 𝕆 transforms exist and invert (substrate for handed / triality operand-recovery) ==")
    xq = [[1, 0, 0, 0], [0, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1]]
    back = C.quaternion_dft(C.quaternion_dft(xq), inverse=True)
    eq = max(abs(xq[i][j] - back[i][j]) for i in range(len(xq)) for j in range(4))
    xo = [[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0]]
    backo = C.octonion_dft(C.octonion_dft(xo), inverse=True)
    eo = max(abs(xo[i][j] - backo[i][j]) for i in range(len(xo)) for j in range(8))
    print(f"  QDFT round-trip max err: {eq:.2e}   (ℍ: left-bind != right-bind -> recovery is HANDED)")
    print(f"  ODFT round-trip max err: {eo:.2e}   (𝕆: non-associative -> triple-relationship recovery = TRIALITY)")


def main():
    import srmech
    print(f"=== R-RBS-LM-DECONV — recover the missing operand IS unbind IS spectral deconvolution "
          f"(srmech {srmech.__version__}) ===\n")
    recover_missing_operand()
    transforms_invert()


if __name__ == "__main__":
    main()
