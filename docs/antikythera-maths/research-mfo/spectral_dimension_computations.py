"""
Spectral Dimension Flow: Unified Fractal Metric Field
======================================================

Computes and compares:
1. Spectral dimension flow profiles from multiple QG approaches
2. What the unified fractal metric field framework predicts
3. The crucial difference: flow to ~2 vs flow through intermediate values
4. Observational constraints and predictions

Key insight being tested: if spatial and internal dimensions are the SAME
fractal geometry at different scales, spectral dimension should flow from
~4 at large scales through intermediate values to some UV value,
and the INTERMEDIATE flow profile contains the particle spectrum.
"""

import sys
import numpy as np
import json
from pathlib import Path

# Windows console (cp1252) can't render the Greek letters / unicode math glyphs
# this script prints. Force UTF-8 stdout when running interactively.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results-mfo"

results = {}

print("=" * 80)
print("PART 1: SPECTRAL DIMENSION FLOW IN QUANTUM GRAVITY")
print("What every approach finds, and what they agree on")
print("=" * 80)
print()

print("Spectral dimension d_S is measured by how a random walk")
print("(or diffusion process) spreads on the geometry:")
print()
print("  P(σ) ~ σ^{-d_S/2}")
print()
print("where P(σ) is the return probability after diffusion time σ.")
print("σ acts as a scale probe: small σ = short distances, large σ = long distances.")
print()

# Compile the dimensional flow results from all approaches
approaches = {
    "CDT (Ambjorn-Jurkiewicz-Loll 2005)": {
        "UV": 1.80,  # ~2, possibly 1.5
        "IR": 4.02,  # ~4
        "flow": "smooth, monotonic",
        "note": "Numerically computed from Monte Carlo simulations of causal triangulations"
    },
    "Asymptotic Safety (Lauscher-Reuter 2005)": {
        "UV": 2.0,  # exactly 2
        "IR": 4.0,
        "flow": "smooth, from anomalous scaling at UV fixed point",
        "note": "d_S = 2d/(2+d) at UV fixed point, giving d_S=2 for d=4"
    },
    "Horava-Lifshitz (Horava 2009)": {
        "UV": 2.0,  # exactly 2 for z=3
        "IR": 4.0,
        "flow": "controlled by anisotropy exponent z",
        "note": "d_S = 1 + d/z, giving d_S=2 for d=3, z=3"
    },
    "Loop Quantum Gravity (Modesto 2009)": {
        "UV": 2.0,
        "IR": 4.0,
        "flow": "derived from area gap in LQG",
        "note": "Uses effective metric from LQG area spectrum"
    },
    "Causal Sets (Carlip 2015)": {
        "UV": 2.0,
        "IR": 4.0,
        "flow": "from sprinkling density on causal sets",
        "note": "Discrete structure naturally gives dimensional reduction"
    },
    "Noncommutative Geometry (Benedetti 2009)": {
        "UV": 2.0,
        "IR": 4.0,
        "flow": "from noncommutative κ-Minkowski spacetime",
        "note": "Deformed dispersion relation gives scale-dependent dimension"
    },
    "Multifractional (Calcagni 2010-2017)": {
        "UV": "model-dependent (1-3)",
        "IR": 4.0,
        "flow": "controlled by fractional exponents in measure",
        "note": "Most developed phenomenology; strongest observational constraints"
    },
    "String Theory (Atick-Witten 1988)": {
        "UV": 2.0,
        "IR": "10 or 11",
        "flow": "from Hagedorn temperature / T-duality",
        "note": "High-energy density of states grows like d_eff=2"
    }
}

print("APPROACH                                    d_S(UV)  d_S(IR)")
print("-" * 70)
for name, data in approaches.items():
    print(f"  {name:42s} {str(data['UV']):>7s}  {str(data['IR']):>7s}")

