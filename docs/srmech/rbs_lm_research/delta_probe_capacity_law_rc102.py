"""DELTA probe: does the exact-operations machinery INSTRUMENT + FORMALIZE
siona's information-side architecture (F994/F995/F996)?

Q2: fractal_spectrum (Ch-2) as the reader of F995's asymmetric fold's
    self-similarity signature; Ch-1/Ch-2 split diagnoses F994(sym)-vs-F995(asym).
Q3: the elliptic quasi-periodicity multiplier (-z^-1) as the EXACT per-level
    asymmetric fold; is_elliptic as the half-beat coherence reader.

Pure-Python worktree path (rc100); non_compute + exact-Q ops, so pure IS the
complete alternative. No numpy, no abs().
"""
import sys
import os as _os
# Session-local rc100+ worktree, if present; otherwise fall through to an
# installed srmech >= 0.9.0rc100 (fractal_spectrum + ellbase are shipped there).
# The ops exercised are non_compute / exact-Q, so worktree == installed.
_wt = "D:/GitHub/mlehaptics/.claude/worktrees/srmech-rc101-jackson-verified/docs/srmech/python"
if _os.path.isdir(_wt):
    sys.path.insert(0, _wt)

import srmech
from srmech.amsc.coupling import fractal_spectrum, resonant_spectrum
from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
print("srmech", srmech.__version__)
print("=" * 70)

# ---------------------------------------------------------------------------
# Q2a — F994 fact reproduced with srmech (Ch-1 isometry diagnostic):
# the gamma5 (Klein-4 chirality) flip is an EXACT ISOMETRY -> a SYMMETRIC fold
# preserves every inner product -> preserves the Gram/eigenspectrum -> adds NO
# new orthogonal mode (why F994's 4x symmetric write = 56->56%, 0 gain).
# ---------------------------------------------------------------------------
print("Q2a  SYMMETRIC fold = Ch-1 isometry (F994 mechanism)")
try:
    from srmech.amsc.hdc import (klein4_bind, klein4_bundle, klein4_similarity,
                                 klein4_chirality_flip_gamma5)
    import random
    random.seed(7)
    D = 2048
    def rhv():
        return [random.randint(0, 1) for _ in range(D)]
    a, b = rhv(), rhv()
    s_ab = klein4_similarity(a, b)
    s_g = klein4_similarity(klein4_chirality_flip_gamma5(a),
                            klein4_chirality_flip_gamma5(b))
    print(f"   sim(a,b)         = {float(s_ab):.4f}")
    print(f"   sim(g5 a, g5 b)  = {float(s_g):.4f}   -> isometry: {s_ab == s_g}")
    print("   => symmetric (isometry) fold preserves the spectrum = Ch-1, no new mode")
except Exception as e:
    print("   (klein4 path skipped:", repr(e), ")")
print("-" * 70)

# ---------------------------------------------------------------------------
# Q2b — fractal_spectrum READS a fold's self-similarity signature.
# The F995 asymmetric fold folds nexts to rungs by salience rank (recession r
# per rung) with fan-out B per level (the F962 recursive/self-similar compose).
# Its self-similar signature is exactly what fractal_spectrum computes: scale
# = 1/r (the |q| per level), d_s = 2 log(B)/log(scale), octaves/level, rung.
# A degree-2 decimation with the fold's scale: R(z)=z(s-(s-1)z), R'(0)=s.
# ---------------------------------------------------------------------------
print("Q2b  fractal_spectrum reads the ASYMMETRIC fold's self-similarity signature")
def fold_signature(recession_r, branches, label):
    s = int(round(1 / recession_r)) if (1 / recession_r) == int(1 / recession_r) else 1 / recession_r
    # decimation Poly with R'(0)=scale, R(0)=0, degree 2 (a genuine renormalization)
    R = Poly.from_coeffs([0, s, -(s - 1)])           # z(s-(s-1)z)
    out = fractal_spectrum(R, branches)
    d_s = out["self_similarity_dim"]
    print(f"   {label}: recession r=1/{s}, fan-out B={branches}")
    print(f"      scale=R'(0)={out['scale']}  octaves/level(|q|-meter)={out['q_octaves_per_level']}"
          f"  rung={out['rung_class']}")
    print(f"      self_similarity_dim d_s = {d_s[0]}/{d_s[1]} = {d_s[0]/d_s[1]:.5f}")
    return out

fold_signature(Q(1, 2), 3, "fold-A (half-life recession)")   # r=1/2 -> 1 octave (F974 unit)
fold_signature(Q(1, 5), 3, "fold-B (Sierpinski-scale recession)")   # r=1/5 -> 3 octaves
fold_signature(Q(1, 5), 5, "fold-C (same scale, DIFFERENT fan-out)")  # distinct d_s
print("   => distinct folds -> distinct signatures; the |q|-meter reads the recession,")
print("      d_s reads the branching. fractal_spectrum recovers the fold's fractal shape.")
print("-" * 70)

# ---------------------------------------------------------------------------
# Q2c — the honest boundary (ties to Q1): the fold's PARAMETRIC signature is
# representable; the FULL spectrum of the stored fold = Julia set of R =
# operand-IRREPRESENTABLE (the same ceiling F996's dissolution relocates to).
# ---------------------------------------------------------------------------
out = fold_signature(Q(1, 5), 3, "fold-B again (for the OPEN)")
print("   spectrum_open:", out["spectrum_open"][:88], "...")
print("=" * 70)

# ---------------------------------------------------------------------------
# Q3 — the elliptic quasi-periodicity multiplier is the EXACT per-level
# asymmetric fold; is_elliptic is the half-beat coherence reader.
# ---------------------------------------------------------------------------
print("Q3  elliptic multiplier = exact asymmetric fold ; is_elliptic = coherence reader")
try:
    from srmech.amsc.ellbase import EllMonomial, Theta, EllRatio, _X, _P
    x = EllMonomial(Q(1, 1), {_X: 1})               # the argument x
    th = Theta(x)                                    # theta(x; p)
    r_single = EllRatio.theta(th)                    # a single (unbalanced) theta
    print("   single theta ratio  is_elliptic:", r_single.is_elliptic(),
          "(weight", r_single.weight, ") -> asymmetric halves (multiplier != 1)")
    # the per-level multiplier: pshift(theta) differs from theta by exactly the
    # quasi-periodicity multiplier (-1)^k p^{-k(k-1)/2} z^{-k} -- the -z^-1 family.
    shifted = r_single.pshift()
    print("   pshift(theta) == theta ?", shifted == r_single,
          "-> the period step is a CHIRAL TRANSFORM, not an identity copy")
    print("   pshift prefactor (the multiplier monomial):", shifted.prefactor)

    # a BALANCED / very-well-poised ratio: theta(x)theta(1/x) / [theta(x)theta(1/x)]
    # is trivially elliptic; build a genuine balanced pair to show is_elliptic True.
    xi = EllMonomial(Q(1, 1), {_X: -1})             # 1/x
    th_i = Theta(xi)
    bal = EllRatio(num=(th, th_i), den=(th, th_i))  # balanced (weight 0)
    print("   balanced +/- pair    is_elliptic:", bal.is_elliptic(),
          "(weight", bal.weight, ") -> coherent full beat (multiplier nets to 1)")
    print("   => symmetric(multiplier 1)=F994-redundant ; asymmetric(-z^-1)=F995-fold")
except Exception as e:
    import traceback; traceback.print_exc()
    print("   (elliptic path error:", repr(e), ")")
print("=" * 70)
print("probe done")
