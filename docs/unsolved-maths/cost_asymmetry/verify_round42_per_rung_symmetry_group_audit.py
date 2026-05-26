"""Round 42.A -- the per-rung symmetry-group audit revealed by Round 38.A. R38 showed the
2l+1 spine is SO(3)/S^2-SPECIFIC (off S^2, the disk gives O(2) {1,2,2}). This audit
re-reads EACH prior Reading-D rung: is its Class-L structure genuinely full SO(3), or
does it carry an enhancement / internal symmetry / deformation / finite branching?
Tested honestly per [[feedback_dont_pre_commit_spike_query_operators]].

RESULT -- CONFIRMS R38's symmetry-group-relative principle and TIGHTENS the loose
"9 contiguous SO(3)/S^2 rungs" wording. The ANGULAR (Class-L) structure is SO(3)-rooted
across all rungs, but only ~4 are cleanly FULL SO(3); the rest carry honest deviations:

  CLEAN FULL SO(3) (2l+1 = {1,3,5,7,...}):
    - quantum / Born=Hopf (Bloch sphere; SU(2)->SO(3))
    - nuclear shell (spherical mean field + spin-orbit; 2j+1)
    - planetary magnetics (geomagnetic S^2)
    - CMB sky (full-sky S^2)
  SO(3)-ANGULAR with an ENHANCED full symmetry:
    - atomic = SO(4) bound-state (Laplace-Runge-Lenz; n^2 degeneracy = sum 2l+1),
      SO(3) only angular. (Pauli 1926; Fock 1935.)
  SO(3)-SPATIAL plus an INTERNAL symmetry:
    - hadron = SO(3) spatial (chi_cJ = L(x)S, 2l+1) + SU(3) FLAVOR internal
      (Eightfold Way; multiplets 1,8,10). The SU(3) is NOT spatial SO(3).
  SO(3) DEFORMED / BROKEN (continuous):
    - BH-QNM = Kerr aw deforms SO(3) -> axial SO(2) (only m conserved); SO(3) only at
      a=0 (Schwarzschild). (Teukolsky 1973.)
    - LSS Kaiser RSD = SO(3) on the SKY (C_l) BUT the surviving even-l {0,2,4}
      multipoles are even-Legendre in the LINE-OF-SIGHT mu = SO(2)+parity, NOT sky-SO(3).
  FINITE subgroup of SO(3):
    - bio-capsid = icosahedral I (order 60; irreps {1,3,3,4,5}); a finite branching.

CONCLUSION: 2l+1 appears EXACTLY where full SO(3) is the operative symmetry (4 rungs);
elsewhere the ladder is enhanced (SO(4)), internal (SU(3)), deformed (SO(2)), or finite
(I) -- precisely R38's "the ladder tracks the symmetry group". The "9 SO(3) rungs"
phrase is REFINED to "9 rungs whose angular/Class-L structure is SO(3)-ROOTED; ~4 cleanly
full-SO(3), the rest carrying named enhancements/deformations/branchings".

Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints.
Attested (Explore-verified): hydrogen SO(4) Pauli 1926 / Fock 1935; nuclear Mayer-Jensen
1949 (Elliott SU(3) separate, deformed); hadron SU(3) Gell-Mann/Ne'eman 1961; Kerr SO(2)
Teukolsky 1973; Kaiser RSD 1987 / Hamilton 1998; icosahedral I order 60.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # noqa: F401 (Class N, available)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# per-rung audit table
# ---------------------------------------------------------------------------
AUDIT = [
    {"rung": "quantum / Born=Hopf (sec 11.9.4)", "symmetry": "SO(3) (SU(2) Bloch sphere)", "class": "clean_full_SO3", "irrep_dims": "2l+1 = 1,3,5,..."},
    {"rung": "nuclear shell (sec 11.9.16)", "symmetry": "SO(3) spherical mean field + spin-orbit", "class": "clean_full_SO3", "irrep_dims": "2j+1"},
    {"rung": "planetary magnetics (sec 11.9.15)", "symmetry": "SO(3) (geomagnetic S^2)", "class": "clean_full_SO3", "irrep_dims": "2l+1"},
    {"rung": "CMB sky (sec 11.9.6)", "symmetry": "SO(3) (full sky S^2)", "class": "clean_full_SO3", "irrep_dims": "2l+1"},
    {"rung": "atomic (sec 11.9.12-13; R17/R40)", "symmetry": "SO(4) bound-state (Runge-Lenz); SO(3) angular", "class": "SO3_angular_enhanced_SO4", "irrep_dims": "n^2 full = 1,4,9,16 (sum of 2l+1); 2l+1 angular"},
    {"rung": "hadron / QCD (sec 11.9.17)", "symmetry": "SO(3) spatial + SU(3) FLAVOR internal", "class": "SO3_spatial_plus_internal_SU3", "irrep_dims": "2l+1 (spatial); 1,8,10 (SU(3) flavor)"},
    {"rung": "BH-QNM (sec 11.9.20)", "symmetry": "Kerr: axial SO(2) (a!=0); SO(3) only at a=0", "class": "SO3_deformed_to_SO2", "irrep_dims": "spin-weighted spheroidal (l>=|s|, m conserved)"},
    {"rung": "LSS Kaiser RSD (sec 11.9.18)", "symmetry": "SO(3) on sky (C_l); SO(2)+parity on line-of-sight (even-l)", "class": "SO3_sky_plus_LOS_parity", "irrep_dims": "2l+1 (sky); even-l {0,2,4} (LOS Legendre)"},
    {"rung": "bio-capsid (sec 11.9.19)", "symmetry": "icosahedral I (finite subgroup of SO(3), order 60)", "class": "finite_subgroup_of_SO3", "irrep_dims": "{1,3,3,4,5} (Burnside sum 60)"},
]

# bit-exact checks on the integer signatures
so3 = [2 * l + 1 for l in range(4)]                    # 1,3,5,7
hydrogen_n2 = [n * n for n in (1, 2, 3, 4)]            # 1,4,9,16 = SO(4) shells
assert hydrogen_n2 == [sum(2 * l + 1 for l in range(n)) for n in (1, 2, 3, 4)]   # n^2 = sum 2l+1
icosa = [1, 3, 3, 4, 5]
assert sum(d * d for d in icosa) == 60                 # Burnside: |I| = 60
su3_baryon = {"3x3bar": [1, 8], "3x3x3": [10, 8, 8, 1]}
assert 1 + 8 == 9 and 10 + 8 + 8 + 1 == 27             # SU(3) multiplet dims

clean = [a["rung"] for a in AUDIT if a["class"] == "clean_full_SO3"]
deviations = [a for a in AUDIT if a["class"] != "clean_full_SO3"]
print("per-rung symmetry-group audit:")
for a in AUDIT:
    tag = "FULL SO(3)" if a["class"] == "clean_full_SO3" else a["class"]
    print(f"  [{tag:30s}] {a['rung']}")
    print(f"      symmetry: {a['symmetry']};  irreps: {a['irrep_dims']}")
print(f"\nclean full-SO(3): {len(clean)} rungs; deviations: {len(deviations)} rungs")
emit("per_rung_audit", audit=AUDIT, n_clean_full_SO3=len(clean), n_deviations=len(deviations),
     bit_exact={"SO3_2lplus1": so3, "hydrogen_SO4_n2": hydrogen_n2, "icosahedral_Burnside_sum": 60,
                "SU3_multiplets": su3_baryon},
     note="2l+1 appears exactly where full SO(3) is operative (4 rungs); the rest carry SO(4) enhancement / SU(3) internal / SO(2) deformation / finite-I branching")

emit("verdict",
     finding="the Reading-D ladder's angular/Class-L structure is SO(3)-ROOTED across all rungs, but only ~4 are cleanly FULL SO(3) (quantum, nuclear, planetary, CMB); the rest carry honest deviations -- atomic SO(4) (Runge-Lenz), hadron +SU(3)-flavor (internal), BH-QNM SO(2)-axial (Kerr), LSS SO(2)/parity (line-of-sight), capsid finite-I",
     confirms="R38's symmetry-group-relative principle -- the ladder tracks the operative symmetry group; 2l+1 <=> full SO(3)",
     refines="the loose '9 contiguous SO(3)/S^2 rungs' phrase -> '9 rungs whose Class-L angular structure is SO(3)-ROOTED; ~4 cleanly full-SO(3), the rest carrying named enhancements/deformations/internal-symmetries/finite-branchings'",
     honest_scope="(a)-bit-exact for the integer irrep signatures (2l+1, n^2=sum 2l+1, icosahedral Burnside 60, SU(3) 1+8/10+8+8+1) -- all standard, Explore-verified; (b)-interpretive for the per-rung symmetry assignments and the 'SO(3)-rooted but ~4 clean' refinement; no new physics; extends the R38 candidate stance, no new stance")

META = {
    "record": "meta",
    "round": "42.A",
    "title": "Per-rung symmetry-group audit -- ~4 clean full-SO(3); the rest carry SO(4)/SU(3)/SO(2)/finite-I deviations (confirms R38)",
    "kind": "(a)-bit-exact irrep-signature audit + (b)-interpretive per-rung symmetry catalog; CONFIRMS R38 symmetry-group-relative principle; tightens the '9 SO(3) rungs' phrase",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "hydrogen_SO4": "Pauli 1926; Fock 1935 (Laplace-Runge-Lenz; n^2 degeneracy)",
        "nuclear": "Mayer-Jensen 1949 (spherical + spin-orbit); Elliott SU(3) separate (deformed)",
        "hadron_SU3": "Gell-Mann / Ne'eman 1961 (Eightfold Way; internal flavor)",
        "kerr_SO2": "Teukolsky 1973 (spin-weighted spheroidal; axial for a!=0)",
        "kaiser_RSD": "Kaiser 1987; Hamilton 1998 (even-Legendre line-of-sight multipoles)",
        "icosahedral": "I order 60, finite subgroup of SO(3); irreps {1,3,3,4,5}",
        "framework": "R38 (symmetry-group-relative spine); sec 11.9.22 (Class-L spine); the Reading-D rungs sec 11.9.4-20",
    },
    "discipline": "honest audit -- confirms R38 and tightens an over-loose phrase; the deviations (SO(4), SU(3), SO(2), finite-I) are catalogued, not hidden; bit-exact integer signatures; extends the R38 candidate stance (no new stance); deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: the Reading-D ladder's angular/Class-L structure is SO(3)-ROOTED across all rungs, but only "
      "~4 are cleanly FULL SO(3) (quantum, nuclear, planetary, CMB). The rest carry honest deviations: atomic "
      "SO(4) (Runge-Lenz), hadron +SU(3)-flavor (internal), BH-QNM SO(2)-axial (Kerr), LSS SO(2)/parity "
      "(line-of-sight), capsid finite-I. This CONFIRMS R38's symmetry-group-relative principle (2l+1 <=> full "
      "SO(3)) and tightens the loose '9 SO(3) rungs' phrase. Extends the R38 stance; no new physics.")
