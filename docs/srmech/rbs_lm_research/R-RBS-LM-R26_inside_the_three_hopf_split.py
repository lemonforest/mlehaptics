"""F384 — what is the INTERNAL structure of the "3" of (4:3)=H? The user's (4:(2:1)) and (4:((1:1):1)).

User (2026-06-04): "what if we did (4:((1:1):1)) or this (4:(2:1))?"

Two candidate nestings of the 3 couplings {i,j,k}. The honest answer (srmech-native, reading the octonion
structure-constant table restricted to H): the "3" is NOT flat, but it also does NOT split as a SUBALGEBRA —
it splits as the Hopf 1+2 (fiber : base), and BOTH notations name that same 1+2 split in two coordinate
languages.

  (1) NO 2-dim subalgebra: the commutator of every imaginary pair lands on the THIRD imaginary, so no pair is
      closed -> su(2) is simple, the 3 is IRREDUCIBLE as an algebra. Neither (2:1) nor ((1:1):1) is an algebra
      factorization.
  (2) BUT a complex structure (pick i) splits the 3 as 1 (fiber i, the U(1) phase) + 2 (base {j,k}, one C-line,
      since k = i*j). That is the Hopf fibration S^3 -> S^2 with S^1 fiber (F124).

  (4:(2:1))     = base(2) read as a COMPLEX line : fiber(1)            -- holomorphic reading (base = CP^1 = S^2)
  (4:((1:1):1)) = base(2) read as a balanced (1:1) REAL dual : fiber(1) -- chirality-dual reading (j,k mirror; F129)

Same geometric split; (2:1) is the C language, ((1:1):1) is the R^2/Z_2-dual language.

srmech-native: qm.octonion.octonion_mult_table (read the int8 structure constants; no numpy math, no abs()).
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R26_inside_the_three_hopf_split.py
"""
import json
from pathlib import Path
import srmech
from srmech.qm.octonion import octonion_mult_table

HERE = Path(__file__).parent
NAMES = {0: "1", 1: "i", 2: "j", 3: "k"}


def main():
    print(f"F384 internal structure of the '3' of (4:3)=H (srmech {srmech.__version__})")
    C = octonion_mult_table().tolist()       # (8,8,8) int8: e_a * e_b = sum_k C[a][b][k] e_k
    I, J, K = 1, 2, 3

    def prod(a, b):
        row = C[a][b]
        ks = [k for k in range(8) if row[k] != 0]
        assert len(ks) == 1
        return row[ks[0]], ks[0]             # (sign, index)

    # (1) no 2-dim subalgebra: commutator of each pair lands on the THIRD
    print("\n(1) subalgebra test — product of each imaginary pair (ab = -ba, so [a,b]=2ab):")
    outside = []
    for na, a, nb, b in (("i", I, "j", J), ("j", J, "k", K), ("k", K, "i", I)):
        s, kk = prod(a, b)
        is_outside = kk not in (a, b)
        outside.append(is_outside)
        print(f"    {na}*{nb} = {'+' if s > 0 else '-'}{NAMES[kk]}   -> lands on the THIRD "
              f"({'OUTSIDE' if is_outside else 'inside'} the pair {{{na},{nb}}})")
    no_subalgebra = all(outside)
    print(f"    => NO 2-dim subalgebra among {{i,j,k}}: {no_subalgebra}  "
          f"(su(2) is simple; the 3 is IRREDUCIBLE as an algebra)")

    # (2) Hopf 1+2 split via the complex structure i
    print("\n(2) Hopf fibration split (pick i as the complex structure):")
    sij, kij = prod(I, J)                    # i*j
    sik, kik = prod(I, K)                    # i*k
    print(f"    i*j = {'+' if sij > 0 else '-'}{NAMES[kij]}   => k IS i applied to j -> {{j,k}} is ONE complex line (the base)")
    print(f"    i*k = {'+' if sik > 0 else '-'}{NAMES[kik]}   => i rotates the base j->k->-j->-k : the fiber U(1), order-4 = Z_4 (DYADIC)")
    print(f"    so the 3 = 1 (fiber i = the U(1) phase) + 2 (base {{j,k}} = one C-line) = the Hopf 1+2 (F124)")

    print("\n=== verdict ===")
    print("  (4:(2:1))     = base(2) as a COMPLEX line : fiber(1)        -- holomorphic reading (base = CP^1 = S^2)")
    print("  (4:((1:1):1)) = base(2) as a balanced (1:1) REAL dual : fiber(1) -- chirality-dual reading (F129)")
    print("  SAME geometric 1+2 Hopf split, two coordinate languages. NOT an algebra factorization (su(2) simple).")
    print("  Payoff for F382/F383: the split separates the EXACT-able PHASE (fiber i; its lattice Z_4 is DYADIC)")
    print("  from the continuous DIRECTION (base {j,k}=C; the F382 rotation-decimal). The irreducible-rotation")
    print("  cost lives in the BASE; the fiber phase is quantizable/bit-exact.")
    print("  CAUTION (two different 3s): this '3' = the 3 su(2) IMAGINARIES (the couplings). It is a DIFFERENT")
    print("  object from the Z_3 TRIALITY 3-cycle (the symmetry permuting i->j->k) that F383 found non-dyadic.")

    res = dict(srmech_version=srmech.__version__, no_2dim_subalgebra=no_subalgebra,
               i_times_j=[sij, NAMES[kij]], i_times_k=[sik, NAMES[kik]],
               hopf_split="3 = 1 fiber (i, U(1), Z_4 dyadic) + 2 base ({j,k} = C-line)",
               reading_2_1="base as complex line : fiber (holomorphic, CP^1)",
               reading_11_1="base as balanced (1:1) real dual : fiber (chirality, F129)")
    (HERE / "R-RBS-LM-R26_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R26_results.json'}")


if __name__ == "__main__":
    main()
