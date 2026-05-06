import numpy as np
from wad_parser import WadParser
from doom_bip_encoder import Phase9BIP

def generate_haptic_anchors():
    print("--- Spectral Haptic Research: E1M1 Anchors ---")
    wad = WadParser("docs/antikythera-maths/research-doom/DOOM1.WAD")
    sectors, adj = wad.build_sector_graph("E1M1")
    
    bip = Phase9BIP(D=512)
    num_sectors = len(sectors)
    
    # Generate a unique Anchor Hypervector for each sector
    # Rule: Anchors for adjacent sectors should be more similar than distant ones
    # We can achieve this by 'bleeding' anchors across the graph
    rng = np.random.default_rng(42)
    raw_anchors = rng.choice([-1, 1], size=(num_sectors, 512))
    
    # Diffusion: A' = (I + 0.1 * A) * A_raw
    # (Simplified graph smoothing)
    smooth_anchors = raw_anchors.copy().astype(float)
    for _ in range(3):
        for i in range(num_sectors):
            neighbors = np.where(adj[i] > 0)[0]
            if len(neighbors) > 0:
                smooth_anchors[i] += 0.2 * np.sum(raw_anchors[neighbors], axis=0)
    
    # Re-normalize to bipolar
    anchors = np.sign(smooth_anchors).astype(np.int8)
    
    # Verify: Similarity between adjacent vs distant sectors
    sim_adj = []
    sim_far = []
    for i in range(num_sectors):
        for j in range(i + 1, num_sectors):
            sim = np.dot(anchors[i], anchors[j]) / 512
            if adj[i, j] > 0:
                sim_adj.append(sim)
            else:
                sim_far.append(sim)
                
    print(f"Generated {num_sectors} Spectral Anchors.")
    print(f"  Avg Similarity (Adjacent): {np.mean(sim_adj):.4f}")
    print(f"  Avg Similarity (Distant):  {np.mean(sim_far):.4f}")
    
    # Save Anchors to results-doom
    np.save("docs/antikythera-maths/results-doom/e1m1_haptic_anchors.npy", anchors)
    print("\nSaved anchors to results-doom/e1m1_haptic_anchors.npy")

if __name__ == "__main__":
    generate_haptic_anchors()
