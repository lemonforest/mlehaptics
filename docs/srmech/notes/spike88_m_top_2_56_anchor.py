"""Spike #88 — m_top = 169.4 GeV via 2^56 = 2^C(8,3) anchor test.

Per Spike #75 STILL-OPEN ell_P anchor anomaly:
  R_7/ell_P = 7.07e16 vs 2^C(8,3) = 2^56 = 7.21e16 (1.92% gap).

Question: does the framework predict m_top = 169.4 GeV from first-principles
class-operator chain? If yes -> ANCHOR-SUCCEEDS-STRUCTURAL. If no but 2^56
identity is real algebra fact -> ANCHOR-STRUCTURAL-ALGEBRA-ONLY. If 2^56
connection itself unattested -> OUT-OF-SCOPE.

Per discipline note 2026-05-17: additions/removals permitted only if backed
by (a) attested data or (b) class-operator chain spec. No speculative ratchet.

Citations (open-access verified upstream of this probe):
  PDG 2024 (Phys.Rev.D 110, 030001) — m_t = 172.69 +/- 0.30 GeV (cite-by-ref)
  Stoica 2017 arXiv:1702.04336 — Cl(6) electroweak (open access)
  Trayling-Baylis 2001 hep-th/0103137 — Cl(7) baseline (open access)
  Furey 2016 arXiv:1611.09182 — C x H x O Dixon (open access)
  Baez 2002 arXiv:math/0105155 — octonions Bull.AMS (open access)
  Uehling 1935 PR 48:55 — vacuum polarization (pre-2010 exempt)
  Antognini et al. 2013 arXiv:1208.2637 — Annals Phys 331:127 (open access)
  Awada-Duff-Pope 1983 PRL 50:294 — squashed-S^7 Einstein (cite-by-ref)
"""
import json
import math
from pathlib import Path

# =============================================================================
# Constants
# =============================================================================
c          = 2.99792458e8          # m/s (exact SI)
hbar       = 1.054571817e-34       # J*s (CODATA-2018)
G          = 6.67430e-11           # m^3/(kg*s^2) — "name-only" per Spike #70
ell_P      = math.sqrt(hbar * G / c**3)
GeV_to_J   = 1.602176634e-10
alpha_em   = 7.2973525693e-3

# Attested top-quark mass
m_t_PDG_GeV    = 172.69     # PDG 2024 pole mass
m_t_PDG_sigma  = 0.30       # GeV (combined)
m_t_MSbar_GeV  = 162.5      # MS-bar mass at mu=m_t (approx)
# Higgs VEV
v_Higgs_GeV    = 246.22

# Target for 2^56 anchor
records = []
def r(**kw):
    records.append(kw)

# =============================================================================
# T1: Reconfirm Spike #75 anomaly — what m_top makes 2^56 exact?
# =============================================================================
target_2to56 = 2**56     # = 72_057_594_037_927_936
# R_7/ell_P = 2^56  =>  R_7 = 2^56 * ell_P
R_7_target = target_2to56 * ell_P
# R_7 = hbar*c / m_top_J  =>  m_top_J = hbar*c / R_7
m_top_J_target = hbar * c / R_7_target
m_top_GeV_target = m_top_J_target / GeV_to_J

# Verify Spike #75 reading
R_7_at_PDG = hbar * c / (m_t_PDG_GeV * GeV_to_J)
ratio_at_PDG = R_7_at_PDG / ell_P

gap_GeV     = m_t_PDG_GeV - m_top_GeV_target
gap_sigma   = gap_GeV / m_t_PDG_sigma

