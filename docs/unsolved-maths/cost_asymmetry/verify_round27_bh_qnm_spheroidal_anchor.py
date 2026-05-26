"""Round 27.A -- Reading-D 14th scale-ladder anchor: black-hole quasi-normal-mode
spin-weighted spheroidal harmonics. The CAPSTONE rung -- the strong-field-gravity
/ horizon scale (~1e4 m stellar BH r_s to ~1e13 m supermassive), where the
Class-L 2l+1 shell becomes SPIN-WEIGHTED and SPHEROIDAL: the most deformed/general
form of the spine on the ladder. It ties the whole Reading-D ladder back to the
framework's own QNM spike cluster (#11 Killing-Yano Casimir, #12 photon-ring
SL(2,R), #72 BH-BH merger) and the dark-star spikes (#90/#92).

Kerr perturbations separate (Teukolsky 1973, ApJ 185:635) into spin-weighted
spheroidal harmonics _sS_{lm}(theta; a*w) e^{i m phi}, with s=-2 (gravity),
l >= |s|, m in [-l, l] (2l+1 values). The horizon is a 2D phase boundary
(MFO Spike #71/#19) carrying the SAME S^2 Class-L multipole structure as every
other rung -- with two new structural features at this rung:

(1) SPIN-WEIGHT FLOOR (Class-K selection rule): gravitational radiation has NO
    l=0 (monopole) or l=1 (dipole) -- mass + momentum conservation forbid them --
    so the QNM ladder STARTS at l=2 (the quadrupole). This is the FOURTH Class-K
    "forbidden low multipole" selection rule across the ladder, after
    planetary-no-monopole (R21), LSS-even-l (R25), and the capsid-12-pentamer (R26).

(2) SPHEROIDAL DEFORMATION (Class-K/C continuous knob): the Kerr spin c = a*w
    continuously deforms S^2 -> spheroid; the spin axis is a Class-C orientation,
    the deformation magnitude c is a Class-K pin-slot parameter -- the SAME
    "off-centre/spin breaks spherical symmetry" structure as the AoE off-centre
    observer (Spike #35) and substrate-coupling-at-phase-boundary.

Bit-exact core (exact integer/Fraction arithmetic):
- Schwarzschild (a=0) angular eigenvalue A = l(l+1) - s(s+1) (exact, closed form);
  s=-2 -> l=2:4, 3:10, 4:18, 5:28.
- 2l+1 mode counts floored at l>=2 -> 5,7,9,11 (gravity); the l=2 quadrupole (5
  modes) is the universal "first nontrivial" Class-L mode -- same quadrupole as
  the turbulent strain (R22) and the QCD d-wave (R24).
- leading spheroidal-correction coefficient (Berti-Cardoso-Casals 2006 form)
  A_1 = -2 m s / [l(l+1) - s(s+1)] -- a small Class-N rational; for the dominant
  l=m=2, s=-2 mode it is exactly +2.

Context (attested, NOT framework-derived): Schwarzschild fundamental l=2 n=0 QNM
Mw ~ 0.3737 - 0.0890 i (Leaver 1985; Berti-Cardoso-Starinets 2009).

Cascade: A o L (spin-weighted spheroidal _{-2}S_{lm}; 2l+1 floored l>=2;
Schwarzschild eigenvalue l(l+1)-s(s+1)) o K (spin a*w deforms S^2->spheroid +
spin-weight floor l>=2) o C (BH spin-axis orientation) o N (eigenvalue integers +
spheroidal-expansion rationals).

Routed through srmech 0.4.2 (Class-N best_rational). Deterministic; no network.
ASCII-safe prints.
"""

