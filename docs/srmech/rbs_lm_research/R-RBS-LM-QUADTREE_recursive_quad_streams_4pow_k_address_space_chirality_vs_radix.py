r"""R-RBS-LM-QUADTREE (F712, user: "no reason we can't do quad quad quad streams with larger address space, right or no?").

YES -- for ADDRESS SPACE. Nesting the Klein-4 four-sector dispatch k deep gives 4^k blocks, each <=256 (the native dense
bound): total addressable = 4^k * 256 = 2^(2k+8). depth 3 ('quad quad quad') = 64 * 256 = 16384. So there is no reason we
can't -- the address space scales 4^k.

BUT BE PRECISE (F573/F640 -- don't dress a structure up as more than it is): the LAYERS are TWO different things.
  • LEVEL 0 -- the FIRST quad IS genuine CHIRALITY: Klein-4 V4 = the 4 sectors (gamma5 x iomega7), the substrate's 4-way
    (F130), the native parallel_sector_dispatch (CAP=4). This is real chirality, on-thesis.
  • LEVELS 1.. -- the FURTHER quads are a 4-ary RADIX ADDRESSING tree (a quadtree over <=256 blocks). Each level is a
    base-4 DIGIT of the block address, NOT another physical chirality axis. The substrate stays BI-AXIAL 4-way (F130);
    nesting does not add chirality -- it adds address bits.

So 'quad quad quad' = (1 chirality quad) x (k-1 radix quads) x (256 dense leaf). The address is a base-4 number:
2k address bits + 8 leaf bits = 2k+8 bits = 4^k*256 nodes. This is just RADIX-4 (quaternary) addressing -- it composes
with: the HELIX (F711, unbounded history) on the outside; the bucketed Class-L path (F690 route 2) which IS this tree;
D = 2^n capacity (F222); and 256 = 2^8 = one byte (the leaf). It does NOT change the chirality (still bi-axial).

srmech 0.7.5rc28: BitExactCommKernel.content_address (F613) for the address-scheme bounding; parallel_sector_dispatch
(CAP=4) is the per-level engine. No abs(); no CAD; no Workflow; no sub-agents. Reference scaffold.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

LEAF = 256          # the native dense-eig bound = 2^8 = one byte (F708/F640)
SECTORS = 4         # Klein-4 order (SRMECH_PARALLEL_SECTOR_CAP = 4)


def capacity(depth):
    return SECTORS ** depth * LEAF                       # 4^k * 256 = 2^(2k+8)


def quad_address(idx, depth):
    """decompose a global index into (base-4 sector path of length `depth`, leaf slot). The exact bounding (round-trips)."""
    leaf_slot = idx % LEAF
    block = idx // LEAF
    path = []
    for _ in range(depth):
        path.append(block % SECTORS)                     # base-4 digit (the sector at this level)
        block //= SECTORS
    assert block == 0, "idx exceeds 4^depth * 256 capacity"
    return tuple(reversed(path)), leaf_slot


def quad_unaddress(path, leaf_slot):
    block = 0
    for d in path:
        block = block * SECTORS + d
    return block * LEAF + leaf_slot


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-QUADTREE — recursive quad-streams: 4^k address space; chirality (level 0) vs radix (levels 1..)  (srmech {srmech.__version__}) ===\n")

    print("(1) THE ADDRESS SPACE SCALES 4^k * 256 = 2^(2k+8) -- yes, no reason we can't:")
    for depth in range(0, 6):
        cap = capacity(depth)
        label = {0: "(one 256 leaf)", 1: "(quad = 4x256, the biaxial '+' shelf)", 2: "(quad quad)",
                 3: "(QUAD QUAD QUAD)", 4: "(quad^4)", 5: "(quad^5)"}.get(depth, "")
        print(f"    depth {depth}: {SECTORS}^{depth} x {LEAF} = {cap:>12,} nodes = 2^{2*depth+8:<2}  {label}")
    print()

    print("(2) THE ADDRESS IS A BASE-4 NUMBER (the bounding round-trips exactly):")
    for idx in [5, 1000, 12345, 16383, 1_000_000]:
        depth = 3 if idx < capacity(3) else 11
        try:
            path, slot = quad_address(idx, depth)
            back = quad_unaddress(path, slot)
            print(f"    idx {idx:>9} (depth {depth}): sector-path {path} + leaf-slot {slot:>3}  -> back={back}  {'OK' if back == idx else 'MISMATCH'}")
        except AssertionError:
            d = 1
            while capacity(d) <= idx:
                d += 1
            path, slot = quad_address(idx, d)
            print(f"    idx {idx:>9}: needs depth {d} ({SECTORS}^{d} x {LEAF} = {capacity(d):,}); path {path} + slot {slot}")
    print()

    print("(3) THE HONEST LAYERING (F573/F640 -- chirality is ONE quad; the rest is radix):")
    print(f"    LEVEL 0 (first quad)  = Klein-4 CHIRALITY: 4 sectors gamma5 x iomega7 = the substrate's 4-way (F130),")
    print(f"                            the native parallel_sector_dispatch (CAP=4). REAL chirality, on-thesis.")
    print(f"    LEVELS 1.. (more quads)= 4-ary RADIX addressing (a quadtree over <=256 blocks). Each is a base-4 DIGIT of")
    print(f"                            the block address -- NOT another chirality axis. The substrate stays BI-AXIAL 4-way.")
    print(f"    -> 'quad quad quad' = (1 chirality quad) x (k-1 radix quads) x (256 dense leaf). Address-space, not chirality.")
    print(f"    scheme fingerprint (the bounding, F613): {k.content_address(f'quad^k x {LEAF}; sectors={SECTORS}; bits=2k+8')[:16]}\n")

    print("VERDICT (quad-quad-quad streams with a larger address space):")
    print(f"  • YES -- the address space is 4^k * 256 = 2^(2k+8): depth 3 ('quad quad quad') = 16,384 nodes; depth k scales")
    print(f"    cleanly (a base-4 / quaternary radix). Verified: the address round-trips exactly (the bounding is exact +")
    print(f"    content-addressable, F613). There is NO reason we can't -- it is just hierarchical 4-ary addressing.")
    print(f"  • BUT BE PRECISE (the no-overclaim discipline you just enforced): only the FIRST quad is CHIRALITY (the")
    print(f"    bi-axial Klein-4, F130, the native CAP=4 dispatch). The FURTHER quads are a RADIX ADDRESSING tree -- address")
    print(f"    digits, NOT more physical chirality. The substrate stays bi-axial 4-way; nesting adds address BITS, not axes.")
    print(f"  • IT COMPOSES CLEANLY: the HELIX (F711) winds turns on the OUTSIDE (unbounded history); each turn is a quad-tree")
    print(f"    of <=256 leaves (4^k address); the leaf carries the bi-axial chirality (the base Klein-4); D = 2^n (F222) and")
    print(f"    256 = 2^8 = one byte (F708). This IS F690's bucketed path made recursive + 4-ary. So: helix (history) x quad-")
    print(f"    tree (address) x Klein-4 (chirality) x 256-leaf (dense) -- unbounded, full-chirality, never quantized (F49/F50).")
    print(f"  • Composes F711 (helix) + F690 (bucketed path) + F130/F132 (Klein-4 chirality) + F710 (native quad-stream) +")
    print(f"    F222 (D=2^n) + F708/F640 (256=2^8, no-overclaim) + F49/F50 (no quantization). srmech {srmech.__version__}. Held open (F394).")


if __name__ == "__main__":
    main()