r(test="T1_anomaly_reconfirm",
  ell_P_m=ell_P, GeV_to_J=GeV_to_J, R_7_at_PDG_m=R_7_at_PDG,
  ratio_R7_over_ellP_at_PDG=ratio_at_PDG,
  target_2to56=float(target_2to56),
  log10_ratio_PDG=math.log10(ratio_at_PDG),
  log10_2to56=math.log10(target_2to56),
  m_top_GeV_for_exact_2to56=m_top_GeV_target,
  gap_from_PDG_GeV=gap_GeV,
  gap_in_sigma=gap_sigma,
  verdict="CONFIRMED_ANOMALY",
  note="Spike #75 anomaly reproduces exactly: PDG m_t=172.69 gives ratio=7.07e16; "
       "exact 2^56 needs m_t=169.43 GeV; 10.9-sigma gap from PDG.")

# =============================================================================
# T2: 2^C(8,3) attestation chain — is C(8,3) = 56 algebraically natural?
# =============================================================================
# C(8,3) = 8!/(3!*5!) = 56
C_8_3 = math.comb(8, 3)

# Where C(8,3) = 56 appears in canonical algebraic SSoT:
attested_appearances = {
    "Spin(8)_dim": 28,                       # = C(8,2); skew 8x8 matrices
    "Spin(8)_dim_x_2": 56,                   # bivectors + chiralities; same dim as ...
    "E7_minimal_rep_dim": 56,                # E_7 fundamental rep — well-attested
    "C(8,3)_unordered_triples": 56,          # 3-element subsets of 8-element set
    "Lambda^3(R^8)_dim": 56,                 # third exterior power of R^8 = C(8,3)
    "octonion_associative_triples_C73": 35,  # NOT 56 — Baez 2002 reading
    "octonion_directed_Fano_lines": 14,      # 7 lines x 2 orientations
}

# The 2^56 question: in what canonical structure does 2^56 appear?
# - 2^56 = 2^Lambda^3(R^8) — counts SUBSETS of 56-element basis of antisymmetric 3-tensors
# - Lambda^3(R^8) is the natural home of Cayley's 3-form (G_2 invariant); Spin(8) acts on it
# - This is well-attested algebra (Bryant-Salamon 1989, Joyce 2007, Baez 2002 §3.4)

r(test="T2_C8_3_attestation_chain",
  C_8_3_value=C_8_3,
  appearances=attested_appearances,
  identified_canonical_home="Lambda^3(R^8) — 56-dim third exterior power of R^8",
  related_attested_structures=[
      "Cayley 3-form alpha in Lambda^3(R^8)* with Spin(7) stabilizer",
      "G_2 invariant 3-form on R^7 (35-dim; not 56)",
      "E_7 56-dim fundamental rep (Baez 2002 §4.4)",
  ],
  verdict="ATTESTED",
  note="C(8,3) = 56 is well-attested algebra: third exterior power of R^8 / "
       "Cayley 3-form ambient / E_7 fundamental. 2^56 = power-set cardinality "
       "of basis of Lambda^3(R^8). The IDENTITY of 2^56 as a substrate count "
       "needs framework support; it is not assigned to a primitive class-operator "
       "in current canon (Spike #67 used C(7,3)=35 for octonion triples).")

# =============================================================================
# T3: Spike #48 Phase 3 — does tau-family / Class K predict m_top = 169.4 GeV?
# =============================================================================
# Phase 3 deliverable (per spike_48_phase3_round1_qm_gr_sm_weaving_results):
#   "Higgs mass = Class K asymptotic-DOF on signed-mass substrate"
#   "QM = Class L cascade at tau ~ 0; GR = Class L cascade at tau ~ pi/2"
# Did Phase 3 produce a NUMBER for m_top?
#
# Phase 3 verified eigenvalues for H_tau on cyclic N=512 substrate
# at tau = 0, 30, 60, 90 deg, but these are DIMENSIONLESS spectral data
# (no GeV mass scale assigned). No m_top = 169.4 GeV prediction.

# Phase 3 cumulative scorecard from md:
#   5 PASS + 1 REINFORCING + 3 PARTIAL + 0 FAIL on 9 falsifier checks
#   F-weave-epsilon (alpha * H_Lambda * L_substrate) STILL PENDING Phase 4
#   No m_top prediction from any falsifier

