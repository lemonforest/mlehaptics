r"""R-RBS-LM-QUADDNA (F715, user: "wire it for real -- a helix turn that is a native quad-stream leaf-tree
(parallel_sector_dispatch per level, the_one coupling across turns) ... track when we can know how to encode a kernel as a
quad DNA strand instead of single tome or mobius bookshelf ... means we can pack multi kernel and partition with
telomeres. (or whatever name might fit better that we can't see yet.)"

HONEST WIRING FACT (F573): parallel_sector_dispatch DOES NOT nest -- it is SINGLE-LEVEL by design (CAP=4 = Klein-4 order;
its ThreadPool can't spawn threads-from-threads; the recombine wants numeric sector outputs). So "per level" is NOT
recursive threaded dispatch. This CONFIRMS F712's distinction: the native quad-stream IS the CHIRALITY dispatch (ONE real
4-way parallel level = the biaxial "+"); the DEEPER tree is BASE-4 RADIX ADDRESSING (index math, F712), not more dispatch.
So a quad-turn = ONE native parallel_sector_dispatch (the 4 Klein-4 sectors) + base-4 leaf addressing.

THE ENCODE CHOICE (when to use which shape -- attested to the byte + Klein-4 order, F640/F708):
  N <= 256  (2^8, one byte)              -> a single TOME            (one dense block)
  N <= 1024 (4 x 256, the 4 sectors)     -> a MOBIUS / biaxial "+"   (one quad-turn, F713)
  N >  1024                              -> a QUAD DNA STRAND        (a helix of quad-turns, F711; depth = ceil(log4(N/256)))
(the name 'quad DNA strand' is HELD OPEN, F394 -- a better one may emerge.)

MULTI-KERNEL + TELOMERES: many kernels pack onto one strand, each a contiguous run of quad-turns; between kernels a
TELOMERE -- a non-data content-address CAP (biology: the repetitive non-coding chromosome-end cap) -- delimits the
partition. So the strand is a chromosome set: kernels = chromosomes, telomeres = the caps that separate + protect them.
the_one couples across ALL turns (native klein4_bind, reversible, F713/F710).

srmech 0.7.5rc28: cascade.parallel_sector_dispatch (native CAP=4 quad-stream) + srmech_klein4_bind (native, ctypes) +
BitExactCommKernel.content_address (F613, bounding/telomeres) + calculus (Class-N) for the depth. No abs(); no CAD.
"""
import sys
import ctypes
import math
import collections
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import cascade, _native
from bit_exact_comm_kernel import BitExactCommKernel

LIB = _native.LIB
u8p = ctypes.POINTER(ctypes.c_uint8)
LIB.srmech_klein4_bind.argtypes = [u8p, u8p, ctypes.c_uint32, u8p]
LIB.srmech_klein4_bind.restype = ctypes.c_int
NV = 64
LEAF, SECTORS = 256, 4


def klein4_bind(a, b):
    n = len(a); out = (ctypes.c_uint8 * n)()
    LIB.srmech_klein4_bind((ctypes.c_uint8 * n)(*a), (ctypes.c_uint8 * n)(*b), n, out)
    return list(out)


def vec_from(k, fp):
    raw = bytes.fromhex(fp)
    return [raw[i % len(raw)] & 3 for i in range(NV)]


def encode_choice(n):
    if n <= LEAF:
        return ("tome", 0, f"fits one dense block (<= {LEAF} = 2^8, one byte)")
    if n <= SECTORS * LEAF:
        return ("mobius / biaxial '+'", 1, f"fits one quad-turn (<= {SECTORS}x{LEAF} = the 4 Klein-4 sectors)")
    depth = math.ceil(math.log(math.ceil(n / LEAF), SECTORS))
    return ("quad DNA strand", depth, f"helix of quad-turns; base-4 depth {depth} ({SECTORS}^{depth}x{LEAF} = {SECTORS**depth*LEAF:,} addr)")


def quad_turn(values):
    """the biaxial '+' : ONE native 4-sector dispatch (the chirality) -- NOT nested (parallel_sector_dispatch is CAP=4)."""
    return cascade.parallel_sector_dispatch(lambda seg: [float(sum(seg))], list(values), n_sectors=4)