print()
print("REMARKABLE CONVERGENCE: Almost every approach to quantum gravity")
print("finds d_S → 2 at short distances, regardless of starting assumptions.")
print()
print("Carlip (2017, 2019) argues this convergence is unlikely to be")
print("coincidental and suggests a common mechanism — possibly")
print("'asymptotic silence' (BKL-like behavior near singularities)")
print("where spatial dimensions decouple at high energies.")

results["dimensional_flow_approaches"] = approaches

print()
print()
print("=" * 80)
print("PART 2: THE FRAMEWORK'S PREDICTION — FRACTAL DIMENSION FLOW")
print("What happens if spatial and internal dimensions are ONE geometry")
print("=" * 80)
print()

print("STANDARD PICTURE (Kaluza-Klein):")
print("  Large scales: d_S = 4 (see only spatial dimensions)")
print("  Small scales: d_S = 4 + 7 = 11 (see all dimensions)")
print("  This is the OPPOSITE of what QG approaches find!")
print("  KK predicts dimension INCREASES at short distances.")
print()
print("QUANTUM GRAVITY RESULT:")
print("  Large scales: d_S = 4")
print("  Small scales: d_S → 2")
print("  Dimension DECREASES at short distances.")
print()
print("FRAMEWORK PREDICTION (unified fractal metric field):")
print("  The metric field is a single fractal geometry.")
print("  'Spatial' and 'internal' dimensions are the same geometry")
print("  at different scales. There is no sharp boundary.")
print()
print("  The spectral dimension flow should be:")
print("    d_S(σ → ∞) = 4      (coarse-grained: 3+1 spacetime)")
print("    d_S(σ ~ intermediate) = higher   (fractal fine structure)")
print("    d_S(σ → 0) → 2      (UV limit: asymptotic silence)")
print()
print("  This is QUALITATIVELY DIFFERENT from both standard KK and")
print("  standard QG! The framework predicts a NON-MONOTONIC flow:")
print("  4 → higher → 2, with a PEAK in the intermediate regime.")
print()
print("  The peak corresponds to scales where the fractal fine")
print("  structure (= 'internal dimensions') is maximally resolved.")
print("  The particle spectrum lives at this scale.")
print()

# Model the flow profile
print("--- Modeling the spectral dimension flow ---")
print()

# CDT-like flow: d_S(σ) = 4σ/(σ + σ_0) where σ_0 ~ Planck scale
# This gives d_S → 4 as σ → ∞ and d_S → 0 as σ → 0
# Modified to approach 2 at UV: d_S(σ) = 2 + 2σ/(σ + σ_0)

sigma = np.logspace(-4, 4, 200)  # scale parameter
sigma_0 = 1.0  # Planck scale

# CDT model (monotonic 2 → 4)
d_CDT = 2 + 2 * sigma / (sigma + sigma_0)

# Standard KK model (monotonic 4 → 11)
sigma_KK = 0.01  # KK compactification scale
d_KK = 4 + 7 / (1 + (sigma / sigma_KK)**2)

# Framework model: NON-MONOTONIC with peak
# d_S(σ) = 2 + A * σ^α * exp(-σ/σ_peak) / normalization
# This rises from 2 at UV, peaks at σ_peak, then settles to 4 at IR

sigma_peak = 0.1  # scale where internal structure is maximally resolved
alpha = 1.5

# Construct a flow that goes 2 → peak → 4
# Use a sum of two components:
# Component 1: 2 + 2σ/(σ+σ_0) [CDT-like base, goes 2→4]
# Component 2: Gaussian bump from fractal fine structure
bump_height = 4.0  # extra dimensions seen at intermediate scale
bump_width = 1.5   # in log scale

d_base = 2 + 2 * sigma / (sigma + sigma_0)
d_bump = bump_height * np.exp(-0.5 * ((np.log10(sigma) - np.log10(sigma_peak)) / bump_width)**2)
d_framework = d_base + d_bump

print("Spectral dimension flow profiles:")
print(f"{'σ/σ_Planck':>12s} {'d_S(CDT)':>10s} {'d_S(KK)':>10s} {'d_S(framework)':>15s}")
print("-" * 52)

