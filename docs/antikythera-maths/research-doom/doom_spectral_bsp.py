import numpy as np
from wad_parser import WadParser
from doom_topology import SectorGraph

def spectral_bsp_partition(level_name="E1M1"):
    print(f"--- Spectral BSP Partitioning: {level_name} ---")
    wad = WadParser("docs/antikythera-maths/research-doom/DOOM1.WAD")
    sectors, adj = wad.build_sector_graph(level_name)
    graph = SectorGraph(type('MockWad', (), {'get_sector_graph': lambda self: adj})())
    
    # 1. Compute Eigenvalues and Eigenvectors
    # lambda_2 (Fiedler value) and v_2 (Fiedler vector)
    vals, vecs = np.linalg.eigh(graph.L)
    
    # Sort just in case
    idx = vals.argsort()
    vals = vals[idx]
    vecs = vecs[:, idx]
    
    fiedler_vec = vecs[:, 1]
    
    # 2. Partition based on the sign of the Fiedler vector
    # This identifies the "Nodal Domains" which represent the primary cut in the graph.
    partition_0 = [i for i, val in enumerate(fiedler_vec) if val >= 0]
    partition_1 = [i for i, val in enumerate(fiedler_vec) if val < 0]
    
    print(f"Fiedler Value (lambda_2): {vals[1]:.6f}")
    print(f"Partition 0 size: {len(partition_0)} sectors")
    print(f"Partition 1 size: {len(partition_1)} sectors")
    
    # 3. Analyze the cut
    # Find edges that cross the partition
    cut_edges = 0
    for i in partition_0:
        for j in partition_1:
            if adj[i, j] > 0:
                cut_edges += 1
    
    print(f"Number of cut portals: {cut_edges}")
    
    # Save partitions to results-doom
    np.save("docs/antikythera-maths/results-doom/e1m1_spectral_partition.npy", 
            {'p0': partition_0, 'p1': partition_1, 'fiedler': fiedler_vec})
    print("\nSaved spectral partition data to results-doom/e1m1_spectral_partition.npy")

if __name__ == "__main__":
    spectral_bsp_partition()
