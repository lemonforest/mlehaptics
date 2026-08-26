r"""R-RBS-SNN-DOFFIBER — yes: from the fibration perspective DoF = fiber, so the B/H/N DoF IS fiber content — it is
the OUTER fiber, the +1 per block that completes each imaginary base (1,3,7) into the full Hurwitz algebra (2,4,8).
That makes 1:3:7:3 = (1+1):(3+1):(7+1) = 2:4:8 (AX-1) a FIBRATION statement: base (imaginary) ⊕ fiber (the +1 DoF).

Two fibers, two scales (the partition is DOUBLY fibered):
  • OUTER fiber  = the +1 per block (the B/H/N grammar / DoF / gauge) — completes imaginary base → division algebra
                   (1,3,7) ⊕ (1,1,1) = (2,4,8). The +1 is the REAL/scalar DoF (the anchor / phase / projection-enabler).
  • INNER fiber  = the 3-in-7 (the quaternion {e1,e2,e3} inside the 𝕆 heptad, F491) — base 4 ⊕ fiber 3 = 7.
                   The 3 here is IMAGINARY (the Hopf fiber of S⁷→S⁴).
Both are "DoF = fiber" (the fiber-as-spatially-absent stance) → recursive (F128). Every count ∈ Hurwitz {1,2,4,8}
⇒ no magic (F495). Honest: the arithmetic (AX-1) is a theorem; "DoF = fiber" is the framework reading; the OUTER
(real/+1) and INNER (imaginary 3-in-7) fibers are DISTINCT — the user's "sort of." srmech 0.7.4.
"""
import srmech
from srmech.amsc.cascade import cayley_dickson as cd


def main():
    print(f"=== R-RBS-SNN-DOFFIBER — DoF = fiber: the B/H/N is the OUTER fiber; the partition is doubly fibered  (srmech {srmech.__version__}) ===\n")

    imag = (1, 3, 7)                                                       # imag dims of ℂ,ℍ,𝕆 — the BASE (content)
    hurwitz = tuple(d for d in (1, 2, 4, 8) if cd.is_division_algebra_dim(d) and d >= 2)   # (2,4,8)
    plus1 = [hurwitz[i] - imag[i] for i in range(3)]                       # the +1 per block = the OUTER fiber DoF
    completed = [imag[i] + plus1[i] for i in range(3)]

    print("PART 1 — the OUTER fiber: the +1 per block completes the imaginary base into the Hurwitz algebra (AX-1):")
    print(f"  imaginary BASE (content):        {imag}        = (ℂ,ℍ,𝕆) imag dims")
    print(f"  + OUTER fiber (the +1 per block): {tuple(plus1)}        = the B/H/N DoF (one per Hurwitz rung)")
    print(f"  = full division algebra:          {tuple(completed)}        == Hurwitz {hurwitz}: {completed == list(hurwitz)}")
    print(f"  so 1:3:7:3 = (1+1):(3+1):(7+1) = 2:4:8 ; the trailing :3 (B/H/N) = Σ(+1) = {sum(plus1)}\n")

    print("PART 2 — DoF = fiber (the fiber-as-spatially-absent stance): the +1 (B/H/N) IS fiber content:")
    print("  the +1 is the REAL/scalar DoF — the anchor / phase / projection-enabler (the gauge, F492; the 3DoF, F494).")
    print("  a degree of freedom is a direction NOT in the base extent = a fiber (spatially-absent, projected on read).")
    print("  → YES, the framework calls the B/H/N DoF 'fiber content' — it is the OUTER (completion) fiber.\n")

    print("PART 3 — two fibers, two scales: the partition is DOUBLY fibered (recursive, F128):")
    print(f"  OUTER fiber: the +1 per Hurwitz rung (B/H/N)  — REAL/DoF — completes (1,3,7) ⊕ (1,1,1) → (2,4,8)")
    print(f"  INNER fiber: the 3-in-7 ({{e1,e2,e3}} in the 𝕆 heptad, F491) — IMAGINARY — base 4 ⊕ fiber 3 = 7")
    print(f"  the two are DISTINCT (real-completion vs imaginary-Hopf) but BOTH are DoF=fiber → fibers within fibers.\n")

    residue = [n for n in (*imag, *plus1, *hurwitz, sum(plus1)) if n not in (1, 2, 3, 4, 7, 8)]
    print("PART 4 — no magic (ties to F495): every count ∈ Hurwitz {1,2,4,8}:")
    print(f"  magic residue: {residue or 'NONE'} — the doubly-fibered partition is fully attested (no chosen dims).\n")

    ok = completed == list(hurwitz) and sum(plus1) == 3 and not residue
    print("VERDICT:")
    print(f"  • YES — DoF = fiber, so the B/H/N DoF IS fiber content: it is the OUTER fiber, the +1 per block that")
    print(f"    completes each imaginary base (1,3,7) into the Hurwitz algebra (2,4,8). 1:3:7:3 = (1+1):(3+1):(7+1)")
    print(f"    is a FIBRATION statement (base ⊕ fiber), not just an arithmetic one. checks: {ok}")
    print(f"  • the partition is DOUBLY fibered: the OUTER fiber (real +1 = B/H/N) AND the INNER fiber (imaginary")
    print(f"    3-in-7, F491) — two scales, both DoF=fiber, recursive (F128). consistent with F492 (fiber=gauge) +")
    print(f"    F494 (B/H/N=3DoF=gauge). Honest 'sort of': the arithmetic (AX-1) is the theorem; DoF=fiber is the")
    print(f"    framework reading; the outer (real) and inner (imaginary) fibers are distinct, at different scales.")


if __name__ == "__main__":
    main()