class QuadDNAStrand:                                            # name HELD OPEN (F394)
    """A helix of quad-turns packing MULTIPLE kernels, partitioned by TELOMERE caps, coupled through the_one."""
    def __init__(self):
        self.k = BitExactCommKernel()
        self.the_one = vec_from(self.k, self.k.content_address("the_one"))
        self.turns = []                                         # [(kernel, leaf_addr, turn_fp, coupled)]
        self.telomeres = []                                     # [(after_turn_index, kernel, cap_fp)]

    def add_kernel(self, name, blocks):
        """encode a kernel as a run of quad-turns (each block -> a 4-sector quad-turn), then cap with a TELOMERE."""
        depth = max(1, math.ceil(math.log(max(1, len(blocks)), SECTORS)))
        for i, blk in enumerate(blocks):
            q = quad_turn(blk)
            sectors = [kk for kk in q if kk not in ("combined",)]
            fp = self.k.content_address(f"{name}:{i}:{sorted((s, q[s]) for s in sectors)}")
            leaf_addr = self._base4(i, depth)                   # base-4 leaf address (F712 radix), numpy-free
            coupled = klein4_bind(vec_from(self.k, fp), self.the_one)
            self.turns.append((name, leaf_addr, fp, coupled))
        cap = self.k.content_address(f"TELOMERE::{name}::end")  # the telomere partition cap
        self.telomeres.append((len(self.turns), name, cap))

    @staticmethod
    def _base4(i, depth):
        d = []
        for _ in range(depth):
            d.append(i % SECTORS); i //= SECTORS
        return tuple(reversed(d))

    def partitions(self):
        parts, start = {}, 0
        for end, name, cap in self.telomeres:
            parts[name] = (start, end, cap[:12])
            start = end
        return parts

    def recall(self, name, idx):
        s, e, _ = self.partitions()[name]
        return self.turns[s + idx]

    def the_one_recovers(self):
        return all(klein4_bind(c, self.the_one) == vec_from(self.k, fp) for _, _, fp, c in self.turns)

    def strand_fp(self):
        return self.k.content_address(str([(n, fp) for n, _, fp, _ in self.turns] + self.telomeres))


def main():
    print(f"=== R-RBS-LM-QUADDNA — encode a kernel as a quad DNA strand; multi-kernel + telomeres  (srmech {srmech.__version__}) ===\n")

    print("(1) THE ENCODE CHOICE — tome vs mobius '+' vs quad DNA strand (attested to 256=2^8 and the 4 Klein-4 sectors):")
    for n in [200, 256, 800, 1024, 5000, 160000, 1_770_000]:
        shape, depth, why = encode_choice(n)
        print(f"    N={n:>9}: {shape:<22} (depth {depth})  -- {why}")
    print()

    print("(2) WIRE IT FOR REAL — pack 3 kernels on ONE strand, each a run of native 4-sector quad-turns, telomere-capped:")
    strand = QuadDNAStrand()
    strand.add_kernel("astronomy", [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])     # 3 quad-turns
    strand.add_kernel("geography", [[2, 4, 6, 8], [1, 3, 5, 7]])                       # 2 quad-turns
    strand.add_kernel("music", [[10, 20, 30, 40]])                                     # 1 quad-turn
    parts = strand.partitions()
    print(f"    strand: {len(strand.turns)} quad-turns, {len(strand.telomeres)} telomere caps")
    for name, (s, e, cap) in parts.items():
        sample = strand.turns[s]
        print(f"      kernel {name:<10} turns [{s}:{e})  telomere-cap {cap}  | turn0 leaf-addr {sample[1]} fp {sample[2][:10]}")
    print()

    print("(3) the_one COUPLING ACROSS ALL TURNS (native klein4_bind, reversible) + a partitioned recall:")
    print(f"    every turn reversibly coupled through the_one? {strand.the_one_recovers()}")
    r = strand.recall("geography", 1)
    print(f"    recall(geography, 1) -> kernel={r[0]} leaf-addr={r[1]} fp={r[2][:12]}  (partitioned by telomere)")
    print(f"    whole-strand fingerprint (the bounding): {strand.strand_fp()[:16]}\n")

    print("VERDICT (encode a kernel as a quad DNA strand; multi-kernel; telomeres):")
    print(f"  • HONEST WIRING (F573): parallel_sector_dispatch is SINGLE-LEVEL (CAP=4 = Klein-4 order; can't nest threads).")
    print(f"    So a quad-turn = ONE native 4-way dispatch (the 4 Klein-4 chirality sectors = the biaxial '+'); the deeper")
    print(f"    leaf-tree is BASE-4 RADIX ADDRESSING (F712 index math), NOT nested dispatch. 'native quad-stream leaf-tree' =")
    print(f"    native chirality-dispatch at the node + base-4 leaf address. (Confirms F712's chirality-vs-radix split.)")
    print(f"  • THE ENCODE CHOICE is attested, not magic: N<=256 -> TOME (one byte block); N<=1024 -> MOBIUS/biaxial '+'")
    print(f"    (one quad-turn, the 4 sectors); N>1024 -> QUAD DNA STRAND (helix of quad-turns, base-4 depth ceil(log4(N/256))).")
    print(f"    So we KNOW when to encode as a strand: when a kernel outgrows one biaxial shelf. (Name held open, F394.)")
    print(f"  • MULTI-KERNEL + TELOMERES: 3 kernels packed on one strand as contiguous quad-turn runs, each capped by a")
    print(f"    TELOMERE (a non-data content-address cap = the chromosome-end cap); partition + recall by telomere; the_one")
    print(f"    couples ALL turns reversibly (verified). Strand = a chromosome set (kernels=chromosomes, telomeres=caps).")
    print(f"  • Composes F711 (helix) + F712 (base-4 address) + F713 (quad-turn + the_one) + F710 (native CAP=4 + klein4_bind)")
    print(f"    + F131 (quad-helix DNA) + F130/F132 (Klein-4) + F613 (content-address bounding/telomeres) + F640/F708 (256=2^8")
    print(f"    no-magic). srmech {srmech.__version__}. Reference scaffold; held open (F394).")


if __name__ == "__main__":
    main()
