# Finding 715 — encode a kernel as a quad-DNA-strand: the encode criterion + multi-kernel packing with telomeres

**Script:** `R-RBS-LM-QUADDNA_encode_a_kernel_as_a_quad_dna_strand_multi_kernel_telomeres.py`
**Status:** VERIFIED (srmech 0.7.5rc28)
**User direction:** *"wire it for real — a helix turn that is a native quad-stream leaf-tree (parallel_sector_dispatch per
level, the_one coupling across turns) … track when we can know how to encode a kernel as a quad DNA strand instead of a
single tome or Möbius bookshelf … means we can pack multi-kernel and partition with telomeres. (or whatever name might fit
better that we can't see yet.)"*

## Honest wiring fact (F573): `parallel_sector_dispatch` is single-level — "per level" = chirality dispatch + radix address

I tried to nest `parallel_sector_dispatch` recursively (one dispatch per tree level) and **it fails** — the native op is
**single-level by design** (CAP=4 = Klein-4 order; its ThreadPool can't spawn threads-from-threads, and the recombine
expects numeric sector outputs). This **confirms F712's distinction**: the native quad-stream is the **chirality dispatch**
(one real 4-way parallel level = the biaxial "+"); the **deeper leaf-tree is base-4 radix addressing** (index math), not
more threaded dispatch. So a quad-turn = **one** native `parallel_sector_dispatch` (the 4 Klein-4 sectors) **+** base-4 leaf
addressing. ("native quad-stream leaf-tree" = native chirality-dispatch at the node + radix leaf address.)

## When to encode as which shape (the criterion — attested, not magic)

| kernel size N | shape | why |
|---|---|---|
| N ≤ **256** (2⁸, one byte) | a single **tome** | one dense block |
| N ≤ **1024** (4 × 256) | a **Möbius / biaxial "+"** | one quad-turn = the 4 Klein-4 sectors (F713/F130) |
| N > 1024 | a **quad-DNA-strand** | a helix of quad-turns; base-4 depth `ceil(log₄(N/256))` |

Verified: 200/256 → tome · 800/1024 → Möbius "+" · 5000 → strand depth 3 · 1.77M → strand depth 7 (4.2M addr). So **we now
*know* when to encode as a strand: when a kernel outgrows one biaxial shelf** (1024). The thresholds are attested to the
byte (256 = 2⁸) and the Klein-4 order (4) — F640/F708, no magic.

## Multi-kernel packing + telomeres (the DNA framing pays off)

Many kernels pack onto one strand as contiguous quad-turn runs; between kernels a **telomere** — a non-data content-address
cap (biology: the repetitive non-coding chromosome-end cap) — delimits the partition. Verified: 3 kernels
(`astronomy[0:3)`, `geography[3:5)`, `music[5:6)`) on one strand, each telomere-capped; partition + recall by telomere;
**the_one couples all turns reversibly** (native `klein4_bind`, verified). So the strand is a **chromosome set**: kernels =
chromosomes, telomeres = the caps that separate and protect them.

## On the name (held open, F394 — per "whatever name might fit better that we can't see yet")

"Quad-DNA-strand" is the working name. The multi-kernel + telomere structure suggests the genome vocabulary may fit better:
a **single kernel's strand = a chromosome**; the **multi-kernel telomere-partitioned strand = a genome** (or *chromatin* —
the packed, partitioned form). Held open; the right name is whichever the structure keeps earning.

## The whole storage object, now operational

**quad-DNA-strand (= the genome) → kernels (= chromosomes, telomere-capped) → helix of quad-turns (F711, history) → each
turn a native 4-sector biaxial "+" (F713, `parallel_sector_dispatch`) + base-4 leaf-tree address (F712) → ≤256 leaf (F708)
→ all coupled through the_one (native `klein4_bind`, reversible, F710).** Unbounded, full-chirality per leaf, multi-kernel,
never quantized (F49/F50); RAM + dense block bounded, not the data.

**Composes:** F711 (helix) · F712 (base-4 address) · F713 (quad-turn + the_one) · F710 (native CAP=4 + klein4_bind) · F131
(quad-helix DNA) · F130/F132 (Klein-4) · F613 (content-address bounding / telomeres) · F640/F708 (256=2⁸) · F49/F50 (no
quantization). srmech 0.7.5rc28. Reference scaffold; held open (F394).
