"""F924 Qarg polar-read prototype (closes C+K) — concatenated probes: qarg_polar + qarg_ck_closure + qarg_api. srmech rc28."""
# ===== qarg_polar.py =====
"""Prototype the polar read on srmech's exact-complex carrier Qi.

Discipline: srmech + stdlib fractions only. No numpy, no math.*, no the ALU absolute-value op.
- modulus r : srmech.asymptotic_calculus.hypot (Class-N exact sqrt of re^2+im^2)
- argument theta : srmech.asymptotic_calculus.atan2 (exact Q, quadrant logic, Class-C/K)
- round-trip : srmech cos/sin series (exact Q) -> r*cos, r*sin
"""
import srmech.asymptotic_calculus as ac
from srmech.amsc.qi import Qi
from srmech.amsc.q import Q


def qi_modulus(z: Qi) -> Q:
    """r = |z| as an exact Q. The carrier already exposes the EXACT-rational
    norm_sq() = re^2+im^2 (Class-K magnitude-squared); sqrt(Q) keeps it rational.
    Equivalent to hypot(re, im) but starts from the carrier's own exact norm_sq."""
    return ac.sqrt(z.norm_sq())


def qi_arg(z: Qi) -> Q:
    """theta = atan2(im, re) as an exact Q. Quadrant logic is Class-C direction
    + Class-K pin-slot sign handling (NOT abs)."""
    return ac.atan2(z.imag, z.real)


def qi_as_polar(z: Qi):
    """(r, theta) both exact Q."""
    return qi_modulus(z), qi_arg(z)


def qi_from_polar(r: Q, theta: Q) -> Qi:
    """Reconstruct via exact cos/sin series. (r*cos(theta), r*sin(theta))."""
    c = ac.cos(theta)          # exact Q
    s = ac.sin(theta)          # exact Q
    re = Q(r.numerator * c.numerator, r.denominator * c.denominator)
    im = Q(r.numerator * s.numerator, r.denominator * s.denominator)
    return Qi(re, im)


# ---- gap confirmation ----
print("=== GAP: polar read accessors on the carriers ===")
for name, cls in [("Qi", Qi), ("Q", Q)]:
    surf = [a for a in dir(cls) if not a.startswith("_")]
    polar = [a for a in surf if a in ("arg", "argument", "as_polar", "modulus",
                                      "phase", "polar", "angle", "abs")]
    print(f"{name} public surface: {surf}")
    print(f"{name} polar accessors present: {polar if polar else 'NONE'}")
print()

# ---- construct + read ----
print("=== construct Qi and read real/imag ===")
z = Qi(Q(3, 1), Q(4, 1))            # 3 + 4i
print("Qi(Q(3,1), Q(4,1)) =", z, "| real =", float(z.real), "imag =", float(z.imag),
      "| norm_sq() =", float(z.norm_sq()))
print("from_pairs((3,1),(4,1)) =", Qi.from_pairs((3, 1), (4, 1)))
print()

# ---- round-trip across 4 quadrants + axes ----
print("=== polar round-trip residuals (exact Qi in -> polar -> exact Qi out) ===")
test_points = [
    ("Q1 (+,+)", Q(3, 1), Q(4, 1)),
    ("Q2 (-,+)", Q(-3, 1), Q(4, 1)),
    ("Q3 (-,-)", Q(-3, 1), Q(-4, 1)),
    ("Q4 (+,-)", Q(3, 1), Q(-4, 1)),
    ("+x axis ", Q(5, 1), Q(0, 1)),
    ("+y axis ", Q(0, 1), Q(5, 1)),
    ("-x axis ", Q(-5, 1), Q(0, 1)),
    ("-y axis ", Q(0, 1), Q(-5, 1)),
    ("frac    ", Q(1, 3), Q(2, 7)),
]
for label, re, im in test_points:
    z = Qi(re, im)
    r, th = qi_as_polar(z)
    zr = qi_from_polar(r, th)
    # residual = |z - zr| via exact Q diffs, magnitude only at display
    dre = float(z.real) - float(zr.real)
    dim = float(z.imag) - float(zr.imag)
    # residual magnitude through srmech (Class-K), not the ALU absolute-value op
    res = float(ac.hypot(dre, dim))
    print(f"{label}: z=({float(re):+.4f},{float(im):+.4f})  "
          f"r={float(r):.6f}  theta={float(th):+.8f} rad  "
          f"recon=({float(zr.real):+.6f},{float(zr.imag):+.6f})  residual={res:.3e}")
