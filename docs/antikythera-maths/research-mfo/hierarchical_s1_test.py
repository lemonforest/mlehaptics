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
target_log = np.array([np.log10((x[1]/m_e)**2) for x in sorted_sm])

# Best-fit fractal eigenvalues (L=5, Level 5) from the global inverse test
# Scale factor S = 0.2975
# Mapping (based on the global refinement output):
base_fractal_evals = [
    0.0000,   # electron
    0.4384,   # up
    0.4384,   # down
    1.3557,   # strange
    1.3767,   # muon
    2.0000,   # charm
    2.0000,   # tau
    2.0000,   # bottom
    3.6180    # top
]

def run_hierarchical_s1():
    S = 0.297479  # Exact scale factor from refined test
    R = 1000.0
    s1_unit = 1.0 / (R**2)
    
    best_n_values = []
    best_errors = []
    best_ratios = []
    total_error = 0.0
    
    print(f"Hierarchical S1 Assignment Test (L=5, S={S:.4f}, R={R})")
    print(f"{'Particle':>10s} {'Target Log':>12s} {'Base λ':>10s} {'Best n':>6s} {'Final Log':>12s} {'Error':>10s}")
    
    for i in range(9):
        target = target_log[i]
        base_lam = base_fractal_evals[i]
        
        # Sweep n for this particle
        best_n = 0
        min_err = float('inf')
        best_log_pred = 0.0
        
        for n in range(6):
            # Prediction in spectral domain: lambda_total = base + n^2/R^2
            # Map to log domain: log_pred = lambda_total / S
            log_pred = (base_lam + (n**2 * s1_unit)) / S
            err = (log_pred - target)**2
            if err < min_err:
                min_err = err
                best_n = n
                best_log_pred = log_pred
        
        best_n_values.append(best_n)
        best_errors.append(min_err)
        best_ratios.append(10**best_log_pred)
        total_error += min_err
        
        print(f"{sm_names[i]:10s} {target:12.4f} {base_lam:10.4f} {best_n:6d} {best_log_pred:12.4f} {min_err:10.4f}")

    results = {
        "parameters": {"L": 5.0, "S": S, "R": R},
        "total_log10_squared_error": total_error,
        "assignments": [
            {
                "particle": sm_names[i],
                "base_eigenvalue": base_fractal_evals[i],
                "s1_n": best_n_values[i],
                "target_log": target_log[i],
                "predicted_log": (base_fractal_evals[i] + (best_n_values[i]**2 * s1_unit)) / S,
                "error": best_errors[i]
            } for i in range(9)
        ]
    }

    with open("results-mfo/hierarchical_s1_assignment.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nFinal Total Error: {total_error:.6f}")

if __name__ == "__main__":
    run_hierarchical_s1()
