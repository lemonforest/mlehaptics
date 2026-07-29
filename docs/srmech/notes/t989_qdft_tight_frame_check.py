"""`#T989` — the F683 tight-frame / Parseval claim, decided.

MFO §XIV.7 [F683] asserts ``<X_a, X_b> = N * <a, b>`` (equivalently ``G* G = N*I``)
and MFO §VIII.31.19 item 7 carried it as **UNCONFIRMED**, on the grounds that
"whether that 14-operator basis is literally ``G`` could not be established".

That question was MIS-POSED, and the conflation was the whole difficulty:

  * item 7's ``G`` is ``one.py``'s ``to_matrix()`` CARRIER frame (14x14; ``G* G``
    exactly diagonal, approximately ``I``);
  * F683's ``G`` is the length-``N`` QDFT TWIDDLE matrix of
    ``srmech.amsc.cascade.quaternion_dft``, with ``N = 14`` the operator count
    used as a TRANSFORM LENGTH.

They are different objects, so ``G* G = N*I`` (F683) and ``G* G ~ I`` (item 7)
were never in tension. This script supplies both receipts.

  A. EXACT   -- integer-only proof that ``G* G = N*I`` for the length-N
                unnormalised DFT twiddle. No float anywhere in this half.
  B. MEASURED -- the SHIPPED ``quaternion_dft`` at N = 14, both forms, four
                mu-axes.

Discipline: no numpy, no fractions, no float in half A. Sign handling is Class K
(pin-slot at zero) + Class C (re-application) via ``cascade.magnitude`` -- never
Python ``abs()`` (`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`).
Class-I ``gcd`` is srmech's own (`[[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_invisible]]`).

Run:  PYTHONPATH=docs/srmech/python python docs/srmech/notes/t989_qdft_tight_frame_check.py
"""
from srmech.amsc.cyclic import gcd                       # Class I
from srmech.amsc.cascade import magnitude, quaternion_dft

N = 14   # the 14 A-N operators, used as the transform length


# ───────────────────────────────────────────────────────────── A. EXACT
def exact_twiddle_gram(n):
    """(G* G)_{ab} = sum_k conj(w^{ka}) w^{kb} = sum_k w^{k*m},  m = (b-a) mod n.

    Decided with integers only. The exponent histogram of {k*m mod n} is
    supported on the subgroup <g>, g = gcd(m, n); descending to
    Z[y]/(y^{n'} - 1) with y = x^g, the reduced vector is g*(all-ones), which
    (y - 1) annihilates exactly. zeta = w^g is a PRIMITIVE n'-th root, so
    zeta != 1 exactly when n' > 1, and (zeta - 1)*S = zeta^{n'} - 1 = 0 forces
    S = 0. For m = 0 every exponent is 0 and the sum is n.
    """
    rows = []
    for m in range(n):
        hist = [0] * n
        for k in range(n):
            hist[(k * m) % n] += 1

        g = gcd(m, n)
        n_prime = n // g

        structural_ok = all(hist[j] == (g if j % g == 0 else 0) for j in range(n))
        reduced = [hist[(t * g) % n] for t in range(n_prime)]
        reduced_uniform = all(c == g for c in reduced)
        shifted = [reduced[(t - 1) % n_prime] for t in range(n_prime)]     # y * reduced
        annihilated = [shifted[t] - reduced[t] for t in range(n_prime)]    # (y-1) * reduced
        is_zero_vec = all(c == 0 for c in annihilated)
        zeta_is_not_one = n_prime > 1

        if m == 0:
            value = n
        elif structural_ok and reduced_uniform and is_zero_vec and zeta_is_not_one:
            value = 0
        else:
            value = None                                   # undecided -> loud
        rows.append((m, g, n_prime, structural_ok, is_zero_vec, value))
    return rows


# ────────────────────────────────────────────────────────── B. MEASURED
def rinner(u, v):
    """Real inner product on H^N == R^{4N}."""
    return sum(uc * vc for us, vs in zip(u, v) for uc, vc in zip(us, vs))


def qseq(seed, n):
    """Deterministic integer-valued quaternion samples (no RNG dependency)."""
    out, s = [], seed
    for _ in range(n):
        s = (s * 1103515245 + 12345) % 2147483648
        out.append([float((s >> (8 * c)) % 17 - 8) for c in range(4)])
    return out


def main():
    print("=== A. EXACT integer proof of  G* G = N*I,  N =", N, "===")
    print("  m   g   N'   hist = g*coset   (y-1)*reduced == 0   (G* G) entry")
    rows = exact_twiddle_gram(N)
    for m, g, n_prime, s_ok, z_ok, value in rows:
        print(f" {m:2d}  {g:2d}  {n_prime:3d}        {str(s_ok):5s}"
              f"               {str(z_ok):5s}            {value}")
    diag_ok = all(r[5] == N for r in rows if r[0] == 0)
    off_ok = all(r[5] == 0 for r in rows if r[0] != 0)
    print()
    print("  diagonal (m=0) entries == N :", diag_ok)
    print("  off-diagonal entries == 0   :", off_ok)
    print("  => G* G == N * I  (EXACT, integer, 14/14 residues):", diag_ok and off_ok)

    print()
    print("=== B. MEASURED on the shipped quaternion_dft, N =", N, "===")
    worst, n_cases = 0.0, 0
    for form in ("left", "right"):
        for mu in ("i", "j", "k", "diagonal"):
            for sa, sb in ((1, 2), (7, 11), (99, 100), (5, 5)):
                a, b = qseq(sa, N), qseq(sb, N)
                Xa = quaternion_dft(a, form=form, mu_axis=mu)
                Xb = quaternion_dft(b, form=form, mu_axis=mu)
                lhs, rhs = rinner(Xa, Xb), N * rinner(a, b)
                dev = magnitude(lhs - rhs)          # Class K pin + Class C re-apply
                scale = magnitude(rhs)
                rel = dev / scale if scale > 0.0 else dev
                worst = rel if rel > worst else worst
                n_cases += 1
    print(f"  cases: {n_cases}  (2 forms x 4 mu-axes x 4 sample pairs)")
    print(f"  worst relative deviation: {worst:.3e}")
    print("  <X_a,X_b> / <a,b> == N == 14 :", worst < 1e-12)
    print()
    print("  cross-check: the identity is already SSoT'd in code at")
    print("  srmech/amsc/cascade/hypercomplex_dft.py:639-640 --")
    print('  "Parseval (this convention, forward unscaled): sum_k ||X[k]||^2 =')
    print('   N*sum_n ||x[n]||^2 for both one-sided forms."')


if __name__ == "__main__":
    main()