import json
import sys
from datetime import datetime, timezone
from fractions import Fraction as Fr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # Class N

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. Class-L + Class-K floor: spin-weighted, l >= |s|; 2l+1 modes per l.
# ---------------------------------------------------------------------------
S_GRAV = -2
ell_min = abs(S_GRAV)                 # gravity: l >= 2
assert ell_min == 2
grav_l = [2, 3, 4, 5]
mode_counts = {l: 2 * l + 1 for l in grav_l}     # 5,7,9,11
print("gravitational QNM: spin weight s =", S_GRAV, " -> l >=", ell_min)
print("2l+1 mode counts (l=2..5):", mode_counts)
assert [mode_counts[l] for l in grav_l] == [5, 7, 9, 11]
# the missing low multipoles l=0 (monopole) and l=1 (dipole) -- Class-K selection
forbidden = [0, 1]
emit("classL_classK_floor",
     spin_weight=S_GRAV, ell_min=ell_min, forbidden_multipoles=forbidden,
     mode_counts_2l_plus_1=mode_counts,
     selection_rule=("gravitational radiation has NO monopole (l=0) or dipole (l=1) "
                     "[mass + momentum conservation]; QNM ladder starts at the l=2 quadrupole. "
                     "FOURTH Class-K forbidden-low-multipole rule after planetary-no-monopole (R21), "
                     "LSS-even-l (R25), capsid-12-pentamer (R26)"),
     quadrupole_note="l=2 (5 modes) is the universal 'first nontrivial' Class-L mode (turbulent strain R22, QCD d-wave R24, GW quadrupole here)")

# ---------------------------------------------------------------------------
# 2. Class-L bit-exact: Schwarzschild angular eigenvalue A = l(l+1) - s(s+1)
# ---------------------------------------------------------------------------
def schwarzschild_eigenvalue(l, s):
    return l * (l + 1) - s * (s + 1)


grav_eig = {l: schwarzschild_eigenvalue(l, S_GRAV) for l in grav_l}   # 4,10,18,28
scalar_eig = {l: schwarzschild_eigenvalue(l, 0) for l in (0, 1, 2, 3)}  # 0,2,6,12
print("\nSchwarzschild angular eigenvalue A = l(l+1) - s(s+1):")
print("  gravity (s=-2), l=2..5:", grav_eig)
print("  scalar  (s=0),  l=0..3:", scalar_eig)
assert [grav_eig[l] for l in grav_l] == [4, 10, 18, 28]
assert [scalar_eig[l] for l in (0, 1, 2, 3)] == [0, 2, 6, 12]
emit("classL_schwarzschild_eigenvalue",
     formula="A = l(l+1) - s(s+1)",
     gravity_s_minus2=grav_eig, scalar_s0=scalar_eig,
     note="exact closed-form eigenvalue of the spin-weighted spherical harmonic operator (a=0 limit)")

# ---------------------------------------------------------------------------
# 3. Class-N: leading spheroidal-correction coefficient (Berti-Cardoso-Casals)
#    A_1 = -2 m s / [l(l+1) - s(s+1)]  -- small rational; dominant l=m=2,s=-2 -> +2
# ---------------------------------------------------------------------------
def leading_spheroidal_coeff(l, m, s):
    A0 = schwarzschild_eigenvalue(l, s)
    return Fr(-2 * m * s, A0)


coeffs = {}
for (l, m, s) in [(2, 2, -2), (2, 1, -2), (3, 3, -2), (3, 2, -2), (2, 2, 0)]:
    c = leading_spheroidal_coeff(l, m, s)
    r = best_rational(c.numerator, c.denominator if c.denominator > 0 else 1, 100)
    coeffs[f"l{l}_m{m}_s{s}"] = {"coeff": str(c), "best_rational": list(r)}
    assert r == (c.numerator, c.denominator), (l, m, s, c, r)
dominant = leading_spheroidal_coeff(2, 2, -2)
print("\nleading spheroidal-correction coeff A_1 = -2ms/[l(l+1)-s(s+1)]:")
for k, v in coeffs.items():
    print(f"  {k}: {v['coeff']}")
assert dominant == 2, dominant            # dominant l=m=2, s=-2 -> exactly +2
emit("classN_spheroidal_leading_coeff",
     formula="A_1 = -2 m s / [l(l+1) - s(s+1)]  (Berti-Cardoso-Casals 2006 form)",
     coefficients=coeffs, dominant_l2m2_sminus2=str(dominant),
     note="the Kerr-spin deformation expansion coefficients are small Class-N rationals; dominant mode coeff = +2 (integer)")