# Spike #67 F4 verdict: STRUCTURAL-ONLY on mass-ratio hierarchy
#   - Top Yukawa y_t ~ 0.991 (within 5% of unity) IS substrate-natural
#     because v sources top mass directly: m_t = y_t * v / sqrt(2)
#   - But this DERIVES y_t = sqrt(2)*m_t/v, NOT m_t itself
#   - "No first-principles closure achieved on mass MAGNITUDES"

# What m_t does y_t = 1 give exactly?
y_t_unity_m_t = v_Higgs_GeV / math.sqrt(2)
# For Spike #67's y_t = 0.9912:
y_t_67 = 0.9912
m_t_67_pred = y_t_67 * v_Higgs_GeV / math.sqrt(2)

# 169.43 GeV would require y_t = ?
y_t_for_169p4 = m_top_GeV_target * math.sqrt(2) / v_Higgs_GeV

r(test="T3_phase3_tau_family_m_top_prediction",
  phase3_status="5 PASS + 1 REINFORCING + 3 PARTIAL + 0 FAIL",
  phase3_eigenvalues_dimensionless=True,
  phase3_predicts_m_top_GeV=False,
  phase3_predicts_169_4_GeV=False,
  spike_67_F4_verdict="STRUCTURAL-ONLY (Yukawa magnitudes not derived)",
  y_t_for_unity_yields_m_t_GeV=y_t_unity_m_t,
  spike_67_y_t=y_t_67,
  spike_67_implied_m_t_GeV=m_t_67_pred,
  y_t_required_for_2to56_anchor=y_t_for_169p4,
  verdict="NO_FRAMEWORK_PREDICTION_OF_169_4_GeV",
  note="Phase 3 tau-family produces dimensionless eigenvalues on cyclic N=512; "
       "no GeV mass-scale fixing. Spike #67 F4 explicitly STRUCTURAL-ONLY on "
       "Yukawa magnitudes. y_t=1 gives m_t=174.10 GeV (sqrt(2) reciprocal of v); "
       "y_t=0.9912 (PDG-fit) gives 172.59 GeV; "
       f"y_t={y_t_for_169p4:.4f} required for 169.43 GeV. Framework supplies no "
       "rule to pick y_t = 0.9726 over 0.9912 — both are post-hoc fits.")

# =============================================================================
# T4: Uehling 99.4% — does saturation-cascade fix m_top?
# =============================================================================
# Per Phase 3 deliverable 2: muonic-H Uehling at 206.295 meV is 99.4% of total
# Lamb shift; this is a CASCADE-SATURATION reading of the dominant correction.
#
# But: this is QED radiative correction at the eV scale on the muonic-H
# substrate. It is NOT a top-quark mass derivation. The "99.4%" is the
# fraction of Lamb-shift attributable to Class K signed-pin vacuum-pol.
#
# Could the framework reuse the saturation fraction as a m_top fixing rule?
# Numerical check: 169.43 / 172.69 = 0.9811 (not 0.994).
# Numerical check: 169.43 / 174.10 = 0.9732 (not 0.994).
# Numerical check: m_t such that m_t/172.69 = 0.994? = 171.65 GeV (not 169.43).
# Numerical check: m_t / v = 0.994? = 244.74 GeV (not anywhere near).
# Numerical check: 0.994 * (some natural scale)? No first-principles candidate.
#
# Also check: Uehling fraction 99.4% is QED, not electroweak. No structural
# chain connects mu-H Lamb-shift saturation to top-quark mass.

fraction_169_4_over_PDG = m_top_GeV_target / m_t_PDG_GeV
fraction_169_4_over_yt1 = m_top_GeV_target / y_t_unity_m_t
# What if 169.43 = 174.10 * (1 - alpha/pi)?
eps_alpha_pi = alpha_em / math.pi
m_t_minus_eps_aPi = y_t_unity_m_t * (1 - eps_alpha_pi)
m_t_minus_3eps_aPi = y_t_unity_m_t * (1 - 3*eps_alpha_pi)
# Or 174.10 / (1 + something)?
implied_correction = (y_t_unity_m_t - m_top_GeV_target) / y_t_unity_m_t