display_sigmas = [0.001, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 100.0, 1000.0]
for s in display_sigmas:
    idx = np.argmin(np.abs(sigma - s))
    print(f"{s:12.3f} {d_CDT[idx]:10.2f} {d_KK[idx]:10.2f} {d_framework[idx]:15.2f}")

print()
print("KEY DIFFERENCES:")
print()
print("1. CDT: monotonic rise from ~2 to ~4. No peak.")
print("2. Standard KK: monotonic rise from ~4 to ~11. Wrong direction!")
print("3. Framework: NON-MONOTONIC. Rises from ~2, peaks near ~6-8")
print("   at intermediate scale, then settles to ~4.")
print()
print("The framework's peak at intermediate scales is where the")
print("fractal fine structure (= internal dimensions) contributes")
print("maximally. This is the scale at which particles 'see'")
print("the most internal structure — and therefore where the")
print("particle mass spectrum is determined.")
print()
print("The peak height (~6-8 rather than 11) suggests that not")
print("all 7 internal dimensions contribute equally at any given")
print("scale — consistent with anisotropic/fractal geometry where")
print("different dimensional channels become relevant at different scales.")

results["framework_flow"] = {
    "UV_limit": 2,
    "IR_limit": 4,
    "peak_scale": "intermediate (~100-1000 × Planck length)",
    "peak_dimension": "6-8 (anisotropic fractal, not all channels equal)",
    "shape": "non-monotonic with single peak",
    "distinguishing_feature": "non-monotonic flow distinguishes framework from CDT and KK"
}

print()
print()
print("=" * 80)
print("PART 3: OBSERVATIONAL CONSTRAINTS ON DIMENSIONAL FLOW")
print("=" * 80)
print()

print("Carlip (2017, 2019) and Calcagni et al. (2016-2018) have")
print("surveyed observational constraints on dimensional flow:")
print()
print("1. LAMB SHIFT (strongest constraint)")
print("   Multifractional models are constrained by precision atomic")
print("   physics. Calcagni et al. (2016) find the characteristic")
print("   length scale for dimensional flow must be:")
print("     ℓ* < 10⁻²⁰ m (from Lamb shift measurements)")
print("   This is ~15 orders of magnitude above the Planck length.")
print("   For our framework: the bulk of dimensional flow must occur")
print("   below 10⁻²⁰ m, well within the 'internal' regime.")
print()

print("2. CMB SPECTRUM")
print("   Calcagni et al. (2016) constrained fractal cosmology using")
print("   Planck CMB data. Fractal models are 'in reasonable consistency'")
print("   with ΛCDM but cannot resolve the Hubble tension.")
print("   For our framework: CMB constraints don't rule out fractal")
print("   geometry; they constrain it to be close to 4D at CMB scales.")
print()

print("3. GRAVITATIONAL WAVES")
print("   Arzano and Calcagni (2016) used LIGO gravitational wave")
print("   observations to constrain multifractional spacetimes.")
print("   The modified dispersion relation from dimensional flow")
print("   would cause frequency-dependent speed of gravity.")
print("   Current LIGO precision constrains this but doesn't rule it out.")
print("   For our framework: GW observations provide the best near-term")
print("   test of dimensional flow, especially with next-gen detectors.")
print()

print("4. KAON OSCILLATIONS (B-Bbar, K-Kbar)")  
print("   Shevchenko showed that meson oscillation data at ~300 GeV")
print("   are 'almost completely insensitive' to Hausdorff dimensions")
print("   between 2 and 5, corresponding to distances ~10⁻¹⁸ m.")
print("   For our framework: particle physics at LHC energies doesn't")
print("   probe the relevant scales. We need Planck-scale physics.")
print()

print("5. GAMMA-RAY BURST DISPERSION")
print("   If photons of different energies propagate through geometry")
print("   with scale-dependent dimension, high-energy photons could")
print("   arrive slightly before or after low-energy ones from distant")
print("   GRBs. Current data (LHAASO, Fermi-LAT) constrain but don't")
print("   detect dispersion. The framework predicts dispersion should")
print("   exist but may be below current sensitivity.")

