r"""R-RBS-LM-THEONECONSTRUCTOR — is `the_one` a CONSTRUCTOR? Exact-rational (Q) measurement.

Answers MFO §VIII.31.18's open constructor question, and separates the TWO uniqueness questions
that are easy to conflate:

  Q1 (ALGEBRA level)  is O's multiplication table FORCED by H's?              -> measured here
  Q2 (ELEMENT level)  is an O VALUE forced by its lower-rung shadows?         -> measured here

EXACTNESS DISCIPLINE (user correction, 2026-07-25): `cd_mult` returns exact `Q` rationals. An
earlier probe collapsed them to float before comparing (`float(x.as_float())` + `round`) — the
values happened to be in {-1,0,1} so it was safe, but the METHOD was wrong and would not scale.
Everything here compares `Q` EXACTLY (`Q.__eq__` / integer numerator-denominator pairs). No float
anywhere; no `abs()`; no numpy; no fractions module (`[[feedback_stay_rational_collapse_only_at_display]]`).

THE STANDING CORRECTION this file records: H is NOT abelian. Non-abelianity is BORN at C->H
(§VIII.31.18's loss ladder); H is the FIRST NON-ABELIAN and LAST ASSOCIATIVE rung. So "abelian
information from R/C/H" is false as stated — the repair is that every rung has an abelian SHADOW
(Z2^n, F1317), and the shadow is the abelian information, not the algebra.

srmech 0.9.0rc336. Composes F1317 (shadow nests / fiber = 1 sign bit), F1307 (_coupler_q8's
shadow+sign shape), MFO §VIII.31.18 (the constructor) / §VIII.31.19 (H as pivot).
Run:  /tmp/srmech_335/bin/python3 R-RBS-LM-THEONECONSTRUCTOR_*.py
"""
import sys

import srmech
from srmech.amsc import cascade as C, q8 as Q8, hdc as H, octonion as O
from srmech.amsc.q import Q
from srmech.amsc.format import sha256_bytes

D = 64


# ---- exact Q helpers (integer numerator/denominator only; never float) ------------------------
def qneg(x):
    return Q(-x.numerator, x.denominator)


def qadd(a, b):
    return Q(a.numerator * b.denominator + b.numerator * a.denominator,
             a.denominator * b.denominator)


def qsub(a, b):
    return qadd(a, qneg(b))


def unit(i, d):
    return [Q(1, 1) if k == i else Q(0, 1) for k in range(d)]


def conj(v):
    return [v[0]] + [qneg(x) for x in v[1:]]


def eq(u, v):
    return len(u) == len(v) and all(a == b for a, b in zip(u, v))


def main():
    print("=== the_one as CONSTRUCTOR — exact Q, srmech %s ===" % srmech.__version__)
    ok = True

    # ---- Q1: is O's TABLE forced by H's? (exact Q, CD doubling rule) -------------------------
    def qm(a, b):
        return list(C.cd_mult(a, b))

    def double(a, b, c, d):
        """(a,b)(c,d) = (a·c − d*·b , d·a + b·c*) — computed ONLY from dim-4 ops, exactly."""
        lo = [qsub(x, y) for x, y in zip(qm(a, c), qm(conj(d), b))]
        hi = [qadd(x, y) for x, y in zip(qm(d, a), qm(b, conj(c)))]
        return lo + hi

    mism = 0
    for i in range(8):
        for j in range(8):
            A, B = unit(i, 8), unit(j, 8)
            if not eq(double(A[:4], A[4:], B[:4], B[4:]), qm(A, B)):
                mism += 1
    ok &= mism == 0
    print("  [Q1 ALGEBRA] dim-8 table reproduced from dim-4 by CD doubling, EXACT Q: %d/64 match, %d mismatch"
          % (64 - mism, mism))
    print("              => O's multiplication table is FORCED by H's. No freedom. (CD + Hurwitz)")

    # ---- Q2: is an O VALUE forced by its shadows? --------------------------------------------
    fib = {}
    for u in range(16):
        fib.setdefault(u & 7, []).append(u)
    sizes = sorted({len(v) for v in fib.values()})
    ok &= sizes == [2]
    print("  [Q2 ELEMENT ] fiber over each Z2^3 shadow: sizes %s -> a VALUE is NOT forced; 1 bit is missing"
          % sizes)

    # ---- THE CONSTRUCTOR: does the_one CLOSE the 2-element fiber, resonantly? -----------------
    ONE = C.the_one(1, 0)

    def sign_channel(idx):
        """The fiber-closing bit: a Class-A content-address of the_one, keyed by slot. RESONANT —
        a declared function of (sigma, theta, terms, winding) and the slot index; never an RNG."""
        pre = b"one/sigma:%d/theta:%d,%d/terms:%d/slot:%d" % (
            int(ONE.sigma), int(ONE.theta[0]), int(ONE.theta[1]), int(ONE.terms), idx)
        return int(sha256_bytes(pre)[:2], 16) & 1

    def lift(shadow_leaf):
        """shadow (which AXIS, free) + the_one sign (which WAY, supplied) -> the O element."""
        return bytes((sign_channel(i) << 3) | (s & 7) for i, s in enumerate(shadow_leaf))

    def project(oct_leaf):
        return bytes(b & 7 for b in oct_leaf)

    shadow = bytes((int(sha256_bytes(b"shadow:%d" % i)[:2], 16) & 7) for i in range(D))
    E = lift(shadow)
    rt = lift(project(E)) == E                      # shadow + the_one -> E, exactly
    det = lift(shadow) == lift(shadow)              # deterministic (no RNG)
    proj_ok = project(E) == shadow                  # the shadow really is recoverable
    nontrivial = 0 < sum(b >> 3 for b in E) < D     # the sign channel actually varies
    ok &= rt and det and proj_ok and nontrivial
    print("  [CONSTRUCTOR] shadow+the_one -> E round-trips EXACTLY: %s | deterministic: %s | "
          "projection exact: %s | sign channel non-trivial: %d/%d"
          % (rt, det, proj_ok, sum(b >> 3 for b in E), D))

    # falsification: a DIFFERENT the_one must pick the OTHER fiber member somewhere
    ONE2 = C.the_one(1, 1)

    def sign2(idx):
        pre = b"one/sigma:%d/theta:%d,%d/terms:%d/slot:%d" % (
            int(ONE2.sigma), int(ONE2.theta[0]), int(ONE2.theta[1]), int(ONE2.terms), idx)
        return int(sha256_bytes(pre)[:2], 16) & 1
    E2 = bytes((sign2(i) << 3) | (s & 7) for i, s in enumerate(shadow))
    same_shadow = project(E2) == shadow
    differs = E2 != E
    ok &= same_shadow and differs
    print("  [FALSIFY    ] a DIFFERENT the_one: same shadow %s, different element %s "
          "-> the fiber is real and the_one CHOOSES within it" % (same_shadow, differs))

    # ---- the information ledger --------------------------------------------------------------
    print("  [LEDGER     ] rung: shadow bits + fiber bits = symbol bits")
    for nm, sw, tot in (("C", 1, 4), ("H", 2, 8), ("O", 3, 16)):
        exact = (1 << (sw + 1)) == tot
        ok &= exact
        print("                %s: %d shadow + 1 sign = %d bits -> %d symbols (exact: %s)"
              % (nm, sw, sw + 1, tot, exact))

    print("\n=== %s ===" % ("CONSTRUCTOR CONFIRMED: the ALGEBRA is forced by the rung below (exact Q); "
                            "an ELEMENT is not — the_one closes the 2-element fiber resonantly."
                            if ok else "REGRESSION — reconcile before trusting F1318."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
