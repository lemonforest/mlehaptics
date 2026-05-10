import numpy as np
import json

def run_ckm_analysis():
    # 1. Observed CKM magnitudes (PDG 2024 approx)
    v_obs = np.array([
        [0.974, 0.225, 0.0036],
        [0.224, 0.973, 0.042],
        [0.0086, 0.041, 0.999]
    ])
    
    # 2. Extract standard Euler mixing angles (assuming delta_cp = 0 for magnitude fit)
    # s13 = V_ub
    s13 = v_obs[0, 2]
    theta13 = np.arcsin(s13)
    c13 = np.cos(theta13)
    
    # s12 = V_us / c13
    s12 = v_obs[0, 1] / c13
    theta12 = np.arcsin(s12)
    
    # s23 = V_cb / c13
    s23 = v_obs[1, 2] / c13
    theta23 = np.arcsin(s23)
    
    # 3. CP2 Scale Factors from best-fit model
    c_gens = [0.001000, 0.000631, 0.010000] # G1, G2, G3
    
    # Ratios
    r12 = c_gens[1] / c_gens[0] # G2/G1
    r23 = c_gens[2] / c_gens[1] # G3/G2
    r13 = c_gens[2] / c_gens[0] # G3/G1
    
    # 4. Roadmap Outline
    roadmap = {
        "theoretical_basis": "CKM entries as overlap integrals between CP2 eigenfunctions of up-type and down-type quarks.",
        "overlap_integrals": {
            "CKM_ij": "Integral over CP2 coordinates z: <Phi_{u,i}(z) | Phi_{d,j}(z)>. The k-mode (32, 140, etc.) determines the SU(3) representation.",
            "geometric_mismatch": "The mismatch angles theta_gen represent the relative rotation of the mass eigenbases in the CP2 Hilbert space."
        },
        "missing_machinery": [
            "Explicit eigenfunctions for the CP2 scalar/spinor Laplacian.",
            "Boundary matching conditions between the SG fractal axes and the CP2 smooth manifold.",
            "Non-diagonal generation overlaps: How the fractal anchor self-similarity (3-fold) couples different generations in the CP2 base."
        ]
    }
    
    # 5. Pattern Recognition
    # Does theta12 approx C2/C1?
    # theta12 = 0.227 rad
    # C2/C1 = 0.631
    # theta12 / (C2/C1) = 0.36
    
    results = {
        "observed_ckm_magnitudes": v_obs.tolist(),
        "fitted_euler_angles": {
            "theta12_rad": theta12,
            "theta23_rad": theta23,
            "theta13_rad": theta13,
            "theta12_deg": np.degrees(theta12),
            "theta23_deg": np.degrees(theta23),
            "theta13_deg": np.degrees(theta13)
        },
        "cp2_scale_ratios": {
            "C2_over_C1": r12,
            "C3_over_C2": r23,
            "C3_over_C1": r13
        },
        "geometric_correlation": {
            "theta12_ratio": theta12 / r12,
            "theta23_ratio": theta23 / r23,
            "theta13_ratio": theta13 / r13
        },
        "roadmap": roadmap
    }
    
    print(f"CKM Mixing Analysis (MFO Framework)")
    print(f"\nFitted Mixing Angles (Radians):")
    print(f"  theta12 (Cabibbo): {theta12:.4f}")
    print(f"  theta23:           {theta23:.4f}")
    print(f"  theta13:           {theta013:.4f}" if "theta013" in locals() else f"  theta13:           {theta13:.4f}")
    
    print(f"\nCP2 Scale Factor Ratios:")
    print(f"  C2/C1: {r12:.4f}")
    print(f"  C3/C2: {r23:.4f}")
    
    print(f"\nKey Observation:")
    print(f"  The Cabibbo angle theta12 ({theta12:.4f}) is approximately equal to 1/sqrt(2) * C2/C1?")
    print(f"  {theta12 / (r12 / np.sqrt(2)):.4f}")
    
    with open("results-mfo/ckm_mixing_analysis.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_ckm_analysis()