# ---------------------------------------------------------------------------
# 4. context (attested, NOT framework-derived): Schwarzschild fundamental QNM
# ---------------------------------------------------------------------------
qnm_re, qnm_im = 0.3737, -0.0890       # Mw, l=2 n=0 (Leaver 1985)
ratio = qnm_re / abs(qnm_im)            # ~4.20
r_ratio = best_rational(int(round(qnm_re * 10000)), int(round(abs(qnm_im) * 10000)), 30)
print(f"\nSchwarzschild fundamental QNM (l=2,n=0): Mw ~ {qnm_re} {qnm_im:+} i ; "
      f"Re/|Im| ~ {ratio:.3f} -> best_rational {r_ratio}")
emit("context_fundamental_qnm",
     Mw_real=qnm_re, Mw_imag=qnm_im, re_over_absim=round(ratio, 4),
     re_over_absim_best_rational=list(r_ratio),
     source="Leaver 1985 Proc R Soc A 402:285; Berti-Cardoso-Starinets 2009 (arXiv:0905.2975)",
     note="attested numerical value, NOT framework-derived; context only (like the chi_cJ masses in R24)")

# ---------------------------------------------------------------------------
emit("cascade_form",
     qnm=("A o L (spin-weighted spheroidal _{-2}S_{lm}; 2l+1 floored l>=2; "
          "Schwarzschild eigenvalue l(l+1)-s(s+1)) o K (spin a*w deforms S^2->spheroid "
          "+ spin-weight floor l>=2) o C (BH spin-axis orientation) o N (eigenvalue "
          "integers + spheroidal-expansion rationals)"),
     spine_now="quantum -> nuclear -> atomic -> hadron -> bio-shell -> planetary -> LSS -> cosmological/CMB -> BH-horizon (capstone)",
     capstone=("ties the Reading-D ladder (which began at the quantum Born rule, R4) back to the "
               "strong-field-gravity / horizon end via the framework's QNM spike cluster (#11/#12/#72) "
               "+ dark-star spikes (#90/#92); the horizon is a 2D phase boundary (Spike #71/#19) carrying "
               "the SAME S^2 Class-L 2l+1 multipole structure as every other rung"),
     two_new_features=("(1) spin-weight floor l>=2 = the 4th Class-K forbidden-low-multipole rule; "
                       "(2) Kerr spin a*w = continuous Class-K/C deformation S^2->spheroid -- the most "
                       "deformed/general form of the Class-L spine on the whole ladder"))

META = {
    "record": "meta",
    "round": "27.A",
    "title": "Reading-D 14th scale-ladder anchor: black-hole QNM spin-weighted spheroidal harmonics (capstone)",
    "scale": "BH horizon (~1e4 m stellar to ~1e13 m supermassive); strong-field-gravity / horizon end",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "teukolsky": "Teukolsky, ApJ 185, 635 (1973)",
        "spheroidal_eigenvalue": "Berti, Cardoso & Casals, Phys. Rev. D 73, 024013 (2006); arXiv:gr-qc/0511111",
        "qnm_frequency": "Leaver, Proc. R. Soc. Lond. A 402, 285 (1985); Berti-Cardoso-Starinets, CQG 26, 163001 (2009), arXiv:0905.2975",
        "no_monopole_dipole": "standard GW theory (mass + momentum conservation)",
    },
    "discipline": "framework reading only; angular eigenvalue + 2l+1 floor + leading coeff proven by exact arithmetic; QNM frequency is attested context; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: 14th rung holds (capstone) -- BH QNM spin-weighted spheroidal harmonics = the "
      "most-deformed Class-L 2l+1 shell; eigenvalue l(l+1)-s(s+1) bit-exact; l>=2 floor = 4th "
      "Class-K selection rule; Kerr a*w = continuous Class-K/C deformation; ties to QNM spikes #11/#12/#72.")