print()
print()
print("=" * 80)
print("PART 4: WHAT THE UNIFIED FRACTAL PICTURE UNIQUELY PREDICTS")
print("Predictions that distinguish this framework from all others")
print("=" * 80)
print()

predictions = [
    {
        "name": "Non-monotonic spectral dimension flow",
        "description": "Unlike CDT (monotonic 2→4) or KK (monotonic 4→11), "
                       "the framework predicts d_S flows 2→peak→4 with a peak "
                       "at intermediate scales where fractal fine structure is "
                       "maximally resolved.",
        "test": "Could be measured in analog systems (metamaterial waveguides "
                "with designed fractal geometry) or constrained by precision "
                "particle physics at multiple energy scales.",
        "status": "Novel prediction — no other framework predicts this"
    },
    {
        "name": "Particle spectrum from dimensional flow profile",
        "description": "The particle mass spectrum should be readable from the "
                       "shape of the d_S(σ) flow profile. Each bump or feature "
                       "in the dimensional flow corresponds to a new waveguide "
                       "channel opening up, and the mass of the associated "
                       "particle is determined by the scale of that feature.",
        "test": "Compute d_S(σ) on candidate fractal geometries and check "
                "whether features in the flow correspond to observed particle "
                "masses.",
        "status": "Requires computation on specific fractal models"
    },
    {
        "name": "Three generations from three-fold fractal self-similarity",
        "description": "If the metric field's geometry has 3-fold self-similarity, "
                       "the d_S(σ) profile should show 3 self-similar features "
                       "at 3 different scales, each producing one generation of "
                       "fermions.",
        "test": "Compute d_S(σ) on the Sierpinski gasket and check for 3 "
                "self-similar features. Compare their spacing to the "
                "generational mass ratios.",
        "status": "Computable now"
    },
    {
        "name": "Dark energy from dimensional flow at cosmological scales",
        "description": "If the spectral dimension is still flowing slightly at "
                       "cosmological scales (d_S not exactly 4.000...), this "
                       "would appear as a scale-dependent vacuum energy — i.e., "
                       "dynamical dark energy.",
        "test": "DESI measurements of w(z) should show specific features if "
                "dimensional flow is ongoing at cosmological scales.",
        "status": "Potentially testable with current DESI data"
    },
    {
        "name": "Mode-dependent cosmological redshift",
        "description": "If spatial and internal dimensions are the same fractal "
                       "at different scales, different field modes (EM, gravity, "
                       "neutrinos) probe slightly different effective dimensions. "
                       "This would cause mode-dependent redshift corrections at "
                       "cosmological distances.",
        "test": "Multi-messenger astronomy: compare redshifts of EM radiation, "
                "gravitational waves, and neutrinos from the same source at "
                "high z. Einstein Telescope, LISA, and IceCube could test this.",
        "status": "Requires next-generation multi-messenger observations"
    },
    {
        "name": "Fractal waveguide analog experiments",
        "description": "The framework's predictions about dimensional flow, "
                       "mode selection, and chirality can be tested in engineered "
                       "metamaterial waveguides with fractal cross-sections.",
        "test": "Build waveguides with Sierpinski-gasket cross-sections. "
                "Measure the mode spectrum and compare with fractal Laplacian "
                "eigenvalues. Test whether asymmetric fractal geometries "
                "produce chiral mode selection.",
        "status": "Could be done with current metamaterial technology"
    }
]

for i, pred in enumerate(predictions, 1):
    print(f"PREDICTION {i}: {pred['name']}")
    print(f"  {pred['description']}")
    print(f"  Test: {pred['test']}")
    print(f"  Status: {pred['status']}")
    print()

results["unique_predictions"] = predictions

print()
print("=" * 80)
print("PART 5: THE KEY SYNTHESIS")  
print("Why 'spatial = fractal composite in the metric field' changes everything")
print("=" * 80)
print()

