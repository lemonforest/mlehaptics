import numpy as np
import json
import matplotlib.pyplot as plt

def get_sg_spectrum(L=5.0, max_level=5):
    """Generate the L=5 decimation eigenvalues at Level 5."""
    def R_inverse(w):
        disc = L*L - 4*w
        if disc < 0: return []
        sd = np.sqrt(disc)
        return [(L - sd)/2.0, (L + sd)/2.0]

    current_evals = {0.0, L}
    all_evals = set()
    for m in range(max_level + 1):
        factor = L**m
        for e in current_evals:
            if e > 1e-10:
                all_evals.add(round(e * factor, 10))
        if m < max_level:
            next_evals = set()
            for w in current_evals:
                for z in R_inverse(w):
                    if 0 <= z <= L + 1:
                        next_evals.add(z)
            next_evals.add(2.0)
            next_evals.add(5.0)
            current_evals = next_evals
    return np.array(sorted(list(all_evals)))

def compute_spectral_dimension(sigma_vals, eigenvalues):
    ds_vals = []
    for sigma in sigma_vals:
        # K(sigma) = sum exp(-lambda * sigma)
        # We include the zero mode (lambda=0) in the heat kernel sum
        # K(sigma) = 1 + sum_{i>0} exp(-lambda_i * sigma)
        exps = np.exp(-eigenvalues * sigma)
        k_sigma = 1.0 + np.sum(exps)
        
        # S(sigma) = sum lambda * exp(-lambda * sigma)
        s_sigma = np.sum(eigenvalues * exps)
        
        # d_S = 2 * sigma * S / K
        ds = 2.0 * sigma * s_sigma / k_sigma
        ds_vals.append(ds)
    return np.array(ds_vals)

def run_flow_analysis():
    sigma_vals = np.logspace(-8, 8, 200)
    
    # 1. SG Spectral Dimension
    evals = get_sg_spectrum(L=5.0, max_level=5)
    ds_sg = compute_spectral_dimension(sigma_vals, evals)
    
    # 2. Total Spectral Dimension (SG + S1 + CP2)
    # User says dS_S1 = 1, dS_CP2 = 4 (constant)
    ds_total = ds_sg + 1.0 + 4.0
    
    # 3. CDT Base Flow
    ds_base = 2.0 + (2.0 * sigma_vals) / (sigma_vals + 1.0)
    
    # 4. Find Peak
    peak_idx = np.argmax(ds_sg)
    peak_sigma = sigma_vals[peak_idx]
    peak_ds_sg = ds_sg[peak_idx]
    peak_ds_total = ds_total[peak_idx]
    
    # 5. Plotting
    plt.figure(figsize=(10, 6))
    plt.semilogx(sigma_vals, ds_sg, label="SG (L=5, Level 5)", color="blue", linewidth=2)
    plt.semilogx(sigma_vals, ds_total, label="Total (SG x S1 x CP2)", color="red", linestyle="--", linewidth=2)
    plt.semilogx(sigma_vals, ds_base, label="CDT Base (2 -> 4)", color="green", alpha=0.5)
    
    plt.axvline(peak_sigma, color="gray", linestyle=":", label=f"Peak at σ={peak_sigma:.1e}")
    
    plt.xlabel("Diffusion Time σ (Log Scale)")
    plt.ylabel("Spectral Dimension d_S(σ)")
    plt.title("Spectral Dimension Flow: Metric Field Ontology (MFO)")
    plt.legend()
    plt.grid(True, which="both", alpha=0.3)
    
    plot_path = "results-mfo/spectral_dimension_flow.png"
    plt.savefig(plot_path)
    
    # 6. Save Data
    results = {
        "peak_analysis": {
            "peak_sigma": float(peak_sigma),
            "peak_ds_sg": float(peak_ds_sg),
            "peak_ds_total": float(peak_ds_total),
            "theoretical_ds_sg": 2.0 * np.log(3) / np.log(5) # ~1.365
        },
        "flow_data": {
            "sigma": sigma_vals.tolist(),
            "ds_sg": ds_sg.tolist(),
            "ds_total": ds_total.tolist(),
            "ds_base": ds_base.tolist()
        }
    }
    
    with open("results-mfo/spectral_dimension_flow.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Spectral Dimension Flow Analysis Complete.")
    print(f"\nKey Findings:")
    print(f"  Peak Spectral Dimension (SG): {peak_ds_sg:.4f} (Theoretical: {results['peak_analysis']['theoretical_ds_sg']:.4f})")
    print(f"  Peak Spectral Dimension (Total): {peak_ds_total:.4f}")
    print(f"  Peak Diffusion Time σ: {peak_sigma:.2e}")
    print(f"  Non-monotonic behavior: {'YES' if peak_ds_sg > ds_sg[0] and peak_ds_sg > ds_sg[-1] else 'NO'}")
    print(f"\nResults saved to results-mfo/")

if __name__ == "__main__":
    run_flow_analysis()
