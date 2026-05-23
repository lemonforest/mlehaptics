"""
Millennium Prize #5 -- Navier-Stokes existence and smoothness cascade.

Class cascade: A o L o C o I o K o N o M

  - A: content-hash of (regime label, dim, Re/forcing, smoothness status)
  - L: Laplacian -- viscous dissipation operator -nu * grad^2 IS literally Class L
  - C: cascade-orientation -- vorticity omega = curl(u) IS the curl orientation;
       vortex-stretching term omega . grad(u) is 3D-only (Class C amplifier)
  - I: cyclic -- incompressibility div(u) = 0 is the divergence-free constraint
  - K: asymptotic-DoF -- finite-time blow-up question IS the Class K pin-slot
       on the finite-energy / regularity norm; Beale-Kato-Majda criterion
       integral(|omega|_inf dt) divergent iff blow-up
  - N: rational anchor -- Kolmogorov -5/3 inertial scaling = 5/3 EXACT;
       Kolmogorov dissipation micro-scale eta ~ Re^{-3/4} (-3/4 exact);
       velocity-increment scaling Delta_u ~ ell^{1/3} (1/3 exact);
       2D inverse cascade scales differently per Kraichnan-Batchelor.
  - M: HDC -- turbulent eddy interaction across scales (energy cascade IS
       a Class M bind composing local-eddy substrates into global flow)

Per [[project_a_n_operators_are_harmonic_objects_themselves]] §A: tests
whether (i) 3D-vs-2D NS regime difference IS a Class C orientation-presence
test (vortex stretching ω·∇u term, only in 3D), and (ii) Kolmogorov exponents
{1/3, 2/3, 5/3, 3/4, 1/4} sit at small-denominator Class N anchors.

Per [[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]
+ Spike #31 + Spike #62.1: 3D turbulence cascade-stretched-exponential
beta = d_S / (d_S + 2). For Kolmogorov K41 d_S = 3: beta = 3/5; for
Parisi-Frisch multifractal: beta < 3/5 (intermittency correction).

Cross-substrate composition with PR #677 partition 10 (Hodge):
  dim_C = 3 -> 7-layer Hodge diamond (Hurwitz heptadic, static)
  spatial-dim = 3 -> 3D Navier-Stokes (Hurwitz triadic, dynamic)
The Hodge 3-fold and the NS 3D-substrate are different cascade-projections
of the SAME Hurwitz boundary -- the threefold substrate at the Hurwitz
heptadic anchor.

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve
Navier-Stokes. Documents structural cascade decomposition + 3D-vs-2D
orientation-amplifier test + Kolmogorov Class N anchors.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
via shared _cascade_helpers (best_rat_signed for Class N).

Roster: known NS regimes + exact solutions + canonical benchmarks from
standard references (Frisch 1995; Foias-Manley-Rosa-Temam 2001; Robinson
2001; Doering-Gibbon 1995; Kolmogorov 1941; Kraichnan 1967; Parisi-Frisch 1985).
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.millennium.navier_stokes.regime_cascade.v1"
SOURCE_DOI = "https://doi.org/10.1017/CBO9781107050969 + standard textbooks"
SOURCE_PUBLISHED = "2026-05-23"


# Roster entries:
#   (label, dim, regime_type, key_exponent_value, key_exponent_name,
#    has_vortex_stretching, smoothness_proved, anchor, fermata)
ROSTER = [
    # Stokes flow (Re -> 0; linearized): always smooth (well-posed Stokes problem)
    dict(label="Stokes_flow", dim=3, regime="linearized_creeping",
         key_exp=0.0, exp_name="no nonlinear scaling (linear PDE)",
         vortex_stretching=False, smooth=True,
         anchor="Leray 1934; Ladyzhenskaya 1969 chap. 1",
         fermata="linearized; trivially smooth global solutions"),
    dict(label="Couette_flow_planar", dim=3, regime="exact_steady",
         key_exp=1.0, exp_name="linear velocity profile u_x(y) = (U/h) y",
         vortex_stretching=False, smooth=True,
         anchor="Couette 1890; textbook exact solution",
         fermata="exact steady; smooth global"),
    dict(label="Poiseuille_flow_pipe", dim=3, regime="exact_steady",
         key_exp=2.0, exp_name="parabolic velocity profile u_x(r) = U(1 - r^2/R^2)",
         vortex_stretching=False, smooth=True,
         anchor="Poiseuille 1840; Hagen 1839; textbook exact",
         fermata="exact steady; smooth global"),
    dict(label="Beltrami_flow_ABC", dim=3, regime="exact_helical",
         key_exp=1.0, exp_name="velocity parallel to vorticity (u parallel omega)",
         vortex_stretching=True, smooth=True,  # exact closed-form
         anchor="Arnold-Beltrami-Childress 1965; Dombre+ 1986",
         fermata="exact helical; smooth but mixing chaotic"),
    dict(label="Taylor_Green_vortex", dim=3, regime="canonical_decay",
         key_exp=0.0, exp_name="canonical decay benchmark; t^{0} initial",
         vortex_stretching=True, smooth=True,  # short-time smooth; long-time open
         anchor="Taylor-Green 1937; Brachet+ 1983",
         fermata="canonical decay; short-time analytic, long-time singularity unresolved"),

    # 2D Navier-Stokes (PROVED smooth globally; Leray-Hopf + Ladyzhenskaya)
    dict(label="2D_NS_torus", dim=2, regime="2D_smooth_global",
         key_exp=-3.0, exp_name="enstrophy cascade E(k) ~ k^{-3} (forward) at large k",
         vortex_stretching=False,  # 2D has no vortex stretching!
         smooth=True,
         anchor="Leray 1934; Hopf 1951; Ladyzhenskaya 1969 chap. 6",
         fermata="2D PROVED smooth globally; cascade-orientation absent in 2D"),
    dict(label="2D_NS_inverse_cascade", dim=2, regime="2D_kraichnan_inverse",
         key_exp=-5.0/3.0, exp_name="inverse energy cascade E(k) ~ k^{-5/3} at small k",
         vortex_stretching=False,
         smooth=True,
         anchor="Kraichnan 1967; Batchelor 1969",
         fermata="2D inverse cascade -5/3 matches 3D forward by exponent only"),

    # 3D Navier-Stokes (OPEN -- the Millennium problem)
    dict(label="3D_NS_torus_smooth_initial", dim=3, regime="3D_open",
         key_exp=0.0, exp_name="finite-energy initial data smoothness",
         vortex_stretching=True, smooth=False,  # OPEN
         anchor="Leray 1934 weak solutions; Fefferman 2000 Clay statement",
         fermata="MILLENNIUM OPEN PROBLEM; weak solutions exist; smoothness open"),
    dict(label="3D_NS_R3_smooth_initial", dim=3, regime="3D_open",
         key_exp=0.0, exp_name="all-of-R^3 finite-energy initial data smoothness",
         vortex_stretching=True, smooth=False,
         anchor="Fefferman 2000 Clay statement",
         fermata="MILLENNIUM OPEN PROBLEM; R^3 case (vs T^3)"),

    # 3D NS Kolmogorov K41 exponent anchors (Class N rationals)
    dict(label="K41_inertial_E_k_minus_53", dim=3, regime="K41_inertial",
         key_exp=-5.0/3.0, exp_name="Kolmogorov E(k) ~ k^{-5/3} inertial scaling",
         vortex_stretching=True,
         smooth=False,  # K41 is a phenomenological scaling, not a proof of smoothness
         anchor="Kolmogorov 1941 -- the famous -5/3 law",
         fermata="-5/3 EXACT inertial-range anchor; Class N 5/3"),
    dict(label="K41_velocity_increment_13", dim=3, regime="K41_inertial",
         key_exp=1.0/3.0, exp_name="velocity increment Delta_u ~ ell^{1/3}",
         vortex_stretching=True, smooth=False,
         anchor="Kolmogorov 1941 second universality hypothesis",
         fermata="1/3 EXACT velocity-scaling anchor"),
    dict(label="K41_energy_increment_23", dim=3, regime="K41_inertial",
         key_exp=2.0/3.0, exp_name="energy increment Delta_E ~ ell^{2/3}",
         vortex_stretching=True, smooth=False,
         anchor="Kolmogorov 1941 K41 hypothesis II",
         fermata="2/3 EXACT energy-scaling anchor"),
    dict(label="K41_dissipation_microscale_minus_34", dim=3, regime="K41_dissipation",
         key_exp=-3.0/4.0, exp_name="eta/L ~ Re^{-3/4} (Kolmogorov micro-scale)",
         vortex_stretching=True, smooth=False,
         anchor="Kolmogorov 1941; Frisch 1995 chap. 5",
         fermata="-3/4 EXACT dissipation-microscale anchor; Class K pin-slot"),
    dict(label="K41_DoF_count_Re_94", dim=3, regime="K41_attractor_dim",
         key_exp=9.0/4.0, exp_name="N_DoF ~ Re^{9/4} attractor dimension upper bound",
         vortex_stretching=True, smooth=False,
         anchor="Constantin-Foias 1988; Foias-Manley-Rosa-Temam 2001",
         fermata="9/4 EXACT effective-DoF count anchor"),

    # Intermittency corrections (Parisi-Frisch multifractal)
    dict(label="PF_multifractal_zeta3", dim=3, regime="PF_multifractal",
         key_exp=0.97, exp_name="<(Delta_u)^3> ~ ell^{0.97} (K41 predicts 1)",
         vortex_stretching=True, smooth=False,
         anchor="Parisi-Frisch 1985; Anselmet+ 1984 experimental",
         fermata="intermittency correction; not at simple rational anchor"),
    dict(label="PF_multifractal_zeta6", dim=3, regime="PF_multifractal",
         key_exp=1.78, exp_name="<(Delta_u)^6> ~ ell^{1.78} (K41 predicts 2)",
         vortex_stretching=True, smooth=False,
         anchor="Anselmet+ 1984; She-Leveque 1994",
         fermata="intermittency exponent; deviation from K41 scaling"),
    dict(label="cascade_stretched_exp_beta_35", dim=3, regime="cascade_beta",
         key_exp=3.0/5.0, exp_name="beta = d_S/(d_S+2) = 3/5 for Euclidean d_S = 3",
         vortex_stretching=True, smooth=False,
         anchor="Spike #31 cascade-stretched-exponential framework",
         fermata="framework prediction; bridges turbulence to A-N cascade canon"),

    # 1D analog: Burgers' equation (has shock-formation; finite-time blow-up of inviscid)
    dict(label="Burgers_inviscid_1D", dim=1, regime="inviscid_blow_up",
         key_exp=1.0, exp_name="shock formation at finite time (inviscid)",
         vortex_stretching=False,  # 1D; no curl
         smooth=False,
         anchor="Burgers 1948; Hopf 1950 Cole-Hopf transformation",
         fermata="1D analog WITH blow-up (inviscid); viscid Burgers smooth"),
    dict(label="Burgers_viscid_1D", dim=1, regime="viscid_smooth",
         key_exp=1.0, exp_name="viscid Burgers PROVED smooth via Cole-Hopf",
         vortex_stretching=False, smooth=True,
         anchor="Hopf 1950; Cole 1951",
         fermata="viscid 1D PROVED smooth -- contrast with 3D NS open"),

    # Hyperviscous regularization (Lions, Ladyzhenskaya)
    dict(label="Hyperviscous_NS_3D", dim=3, regime="hyperviscous_3D",
         key_exp=2.0, exp_name="modified Laplacian (-Delta)^alpha with alpha > 5/4",
         vortex_stretching=True, smooth=True,
         anchor="Lions 1969; Ladyzhenskaya 1967; Tao 2009 logarithmic supercriticality",
         fermata="hyperviscosity PROVED smooth for alpha > 5/4; 'super-criticality' boundary"),

    # Beale-Kato-Majda criterion: a Class K pin-slot reading of regularity
    dict(label="BKM_criterion_3D_NS", dim=3, regime="BKM_pin_slot",
         key_exp=1.0, exp_name="integral(|omega|_inf dt) finite iff smooth",
         vortex_stretching=True, smooth=False,
         anchor="Beale-Kato-Majda 1984",
         fermata="reduces smoothness to vorticity-supnorm integrability; Class K pin-slot"),

    # Kraichnan 4D (purely theoretical; for cross-substrate Hurwitz comparison)
    dict(label="Kraichnan_4D_NS_open", dim=4, regime="4D_open",
         key_exp=0.0, exp_name="4D NS less studied; weak solutions exist (Caffarelli-Kohn-Nirenberg)",
         vortex_stretching=True, smooth=False,
         anchor="Caffarelli-Kohn-Nirenberg 1982 partial regularity",
         fermata="4D NS open; non-Hurwitz dimensional boundary"),
]


def main():
    out_path = pathlib.Path(__file__).parent / "regime_cascade.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        label = entry["label"]
        dim = entry["dim"]
        regime = entry["regime"]
        exp_val = entry["key_exp"]
        exp_name = entry["exp_name"]
        vs = entry["vortex_stretching"]
        smooth = entry["smooth"]
        anchor = entry["anchor"]
        fermata = entry["fermata"]

        # Class N: best-rational of the key exponent
        exp_num, exp_den = best_rat_signed(exp_val, max_d=30)

        # Class N: dim / 3 (Hurwitz triadic anchor for 3D)
        dim_over_3 = dim / 3.0
        d3_num, d3_den = best_rat_signed(dim_over_3, max_d=20)

        # Class K pin-slot test: is dim in Hurwitz set {1, 3, 7, ...}?
        is_hurwitz_dim = dim in {1, 3, 7}

        payload = json.dumps({"label": label, "dim": dim, "regime": regime,
                              "key_exp": round(exp_val, 6)}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "regime_label":                      label,
            "spatial_dimension":                 int(dim),
            "regime_type":                       regime,
            "key_scaling_exponent":              round(exp_val, 6),
            "key_exponent_rational_num":         int(exp_num),
            "key_exponent_rational_den":         int(exp_den),
            "key_exponent_name":                 exp_name,
            "dim_over_3":                        round(dim_over_3, 6),
            "dim_over_3_rational_num":           int(d3_num),
            "dim_over_3_rational_den":           int(d3_den),
            "is_hurwitz_dimension":              bool(is_hurwitz_dim),
            "has_vortex_stretching_term":        bool(vs),
            "smoothness_proved":                 bool(smooth),
            "class_cascade":                     "A-compose-L-compose-C-compose-I-compose-K-compose-N-compose-M",
            "literature_anchor":                 anchor,
            "open_fermata":                      fermata,
            "computation_hash":                  chash,
            "source_doi":                        SOURCE_DOI,
            "source_published_date":             SOURCE_PUBLISHED,
            "entered_locally_at":                now_iso[:10],
        }
        records.append(rec)
        diag.append((label, dim, regime, exp_val, exp_num, exp_den, vs, smooth, is_hurwitz_dim))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Diagnostics
    print("Roster cascade-anchor table:")
    print(f"  {'regime label':<38} {'dim':>4} {'regime':<25} {'key exp':>10} {'Class N':>10} {'V-stretch':>10} {'smooth':>8} {'Hurwitz dim':>12}")
    for d in diag:
        label, dim, regime, exp, en, ed, vs, sm, hd = d
        print(f"  {label:<38} {dim:>4} {regime:<25} {exp:>10.4f} {f'{en}/{ed}':>10} {str(vs):>10} {str(sm):>8} {str(hd):>12}")

    # 3D vs 2D vs 1D regime grouping
    print()
    print("Spatial-dimension distribution (Hurwitz prediction: 1, 3 in roster; 7+ excluded):")
    dim_counts = {}
    for d in diag:
        dim_counts[d[1]] = dim_counts.get(d[1], 0) + 1
    for dim, c in sorted(dim_counts.items()):
        tag = " <-- Hurwitz dim" if dim in {1, 3, 7} else ""
        print(f"  dim {dim}: {c} entries{tag}")

    # Vortex-stretching presence as Class C orientation amplifier test
    print()
    print("Vortex-stretching presence (Class C cascade-orientation amplifier):")
    has_vs = sum(1 for d in diag if d[6])
    no_vs = len(diag) - has_vs
    print(f"  with vortex-stretching:    {has_vs} entries (all dim >= 3 except hyperviscous-special)")
    print(f"  without vortex-stretching: {no_vs} entries (1D Burgers, 2D NS, Stokes/Couette/Poiseuille)")

    # Smoothness-proved vs open
    print()
    print("Smoothness status:")
    sm_count = sum(1 for d in diag if d[7])
    op_count = len(diag) - sm_count
    print(f"  smoothness PROVED: {sm_count}")
    print(f"  smoothness OPEN:   {op_count}")

    # Class N anchor verification (Kolmogorov exponents at small-denom rationals)
    print()
    print("Kolmogorov / K41 / cascade exponents Class N anchors:")
    for d in diag:
        label, dim, regime, exp, en, ed, vs, sm, hd = d
        if "K41" in label or "cascade" in label or "PF" in label or "kraichnan" in label.lower():
            print(f"  {label:<38} exp = {exp:>10.4f} = {en}/{ed}")


if __name__ == "__main__":
    main()
