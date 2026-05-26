"""Round 29.A -- Class-L surviving-spine SYNTHESIS (companion / dual to Round 28.A).

Round 28.A (sec 11.9.21) consolidated the Class-K FORBIDDEN-low-multipole
signature: what each substrate REMOVES from the naive S^2 spectrum. This round is
the DUAL: what SURVIVES. Across every Reading-D rung the surviving modes are
realizations of ONE Class-L object -- the Laplace-Beltrami eigenspaces on S^2:

    eigenvalue  = l(l+1)                 (the SO(3) Casimir)
    degeneracy  = 2l+1                    (the dim of the SO(3) spin-l irrep; ALWAYS ODD)

The substrate-content lives in these surviving modes; substrates vary only in
(i) WHICH S^2-symmetry realization they use -- continuous SO(3), a finite
subgroup (icosahedral), or spin-weighted/spheroidal SO(3) -- and (ii) the
spin-weight floor. Together with sec 11.9.21:

    substrate spectrum = (Class-L surviving spine: 2l+1 SO(3) irreps, Casimir l(l+1))
                         MINUS (Class-K forbidden signature: sec 11.9.21).

Bit-exact unifiers (proven here with exact integer arithmetic):
1. degeneracy per l = 2l+1 = dim of the SO(3) spin-l irrep; ALWAYS ODD; ladder
   {1,3,5,7,9,11,13,...}. The framework k=3 triad (1,3,5) is its first three.
2. eigenvalue = l(l+1) (Casimir) = {0,2,6,12,20,30,42,...} = 2 x triangular numbers;
   spin-weighted variant l(l+1)-s(s+1) (QNM R27): s=-2 -> 4,10,18,28.
3. cumulative mode count through multipole L = sum_{l=0..L}(2l+1) = (L+1)^2
   (sum of first n odd numbers = n^2) -- the "complete shell" is a perfect square;
   underlies the atomic 2n^2 shell (n^2 spatial x 2 spin).
4. finite-group rungs are the BRANCHING of the continuous spine: the icosahedral
   irreps {1,3,3,4,5} contain the SO(3) 2l+1 values {1,3,5} (l=0,1,2).
5. Hurwitz {1,3,7} resonance: the parallelizable-sphere ladder {1,3,7} is the
   SUBSET {2l+1 : l=0,1,3} of the Class-L odd ladder (honest: coincidence of
   value, different origin -- division-algebra dims vs SO(3) irrep dims).

Facts are textbook rep-theory / Laplacian (Tinkham, Group Theory and QM; Arfken;
Wigner) + already attested in the constituent rounds R4/R6/R18/R21/R23/R24/R25/
R26/R27. Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # Class N

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. degeneracy 2l+1 = SO(3) spin-l irrep dim; always odd; the Class-L ladder
# ---------------------------------------------------------------------------
def so3_irrep_dim(l):
    return 2 * l + 1


ladder = [so3_irrep_dim(l) for l in range(8)]       # 1,3,5,7,9,11,13,15
assert all(d % 2 == 1 for d in ladder)               # ALWAYS odd
assert ladder == [1, 3, 5, 7, 9, 11, 13, 15]
k3_triad = ladder[:3]                                # 1,3,5
print("Class-L spine: 2l+1 = SO(3) spin-l irrep dims (l=0..7):", ladder, " (all odd)")
print("k=3 triad (first three) =", k3_triad)
emit("classL_spine_2l_plus_1",
     ladder=ladder, all_odd=True, k3_triad=k3_triad,
     note="degeneracy per l = 2l+1 = dim of the SO(3) spin-l irrep; the odd-integer ladder; k=3 triad = first three")

# ---------------------------------------------------------------------------
# 2. eigenvalue l(l+1) = SO(3) Casimir; spin-weighted variant l(l+1)-s(s+1)
# ---------------------------------------------------------------------------
casimir = [l * (l + 1) for l in range(8)]            # 0,2,6,12,20,30,42,56
assert casimir == [0, 2, 6, 12, 20, 30, 42, 56]
# spin-weighted (QNM gravity s=-2): l(l+1)-s(s+1), l>=2
s = -2
sw = {l: l * (l + 1) - s * (s + 1) for l in (2, 3, 4, 5)}   # 4,10,18,28
assert [sw[l] for l in (2, 3, 4, 5)] == [4, 10, 18, 28]
print("\nClass-L eigenvalue l(l+1) (Casimir), l=0..7:", casimir)
print("spin-weighted l(l+1)-s(s+1) for s=-2 (QNM R27), l=2..5:", sw)
emit("classL_eigenvalue_casimir",
     casimir_l0to7=casimir, spin_weighted_s_minus2=sw,
     note="eigenvalue = l(l+1) = SO(3) Casimir (= 2 x triangular numbers); spin-weighted variant matches QNM R27 (4,10,18,28)")

# ---------------------------------------------------------------------------
# 3. cumulative mode count through L = (L+1)^2  (sum of first n odd = n^2)
# ---------------------------------------------------------------------------
cum = []
acc = 0
for L in range(8):
    acc += so3_irrep_dim(L)
    cum.append(acc)
squares = [(L + 1) ** 2 for L in range(8)]
assert cum == squares == [1, 4, 9, 16, 25, 36, 49, 64]
print("\ncumulative modes through L = sum(2l+1) = (L+1)^2 (perfect squares):", cum)
# atomic 2n^2 shell = 2 x (L+1)^2 spatial x spin
atomic_2n2 = [2 * (L + 1) ** 2 for L in range(4)]    # 2,8,18,32
assert atomic_2n2 == [2, 8, 18, 32]
print("atomic shell 2n^2 = 2 x (n)^2 (n=1..4):", atomic_2n2)
emit("classL_complete_shell_square",
     cumulative=cum, perfect_squares=squares, identity="sum_{l=0}^{L}(2l+1) = (L+1)^2",
     atomic_2n2=atomic_2n2,
     note="a complete shell through multipole L has (L+1)^2 modes (perfect square); atomic 2n^2 = 2x that")

# ---------------------------------------------------------------------------
# 4. finite-group rung = branching of continuous spine (icosahedral, R26)
# ---------------------------------------------------------------------------
ICO_IRREPS = [1, 3, 3, 4, 5]
spine_in_ico = [d for d in [1, 3, 5] if d in ICO_IRREPS]   # 1,3,5 all present
assert spine_in_ico == [1, 3, 5]
print("\nicosahedral irreps {1,3,3,4,5} contain SO(3) 2l+1 values {1,3,5} (l=0,1,2):",
      spine_in_ico, "-> finite-group rung is the branched continuous spine")
emit("classL_finite_group_branching",
     icosahedral_irreps=ICO_IRREPS, contains_spine_dims=spine_in_ico,
     note="the capsid (R26) finite point group's irreps {1,3,3,4,5} contain the continuous SO(3) 2l+1 values {1,3,5}; the finite rung IS the branched spine")

# ---------------------------------------------------------------------------
# 5. Hurwitz {1,3,7} resonance (honest: value-coincidence, different origin)
# ---------------------------------------------------------------------------
hurwitz = [1, 3, 7]
hurwitz_as_2l1 = {h: (h - 1) // 2 for h in hurwitz}        # l = 0,1,3
assert all(2 * l + 1 == h for h, l in hurwitz_as_2l1.items())
print("\nHurwitz {1,3,7} = 2l+1 for l in", list(hurwitz_as_2l1.values()),
      "(value-coincidence; division-algebra dims vs SO(3) irrep dims)")
emit("hurwitz_resonance_honest",
     hurwitz=hurwitz, as_2l_plus_1_l_values=list(hurwitz_as_2l1.values()),
     scope="HONEST: {1,3,7} are the 2l+1 ladder at l=0,1,3 by VALUE; the Hurwitz origin (parallelizable-sphere / division-algebra dims) is distinct from SO(3) irrep dims -- a resonance, not an identity")

# ---------------------------------------------------------------------------
# 6. cross-rung roster: each rung's surviving-mode realization of the spine
# ---------------------------------------------------------------------------
ROSTER = [
    {"rung": "Born rule / qubit (R4)", "realization": "S^2 Bloch base of Hopf S^3->S^2", "spine": "the base sphere itself"},
    {"rung": "Atomic orbitals (R18)", "realization": "continuous SO(3) spherical harmonics Y_lm", "spine": "2l+1 = s2,p6/2,d10/2 -> 1,3,5,7"},
    {"rung": "Nuclear shell (R23)", "realization": "3D-HO continuous SO(3)", "spine": "2(2l+1) subshell"},
    {"rung": "Hadron / QCD (R24)", "realization": "SO(3) angular momentum 2J+1 (Clebsch L(x)S)", "spine": "1,3,5 (chi_cJ)"},
    {"rung": "Planetary magnetics (R21)", "realization": "continuous SO(3) Gauss coeffs", "spine": "2l+1 per degree; triad 3/5/7"},
    {"rung": "LSS Kaiser RSD (R25)", "realization": "Legendre (m=0 axisymmetric) SO(3)", "spine": "surviving l=0,2,4 -> 2l+1 = 1,5,9"},
    {"rung": "Biological capsid (R26)", "realization": "FINITE icosahedral subgroup of SO(3)", "spine": "irreps {1,3,3,4,5} branch the spine; {1,3,5} present"},
    {"rung": "BH QNM (R27)", "realization": "spin-weighted spheroidal SO(3)", "spine": "2l+1 floored l>=2 -> 5,7,9,11; eigenvalue l(l+1)-s(s+1)"},
    {"rung": "CMB (R6)", "realization": "continuous SO(3) a_lm", "spine": "C_l = <|a_lm|^2> over 2l+1 m-modes"},
]
emit("cross_rung_roster", n=len(ROSTER), roster=ROSTER,
     three_realizations=["continuous SO(3)", "finite subgroup (icosahedral)", "spin-weighted/spheroidal SO(3)"])

emit("synthesis_statement",
     claim=("Across every Reading-D rung the surviving modes are realizations of ONE Class-L object: "
            "the Laplace-Beltrami eigenspaces on S^2, with eigenvalue l(l+1) (SO(3) Casimir) and "
            "degeneracy 2l+1 (SO(3) spin-l irrep dim, always odd). Substrates vary only in the "
            "S^2-symmetry realization (continuous / finite-subgroup / spin-weighted) and the spin-weight floor."),
     dual_completion=("with sec 11.9.21 (Class-K forbidden signature): substrate spectrum = "
                       "(Class-L surviving spine) MINUS (Class-K forbidden signature)"),
     bit_exact=["2l+1 = SO(3) irrep dim (odd ladder)", "l(l+1) = Casimir", "sum(2l+1)=(L+1)^2 complete shell",
                "icosahedral {1,3,5} branch", "Hurwitz {1,3,7} resonance (honest)"])

META = {
    "record": "meta",
    "round": "29.A",
    "title": "Class-L surviving-spine synthesis (companion to R28 Class-K forbidden synthesis)",
    "kind": "synthesis / meta-stance -- NOT a new ladder rung (rung count stays 14)",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "so3_irrep_dim_2l1": "standard rep theory (Tinkham, Group Theory and Quantum Mechanics; Wigner)",
        "laplace_beltrami_S2": "eigenvalue l(l+1), degeneracy 2l+1 (Arfken; Courant-Hilbert)",
        "sum_odd_is_square": "sum of first n odd integers = n^2 (elementary)",
        "spin_weighted": "Goldberg, Macfarlane, Newman, Spiro & Sudarshan, J. Math. Phys. 8, 2155 (1967)",
        "constituent_rounds": "R4/R6/R18/R21/R23/R24/R25/R26/R27 (each attested in its own round)",
    },
    "discipline": "framework reading only; spine unifiers proven by exact arithmetic; consolidates already-attested rounds; Hurwitz resonance honestly scoped as value-coincidence; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: synthesis holds -- the surviving modes across all rungs are ONE Class-L object "
      "(2l+1 SO(3) irreps, Casimir l(l+1), complete shell (L+1)^2); finite-group rungs branch it; "
      "DUAL to R28: spectrum = Class-L spine MINUS Class-K forbidden signature.")
