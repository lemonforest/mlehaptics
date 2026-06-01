"""loop_bind_moufang.py — the k=7 "loop bind" (Moufang) operation.

NAME: "Loop bind (Moufang)" — user direction 2026-06-02.
  The k=7-native bind: the Cayley-Dickson / octonion product. Non-commutative AND
  non-associative; left-order (ab)c != right-order a(bc). The chirality the user
  predicted as (4:3)|(3:4).

CLASS-HOME (no new class; 14 A-N held; Class O stays dissolved):
  M (bind) o C (chirality = the left/right ordering) with a Class-K associator
  RESIDUE (the boundary that is zero inside an associative region, nonzero outside).
  STRUCTURE = the Moufang loop of unit octonions = the non-associative rung above
  the group/ring ("loop replaces ring", substrate-vocabulary discipline).

WHAT IT IS (F271/F272): the gauge *arithmetic* triality (a mere automorphism) is
  blind to. srmech has the gauge *symmetry* (klein4_triality_cycle) but NOT this
  product (F271 sec-C / F272 sec-C capability target) -- so the product here is
  hand-rolled numpy (honest), pending a native srmech op if it earns its place.

DISCIPLINE: Class-K clean (zero-tests via inner-product norm^2 <v,v>, never abs();
  no sign-folding). numpy-only. No-magic (DIM, the 7 Fano lines, the identities are
  attested-to-structure; the test seed is attested-B). Commits the F272 numerics
  (computational-provenance discipline) -> run `python loop_bind_moufang.py`.
"""
import itertools
import numpy as np

DIM = 8           # octonion / k=7
TEST_SEED = 12345  # attested-B (reproducibility seed for the Moufang/Mal'cev checks)


def conj(x):
    """Octonion conjugate: negate the imaginary part, keep the real anchor."""
    x = np.asarray(x, dtype=float)
    y = -x.copy()
    y[0] = x[0]
    return y


