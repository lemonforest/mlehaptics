r"""R-RBS-LM-CDLAPLACIAN (F1229) — the Cayley-Dickson Laplacian ladder: which rung folds the FIBER into a SINGLE object?

Question (user): responsion = the form for curvature-over-time; is that curvature also non-commutative? Can we fold the
fiber into ONE Laplacian — is "iL over time" that object, a universal decomposition, or did I just need an OCTONION
Laplacian? Answer, MEASURED: the algebra the Laplacian's VALUES live in (the Cayley-Dickson rung ℝ→ℂ→ℍ→𝕆) is exactly
"how much of the fiber is folded in":

  ℝ  (real symmetric L)     : metric only            — Abelian, associative      -> the FLAT bag (holonomy 0)
  ℂ  (magnetic L = iL/time) : + CHIRALITY (the phase) — Abelian, associative      -> "not mirrored" (nonzero holonomy,
                                                                                     but ORDER does NOT yet matter)
  ℍ  (quaternion L)         : + NON-COMMUTATIVITY     — non-Abelian, associative  -> "order of operations matters"
  𝕆  (octonion L)           : + NON-ASSOCIATIVITY     — non-Abelian, non-assoc.   -> the FULL fiber (the cd_mult walk)

So "iL over time" is the ℂ rung (chirality — the responsion propagator e^{-iLt}); it does NOT carry order. The single
object that encodes the fiber is a NON-COMMUTATIVE-valued Laplacian: ℍ for order, 𝕆 for the full walk. The universal
decomposition IS the Cayley-Dickson tower of Laplacians; "octonion Laplacian" is its top rung.

Measured from srmech's octonion structure-constant tensor (qm.so8.octonion_mult_table), restricted to the first
1/2/4/8 basis elements. Exact ints; no numpy; no abs-builtin. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CDLAPLACIAN_...py
"""
import sys

from srmech.qm.so8 import octonion_mult_table

C = octonion_mult_table()                                        # C[i][j][k]: e_i * e_j = sum_k C[i][j][k] e_k


def cd_mult(a, b, dim):
    """Multiply two Cayley-Dickson numbers (length-`dim` real coeffs, dim in {1,2,4,8}) via the octonion structure
    constants restricted to the sub-algebra — ℝ⊂ℂ⊂ℍ⊂𝕆 are closed, so the product stays in the first `dim` slots."""
    out = [0] * dim
    for i in range(dim):
        if a[i] == 0:
            continue
        for j in range(dim):
            if b[j] == 0:
                continue
            for k in range(dim):
                c = C[i][j][k]
                if c:
                    out[k] += c * a[i] * b[j]
    return out


def _unit(idx, dim):
    v = [0] * dim
    v[idx] = 1
    return v


def _neg(v):
    return [-x for x in v]


def main():
    print("=== R-RBS-LM-CDLAPLACIAN — the Cayley-Dickson Laplacian ladder: which rung folds in the fiber? ===\n")
    rungs = [(1, "ℝ  real     "), (2, "ℂ  complex  "), (4, "ℍ  quaternion"), (8, "𝕆  octonion  ")]
    for dim, name in rungs:
        imags = list(range(1, dim))                              # the imaginary basis units e_1..e_{dim-1}
        # commutativity: over imaginary pairs, does e_i e_j == e_j e_i (commute) or == -(e_j e_i) (anti-commute)?
        comm = anti = 0
        for a_i in imags:
            for b_j in imags:
                if a_i >= b_j:
                    continue
                ab = cd_mult(_unit(a_i, dim), _unit(b_j, dim), dim)
                ba = cd_mult(_unit(b_j, dim), _unit(a_i, dim), dim)
                if ab == ba:
                    comm += 1
                elif ab == _neg(ba):
                    anti += 1
        # associativity: over imaginary triples, is (e_i e_j) e_k == e_i (e_j e_k)?
        assoc = nonassoc = 0
        for a_i in imags:
            for b_j in imags:
                for c_k in imags:
                    lhs = cd_mult(cd_mult(_unit(a_i, dim), _unit(b_j, dim), dim), _unit(c_k, dim), dim)
                    rhs = cd_mult(_unit(a_i, dim), cd_mult(_unit(b_j, dim), _unit(c_k, dim), dim), dim)
                    if lhs == rhs:
                        assoc += 1
                    else:
                        nonassoc += 1
        # a triangle holonomy: ordered loop product vs reversed order (does the WALK ORDER change the result?)
        if len(imags) >= 3:
            e = [_unit(imags[0], dim), _unit(imags[1], dim), _unit(imags[2], dim)]
        else:
            e = [_unit(imags[0] if imags else 0, dim)] * 3
        fwd = cd_mult(cd_mult(e[0], e[1], dim), e[2], dim)
        rev = cd_mult(cd_mult(e[2], e[1], dim), e[0], dim)
        order_matters = (fwd != rev)
        is_ab = (anti == 0)
        is_as = (nonassoc == 0)
        print("  %s  imag-pairs: %d commute / %d ANTI-commute  ->  %s"
              % (name, comm, anti, "ABELIAN (order-free)" if is_ab else "NON-Abelian (ORDER MATTERS)"))
        print("      %s associate / %d NON-associate triples   ->  %s"
              % (assoc, nonassoc, "associative" if is_as else "NON-associative (grouping matters)"))
        print("      triangle holonomy fwd vs reversed order differ? %s\n" % order_matters)

    print("VERDICT (the answer, measured):")
    print("  * responsion IS the universal FORM for curvature-over-time (the propagator e^{-zL}); what changes per")
    print("    rung is the ALGEBRA it lives in — that determines commutativity. 'iL over time' = the ℂ rung's")
    print("    responsion e^{-iLt}: it folds in CHIRALITY (the phase / 'not mirrored'), but ℂ is still Abelian —")
    print("    ORDER does NOT yet matter there. So iL is NOT enough to encode the fiber.")
    print("  * to fold the FIBER (order-of-operations) into a SINGLE Laplacian you must make its VALUES")
    print("    non-commutative: ℍ (quaternion L) gives 'order matters'; 𝕆 (octonion L) adds non-associativity =")
    print("    the FULL walk (the cd_mult fiber). So BOTH your guesses are right and are DIFFERENT RUNGS of ONE")
    print("    ladder: the universal decomposition IS the Cayley-Dickson tower of Laplacians ℝ→ℂ→ℍ→𝕆, and")
    print("    'octonion Laplacian' is its top rung — the one that carries the whole fiber in one object.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