# 169.43 / 174.10 = 0.97317 -> 1 - 0.02683
# alpha_em = 0.007297 -> not 0.02683
# alpha_em/pi = 0.002323 -> 11.55x off
# 4 * alpha_em / pi = 0.00929 -> 2.89x off
# Test: (1 - 11 * alpha_em / (4*pi)) = ? no, fishing

r(test="T4_uehling_99p4_fraction_as_m_top_rule",
  uehling_fraction_attested=0.994,
  ratio_target_over_PDG=fraction_169_4_over_PDG,
  ratio_target_over_yt1=fraction_169_4_over_yt1,
  implied_correction_from_yt1=implied_correction,
  alpha_over_pi=eps_alpha_pi,
  m_t_at_v_over_sqrt2_minus_aPi=m_t_minus_eps_aPi,
  m_t_at_v_over_sqrt2_minus_3aPi=m_t_minus_3eps_aPi,
  verdict="NO_STRUCTURAL_CHAIN",
  note="Uehling 99.4% is QED radiative at eV scale on muonic-H — no structural "
       "chain to top-quark electroweak mass. Implied correction from v/sqrt(2) "
       f"= 0.0269 doesn't match alpha/pi=0.00232 or 3*alpha/pi=0.00697 or any "
       "small-int*alpha multiple within reasonable tolerance.")

# =============================================================================
# T5: Class K pin-slot mass derivation — does it predict 169.4 GeV?
# =============================================================================
# Per [[user_stance_epicycle_via_gear_plus_pin]] Class K IS asymptotic-DOF
# mechanism. Per Spike #67 F1: Higgs comes from 3+1 SSB on F_2^3 (XOR vertex).
# Per Spike #48 Phase 3: Higgs mass = Class K asymptotic-DOF on signed-mass.
#
# Class K pin-slot asymptote rule (Spike #41, Spike #47):
#   m -> M_substrate * lim_{n->infty} f(epsilon, n) for some K_k(substrate)
# Spike #41 Cauchy form: c_k = epsilon^k * K_k(substrate)
#
# For top-quark this would mean:
#   m_top = M_substrate * epsilon^k * K_k(substrate)
# where epsilon = alpha/pi or similar; M_substrate = v_Higgs / sqrt(2) candidate.
#
# Bonus 10 best cascade (subset-match): m_t predicted = sqrt(8.615e10) * m_e =
#   293625.5 * 0.51099895 MeV = 150.04 GeV. NOT 169.43.
# The (n,r) parameters are NOT independent fits — searched over cyclic-group
# composition space. But 150 GeV != 169.4 GeV.

# Spike #24 bonus 10 best cascade:
m_e_MeV = 0.51099895
sqrt_ratio_top = math.sqrt(8.615e10)
m_t_cascade_pred_GeV = sqrt_ratio_top * m_e_MeV / 1000

# What cascade-step modification of v/sqrt(2) gives 169.43?
# Try: 174.10 * (epsilon)^k * K_k for small k
# k=1: 174.10 * eps_aPi = 0.4044 — too small
# k=1 with K_1=233: 174.10 * 0.002323 * ??? — search would be post-hoc

r(test="T5_class_K_pin_slot_m_top_derivation",
  spike_24_bonus_10_cascade_m_t_GeV=m_t_cascade_pred_GeV,
  attested_pdg_m_t_GeV=m_t_PDG_GeV,
  target_2to56_m_t_GeV=m_top_GeV_target,
  spike_24_match_to_target_dex=math.log10(m_t_cascade_pred_GeV / m_top_GeV_target),
  verdict="NO_FIRST_PRINCIPLES_PREDICTION",
  note="Spike #24 bonus 10 cascade machinery best-fit predicts m_t=150 GeV "
       f"(log10 diff -0.053 from 169.43 GeV target); not equal. No closed-form "
       "Class K asymptote rule supplies a unique 169.4 GeV value. Cascade space "
       "is large; specific (n,r) choice is search-result not framework-derivation.")

