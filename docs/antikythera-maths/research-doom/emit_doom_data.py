import numpy as np
from wad_parser import WadParser
from doom_topology import SectorGraph

def emit_c_header():
    # 1. BIP Base Phases
    D = 512
    rng = np.random.default_rng(42)
    phi_x = rng.choice([-1, 1], size=D).astype(np.int8)
    phi_y = rng.choice([-1, 1], size=D).astype(np.int8)

    # 2. E1M1 Spectral Data
    wad = WadParser("docs/antikythera-maths/research-doom/DOOM1.WAD")
    sectors, adj = wad.build_sector_graph("E1M1")
    graph = SectorGraph(type('MockWad', (), {'get_sector_graph': lambda self: adj})())
    
    # Fiedler Vector for BSP partitioning
    vals, vecs = np.linalg.eigh(graph.L)
    fiedler = vecs[:, 1]
    
    # 3. Write Header
    with open("docs/antikythera-maths/research-doom/c/include/ds_data.h", "w") as f:
        f.write("#ifndef DS_DATA_H\n#define DS_DATA_H\n\n")
        f.write("#include <stdint.h>\n\n")
        
        f.write(f"#define DS_BIP_DIM {D}\n")
        f.write(f"#define DS_E1M1_SECTORS {len(sectors)}\n\n")
        
        # BIP Phases
        f.write("static const int8_t ds_phi_x[DS_BIP_DIM] = {\n    ")
        f.write(", ".join(map(str, phi_x)))
        f.write("\n};\n\n")
        
        f.write("static const int8_t ds_phi_y[DS_BIP_DIM] = {\n    ")
        f.write(", ".join(map(str, phi_y)))
        f.write("\n};\n\n")
        
        # Sector Data
        f.write("typedef struct { int16_t floor; int16_t ceiling; } ds_sector_info_t;\n")
        f.write("static const ds_sector_info_t ds_e1m1_sectors[DS_E1M1_SECTORS] = {\n")
        for s in sectors:
            f.write(f"    {{ {s['floor']}, {s['ceiling']} }},\n")
        f.write("};\n\n")
        
        # Fiedler Vector (Fixed-point 16.16)
        f.write("static const int32_t ds_e1m1_fiedler[DS_E1M1_SECTORS] = {\n    ")
        fiedler_fixed = (fiedler * 65536).astype(np.int32)
        f.write(", ".join(map(str, fiedler_fixed)))
        f.write("\n};\n\n")
        
        # Laplacian Matrix (Compact Sparse Row would be better, but let's do dense for now since it's only 85x85)
        f.write("static const int8_t ds_e1m1_adj[DS_E1M1_SECTORS][DS_E1M1_SECTORS] = {\n")
        for row in adj:
            f.write("    { " + ", ".join(map(lambda x: str(int(x)), row)) + " },\n")
        f.write("};\n\n")
        
        f.write("#endif\n")

if __name__ == "__main__":
    emit_c_header()
    print("Generated ds_data.h with E1M1 spectral data.")
