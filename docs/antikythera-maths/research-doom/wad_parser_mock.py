import numpy as np

class MockWad:
    def __init__(self):
        # Mock Sectors for E1M1-like structure
        # Sector 0: Entry Hangar
        # Sector 1: Hallway
        # Sector 2: Acid Pit (Lowered floor)
        # Sector 3: Secret Room
        self.sectors = [
            {"id": 0, "floor": 0, "ceiling": 128, "name": "Hangar"},
            {"id": 1, "floor": 0, "ceiling": 128, "name": "Hallway"},
            {"id": 2, "floor": -24, "ceiling": 128, "name": "Acid Pit"},
            {"id": 3, "floor": 8, "ceiling": 136, "name": "Secret"}
        ]
        
        # Adjacency matrix for the Sector Graph
        # (0,1), (1,2), (1,3)
        self.adj = np.zeros((4, 4))
        connections = [(0, 1), (1, 2), (1, 3)]
        for u, v in connections:
            self.adj[u, v] = 1
            self.adj[v, u] = 1

    def get_sector_graph(self):
        return self.adj

    def get_sector_data(self):
        return self.sectors

if __name__ == "__main__":
    wad = MockWad()
    print("Mock WAD Sectors:", wad.get_sector_data())
    print("Adjacency Matrix:\n", wad.get_sector_graph())