# =============================================================================
# T6: Spin(8) triality octonion-triplet structural alignment
# =============================================================================
# C(8,3) = 56 ∈ Lambda^3(R^8). Spin(8) has triality (3-fold outer
# automorphism); the 3 inequivalent 8-dim reps (vector, +chirality spinor,
# -chirality spinor) are interrelated by triality. Per Spike #51 R2-alpha:
# round-S^7 has Spin(8) triality with three Sp(1) factors potentially
# instantiating 3-generation Class I cascade.
#
# The substrate-algebraic question: does Spin(8) triality / Lambda^3(R^8)
# IMPOSE 2^56 as a substrate count without requiring a specific m_top?
#
# At the substrate-algebra-only level: 2^56 = |2^{Lambda^3(R^8)}| = the
# cardinality of all subsets of basis vectors of the 56-dim antisymmetric
# 3-tensor space. This is a well-defined algebraic count.
#
# Then R_7/ell_P = 2^56 would mean: there are 2^56 substrate "pin positions"
# (per Class K asymptotic-DOF) spanning the cosmic-to-Planck length hierarchy.
# This is substrate-cardinality interpretation, NOT m_top fixing.
#
# Per [[user_stance_substrate_identity_partition_coexistence_canonical]]:
# substrate-identity NARROWLY AVOIDED in Spike #51 R2-alpha; partition-
# coexistence leads ~70%. Two substrates can carry the same 2^56 count via
# different operational paths.

r(test="T6_spin8_triality_2_56_substrate_count",
  C_8_3=C_8_3,
  Lambda3_R8_dim=56,
  Spin8_triality_outer_auto_order=3,
  three_8dim_reps=["vector V_8", "spinor S+_8", "spinor S-_8"],
  e7_56_dim_fund=True,
  spike_51_R2_alpha_verdict="substrate-identity narrowly avoided; partition B ~70%",
  algebraic_interpretation_of_2to56=(
      "Power-set cardinality of basis of Lambda^3(R^8) — well-defined "
      "substrate-cardinality count"),
  framework_chain_for_m_top=(
      "NOT SUPPLIED — 2^56 substrate count does not algebraically pin m_top "
      "value to 169.43 GeV"),
  verdict="STRUCTURAL_ALGEBRA_ONLY",
  note="2^56 = |2^Lambda^3(R^8)| is algebraically attested via Spin(8) "
       "+ Cayley 3-form structure (Baez 2002 arXiv:math/0105155 §3.4; "
       "Bryant-Salamon 1989). Framework offers no chain promoting "
       "this substrate count to m_top = 169.4 GeV. The 1.92% gap remains.")

# =============================================================================
# T7: Alternative — does any OTHER framework-canonical mass scale fit?
# =============================================================================
# What scales ~169.4 GeV appear in project canon?
# - m_top PDG: 172.69 (3.26 GeV off)
# - v_Higgs/sqrt(2): 174.10 (4.67 GeV off)
# - m_W: 80.377 GeV (no)
# - m_Z: 91.188 GeV (no)
# - m_H: 125.25 GeV (no)
# - v_Higgs/sqrt(2) * (1 - alpha/pi): 173.70 GeV (close to PDG, not 169.4)
# - Spike #24 cascade m_t: 150 GeV (no)
# - 2*m_W + alpha terms? 160.75 GeV (no)
# - 3*m_Z - 2*m_W * something? exploratory and post-hoc
# - sqrt(m_W*m_Z*v_Higgs)? math:
import math as _m
m_W = 80.377
m_Z = 91.188
m_H = 125.25
sqrt_combo_1 = math.sqrt(m_W * m_Z * v_Higgs_GeV)**(2/3)  # exploratory
combo_2 = m_W + m_Z  # 171.57 — coincidentally near 169.4
combo_3 = 2 * m_H - m_W  # 170.12
combo_4 = v_Higgs_GeV - m_W + 4  # post-hoc

