import json
import matplotlib.pyplot as plt
import numpy as np

def create_publication_plot():
    # 1. Read the JSON data
    input_path = "results-mfo/spectral_dimension_flow.json"
    try:
        with open(input_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_path} not found.")
        return
    
    sigma = np.array(data["flow_data"]["sigma"])
    ds_sg = np.array(data["flow_data"]["ds_sg"])
    ds_total = np.array(data["flow_data"]["ds_total"])
    ds_base = np.array(data["flow_data"]["ds_base"])
    
    # 2. Setup Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 3. Plot Curves
    ax.semilogx(sigma, ds_sg, label="Fractal Axis (SG L=5)", color="blue", linewidth=1.5, alpha=0.8)
    ax.semilogx(sigma, ds_total, label="Total Metric Field (SG x S1 x CP2)", color="red", linewidth=2.0)
    ax.semilogx(sigma, ds_base, label="CDT Base (Background 2 -> 4)", color="green", linestyle="--", linewidth=1.0)
    
    # 4. Format Axes
    ax.set_ylim(0, 8)
    ax.set_xlabel(r"Diffusion time $\sigma$ / $\sigma_{Planck}$", fontsize=12)
    ax.set_ylabel(r"Spectral dimension $d_S(\sigma)$", fontsize=12)
    ax.set_title("Spectral Dimension Flow – L=5 SG x S1 x CP2", fontsize=14, fontweight='bold')
    
    # 5. Add Legend and Grid
    ax.legend(loc='upper right', frameon=True)
    ax.grid(True, which="both", linestyle=':', alpha=0.4)
    
    # 6. Save Plot
    output_path = "results-mfo/spectral_dimension_flow.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    
    print(f"Publication-quality plot saved to {output_path}")

if __name__ == "__main__":
    create_publication_plot()