# ===== qarg_ck_closure.py =====
"""C/K closure demo on a real srmech magnetic Laplacian.

The magnetic Laplacian encodes directed-edge DIRECTION as a complex phase
(Class C, theta) on top of edge MAGNITUDE (Class K, r). The polar read
(arg + modulus) is exactly the accessor that recovers both. Reversing a
directed edge/cycle flips the phase sign -> chirality flip, visible as
opposite-sign theta.

Discipline: srmech ops only; no numpy/math/abs. Complex entries come back as
builtin `complex` from the Mat engine, so we lift them into the exact carrier
Qi via Q.from_float before the polar read (and note this interop gap).
"""
import srmech.asymptotic_calculus as ac
from srmech.amsc.qi import Qi
from srmech.amsc.q import Q
import srmech.amsc.laplacian as lap
from srmech.amsc.cascade import magnitude as kmag   # Class-K magnitude, replaces the ALU absolute-value op


def polar_of_complex(z) -> tuple:
    """Polar read of a builtin complex via the exact carrier path.
    Lift to Qi (exact), then r=sqrt(norm_sq()), theta=atan2(im,re)."""
    qz = Qi(Q.from_float(z.real), Q.from_float(z.imag))
    r = ac.sqrt(qz.norm_sq())          # Class-K modulus, exact Q
    th = ac.atan2(qz.imag, qz.real)    # Class-C/K argument, exact Q
    return r, th


n = 3
fwd = [(0, 1), (1, 2), (2, 0)]   # directed 3-cycle, one chirality
rev = [(1, 0), (2, 1), (0, 2)]   # the REVERSED cycle (opposite chirality)

Hf = lap.magnetic_laplacian(n, fwd, q=0.25)
Hr = lap.magnetic_laplacian(n, rev, q=0.25)

print("=== C/K CLOSURE: directed 3-cycle off-diagonal phase ===")
print("q=0.25 (quarter-turn per unit net flow). Off-diagonal H[i,j] carries")
print("direction as phase (Class C) on magnitude (Class K).")
print()
print(f"{'edge':<8}{'FORWARD H[i,j]':<28}{'r (K)':<12}{'theta (C) rad':<18}"
      f"{'REVERSED H[i,j]':<28}{'theta_rev (C) rad'}")
for (i, j) in [(0, 1), (1, 2), (2, 0)]:
    zf = Hf[i, j]
    zr = Hr[i, j]
    rf, thf = polar_of_complex(zf)
    rr, thr = polar_of_complex(zr)
    print(f"({i},{j})   "
          f"{f'{zf.real:+.4f}{zf.imag:+.4f}i':<24}"
          f"{float(rf):<12.6f}{float(thf):<+18.8f}"
          f"{f'{zr.real:+.4f}{zr.imag:+.4f}i':<24}"
          f"{float(thr):<+.8f}")

print()
print("=== chirality flip: forward theta + reversed theta (should sum to 0) ===")
for (i, j) in [(0, 1), (1, 2), (2, 0)]:
    _, thf = polar_of_complex(Hf[i, j])
    _, thr = polar_of_complex(Hr[i, j])
    s = thf + thr                       # exact Q addition
    print(f"H[{i},{j}]: theta_fwd={float(thf):+.8f}  theta_rev={float(thr):+.8f}  "
          f"sum={float(s):+.2e}  (modulus equal: r_fwd={float(ac.sqrt(Qi(Q.from_float(Hf[i,j].real),Q.from_float(Hf[i,j].imag)).norm_sq())):.6f})")

