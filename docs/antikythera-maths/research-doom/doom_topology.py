import numpy as np
from scipy.linalg import expm
from wad_parser_mock import MockWad

class SectorGraph:
    def __init__(self, wad):
        self.wad = wad
        self.adj = wad.get_sector_graph()
        self.num_sectors = self.adj.shape[0]
        self.L = self._compute_laplacian()

    def _compute_laplacian(self):
        # L = D - A
        degree_matrix = np.diag(np.sum(self.adj, axis=1))
        return degree_matrix - self.adj

    def propagate_sound(self, source_sector_id, time=1.0):
        # Initial sound vector: 1.0 at source, 0 elsewhere
        s0 = np.zeros(self.num_sectors)
        s0[source_sector_id] = 1.0
        
        # Heat equation: s(t) = exp(-L * t) * s(0)
        # Note: In DOOM, sound propagation is more like flooding, 
        # but spectral diffusion is a good continuous model for it.
        st = expm(-self.L * time) @ s0
        return st

if __name__ == "__main__":
    wad = MockWad()
    graph = SectorGraph(wad)
    print("Laplacian Matrix:\n", graph.L)
    
    # Simulate sound firing in Hangar (Sector 0)
    sound_dist = graph.propagate_sound(0, time=0.5)
    print("\nSound distribution after time 0.5 (Source: Hangar):")
    for i, sector in enumerate(wad.get_sector_data()):
        print(f"Sector {i} ({sector['name']}): {sound_dist[i]:.4f}")
