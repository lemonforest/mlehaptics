"""loop_bind_algebraic_laws_F291_bugtest.py — deep bug-test of the rc2 native loop-bind surface
against the MODEL-INDEPENDENT algebraic laws an octonion product / G2 structure MUST satisfy.

Complement to the F291 workflow legs: those check consistency (native == oracle), but the oracle
could share a bug with native. THESE are the laws themselves (composition-algebra ground truth) — if
native passes them, the shipped op IS a genuine octonion product, independent of any reference impl.

Laws checked on srmech.amsc.hdc.{loop_bind, loop_conj, cross7, g2_three_form}:
  1. identity      e0 (x) x = x (x) e0 = x
  2. units^2 = -e0   e_i (x) e_i = -e0,  i = 1..7
  3. anticommute   e_i (x) e_j = -(e_j (x) e_i),  i != j in 1..7
  4. norm mult.    N(xy) = N(x) N(y)         (composition algebra; Class-K Born norm^2, NO abs)
  5. conjugate     conj(x) (x) x = N(x) e0    (real, = norm^2 anchor)
  6. alternativity  x(xy) = (xx)y  and  (yx)x = y(xx)   (associator alternates -> vanishes on repeats)
  7. Moufang       (x(yx))z = x(y(xz))        (the loop's defining identity)
  8. associator antisymmetry  [x,y,z] = -[y,x,z] = -[x,z,y]   (totally antisymmetric)
  9. NON-assoc     exists triple with [x,y,z] != 0   (genuinely octonionic, not an associative impostor)
 10. cross7        cross7(x,y) = Im(loop_bind(x,y)) on imaginaries; antisymmetric; orthogonal to x,y
 11. G2 3-form     g2(x,y,z) = <x, cross7(y,z)>; totally antisymmetric
 12. L != R        left-mult != right-mult (the (4:3)|(3:4) chirality)

Class-K clean: magnitudes are Born inner products (re^2+im^2 = np.dot(v,v)); NEVER abs(). srmech-first.
Scope: algebra only; benign; no CAD/MD/clinical. Bug-test record for the 'we are bug-testing srmech' directive.
"""
import os
import sys

import numpy as np

RESEARCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RESEARCH)
from srmech.amsc import hdc  # noqa: E402  native rc2

rng = np.random.default_rng(291)  # seed attested (B)
E0 = np.zeros(8); E0[0] = 1.0


def e(i):
    v = np.zeros(8); v[i] = 1.0
    return v


def n2(v):
    """Born norm^2 = <v|v> = sum re^2+im^2 (Class-K; NOT abs)."""
    return float(np.dot(v, v))


def rand_oct():
    return rng.standard_normal(8)


def rand_imag():
    v = rng.standard_normal(8); v[0] = 0.0
    return v


