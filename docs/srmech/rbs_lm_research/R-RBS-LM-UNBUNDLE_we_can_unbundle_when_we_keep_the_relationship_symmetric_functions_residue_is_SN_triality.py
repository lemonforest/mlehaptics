r"""R-RBS-LM-UNBUNDLE (F822) — "why do we say we can't unbundle?" Because we keep only the BUNDLE (e₁ = the sum /
superposition) and THROW AWAY the relationship. The user is right: keep the relationship and we CAN unbundle, and the
residual ambiguity is a TRIALITY.

The math (Newton / Vieta — elementary symmetric polynomials):
  bundle    e₁ = a + b              (the sum / superposition — ONE equation, N unknowns -> underdetermined)
  bind      e₂ = a · b              (the pairwise product — the RELATIONSHIP we'd been discarding)
  triple    e₃ = a · b · c          (the 3-way bind)
The full tuple (e₁,…,e_N) is a COMPLETE invariant of the multiset {a₁,…,a_N}: the aᵢ are exactly the roots of
  xᴺ − e₁xᴺ⁻¹ + e₂xᴺ⁻² − … ± e_N .
So "unbundle" = recover the operands from (bundle + all the binds). It is SOLVABLE; the only thing left undetermined
is the ORDERING — the permutation group S_N. For N=2 that residue is Z₂ (the swap); for N=3 it is S₃ — and S₃ is
EXACTLY the triality group: Aut(V₄)=S₃, the carrier of the so(8) triality 8v→8s→8c (srmech `klein4_triality_cycle`,
the order-3 generator; `qm.triality`). "If only the math would support it as a triality" — it does, at k=3.

So the F806 "a global bundle overflows / can't be read back" wall is NOT that superposition is fundamentally lossy —
it is that we kept only e₁. Keep the symmetric tower (bundle + binds) and the bundle is invertible UP TO S_N. This is
the same family as F821 unbind/deconvolution (recover ONE operand from the bind + the other); unbundle is its N-ary
sibling (recover ALL operands from the bundle + the binds).

Two realisations, by substrate:
  * FIELD / phasor (ℂ per component — polar HDC): Vieta is exact (roots always exist in ℂ). The clean "answer right
    in front of us." (Shown here on ℚ with chosen exact roots.)
  * GROUP / Klein-4 (Z₂×Z₂ — not a field, no Vieta): the framework instead keeps the order-3 triality ORBIT
    [v, Tv, T²v] and recovers by 2-of-3 majority — `klein4_triality_encode`/`klein4_triality_correct` (shipped rc170).
    Same k=3 structure (S₃), different mechanism for the non-field carrier.

srmech 0.7.5rc170 (TestPyPI, verified clean). No abs(); no CAD. Composes F806/F808 (the bundle wall + context-recall),
F821 (unbind = the 1-operand sibling), F291 (triality = k=3 error-correction), F124/F129 (Hurwitz/Hopf 1/2/4/8).
"""
from srmech.amsc import hdc


def _isqrt(n):
    r = int(n ** 0.5)
    while r * r > n:
        r -= 1
    while (r + 1) * (r + 1) <= n:
        r += 1
    return r


def unbundle_via_symmetric_functions():
    """Recover the operand MULTISET from the bundle (e₁) + the binds (e₂,…) — exact; residue = S_N permutation."""
    print("== bundle e₁ ALONE is underdetermined (this is 'can't unbundle') ==")
    print("   a+b=5 fits (1,4),(2,3),(0,5),…  — 1 equation, 2 unknowns; the missing datum is the bind e₂=a·b\n")
    print("== keep the bind too -> UNBUNDLE solves (Vieta); residue = the ordering = S_N ==")
    a, b = 2, 3
    e1, e2 = a + b, a * b
    d = _isqrt(e1 * e1 - 4 * e2)
    pair = sorted({(e1 - d) // 2, (e1 + d) // 2})
    print(f"   N=2: bundle e₁={e1}, bind e₂={e2} -> multiset {pair}   (residue Z₂ = swap)")
    a, b, c = 1, 2, 3
    e1, e2, e3 = a + b + c, a * b + a * c + b * c, a * b * c
    triple = sorted(d for d in range(-e3 - 1, e3 + 2) if d ** 3 - e1 * d * d + e2 * d - e3 == 0)
    print(f"   N=3: bundle e₁={e1}, binds e₂={e2}, triple e₃={e3} -> multiset {triple}   (residue S₃ = TRIALITY)")
    print("        all 3!=6 orderings share the SAME (e₁,e₂,e₃) — the ambiguity IS S₃\n")


def triality_is_the_SN_resolver_klein4():
    """Klein-4 (a GROUP, no Vieta): the k=3 recovery is the triality ORBIT + 2-of-3 majority — shipped rc170."""
    from srmech.amsc.format import sha256_raw                  # Class-A content hash (not bare hashlib)
    seed = lambda s: int.from_bytes(sha256_raw(s.encode())[:8], "big")
    print("== Klein-4 carrier: S₃/triality recovery is already in srmech (rc170) ==")
    v = hdc.klein4_random(64, seed=seed("v"))
    T = hdc.klein4_triality_cycle
    print(f"   klein4_triality_cycle is order-3 (T³==I)? {T(T(T(v))) == v}   (the S₃ order-3 generator, Aut(V₄))")
    rec = hdc.klein4_triality_correct(hdc.klein4_triality_encode(v))
    print(f"   triality orbit [v,Tv,T²v] -> 2-of-3 correct round-trips to v? {rec == v}   (k=3 recovery, F291)")
    a = hdc.klein4_random(64, seed=seed("a"))
    b = hdc.klein4_random(64, seed=seed("b"))
    bun = hdc.klein4_bundle(a, b)
    print(f"   plain klein4_bundle(a,b) of two distinct -> sim a={hdc.klein4_similarity(bun, a):.2f} "
          f"b={hdc.klein4_similarity(bun, b):.2f}  (e₁ alone ≈ chance: NOT unbundle-able)")


def main():
    import srmech
    print(f"=== R-RBS-LM-UNBUNDLE — we CAN unbundle when we keep the relationship; the residue is S_N (=triality at "
          f"k=3) (srmech {srmech.__version__}) ===\n")
    unbundle_via_symmetric_functions()
    triality_is_the_SN_resolver_klein4()


if __name__ == "__main__":
    main()
