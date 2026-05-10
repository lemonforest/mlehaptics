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

# Fixed parameters from the best previous model
S = 0.297479
R = 1000.0
s1_unit = 1.0 / (R**2)

# Fixed assignments from the 2.81 error model (hierarchical_s1_test.py)
anchors = [
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

s1_ns = [
    0,   # electron
    0,   # up
    5,   # down
    0,   # strange
    5,   # muon
    5,   # charm
    5,   # tau
    5,   # bottom
    0    # top
]

cp2_eigenvalues = [0, 12, 32, 60, 96, 140]

def run_cp2_sweep():
    # Sweep C_gen from 0.0001 to 0.01 in log steps
    c_range = np.logspace(-4, -2, 21)
    
    best_total_error = float('inf')
    best_c_gens = [0.0, 0.0, 0.0]
    best_k_assignments = [0] * 9

    print("Starting CP2 Scale Factor Sweep...")
    
    # We iterate over Gen1, Gen2, Gen3 scale factors independently
    for C1 in c_range:
        for C2 in c_range:
            for C3 in c_range:
                current_total_error = 0.0
                current_ks = []
                
                for i in range(9):
                    target = target_log[i]
                    base = anchors[i] + (s1_ns[i]**2 * s1_unit)
                    gen_idx = i // 3
                    C = [C1, C2, C3][gen_idx]
                    
                    # Find best k for this fermion
                    best_k = 0
                    min_p_err = float('inf')
                    for k in cp2_eigenvalues:
                        val = base + (k * C)
                        log_pred = val / S
                        err = (log_pred - target)**2
                        if err < min_p_err:
                            min_p_err = err
                            best_k = k
                    
                    current_total_error += min_p_err
                    current_ks.append(best_k)
                
                if current_total_error < best_total_error:
                    best_total_error = current_total_error
                    best_c_gens = [C1, C2, C3]
                    best_k_assignments = current_ks

    # Final Mapping
    mappings = []
    print(f"\nCP2 Refinement Complete.")
    print(f"Optimal Scales: C1={best_c_gens[0]:.6f}, C2={best_c_gens[1]:.6f}, C3={best_c_gens[2]:.6f}")
    print(f"Total Error: {best_total_error:.6f}")
    print(f"\n{'Particle':>10s} {'Target':>8s} {'Anchor':>8s} {'S1 n':>5s} {'CP2 k':>5s} {'Final Log':>10s} {'Error':>8s}")
    
    for i in range(9):
        C = best_c_gens[i // 3]
        k = best_k_assignments[i]
        final_lam = anchors[i] + (s1_ns[i]**2 * s1_unit) + (k * C)
        log_pred = final_lam / S
        err = (log_pred - target_log[i])**2
        
        mappings.append({
            "particle": sm_names[i],
            "generation": (i // 3) + 1,
            "anchor": anchors[i],
            "s1_n": s1_ns[i],
            "cp2_k": k,
            "scale_c": C,
            "predicted_log": log_pred,
            "target_log": target_log[i],
            "error": err
        })
        
        print(f"{sm_names[i]:10s} {target_log[i]:8.4f} {anchors[i]:8.4f} {s1_ns[i]:5d} {k:5d} {log_pred:10.4f} {err:8.4f}")

    results = {
        "parameters": {"S": S, "R": R, "C_gens": best_c_gens},
        "total_error": best_total_error,
        "mappings": mappings
    }

    with open("results-mfo/cp2_assignment.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_cp2_sweep()