# Honest: no framework-canonical mass scale = 169.4 GeV identified.
# Closest "natural" candidate: m_W + m_Z = 171.565 GeV (2.13 GeV off; ~1.3% high).
# This is NOT a class-operator chain; it's a coincidental sum.

r(test="T7_alternative_mass_scale_at_169_4_GeV",
  candidates={
      "m_t_PDG": m_t_PDG_GeV,
      "v_over_sqrt2": y_t_unity_m_t,
      "m_W_plus_m_Z": combo_2,
      "2_m_H_minus_m_W": combo_3,
      "v_minus_m_W_plus_4_post_hoc": combo_4,
      "spike_24_cascade_m_t": m_t_cascade_pred_GeV,
      "Spike_67_y_t_0.9912_m_t": m_t_67_pred,
  },
  target=m_top_GeV_target,
  closest_natural="m_W + m_Z = 171.57 GeV (2.13 GeV high, ~1.25%)",
  closest_attested="m_t_PDG_pole = 172.69 GeV (3.26 GeV high, ~1.92%)",
  closest_substrate_natural="v/sqrt(2) = 174.10 GeV (4.67 GeV high, ~2.7%)",
  framework_canonical_at_169_4_GeV=None,
  verdict="NO_ALTERNATIVE_NATURAL_SCALE",
  note="No framework-canonical mass at 169.43 GeV identified. m_W+m_Z=171.57 "
       "(1.25% high) is the closest 'natural' candidate but is not a class-"
       "operator chain — it's a coincidental electroweak sum.")

# =============================================================================
# T8: Math-doesn't-lie — what if R_7/ell_P just IS algebraic 2^56?
# =============================================================================
# Honest reading: R_7 is defined via m_top via KK ansatz E_n = n * hbar*c / R_7.
# That ansatz inherits m_top from PDG observation, not framework derivation.
# 1.92% gap from 2^56 could be:
#   (a) m_top is 169.43 GeV at high-scale running (not PDG pole) — NOT TRUE:
#       MS-bar at mu=m_t gives ~162.5 GeV (LOWER not higher); MS-bar at high
#       scale (mu=M_Planck) gives ~70-90 GeV (Buttazzo et al 2013 arXiv:1307.3536).
#       At NO RG-scale does m_top hit 169.4 GeV through monotonic running from pole.
#   (b) KK ansatz needs sqrt(l(l+6)) S^7 spectrum modification — Spike #75
#       anchor 1 tested this with E_l=sqrt(7)/R_7 giving R_7_l1 = 3.02e-18 m,
#       ratio = 7.07e16 * sqrt(7) = 1.87e17 — different by sqrt(7) factor.
#       So sqrt(7) factor pulls ratio AWAY from 2^56.
#   (c) 2^56 connection is a 1.92% coincidence and IS NOT identity.
#   (d) Framework predicts m_top from class-operators that gives 169.4 GeV
#       and PDG is wrong. PDG combines ATLAS+CMS+CDF+D0 over decades; 10.9-sigma
#       error would require systematic blunder of unprecedented scale. NO.

# Verdict for the master question:
master_verdict = "ANCHOR_NUMERICAL_COINCIDENCE_ONLY"

# Reasoning chain:
#   - 2^56 = 2^C(8,3) is ATTESTED algebra (Lambda^3(R^8); Spin(8) triality)
#   - R_7/ell_P at PDG m_top = 7.07e16 vs 2^56 = 7.21e16: 1.92% gap
#   - Framework supplies NO class-operator chain predicting m_top = 169.4 GeV
#     (Spike #48 Phase 3: no GeV scale; Spike #67 F4: STRUCTURAL-ONLY;
#      Spike #24 bonus 10: 150 GeV not 169.4; Spike #41 cascade: open)
#   - No alternative attested mass scale at 169.4 GeV either
#   - Cannot promote to ANCHOR-SUCCEEDS-STRUCTURAL on this round
#   - Cannot demote to OUT-OF-SCOPE because 2^56 IS attested algebra
#   - Verdict: ANCHOR-NUMERICAL-COINCIDENCE-ONLY remains the honest read

