"""Round 31.A -- user hypothesis (from R30): "EM and gravity are inextricably coupled
in some way we have NOT yet noticed."

Tested honestly (per [[feedback_dont_pre_commit_spike_query_operators]]; the graviton
round just showed the framework does not win by default). Result is TWO-PART:

(A) STRUCTURAL CLAIM -- CONFIRMED. EM and gravity ARE inextricably coupled. The
    deepest sense: Kaluza-Klein (1921/1926) -- 5D pure gravity, compactified on a
    circle S^1, IS 4D gravity + 4D electromagnetism + a scalar. EM's vector
    potential A_mu = the off-diagonal g_{mu 5} of the 5D metric; the U(1) gauge
    symmetry of EM = the isometry (rotation) of the compact circle. EM is "the
    off-diagonal part of higher-dimensional gravity." This matches the framework's
    Hopf base+fiber reading: gravity = base geometry, EM = the U(1)-fiber isometry
    (Born=Hopf R4; Spike #58.I U(1)_Y from a 1D_circle; the (4+3)D_g gauge sector).

(B) "NOT YET NOTICED" -- CORRECTED (honest). It WAS noticed: light-bending 1919
    (Eddington), Kaluza 1921, Klein 1926, Gertsenshtein photon<->graviton mixing
    1962. The coupling is 60-107-year-established physics. What is genuinely
    UNDERAPPRECIATED is HOW DEEP the geometric unification is (EM = higher-D metric
    off-diagonal; U(1) = circle isometry) -- and the framework synthesis below.

FRAMEWORK SYNTHESIS (the genuine contribution): the R30 helicity ceiling {0,1,2}
is the 4D SHADOW of Kaluza-Klein. The 4D photon (|s|=1) and the 4D graviton (|s|=2)
are BOTH pieces of the SINGLE 5D graviton (|s|=2): the 5 polarizations of the 5D
graviton split EXACTLY as 2 (4D graviton) + 2 (photon) + 1 (dilaton) = 5. So EM and
gravity are not merely "coupled" -- in the higher-D / Hopf-bundle reading they are
ONE object (substrate-geometry), seen as base (gravity, |s|=2) vs fiber (EM,
U(1)=|s|=1 isometry). The {0,1,2} ceiling = base-diffeomorphism (2) + fiber-U(1) (1)
+ scalar/dilaton (0) of one higher-D geometry.

Three coupling levels (all attested, all "noticed"):
  L0 universal (trivial): EM stress-energy gravitates (light bends; Eddington 1919)
  L1 dynamical (overlooked): Gertsenshtein photon<->graviton oscillation in a B field
  L2 GEOMETRIC (deep): Kaluza-Klein -- EM = off-diagonal 5D metric; U(1) = S^1 isometry

Bit-exact core: massless spin-2 in D dims has D(D-3)/2 physical polarizations;
5D graviton (5) = 4D graviton (2) + photon (2) + dilaton (1).

HONEST CAVEAT: clean KK gives EM from gravity, but KK-for-the-WHOLE-Standard-Model
from pure higher-D gravity has known obstructions (chiral fermions, moduli/radion
stabilization). So "EM<->gravity = one geometry" is clean+established; the broader
"all gauge forces = fiber geometry" is the framework aspiration WITH known problems.

Facts verified (Explore, attested): Kaluza Sitzungsber.Preuss.Akad.Wiss. (1921) 966;
Klein Z.Phys. 37:895 (1926); Gertsenshtein Sov.Phys.JETP 14:84 (1962); Raffelt-
Stodolsky PRD 37:1237 (1988); Eddington 1919. Routed through srmech 0.4.2.
Deterministic; no network. ASCII-safe prints.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # noqa: F401 (Class N)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. BIT-EXACT: massless spin-2 DOF = D(D-3)/2 ; 5D graviton splits 5 = 2+2+1
# ---------------------------------------------------------------------------
def graviton_dof(D):
    return D * (D - 3) // 2


dof_5d = graviton_dof(5)              # 5
dof_4d_graviton = graviton_dof(4)     # 2
dof_photon = 2                         # massless spin-1 in 4D
dof_dilaton = 1                        # one real scalar
split = dof_4d_graviton + dof_photon + dof_dilaton
print("massless spin-2 DOF = D(D-3)/2:  5D ->", dof_5d, " 4D ->", dof_4d_graviton)
print("Kaluza-Klein split of the 5D graviton:",
      f"{dof_4d_graviton} (4D graviton) + {dof_photon} (photon) + {dof_dilaton} (dilaton) = {split}")
assert dof_5d == 5
assert split == dof_5d == 5            # 2 + 2 + 1 = 5  (EXACT)
emit("kaluza_klein_dof_split",
     graviton_dof_formula="D(D-3)/2",
     dof_5d_graviton=dof_5d,
     split={"4D_graviton": dof_4d_graviton, "photon": dof_photon, "dilaton": dof_dilaton, "sum": split},
     identity="5D graviton (5 dof) = 4D graviton (2) + photon (2) + dilaton (1)",
     note="EM emerges from gravity by dimensional reduction; the photon IS the off-diagonal g_{mu5} of the 5D metric; U(1) gauge = isometry of the compact circle S^1")

# 11D context (framework substrate): 11D graviton DOF = 44 (honest context only)
dof_11d = graviton_dof(11)             # 44
emit("eleven_d_context", dof_11d_graviton=dof_11d,
     note="framework 11D substrate: the 11D graviton has 44 dof; KK reduction yields 4D gravity + a tower of gauge fields + scalars -- the (4+3)D_g gauge sector. Context only; full SM from pure gravity has known obstructions (see caveat).")

# ---------------------------------------------------------------------------
# 2. three established coupling levels (all NOTICED -- honest)
# ---------------------------------------------------------------------------
LEVELS = [
    {"level": "L0 universal (trivial)", "mechanism": "EM stress-energy T_mu_nu^(EM) gravitates",
     "noticed": "1919 (Eddington light-bending)", "kind": "everything couples to gravity"},
    {"level": "L1 dynamical (overlooked)", "mechanism": "Gertsenshtein photon<->graviton oscillation in a B field",
     "noticed": "1962 (Gertsenshtein); Raffelt-Stodolsky 1988", "kind": "direct, weak, real exchange"},
    {"level": "L2 GEOMETRIC (deep)", "mechanism": "Kaluza-Klein: EM = off-diagonal 5D metric; U(1) = S^1 isometry",
     "noticed": "1921 (Kaluza) / 1926 (Klein)", "kind": "EM and gravity are ONE higher-D geometry (base+fiber)"},
]
print("\nthree established EM-gravity coupling levels (all NOTICED):")
for L in LEVELS:
    print(f"  {L['level']:26s} [{L['noticed']}]: {L['mechanism']}")
emit("three_coupling_levels", levels=LEVELS,
     honest_correction=("the coupling is NOT 'unnoticed' -- it is 60-107-year-established (Eddington 1919, "
                        "Kaluza 1921, Klein 1926, Gertsenshtein 1962). What is underappreciated is the DEPTH "
                        "of the geometric unification (L2) -- and the framework synthesis below."))

# ---------------------------------------------------------------------------
# 3. framework synthesis: the R30 helicity ceiling {0,1,2} = the KK shadow
# ---------------------------------------------------------------------------
ceiling = {0: "scalar / dilaton (KK radion)", 1: "photon = U(1) fiber isometry (off-diagonal metric)",
           2: "graviton = base-space diffeomorphism (4D metric)"}
print("\nR30 helicity ceiling {0,1,2} = the 4D shadow of the single 5D graviton (|s|=2):")
for s, v in ceiling.items():
    print(f"  |s|={s}: {v}")
emit("helicity_ceiling_is_kk_shadow",
     ceiling=ceiling,
     synthesis=("the 4D photon (|s|=1) and 4D graviton (|s|=2) are BOTH pieces of the SINGLE 5D graviton "
                "(|s|=2); the {0,1,2} long-range-force ceiling (R30) = base-diffeo (2) + fiber-U(1) (1) + "
                "dilaton (0) of ONE higher-D geometry. So EM and gravity are not merely coupled -- they are "
                "ONE substrate-geometry seen as base (gravity) vs fiber (EM/U(1))."),
     framework_ties=["Born=Hopf R4 (U(1) fiber of S^3->S^2)", "Spike #58.I (U(1)_Y from a 1D_circle, Class C/I)",
                     "(4+3)D_g gauge sector = KK fiber geometry of the 11D substrate"])

# ---------------------------------------------------------------------------
# 4. verdict
# ---------------------------------------------------------------------------
emit("verdict",
     hypothesis="EM and gravity are inextricably coupled in some way we have NOT yet noticed",
     structural_claim="CONFIRMED -- they ARE inextricably coupled (deepest: Kaluza-Klein base+fiber; EM = off-diagonal higher-D gravity, U(1) = circle isometry)",
     not_yet_noticed_qualifier="CORRECTED (honest) -- it WAS noticed: Eddington 1919, Kaluza 1921, Klein 1926, Gertsenshtein 1962. Established physics, not new.",
     framework_synthesis="the R30 helicity ceiling {0,1,2} IS the 4D shadow of Kaluza-Klein: photon (|s|=1) + graviton (|s|=2) are both the single 5D graviton (|s|=2); 5 dof = 2+2+1. EM and gravity = base+fiber of one substrate-geometry (Hopf / (4+3)D_g).",
     honest_caveat="clean KK gives EM<->gravity (established); KK-for-the-whole-SM from pure gravity has known obstructions (chiral fermions, moduli/radion). The broad 'all gauge = fiber geometry' is aspiration WITH problems, not settled.")

META = {
    "record": "meta",
    "round": "31.A",
    "title": "Are EM and gravity inextricably coupled? (user follow-on from R30)",
    "kind": "structural claim CONFIRMED (Kaluza-Klein) + honest correction of 'not yet noticed' + framework synthesis",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "kaluza": "Kaluza, Sitzungsber. Preuss. Akad. Wiss. Berlin (1921) 966 (Engl. transl. arXiv:1803.08616)",
        "klein": "Klein, Z. Phys. 37, 895 (1926)",
        "gertsenshtein": "Gertsenshtein, Sov. Phys. JETP 14, 84 (1962); Raffelt & Stodolsky, Phys. Rev. D 37, 1237 (1988)",
        "light_bending": "Eddington 1919 eclipse (GR light deflection)",
        "dof_formula": "massless spin-2 has D(D-3)/2 physical polarizations (standard)",
        "framework": "Born=Hopf R4; Spike #58.I (U(1)_Y from 1D_circle); (4+3)D_g gauge sector",
    },
    "discipline": "framework reading only; honest correction of the 'not yet noticed' qualifier (it was noticed, 1921); bit-exact DOF split proven; KK-whole-SM caveat stated; no flattery; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: EM<->gravity ARE inextricably coupled (CONFIRMED, Kaluza-Klein base+fiber; 5 dof = 2+2+1). "
      "'not yet noticed' CORRECTED -- noticed 1921. Framework synthesis: the R30 {0,1,2} ceiling is the 4D "
      "shadow of the single higher-D graviton; EM = fiber (U(1)), gravity = base, of one substrate-geometry.")
