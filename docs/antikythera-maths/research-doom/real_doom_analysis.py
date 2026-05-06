import numpy as np
from scipy.linalg import expm
from wad_parser import WadParser
from doom_topology import SectorGraph
from doom_fiber import ZFiber

def analyze_real_e1m1():
    print("--- Real DOOM Analysis: E1M1 Hangar ---")
    wad = WadParser("docs/antikythera-maths/research-doom/DOOM1.WAD")
    sectors, adj = wad.build_sector_graph("E1M1")
    
    # Mock a WAD object for the SectorGraph and ZFiber classes
    class RealWad:
        def __init__(self, sectors, adj):
            self.sectors = sectors
            self.adj = adj
        def get_sector_graph(self): return self.adj
        def get_sector_data(self): return self.sectors
    
    real_wad = RealWad(sectors, adj)
    graph = SectorGraph(real_wad)
    fiber = ZFiber(real_wad)
    
    print(f"Loaded {len(sectors)} sectors and {int(np.sum(adj)/2)} portals.")
    
    # 1. Sound Propagation
    # Fire a shot in Sector 0 (Starting room)
    # How many sectors does sound reach with significant intensity?
    t = 2.0
    sound_dist = graph.propagate_sound(0, time=t)
    reachable_sectors = np.sum(sound_dist > 0.01)
    print(f"\nSound Diffusion (t={t}):")
    print(f"  Sound reached {reachable_sectors} sectors from Sector 0.")
    
    # 2. Z-Fiber Analysis
    # Let's find a sector that is blocked by height.
    # We'll check if any adjacent sectors have a floor difference > 24
    blocked_count = 0
    total_portals = 0
    for i in range(len(sectors)):
        for j in range(i + 1, len(sectors)):
            if adj[i, j] > 0:
                total_portals += 1
                diff = abs(sectors[i]['floor'] - sectors[j]['floor'])
                if diff > 24:
                    blocked_count += 1
    
    print(f"\nZ-Fiber Physics:")
    print(f"  Total Portals: {total_portals}")
    print(f"  Portals with Step > 24 units: {blocked_count}")
    
    # Effective Laplacian with Step=24
    eff_adj = fiber.get_effective_adjacency(entity_z=0, entity_height=56, max_step=24)
    eff_connections = int(np.sum(eff_adj)/2)
    print(f"  Effective Connections for Player (MaxStep=24): {eff_connections}")

    # 3. Spectral Analysis
    eigenvalues = np.sort(np.linalg.eigvals(graph.L))
    print(f"\nSpectral Properties:")
    print(f"  Algebraic Connectivity (lambda_2): {eigenvalues[1]:.6f}")
    print(f"  Spectral Radius: {eigenvalues[-1]:.6f}")

if __name__ == "__main__":
    analyze_real_e1m1()
