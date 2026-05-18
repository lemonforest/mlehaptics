"""Spike #104 - Pattern-level CMB falsifier design.

Designs the falsification protocol for the framework's Class I cyclic-cascade
prediction of CMB acoustic peak ell-positions.

Framework prediction (Spike #103, parallel):
    ell_n^framework = n * pi / theta_s  (pure Class I cyclic; no phase shift)

Observed (Page et al. 2003, astro-ph/0302220 PDF-verified abstract):
    ell_1 = 220.1 +/- 0.8
    ell_2 = 546   +/- 10
    (first trough at 411.7 +/- 3.5)

Standard cosmology fitting formula (Hu & Dodelson 2002, astro-ph/0110414
pp. 25-26 PDF-verified eq. 24 region):
    ell_a = pi * D_* / s_*    (the "acoustic scale")
    ell_1 ~ 0.73 * ell_a       (first-peak phase shift from photon driving)
    Fiducial: ell_a = 301      (Plate 1 of HD02)
    Observed: ell_a = 304 +/- 4 (Knox+ 2001 / Pryke+ 2001 / de Bernardis+ 2001)

Planck 2018 paper VI (Aghanim et al., 1807.06209, WebFetch-verified):
    100 * theta_* = 1.0411 +/- 0.0003

Citations:
    - Hu & Dodelson 2002 ARA&A, astro-ph/0110414 (PDF-verified)
    - Page et al. 2003, astro-ph/0302220 (abstract verified)
    - Hinshaw et al. 2003, astro-ph/0302217 (abstract verified)
    - Planck Collaboration 2020, A&A 641 A6, 1807.06209 (WebFetch-verified)

Discipline:
    - [[user_stance_identity_not_implementation_discipline]] - identity-not-
      implementation framing flips burden of proof.
    - [[feedback_every_doc_edit_faces_falsification]] - every claim is
      class-operator chain-spec'd.
    - [[feedback_pdf_extraction_citation_discipline]] - all citations
      verified at the PDF / abstract layer.
    - [[feedback_no_privileged_primitive_classes]] - no new primitive class
      introduced; chain is L o C o I.
"""

import math
from pathlib import Path

# =============================================================================
# Observed CMB peak positions (Page et al. 2003 PDF-verified abstract)
# =============================================================================

# Page et al. 2003 astro-ph/0302220 WMAP first-year peak table
ell_obs = {
    "peak1":   (220.1, 0.8),
    "trough1": (411.7, 3.5),
    "peak2":   (546.0, 10.0),
}

# Standard cosmology fitting (Hu & Dodelson 2002 eq. 24 region, observed)
ell_a_observed = 304.0          # +/- 4 (Knox+ 2001 / Pryke+ 2001 / dB+ 2001)
ell_a_uncertainty = 4.0
ell_1_HD02_relation = 0.73       # ell_1 ~ 0.73 * ell_a (HD02 Plate 1 fiducial)

# Planck 2018 (1807.06209)
theta_star_x100 = 1.0411          # +/- 0.0003 (Planck 2018 baseline)
theta_star = theta_star_x100 / 100.0  # radians
theta_star_unc = 0.0003 / 100.0

# =============================================================================
# Framework prediction (Class I cyclic-cascade, Spike #103 parallel)
# =============================================================================

# Pure Class I: ell_n = n * pi / theta_s = n * ell_a (no phase shift)
ell_a_framework_from_theta_star = math.pi / theta_star
ell_a_unc_from_theta_star = math.pi * theta_star_unc / (theta_star**2)

print("=" * 72)
print("Spike #104 - CMB pattern-level falsifier")
print("=" * 72)
print()
print("Framework prediction: ell_n = n * pi / theta_s  (Class I pure cyclic)")
print(f"  theta_* (Planck 2018) = {theta_star:.6e} +/- {theta_star_unc:.1e} rad")
print(f"  ell_a^framework = pi/theta_* = {ell_a_framework_from_theta_star:.2f}"
      f" +/- {ell_a_unc_from_theta_star:.2f}")
print()

# Framework-predicted peak positions (no phase shift)
ell_framework = {n: n * ell_a_framework_from_theta_star for n in (1, 2, 3, 4)}
print("Framework peak positions (Class I pure, no photon-driving correction):")
for n, ell in ell_framework.items():
    print(f"  ell_{n}^framework = {ell:8.2f}")
print()