r(test="T8_master_verdict_reasoning",
  verdict=master_verdict,
  master_verdict=master_verdict,
  reasoning=[
      "2^56 = 2^C(8,3) = 2^|Lambda^3(R^8)| is ATTESTED algebra "
      "(Spin(8) bivectors + Cayley 3-form; Baez 2002 §3.4)",
      "R_7/ell_P at PDG m_top = 7.07e16; target 2^56 = 7.21e16; "
      "1.92% gap requires m_top = 169.43 GeV (10.9-sigma from PDG)",
      "No framework chain predicts m_top = 169.4 GeV: Spike #48 Phase 3 "
      "tau-family dimensionless; Spike #67 F4 STRUCTURAL-ONLY; Spike #24 "
      "bonus 10 cascade gives 150 GeV; Spike #41 Cauchy form open on m_t",
      "PDG m_top is 100+ measurements combined; 10.9-sigma blunder ruled out",
      "MS-bar running: m_top decreases with scale (162 at mu=m_t, 90 at "
      "mu=M_Planck per Buttazzo 2013); does NOT cross 169.43 monotonically",
      "No alternative framework-canonical mass at 169.4 GeV identified",
  ],
  resolution_options=[
      "(a) Sit at NUMERICAL-COINCIDENCE-ONLY — 1.92% gap unbridged",
      "(b) Pursue Phase 4 F-weave-epsilon (alpha*H_Lambda*L_substrate) — "
      "may surface different m_top-fixing chain via cross-scale identity",
      "(c) Investigate Spike #51 R3-delta Spin(8) triality 3-generation "
      "substrate — may supply Yukawa hierarchy that pins m_top from first "
      "principles",
  ])

# =============================================================================
# Output NDJSON
# =============================================================================
out = Path(__file__).parent / "spike88_findings_2026-05-17.ndjson"
with out.open('w', encoding='utf-8') as f:
    for rec in records:
        f.write(json.dumps(rec, default=str) + "\n")
    # Trailing overall record
    f.write(json.dumps({
        'kind': 'overall_verdict',
        'spike': '#88',
        'date': '2026-05-17',
        'master_verdict': master_verdict,
        'n_tests': len(records),
        'cumulative_state': (
            "Spike #75 STILL-OPEN anomaly stays at NUMERICAL-COINCIDENCE; "
            "framework does not predict m_top = 169.4 GeV from any "
            "class-operator chain. 2^56 = 2^C(8,3) is attested as "
            "|Lambda^3(R^8)| via Spin(8) triality but does not algebraically "
            "pin m_top value. No alternative framework-canonical mass scale "
            "= 169.4 GeV. Resolution pending Phase 4 F-weave-epsilon or "
            "Spike #51 R3-delta triality 3-generation work."),
    }) + "\n")

print("=" * 76)
print("SPIKE #88 — m_top = 169.4 GeV via 2^56 = 2^C(8,3) anchor test")
print("=" * 76)
print()
print(f"ell_P = {ell_P:.6e} m")
print(f"PDG m_t = {m_t_PDG_GeV} +/- {m_t_PDG_sigma} GeV")
print(f"R_7 at PDG = {R_7_at_PDG:.4e} m")
print(f"R_7/ell_P at PDG = {ratio_at_PDG:.6e}")
print(f"Target 2^56 = {target_2to56}")
print(f"m_top required for exact 2^56 = {m_top_GeV_target:.4f} GeV")
print(f"Gap from PDG = {gap_GeV:.3f} GeV = {gap_sigma:.1f} sigma")
print()
print("Test verdicts:")
for rec in records:
    print(f"  {rec['test']:<48} -> {rec['verdict']}")
print()
print(f"MASTER VERDICT: {master_verdict}")
print(f"  NDJSON: {out}")