print()
print("=== eigenvector component polar read (complex eigenpair = nav signature) ===")
eigvals_f, Vf = lap.hermitian_eigendecompose(Hf)
eigvals_r, Vr = lap.hermitian_eigendecompose(Hr)
print("forward eigenvalues :", [round(float(eigvals_f[k]), 6) for k in range(n)])
print("reversed eigenvalues:", [round(float(eigvals_r[k]), 6) for k in range(n)])
print("(eigenvalues are real + identical: reversal is a UNITARY/gauge flip, not a spectral change)")
print()
# pick a complex eigenvector component and polar-read it (forward vs reversed)
print("eigenvector component V[i, k] polar read (a component with nonzero phase):")
for k in range(n):
    for i in range(n):
        zf = Vf[i, k]
        rf, thf = polar_of_complex(zf)
        # find reversed counterpart same slot
        zr = Vr[i, k]
        rr, thr = polar_of_complex(zr)
        if kmag(zf.imag) > 1e-9:   # display-only guard (Class-K magnitude, not abs)
            print(f"V[{i},{k}]: fwd=({zf.real:+.4f},{zf.imag:+.4f}) "
                  f"r={float(rf):.6f} theta={float(thf):+.6f} | "
                  f"rev=({zr.real:+.4f},{zr.imag:+.4f}) theta={float(thr):+.6f}")
            break
# ===== qarg_api.py =====
"""Proposed srmech carrier polar-read API: Qi.modulus / Qi.arg / Qi.as_polar.

Minimal, exact, numpy-free. Built ENTIRELY from ops already shipped in
srmech.asymptotic_calculus:
  - modulus  : sqrt(self.norm_sq())     # norm_sq() already exact Q on the carrier
  - arg      : atan2(self.imag, self.real)   # exact Q, full-circle quadrant logic
  - as_polar : (modulus, arg)
  - from_polar (classmethod): r*cos(theta), r*sin(theta)   # exact cos/sin series

No new transcendental code needed — these are thin accessors over the existing
exact Class-N cascade. Closes harmonics open rungs Class C (arg=direction) and
Class K (modulus=pin-slot magnitude).
"""
import srmech.asymptotic_calculus as ac
from srmech.amsc.qi import Qi
from srmech.amsc.q import Q


# ---- proposed methods (monkeypatched here to prove they compose; in srmech
#      these would be methods on the Qi class in srmech/amsc/qi.py) ----
def _modulus(self) -> Q:
    """r = |z|, exact Q (Class K pin-slot magnitude). sqrt of the carrier's
    own exact norm_sq()."""
    return ac.sqrt(self.norm_sq())


def _arg(self) -> Q:
    """theta = arg(z) in (-pi, pi], exact Q (Class C direction via atan2
    quadrant logic; sign handling is Class-K/C, not abs)."""
    return ac.atan2(self.imag, self.real)


def _as_polar(self):
    """(r, theta) both exact Q."""
    return self.modulus(), self.arg()


@classmethod
def _from_polar(cls, r: Q, theta: Q) -> "Qi":
    """Inverse: build Qi from (r, theta) via exact cos/sin series."""
    c = ac.cos(theta)
    s = ac.sin(theta)
    return cls(Q(r.numerator * c.numerator, r.denominator * c.denominator),
               Q(r.numerator * s.numerator, r.denominator * s.denominator))


Qi.modulus = _modulus
Qi.arg = _arg
Qi.as_polar = _as_polar
Qi.from_polar = _from_polar

# ---- integration test ----
print("=== proposed Qi polar API (integration test) ===")
for re, im in [(3, 4), (-3, 4), (-3, -4), (3, -4), (0, 5), (-5, 0)]:
    z = Qi(Q(re, 1), Q(im, 1))
    r = z.modulus()
    th = z.arg()
    z2 = Qi.from_polar(r, th)
    res = float(ac.hypot(float(z.real) - float(z2.real),
                         float(z.imag) - float(z2.imag)))
    print(f"Qi({re:+},{im:+}i).as_polar() = (r={float(r):.6f}, theta={float(th):+.8f})  "
          f"from_polar round-trip residual={res:.2e}")

print()
print("as_polar() returns exact Q pair:", [type(x).__name__ for x in Qi(Q(3,1),Q(4,1)).as_polar()])