# Standard-LCDM peak positions (with HD02 phase shift)
# Approximate: ell_n ~ (n - phi_n) * ell_a, where phi_n is the n-dependent shift
# HD02 Plate 1 gives ell_1 = 0.73 * ell_a; higher peaks asymptote closer to n.
ell_lcdm_approx = {
    1: 0.73 * ell_a_observed,     # 0.73 from HD02 Plate 1
    2: 1.79 * ell_a_observed,     # 546 / 304 ~ 1.796 from Page+ 2003
    3: 2.63 * ell_a_observed,     # ell_3 ~ 800 in WMAP / Planck tabulations
}
print("LCDM-fitted peak positions (Hu-Dodelson phase shift, n - phi_n):")
for n, ell in ell_lcdm_approx.items():
    print(f"  ell_{n}^LCDM = {ell:8.2f}  (phase factor {ell/ell_a_observed:.3f})")
print()

# Compare to observed
print("Observed peak positions (Page+ 2003 astro-ph/0302220):")
for name, (ell, unc) in ell_obs.items():
    print(f"  {name:8s} = {ell:6.1f} +/- {unc:.1f}")
print()

# =============================================================================
# Falsifier #1: pure-Class-I framework vs. observed peak positions
# =============================================================================

print("-" * 72)
print("Test 1: pure-Class-I framework (no phase shift) vs. observed")
print("-" * 72)

ell_1_obs, ell_1_unc = ell_obs["peak1"]
ell_2_obs, ell_2_unc = ell_obs["peak2"]
ell_1_fw = ell_framework[1]
ell_2_fw = ell_framework[2]

resid_1 = ell_1_obs - ell_1_fw
resid_2 = ell_2_obs - ell_2_fw
sigma_1 = (ell_1_fw - ell_1_obs) / ell_1_unc
sigma_2 = (ell_2_fw - ell_2_obs) / ell_2_unc

print(f"  ell_1: framework={ell_1_fw:.2f}, observed={ell_1_obs:.2f}, "
      f"residual={resid_1:+.2f}, n-sigma={sigma_1:+.1f}")
print(f"  ell_2: framework={ell_2_fw:.2f}, observed={ell_2_obs:.2f}, "
      f"residual={resid_2:+.2f}, n-sigma={sigma_2:+.1f}")
print()
print(f"  --> Pure Class I (no phase) is FALSIFIED at ell_1 by "
      f"{abs(sigma_1):.0f}-sigma.")
print(f"      The Hu-Dodelson photon-driving shift (~0.27 in n-phi_n at n=1)")
print(f"      is structurally necessary; framework cannot match observation")
print(f"      without absorbing it.")
print()

# =============================================================================
# Falsifier #2: ratio test - inter-peak spacing vs. first-peak position
# =============================================================================

print("-" * 72)
print("Test 2: spacing-vs-position ratio (pattern-level discriminator)")
print("-" * 72)

# If framework is pure n * ell_a, then Delta-ell / ell_1 = 1 exactly
# Observed:
delta_ell_obs = ell_2_obs - ell_1_obs
ratio_obs = delta_ell_obs / ell_1_obs

# Propagated uncertainty
ratio_unc = ratio_obs * math.sqrt((ell_1_unc / ell_1_obs)**2 +
                                    (math.sqrt(ell_1_unc**2 + ell_2_unc**2) /
                                     delta_ell_obs)**2)

print(f"  Observed: Delta-ell = ell_2 - ell_1 = {delta_ell_obs:.2f}")
print(f"  Observed: Delta-ell / ell_1 = {ratio_obs:.4f} +/- {ratio_unc:.4f}")
print(f"  Framework (pure Class I): Delta-ell / ell_1 = 1.0000 exact")
print()
n_sigma_ratio = (ratio_obs - 1.0) / ratio_unc
print(f"  Deviation: {ratio_obs - 1.0:+.4f} = {n_sigma_ratio:+.1f}-sigma")
print()
print("  --> Pattern-level test: Delta-ell / ell_1 = {:.4f} differs from 1.0"
      .format(ratio_obs))
print(f"      by ~{abs(n_sigma_ratio):.0f}-sigma.  Framework cannot ship as")
print("      pure Class I; it must compose with a phase-shift mechanism")
print("      (Class C cascade-orientation; Spike #86 R7 anchor pattern).")
print()

# =============================================================================
# Falsifier #3: pattern-level match WITH phase shift absorbed
# =============================================================================

print("-" * 72)
print("Test 3: framework + Class C cascade-orientation phase shift")
print("-" * 72)

