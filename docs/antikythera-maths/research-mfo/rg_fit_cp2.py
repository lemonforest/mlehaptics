import numpy as np
import json

# Standard Model target mass-squared ratios relative to electron
sm_masses_gev = {
    'electron': 0.000511,
    'up': 0.0022,
    'down': 0.0047,
    'strange': 0.095,
    'muon': 0.1057,
    'charm': 1.275,
    'tau': 1.777,
    'bottom': 4.18,
    'top': 173.0,
}
m_e = 0.000511
sorted_sm = sorted(sm_masses_gev.items(), key=lambda x: x[1])
sm_names = [x[0] for x in sorted_sm]
target_log_m2 = np.array([np.log10((x[1]/m_e)**2) for x in sorted_sm])

# Fixed parameters from the best previous model
S = 0.297479
R = 1000.0
s1_unit = 1.0 / (R**2)
C_gens = [0.001000, 0.000631, 0.010000]

# Assignments from CP2 refinement
# (anchor, s1_n, cp2_k)
assignments = [
    (0.0000, 0, 0),    # electron
    (0.4384, 0, 0),    # up
    (0.4384, 5, 140),  # down
    (1.3557, 0, 0),    # strange
    (1.3767, 5, 0),    # muon
    (2.0000, 5, 32),   # charm
    (2.0000, 5, 12),   # tau
    (2.0000, 5, 32),   # bottom
    (3.6180, 0, 0)     # top
]

# Multiplet grouping
multiplets = {
    'charged_lepton': [0, 4, 6], # electron, muon, tau
    'up_quark': [1, 5, 8],       # up, charm, top
    'down_quark': [2, 3, 7]      # down, strange, bottom
}

def run_rg_cp2_fit():
    # 1. Compute Base Model Predictions
    pred_log_m2 = []
    mass_shifts = []
    
    for i in range(9):
        anchor, s1_n, cp2_k = assignments[i]
        gen_idx = i // 3
        C = C_gens[gen_idx]
        
        final_lam = anchor + (s1_n**2 * s1_unit) + (cp2_k * C)
        log_pred = final_lam / S
        pred_log_m2.append(log_pred)
        
        # Shift: m(mu)/m(Lambda) = sqrt(m2_obs / m2_pred)
        shift = np.sqrt(10**(target_log_m2[i] - log_pred))
        mass_shifts.append(shift)

    # 2. RG Fit (assuming Lambda = 1e19 GeV, mu = 246.22 GeV)
    X = np.log(1e19 / 246.22)
    
    alpha_fits = {}
    corrected_shifts = [0.0] * 9
    
    for m_name, indices in multiplets.items():
        shifts = np.array([mass_shifts[i] for i in indices])
        # Find best c = alpha/pi: c = mean(1 - shifts) / X
        c = np.mean(1.0 - shifts) / X
        alpha = c * np.pi
        alpha_fits[m_name] = alpha
        
        for i in indices:
            corrected_shifts[i] = 1.0 - (alpha * X / np.pi)

    # 3. Final Calculations
    final_errors = []
    mappings = []
    
    for i in range(9):
        # Corrected log10(m2) = pred_log_m2 + 2*log10(corrected_shift)
        corrected_log_m2 = pred_log_m2[i] + 2 * np.log10(corrected_shifts[i])
        error = (corrected_log_m2 - target_log_m2[i])**2
        final_errors.append(error)
        
        m_name = ""
        for k, v in multiplets.items():
            if i in v: m_name = k
            
        mappings.append({
            "particle": sm_names[i],
            "multiplet": m_name,
            "observed_log_m2": target_log_m2[i],
            "model_log_m2": pred_log_m2[i],
            "rg_corrected_log_m2": corrected_log_m2,
            "shift_factor": mass_shifts[i],
            "coupling_alpha": alpha_fits[m_name],
            "final_error": error
        })

    results = {
        "parameters": {
            "L": 5.0, "S": S, "R": R, "C_gens": C_gens,
            "Lambda_mu_ratio": np.exp(X), "ln_Lambda_mu": X
        },
        "alpha_fits": alpha_fits,
        "total_error": sum(final_errors),
        "mappings": mappings
    }

    with open("results-mfo/rg_fit_cp2.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"RG + CP2 Refinement Results (Lambda=1e19 GeV)")
    print(f"Total Residual Error: {sum(final_errors):.6f}")
    print(f"\nCoupling Strengths (Alpha):")
    for m, a in alpha_fits.items():
        print(f"  {m:15s}: {a:.4f}")
    
    print(f"\n{'Particle':>10s} {'Obs Log':>10s} {'Model Log':>10s} {'RG Log':>10s} {'Error':>10s}")
    for m in mappings:
        print(f"{m['particle']:10s} {m['observed_log_m2']:10.4f} {m['model_log_m2']:10.4f} {m['rg_corrected_log_m2']:10.4f} {m['final_error']:10.4f}")

if __name__ == "__main__":
    run_rg_cp2_fit()
