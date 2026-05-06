import numpy as np
from wad_parser_mock import MockWad
from doom_fiber import ZFiber
from doom_sheaf import SheafRay
from doom_topology import SectorGraph

def test_3d_movement_denial():
    print("--- Test 1: 3D Movement Denial (Z-Fiber) ---")
    wad = MockWad()
    fiber = ZFiber(wad)
    
    # DoomGuy (Height 56) in Acid Pit (Sector 2, Floor -24)
    # Trying to move to Hallway (Sector 1, Floor 0)
    # Height difference is 24.
    
    # Case A: MaxStep = 24 (Should pass)
    adj_pass = fiber.get_effective_adjacency(entity_z=-24, entity_height=56, max_step=24)
    can_climb = adj_pass[1, 2] > 0
    print(f"Climb with MaxStep 24: {'PASSED' if can_climb else 'FAILED'}")
    
    # Case B: MaxStep = 16 (Should be blocked)
    adj_fail = fiber.get_effective_adjacency(entity_z=-24, entity_height=56, max_step=16)
    can_climb = adj_fail[1, 2] > 0
    print(f"Climb with MaxStep 16: {'BLOCKED (Expected)' if not can_climb else 'FAILED'}")
    
    # Case C: Low Ceiling
    # Sector 3 (Secret) has floor 8, ceiling 136.
    # If DoomGuy is at Z=0, and tries to enter a sector with ceiling < 56, he's blocked.
    # Our mock has high ceilings, but let's mock a low ceiling.
    wad.sectors[1]['ceiling'] = 40 # Hallway now has very low ceiling
    adj_ceiling = fiber.get_effective_adjacency(entity_z=0, entity_height=56)
    can_enter = adj_ceiling[0, 1] > 0
    print(f"Enter Low Ceiling (40) with Height 56: {'BLOCKED (Expected)' if not can_enter else 'FAILED'}")
    print()

def test_sheaf_ray_absorption():
    print("--- Test 2: Sheaf Ray Absorption ---")
    # 10x10 Grid
    grid = np.ones((10, 10))
    # Place a 'dynamic' wall at (5, 5)
    grid[5, 5] = 0
    
    start = (0, 0)
    end = (9, 9)
    
    sheaf = SheafRay(start, end, grid)
    hit = sheaf.find_absorption_point()
    
    print(f"Ray from {start} to {end}")
    print(f"Dynamic Wall at (5, 5)")
    print(f"Absorption Point: {hit}")
    
    if hit == (5, 5):
        print("RESULT: Ray absorbed correctly at dynamic wall.")
    else:
        print(f"RESULT: FAILED. Ray hit {hit}")
    print()

def test_spectral_sound_diffusion():
    print("--- Test 3: Spectral Sound Diffusion ---")
    wad = MockWad()
    graph = SectorGraph(wad)
    
    # Sound source in Hangar (0)
    # Propagate sound to Hallway (1) and Acid Pit (2)
    # Acid Pit is 'further' from Hangar than Hallway is.
    
    t = 0.8
    s_dist = graph.propagate_sound(0, time=t)
    
    print(f"Sound distribution at t={t} (Source: Hangar):")
    for i, sector in enumerate(wad.get_sector_data()):
        print(f"  {sector['name']}: {s_dist[i]:.4f}")
    
    # Verify Hallway (immediate neighbor) has more sound than Acid Pit (neighbor's neighbor)
    if s_dist[1] > s_dist[2]:
        print("RESULT: Sound decayed correctly across the graph topology.")
    else:
        print("RESULT: FAILED. Sound distribution is non-physical.")
    print()

if __name__ == "__main__":
    test_3d_movement_denial()
    test_sheaf_ray_absorption()
    test_spectral_sound_diffusion()
