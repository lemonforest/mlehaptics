import numpy as np
from wad_parser_mock import MockWad

class ZFiber:
    def __init__(self, wad):
        self.wad = wad
        self.sectors = wad.get_sector_data()
        self.adj = wad.get_sector_graph()
        self.num_sectors = len(self.sectors)

    def get_effective_adjacency(self, entity_z, entity_height, max_step=24):
        """
        Computes the adjacency matrix for an entity at a given Z position.
        Edges are severed if the height constraints are not met.
        """
        eff_adj = self.adj.copy()
        for i in range(self.num_sectors):
            for j in range(self.num_sectors):
                if self.adj[i, j] > 0:
                    # Check transition from i to j
                    sec_j = self.sectors[j]
                    
                    # Constraint 1: Floor of B must be reachable from entity's current Z + step
                    # (DOOM actually checks floor-to-floor and floor-to-ceiling)
                    # For simplicity, we use the notebook's logic:
                    # Floor(B) <= Z_entity + MaxStep
                    # Ceiling(B) >= Z_entity + Height_entity
                    
                    can_enter = (sec_j['floor'] <= entity_z + max_step) and \
                                (sec_j['ceiling'] >= entity_z + entity_height)
                    
                    if not can_enter:
                        eff_adj[i, j] = 0
                        eff_adj[j, i] = 0 # Assume symmetric blockage for now
        return eff_adj

    def get_effective_laplacian(self, entity_z, entity_height, max_step=24):
        eff_adj = self.get_effective_adjacency(entity_z, entity_height, max_step)
        degree_matrix = np.diag(np.sum(eff_adj, axis=1))
        return degree_matrix - eff_adj

if __name__ == "__main__":
    wad = MockWad()
    fiber = ZFiber(wad)
    
    # Entity: DoomGuy (Height 56, at Z=0)
    # Trying to move from Hallway (1) to Acid Pit (2)
    # Acid Pit floor is -24. Hangar/Hallway is 0.
    # Moving from Hallway to Acid Pit is always possible (dropping down).
    # Moving from Acid Pit to Hallway requires climbing 24 units.
    
    print("Normal Adjacency:\n", wad.get_sector_graph())
    
    # Case 1: Entity in Acid Pit (Z=-24), trying to climb to Hallway (Z=0)
    # MaxStep is 24. Should be possible.
    adj_climb = fiber.get_effective_adjacency(entity_z=-24, entity_height=56, max_step=24)
    print("\nEffective Adjacency (Climbing from Z=-24 with MaxStep=24):\n", adj_climb)
    
    # Case 2: MaxStep is 16. Climbing to Hallway (Z=0) should be impossible.
    adj_blocked = fiber.get_effective_adjacency(entity_z=-24, entity_height=56, max_step=16)
    print("\nEffective Adjacency (Climbing from Z=-24 with MaxStep=16):\n", adj_blocked)