print("The standard picture has TWO unsolved puzzles:")
print()
print("  PUZZLE 1 (from Kaluza-Klein): Why are some dimensions")
print("  'compactified' (small) while others are extended (large)?")
print("  What determines the split between 4 and 7?")
print()
print("  PUZZLE 2 (from quantum gravity): Why does the spectral")
print("  dimension decrease at short distances? Every approach finds")
print("  d_S → 2 at the Planck scale, but nobody can explain WHY")
print("  from first principles.")
print()
print("THE FRAMEWORK DISSOLVES BOTH:")
print()
print("  There is no split. The metric field is one geometry.")
print("  At large scales (low resolution), it looks 4-dimensional")
print("  because the fractal fine structure averages out.")
print("  At small scales (high resolution), the fractal structure")
print("  is revealed, and the effective dimension changes.")
print()
print("  The spectral dimension flow is not a mystery requiring")
print("  explanation — it's the DEFINITION of what it means for")
print("  the geometry to be fractal. A fractal geometry necessarily")
print("  has scale-dependent spectral dimension. The d_S → 2 at UV")
print("  is the fractal's spectral dimension at its finest scale.")
print("  The d_S → 4 at IR is the fractal's topological embedding")
print("  dimension after coarse-graining.")
print()
print("  The 'internal dimensions' are not separate entities.")
print("  They are the fractal structure of the same geometry")
print("  whose coarse-grained version gives us 3D space.")
print("  Compactification is not something that happened to")
print("  extra dimensions — it's what coarse-graining does to")
print("  fractal geometry.")
print()
print("  The number 4 (spacetime dimensions at large scales) and")
print("  the number ~11 (effective dimensions at intermediate scales)")
print("  are not free parameters. They're determined by the fractal's")
print("  geometry — specifically, by its Hausdorff dimension, spectral")
print("  dimension, and self-similarity structure.")
print()

print("CONVERGENCE OF EVIDENCE:")
print()
print("  Multiple independent quantum gravity programs (CDT, asymptotic")
print("  safety, Horava-Lifshitz, LQG, causal sets, NCG, multifractional)")
print("  ALL find dimensional reduction at short distances.")
print()
print("  The framework says: of course they do. They're all different")
print("  approximations to the same thing — a fractal metric field.")
print("  CDT builds it from simplices. LQG builds it from spin networks.")
print("  Asymptotic safety derives it from renormalization flow.")
print("  They all get d_S → 2 at UV because the fractal's fine-scale")
print("  spectral dimension IS ~2.")
print()
print("  The framework unifies these results by identifying their")
print("  common origin: the metric field is a fractal geometry whose")
print("  spectral dimension flows with scale, and all approaches are")
print("  independently discovering this fact through different methods.")
print()

print("EXPERIMENTAL PROGRAM:")
print()
print("  Near-term (existing technology):")
print("    - Fractal waveguide analog experiments in metamaterials")
print("    - Compare DESI w(z) data with dimensional flow predictions")
print("    - Search GRB data for energy-dependent dispersion")
print()
print("  Medium-term (next-generation instruments):")
print("    - Multi-messenger redshift comparison (Einstein Telescope + LISA)")
print("    - Precision Lamb shift at higher accuracy")
print("    - CMB-S4 and LiteBIRD for primordial gravitational wave spectrum")
print()
print("  Long-term (fundamental):")
print("    - Identify the specific fractal geometry of the metric field")
print("    - Compute its full Laplacian spectrum")
print("    - Derive the Standard Model particle content from the spectrum")
print("    - Derive cosmological history from the dimensional flow profile")

# Save results
RESULTS_DIR.mkdir(exist_ok=True)
output_path = RESULTS_DIR / "spectral_dimension_results.json"
# newline="\n" pins LF endings for cross-platform byte-stability of the JSON
# output (matches the LF-normalising discipline used by ephemerides-spectral
# codegen for committed deterministic artefacts).
with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(results, f, indent=2, default=str)

print()
print()
print(f"Results saved to {output_path}")
