"""F387 — at k=7 (octonion) the chirality is the CONSTRUCTION: 7 = (4:3)|(3:4), a quaternion glued to its
conjugate-dual by Cayley-Dickson doubling; the "|" seam IS where the chirality AND the non-associativity live.

User (2026-06-04): "so then when we do k=7 we need to be doing k=(4:3)|(3:4)? to enforce us to see the chiral
need through notation? should one day be assumed but need notation now."

Reading the octonion structure-constant table (srmech qm.octonion), with H = span{e0,e1,e2,e3}, l = e4,
Hl = {e4,e5,e6,e7} (the Cayley-Dickson double):
  (1) the 7 imaginaries split 3 (the H imaginaries {e1,e2,e3}) + 4 (the doubling Hl {e4..e7}).
  (2) H is an ASSOCIATIVE subalgebra: (e1*e2)*e3 == e1*(e2*e3).
  (3) NON-associativity lives at the "|" seam (cross-terms with l): (e1*e2)*e4 != e1*(e2*e4).
  (4) CHIRALITY: the first triad {e1,e2,e3} and the doubled triad have OPPOSITE handedness (the conjugation
      twist in the doubling) -> a (4:3) and its (3:4) mirror.

So writing k=7 as (4:3)|(3:4) makes the construction visible: a (4:3) and its conjugate-dual, "|"=the
doubling/chirality/non-associativity seam. Notation as a TEACHING scaffold for the F385 chiral-need: one
day this chirality should be KNOWN because it is TAUGHT (canon/curriculum — the cone-of-ignorance pedagogy),
NOT merely assumed; until it is taught, the (4:3)|(3:4) notation enforces seeing it (user: "not assumed,
known as in taught").

srmech-native: qm.octonion.octonion_mult_table (read int8 structure constants; no numpy math, no abs()).
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R29_k7_is_43_chiral_dual_doubling.py
"""
import json
from pathlib import Path
import srmech
from srmech.qm.octonion import octonion_mult_table

HERE = Path(__file__).parent
NM = {0: "1", 1: "i", 2: "j", 3: "k", 4: "l", 5: "il", 6: "jl", 7: "kl"}


def main():
    print(f"F387 k=7 = (4:3)|(3:4) chiral-dual doubling (srmech {srmech.__version__})")
    C = octonion_mult_table().tolist()

    def prod(a, b):
        row = C[a][b]
        ks = [k for k in range(8) if row[k] != 0]
        return (row[ks[0]], ks[0]) if ks else (0, 0)

    def show(a, b):
        s, k = prod(a, b)
        return f"{'+' if s > 0 else '-'}{NM[k]}"

    # (1) 7 = 3 + 4 split: H={e1,e2,e3} closes; e_*l opens the doubling
    print("\n(1) the split 7 = 3 (H imaginaries) + 4 (the doubling Hl):")
    Hclosed = all(prod(a, b)[1] in (0, 1, 2, 3) for a in (1, 2, 3) for b in (1, 2, 3))
    print(f"    H={{i,j,k}} products stay in {{1,i,j,k}}: {Hclosed}   (i*j={show(1,2)}, j*k={show(2,3)}, k*i={show(3,1)})")
    print(f"    i*l={show(1,4)}, j*l={show(2,4)}, k*l={show(3,4)}  -> l lifts {{i,j,k}} into the doubling {{il,jl,kl}}")

    # (2) H is associative
    lhs = prod(prod(1, 2)[1], 3); rhs = prod(1, prod(2, 3)[1])
    # careful: need signed assoc; compute with signs
    def smul(sa, a, sb, b):
        s, k = prod(a, b); return sa * sb * s, k
    s1, k1 = prod(1, 2); a_lhs = smul(s1, k1, 1, 3)
    s2, k2 = prod(2, 3); a_rhs = smul(1, 1, s2, k2); a_rhs = (1 * s2 * prod(1, k2)[0], prod(1, k2)[1])
    H_assoc = a_lhs == a_rhs
    print(f"\n(2) H associative: (i*j)*k = {('+' if a_lhs[0]>0 else '-')}{NM[a_lhs[1]]}, "
          f"i*(j*k) = {('+' if a_rhs[0]>0 else '-')}{NM[a_rhs[1]]}  -> equal: {H_assoc}")

    # (3) non-associativity at the | seam (cross with l = e4)
    s1, k1 = prod(1, 2); b_lhs = (s1 * prod(k1, 4)[0], prod(k1, 4)[1])      # (i*j)*l
    s2, k2 = prod(2, 4); b_rhs = (s2 * prod(1, k2)[0], prod(1, k2)[1])      # i*(j*l)
    seam_nonassoc = b_lhs != b_rhs
    print(f"\n(3) the '|' seam is NON-associative: (i*j)*l = {('+' if b_lhs[0]>0 else '-')}{NM[b_lhs[1]]}, "
          f"i*(j*l) = {('+' if b_rhs[0]>0 else '-')}{NM[b_rhs[1]]}  -> differ: {seam_nonassoc}  (F378 lives here)")

    # (4) chirality: first triad {i,j,k} vs the doubled triad {il,jl,kl} handedness
    print("\n(4) chirality (handedness of the two halves):")
    print(f"    first  triad  i*j  = {show(1,2)} ,  j*k  = {show(2,3)} ,  k*i  = {show(3,1)}")
    print(f"    doubled triad il*jl = {show(5,6)} , jl*kl = {show(6,7)} , kl*il = {show(7,5)}")
    # compare the sign pattern of the doubled triad to the first (same axes -> opposite sign = chiral dual)
    first_signs = [prod(1, 2)[0], prod(2, 3)[0], prod(3, 1)[0]]
    doubled_signs = [prod(5, 6)[0], prod(6, 7)[0], prod(7, 5)[0]]
    chiral_dual = doubled_signs == [-s for s in first_signs]
    print(f"    first-triad signs {first_signs} vs doubled-triad signs {doubled_signs} "
          f"-> opposite handedness (the (3:4) mirror of the (4:3)): {chiral_dual}")

    print("\n=== verdict ===")
    print("  k=7 (octonion) is NOT a flat 7: it is H (+) Hl = a quaternion (4:3) Cayley-Dickson-DOUBLED with a")
    print("  conjugation twist. The 7 splits 3 (H, associative) + 4 (the double); the '|' seam (cross-terms with")
    print("  l) is where BOTH the non-associativity (F378) AND the chirality (F385) live; the doubled triad has")
    print("  the OPPOSITE handedness to the first = a (4:3) and its (3:4) mirror.")
    print("  => YES: write k=7 as (4:3)|(3:4). The notation FORCES seeing the chiral need (F385) — at k=7 the")
    print("     chirality is not a tag on a fibration, it is the CONSTRUCTION; you cannot build the octonion")
    print("     without the two opposite-handed halves. 'Should one day be assumed but need notation now' = the")
    print("     same point-of-action forcing-function logic the project uses for srmech-first (STOP-list).")

    res = dict(srmech_version=srmech.__version__, H_closed=bool(Hclosed), H_associative=bool(H_assoc),
               seam_nonassociative=bool(seam_nonassoc), first_triad_signs=first_signs,
               doubled_triad_signs=doubled_signs, chiral_dual=bool(chiral_dual))
    (HERE / "R-RBS-LM-R29_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R29_results.json'}")


if __name__ == "__main__":
    main()