def report(name, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")
    return ok


def main():
    lb = hdc.loop_bind
    results = []
    print("=== rc2 native loop-bind: algebraic-law bug-test (model-independent ground truth) ===\n")

    # surface presence (bug-test: report missing ops, do not crash)
    has_conj = hasattr(hdc, "loop_conj")
    has_cross7 = hasattr(hdc, "cross7")
    has_g2 = hasattr(hdc, "g2_three_form")
    print(f"  surface: loop_conj={has_conj}  cross7={has_cross7}  g2_three_form={has_g2}\n")

    # 1. identity
    ok = all(np.allclose(lb(E0, x), x) and np.allclose(lb(x, E0), x)
             for x in (rand_oct() for _ in range(20)))
    results.append(report("1  identity  e0(x)x = x(x)e0 = x", ok))

    # 2. e_i^2 = -e0
    ok = all(np.allclose(lb(e(i), e(i)), -E0) for i in range(1, 8))
    results.append(report("2  e_i (x) e_i = -e0  (i=1..7)", ok))

    # 3. anticommutativity on distinct imaginary units
    ok = all(np.allclose(lb(e(i), e(j)), -lb(e(j), e(i)))
             for i in range(1, 8) for j in range(1, 8) if i != j)
    results.append(report("3  e_i (x) e_j = -(e_j (x) e_i)  i!=j", ok))

    # 4. norm multiplicativity  N(xy) = N(x)N(y)  -- the composition-algebra law
    #    (squared residual = Born-clean; NO abs)
    errs = []
    for _ in range(2000):
        x, y = rand_oct(), rand_oct()
        errs.append((n2(lb(x, y)) - n2(x) * n2(y)) ** 2)
    ok = max(errs) < 1e-12
    results.append(report("4  N(xy) = N(x)N(y)  (composition algebra)", ok, f"max resid^2={max(errs):.2e}"))

    # 5. conjugate: conj(x)(x)x = N(x) e0
    if has_conj:
        errs = []
        for _ in range(500):
            x = rand_oct()
            errs.append(float(np.linalg.norm(lb(hdc.loop_conj(x), x) - n2(x) * E0)))
        ok = max(errs) < 1e-9
        results.append(report("5  conj(x)(x)x = N(x) e0", ok, f"max err={max(errs):.2e}"))
    else:
        results.append(report("5  conj law", False, "loop_conj MISSING"))

    # 6. alternativity: x(xy) = (xx)y  and  (yx)x = y(xx)
    errs = []
    for _ in range(500):
        x, y = rand_oct(), rand_oct()
        errs.append(float(np.linalg.norm(lb(x, lb(x, y)) - lb(lb(x, x), y))))
        errs.append(float(np.linalg.norm(lb(lb(y, x), x) - lb(y, lb(x, x)))))
    ok = max(errs) < 1e-9
    results.append(report("6  alternativity  x(xy)=(xx)y, (yx)x=y(xx)", ok, f"max err={max(errs):.2e}"))

    # 7. Moufang identity  (x(yx))z = x(y(xz))
    errs = []
    for _ in range(500):
        x, y, z = rand_oct(), rand_oct(), rand_oct()
        lhs = lb(lb(x, lb(y, x)), z)
        rhs = lb(x, lb(y, lb(x, z)))
        errs.append(float(np.linalg.norm(lhs - rhs)))
    ok = max(errs) < 1e-9
    results.append(report("7  Moufang  (x(yx))z = x(y(xz))", ok, f"max err={max(errs):.2e}"))

    # 8. associator [x,y,z] = (xy)z - x(yz)  totally antisymmetric
    def assoc(x, y, z):
        return lb(lb(x, y), z) - lb(x, lb(y, z))
    errs = []
    for _ in range(500):
        x, y, z = rand_imag(), rand_imag(), rand_imag()
        errs.append(float(np.linalg.norm(assoc(x, y, z) + assoc(y, x, z))))  # swap 1,2 -> sign flip
        errs.append(float(np.linalg.norm(assoc(x, y, z) + assoc(x, z, y))))  # swap 2,3 -> sign flip
    ok = max(errs) < 1e-9
    results.append(report("8  associator totally antisymmetric", ok, f"max err={max(errs):.2e}"))

    # 9. genuine NON-associativity: some triple has nonzero associator
    big = max(float(np.linalg.norm(assoc(rand_imag(), rand_imag(), rand_imag()))) for _ in range(500))
    ok = big > 1e-3
    results.append(report("9  NON-associative (genuinely octonionic)", ok, f"max|assoc|={big:.3f}"))

    # 10. cross7 = Im(loop_bind) on imaginaries; antisymmetric; orthogonal to args
    if has_cross7:
        errs_im, errs_anti, errs_orth = [], [], []
        for _ in range(500):
            x, y = rand_imag(), rand_imag()
            c = hdc.cross7(x, y)
            im_lb = lb(x, y).copy(); im_lb[0] = 0.0  # Im part
            errs_im.append(float(np.linalg.norm(c - im_lb)))
            errs_anti.append(float(np.linalg.norm(c + hdc.cross7(y, x))))
            errs_orth.append(abs(float(np.dot(c, x))) + abs(float(np.dot(c, y))))  # residuals
        ok = max(errs_im) < 1e-9 and max(errs_anti) < 1e-9 and max(errs_orth) < 1e-9
        results.append(report("10 cross7 = Im(lb), antisym, orthogonal", ok,
                              f"im={max(errs_im):.1e} anti={max(errs_anti):.1e} orth={max(errs_orth):.1e}"))
    else:
        results.append(report("10 cross7 laws", False, "cross7 MISSING"))

    # 11. G2 3-form g2(x,y,z) = <x, cross7(y,z)>, totally antisymmetric
    if has_g2 and has_cross7:
        errs_def, errs_anti = [], []
        for _ in range(500):
            x, y, z = rand_imag(), rand_imag(), rand_imag()
            g = hdc.g2_three_form(x, y, z)
            errs_def.append(abs(g - float(np.dot(x, hdc.cross7(y, z)))))
            errs_anti.append(abs(g + hdc.g2_three_form(y, x, z)))  # swap -> sign flip
        ok = max(errs_def) < 1e-9 and max(errs_anti) < 1e-9
        results.append(report("11 G2 3-form  g2=<x,cross7(y,z)>, antisym", ok,
                              f"def={max(errs_def):.1e} anti={max(errs_anti):.1e}"))
    else:
        results.append(report("11 G2 3-form laws", False, "g2_three_form/cross7 MISSING"))

    # 12. L != R chirality (left-mult vs right-mult differ): (a (x) b) vs (b (x) a) generically differ
    diffs = max(float(np.linalg.norm(lb(a, b) - lb(b, a)))
                for a, b in ((rand_imag(), rand_imag()) for _ in range(500)))
    ok = diffs > 1e-3
    results.append(report("12 L != R  (the (4:3)|(3:4) chirality)", ok, f"max|ab-ba|={diffs:.3f}"))

    # 13-14. Moufang DIVISION (cancellation) laws -- the algebraic GROUND of F290/F291 peelability.
    #   left:  conj(x) (x) (x (x) v) = N(x) v   (alternativity x_bar(xv)=(x_bar x)v=N v)
    #   right: (v (x) x) (x) conj(x) = N(x) v   (alternativity (vx)x_bar = v(x x_bar)=N v)
    # For unit x (N=1) these give EXACT recovery -> the peel/unbind that path-memory relies on.
    if has_conj:
        el, er = [], []
        for _ in range(500):
            x, v = rand_oct(), rand_oct()
            nx = n2(x)
            el.append(float(np.linalg.norm(lb(hdc.loop_conj(x), lb(x, v)) - nx * v)))
            er.append(float(np.linalg.norm(lb(lb(v, x), hdc.loop_conj(x)) - nx * v)))
        ok = max(el) < 1e-9 and max(er) < 1e-9
        results.append(report("13 left-division  conj(x)(x(v)) = N(x) v", max(el) < 1e-9, f"max err={max(el):.2e}"))
        results.append(report("14 right-division ((v)x)conj(x) = N(x) v  [F290 PEEL ground]", max(er) < 1e-9, f"max err={max(er):.2e}"))
    else:
        results.append(report("13 left-division", False, "loop_conj MISSING"))
        results.append(report("14 right-division", False, "loop_conj MISSING"))

    npass = sum(results)
    print(f"\n  === {npass}/{len(results)} algebraic laws PASS ===")
    if npass == len(results):
        print("  rc2 native loop-bind IS a genuine octonion product / G2 structure (model-independent). No bug.")
    else:
        print("  ANOMALY: one or more laws FAILED -> srmech bug to report upstream (UPSTREAM_NOTES).")


if __name__ == "__main__":
    main()