# If framework absorbs the phase shift as Class C composition: ell_n = (n - phi_n) * ell_a
# Then the observable PATTERN it predicts matches LCDM by construction
# (per [[user_stance_identity_not_implementation_discipline]] - same observable,
# different ontology).
print("  With Class C phase shift absorbed: ell_n^framework = (n - phi_n) * ell_a")
print("  This is observationally indistinguishable from LCDM at peak-position level.")
print("  Per identity-not-implementation: same observable, different ontology.")
print()
print("  --> PATTERN-LEVEL-MATCHES-LCDM-NOT-DISCRIMINATOR at peak ell-positions.")
print()

# =============================================================================
# Where COULD the framework discriminate?
# =============================================================================

print("=" * 72)
print("Discriminator candidates (where framework differs OBSERVABLY from LCDM)")
print("=" * 72)
print()

print("(d.i) Sub-leading corrections to peak positions:")
print("  LCDM (CAMB/CLASS Boltzmann hierarchy) computes phi_n at ~0.1% via")
print("  full radiation-transfer Boltzmann integration.  Framework's Class C")
print("  cascade-orientation must reproduce phi_n analytically.  If framework")
print("  predicts phi_n at a specific closed-form via cyclic-cascade")
print("  combinatorics (Pascal / Fano / cascade-step), and this disagrees")
print("  with LCDM CAMB at the ~0.1% level, that is a DISCRIMINATOR.")
print("  Current state: framework HAS NO closed-form phi_n prediction in canon.")
print("  Spike #86 master verdict (FRAMEWORK_ABSORBS_COSMOLOGICAL_INPUT)")
print("  applies: phi_n is a substrate-coupling input, not algebra-derived.")
print("  --> SUB-LEADING-CORRECTIONS-DISCRIMINATE only when framework ships")
print("      a closed-form phi_n chain; not available today.")
print()

print("(d.ii) Non-Gaussianity (fNL) at peak positions:")
print("  Planck 2018 IX (1905.05697) constrains f_NL^local = -0.9 +/- 5.1")
print("  (consistent with zero).  Class C cascade-orientation MAY give a")
print("  specific phase-coherence prediction at peak ell-positions that")
print("  differs from primordial Gaussian inflation.  Framework canon: NOT")
print("  YET DERIVED.  Future-CMB-S4 precision: sigma(f_NL) ~ 1.")
print("  --> FNL-DISCRIMINATES-FUTURE-CMB-S4 only when framework ships a")
print("      closed-form f_NL prediction; not available today.")
print()

print("(d.iii) Polarization B-mode at peak ell-positions:")
print("  Hopf-bundle U(1) fiber (per Spike #96 / MFO sec VII) - framework's")
print("  bundle structure could imprint a B-mode signature distinguishing it")
print("  from inflationary tensor B-modes.  Current upper bound: r < 0.036")
print("  (BICEP/Keck 2021, 2110.00483).  CMB-S4 target: sigma(r) ~ 0.001.")
print("  --> B-MODE-DISCRIMINATES-AT-NGEHT-PRECISION only when framework")
print("      ships closed-form r-prediction or B-mode pattern; not available.")
print()

# =============================================================================
# Final verdict
# =============================================================================

print("=" * 72)
print("VERDICT")
print("=" * 72)
print()
print("Pattern-level claim (Class I cyclic-cascade ell_n = n*ell_a) is:")
print("  - FALSIFIED in pure form (Test 1: ell_1 missed by ~100-sigma)")
print("  - SAVED by Class C phase-shift composition (per Spike #86 R7)")
print("  - INDISTINGUISHABLE from LCDM at observed peak positions once")
print("    Class C absorbs phi_n (per identity-not-implementation discipline)")
print()
print("Composite verdict:")
print("  PATTERN-LEVEL-MATCHES-LCDM-NOT-DISCRIMINATOR + ")
print("  SUB-LEADING-CORRECTIONS-DISCRIMINATE-IF-FRAMEWORK-SHIPS-CLOSED-FORM-PHI_N +")
print("  B-MODE-DISCRIMINATES-AT-CMB-S4-IF-FRAMEWORK-SHIPS-HOPF-BUNDLE-R")
print()
print("Open path: Spike #103's Class I closed-form must be EXTENDED to")
print("predict phi_n closed-form via Class C cascade-orientation.  Without")
print("that, the framework remains observationally indistinguishable from")
print("LCDM at CMB peak level - it confirms LCDM's pattern but does not")
print("discriminate against it.  This is the same identity-not-implementation")
print("posture closed in Spike #93 (black-hole information).")