def loop_bind(x, y):
    """THE LOOP BIND (Moufang) = Cayley-Dickson / octonion product.

    A_{n+1} = A_n (+) A_n*ell, recursing on the (prev, prev) self-pairing (F270).
    Non-commutative + non-associative => left-order != right-order (Class C).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x) // 2
    if n == 0:
        return x * y
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    return np.concatenate([loop_bind(a, c) - loop_bind(conj(d), b),
                           loop_bind(d, a) + loop_bind(b, conj(c))])


def e(i, dim=DIM):
    """Unit basis element e_i (e_0 = real anchor; e_1..e_{dim-1} = imaginary DoF)."""
    v = np.zeros(dim)
    v[i] = 1.0
    return v


def left_op(a):
    """Left-multiplication operator L_a(x) = a*x  (the (4:3) ordering)."""
    return np.column_stack([loop_bind(a, e(k)) for k in range(DIM)])


def right_op(a):
    """Right-multiplication operator R_a(x) = x*a  (the (3:4) mirror ordering)."""
    return np.column_stack([loop_bind(e(k), a) for k in range(DIM)])


def associator(a, b, c):
    """(ab)c - a(bc) = the Class-K RESIDUE of the loop bind.

    Identity: associator(a, x, b) = -([L_a, R_b] applied to x). Zero inside an
    associative (quaternionic) region; nonzero outside = the (4:3)|(3:4) boundary.
    """
    return loop_bind(loop_bind(a, b), c) - loop_bind(a, loop_bind(b, c))


def commutator(a, b):
    """[a, b] = a*b - b*a  (the tangent bracket; Mal'cev, not Lie, at k=7)."""
    return loop_bind(a, b) - loop_bind(b, a)


def normsq(v):
    """Inner-product norm^2 <v,v> -- Class-K clean (no abs(), no sign-op)."""
    return float(np.dot(np.asarray(v, dtype=float), np.asarray(v, dtype=float)))


def is_zero(v, tol=1e-9):
    return normsq(v) < tol


def fano_lines():
    """The associative 3-planes = imaginary triples with zero associator.

    These are the 7 Fano lines = the quaternionic sub-triples (the '3' of (4:3),
    where ordering does NOT matter). The complementary 28 triples are the
    coassociative '4'-content (where ordering DOES matter).
    """
    return [t for t in itertools.combinations(range(1, DIM), 3)
            if is_zero(associator(e(t[0]), e(t[1]), e(t[2])))]


def cross7(a, b):
    """7D cross product = imaginary part of the loop bind on imaginary octonions."""
    p = loop_bind(a, b).copy()
    p[0] = 0.0
    return p


def g2_three_form(a, b, c):
    """G2 calibration 3-form phi(a,b,c) = <a, b x c>.

    phi = +/-1 on an associative 3-plane (a Fano line); |phi| < 1 off it. The
    geometric face of the (4:3) split (associative 3-planes); its Hodge dual *phi
    (the coassociative 4-form) is the '4' face -- left as a forward leg.
    """
    return float(np.dot(np.asarray(a, dtype=float), cross7(b, c)))


# ---------------------------------------------------------------------------
# Self-test: reproduces the F271/F272 numerics (provenance discipline).
# ---------------------------------------------------------------------------
def _selftest():
    rng = np.random.default_rng(TEST_SEED)
    rnd = lambda: rng.standard_normal(DIM)
    checks = []

    # [1] exactly 7 associator-zero triples = the associative 3-planes (Fano lines)
    fl = fano_lines()
    checks.append(("7 associator-zero Fano lines (associative 3-planes)", len(fl) == 7))
    print(f"[1] associator-zero triples: {len(fl)} (expect 7)\n    {fl}")

    # [2] L != R and L != R^T (left/right are distinct mirror operators); and
    #     [L_a, R_b] x == -associator(a, x, b)  (the operational chirality = the residue)
    a, b, x = e(1), e(2), e(4)
    La, Ra = left_op(a), right_op(a)
    lr = left_op(a) @ right_op(b) - right_op(b) @ left_op(a)
    id_ok = np.allclose(lr @ x, -associator(a, x, b))
    distinct = (not np.allclose(La, Ra)) and (not np.allclose(La, Ra.T))
    checks.append(("L != R != R^T", distinct))
    checks.append(("[L_a,R_b] x == -associator(a,x,b)", id_ok))
    print(f"[2] L!=R!=R^T: {distinct}   [L_a,R_b]x == -assoc(a,x,b): {id_ok}")

    # [3] the three Moufang identities (the loop is Moufang) -- hold for all elements
    def moufang_resid():
        z, u, w = rnd(), rnd(), rnd()
        lb = loop_bind
        m1 = lb(z, lb(u, lb(z, w))) - lb(lb(lb(z, u), z), w)            # left
        m2 = lb(u, lb(z, lb(w, z))) - lb(lb(lb(u, z), w), z)            # right
        m3 = lb(lb(u, w), lb(z, u)) - lb(u, lb(lb(w, z), u))            # the Moufang identity
        return max(normsq(m1), normsq(m2), normsq(m3))
    mres = max(moufang_resid() for _ in range(50))
    checks.append(("all 3 Moufang identities hold (<1e-18)", mres < 1e-18))
    print(f"[3] max Moufang residual over 50 random triples: {mres:.2e} (expect ~0)")

    # [4] tangent algebra is Mal'cev, NOT Lie: Jacobi FAILS, Mal'cev HOLDS
    def jac(p, q, r):
        return commutator(commutator(p, q), r) + commutator(commutator(q, r), p) \
            + commutator(commutator(r, p), q)
    jfail = normsq(jac(e(1), e(2), e(4)))                  # nonzero => not Lie
    # Mal'cev identity: J(x, y, x*z) == J(x, y, z) * x
    xs, ys, zs = rnd(), rnd(), rnd()
    mal = jac(xs, ys, loop_bind(xs, zs)) - loop_bind(jac(xs, ys, zs), xs)
    checks.append(("Jacobi FAILS (not a Lie algebra)", jfail > 1e-6))
    checks.append(("Mal'cev identity HOLDS", normsq(mal) < 1e-18))
    print(f"[4] Jacobi residual (expect >0): {jfail:.3f}   Mal'cev residual (expect ~0): {normsq(mal):.2e}")

    # [5] G2 3-form phi calibrates the associative 3-planes (phi=+/-1 on a Fano line)
    t = fl[0]
    phi = g2_three_form(e(t[0]), e(t[1]), e(t[2]))
    checks.append(("phi == +/-1 on a Fano line", abs(abs(phi) - 1.0) < 1e-9))
    print(f"[5] phi{t} = {phi:+.3f} (expect +/-1 on the associative 3-plane)")

    print("\n--- results ---")
    allok = True
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        allok &= ok
    print(f"\n{'ALL PASS' if allok else 'FAILURES PRESENT'}")
    return allok


if __name__ == "__main__":
    import sys
    sys.exit(0 if _selftest() else 1)
