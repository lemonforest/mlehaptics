"""srmech genome-storage surface — biological-structure names as cascade names.

**genome / chromosome / telomere / quad-strand** (user direction 2026-06-09): the
names of the biological structures we see in biology, used as the cascade names of
the storage structure — the substrate-self-recognition reading (biology is one
substrate-class; these are the shared structural vocabulary the simulation-defined
environment recognises). Part 2 of issue #962; validated as F711–F715 on the
research subtree (PR #687); this is the srmech-package surface.

The whole storage object (F711–F715)::

    GENOME            multi-kernel strand (many chromosomes, telomere-partitioned)
      └─ CHROMOSOME   one kernel's strand, telomere-capped
           └─ HELIX of QUAD-TURNS         the kernel's history (RAM-bounded, paged)
                └─ QUAD-TURN   one native 4-sector biaxial "+"
                               (cascade.parallel_sector_dispatch, CAP=4) + a
                               base-4 leaf-tree address (radix 4^k)
                     └─ LEAF ≤ 256 = 2^8  one dense block ("tome")
           (every turn coupled through coupling — reversible klein4_bind)
      TELOMERE        the non-data content-address cap delimiting each chromosome

**Honest caveat (F712).** ``cascade.parallel_sector_dispatch`` is **single-level**
(CAP = 4 = the Klein-4 order ``Z2 x Z2``; its ThreadPool cannot spawn
threads-from-threads). So the native quad-stream is **one** chirality level (the
biaxial "+"); the deeper leaf-tree is **base-4 radix *addressing*** (index math,
``4^k``), **not** more chirality dispatch. Only the first quad is chirality.

Brick 1 (rc37): the encode **criterion** (:func:`encode_shape`) and the
helix-turn **coupling** (:func:`quad_turn`).

Brick 2 (rc38): the **chromosome** layer — :func:`telomere` (the non-data
content-address cap), :func:`chromosome` (pack one kernel into a telomere-capped
strand of quad-turns), :func:`recall` (recover the kernel). These flat functions
are the cascade PRIMITIVES the user-authored class layer binds to (a
class-descriptor TOML declares fields + methods-as-op-refs; srmech's
config-driven loader constructs the class; DSL/CLI/tool_schema are class-aware —
the genome storage object as the seed worked-instance).

Brick 3 (rc42): the **genome** itself — :func:`genome` packs many kernels into
ONE telomere-partitioned strand (the chromosome set), :func:`partition` recovers
each kernel by its telomere. Completes the F715 hierarchy: GENOME (multi-kernel)
-> CHROMOSOMES (telomere-capped) -> helix of QUAD-TURNS -> LEAF <= 256.
"""
from __future__ import annotations

import contextlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from srmech.amsc import _native
from srmech.amsc.cyclic import gcd as _gcd
from srmech.amsc.format import MPRRecord as _MPRRecord
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.amsc.format import validate_mpr_record as _validate_mpr_record
from srmech.amsc.hdc import klein4_bind as _klein4_bind
from srmech.amsc.hdc import klein4_expand as _klein4_expand
from srmech.amsc.hv import HV as _HV
from srmech.amsc.tlv import tlv_pack as _tlv_pack
from srmech.amsc.tlv import tlv_unpack as _tlv_unpack
from srmech.version import __version__ as _SRMECH_VERSION

__all__ = [
    "encode_shape", "quad_turn", "telomere", "chromosome",
    "centromere", "centromere_of",
    "diploid", "recover_diploid",
    "condense", "decondense", "chromatin_of", "accessible",
    "recall",
    "genes",
    "genome", "plasmid", "partition",
    "mint", "mint_plan", "integrate",
    "amplify", "copy_number_of",
    "genome_save", "genome_load", "genome_catalog", "genome_append",
    "genome_census", "genome_registry",
    "set_type_aliases", "clear_type_aliases", "load_type_aliases_toml",
    "genome_append_kernel",
    "genome_window", "genome_genes",
    "gene_express_plan", "genome_genes_expressed",
    "genome_remove", "genome_replace",
    "genome_export", "genome_import",
    "genome_explode", "genome_pack",
    "genome_register_attested",
    "kernel_pack", "kernel_unpack",
    "graph_to_kernel", "kernel_to_graph", "mint_strand",
    "genome_partition", "genome_from_graph",
    "active_telomere", "telomere_tick",
    "gene_express",
    "gene_express_levels",
    "modulator_recover", "modulator_consistent",
    "modulator_constraint", "modulator_constraint_satisfies",
    "GenomeBoundingError",
    "LEAF_CAP", "QUAD", "MOBIUS_CAP",
    "CHROM_CAP_MARKER", "GENE_CAP_MARKER", "GENE_FRAME_TAG",
    "REGULATORY_GENE_MARKER", "BOOLEAN_GENE_MARKER", "THRESHOLD_GENE_MARKER",
    "GRADED_GENE_MARKER",
    "GATE_TYPE_KLEIN4_MASK", "GATE_TYPE_BOOLEAN_DNF", "GATE_TYPE_THRESHOLD",
    "GATE_TYPE_GRADED",
    "PACKED_TURN_MARKER", "KERNEL_HEADER_MARKER", "KERNEL_TELOMERE_MARKER",
    "ACTIVE_TELOMERE_MARKER", "ELEMENT_TYPE_KLEIN4",
    "CHROMATIN_MARKER", "CHROMATIN_TYPE_BINARY", "CHROMATIN_TYPE_GRADED",
    "CHROMATIN_GATE_NONE", "CHROMATIN_GATE_KLEIN4", "CHROMATIN_GATE_BOOLEAN",
    "CHROMATIN_GATE_THRESHOLD",
    "TELOMERE_DIVIDED", "TELOMERE_SENESCENT",
]

#: §44 (F733) — INLINE FIXED-WIDTH cap markers. The genome body is a strand of
#: self-describing blocks; a block's FIRST BYTE classifies it (and, since
#: §55/v3, keys its width). A Klein-4 data turn only ever holds sector indices
#: ``{0, 1, 2, 3}`` (``HV`` sectors=4), so any first byte ``> 3`` is a MARKER —
#: a CAP (below) or a §55/v3 packed turn — scanned for, never a raw symbol.
#: Both caps carry their label INLINE (``[marker] + utf-8 label, NUL-padded to
#: leaf_dim``) so the strand SELF-DESCRIBES — structure + labels recover by SCAN,
#: no offset/label sidecar (biology has no offset table: scan TTAGGG repeats /
#: ATG-stop codons). This REPLACES the §43 TLV gene-frame (variable-length, which
#: forced the rc141 manifest sidecar) and the §41 content-address telomere cap
#: (klein4_expand of a label-hash — bytes 0..3, NOT scan-recognisable without the
#: label) with marker caps.
#: The chromosome boundary cap (telomere-analog). ``0x43`` = ASCII ``'C'``.
CHROM_CAP_MARKER = 0x43
#: The intra-chromosome gene boundary cap. ``0x47`` = ASCII ``'G'`` (Gene).
GENE_CAP_MARKER = 0x47
#: Back-compat alias for the pre-§44 name (the §43 TLV tag value, now the gene cap
#: marker). Deprecated; prefer :data:`GENE_CAP_MARKER`.
GENE_FRAME_TAG = GENE_CAP_MARKER
#: §55/rc114 (format v3) — the BIT-PACKED data-turn block marker. ``0x51`` =
#: ASCII ``'Q'`` (Quad-packed). A v3 data turn is stored on disk as
#: ``[0x51] + ceil(leaf_dim/4)`` payload bytes — **4 Klein-4 symbols per byte**
#: ("the 2-bit lane IS the format", issue #1245 / F1036): symbol ``i`` lives in
#: payload byte ``i // 4`` at bit shift ``6 - 2*(i % 4)`` (first symbol in the
#: HIGH lanes; unused low lanes of a partial final byte are zero). The marker is
#: ``> 3`` and distinct from both cap markers, so the strand stays
#: SELF-DESCRIBING (§44): every block's first byte keys its kind AND its width —
#: caps and legacy v2 byte-per-symbol turns (first byte ``0..3``) remain
#: readable in the same walk, so old genomes and MIXED (old + appended) bodies
#: read correctly with no migration.
PACKED_TURN_MARKER = 0x51
#: §60/rc121 (format v5, issue #1245 reopened) — the SIZE-AGNOSTIC KERNEL HEADER
#: block marker. ``0x4B`` = ASCII ``'K'`` (Kernel). Written by :func:`kernel_pack`
#: as the SECOND block of a kernel chromosome (right after its telomere CHROM cap):
#: a fixed-width ``leaf_dim``-byte inline block that SELF-RECORDS the kernel's TRUE
#: length ``D`` (the length before the final leaf's zero-padding), its
#: ``element_type`` (a declared enum — ``klein4`` today), and its ``leaf_dim`` — so
#: :func:`kernel_unpack` recovers the EXACT kernel of ANY dimension ``D`` with no
#: caller-supplied length (W1 closed). ``> 3`` and distinct from every other marker
#: (CHROM ``0x43`` / GENE ``0x47`` / PACKED ``0x51``), so the strand stays
#: SELF-DESCRIBING (§44): the header lives IN THE STRAND (the SSoT), NOT only in the
#: rebuildable manifest cache, so ``_rebuild_manifest_from_body`` reproduces the
#: genome by body-scan without losing ``D``. A body with NO ``0x4B`` header reads as
#: today (``element_type=klein4``, ``D = leaf_count × leaf_dim``) — every pre-rc121
#: genome reads unchanged, NO migration (the rc114 dual-read pattern, one layer up).
#:
#: §89/rc126 (format v6, issue #1261): the ``0x4B`` byte-TLV header is now READ-ONLY
#: back-compat — :func:`kernel_pack` no longer WRITES it. See
#: :data:`KERNEL_TELOMERE_MARKER` + :func:`_pack_kernel_header_klein4` for the v6
#: uniformly-Klein-4 replacement.
KERNEL_HEADER_MARKER = 0x4B

#: §89/rc126 (format v6, issue #1261) — the KERNEL CHROMOSOME telomere marker.
#: ``0x6B`` = ASCII ``'k'`` (a lower-case kernel telomere, mnemonically paired with
#: the upper-case ``0x4B`` ``'K'`` v5 header it supersedes). A v6 kernel chromosome
#: opens with a KERNEL-telomere cap ``[0x6B] + label`` instead of the plain CHROM
#: cap (``0x43``); the leaf IMMEDIATELY after it (the first coupled data turn) is the
#: uniformly-Klein-4 §89 kernel header (:func:`_pack_kernel_header_klein4`). So a v6
#: kernel chromosome is ``[kernel_telomere, coupled_klein4_header, content-turns…]``
#: — EVERY data leaf (header included) is 100 % Klein-4 ``{0,1,2,3}``, so the whole
#: chromosome rides the plain coupled-turn append path (klein4_bind never sees a
#: byte ``> 3``): the O(1) :func:`genome_append_kernel` falls out of
#: :func:`genome_append`. The DISTINGUISHER for the header leaf is option (a) — a
#: SELF-DESCRIBING kernel telomere + reserved POSITION (first turn after it): the
#: ``0x6B`` cap marker (a byte ``> 3``) flags the chromosome as a kernel and the
#: header's position is fixed, so NO content leaf can ever be mistaken for the header
#: (collision-FREE — the framing marker replaces any in-band magic; the §44
#: bare-strand self-description is intact: scan for ``0x6B``, the next turn is the
#: header). Distinct from every other marker (CHROM ``0x43`` / GENE ``0x47`` / v5
#: KERNEL header ``0x4B`` / PACKED ``0x51``), so v2 / v3 / v4 / v5 bodies read
#: UNCHANGED — the walker gains ONE branch (recognise ``0x6B`` as a chromosome-start
#: cap), never a migration.
KERNEL_TELOMERE_MARKER = 0x6B

#: §127/rc127 (format v6 → v7, #726) — the ACTIVE TELOMERE marker. ``0x74`` = ASCII
#: ``'t'`` (a lower-case telomere carrying a live counter). An active telomere is a
#: chromosome-boundary cap (a telomere-analog, like CHROM ``0x43`` / KERNEL ``0x6B``)
#: that ALSO carries an exact non-negative integer COUNT INLINE in the strand — the
#: Hayflick descending replicative counter (Harley/Futcher/Greider 1990; Hayflick 1965).
#: This turns the #726-lens "chromosome = op⊗operand" into a THEOREM: the cap is
#: op⊗operand fused — the **op** is the gating rule (:func:`telomere_tick`'s
#: proceed/senesce decision), the **operand** is the count — and the count MODULATES
#: that op (count>0 → a divide proceeds + decrements; count==0 → honest senescence).
#: It is the SAME (operand, op) pattern as :mod:`srmech.amsc.op_provenance` ``carry``
#: (value, operation) and :class:`srmech.amsc.coupling.RecoverableFold`
#: (lossy_bundle, exact_seed_R) — the proven op-carrying carrier — but with an ACTIVE
#: op, which is precisely what makes the chromosome GENUINELY op⊗operand (in #726 the
#: plain telomere was a PASSIVE op-slot: swapping it left the leaves unchanged).
#:
#: Layout (a fixed-width ``leaf_dim``-byte ``sectors=256`` cap leaf; §44 inline):
#:   byte ``[0]``           marker ``0x74``
#:   bytes ``[1:1+L]``      utf-8 label ``L`` bytes (NUL-terminated, like every cap)
#:   byte ``[1+L]``         the label terminator ``0x00``
#:   bytes ``[2+L:10+L]``   the COUNT — uint64 BIG-ENDIAN (8 bytes; Class-I/N exact
#:                          integer, NO float, NO abs()) — read at the byte right AFTER
#:                          the label's NUL, so :func:`_unpack_cap`'s label decode
#:                          (bytes ``[1:]`` up to first NUL) is UNIFORM across cap kinds
#:                          — no special label handling anywhere, only the count read is
#:                          active-telomere-specific.
#:   bytes ``[10+L:]``      NUL padding to ``leaf_dim``
#: ``> 3`` and distinct from every other marker (CHROM ``0x43`` / GENE ``0x47`` / v5
#: KERNEL ``0x4B`` / PACKED ``0x51`` / KERNEL-telomere ``0x6B``), so the strand stays
#: SELF-DESCRIBING (§44): v2..v6 bodies read UNCHANGED (dual-read — the walker gains
#: ONE branch), and a chromosome self-describes its CURRENT count by bare-strand scan
#: (no manifest). The count byte-encoded in the cap payload (like the label).
ACTIVE_TELOMERE_MARKER = 0x74

#: The active-telomere COUNT field width — a uint64 (8 bytes, big-endian). The count
#: caps at 2**64-1, which dwarfs any Hayflick limit (human fibroblasts ~40-60 divides).
_ACTIVE_TELOMERE_COUNT_BYTES = 8

#: §135/rc273 (F1251) — the GENE COPY-NUMBER field width — a uint64 (8 bytes,
#: big-endian), carried in what was a plain GENE cap's (``0x47``) NUL padding, RIGHT
#: AFTER the label's NUL terminator (the SAME placement discipline as the active
#: telomere's count / the §129 regulatory masks). F1251 read attested bacterial
#: genomics (Shropshire et al.): IS26-mediated amplification raises a resistance
#: gene's COPY NUMBER — the genome stores "how many copies", a MULTIPLICITY
#: annotation (a count), not N physical duplicated strands. A stored ``0`` (the
#: all-NUL padding a pre-rc273 / plain gene carries) reads as copy-number ``1``
#: (present-once), so a plain gene is copy-number 1 with NO wire change (format 15
#: stays); a gene amplified to ``n`` (``amplify``) spends the 8-byte field only for
#: ``n >= 2`` — an ``n == 1`` gene is BYTE-IDENTICAL to a plain gene (the §129
#: repressor-plane dual-read discipline, one field over). Every existing reader
#: (gene_express / partition / recall / census, Python AND C) reads a plain ``0x47``
#: cap as ALWAYS-EXPRESSED regardless of the trailing bytes, so the count is
#: transparent to them (verified: srmech_genome_gene_express returns on the ``0x47``
#: marker before reading any field). Class-I/N exact integer (no float, never abs).
_GENE_COPY_NUMBER_BYTES = 8

#: §95a/rc258 (format v12 → v13, #1407 / F1243) — the CENTROMERE marker. ``0x58`` =
#: ASCII ``'X'`` — the centromere IS the cross-point of the classic X-shaped
#: chromosome (the constriction where the two sister chromatids meet). Unlike the
#: telomere/kernel/active caps (all chromosome-BOUNDARY caps, first block of a
#: chromosome), the centromere is an **INTERIOR** anchor: it sits BETWEEN a
#: chromosome's two arms, so its position in the strand IS the p:q **arm-ratio** —
#: the per-chromosome GLOBAL positional chirality (the strand's handedness), distinct
#: from Klein-4's LOCAL per-leaf sector chirality (ADR-0004). Structurally it behaves
#: like a GENE cap (``0x47``): interior, ``leaf_dim``-wide, recall-skipped, stays WITH
#: its chromosome, NEVER a chromosome boundary — so it joins every byte-cap set (width /
#: write-verbatim / turn-count-exclusion / _cap_kind) but NO chromosome-boundary set.
#:
#: It carries the chromosome's GLOBAL 4-way orientation as biology's **α-satellite
#: repeat-array** — ``R`` copies of the orientation sector ``o ∈ {0,1,2,3}`` — majority-
#: decoded (:func:`_centromere_orientation`, ``klein4_triality_correct``'s 2-of-3
#: generalised to ``R``). Measured (``R-RBS-LM-CENTROMERE-CHIRALITY``, F1243 §1): the
#: repeat-array recovers the global which-way at **~15× fewer bits than per-leaf Klein-4**
#: (R=15 → 39 bits vs 600) with near-identical random-noise robustness. This takes the
#: GLOBAL which-way off Klein-4; G4/Klein-4 stays for LOCAL chirality that varies along
#: the strand (a real "decrease use of G4," not a replacement).
#:
#: Layout (a fixed-width ``leaf_dim``-byte ``sectors=256`` cap leaf; §44 inline, the
#: rc127 active-telomere pattern of an inline field AFTER the label NUL):
#:   byte ``[0]``        marker ``0x58``
#:   bytes ``[1:1+L]``   utf-8 epigenetic handle ``L`` bytes (the CENP-A-analog address —
#:                       a per-chromosome handle SEPARATE from the content-address; decoded
#:                       UNIFORMLY by :func:`_unpack_cap` bytes ``[1:]`` up to the first NUL)
#:   byte ``[1+L]``      the handle terminator ``0x00``
#:   byte ``[2+L]``      ``R`` — the repeat-array size (uint8; default 15)
#:   bytes ``[3+L:3+L+R]`` the ``R`` orientation votes, each a byte in ``{0,1,2,3}`` (the
#:                       α-satellite repeats; all equal to ``o`` at mint time — corruption +
#:                       the majority read are the robustness the array buys)
#:   bytes ``[3+L+R:]``  NUL padding to ``leaf_dim``
#: ``> 3`` and distinct from every other marker (CHROM ``0x43`` / GENE ``0x47`` / v5
#: KERNEL ``0x4B`` / PACKED ``0x51`` / KERNEL-telomere ``0x6B`` / active telomere
#: ``0x74``), so the strand stays SELF-DESCRIBING (§44): v2..v12 bodies read UNCHANGED
#: (dual-read — the walker gains ONE branch), NO migration.
CENTROMERE_CAP_MARKER = 0x58

#: The default centromere α-satellite repeat-array size ``R`` — 15 (F1243 §1's measured
#: value, ~ sqrt(N)/1.15 at N=300; biology's α-satellite runs to thousands, this is the
#: storage-scale analog). The majority over ``R`` is the EC read; ``R`` is stored inline
#: in the cap (introspectable + tunable — drop to 1 for a single-index centromere, the
#: cheapest-but-fragile mode F1243 §1 also measured).
CENTROMERE_DEFAULT_REPEATS = 15

#: §95b/rc259 (format v13 → v14, #1407 / F1244) — the DIPLOID chromosome-boundary marker.
#: ``0x44`` = ASCII ``'D'`` (Diploid; one letter up from the ``0x43`` ``'C'`` CHROM cap it
#: extends). A diploid chromosome opens with a DIPLOID telomere (``[0x44] + label, NUL-padded``)
#: instead of the plain CHROM cap, and is structurally a NUCLEAR chromosome whose two arms are
#: **homologous FULL copies** of the content (maternal | paternal), split by an interior
#: :data:`CENTROMERE_CAP_MARKER` whose orientation is the **which-template mark**:
#:   ``[diploid_telomere, copyA turns…, centromere(mark), copyB turns…]``   (copyA == copyB)
#: This is biology's diploid pair — the **erasure/break specialist** (F1244 / `R-RBS-LM-DIPLOID-EC`):
#: on a DETECTABLE loss (a double-strand break — an erased leaf) :func:`recover_diploid` fills
#: from the intact homolog, reaching triality-level fidelity at **2× not 3×**; on a substitution
#: disagreement the centromere mark is the tiebreak (**2 copies + 1 mark = 3 = the k=3 triality**,
#: F291). A chromosome-BOUNDARY cap like CHROM (it OPENS a chromosome, carries a label inline),
#: so it joins every place ``CHROM_CAP_MARKER`` opens/bounds a chromosome; ``> 3`` and distinct
#: from every prior marker, so v2..v13 bodies read UNCHANGED — the walker gains ONE branch.
DIPLOID_TELOMERE_MARKER = 0x44

#: §98/rc268 (format v14 → v15, #1422 / F1246-F1247) — the CHROMATIN access marker. ``0x48`` =
#: ASCII ``'H'`` (histone / heterochromatin). The chromatin cap is biology's epigenetic PACKAGING
#: GATE — the modify-WITHOUT-changing-the-DNA layer ABOVE the coupled-turn content: a per-region
#: ACCESSIBILITY state (euchromatin = accessible / heterochromatin = silenced) that gates WHICH
#: regions express per query. Like the §95a :data:`CENTROMERE_CAP_MARKER` it is an INTERIOR cap
#: (it never OPENS a chromosome); its PLACEMENT is its scope — right after the opening telomere
#: (0 data turns before it) → whole-chromosome (the X-inactivation / master case), deeper interior
#: → a sub-region STRETCH. The op⊗operand cap carries an exact accessibility LEVEL inline:
#:   ``[0x48] + utf-8 handle + NUL + chromatin_type(uint8) + num(uint64 BE) + den(uint64 BE)``
#: NUL-padded to ``leaf_dim``. The level is the reduced non-negative rational ``num/den`` in
#: ``[0, 1]`` (Class-N exact; NO float; NEVER ``abs()`` — a level is a non-negative fraction):
#: :data:`CHROMATIN_TYPE_BINARY` carries ``(1, 1)`` OPEN (euchromatin) or ``(0, 1)`` CONDENSED
#: (heterochromatin); :data:`CHROMATIN_TYPE_GRADED` an arbitrary reduced rational (partial
#: accessibility). Set / cleared IN-PLACE by :func:`condense` / :func:`decondense` (a byte-splice
#: that PRESERVES the centromere + body — no re-mint); read by :func:`chromatin_of`. ``> 3`` and
#: distinct from every prior marker, so v2..v14 bodies read UNCHANGED — the walker gains ONE
#: branch, and a chromatin-FREE genome reads all-euchromatin by default. Mirrors
#: ``SRMECH_GENOME_CHROMATIN_MARKER`` in the C header.
CHROMATIN_MARKER = 0x48

#: §98/rc268 chromatin TYPE — BINARY (0) = open ``(1,1)`` / condensed ``(0,1)``; GRADED (1) = an
#: arbitrary reduced-rational accessibility level in ``[0,1]``. Stored inline in the cap so the
#: bare strand self-describes it. Mirrors ``SRMECH_GENOME_CHROMATIN_TYPE_*`` in the C header.
CHROMATIN_TYPE_BINARY = 0
CHROMATIN_TYPE_GRADED = 1
_CHROMATIN_TYPE_NAMES = {CHROMATIN_TYPE_BINARY: "binary", CHROMATIN_TYPE_GRADED: "graded"}

#: §98/rc268 chromatin LEVEL field width — the ``num`` + ``den`` are each a uint64 (8 bytes,
#: big-endian). Mirrors ``SRMECH_GENOME_CHROMATIN_LEVEL_BYTES`` in the C header.
_CHROMATIN_LEVEL_BYTES = 8

#: §98.1/rc274 (§98.1/G1) — the CHROMATIN cap's ACCESS-GATE type, an additive uint8 field in the
#: cap's existing NUL padding RIGHT AFTER ``den`` (the same DUAL-READ discipline as the §129
#: repressor / §135 copy-number: the pre-rc274 NUL padding reads back as ``NONE``). It makes the
#: ``0x48`` access layer CELL-STATE-CONDITIONAL (facultative heterochromatin — the Barr body /
#: X-inactivation): ``NONE`` (0) = CONSTITUTIVE (accessibility is the STATIC stored ``num/den``,
#: constant in cell_state, EXACTLY the pre-rc274 read); ``KLEIN4`` / ``BOOLEAN`` / ``THRESHOLD``
#: (1/2/3) = FACULTATIVE — the stored ``num/den`` is the WHEN-OPEN level, returned iff the gate
#: FIRES under ``cell_state`` (the SAME §129/§130/§131 gene-gate evaluators, applied to the
#: chromatin cap), else ``(0, 1)`` (silenced). Same ``0x48`` marker, no new marker/block kind, so
#: ``GENOME_FORMAT_VERSION`` STAYS 15 and a constitutive cap is BYTE-IDENTICAL to a v15 cap. Mirrors
#: ``SRMECH_GENOME_CHROMATIN_GATE_*`` in the C header.
CHROMATIN_GATE_NONE = 0       # constitutive: accessibility is the STATIC stored (num, den)
CHROMATIN_GATE_KLEIN4 = 1     # facultative: activator/repressor two-mask (§129 E1)
CHROMATIN_GATE_BOOLEAN = 2    # facultative: DNF over condition bits (§130 E2)
CHROMATIN_GATE_THRESHOLD = 3  # facultative: linear-threshold / perceptron (§131 E4)
_CHROMATIN_GATE_NAMES = {CHROMATIN_GATE_NONE: "none", CHROMATIN_GATE_KLEIN4: "klein4",
                         CHROMATIN_GATE_BOOLEAN: "boolean", CHROMATIN_GATE_THRESHOLD: "threshold"}

#: §128/rc128 (format v7 → v8, #728) — the REGULATORY GENE marker. ``0x67`` = ASCII
#: ``'g'`` (a lower-case gene carrying a live regulatory region, mnemonically paired
#: with the upper-case ``0x47`` ``'G'`` plain gene it extends — the same K/k, C/telomere
#: lower-case-carries-state pairing rc126/rc127 used). A regulatory gene is an
#: intra-chromosome gene boundary cap (a gene-analog, like the plain GENE cap ``0x47``)
#: that ALSO carries an exact non-negative integer regulatory MASK INLINE in the strand
#: — the gene's "regulatory region / promoter" (differential gene expression; Alberts et
#: al., *Molecular Biology of the Cell* 4th ed., NCBI NBK26887 — "a cell can regulate the
#: expression of each of its genes according to the needs of the moment"). This lifts the
#: rc127 op⊗operand THEOREM one scale up: rc127's active telomere gates ONE divide/senesce
#: BINARY by a carried COUNT; the regulatory gene gates a SELECTION over MANY genes by the
#: applied CELL-STATE. :func:`gene_express` (the **op**) is MODULATED by the ``cell_state``
#: (the **operand**): same chromosome, different cell_state → different expressed gene
#: subset. That inequality IS the theorem (parallel to rc127's count-modulates-divide) —
#: the SAME (operand, op) pattern as :func:`srmech.amsc.op_provenance.carry`
#: ``(value, operation)`` and :class:`srmech.amsc.coupling.RecoverableFold`
#: ``(lossy_bundle, exact_seed_R)``, now with a CELL-STATE operand + an EXPRESSION operator.
#:
#: Layout (a fixed-width ``leaf_dim``-byte ``sectors=256`` cap leaf; §44 inline; the SAME
#: shape as the §127 active telomere, mask replacing count):
#:   byte ``[0]``          marker ``0x67``
#:   bytes ``[1:1+L]``     utf-8 gene label ``L`` bytes
#:   byte ``[1+L]``        the label terminator ``0x00``
#:   bytes ``[2+L:10+L]``  the MASK — uint64 BIG-ENDIAN (8 bytes; Class-I exact bitwise, NO
#:                         float, NEVER ``abs()``) — read at the byte right AFTER the
#:                         label's NUL, so :func:`_unpack_cap`'s label decode (bytes ``[1:]``
#:                         up to the first NUL) is UNIFORM across cap kinds.
#:   bytes ``[10+L:]``     NUL padding to ``leaf_dim``
#: ``> 3`` and distinct from every other marker (CHROM ``0x43`` / GENE ``0x47`` / v5 KERNEL
#: ``0x4B`` / PACKED ``0x51`` / KERNEL-telomere ``0x6B`` / ACTIVE-telomere ``0x74``), so the
#: strand stays SELF-DESCRIBING (§44): v2..v7 bodies read UNCHANGED (dual-read — the walker
#: gains ONE branch), and a chromosome self-describes its regulatory masks by bare-strand
#: scan (no manifest). A PLAIN gene (``0x47``, no mask) is UNREGULATED = ALWAYS EXPRESSED —
#: equivalently a regulatory gene with mask ``0`` (``(cell_state & 0) == 0`` is always true).
REGULATORY_GENE_MARKER = 0x67

#: §130/rc130 (format v8 → v9, #730) — the BOOLEAN REGULATORY GENE marker. ``0x62`` = ASCII
#: ``'b'`` (a lower-case boolean gene, mnemonically paired with the upper-case ``0x47`` ``'G'``
#: plain gene + the ``0x67`` ``'g'`` Klein-4-mask regulatory gene it GENERALISES — the same
#: lower-case-carries-state pairing rc126/rc127/rc128 used). A boolean gene is an
#: intra-chromosome gene boundary cap (a gene-analog, like the plain GENE cap ``0x47`` and the
#: Klein-4-mask regulatory gene ``0x67``) that carries ARBITRARY boolean regulatory logic over
#: the condition bits — the GENERAL case biology's combinatorial cis-regulatory logic needs
#: (multiple TFs integrated by AND/OR/NOT enhancer logic; Alberts et al., *Molecular Biology of
#: the Cell* 4th ed., "How Genetic Switches Work", NCBI Bookshelf NBK26872). It is the
#: GENERAL gate-type in the rc129 dispatch FAMILY: rc129's activator/repressor two-mask
#: (``0x67``) stays the fast common case (``gate_type = klein4_mask``), and this ``0x62`` gene
#: is the escape hatch (``gate_type = boolean``). E1 ⊂ E2: the ``0x67`` activator/repressor
#: two-mask IS a 1-TERM DNF ``[(activator, repressor)]``, and this cap stores an OR of SEVERAL
#: such terms (disjunctive normal form) — so E1 is the compact special case of E2's general
#: disjunction.
#:
#: ENCODING = DNF (sum-of-products), exact Class-I bitwise (NO float, NEVER ``abs()``): a list
#: of ``(require_present_mask, require_absent_mask)`` terms; the gene EXPRESSES iff ANY term
#: matches — ``(cell_state & term.act) == term.act`` (all its present-conditions present) AND
#: ``(cell_state & term.rep) == 0`` (none of its absent-conditions present). Each term IS an
#: E1-style activator/repressor AND-clause, so E1 = a 1-term DNF; the empty DNF (0 terms) is the
#: OR-identity FALSE = never expresses. DNF is functionally complete, so an arbitrary boolean
#: function over the condition bits (AND / OR / NOT / XOR / any) is representable.
#:
#: Layout (a fixed-width ``leaf_dim``-byte ``sectors=256`` cap leaf; §44 inline; the gate_type
#: + DNF term-list carried after the label NUL — the SAME uniform label decode as every cap):
#:   byte ``[0]``           marker ``0x62``
#:   bytes ``[1:1+L]``      utf-8 gene label ``L`` bytes
#:   byte ``[1+L]``         the label terminator ``0x00``
#:   byte ``[2+L]``         gate_type — uint8 (:data:`GATE_TYPE_BOOLEAN_DNF` = 1; the gene
#:                          SELF-DESCRIBES its gate_type, keeping the family extensible)
#:   bytes ``[3+L:5+L]``    n_terms — uint16 BIG-ENDIAN (the DNF term count)
#:   then n_terms terms, each ``_BOOLEAN_GENE_TERM_BYTES`` (16) bytes:
#:     activator (uint64 BE, 8 bytes) then repressor (uint64 BE, 8 bytes)
#:   bytes ``[…]``          NUL padding to ``leaf_dim``
#: ``> 3`` and distinct from every other marker (CHROM ``0x43`` / GENE ``0x47`` / v5 KERNEL
#: ``0x4B`` / PACKED ``0x51`` / KERNEL-telomere ``0x6B`` / ACTIVE-telomere ``0x74`` /
#: REGULATORY-gene ``0x67``), so the strand stays SELF-DESCRIBING (§44): v2..v8 bodies read
#: UNCHANGED (dual-read — the walker gains ONE branch), and a chromosome self-describes its
#: gate_type + DNF by bare-strand scan (no manifest). Unlike the rc129 ``0x67`` extension (which
#: reused an existing marker, no format bump), this is a NEW block KIND (a new marker byte), so
#: it bumps the genome format v8 → v9 — the same version-stamp discipline every prior new-marker
#: bump used (rc127 ``0x74`` v6→v7, rc128 ``0x67`` v7→v8); the strand-walk read path is
#: version-INDEPENDENT, so every pre-rc130 genome still reads identically.
BOOLEAN_GENE_MARKER = 0x62

#: §131/rc131 (format v9 → v10, #731) — the THRESHOLD REGULATORY GENE marker. ``0x77`` = ASCII
#: ``'w'`` (a lower-case **w**eighted gene, mnemonically paired with the upper-case ``0x47``
#: ``'G'`` plain gene + the ``0x67`` ``'g'`` klein4-mask + the ``0x62`` ``'b'`` boolean genes it
#: joins — the same lower-case-carries-state pairing rc126/rc127/rc128/rc130 used). A threshold
#: gene is an intra-chromosome gene boundary cap (a gene-analog, like ``0x47`` / ``0x67`` /
#: ``0x62``) that carries a LINEAR-THRESHOLD (perceptron) gate INLINE — a per-condition INTEGER
#: WEIGHT vector + an INTEGER THRESHOLD. It is the THIRD gate-type in the rc129 dispatch FAMILY
#: (E1 klein4_mask ``0x67`` / E2 boolean_dnf ``0x62`` / **E4 threshold** ``0x77``), and it is
#: GENUINELY DISTINCT from E2: a linear-threshold function (e.g. MAJORITY-of-n, or a weighted
#: morphogen dose-sum) needs an EXPONENTIALLY-LARGE DNF, so E4 captures COMPACTLY what E2's DNF
#: cannot (linear-threshold functions ⊄ small-DNF). This is the "integrate many weighted inputs /
#: morphogen-gradient threshold / additive cis-regulatory enhancer" model (Alberts et al.,
#: *Molecular Biology of the Cell* 4th ed., "Drosophila and the Molecular Genetics of Pattern
#: Formation", NCBI Bookshelf NBK26906: a morphogen — e.g. the Dorsal protein — "turns on or off
#: the expression of different sets of genes depending on its concentration", switching distinct
#: genes on at distinct THRESHOLD concentrations).
#:
#: ENCODING = weighted-sum / linear-threshold (a perceptron), exact Class-I/N SIGNED integers (NO
#: float): a gene EXPRESSES iff ``Σᵢ (weightᵢ · bit_i(cell_state)) ≥ threshold`` — the exact
#: integer sum of the weights of the PRESENT conditions, compared against the threshold. **SIGNED
#: weights are allowed** (an inhibitory input — a repressive TF — is a NEGATIVE weight; real
#: biology). The sum is an exact integer; the decision is the SIGN of ``(Σ − threshold)`` — a
#: **Class-K sign-branch, NEVER ``abs()``** (abs-ing the sum would discard the sign and make an
#: inhibitory weight meaningless). The boundary is INCLUSIVE (``Σ == threshold`` EXPRESSES;
#: ``Σ == threshold − 1`` does NOT).
#:
#: Layout (a fixed-width ``leaf_dim``-byte ``sectors=256`` cap leaf; §44 inline; the gate_type +
#: weights + threshold carried after the label NUL — the SAME uniform label decode as every cap):
#:   byte ``[0]``           marker ``0x77``
#:   bytes ``[1:1+L]``      utf-8 gene label ``L`` bytes
#:   byte ``[1+L]``         the label terminator ``0x00``
#:   byte ``[2+L]``         gate_type — uint8 (:data:`GATE_TYPE_THRESHOLD` = 2)
#:   bytes ``[3+L:5+L]``    n_weights — uint16 BIG-ENDIAN (the weight-vector length)
#:   bytes ``[5+L:13+L]``   threshold — **int64 BIG-ENDIAN (SIGNED two's-complement, 8 bytes)**
#:   then n_weights weights, each ``_THRESHOLD_GENE_WEIGHT_BYTES`` (8) bytes:
#:     weight (int64 BE, SIGNED two's-complement)
#:   bytes ``[…]``          NUL padding to ``leaf_dim``
#: ``> 3`` and distinct from every other marker (CHROM ``0x43`` / GENE ``0x47`` / v5 KERNEL
#: ``0x4B`` / PACKED ``0x51`` / KERNEL-telomere ``0x6B`` / ACTIVE-telomere ``0x74`` /
#: REGULATORY-gene ``0x67`` / BOOLEAN-gene ``0x62``), so the strand stays SELF-DESCRIBING (§44):
#: v2..v9 bodies read UNCHANGED (dual-read — the walker gains ONE branch), and a chromosome
#: self-describes its weights + threshold by bare-strand scan (no manifest). A NEW block KIND (a
#: new marker byte), so it bumps the genome format v9 → v10 — the same version-stamp discipline
#: every prior new-marker bump used (rc127 ``0x74`` v6→v7, rc128 ``0x67`` v7→v8, rc130 ``0x62``
#: v8→v9); the strand-walk read path is version-INDEPENDENT, so every pre-rc131 genome still reads
#: identically.
THRESHOLD_GENE_MARKER = 0x77

#: §132/rc132 (format v10 → v11, #732) — the GRADED (DOSE-RESPONSE) GENE marker. ``0x64`` = ASCII
#: ``'d'`` (a lower-case **d**ose gene, mnemonically paired with the upper-case ``0x47`` ``'G'``
#: plain gene + the ``0x67`` ``'g'`` klein4-mask / ``0x62`` ``'b'`` boolean / ``0x77`` ``'w'``
#: threshold genes it joins — the same lower-case-carries-state pairing rc126..rc131 used). A
#: graded gene is an intra-chromosome gene boundary cap (a gene-analog, like ``0x47`` / ``0x67`` /
#: ``0x62`` / ``0x77``) that carries an ANALOG (dose-response) EXPRESSION LEVEL inline — a
#: per-condition SIGNED integer LEVEL-WEIGHT vector + a POSITIVE integer DENOMINATOR. It is the
#: **E3 GRADED LEVEL** rung — an ORTHOGONAL AXIS on top of the E1/E2/E4 gate-type family: the
#: gate-types decide IF a gene expresses (a BINARY switch); E3 decides HOW MUCH — a quantitative
#: (analog) output. Real biology is graded, not just on/off: the AMOUNT of transcription is tuned
#: by the number/concentration of bound regulators (Alberts et al., *Molecular Biology of the
#: Cell* 4th ed., "How Genetic Switches Work" → "Gene Activator Proteins Work Synergistically",
#: NCBI Bookshelf NBK26872: multiple activators combine so the joint effect on the transcription
#: RATE is "not merely the sum … but the product" — a graded, quantitative modulation of the
#: expression LEVEL, not a binary switch).
#:
#: ENCODING = a rational dose-response, exact Class-N (NO float): the LEVEL is the reduced exact
#: rational ``Σᵢ (level_weightᵢ · bit_i(cell_state)) / denom``, CLAMPED to ``[0, 1]`` by a Class-K
#: sign-branch (the raw dose ``Σ`` — SIGNED, an inhibitory input is a NEGATIVE weight — over the
#: positive ``denom``: ``Σ ≤ 0 → level 0``; ``Σ ≥ denom → level 1``; else the reduced
#: ``Σ/denom`` in ``(0, 1)``). The fraction is reduced by the **Class-I gcd**. ``denom`` is the
#: full-expression normalizer (the dose at which the gene is fully ON). A graded gene is
#: "expressed" iff its LEVEL ``> 0`` (the dose-response IS the gate — dose 0 = off), so it also
#: participates in the BINARY :func:`gene_express` (present iff level > 0). :func:`gene_express_levels`
#: is the op that returns the exact-rational LEVEL per expressed gene.
#:
#: Layout (a fixed-width ``leaf_dim``-byte ``sectors=256`` cap leaf; §44 inline; the gate_type +
#: n_weights + denom + weights carried after the label NUL — the SAME uniform label decode as
#: every cap):
#:   byte ``[0]``           marker ``0x64``
#:   bytes ``[1:1+L]``      utf-8 gene label ``L`` bytes
#:   byte ``[1+L]``         the label terminator ``0x00``
#:   byte ``[2+L]``         gate_type — uint8 (:data:`GATE_TYPE_GRADED` = 3)
#:   bytes ``[3+L:5+L]``    n_weights — uint16 BIG-ENDIAN (the level-weight-vector length)
#:   bytes ``[5+L:13+L]``   denom — **uint64 BIG-ENDIAN (POSITIVE, ≥ 1; the full-ON dose)**
#:   then n_weights weights, each ``_GRADED_GENE_WEIGHT_BYTES`` (8) bytes:
#:     level_weight (int64 BE, SIGNED two's-complement)
#:   bytes ``[…]``          NUL padding to ``leaf_dim``
#: ``> 3`` and distinct from every other marker (CHROM ``0x43`` / GENE ``0x47`` / v5 KERNEL
#: ``0x4B`` / PACKED ``0x51`` / KERNEL-telomere ``0x6B`` / ACTIVE-telomere ``0x74`` /
#: REGULATORY-gene ``0x67`` / BOOLEAN-gene ``0x62`` / THRESHOLD-gene ``0x77``), so the strand
#: stays SELF-DESCRIBING (§44): v2..v10 bodies read UNCHANGED (dual-read — the walker gains ONE
#: branch), and a chromosome self-describes its level-weights + denom by bare-strand scan (no
#: manifest). A NEW block KIND (a new marker byte), so it bumps the genome format v10 → v11 — the
#: same version-stamp discipline every prior new-marker bump used (rc127 ``0x74`` v6→v7, rc128
#: ``0x67`` v7→v8, rc130 ``0x62`` v8→v9, rc131 ``0x77`` v9→v10); the strand-walk read path is
#: version-INDEPENDENT, so every pre-rc132 genome still reads identically.
GRADED_GENE_MARKER = 0x64

#: The regulatory-gene MASK field width — a uint64 (8 bytes, big-endian), read at the byte
#: right after the inline label's NUL terminator (the SAME field shape as the §127 active
#: telomere's count). 64 exact bitwise cell-state conditions; Class-I integer, no float.
#: §129/rc129 (#729) — a regulatory gene carries TWO consecutive uint64 mask fields
#: (activator then repressor); rc128's SINGLE-mask cap is dual-read as ``activator=mask,
#: repressor=0`` (see :data:`_REGULATORY_GENE_ROLES` below).
_REGULATORY_GENE_MASK_BYTES = 8

#: §129/rc129 (#729) — KLEIN-4 REGULATORY ROLES: each regulatory CONDITION (bit position)
#: carries one of FOUR roles, the genome's NATIVE Klein-4 alphabet (element_type ``0 =
#: klein4``, the 2-bit ``{0,1,2,3}`` symbol). A condition's role is a **Klein-4 sector**: the
#: per-condition pair ``(act_bit, rep_bit)`` IS the 2-bit Klein-4 symbol (the two bit-planes
#: are the two ``Z2`` factors of ``V = Z2 × Z2``)::
#:
#:   (act_bit, rep_bit)  Klein-4 symbol   role          expression constraint on this bit
#:   ------------------  --------------   -----------   ------------------------------------
#:        (0, 0)              0            don't-care    (no constraint)
#:        (1, 0)              2            activator     the bit MUST be present in cell_state
#:        (0, 1)              1            repressor     the bit MUST be absent from cell_state
#:        (1, 1)              3            never         present AND absent → contradiction →
#:                                                       the gene NEVER expresses (auto-silenced)
#:
#: ENCODING = TWO PARALLEL bitmasks ``(activator_mask, repressor_mask)`` — the two Klein-4
#: bit-planes over the 64 conditions. rc128 shipped only the activator plane (a pure
#: conjunctive AND-gate = all-ACTIVATOR); biology (the lac operon, Jacob & Monod 1961) also
#: has REPRESSORS (require-absent), the second plane. The expression rule is exact Class-I
#: bitwise (:func:`_gene_expresses`): a gene expresses iff ``(cell_state & activator_mask) ==
#: activator_mask`` (all activators present) AND ``(cell_state & repressor_mask) == 0`` (no
#: repressor present). A 'never' bit (set in BOTH masks) auto-silences: ``(cs & act) == act``
#: needs it set while ``(cs & rep) == 0`` needs it clear → contradiction → never expresses.
#: NO float, NEVER ``abs()`` (a mask is never negated).
#:
#: LAYOUT / DUAL-READ: the repressor mask occupies the 8 bytes that were NUL PADDING in a
#: rc128 single-mask cap — so the second Klein-4 bit-plane was latent in the padding all
#: along. The writer emits the 8-byte (activator-only) form when ``repressor == 0`` (the
#: repressor 0 IS the padding), making an activator-only rc129 gene BYTE-IDENTICAL to a rc128
#: gene; it emits the 16-byte (activator+repressor) form only when ``repressor != 0``. The
#: reader reads the activator (8 bytes after the NUL, always present) and the repressor (the
#: NEXT 8 bytes if the leaf has room, else 0) — so a rc128 single-mask cap and a plain gene
#: read as ``repressor = 0`` (unregulated by repression). SAME marker ``0x67`` (an ADDITIVE
#: extension of an existing block kind — NOT a new marker, so no genome-format bump).
_REGULATORY_GENE_ROLES = ("dont-care", "repressor", "activator", "never")

#: §130/rc130 (#730) — the REGULATORY GATE-TYPE dispatch family. A regulatory gene declares a
#: ``gate_type``, and :func:`gene_express` dispatches on it. Two gate-types today:
#:   * :data:`GATE_TYPE_KLEIN4_MASK` (``0``) — the rc129 E1 activator/repressor two-mask (the
#:     DEFAULT / FAST common case): a gene expresses iff ``(cs & act) == act`` AND
#:     ``(cs & rep) == 0``. Carried in a plain GENE cap (``0x47``, masks 0 = always) or a
#:     Klein-4-mask regulatory gene cap (``0x67``). UNCHANGED — stays the compact fast path.
#:   * :data:`GATE_TYPE_BOOLEAN_DNF` (``1``) — the rc130 E2 arbitrary boolean logic (the GENERAL
#:     escape hatch): a DNF (OR-of-AND-clauses) over the condition bits, carried in a BOOLEAN
#:     GENE cap (``0x62``). Each DNF term is an E1-style ``(act, rep)`` clause, so E1's two-mask
#:     is exactly a 1-TERM DNF (E1 ⊂ E2). Represents any boolean function (AND / OR / NOT / XOR).
#: The gate_type is IMPLIED by the cap marker (``0x47``/``0x67`` → klein4_mask; ``0x62`` →
#: boolean_dnf) AND — for a ``0x62`` gene — stored EXPLICITLY as a byte in the cap, so the bare
#: strand self-describes the gate_type and the family stays extensible (a future truth-table
#: encoding slots in as ``0x62`` + a new gate_type value, no new marker).
#:   * :data:`GATE_TYPE_THRESHOLD` (``2``) — the rc131 E4 LINEAR-THRESHOLD gate (a perceptron):
#:     a per-condition INTEGER weight vector + an INTEGER threshold, carried in a THRESHOLD GENE
#:     cap (``0x77``). A gene expresses iff ``Σᵢ (weightᵢ · bit_i(cell_state)) ≥ threshold``.
#:     SIGNED weights (inhibitory inputs) are allowed; the decision is the SIGN of ``(Σ −
#:     threshold)`` (Class-K, never ``abs()``). GENUINELY DISTINCT from E2 (linear-threshold ⊄
#:     small-DNF: MAJORITY-of-n needs an exponential DNF but a compact all-ones threshold gate).
#:   * :data:`GATE_TYPE_GRADED` (``3``) — the rc132 E3 GRADED / ANALOG LEVEL (a dose-response),
#:     carried in a GRADED GENE cap (``0x64``). This is NOT a binary gate-type in the E1/E2/E4
#:     "IF it expresses" family — it is the ORTHOGONAL "HOW MUCH" axis: a per-condition SIGNED
#:     integer level-weight vector + a positive integer denominator whose LEVEL is the reduced
#:     exact rational ``Σᵢ level_weightᵢ·bit_i(cell_state) / denom`` clamped to ``[0, 1]``. The
#:     gate_type byte is carried in the cap for self-description / family-extensibility, exactly
#:     like the boolean / threshold genes.
GATE_TYPE_KLEIN4_MASK = 0
GATE_TYPE_BOOLEAN_DNF = 1
GATE_TYPE_THRESHOLD = 2
GATE_TYPE_GRADED = 3
_GATE_TYPE_NAMES = {GATE_TYPE_KLEIN4_MASK: "klein4_mask", GATE_TYPE_BOOLEAN_DNF: "boolean_dnf",
                    GATE_TYPE_THRESHOLD: "threshold", GATE_TYPE_GRADED: "graded"}

#: §130/rc130 (#730) — the BOOLEAN GENE DNF wire widths. The DNF term COUNT is a uint16
#: big-endian (2 bytes; up to 65535 terms — a leaf_dim-bounded ceiling, plenty for the
#: combinatorial cis-regulatory logic this models). Each DNF TERM is TWO consecutive uint64
#: big-endian masks — the ``(activator, repressor)`` AND-clause (16 bytes), the SAME
#: ``(require-present, require-absent)`` pair the rc129 klein4_mask carries as its ONE clause.
#: Class-I exact integers (no float, never ``abs()``).
_BOOLEAN_GENE_NTERMS_BYTES = 2
_BOOLEAN_GENE_TERM_BYTES = 2 * _REGULATORY_GENE_MASK_BYTES

#: §131/rc131 (#731) — the THRESHOLD GENE wire widths. The weight-vector LENGTH is a uint16
#: big-endian (2 bytes; up to 65535 weights — a leaf_dim-bounded ceiling; a weight at index i
#: gates condition bit i of the cell_state). The THRESHOLD and each WEIGHT are **int64 big-endian
#: SIGNED two's-complement** (8 bytes each; signed so an inhibitory / repressive input is a
#: NEGATIVE weight — real biology). Class-I/N exact signed integers (no float; the SIGN is a
#: Class-K pin-slot, never ``abs()``).
_THRESHOLD_GENE_NWEIGHTS_BYTES = 2
_THRESHOLD_GENE_THRESHOLD_BYTES = 8
_THRESHOLD_GENE_WEIGHT_BYTES = 8
#: The int64 two's-complement bound: a signed weight / threshold lives in [-2**63, 2**63).
_THRESHOLD_I64_MIN = -(1 << 63)
_THRESHOLD_I64_MAX = (1 << 63) - 1

#: §132/rc132 (#732) — the GRADED (dose-response) GENE wire widths. The level-weight-vector LENGTH
#: is a uint16 big-endian (2 bytes; a weight at index i doses condition bit i of the cell_state).
#: The DENOMINATOR is a uint64 big-endian POSITIVE integer (8 bytes; the full-expression dose — a
#: divisor is never negative, so it is UNSIGNED and validated ``≥ 1``, never ``abs()``). Each
#: LEVEL-WEIGHT is an int64 big-endian SIGNED two's-complement (8 bytes; SIGNED so an inhibitory
#: input REDUCES the dose — real biology). Class-N exact rational level; the SIGN of the raw dose
#: is a Class-K pin-slot, never ``abs()``; the fraction is reduced by the Class-I gcd.
_GRADED_GENE_NWEIGHTS_BYTES = 2
_GRADED_GENE_DENOM_BYTES = 8
_GRADED_GENE_WEIGHT_BYTES = 8
#: The uint64 denominator bound: a positive divisor lives in [1, 2**64).
_GRADED_U64_MAX = (1 << 64) - 1

#: The two :func:`telomere_tick` verdicts (the honest-decline / inform-don't-crash
#: pattern — a clean STATUS, never a crash). ``DIVIDED`` = the count was > 0, so the op
#: proceeded (decremented the count, returned the daughter strand); ``SENESCENT`` = the
#: count was 0, so the op REFUSED (Hayflick senescence — no daughter). Same op call,
#: operator behaviour selected by the operand: THE op⊗operand duality made testable.
TELOMERE_DIVIDED = "divided"
TELOMERE_SENESCENT = "senescent"

#: §101 (rc275) — the progress/abort status a dict-returning encode op reports.
#: ``"ok"`` = ran to completion; ``"cancelled"`` = a ``progress`` tick returned
#: truthy → a CLEAN partial + honest-decline (mirror telomere_tick one scale up).
GENOME_STATUS_OK = "ok"
GENOME_STATUS_CANCELLED = "cancelled"

#: §101 progress-event mirrors — shared by the pure + native (trampoline) tick
#: paths so the emitted dict is byte-identical across them (the parity contract).
_PROGRESS_STRUCT_SIZE = _native.PROGRESS_STRUCT_SIZE
_PHASE_MINTING = _native.SRMECH_PHASE_MINTING

#: Declared ``element_type`` enum for the §60 kernel header. ``0 = klein4`` (the
#: genome-native 2-bit ``{0,1,2,3}`` symbol — siona's 8192-dim Klein-4 kernel). New
#: element types slot in as fresh codes WITHOUT another format bump (that IS the
#: size-agnostic discipline — the header carries the type, so the reader never
#: assumes one). A header-less body defaults to :data:`ELEMENT_TYPE_KLEIN4`.
ELEMENT_TYPE_KLEIN4 = 0
_ELEMENT_TYPE_NAMES = {ELEMENT_TYPE_KLEIN4: "klein4"}
_ELEMENT_TYPE_CODES = {name: code for code, name in _ELEMENT_TYPE_NAMES.items()}

#: §60 kernel-header fixed prefix layout (bytes; NUL-padded to ``leaf_dim``):
#:   ``[0]``      marker ``0x4B``
#:   ``[1:9]``    true length ``D``  — uint64 BIG-ENDIAN (8 bytes; caps at 2**64-1,
#:                which dwarfs any MB-scale kernel: 8192 needs 2 bytes, an F1035
#:                ~1.37e7-symbol 3.43 MB kernel needs 4, 2**64-1 needs all 8)
#:   ``[9:13]``   ``leaf_dim``       — uint32 BIG-ENDIAN (4 bytes; the block width)
#:   ``[13]``     ``element_type``   — uint8 enum (:data:`ELEMENT_TYPE_KLEIN4` = 0)
#: The prefix is 14 bytes, so ``leaf_dim`` must be ``>= 14`` (the default 256 and
#: every DoD width satisfy it). Fixed-width + big-endian so the C mirror parses it
#: with the same byte reads. **§89/rc126: v5 byte-TLV — READ-ONLY back-compat.**
_KERNEL_HEADER_PREFIX = 14

#: §89/rc126 (format v6) — the UNIFORMLY-KLEIN-4 kernel header leaf layout, in
#: base-4 Klein-4 symbols ``{0,1,2,3}`` (2 bits/symbol, big-endian / MSB-symbol
#: first). It carries the SAME three fields the v5 byte-TLV did, base-4-encoded:
#:   symbols ``[0:32]``   true length ``D``   — uint64 (32 symbols)
#:   symbols ``[32:48]``  ``leaf_dim``        — uint32 (16 symbols)
#:   symbols ``[48:52]``  ``element_type``    — uint8  (4 symbols)
#:   symbols ``[52:leaf_dim]``                — Klein-4 zero padding
#: Total 52 significant symbols, so a v6 header needs ``leaf_dim >= 52`` (the default
#: 256 and every DoD width satisfy it). The leaf is 100 % Klein-4, so it couples
#: through ``coupling`` like any content leaf and bit-packs like any data turn on disk
#: (the store is uniformly Klein-4 — no byte-TLV residue). Same field widths as v5 so
#: the header carries identical information; the C mirror reads the same base-4 lanes.
_KH4_D_SYMS = 32          # uint64 D  → 32 base-4 symbols
_KH4_LEAFDIM_SYMS = 16    # uint32 leaf_dim → 16 base-4 symbols
_KH4_ETYPE_SYMS = 4       # uint8 element_type → 4 base-4 symbols
_KERNEL_HEADER_KLEIN4_SYMS = _KH4_D_SYMS + _KH4_LEAFDIM_SYMS + _KH4_ETYPE_SYMS  # 52

#: One dense block — a "tome". 256 = 2**8 (one byte of address); F708/F640.
LEAF_CAP = 256
#: The Klein-4 order (Z2 x Z2) — the biaxial "+" / the 4 chirality sectors (F130/F233).
QUAD = 4
#: One quad-turn spans the 4 Klein-4 sectors of leaves: 1024 = 4 x 256 (F713).
MOBIUS_CAP = LEAF_CAP * QUAD


def _ceil_log4(m: int) -> int:
    """Smallest ``d >= 0`` with ``QUAD**d >= m`` — pure-integer ``ceil(log4(m))``.

    No float ``log`` (Class-I/N discipline; "floats are for the FPU lift", and the
    A-N cascade ratchet keeps continuous math out of the integer decision path)."""
    d, power = 0, 1
    while power < m:
        power *= QUAD
        d += 1
    return d


def encode_shape(n: int) -> Dict[str, object]:
    """The genome encode **criterion** (F715): how to encode a kernel of size ``n``.

    +-------------+-----------------+--------------------------------------------+
    | ``n``       | ``shape``       | structure                                  |
    +=============+=================+============================================+
    | ``<= 256``  | ``tome``        | one dense block (a single leaf)            |
    | ``<= 1024`` | ``mobius``      | one quad-turn — the 4 Klein-4 sectors      |
    | ``> 1024``  | ``quad_strand`` | a helix of quad-turns (a chromosome)       |
    +-------------+-----------------+--------------------------------------------+

    ``depth = ceil(log4(ceil(n / 256)))`` is the number of base-4 quad levels
    spanning the ``leaves = ceil(n / 256)`` dense blocks (``0`` -> tome, ``1`` ->
    mobius, ``>= 2`` -> quad_strand). Thresholds are attested to ``256 = 2**8`` and
    the Klein-4 order ``4`` — no magic (F708/F640/F715). Verified against F715:
    ``200 -> tome``, ``800 -> mobius``, ``5000 -> quad_strand depth 3``,
    ``1_770_000 -> quad_strand depth 7``.

    Returns ``{"n", "shape", "leaves", "depth", "leaf_cap"}``.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError(f"encode_shape: n must be a positive int; got {n!r}")
    # rc196 (#887): DISPATCH the pure-integer arithmetic to the srmech_genome_
    # encode_shape C peer when HAS_NATIVE (byte-identical (leaves, depth); the
    # pure ceil-div + ceil_log4 below is the numpy-free fallback + parity oracle,
    # and also handles n >= 2**64 which the uint64 C path routes back here).
    native = _native.genome_encode_shape_c(n)
    if native is not None:
        leaves, depth = native
    else:
        leaves = (n + LEAF_CAP - 1) // LEAF_CAP      # ceil(n / 256), pure integer
        depth = _ceil_log4(leaves)
    shape = "tome" if depth == 0 else "mobius" if depth == 1 else "quad_strand"
    return {"n": n, "shape": shape, "leaves": leaves, "depth": depth, "leaf_cap": LEAF_CAP}


def quad_turn(turn, coupling):
    """Couple one helix turn through ``coupling`` — the genome's turn operation (F713).

    The turn is bound to ``coupling`` (the held invariant) by the **reversible**
    Klein-4 bind (``V4 = (F2)^2`` XOR, so ``quad_turn(quad_turn(t, one), one) ==
    t``): the duality held WITHOUT collapse, numpy-free. ``coupling`` is the shared
    invariant present in every turn's coupling — so a chromosome navigates across
    its turns through ``coupling`` and recovers any turn by re-binding it.

    ``turn`` and ``coupling`` are Klein-4 vectors (e.g. from
    :func:`srmech.amsc.hdc.klein4_from_one`); returns the coupled turn (a Klein-4
    ``HV``). Class-M (bind) ∘ Class-C (the chirality the Klein-4 sectors carry).

    Each turn sits in the native 4-sector biaxial "+"
    (:func:`srmech.amsc.cascade.parallel_sector_dispatch`, CAP=4); that dispatch
    and the base-4 leaf addressing assemble at the chromosome level. Per the F712
    caveat the 4-way is ONE chirality level, the deeper tree is radix addressing.
    """
    return _klein4_bind(turn, coupling)


def _pack_cap(marker, label, dim):
    """A fixed-width ``dim``-byte cap leaf: ``[marker] + utf-8 label, NUL-padded``
    (§44). ``marker`` (``> 3``) classifies it (CHROM / GENE) and distinguishes it
    from any Klein-4 data turn (bytes ``0..3``); the label is recoverable inline by
    reading bytes ``[1:]`` up to the first NUL. Same width as a data turn (one
    ``leaf_dim``-byte block) so the strand stays uniformly fixed-width. The label
    must fit ``dim - 1`` bytes (~63 at ``leaf_dim = 64``)."""
    raw = label.encode("utf-8") if isinstance(label, str) else bytes(label)
    if len(raw) > dim - 1:
        raise ValueError(
            f"cap label {label!r} is {len(raw)} bytes; max {dim - 1} at leaf_dim={dim} "
            f"(a label must fit one fixed-width cap leaf — §44 inline encoding)"
        )
    block = bytes([marker]) + raw + b"\x00" * (dim - 1 - len(raw))
    return _HV.from_sequence(block, sectors=256)


def _cap_kind(hv):
    """The marker byte (``CHROM_CAP_MARKER`` / ``GENE_CAP_MARKER`` /
    ``KERNEL_HEADER_MARKER`` / ``KERNEL_TELOMERE_MARKER``) of a non-data strand
    element, or ``None`` for a Klein-4 data turn (first byte ``0..3``) — the §44 scan
    classifier. §60/v5: the byte-TLV kernel header ``0x4B`` joins the caps as a
    scanned-for, skipped-on-recall marker block. §89/v6: the kernel telomere ``0x6B``
    is the KERNEL-chromosome boundary cap (like the CHROM cap, but flags the
    chromosome as a kernel — the leaf after it is the Klein-4 header turn). §127/v7: the
    active telomere ``0x74`` is a chromosome boundary cap carrying an inline count."""
    first = int(hv[0]) if len(hv) else -1
    return first if first in (
        CHROM_CAP_MARKER, GENE_CAP_MARKER, REGULATORY_GENE_MARKER,
        BOOLEAN_GENE_MARKER, THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER,
        KERNEL_HEADER_MARKER,
        KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER,
        CENTROMERE_CAP_MARKER, DIPLOID_TELOMERE_MARKER,
        CHROMATIN_MARKER) else None   # §95a/§95b/§98 caps


def _unpack_cap(hv):
    """``(marker, label)`` from a fixed-width cap leaf — the inverse of
    :func:`_pack_cap`; the label is bytes ``[1:]`` up to the first NUL."""
    raw = hv.tobytes()
    return raw[0], raw[1:].split(b"\x00", 1)[0].decode("utf-8")


def _pack_kernel_header(true_len, leaf_dim, element_type, dim):
    """A fixed-width ``dim``-byte §60 kernel-header block — the inverse of
    :func:`_unpack_kernel_header`. Records the kernel's TRUE length ``true_len``,
    its ``leaf_dim``, and its ``element_type`` (see the header layout note near
    :data:`KERNEL_HEADER_MARKER`), NUL-padded to ``dim`` (== ``leaf_dim``, the
    block width) so the strand stays uniformly fixed-width. ``dim`` must fit the
    14-byte prefix. ``true_len`` is an unsigned 64-bit value."""
    if dim < _KERNEL_HEADER_PREFIX:
        raise ValueError(
            f"kernel header needs leaf_dim >= {_KERNEL_HEADER_PREFIX}; got {dim} "
            f"(the true-length + leaf_dim + element_type prefix does not fit)"
        )
    if true_len < 0 or true_len >= (1 << 64):
        raise ValueError(
            f"kernel header true_len {true_len} out of the uint64 range [0, 2**64)"
        )
    block = bytearray(dim)
    block[0] = KERNEL_HEADER_MARKER
    block[1:9] = int(true_len).to_bytes(8, "big")     # D — uint64 big-endian
    block[9:13] = int(leaf_dim).to_bytes(4, "big")    # leaf_dim — uint32 big-endian
    block[13] = int(element_type) & 0xFF              # element_type — uint8 enum
    return _HV.from_sequence(bytes(block), sectors=256)


def _unpack_kernel_header(hv):
    """``(true_len, leaf_dim, element_type)`` from a §60 kernel-header block — the
    inverse of :func:`_pack_kernel_header`. Reads the fixed-width big-endian fields
    (the NUL padding after byte 13 is ignored). **§89/rc126: v5 — READ-ONLY.**"""
    raw = hv.tobytes()
    true_len = int.from_bytes(raw[1:9], "big")
    leaf_dim = int.from_bytes(raw[9:13], "big")
    element_type = raw[13]
    return true_len, leaf_dim, element_type


def _uint_to_base4(value, n_syms):
    """A non-negative ``value`` → ``n_syms`` Klein-4 symbols ``{0,1,2,3}``,
    big-endian (MSB-symbol first) — the §89 base-4 encoder (2 bits/symbol, no float,
    Class-I discipline). Raises ``ValueError`` if ``value`` does not fit ``n_syms``
    base-4 places."""
    v = int(value)
    if v < 0 or v >= (1 << (2 * n_syms)):
        raise ValueError(
            f"_uint_to_base4: {value} does not fit {n_syms} base-4 symbols "
            f"(range [0, 4**{n_syms}))"
        )
    syms = [0] * n_syms
    for i in range(n_syms - 1, -1, -1):
        syms[i] = v & 3
        v >>= 2
    return syms


def _base4_to_uint(syms):
    """``syms`` (Klein-4 ``{0,1,2,3}``, big-endian) → the non-negative int — the exact
    inverse of :func:`_uint_to_base4`."""
    v = 0
    for s in syms:
        v = (v << 2) | (int(s) & 3)
    return v


def _pack_kernel_header_klein4(true_len, leaf_dim, element_type, dim):
    """A fixed-width ``dim``-symbol §89/v6 UNIFORMLY-KLEIN-4 kernel-header LEAF — the
    inverse of :func:`_unpack_kernel_header_klein4`. Base-4-encodes the kernel's TRUE
    length ``true_len`` (uint64 → 32 symbols), its ``leaf_dim`` (uint32 → 16) and its
    ``element_type`` (uint8 → 4), Klein-4-zero-padded to ``dim`` (== ``leaf_dim``, the
    block width). EVERY symbol is a Klein-4 sector ``{0,1,2,3}`` — so this leaf
    couples through ``coupling`` and bit-packs like any content turn (the store stays
    uniformly Klein-4). ``dim`` must fit the 52-symbol header."""
    if dim < _KERNEL_HEADER_KLEIN4_SYMS:
        raise ValueError(
            f"§89 kernel header needs leaf_dim >= {_KERNEL_HEADER_KLEIN4_SYMS}; got "
            f"{dim} (the base-4 D + leaf_dim + element_type fields do not fit one leaf)"
        )
    syms = (_uint_to_base4(true_len, _KH4_D_SYMS)
            + _uint_to_base4(leaf_dim, _KH4_LEAFDIM_SYMS)
            + _uint_to_base4(element_type, _KH4_ETYPE_SYMS))
    syms = syms + [0] * (dim - len(syms))          # Klein-4 zero padding
    return _HV.from_sequence(syms, sectors=QUAD)


def _unpack_kernel_header_klein4(hv):
    """``(true_len, leaf_dim, element_type)`` from a §89/v6 Klein-4 kernel-header leaf
    — the inverse of :func:`_pack_kernel_header_klein4`. Reads the fixed-width base-4
    fields (the Klein-4 zero padding after symbol 52 is ignored)."""
    syms = [int(x) for x in hv]
    true_len = _base4_to_uint(syms[0:_KH4_D_SYMS])
    off = _KH4_D_SYMS
    leaf_dim = _base4_to_uint(syms[off:off + _KH4_LEAFDIM_SYMS])
    off += _KH4_LEAFDIM_SYMS
    element_type = _base4_to_uint(syms[off:off + _KH4_ETYPE_SYMS])
    return true_len, leaf_dim, element_type


def telomere(label, dim=64):
    """The chromosome boundary cap — a fixed-width INLINE CHROM cap (F715 / §44).

    A telomere is biology's repetitive non-coding chromosome-end cap. Here (§44) it
    is a fixed-width ``dim``-byte leaf ``[CHROM_CAP_MARKER] + label, NUL-padded`` —
    **scannable** (first byte ``> 3``, so it is found by walking the strand, never
    mistaken for a Klein-4 data turn) and **label-recoverable inline** (the strand
    self-describes; chromosome labels recover by scan, no manifest). Same ``label``
    -> same cap; distinct labels -> distinct caps. ``dim`` is the leaf width — match
    the turns it caps (:func:`chromosome` passes ``len(coupling)`` automatically).

    §44 REPLACES the pre-§43.1 content-address cap (``klein4_expand`` of a label
    hash — bytes ``0..3``, NOT scan-recognisable without already knowing the label,
    which forced a label↔cap sidecar). Integrity (the old cap's one-way hash) moves
    to the optional derived manifest, not the body.
    """
    # rc196 (#887): DISPATCH the cap byte-framing to the srmech_genome_telomere C
    # peer when HAS_NATIVE (byte-identical bytes, then wrapped in the same
    # HV(sectors=256)); the pure _pack_cap below is the numpy-free fallback +
    # parity oracle, and raises the ValueError for an over-long label (the native
    # wrapper returns None in that case so the exact error surfaces here).
    native = _native.genome_telomere_c(label, dim)
    if native is not None:
        return _HV.from_sequence(native, sectors=256)
    return _pack_cap(CHROM_CAP_MARKER, label, dim)


def _kernel_telomere(label, dim=64):
    """The KERNEL-chromosome boundary cap (§89/rc126) — a fixed-width INLINE cap leaf
    ``[KERNEL_TELOMERE_MARKER] + label, NUL-padded`` (the §44 telomere, kernel
    variant). Identical to :func:`telomere` but its ``0x6B`` marker FLAGS the
    chromosome as a kernel: the leaf immediately after it is the uniformly-Klein-4
    §89 header (:func:`_pack_kernel_header_klein4`), so a reader recovers the true
    ``D`` / ``element_type`` / ``leaf_dim`` by scanning for ``0x6B`` and reading the
    next turn (the collision-FREE option-(a) distinguisher — a framing marker, not
    in-band magic). Written by :func:`kernel_pack` / :func:`genome_append_kernel`
    (an internal cap helper — the public kernel surface is kernel_pack /
    genome_append_kernel / kernel_unpack)."""
    return _pack_cap(KERNEL_TELOMERE_MARKER, label, dim)


def _gene_cap(gene_label, dim):
    """The intra-chromosome GENE boundary cap — a fixed-width INLINE leaf (§44,
    replaces the §43 TLV ``_gene_header``). ``[GENE_CAP_MARKER] + label, NUL-padded``
    to ``dim``: scanned for (first byte ``> 3``, distinct from the CHROM cap marker
    and from data turns), label recoverable inline. Telomere caps the chromosome,
    the gene-cap caps the gene — nested fixed-width inline framing, no length prefix
    (so no offset sidecar; biology's own wire-format)."""
    return _pack_cap(GENE_CAP_MARKER, gene_label, dim)


def _pack_gene_cap_copy_number(gene_label, copy_number, dim):
    """A plain GENE cap (``0x47``) carrying an exact COPY-NUMBER (§135/rc273 / F1251) — the
    inverse of :func:`_gene_copy_number`.

    ``[GENE_CAP_MARKER] + utf-8 label + NUL + copy_number(uint64 big-endian)``, NUL-padded to
    ``dim`` — the SAME placement discipline as the active-telomere count / the §129 regulatory
    masks (the field sits RIGHT AFTER the label's NUL terminator, so :func:`_unpack_cap` reads
    the label UNIFORMLY with no copy-number special-case). ``copy_number`` is the MULTIPLICITY
    (how many copies IS26-mediated amplification produced), a Class-I/N exact integer >= 1 (no
    float, never ``abs()``).

    DUAL-READ / BYTE-COMPAT (mirrors §129): ``copy_number == 1`` is the DEFAULT (present-once),
    encoded as the ABSENT field — the writer emits the plain :func:`_gene_cap` form (all-NUL
    padding == stored 0 == copy-number 1), so an ``n == 1`` amplify is BYTE-IDENTICAL to a plain
    gene and no wire change is spent. Only ``n >= 2`` writes the 8-byte field. So a plain gene
    (:func:`_gene_cap`) and a pre-rc273 genome both read as copy-number 1 (back-compat), and the
    on-disk format version STAYS 15 (an additive field in existing NUL padding, not a new
    marker / block kind)."""
    if not isinstance(copy_number, int) or isinstance(copy_number, bool):
        raise ValueError(
            f"gene copy_number must be an exact int (Class-I/N multiplicity); got {copy_number!r}")
    if copy_number < 1:
        raise ValueError(
            f"gene copy_number must be >= 1 (a gene is present at least once; a multiplicity is "
            f"never signed / never abs()); got {copy_number}")
    if copy_number >= (1 << (8 * _GENE_COPY_NUMBER_BYTES)):
        raise ValueError(
            f"gene copy_number {copy_number} exceeds the uint64 field "
            f"[1, 2**{8 * _GENE_COPY_NUMBER_BYTES})")
    if copy_number == 1:
        return _gene_cap(gene_label, dim)              # DEFAULT — byte-identical to a plain gene
    raw_label = gene_label.encode("utf-8") if isinstance(gene_label, str) else bytes(gene_label)
    if b"\x00" in raw_label:
        raise ValueError("gene label must not contain a NUL byte")
    payload = (bytes([GENE_CAP_MARKER]) + raw_label + b"\x00"
               + int(copy_number).to_bytes(_GENE_COPY_NUMBER_BYTES, "big"))
    if len(payload) > dim:
        raise ValueError(
            f"gene cap {gene_label!r} + copy-number field is {len(payload)} bytes; max {dim} at "
            f"leaf_dim={dim} (a copy-number gene label must fit dim - "
            f"{2 + _GENE_COPY_NUMBER_BYTES} bytes)")
    block = payload + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _gene_copy_number(hv):
    """The exact COPY-NUMBER (multiplicity) carried inline in a plain GENE cap (``0x47``,
    §135/rc273 / F1251) — the inverse of :func:`_pack_gene_cap_copy_number`.

    Reads the ``_GENE_COPY_NUMBER_BYTES`` bytes RIGHT AFTER the label's NUL terminator (uint64
    big-endian). A stored ``0`` — the all-NUL padding a pre-rc273 / plain gene carries, or a
    field that does not fit the leaf — reads as copy-number ``1`` (present-once, the DEFAULT), so
    a plain gene and a back-compat genome both surface 1. Only defined for a plain GENE cap
    (``0x47``); a non-gene / regulatory-gene / non-plain cap returns ``1`` (no copy-number axis).
    Class-I/N exact integer (no float, never ``abs()``)."""
    raw = hv.tobytes()
    if raw[:1] != bytes([GENE_CAP_MARKER]):
        return 1                                       # not a plain gene — no copy-number axis
    nul = raw.find(b"\x00", 1)                          # end of the inline label
    if nul < 0 or nul + 1 + _GENE_COPY_NUMBER_BYTES > len(raw):
        return 1                                        # no field room / no NUL → default 1
    stored = int.from_bytes(raw[nul + 1:nul + 1 + _GENE_COPY_NUMBER_BYTES], "big")
    return stored if stored >= 1 else 1                 # stored 0 (plain / back-compat) → 1


def _validate_regulatory_mask(mask, which):
    """Validate one Class-I regulatory mask (activator or repressor) — a non-negative exact
    int that fits the uint64 field. NO float; NEVER ``abs()`` (a mask is never negated)."""
    if not isinstance(mask, int) or isinstance(mask, bool):
        raise ValueError(
            f"regulatory gene {which} mask must be an exact int (Class-I bitwise); got {mask!r}")
    if mask < 0:
        raise ValueError(
            f"regulatory gene {which} mask must be non-negative (a bitmask is never signed; a "
            f"mask is never negated, so never abs()); got {mask}")
    if mask >= (1 << (8 * _REGULATORY_GENE_MASK_BYTES)):
        raise ValueError(
            f"regulatory gene {which} mask {mask} exceeds the uint64 field "
            f"[0, 2**{8 * _REGULATORY_GENE_MASK_BYTES})")


def _pack_regulatory_gene(gene_label, activator, dim, repressor=0):
    """A fixed-width ``dim``-byte REGULATORY GENE cap leaf (§128/§129) — the op⊗operand gene.

    ``[REGULATORY_GENE_MARKER] + utf-8 label + NUL + activator(uint64 BE) [+ repressor(uint64
    BE)]``, NUL-padded to ``dim``. The **op** (a gene: it opens + delimits a gene inside a
    chromosome, like :func:`_gene_cap`) and the **operand** (the regulatory region: which
    cell-state conditions enable the gene, per-condition a KLEIN-4 role — see
    :data:`_REGULATORY_GENE_ROLES`) are FUSED in the ONE cap. Placing the masks right AFTER
    the label's NUL terminator keeps the label decode UNIFORM (bytes ``[1:]`` up to the first
    NUL — :func:`_unpack_cap` reads it with no regulatory-gene special-case).

    §129/rc129 (#729) TWO PARALLEL masks — the two Klein-4 bit-planes: ``activator`` (require
    each set bit PRESENT) + ``repressor`` (require each set bit ABSENT). Both are non-negative
    exact integers (Class-I bitwise; NO float; NEVER ``abs()``). DUAL-READ / BYTE-COMPAT: the
    repressor lives in what was NUL padding, so when ``repressor == 0`` the writer emits the
    rc128 8-byte (activator-only) form (the 0 repressor IS the padding) — an activator-only
    rc129 gene is BYTE-IDENTICAL to a rc128 single-mask gene; only ``repressor != 0`` spends
    the extra 8-byte field. A plain gene (:func:`_gene_cap`, no masks) is the
    ``activator==0, repressor==0`` always-express case, so a regulatory gene is a strict,
    additive extension. Same marker ``0x67`` (an additive extension of an existing block kind,
    NOT a new marker)."""
    _validate_regulatory_mask(activator, "activator")
    _validate_regulatory_mask(repressor, "repressor")
    raw_label = gene_label.encode("utf-8") if isinstance(gene_label, str) else bytes(gene_label)
    if b"\x00" in raw_label:
        raise ValueError("regulatory gene label must not contain a NUL byte")
    payload = (bytes([REGULATORY_GENE_MARKER]) + raw_label + b"\x00"
               + int(activator).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big"))
    # §129 DUAL-READ: repressor 0 == the NUL padding, so emit the rc128 8-byte form for an
    # activator-only gene (byte-identical); spend the second 8-byte field only when needed.
    if repressor != 0:
        payload = payload + int(repressor).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big")
    if len(payload) > dim:
        fields = 2 if repressor != 0 else 1
        raise ValueError(
            f"regulatory gene label {gene_label!r} + {fields}-mask field is {len(payload)} "
            f"bytes; max {dim} at leaf_dim={dim} (label must fit dim - "
            f"{2 + fields * _REGULATORY_GENE_MASK_BYTES} bytes)")
    block = payload + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _regulatory_gene_masks(hv):
    """The exact non-negative ``(activator_mask, repressor_mask)`` pair carried inline in a
    regulatory-gene cap (§128/§129) — the TWO Klein-4 bit-planes. The activator is read at the
    ``_REGULATORY_GENE_MASK_BYTES`` bytes RIGHT AFTER the label's NUL terminator (big-endian,
    always present); the repressor is read at the NEXT ``_REGULATORY_GENE_MASK_BYTES`` bytes IF
    the leaf has room, else ``0`` (a rc128 single-mask cap / a short leaf carries NO repressor
    field — DUAL-READ ``activator=mask, repressor=0``, since the repressor lives in what was
    NUL padding). This is the OPERAND of the op⊗operand gene; the chromosome SELF-DESCRIBES
    BOTH masks by this bare-strand read (no manifest). Class-I exact integers (never a float).
    A plain GENE cap (``0x47``, no mask field) reads as ``(0, 0)`` = unregulated = ALWAYS
    EXPRESSED (the additive back-compat case)."""
    raw = hv.tobytes()
    if raw[:1] != bytes([REGULATORY_GENE_MARKER]):
        return (0, 0)                                  # a plain gene — unregulated
    nul = raw.find(b"\x00", 1)                          # end of the inline label
    if nul < 0 or nul + 1 + _REGULATORY_GENE_MASK_BYTES > len(raw):
        raise ValueError(
            "regulatory gene cap is malformed: no label NUL / activator field truncated")
    act_base = nul + 1
    activator = int.from_bytes(raw[act_base:act_base + _REGULATORY_GENE_MASK_BYTES], "big")
    rep_base = act_base + _REGULATORY_GENE_MASK_BYTES
    # §129 DUAL-READ: the repressor field sits in what was NUL padding — present iff the leaf
    # has room; absent (rc128 single-mask / short leaf) => repressor 0 (no repression).
    if rep_base + _REGULATORY_GENE_MASK_BYTES <= len(raw):
        repressor = int.from_bytes(raw[rep_base:rep_base + _REGULATORY_GENE_MASK_BYTES], "big")
    else:
        repressor = 0
    return (activator, repressor)


def _regulatory_gene_mask(hv):
    """The exact non-negative ACTIVATOR mask of a regulatory-gene cap (§128 back-compat name)
    — the first Klein-4 bit-plane, ``_regulatory_gene_masks(hv)[0]``. A plain GENE cap
    (``0x47``, no mask) reads as ``0`` = unregulated = ALWAYS EXPRESSED. Prefer
    :func:`_regulatory_gene_masks` for BOTH planes (§129 repressor)."""
    return _regulatory_gene_masks(hv)[0]


def _validate_dnf_terms(dnf):
    """Validate a DNF term list (§130) → a list of validated ``(activator, repressor)`` int
    pairs. Each mask is a non-negative exact Class-I integer that fits the uint64 field (NO
    float; NEVER ``abs()`` — a mask is never negated). An empty list is legal (the OR-identity
    FALSE = never expresses)."""
    terms = []
    for i, term in enumerate(dnf):
        if len(term) != 2:
            raise ValueError(
                f"boolean gene DNF term {i} must be a 2-tuple (activator, repressor); got {term!r}")
        act, rep = term
        _validate_regulatory_mask(act, f"DNF term {i} activator")
        _validate_regulatory_mask(rep, f"DNF term {i} repressor")
        terms.append((int(act), int(rep)))
    return terms


def _pack_boolean_gene(gene_label, dnf, dim, gate_type=GATE_TYPE_BOOLEAN_DNF):
    """A fixed-width ``dim``-byte BOOLEAN GENE cap leaf (§130) — the GENERAL gate-type gene.

    ``[BOOLEAN_GENE_MARKER] + utf-8 label + NUL + gate_type(uint8) + n_terms(uint16 BE) +
    n_terms × (activator(uint64 BE) + repressor(uint64 BE))``, NUL-padded to ``dim``. The **op**
    (a gene: it opens + delimits a gene, like :func:`_gene_cap`) and the **operand** (arbitrary
    boolean regulatory logic over the condition bits, in DISJUNCTIVE NORMAL FORM — an OR of
    ``(require-present, require-absent)`` AND-clauses) are FUSED in the ONE cap. Placing the
    gate_type + DNF right AFTER the label's NUL keeps the label decode UNIFORM (bytes ``[1:]`` up
    to the first NUL — :func:`_unpack_cap` reads it with no boolean-gene special-case).

    Each DNF term IS an rc129-style activator/repressor AND-clause, so the rc129 klein4_mask
    two-mask is exactly a 1-TERM DNF (E1 ⊂ E2). :func:`gene_express` reads the DNF and expresses
    the gene IFF ANY term matches (``(cs & act) == act`` AND ``(cs & rep) == 0``). DNF is
    functionally complete, so ANY boolean function over the conditions is representable
    (AND / OR / NOT / XOR / any). All masks are non-negative exact integers (Class-I bitwise; NO
    float; NEVER ``abs()``). Same marker ``0x62`` = a NEW block KIND (v8 → v9), distinct from the
    ``0x67`` klein4_mask gene which stays the fast common case."""
    if gate_type != GATE_TYPE_BOOLEAN_DNF:
        raise ValueError(
            f"boolean gene gate_type {gate_type} is not supported (only "
            f"GATE_TYPE_BOOLEAN_DNF={GATE_TYPE_BOOLEAN_DNF} today)")
    terms = _validate_dnf_terms(dnf)
    if len(terms) >= (1 << (8 * _BOOLEAN_GENE_NTERMS_BYTES)):
        raise ValueError(
            f"boolean gene has {len(terms)} DNF terms; max "
            f"{(1 << (8 * _BOOLEAN_GENE_NTERMS_BYTES)) - 1} (the uint16 term count)")
    raw_label = gene_label.encode("utf-8") if isinstance(gene_label, str) else bytes(gene_label)
    if b"\x00" in raw_label:
        raise ValueError("boolean gene label must not contain a NUL byte")
    payload = bytearray(bytes([BOOLEAN_GENE_MARKER]) + raw_label + b"\x00")
    payload.append(gate_type & 0xFF)                                   # gate_type — uint8
    payload += len(terms).to_bytes(_BOOLEAN_GENE_NTERMS_BYTES, "big")  # n_terms — uint16 BE
    for act, rep in terms:
        payload += int(act).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big")
        payload += int(rep).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big")
    if len(payload) > dim:
        raise ValueError(
            f"boolean gene label {gene_label!r} + {len(terms)}-term DNF is {len(payload)} "
            f"bytes; max {dim} at leaf_dim={dim} (widen leaf_dim or reduce the DNF terms)")
    block = bytes(payload) + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _boolean_gene_dnf(hv):
    """``(gate_type, [(activator, repressor), …])`` carried inline in a BOOLEAN GENE cap (§130) —
    the DNF operand of the op⊗operand gene. Reads the gate_type byte + the uint16 term count
    right AFTER the label's NUL, then the ``n_terms`` ``(activator, repressor)`` uint64-BE pairs.
    The chromosome SELF-DESCRIBES its gate_type + DNF by this bare-strand read (no manifest).
    Class-I exact integers (never a float). Raises ``ValueError`` on a malformed / truncated
    cap."""
    raw = hv.tobytes()
    if raw[:1] != bytes([BOOLEAN_GENE_MARKER]):
        raise ValueError("not a boolean gene cap (first byte != BOOLEAN_GENE_MARKER)")
    nul = raw.find(b"\x00", 1)                          # end of the inline label
    if nul < 0 or nul + 1 + 1 + _BOOLEAN_GENE_NTERMS_BYTES > len(raw):
        raise ValueError(
            "boolean gene cap is malformed: no label NUL / gate_type+n_terms header truncated")
    gate_type = raw[nul + 1]
    if gate_type != GATE_TYPE_BOOLEAN_DNF:
        raise ValueError(
            f"boolean gene cap has unsupported gate_type {gate_type} "
            f"(only GATE_TYPE_BOOLEAN_DNF={GATE_TYPE_BOOLEAN_DNF} today)")
    nt_base = nul + 2
    n_terms = int.from_bytes(raw[nt_base:nt_base + _BOOLEAN_GENE_NTERMS_BYTES], "big")
    base = nt_base + _BOOLEAN_GENE_NTERMS_BYTES
    if base + n_terms * _BOOLEAN_GENE_TERM_BYTES > len(raw):
        raise ValueError("boolean gene cap is malformed: DNF term list truncated")
    terms = []
    for t in range(n_terms):
        o = base + t * _BOOLEAN_GENE_TERM_BYTES
        act = int.from_bytes(raw[o:o + _REGULATORY_GENE_MASK_BYTES], "big")
        rep = int.from_bytes(
            raw[o + _REGULATORY_GENE_MASK_BYTES:o + _BOOLEAN_GENE_TERM_BYTES], "big")
        terms.append((act, rep))
    return gate_type, terms


def _dnf_expresses(dnf_terms, cell_state):
    """Evaluate a DNF term list under ``cell_state`` (§130) — express iff ANY term matches:
    ``(cell_state & act) == act`` (all present-conditions present) AND ``(cell_state & rep) == 0``
    (no absent-condition present). The empty DNF (0 terms) is the OR-identity FALSE = never
    expresses. Exact Class-I bitwise (no float, never ``abs()``)."""
    for act, rep in dnf_terms:
        if (cell_state & act) == act and (cell_state & rep) == 0:
            return True
    return False


def _gene_gate_type(hv):
    """The declared ``gate_type`` of a gene cap (§130/§131 dispatch family): a plain GENE
    (``0x47``) or a Klein-4-mask regulatory gene (``0x67``) is :data:`GATE_TYPE_KLEIN4_MASK` (the
    rc129 fast path); a boolean gene (``0x62``) reads its :data:`GATE_TYPE_BOOLEAN_DNF` from the
    cap; a threshold gene (``0x77``) reads its :data:`GATE_TYPE_THRESHOLD` from the cap. Any other
    block is not a gene → ``None``."""
    kind = _cap_kind(hv)
    if kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER):
        return GATE_TYPE_KLEIN4_MASK
    if kind == BOOLEAN_GENE_MARKER:
        return _boolean_gene_dnf(hv)[0]
    if kind == THRESHOLD_GENE_MARKER:
        return _threshold_gene_spec(hv)[0]
    if kind == GRADED_GENE_MARKER:
        return _graded_gene_spec(hv)[0]
    return None


def _validate_threshold_i64(value, which):
    """Validate one SIGNED Class-I/N threshold-gate integer (a weight or the threshold) — an
    exact int that fits the int64 two's-complement field ``[-2**63, 2**63)``. NO float. SIGNED is
    intended (an inhibitory weight is NEGATIVE — real biology); the SIGN is a Class-K pin-slot,
    never ``abs()`` (abs-ing a weight would silently drop the inhibitory sense)."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(
            f"threshold gene {which} must be an exact int (Class-I/N); got {value!r}")
    if value < _THRESHOLD_I64_MIN or value > _THRESHOLD_I64_MAX:
        raise ValueError(
            f"threshold gene {which} {value} exceeds the SIGNED int64 field "
            f"[-2**63, 2**63)")


def _pack_threshold_gene(gene_label, weights, threshold, dim, gate_type=GATE_TYPE_THRESHOLD):
    """A fixed-width ``dim``-byte THRESHOLD GENE cap leaf (§131) — the E4 linear-threshold gate.

    ``[THRESHOLD_GENE_MARKER] + utf-8 label + NUL + gate_type(uint8) + n_weights(uint16 BE) +
    threshold(int64 BE SIGNED) + n_weights × (weight(int64 BE SIGNED))``, NUL-padded to ``dim``.
    The **op** (a gene: it opens + delimits a gene, like :func:`_gene_cap`) and the **operand** (a
    LINEAR-THRESHOLD / perceptron gate over the condition bits — a signed integer weight per
    condition + an integer threshold) are FUSED in the ONE cap. Placing the gate_type + weights +
    threshold right AFTER the label's NUL keeps the label decode UNIFORM (bytes ``[1:]`` up to the
    first NUL — :func:`_unpack_cap` reads it with no threshold-gene special-case).

    :func:`gene_express` reads the vector + threshold and expresses the gene IFF
    ``Σᵢ (weightᵢ · bit_i(cell_state)) ≥ threshold`` (the exact integer weighted sum of the
    PRESENT conditions ≥ the threshold; the decision is the SIGN of ``Σ − threshold`` — Class-K,
    never ``abs()``). Weights + threshold are SIGNED exact integers (Class-I/N; NO float; an
    inhibitory input is a NEGATIVE weight). Same marker ``0x77`` = a NEW block KIND (v9 → v10),
    distinct from the ``0x67`` klein4-mask / ``0x62`` boolean genes. This is GENUINELY DISTINCT
    from E2's DNF — a linear-threshold function (MAJORITY-of-n, a weighted dose-sum) needs an
    EXPONENTIALLY-large DNF, so E4 compactly captures what E2 cannot."""
    if gate_type != GATE_TYPE_THRESHOLD:
        raise ValueError(
            f"threshold gene gate_type {gate_type} is not supported (only "
            f"GATE_TYPE_THRESHOLD={GATE_TYPE_THRESHOLD} today)")
    weights = list(weights)
    if len(weights) >= (1 << (8 * _THRESHOLD_GENE_NWEIGHTS_BYTES)):
        raise ValueError(
            f"threshold gene has {len(weights)} weights; max "
            f"{(1 << (8 * _THRESHOLD_GENE_NWEIGHTS_BYTES)) - 1} (the uint16 weight count)")
    _validate_threshold_i64(threshold, "threshold")
    for i, w in enumerate(weights):
        _validate_threshold_i64(w, f"weight {i}")
    raw_label = gene_label.encode("utf-8") if isinstance(gene_label, str) else bytes(gene_label)
    if b"\x00" in raw_label:
        raise ValueError("threshold gene label must not contain a NUL byte")
    payload = bytearray(bytes([THRESHOLD_GENE_MARKER]) + raw_label + b"\x00")
    payload.append(gate_type & 0xFF)                                        # gate_type — uint8
    payload += len(weights).to_bytes(_THRESHOLD_GENE_NWEIGHTS_BYTES, "big")  # n_weights — uint16 BE
    payload += int(threshold).to_bytes(_THRESHOLD_GENE_THRESHOLD_BYTES, "big", signed=True)
    for w in weights:
        payload += int(w).to_bytes(_THRESHOLD_GENE_WEIGHT_BYTES, "big", signed=True)
    if len(payload) > dim:
        raise ValueError(
            f"threshold gene label {gene_label!r} + {len(weights)}-weight vector is "
            f"{len(payload)} bytes; max {dim} at leaf_dim={dim} (widen leaf_dim or reduce the "
            f"weight count)")
    block = bytes(payload) + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _threshold_gene_spec(hv):
    """``(gate_type, [weight, …], threshold)`` carried inline in a THRESHOLD GENE cap (§131) — the
    perceptron operand of the op⊗operand gene. Reads the gate_type byte + the uint16 weight count
    + the int64 SIGNED threshold right AFTER the label's NUL, then the ``n_weights`` int64 SIGNED
    weights. The chromosome SELF-DESCRIBES its weights + threshold by this bare-strand read (no
    manifest). Class-I/N exact SIGNED integers (never a float; the sign is meaningful, never
    ``abs()``). Raises ``ValueError`` on a malformed / truncated cap."""
    raw = hv.tobytes()
    if raw[:1] != bytes([THRESHOLD_GENE_MARKER]):
        raise ValueError("not a threshold gene cap (first byte != THRESHOLD_GENE_MARKER)")
    nul = raw.find(b"\x00", 1)                          # end of the inline label
    hdr = 1 + _THRESHOLD_GENE_NWEIGHTS_BYTES + _THRESHOLD_GENE_THRESHOLD_BYTES
    if nul < 0 or nul + hdr > len(raw):
        raise ValueError(
            "threshold gene cap is malformed: no label NUL / gate_type+n_weights+threshold "
            "header truncated")
    gate_type = raw[nul + 1]
    if gate_type != GATE_TYPE_THRESHOLD:
        raise ValueError(
            f"threshold gene cap has unsupported gate_type {gate_type} "
            f"(only GATE_TYPE_THRESHOLD={GATE_TYPE_THRESHOLD} today)")
    nw_base = nul + 2
    n_weights = int.from_bytes(raw[nw_base:nw_base + _THRESHOLD_GENE_NWEIGHTS_BYTES], "big")
    th_base = nw_base + _THRESHOLD_GENE_NWEIGHTS_BYTES
    threshold = int.from_bytes(
        raw[th_base:th_base + _THRESHOLD_GENE_THRESHOLD_BYTES], "big", signed=True)
    base = th_base + _THRESHOLD_GENE_THRESHOLD_BYTES
    if base + n_weights * _THRESHOLD_GENE_WEIGHT_BYTES > len(raw):
        raise ValueError("threshold gene cap is malformed: weight vector truncated")
    weights = []
    for k in range(n_weights):
        o = base + k * _THRESHOLD_GENE_WEIGHT_BYTES
        weights.append(int.from_bytes(
            raw[o:o + _THRESHOLD_GENE_WEIGHT_BYTES], "big", signed=True))
    return gate_type, weights, threshold


def _threshold_expresses(weights, threshold, cell_state):
    """Evaluate a linear-threshold (perceptron) gate under ``cell_state`` (§131) — express iff
    ``Σᵢ (weightᵢ · bit_i(cell_state)) ≥ threshold``. The exact SIGNED integer weighted sum over
    the PRESENT conditions (bit ``i`` of ``cell_state``) is compared against the threshold; the
    decision is the SIGN of ``(Σ − threshold)`` — a **Class-K sign-branch, NEVER ``abs()``**
    (abs-ing the sum would discard the inhibitory sign). SIGNED weights (a repressive input is a
    NEGATIVE weight). Exact Class-I/N integers (arbitrary precision; no float). The boundary is
    INCLUSIVE (``Σ == threshold`` expresses)."""
    total = 0
    for i, w in enumerate(weights):
        if (cell_state >> i) & 1:                        # bit_i(cell_state) — condition present
            total += w                                   # exact signed accumulate (Class-I/N)
    delta = total - threshold                            # Class-K pin-slot: the SIGN decides
    return delta >= 0                                    # inclusive boundary; never abs()


def _validate_graded_denom(denom):
    """Validate the graded-gene DENOMINATOR (§132) — a POSITIVE exact integer that fits the uint64
    field ``[1, 2**64)``. A divisor is never negative (never ``abs()``); a zero denom is rejected
    (division by zero). Class-N exact integer, NO float."""
    if not isinstance(denom, int) or isinstance(denom, bool):
        raise ValueError(
            f"graded gene denom must be an exact int (Class-N); got {denom!r}")
    if denom < 1:
        raise ValueError(
            f"graded gene denom must be POSITIVE (≥ 1 — the full-expression dose; a divisor is "
            f"never zero or negative, so never abs()); got {denom}")
    if denom > _GRADED_U64_MAX:
        raise ValueError(
            f"graded gene denom {denom} exceeds the uint64 field [1, 2**64)")


def _pack_graded_gene(gene_label, weights, denom, dim, gate_type=GATE_TYPE_GRADED):
    """A fixed-width ``dim``-byte GRADED (dose-response) GENE cap leaf (§132) — the E3 analog LEVEL.

    ``[GRADED_GENE_MARKER] + utf-8 label + NUL + gate_type(uint8) + n_weights(uint16 BE) +
    denom(uint64 BE POSITIVE) + n_weights × (level_weight(int64 BE SIGNED))``, NUL-padded to
    ``dim``. The **op** (a gene: it opens + delimits a gene, like :func:`_gene_cap`) and the
    **operand** (a dose-response / analog level over the condition bits — a signed integer
    level-weight per condition + a positive denominator) are FUSED in the ONE cap. Placing the
    gate_type + n_weights + denom + weights right AFTER the label's NUL keeps the label decode
    UNIFORM (bytes ``[1:]`` up to the first NUL — :func:`_unpack_cap` reads it with no
    graded-gene special-case).

    :func:`gene_express_levels` reads the vector + denom and reports the gene's exact-rational
    LEVEL ``Σᵢ (level_weightᵢ · bit_i(cell_state)) / denom`` clamped to ``[0, 1]`` (Class-N exact
    rational; the raw dose SIGN is a Class-K pin-slot, never ``abs()``; the fraction reduced by the
    Class-I gcd). ``denom`` is a POSITIVE exact integer (the full-ON dose); ``weights`` are SIGNED
    exact integers (Class-N; NO float; an inhibitory input is a NEGATIVE weight). Same marker
    ``0x64`` = a NEW block KIND (v10 → v11), distinct from the ``0x67`` / ``0x62`` / ``0x77``
    binary gate genes — the level axis is ORTHOGONAL to the E1/E2/E4 IF-gate family."""
    if gate_type != GATE_TYPE_GRADED:
        raise ValueError(
            f"graded gene gate_type {gate_type} is not supported (only "
            f"GATE_TYPE_GRADED={GATE_TYPE_GRADED} today)")
    weights = list(weights)
    if len(weights) >= (1 << (8 * _GRADED_GENE_NWEIGHTS_BYTES)):
        raise ValueError(
            f"graded gene has {len(weights)} level-weights; max "
            f"{(1 << (8 * _GRADED_GENE_NWEIGHTS_BYTES)) - 1} (the uint16 weight count)")
    _validate_graded_denom(denom)
    for i, w in enumerate(weights):
        _validate_threshold_i64(w, f"level_weight {i}")   # SIGNED int64 level-weight (Class-N)
    raw_label = gene_label.encode("utf-8") if isinstance(gene_label, str) else bytes(gene_label)
    if b"\x00" in raw_label:
        raise ValueError("graded gene label must not contain a NUL byte")
    payload = bytearray(bytes([GRADED_GENE_MARKER]) + raw_label + b"\x00")
    payload.append(gate_type & 0xFF)                                     # gate_type — uint8
    payload += len(weights).to_bytes(_GRADED_GENE_NWEIGHTS_BYTES, "big")  # n_weights — uint16 BE
    payload += int(denom).to_bytes(_GRADED_GENE_DENOM_BYTES, "big")       # denom — uint64 BE (>=1)
    for w in weights:
        payload += int(w).to_bytes(_GRADED_GENE_WEIGHT_BYTES, "big", signed=True)
    if len(payload) > dim:
        raise ValueError(
            f"graded gene label {gene_label!r} + {len(weights)}-weight vector is "
            f"{len(payload)} bytes; max {dim} at leaf_dim={dim} (widen leaf_dim or reduce the "
            f"weight count)")
    block = bytes(payload) + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _graded_gene_spec(hv):
    """``(gate_type, [level_weight, …], denom)`` carried inline in a GRADED GENE cap (§132) — the
    dose-response operand of the op⊗operand gene. Reads the gate_type byte + the uint16 weight count
    + the uint64 POSITIVE denom right AFTER the label's NUL, then the ``n_weights`` int64 SIGNED
    level-weights. The chromosome SELF-DESCRIBES its level-weights + denom by this bare-strand read
    (no manifest). Class-N exact integers (never a float; the weight sign is meaningful, never
    ``abs()``). Raises ``ValueError`` on a malformed / truncated cap."""
    raw = hv.tobytes()
    if raw[:1] != bytes([GRADED_GENE_MARKER]):
        raise ValueError("not a graded gene cap (first byte != GRADED_GENE_MARKER)")
    nul = raw.find(b"\x00", 1)                          # end of the inline label
    hdr = 1 + _GRADED_GENE_NWEIGHTS_BYTES + _GRADED_GENE_DENOM_BYTES
    if nul < 0 or nul + hdr > len(raw):
        raise ValueError(
            "graded gene cap is malformed: no label NUL / gate_type+n_weights+denom header "
            "truncated")
    gate_type = raw[nul + 1]
    if gate_type != GATE_TYPE_GRADED:
        raise ValueError(
            f"graded gene cap has unsupported gate_type {gate_type} "
            f"(only GATE_TYPE_GRADED={GATE_TYPE_GRADED} today)")
    nw_base = nul + 2
    n_weights = int.from_bytes(raw[nw_base:nw_base + _GRADED_GENE_NWEIGHTS_BYTES], "big")
    dn_base = nw_base + _GRADED_GENE_NWEIGHTS_BYTES
    denom = int.from_bytes(raw[dn_base:dn_base + _GRADED_GENE_DENOM_BYTES], "big")
    if denom < 1:
        raise ValueError("graded gene cap is malformed: denom must be POSITIVE (>= 1)")
    base = dn_base + _GRADED_GENE_DENOM_BYTES
    if base + n_weights * _GRADED_GENE_WEIGHT_BYTES > len(raw):
        raise ValueError("graded gene cap is malformed: level-weight vector truncated")
    weights = []
    for k in range(n_weights):
        o = base + k * _GRADED_GENE_WEIGHT_BYTES
        weights.append(int.from_bytes(
            raw[o:o + _GRADED_GENE_WEIGHT_BYTES], "big", signed=True))
    return gate_type, weights, denom


def _clamp_reduce_level(raw_num, denom):
    """Clamp the raw dose ``raw_num / denom`` to ``[0, 1]`` and reduce (§132) — the exact-rational
    LEVEL as a reduced ``(num, den)`` tuple. ``denom`` is POSITIVE; ``raw_num`` is the SIGNED exact
    dose. The clamp is a **Class-K sign-branch, NEVER ``abs()``**: ``raw_num ≤ 0`` (sign of
    ``raw_num``) → ``(0, 1)`` (off); ``raw_num ≥ denom`` (sign of ``raw_num − denom``) → ``(1, 1)``
    (fully on); else the in-range fraction is reduced by the **Class-I gcd** (both parts positive,
    so no ``abs()``). Class-N exact rational, NO float."""
    if raw_num <= 0:                                     # Class-K: sign of raw_num — off
        return (0, 1)
    if raw_num >= denom:                                 # Class-K: sign of (raw_num - denom) — full
        return (1, 1)
    g = _gcd(raw_num, denom)                             # Class-I gcd (both positive; no abs)
    return (raw_num // g, denom // g)


def _graded_level(weights, denom, cell_state):
    """Evaluate a graded / dose-response gate under ``cell_state`` (§132) — the exact-rational
    LEVEL ``Σᵢ (level_weightᵢ · bit_i(cell_state)) / denom`` clamped to ``[0, 1]`` and reduced,
    returned as a ``(num, den)`` tuple. The SIGNED integer weighted dose over the PRESENT
    conditions (bit ``i`` of ``cell_state``) is the numerator; ``denom`` (POSITIVE) the full-ON
    dose. Class-N exact rational (arbitrary precision; no float); the raw-dose SIGN is a Class-K
    pin-slot (never ``abs()``); the fraction is Class-I gcd-reduced. Absent conditions contribute
    0 (a gene with dose ≤ 0 is off = level ``(0, 1)``)."""
    total = 0
    for i, w in enumerate(weights):
        if (cell_state >> i) & 1:                        # bit_i(cell_state) — condition present
            total += w                                   # exact signed dose accumulate (Class-N)
    return _clamp_reduce_level(total, denom)             # clamp [0,1] + gcd-reduce; never abs()


def _gene_level(cap, cell_state):
    """The exact-rational EXPRESSION LEVEL of the gene opened by ``cap`` under ``cell_state`` (§132)
    — a reduced ``(num, den)`` tuple, the per-gene read shared by :func:`gene_express_levels`. A
    GRADED gene (``0x64``) → its clamped reduced dose-response rational (:func:`_graded_level`). A
    BINARY gene (plain ``0x47`` / klein4-mask ``0x67`` / boolean ``0x62`` / threshold ``0x77``) is
    the DEGENERATE graded case with levels ``{0, 1}``: ``(1, 1)`` if its gate passes else
    ``(0, 1)`` (reusing the §128/§130/§131 gate decision :func:`_gene_expresses`). So the LEVEL
    axis composes with EVERY gate-type. Native-authoritative when present (byte-identical C peer
    ``srmech_genome_gene_express_levels``); the pure Class-N/I integer path is the complete
    alternative. NO float, NEVER ``abs()``."""
    native = _gene_level_native(cap, cell_state)
    if native is not None:
        return native
    if _cap_kind(cap) == GRADED_GENE_MARKER:
        _gate_type, weights, denom = _graded_gene_spec(cap)
        return _graded_level(weights, denom, cell_state)
    # a BINARY gene — the degenerate {0, 1} graded case: level 1 iff its gate passes.
    return (1, 1) if _gene_expresses(cap, cell_state) else (0, 1)


def _pack_active_telomere(label, count, dim):
    """A fixed-width ``dim``-byte ACTIVE TELOMERE cap leaf (§127) — the op⊗operand cap.

    ``[ACTIVE_TELOMERE_MARKER] + utf-8 label + NUL + count(uint64 big-endian), NUL-
    padded to ``dim``. The **op** (a telomere: it opens + governs a chromosome, like
    :func:`telomere`) and the **operand** (``count`` — the exact Hayflick replicative
    counter) are FUSED in the ONE cap. Placing the count right AFTER the label's NUL
    terminator keeps the label decode UNIFORM (bytes ``[1:]`` up to the first NUL —
    :func:`_unpack_cap` reads it with no active-telomere special-case). ``count`` is a
    non-negative exact integer (Class-I/N; NO float; NEVER ``abs()`` — a plain count is
    never negated). Same width as any cap so the strand stays uniformly fixed-width."""
    if not isinstance(count, int) or isinstance(count, bool):
        raise ValueError(
            f"active telomere count must be an exact int (Class-I/N); got {count!r}")
    if count < 0:
        raise ValueError(
            f"active telomere count must be non-negative (a Hayflick counter counts "
            f"DOWN to 0 = senescence; it is never signed); got {count}")
    if count >= (1 << (8 * _ACTIVE_TELOMERE_COUNT_BYTES)):
        raise ValueError(
            f"active telomere count {count} exceeds the uint64 field "
            f"[0, 2**{8 * _ACTIVE_TELOMERE_COUNT_BYTES})")
    raw_label = label.encode("utf-8") if isinstance(label, str) else bytes(label)
    if b"\x00" in raw_label:
        raise ValueError("active telomere label must not contain a NUL byte")
    payload = (bytes([ACTIVE_TELOMERE_MARKER]) + raw_label + b"\x00"
               + int(count).to_bytes(_ACTIVE_TELOMERE_COUNT_BYTES, "big"))
    if len(payload) > dim:
        raise ValueError(
            f"active telomere label {label!r} + count field is {len(payload)} bytes; "
            f"max {dim} at leaf_dim={dim} (label must fit dim - {2 + _ACTIVE_TELOMERE_COUNT_BYTES} bytes)")
    block = payload + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _active_telomere_label(hv):
    """The chromosome label of an active-telomere cap — bytes ``[1:]`` up to the first
    NUL (UNIFORM with :func:`_unpack_cap`; the count sits AFTER that NUL)."""
    raw = hv.tobytes()
    return raw[1:].split(b"\x00", 1)[0].decode("utf-8")


def _active_telomere_count(hv):
    """The exact non-negative COUNT carried inline in an active-telomere cap (§127) —
    read at the ``_ACTIVE_TELOMERE_COUNT_BYTES`` bytes RIGHT AFTER the label's NUL
    terminator, big-endian. This is the OPERAND of the op⊗operand cap; the chromosome
    SELF-DESCRIBES its current count by this bare-strand read (no manifest). Class-I/N
    exact integer (never a float)."""
    raw = hv.tobytes()
    nul = raw.find(b"\x00", 1)                        # end of the inline label
    if nul < 0 or nul + 1 + _ACTIVE_TELOMERE_COUNT_BYTES > len(raw):
        raise ValueError(
            "active telomere cap is malformed: no label NUL / count field truncated")
    return int.from_bytes(raw[nul + 1:nul + 1 + _ACTIVE_TELOMERE_COUNT_BYTES], "big")


def active_telomere(label, count, dim=64):
    """The ACTIVE TELOMERE — a chromosome cap that carries a LIVE Hayflick counter (§127).

    A telomere (:func:`telomere`) is biology's non-coding chromosome-end cap. The
    ACTIVE telomere is that cap made op⊗operand: it still opens + governs a chromosome
    (the **op** — a gating rule), but it also carries an exact non-negative integer
    ``count`` INLINE in the strand (the **operand** — the Hayflick replicative counter,
    Harley/Futcher/Greider 1990; Hayflick 1965). The count MODULATES a downstream op
    (:func:`telomere_tick` — the divide/gate): count>0 → a divide proceeds + decrements
    the count (the telomere shortens); count==0 → honest senescence (a clean refuse).
    That is what makes the chromosome GENUINELY op⊗operand (a PASSIVE plain telomere is
    an op-slot only — swapping it leaves the leaves unchanged, #726).

    This is the SAME (operand, op) pattern as :func:`srmech.amsc.op_provenance.carry`
    ``(value, operation)`` and :class:`srmech.amsc.coupling.RecoverableFold`
    ``(lossy_bundle, exact_seed_R)`` — the proven op-carrying carrier — but with an
    ACTIVE op (the count changes how the operator works), which is the theorem #726
    asked for. It carries the DUALITY.md field/excitation duality LOCAL to the
    chromosome: the WHAT (leaves) + the HOW (the gating count) held in ONE object.

    ``count`` is an exact non-negative int (Class-I/N; no float; a count is never
    negated, so never ``abs()``). ``dim`` is the leaf width (match the turns it caps;
    :func:`chromosome` passes ``len(coupling)`` automatically). Same ``label`` + same
    ``count`` → same cap. Recover the count from the bare strand with
    :func:`_active_telomere_count`; tick it with :func:`telomere_tick`.
    """
    return _pack_active_telomere(label, count, dim)


def _pack_centromere(orientation, dim, *, repeats=CENTROMERE_DEFAULT_REPEATS,
                     handle="cen"):
    """A fixed-width ``dim``-byte CENTROMERE cap leaf (§95a) — the interior GLOBAL
    orientation anchor. ``[CENTROMERE_CAP_MARKER] + utf-8 handle + NUL + R(uint8) +
    R orientation votes``, NUL-padded to ``dim``. The handle (the CENP-A-analog
    epigenetic address, a per-chromosome handle SEPARATE from the content-address)
    decodes UNIFORMLY via :func:`_unpack_cap` (bytes ``[1:]`` up to the first NUL); the
    ``R`` + votes sit AFTER that NUL (the rc127 active-telomere inline-field pattern, so
    the handle decode needs no centromere special-case). Each vote is the global 4-way
    orientation ``o ∈ {0,1,2,3}`` (Class-C chirality); the ``R`` copies ARE biology's
    α-satellite repeat-array, majority-decoded on read (:func:`_centromere_orientation`).
    ``orientation`` is one Klein-4 sector; ``repeats`` a uint8 ≥ 1 (exact Class-I; NO
    float, NEVER ``abs()`` — an orientation index + a count are never negated)."""
    if (not isinstance(orientation, int) or isinstance(orientation, bool)
            or not 0 <= orientation <= 3):
        raise ValueError(
            f"centromere orientation must be a Klein-4 sector 0..3 (the global 4-way "
            f"which-way); got {orientation!r}")
    if (not isinstance(repeats, int) or isinstance(repeats, bool)
            or not 1 <= repeats <= 255):
        raise ValueError(
            f"centromere repeats R must be a uint8 in [1, 255] (the α-satellite array "
            f"size); got {repeats!r}")
    raw_handle = handle.encode("utf-8") if isinstance(handle, str) else bytes(handle)
    if b"\x00" in raw_handle:
        raise ValueError("centromere handle must not contain a NUL byte")
    payload = (bytes([CENTROMERE_CAP_MARKER]) + raw_handle + b"\x00"
               + bytes([repeats]) + bytes([orientation]) * repeats)
    if len(payload) > dim:
        raise ValueError(
            f"centromere handle {handle!r} + R={repeats} array is {len(payload)} bytes; "
            f"max {dim} at leaf_dim={dim} (handle must fit dim - {2 + repeats} bytes)")
    block = payload + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _centromere_votes(hv):
    """The ``R`` orientation votes (the α-satellite repeat-array) carried inline in a
    centromere cap (§95a) — read AFTER the handle's NUL terminator: byte ``[nul+1]`` is
    ``R``, bytes ``[nul+2 : nul+2+R]`` the votes. Class-I exact bytes (no float)."""
    raw = hv.tobytes()
    nul = raw.find(b"\x00", 1)                        # end of the inline handle
    if nul < 0 or nul + 2 > len(raw):
        raise ValueError(
            "centromere cap is malformed: no handle NUL / R field truncated")
    r = raw[nul + 1]
    if nul + 2 + r > len(raw):
        raise ValueError("centromere cap is malformed: repeat-array truncated")
    return list(raw[nul + 2:nul + 2 + r])


def _centromere_orientation(votes):
    """Majority-decode the GLOBAL 4-way orientation from the α-satellite repeat-array —
    ``klein4_triality_correct``'s order-3 2-of-3 majority GENERALISED to ``R`` votes
    (F1243 §1). Class-K sector-occupancy count over the 4 buckets + argmax (ties broken
    toward the LOWEST sector index — the same tie-rule the k=3 corrector uses). NO float,
    NO ``abs()``, NO numpy — a pure integer count-and-select (the cascade-honest EC read).
    One corrupted vote is outvoted by the agreeing majority, so the array recovers the
    which-way under the random noise F1243 measured (1.000 to f=0.2, 0.906 at f=0.49)."""
    counts = [0, 0, 0, 0]                             # Class-K sector occupancy
    for v in votes:
        counts[int(v) & 3] += 1
    best = 0
    for s in range(1, 4):
        if counts[s] > counts[best]:                  # strict > keeps ties at the lowest s
            best = s
    return best


def centromere(orientation, *, repeats=CENTROMERE_DEFAULT_REPEATS, handle="cen", dim=64):
    """The CENTROMERE — a chromosome's INTERIOR global-orientation anchor (§95a / F1243).

    A telomere (:func:`telomere`) caps a chromosome's ENDS; the centromere is the
    interior constriction BETWEEN its two arms — the segregation / melange-coupling
    split point, and the carrier of the per-chromosome GLOBAL orientation-chirality
    (the strand's handedness), distinct from Klein-4's LOCAL per-leaf sector chirality
    (ADR-0004). Where a centromere sits in the strand IS the p:q **arm-ratio** (biology:
    the centromere position defines the arms); the ``orientation`` it carries is stored
    as biology's **α-satellite repeat-array** (``repeats`` copies of the 4-way sector
    ``orientation ∈ {0,1,2,3}``), majority-decoded on read. Measured (F1243 §1): this
    recovers the global which-way at **~15× fewer bits than per-leaf Klein-4** (R=15 → 39
    bits vs 600) with matching random-noise robustness — taking the GLOBAL which-way off
    Klein-4 so G4 stays for the LOCAL chirality that varies along the strand.

    ``handle`` is the inline no-sidecar epigenetic address (CENP-A analog — a
    per-chromosome handle separate from the content-address). ``dim`` is the leaf width
    (match the turns; :func:`chromosome` passes ``len(coupling)`` automatically). Place it
    at mint time with ``chromosome(leaves, one, centromere=orientation)`` (or a lower-level
    insert); recover it from a strand with :func:`centromere_of`. Same inputs → same cap."""
    # rc258 (#1407): DISPATCH the cap byte-framing to the srmech_genome_centromere C peer
    # when HAS_NATIVE (byte-identical bytes, then wrapped in the same HV(sectors=256)); the
    # pure _pack_centromere below is the numpy-free fallback + parity oracle (it raises the
    # exact ValueError for a bad orientation / R / over-long handle — the native wrapper
    # returns None in those cases so the error surfaces here).
    native = _native.genome_centromere_c(orientation, repeats, handle, dim)
    if native is not None:
        return _HV.from_sequence(native, sectors=256)
    return _pack_centromere(orientation, dim, repeats=repeats, handle=handle)


def centromere_of(strand):
    """Recover a nuclear chromosome's GLOBAL orientation + arm-ratio from its centromere
    (§95a) — or ``None`` if the strand has no centromere (a Tier-1 plasmid chromosome).

    Scans for the interior ``0x58`` cap, majority-decodes the global 4-way orientation
    from its α-satellite repeat-array (:func:`_centromere_orientation` — the EC read),
    and reads the p:q **arm-ratio** from the cap's POSITION: ``p`` = data turns BEFORE it
    (the short arm), ``q`` = data turns AFTER (the long arm). Position IS the arm-ratio
    (biology: the centromere position defines the arms), so nothing double-encodes.

    Returns ``{"orientation", "arm_ratio": (p, q), "handle", "repeats"}`` or ``None``."""
    strand = list(strand)
    # rc258 (#1407): DISPATCH the orientation-majority + arm-ratio scan to the
    # srmech_genome_centromere_of C peer when HAS_NATIVE; the handle/repeats are read inline
    # in Python (the composition). The pure walk below is the numpy-free fallback + oracle.
    if strand:
        dim = len(list(strand[0]))
        native = _native.genome_centromere_of_c(
            b"".join(hv.tobytes() for hv in strand), len(strand), dim)
        if native is not None:
            found, orientation, p, q = native
            if not found:
                return None
            cen = next(hv for hv in strand if _cap_kind(hv) == CENTROMERE_CAP_MARKER)
            return {"orientation": orientation, "arm_ratio": (p, q),
                    "handle": _unpack_cap(cen)[1],
                    "repeats": len(_centromere_votes(cen))}
    p = 0
    total_turns = 0
    cen = None
    for hv in strand:
        kind = _cap_kind(hv)
        if kind == CENTROMERE_CAP_MARKER:
            cen = hv
            p = total_turns                           # data turns so far = the short arm
        elif kind is None:
            total_turns += 1                          # a coupled data turn (not a cap)
    if cen is None:
        return None
    votes = _centromere_votes(cen)
    _marker, handle = _unpack_cap(cen)
    return {"orientation": _centromere_orientation(votes),
            "arm_ratio": (p, total_turns - p), "handle": handle,
            "repeats": len(votes)}


def _leaf_is_erased(leaf_syms):
    """A leaf is ERASED (a DETECTABLE double-strand break — biology's cleared locus) iff all
    its Klein-4 symbols are 0 (the zero leaf, the erasure sentinel). Class-I exact (no float)."""
    return all(int(s) == 0 for s in leaf_syms)


def _diploid_ec_leaf(a_turn, b_turn, which, coupling):
    """The per-leaf diploid EC read (§95b / F1244; §95.4 erasure-symmetry fix): exactly one
    ERASED (a detectable break) → fill from the intact homolog (the diploid specialist — 2×
    not 3×); both present + agree → use it; both present but DISAGREE (a substitution) → trust
    the centromere which-template mark.

    ``a_turn``/``b_turn`` are the two STORED homolog TURNS (the on-disk Klein-4 HVs, PRE-
    decouple); ``coupling`` the shared invariant; ``which`` the mark parity (0 = trust copyA,
    1 = trust copyB). **Erasure is read on the stored TURN, not the decoupled leaf** — a double-
    strand break zeros the stored turn, and a zeroed turn decouples to a NON-zero leaf, so the
    all-zero erasure sentinel MUST be tested before :func:`quad_turn` (the §95.4 bug: testing
    the decoupled leaf detected NO erasure, so a copyA break healed only by substitution-
    tiebreak luck — asymmetric). Class-K sector compare, no float/abs."""
    a_erased = _leaf_is_erased(list(a_turn))
    b_erased = _leaf_is_erased(list(b_turn))
    if a_erased and not b_erased:
        return quad_turn(b_turn, coupling)              # fill from the intact homolog (erasure)
    if b_erased and not a_erased:
        return quad_turn(a_turn, coupling)
    a, b = quad_turn(a_turn, coupling), quad_turn(b_turn, coupling)
    if list(a) == list(b):
        return a                                       # homologs agree (incl. both-erased)
    return b if which else a                           # substitution → the marked template


def diploid(leaves, coupling, *, label="diploid", orientation=None,
            repeats=CENTROMERE_DEFAULT_REPEATS):
    """A DIPLOID chromosome (§95b / F1244 / #1407) — biology's diploid pair, the erasure/break
    specialist.

    Stores TWO homologous copies of the kernel (maternal | paternal) split by an interior
    :func:`centromere` whose orientation is the **which-template mark** — 2 copies + 1 mark =
    3 = the k=3 triality (F291)::

        [diploid_telomere(label), copyA turns…, centromere(orientation), copyB turns…]

    ``copyA`` and ``copyB`` are the SAME content (a deterministic content-addressed store writes
    identical homologs; the redundancy is READ-time EC). Recover with :func:`recover_diploid`:
    on a DETECTABLE loss (an erased leaf — a double-strand break) it fills from the intact
    homolog, reaching triality-level fidelity at **2× not 3×** (measured, `R-RBS-LM-DIPLOID-EC`);
    on a substitution disagreement the centromere mark is the tiebreak. This is the erasure
    specialist of the k=3 coherency tower (triality is the substitution specialist).

    ``orientation`` is the which-template mark + the global orientation (default the kernel's
    content-address folded to a Klein-4 sector); ``repeats`` the centromere α-satellite size."""
    if coupling is None:
        raise ValueError("diploid: coupling is required")
    leaves = list(leaves)
    dim = len(list(coupling))
    o = _mint_orientation(leaves) if orientation is None else int(orientation)
    if not 0 <= o <= 3:
        raise ValueError(
            f"diploid orientation must be a Klein-4 sector 0..3 (the which-template mark + "
            f"global orientation); got {orientation!r}")
    # rc259 (#1407): DISPATCH the whole diploid assemble to the srmech_genome_diploid C peer
    # when HAS_NATIVE — 1:1 C↔Python byte parity. The pure build below is the numpy-free oracle.
    leaf_bytes = _leaf_blocks(leaves)
    if leaf_bytes and all(len(b) == dim for b in leaf_bytes):
        native = _native.genome_diploid_c(
            label, _coupling_block_bytes(coupling), b"".join(leaf_bytes), len(leaf_bytes),
            o, repeats, dim)
        if native is not None:
            return [_hv_from_block(native[i * dim:(i + 1) * dim])
                    for i in range(len(native) // dim)]
    copy = [quad_turn(leaf, coupling) for leaf in leaves]   # copyA == copyB (homologs)
    cap = _pack_cap(DIPLOID_TELOMERE_MARKER, label, dim)
    cen = _pack_centromere(o, dim, repeats=repeats)
    return [cap] + copy + [cen] + copy


def recover_diploid(strand, coupling):
    """Recover a diploid chromosome's content via the two-copy EC (§95b) — the inverse of
    :func:`diploid`. Splits the strand at its interior centromere into ``copyA | copyB``
    (homologs) and error-corrects per leaf (:func:`_diploid_ec_leaf`): agree → use; one erased
    (a detectable break) → fill from the intact homolog; disagree → trust the centromere
    which-template mark. Returns the recovered leaves. Raises ``ValueError`` if ``strand`` is
    not a diploid chromosome (no ``0x44`` cap) or is malformed (missing centromere / unequal
    arms)."""
    strand = list(strand)
    if not strand or _cap_kind(strand[0]) != DIPLOID_TELOMERE_MARKER:
        raise ValueError(
            "recover_diploid: strand is not a diploid chromosome (no leading 0x44 cap)")
    # rc259 (#1407): DISPATCH the two-copy EC to srmech_genome_recover_diploid when HAS_NATIVE
    # (byte-identical). The pure walk below is the numpy-free oracle.
    dim = len(list(strand[0]))
    native = _native.genome_recover_diploid_c(
        b"".join(hv.tobytes() for hv in strand), len(strand), dim,
        _coupling_block_bytes(coupling))
    if native is not None:
        return [_HV.from_sequence(native[i * dim:(i + 1) * dim], sectors=QUAD)
                for i in range(len(native) // dim)]
    copyA, copyB, cen = [], [], None
    seen_cen = False
    for hv in strand:
        kind = _cap_kind(hv)
        if kind == CENTROMERE_CAP_MARKER:
            cen = hv
            seen_cen = True
        elif kind is None:
            (copyB if seen_cen else copyA).append(hv)   # data turns split at the centromere
    if cen is None or len(copyA) != len(copyB):
        raise ValueError(
            "recover_diploid: malformed diploid (missing centromere or unequal homolog arms)")
    which = _centromere_orientation(_centromere_votes(cen)) & 1   # which-template mark parity
    out = []
    for a_turn, b_turn in zip(copyA, copyB):
        # pass the STORED turns (pre-decouple) — erasure is read on the turn (§95.4)
        out.append(_diploid_ec_leaf(a_turn, b_turn, which, coupling))
    return out


# ── §98/v15 CHROMATIN — biology's epigenetic ACCESS gate (rc268, #1422 / F1246-F1247) ────────

def _validate_chromatin_level(num, den):
    """A chromatin accessibility LEVEL must be an exact reduced-or-not rational ``num/den`` in
    ``[0, 1]`` — a NON-negative fraction (0 = fully silenced heterochromatin, 1 = fully accessible
    euchromatin). Class-N exact integers; NO float; NEVER ``abs()`` (a level is never negated)."""
    if (not isinstance(num, int) or isinstance(num, bool)
            or not isinstance(den, int) or isinstance(den, bool)):
        raise ValueError(
            f"chromatin level must be an exact integer num/den (Class-N); got {num!r}/{den!r}")
    if den < 1:
        raise ValueError(
            f"chromatin level denominator must be POSITIVE (>= 1; a level is a non-negative "
            f"fraction, never abs()); got {den}")
    if num < 0 or num > den:
        raise ValueError(
            f"chromatin accessibility level {num}/{den} is out of [0, 1] (0 = fully silenced "
            f"heterochromatin, 1 = fully accessible euchromatin)")


def _chromatin_state(state):
    """Normalise a :func:`condense` ``state`` argument to ``(chromatin_type, num, den,
    access_gate_type, gate_fields)`` (§98; §98.1/G1 adds the facultative gate tail).

    * ``True`` / ``"condensed"`` → BINARY, level ``(0, 1)`` (heterochromatin — silenced), gate NONE.
    * ``False`` / ``"open"`` → BINARY, level ``(1, 1)`` (euchromatin — accessible), gate NONE.
    * a ``(num, den)`` tuple → GRADED, the exact reduced rational level in ``[0, 1]`` (clamp +
      Class-I gcd-reduce via :func:`_clamp_reduce_level` — a Class-K sign-branch, NEVER ``abs()``),
      gate NONE. The first three are CONSTITUTIVE (``access_gate_type == CHROMATIN_GATE_NONE``,
      ``gate_fields is None``): accessibility is the STATIC level, constant in cell_state.
    * a ``dict`` → a FACULTATIVE (§98.1/G1) cell-state-conditional gate on the ``0x48`` cap (see
      :func:`_chromatin_state_facultative`): ``{"activator": m, "repressor": m0, "open_level": …}``
      (KLEIN4) / ``{"dnf": [(act, rep), …], "open_level": …}`` (BOOLEAN) /
      ``{"weights": [w, …], "threshold": t, "open_level": …}`` (THRESHOLD). ``open_level`` (the
      WHEN-OPEN accessibility level; default ``(1, 1)``) is any constitutive ``state`` form.
    """
    if state is True or state == "condensed":
        return CHROMATIN_TYPE_BINARY, 0, 1, CHROMATIN_GATE_NONE, None
    if state is False or state == "open":
        return CHROMATIN_TYPE_BINARY, 1, 1, CHROMATIN_GATE_NONE, None
    if isinstance(state, (tuple, list)) and len(state) == 2:   # a (num, den) — JSON delivers a list
        num, den = state
        _validate_chromatin_level(num, den)
        rn, rd = _clamp_reduce_level(num, den)   # §132 clamp[0,1] + gcd-reduce (Class-K/I, no abs)
        return CHROMATIN_TYPE_GRADED, rn, rd, CHROMATIN_GATE_NONE, None
    if isinstance(state, dict):                  # §98.1/G1 FACULTATIVE — a cell-state-conditional gate
        return _chromatin_state_facultative(state)
    raise ValueError(
        f"condense state must be True/'condensed' (silenced), False/'open' (accessible), a "
        f"(num, den) graded level in [0, 1], or a §98.1/G1 facultative dict "
        f"({{'activator'/'repressor', ...}} / {{'dnf', ...}} / {{'weights'/'threshold', ...}}); "
        f"got {state!r}")


def _chromatin_state_facultative(state):
    """Parse a §98.1/G1 FACULTATIVE ``condense`` dict → ``(chromatin_type, num, den,
    access_gate_type, gate_fields)``. The gate makes the ``0x48`` access layer cell-state-
    conditional (facultative heterochromatin — the Barr body / X-inactivation), reusing the
    §129/§130/§131 gene-gate wire forms ON the chromatin cap. ``open_level`` (default ``(1, 1)`` —
    fully accessible WHEN the gate fires; the biologically-correct default a gate-blind reader
    degrades to) is any constitutive ``state`` form and gives the ``(chromatin_type, num, den)``
    WHEN-OPEN level. The gate discriminator:

    * ``"activator"`` and/or ``"repressor"`` → :data:`CHROMATIN_GATE_KLEIN4`, fields ``(act, rep)``.
    * ``"dnf"`` (a list of ``(activator, repressor)`` AND-clauses) → :data:`CHROMATIN_GATE_BOOLEAN`.
    * ``"weights"`` (+ optional ``"threshold"``, default 0) → :data:`CHROMATIN_GATE_THRESHOLD`.

    Class-I/N exact integers throughout (no float; a mask/weight is never ``abs()``). The field
    validation is deferred to :func:`_chromatin_gate_blob` (the SAME validators the gene caps use).
    """
    open_level = state.get("open_level", (1, 1))
    ct, num, den, _gt, _f = _chromatin_state(open_level)   # the WHEN-OPEN (static) level
    if "activator" in state or "repressor" in state:
        fields = (int(state.get("activator", 0)), int(state.get("repressor", 0)))
        return ct, num, den, CHROMATIN_GATE_KLEIN4, fields
    if "dnf" in state:
        return ct, num, den, CHROMATIN_GATE_BOOLEAN, state["dnf"]
    if "weights" in state:
        fields = (list(state["weights"]), int(state.get("threshold", 0)))
        return ct, num, den, CHROMATIN_GATE_THRESHOLD, fields
    raise ValueError(
        f"condense facultative dict needs one of 'activator'/'repressor' (klein4), 'dnf' "
        f"(boolean), or 'weights' (threshold); got keys {sorted(state)!r}")


def _chromatin_gate_blob(access_gate_type, gate_fields):
    """Serialize a §98.1/G1 FACULTATIVE chromatin gate → ``[access_gate_type(u8)] + payload`` (the
    wire tail appended after ``den`` in a chromatin cap), or ``b""`` for a constitutive
    (:data:`CHROMATIN_GATE_NONE`) cap. The payload MIRRORS the gene-gate fields but carries NO inner
    ``gate_type`` byte (``access_gate_type`` is already the discriminator):

    * KLEIN4    : ``activator(u64 BE) + repressor(u64 BE)``                    [16 B, fixed]
    * BOOLEAN   : ``n_terms(u16 BE) + n_terms × (act(u64 BE) + rep(u64 BE))``  [2 + 16·n_terms]
    * THRESHOLD : ``n_weights(u16 BE) + threshold(i64 BE) + n_weights × weight(i64 BE)``

    Reuses the SAME field validators the gene caps use (:func:`_validate_regulatory_mask` /
    :func:`_validate_dnf_terms` / :func:`_validate_threshold_i64`). Class-I/N exact integers; NO
    float; a mask is never ``abs()``, a signed weight's sign is a Class-K pin-slot (never ``abs()``).
    The parity oracle for the C peer ``srmech_genome_chromatin_gated``'s appended bytes."""
    if access_gate_type == CHROMATIN_GATE_NONE:
        return b""
    blob = bytearray([access_gate_type & 0xFF])
    if access_gate_type == CHROMATIN_GATE_KLEIN4:
        act, rep = gate_fields
        _validate_regulatory_mask(act, "chromatin klein4 activator")
        _validate_regulatory_mask(rep, "chromatin klein4 repressor")
        blob += int(act).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big")
        blob += int(rep).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big")
    elif access_gate_type == CHROMATIN_GATE_BOOLEAN:
        terms = _validate_dnf_terms(gate_fields)
        if len(terms) >= (1 << (8 * _BOOLEAN_GENE_NTERMS_BYTES)):
            raise ValueError(
                f"chromatin boolean gate has {len(terms)} DNF terms; max "
                f"{(1 << (8 * _BOOLEAN_GENE_NTERMS_BYTES)) - 1} (the uint16 term count)")
        blob += len(terms).to_bytes(_BOOLEAN_GENE_NTERMS_BYTES, "big")
        for act, rep in terms:
            blob += int(act).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big")
            blob += int(rep).to_bytes(_REGULATORY_GENE_MASK_BYTES, "big")
    elif access_gate_type == CHROMATIN_GATE_THRESHOLD:
        weights, threshold = gate_fields
        weights = list(weights)
        if len(weights) >= (1 << (8 * _THRESHOLD_GENE_NWEIGHTS_BYTES)):
            raise ValueError(
                f"chromatin threshold gate has {len(weights)} weights; max "
                f"{(1 << (8 * _THRESHOLD_GENE_NWEIGHTS_BYTES)) - 1} (the uint16 weight count)")
        _validate_threshold_i64(threshold, "chromatin threshold")
        for i, w in enumerate(weights):
            _validate_threshold_i64(w, f"chromatin weight {i}")
        blob += len(weights).to_bytes(_THRESHOLD_GENE_NWEIGHTS_BYTES, "big")
        blob += int(threshold).to_bytes(_THRESHOLD_GENE_THRESHOLD_BYTES, "big", signed=True)
        for w in weights:
            blob += int(w).to_bytes(_THRESHOLD_GENE_WEIGHT_BYTES, "big", signed=True)
    else:
        raise ValueError(
            f"chromatin access_gate_type {access_gate_type} is not supported (NONE="
            f"{CHROMATIN_GATE_NONE} / KLEIN4={CHROMATIN_GATE_KLEIN4} / BOOLEAN="
            f"{CHROMATIN_GATE_BOOLEAN} / THRESHOLD={CHROMATIN_GATE_THRESHOLD})")
    return bytes(blob)


def _pack_chromatin(chromatin_type, num, den, dim, *, handle="chr", gate_blob=b""):
    """A fixed-width ``dim``-byte CHROMATIN cap leaf (§98) — the interior epigenetic ACCESS marker.

    ``[CHROMATIN_MARKER] + utf-8 handle + NUL + chromatin_type(uint8) + num(uint64 BE) +
    den(uint64 BE) [+ §98.1/G1 access-gate tail]``, NUL-padded to ``dim``. The **op** (a cap: it
    packages a region, like :func:`_pack_centromere`) and the **operand** (the accessibility LEVEL
    ``num/den`` in ``[0, 1]``) are FUSED in the ONE cap. Placing the type + num + den right AFTER the
    handle's NUL keeps the handle decode UNIFORM (bytes ``[1:]`` up to the first NUL —
    :func:`_unpack_cap` reads it with no chromatin special-case). §98.1/G1: ``gate_blob`` (from
    :func:`_chromatin_gate_blob`) is the OPTIONAL facultative access-gate tail appended after
    ``den``; ``b""`` (constitutive) makes the cap BYTE-IDENTICAL to a pre-rc274 v15 cap. The pure
    numpy-free parity oracle for the C peer ``srmech_genome_chromatin`` /
    ``srmech_genome_chromatin_gated``. Class-N exact (num/den POSITIVE fractions; NO float, NEVER
    ``abs()``)."""
    if chromatin_type not in (CHROMATIN_TYPE_BINARY, CHROMATIN_TYPE_GRADED):
        raise ValueError(
            f"chromatin_type {chromatin_type} is not supported (BINARY="
            f"{CHROMATIN_TYPE_BINARY} / GRADED={CHROMATIN_TYPE_GRADED})")
    _validate_chromatin_level(num, den)
    raw_handle = handle.encode("utf-8") if isinstance(handle, str) else bytes(handle)
    if b"\x00" in raw_handle:
        raise ValueError("chromatin handle must not contain a NUL byte")
    payload = (bytes([CHROMATIN_MARKER]) + raw_handle + b"\x00"
               + bytes([chromatin_type & 0xFF])
               + int(num).to_bytes(_CHROMATIN_LEVEL_BYTES, "big")
               + int(den).to_bytes(_CHROMATIN_LEVEL_BYTES, "big")
               + bytes(gate_blob))               # §98.1/G1 facultative gate (b"" == constitutive)
    if len(payload) > dim:
        raise ValueError(
            f"chromatin handle {handle!r} + level"
            f"{' + gate' if gate_blob else ''} fields is {len(payload)} bytes; max {dim} at "
            f"leaf_dim={dim} (widen leaf_dim, or the handle must fit dim - "
            f"{2 + 1 + 2 * _CHROMATIN_LEVEL_BYTES + len(gate_blob)} bytes)")
    block = payload + b"\x00" * (dim - len(payload))
    return _HV.from_sequence(block, sectors=256)


def _chromatin_spec(hv):
    """``(chromatin_type, num, den)`` carried inline in a CHROMATIN cap (§98) — the accessibility
    operand of the op⊗operand cap. Reads the chromatin_type byte + the two uint64 BE level fields
    right AFTER the handle's NUL. The chromosome SELF-DESCRIBES its access state by this bare-strand
    read (no manifest). Class-N exact integers (never a float; a level is never ``abs()``). Raises
    ``ValueError`` on a malformed / truncated cap."""
    raw = hv.tobytes()
    if raw[:1] != bytes([CHROMATIN_MARKER]):
        raise ValueError("not a chromatin cap (first byte != CHROMATIN_MARKER)")
    nul = raw.find(b"\x00", 1)                          # end of the inline handle
    need = 2 + 2 * _CHROMATIN_LEVEL_BYTES
    if nul < 0 or nul + need > len(raw):
        raise ValueError(
            "chromatin cap is malformed: no handle NUL / type+num+den header truncated")
    chromatin_type = raw[nul + 1]
    if chromatin_type not in (CHROMATIN_TYPE_BINARY, CHROMATIN_TYPE_GRADED):
        raise ValueError(
            f"chromatin cap has unsupported chromatin_type {chromatin_type}")
    nb = nul + 2
    num = int.from_bytes(raw[nb:nb + _CHROMATIN_LEVEL_BYTES], "big")
    den = int.from_bytes(raw[nb + _CHROMATIN_LEVEL_BYTES:nb + 2 * _CHROMATIN_LEVEL_BYTES], "big")
    if den < 1 or num > den:
        raise ValueError("chromatin cap is malformed: accessibility level out of [0, 1]")
    return chromatin_type, num, den


def _chromatin_gate_spec(hv):
    """Decode the §98.1/G1 FACULTATIVE access gate carried after ``den`` in a chromatin cap →
    ``(access_gate_type, gate_fields)``, or ``(CHROMATIN_GATE_NONE, None)`` for a constitutive /
    pre-rc274 cap. The ``access_gate_type`` byte sits at ``den_end`` (right after the two level
    fields); a TIGHT leaf with no room for it (``den_end >= len(raw)``, the pad-byte default) reads
    as NONE — the guard that keeps the read in-bounds. The EVALUATORS are the gene path's
    (:func:`_dnf_expresses` / :func:`_threshold_expresses` / the klein4 rule) — only THIS decoder is
    chromatin-specific. Class-I/N exact; NO float; NEVER ``abs()``. The parity oracle for the
    matching fields the C peer ``srmech_genome_chromatin_access`` decodes."""
    raw = hv.tobytes()
    if raw[:1] != bytes([CHROMATIN_MARKER]):
        raise ValueError("not a chromatin cap (first byte != CHROMATIN_MARKER)")
    nul = raw.find(b"\x00", 1)                                  # end of the inline handle
    den_end = nul + 2 + 2 * _CHROMATIN_LEVEL_BYTES              # the access_gate_type byte offset
    if nul < 0 or den_end >= len(raw):                          # tight leaf / no sentinel room → NONE
        return CHROMATIN_GATE_NONE, None
    gt = raw[den_end]
    if gt == CHROMATIN_GATE_NONE:
        return CHROMATIN_GATE_NONE, None
    b = den_end + 1                                             # the payload begins after the sentinel
    if gt == CHROMATIN_GATE_KLEIN4:
        if b + 2 * _REGULATORY_GENE_MASK_BYTES > len(raw):
            raise ValueError("chromatin klein4 gate truncated")
        act = int.from_bytes(raw[b:b + _REGULATORY_GENE_MASK_BYTES], "big")
        rep = int.from_bytes(
            raw[b + _REGULATORY_GENE_MASK_BYTES:b + 2 * _REGULATORY_GENE_MASK_BYTES], "big")
        return gt, (act, rep)
    if gt == CHROMATIN_GATE_BOOLEAN:
        if b + _BOOLEAN_GENE_NTERMS_BYTES > len(raw):
            raise ValueError("chromatin boolean gate header truncated")
        n = int.from_bytes(raw[b:b + _BOOLEAN_GENE_NTERMS_BYTES], "big")
        o = b + _BOOLEAN_GENE_NTERMS_BYTES
        if o + n * _BOOLEAN_GENE_TERM_BYTES > len(raw):
            raise ValueError("chromatin boolean gate DNF truncated")
        terms = []
        for _ in range(n):
            act = int.from_bytes(raw[o:o + _REGULATORY_GENE_MASK_BYTES], "big")
            rep = int.from_bytes(
                raw[o + _REGULATORY_GENE_MASK_BYTES:o + _BOOLEAN_GENE_TERM_BYTES], "big")
            terms.append((act, rep))
            o += _BOOLEAN_GENE_TERM_BYTES
        return gt, terms
    if gt == CHROMATIN_GATE_THRESHOLD:
        hdr = _THRESHOLD_GENE_NWEIGHTS_BYTES + _THRESHOLD_GENE_THRESHOLD_BYTES
        if b + hdr > len(raw):
            raise ValueError("chromatin threshold gate header truncated")
        n = int.from_bytes(raw[b:b + _THRESHOLD_GENE_NWEIGHTS_BYTES], "big")
        th_base = b + _THRESHOLD_GENE_NWEIGHTS_BYTES
        threshold = int.from_bytes(
            raw[th_base:th_base + _THRESHOLD_GENE_THRESHOLD_BYTES], "big", signed=True)
        o = th_base + _THRESHOLD_GENE_THRESHOLD_BYTES
        if o + n * _THRESHOLD_GENE_WEIGHT_BYTES > len(raw):
            raise ValueError("chromatin threshold gate weight vector truncated")
        weights = []
        for _ in range(n):
            weights.append(int.from_bytes(
                raw[o:o + _THRESHOLD_GENE_WEIGHT_BYTES], "big", signed=True))
            o += _THRESHOLD_GENE_WEIGHT_BYTES
        return gt, (weights, threshold)
    raise ValueError(f"chromatin cap has unsupported access_gate_type {gt}")


def _chromatin_access(hv, cell_state):
    """The COMPUTED accessibility ``(num, den)`` of ONE chromatin cap under ``cell_state`` (§98.1/G1).

    CONSTITUTIVE (``access_gate_type == CHROMATIN_GATE_NONE``) → the STATIC stored ``(num, den)``
    (constant in ``cell_state`` — EXACTLY the pre-rc274 read). FACULTATIVE → the WHEN-OPEN
    ``(num, den)`` iff the gate FIRES under ``cell_state``, else ``(0, 1)`` (silenced). Reuses the
    gene-gate EVALUATORS verbatim: the klein4 rule (Class-I), :func:`_dnf_expresses`,
    :func:`_threshold_expresses` (Class-K sign). NEVER ``abs()``. The pure parity oracle for the C
    peer ``srmech_genome_chromatin_access``."""
    _ct, num, den = _chromatin_spec(hv)                         # the WHEN-OPEN (or static) level
    gt, fields = _chromatin_gate_spec(hv)
    if gt == CHROMATIN_GATE_NONE:
        return (num, den)                                      # constitutive: constant in cell_state
    if gt == CHROMATIN_GATE_KLEIN4:
        act, rep = fields
        fires = (cell_state & act) == act and (cell_state & rep) == 0   # Class-I, no abs
    elif gt == CHROMATIN_GATE_BOOLEAN:
        fires = _dnf_expresses(fields, cell_state)             # REUSED
    else:                                                       # THRESHOLD
        weights, threshold = fields
        fires = _threshold_expresses(weights, threshold, cell_state)    # REUSED (Class-K sign)
    return (num, den) if fires else (0, 1)


def _chromatin_cap(chromatin_type, num, den, dim, handle="chr", *,
                   access_gate_type=CHROMATIN_GATE_NONE, gate_fields=None):
    """Build the fixed-width CHROMATIN cap leaf — DISPATCH the byte-framing to the C peer when
    HAS_NATIVE (byte-identical bytes, wrapped in the same ``HV(sectors=256)``); the pure
    :func:`_pack_chromatin` is the numpy-free fallback + oracle. A CONSTITUTIVE
    (:data:`CHROMATIN_GATE_NONE`) cap routes through ``srmech_genome_chromatin`` UNCHANGED
    (byte-identical to a pre-rc274 cap); a §98.1/G1 FACULTATIVE cap serializes its
    :func:`_chromatin_gate_blob` and routes through ``srmech_genome_chromatin_gated`` (which appends
    the blob verbatim)."""
    gate_blob = _chromatin_gate_blob(access_gate_type, gate_fields)
    if gate_blob:
        native = _native.genome_chromatin_gated_c(chromatin_type, num, den, gate_blob, handle, dim)
    else:
        native = _native.genome_chromatin_c(chromatin_type, num, den, handle, dim)
    if native is not None:
        return _HV.from_sequence(native, sectors=256)
    return _pack_chromatin(chromatin_type, num, den, dim, handle=handle, gate_blob=gate_blob)


def _chromatin_info(chromatin_type, num, den, at, handle):
    """The :func:`chromatin_of` result dict — the state + scope read shape."""
    if chromatin_type == CHROMATIN_TYPE_BINARY:
        state = "open" if num > 0 else "condensed"   # Class-K: the sign of the level numerator
    else:
        state = "graded"
    return {"type": _CHROMATIN_TYPE_NAMES[chromatin_type], "state": state,
            "level": (num, den), "handle": handle, "at": at,
            "scope": "chromosome" if at == 0 else "stretch"}


def _chrom_range(strand, label, *, op):
    """``(start, end)`` block indices of the TARGET chromosome in ``strand`` (the §98 splice range).

    A chromosome opens with a boundary cap (:data:`_CHROM_BOUNDARY_MARKERS`); ``label`` picks it by
    its inline label. ``label=None`` requires a single-chromosome strand (else it is ambiguous —
    pass ``label=``). ``end`` is the next boundary index (or ``len(strand)``)."""
    bounds = [i for i, hv in enumerate(strand) if _cap_kind(hv) in _CHROM_BOUNDARY_MARKERS]
    if not bounds or bounds[0] != 0:
        raise ValueError(
            f"{op}: strand does not open with a chromosome boundary cap (not a well-formed "
            f"chromosome / genome strand)")
    if label is None:
        if len(bounds) != 1:
            raise ValueError(
                f"{op}: strand has {len(bounds)} chromosomes; pass label= to pick which one to "
                f"condense/decondense")
        start = bounds[0]
    else:
        start = next((b for b in bounds if _unpack_cap(strand[b])[1] == label), None)
        if start is None:
            raise ValueError(f"{op}: no chromosome labelled {label!r} in the strand")
    nxt = [b for b in bounds if b > start]
    return start, (nxt[0] if nxt else len(strand))


def condense(strand, *, coupling=None, state=True, region=None, handle="chr", label=None):
    """CONDENSE a region — SET the chromatin ACCESS marker on an EXISTING chromosome (§98 / #1422).

    Biology's epigenetic packaging gate: the modify-WITHOUT-changing-the-DNA layer. ``condense``
    SPLICES a :data:`CHROMATIN_MARKER` (``0x48``) cap into ``strand`` IN-PLACE (a byte-splice, like
    :func:`genome_remove` / :func:`genome_replace`) — it PRESERVES the centromere + the body
    sequence, so a NUCLEAR chromosome comes out still nuclear (the ``0x58`` centromere byte-identical,
    :func:`centromere_of` unchanged). NO re-mint. Reversible with :func:`decondense`.

    ``state`` is the access state to set (:func:`_chromatin_state`): ``True`` / ``"condensed"`` →
    binary heterochromatin (silenced, level ``0``); ``False`` / ``"open"`` → binary euchromatin
    (accessible, level ``1``); a ``(num, den)`` tuple → a GRADED accessibility level in ``[0, 1]``
    (partial access — composes multiplicatively with a graded gene, :func:`gene_express_levels`).
    §98.1/G1: a ``dict`` state → a FACULTATIVE (cell-state-conditional) access gate — the Barr body /
    X-inactivation analog. ``{"activator": m, "repressor": m0}`` (klein4), ``{"dnf": [(act, rep),
    …]}`` (boolean), or ``{"weights": [w, …], "threshold": t}`` (threshold), each with an optional
    ``"open_level"`` (the WHEN-OPEN accessibility, default ``(1, 1)``). The region is then accessible
    (its stored WHEN-OPEN level) iff the gate FIRES under a query ``cell_state`` (read with
    :func:`accessible` / gated by :func:`gene_express`), else silenced ``(0, 1)``.

    PLACEMENT is scope. ``region=None`` (default) → HEAD scope: the marker goes right after the
    opening telomere and silences the WHOLE chromosome (the X-inactivation / master case).
    ``region`` INTERIOR STRETCH — the marker starts a stretch that silences everything from it to
    the next chromatin marker / chromosome boundary: ``region=k`` (a non-negative int) places it
    before the ``k``-th DATA TURN (the kernel-content granularity, like the §95a centromere sits
    between arms); ``region="<gene_label>"`` places it before that gene's cap (the gene-stretch
    granularity — silences that gene onward). ``label`` picks the chromosome in a multi-chromosome
    genome strand (required when there is more than one). ``coupling`` gives the leaf width (``dim``;
    defaults to the strand's block width). Returns a NEW strand (the input is unchanged). Native-
    dispatched cap bytes (``srmech_genome_chromatin``). Class A (cap) + Class C (the access
    which-way) + Class N (the exact-rational level)."""
    strand = list(strand)
    if not strand:
        raise ValueError("condense: empty strand (nothing to condense)")
    dim = len(list(coupling)) if coupling is not None else len(list(strand[0]))
    chromatin_type, num, den, access_gate_type, gate_fields = _chromatin_state(state)
    cap = _chromatin_cap(chromatin_type, num, den, dim, handle=handle,
                         access_gate_type=access_gate_type, gate_fields=gate_fields)
    start, end = _chrom_range(strand, label, op="condense")
    if region is None:
        insert = start + 1                          # HEAD scope: right after the opening telomere
    elif isinstance(region, str):
        insert = next(
            (i for i in range(start + 1, end)
             if _cap_kind(strand[i]) in _GENE_MARKERS and _unpack_cap(strand[i])[1] == region),
            None)
        if insert is None:
            raise ValueError(f"condense: no gene labelled {region!r} in the chromosome")
    elif isinstance(region, int) and not isinstance(region, bool) and region >= 0:
        turn_idx = [i for i in range(start + 1, end) if _cap_kind(strand[i]) is None]
        if region > len(turn_idx):
            raise ValueError(
                f"condense: region={region} exceeds the chromosome's {len(turn_idx)} data turns")
        insert = turn_idx[region] if region < len(turn_idx) else end
    else:
        raise ValueError(
            "condense: region must be None (whole chromosome), a non-negative data-turn index, or "
            f"a gene label str; got {region!r}")
    return strand[:insert] + [cap] + strand[insert:]


def decondense(strand, *, coupling=None, label=None):
    """DECONDENSE — CLEAR the chromatin ACCESS marker(s), the inverse of :func:`condense` (§98).

    Splices out every :data:`CHROMATIN_MARKER` (``0x48``) cap (or only those inside the ``label``
    chromosome), PRESERVING the centromere + body sequence — so a condensed-then-decondensed NUCLEAR
    chromosome is byte-identical to the original mint (NO re-mint). Returns a NEW strand (the input
    is unchanged). ``coupling`` is accepted for signature symmetry (the clear is a pure splice)."""
    strand = list(strand)
    if label is None:
        return [hv for hv in strand if _cap_kind(hv) != CHROMATIN_MARKER]
    start, end = _chrom_range(strand, label, op="decondense")
    return [hv for i, hv in enumerate(strand)
            if not (start <= i < end and _cap_kind(hv) == CHROMATIN_MARKER)]


def chromatin_of(strand, coupling=None):
    """Recover a chromosome's FIRST chromatin ACCESS state (§98) — or ``None`` if it carries no
    chromatin marker (an all-euchromatin, fully-accessible chromosome; the default).

    Scans for the interior ``0x48`` cap, reads its ``(chromatin_type, num, den)`` accessibility
    level + the number of DATA TURNS before it (the scope: ``0`` → whole-chromosome, ``>0`` → a
    stretch). Returns ``{"type", "state", "level": (num, den), "handle", "at", "scope"}`` or
    ``None``. NEVER MUTATES (a READ — biology reads the packaging, it does not rewrite the DNA).
    Native-dispatched (the C peer ``srmech_genome_chromatin_of`` does the scan; the handle is read
    inline in Python — the composition)."""
    strand = list(strand)
    if not strand:
        return None
    dim = len(list(strand[0]))
    native = _native.genome_chromatin_of_c(
        b"".join(hv.tobytes() for hv in strand), len(strand), dim)
    if native is not None:
        found, ctype, num, den, at = native
        if not found:
            return None
        cap = next(hv for hv in strand if _cap_kind(hv) == CHROMATIN_MARKER)
        return _chromatin_info(ctype, num, den, at, _unpack_cap(cap)[1])
    turns = 0
    for hv in strand:
        kind = _cap_kind(hv)
        if kind == CHROMATIN_MARKER:
            ctype, num, den = _chromatin_spec(hv)
            return _chromatin_info(ctype, num, den, turns, _unpack_cap(hv)[1])
        if kind is None:
            turns += 1                              # a coupled data turn (not a cap)
    return None


def accessible(strand, cell_state, *, coupling=None):
    """The COMPUTED accessibility LEVEL ``(num, den)`` of a chromosome under ``cell_state`` (§98.1/G1).

    The op⊗operand THEOREM at the CHROMATIN scale — the parallel of :func:`gene_express` one gate
    OUTWARD: the SAME genome under a DIFFERENT ``cell_state`` reads a DIFFERENT accessible level. It
    scans for the FIRST interior chromatin cap (``0x48``, the region head gate) and returns its
    computed :func:`_chromatin_access`:

    * a CONSTITUTIVE cap (``access_gate_type == CHROMATIN_GATE_NONE`` — the pre-rc274 default;
      centromeric / telomeric H3K9me3 heterochromatin) → its STATIC stored level, CONSTANT in
      ``cell_state``;
    * a FACULTATIVE cap (a klein4 / boolean / threshold gate, from ``condense(state={…})`` — the
      Barr body / H3K27me3-Polycomb X-inactivation analog) → its WHEN-OPEN level iff the gate FIRES
      under ``cell_state``, else ``(0, 1)`` (silenced);
    * a chromatin-FREE strand → ``(1, 1)`` (default euchromatin — fully accessible).

    ``num > 0`` is "open" (Class-K: the sign of the level numerator). ``cell_state`` is a
    non-negative exact int (Class-I bitwise; each set bit a present cell-state condition; NO float,
    NEVER ``abs()``). ``coupling`` is accepted for signature symmetry / leaf width (optional). ⚠️ A
    READ — the strand is byte-identical after this call (biology reads the packaging, it does not
    rewrite the DNA). Native-dispatched per-cap (the C peer ``srmech_genome_chromatin_access``
    computes the gated level); the pure :func:`_chromatin_access` is the complete alternative +
    oracle. Attests facultative heterochromatin as ONE facet: X-chromosome inactivation / the Barr
    body — Chadwick BP & Willard HF (2004) "Multiple spatially distinct types of facultative
    heterochromatin on the human inactive X chromosome", *PNAS* 101:17450-17455 (NCBI PMC534659,
    OA); constitutive vs facultative heterochromatin — Brown TA, *Genomes* (NCBI Bookshelf
    NBK21137, OA). Class-M (read / projection) over Class-K (the ``num>0`` sign) + Class-I (bitwise
    ``cs & act``) + Class-N (the exact-rational level)."""
    _plan_validate_cell_state("accessible", cell_state)
    strand = list(strand)
    if not strand:
        return (1, 1)                               # empty strand → default euchromatin
    dim = len(list(coupling)) if coupling is not None else len(list(strand[0]))
    for hv in strand:                               # the FIRST chromatin cap gates the chromosome
        if _cap_kind(hv) == CHROMATIN_MARKER:
            native = _native.genome_chromatin_access_c(hv.tobytes(), dim, cell_state)
            if native is not None:
                return native
            return _chromatin_access(hv, cell_state)
    return (1, 1)                                   # chromatin-free → default euchromatin


def chromosome(leaves=None, coupling=None, *, label="chromosome", genes=None,
               kernel=False, active_count=None, centromere=None, centromere_at=None):
    """Pack a kernel — or SEVERAL genes — into a telomere-capped strand (F713/F715/F730).

    **Single kernel (shipped F713/F715 behaviour, unchanged).** Pass ``leaves``
    (each a Klein-4 vector, one tome). They become a helix of QUAD-TURNS, each
    coupled through ``coupling`` (the reversible :func:`quad_turn`), led by a
    :func:`telomere` cap derived from ``label``::

        [telomere(label, dim), quad_turn(leaf0, coupling), quad_turn(leaf1, coupling), ...]

    Recover with :func:`recall`.

    **Several genes (F730/S43.1 / §44).** Pass ``genes=[(gene_label, gene_leaves),
    …]`` instead of ``leaves``: each gene is opened by a fixed-width INLINE
    :func:`_gene_cap` (telomere-analog for the gene), all inside ONE telomere-capped
    chromosome — every element a ``leaf_dim``-byte block, the strand SELF-DESCRIBES::

        [telomere(label, dim),
         gene_cap('rules'), quad_turn(r0, one), quad_turn(r1, one),
         gene_cap('board'), quad_turn(b0, one), ...]

    Recover the ``[(gene_label, gene_leaves), …]`` list with :func:`genes`. Pass
    **exactly one** of ``leaves`` or ``genes``; ``coupling`` is always required
    (the shared invariant every turn is coupled through). §44: the gene boundary is
    a scanned-for fixed-width cap, NOT a variable-length TLV frame (no offset
    sidecar — biology's nested inline framing).

    **Regulatory genes (§128 / #728; §129 / #729).** A gene MAY carry inline regulatory
    MASK(s) (its "regulatory region / promoter") by passing a **3- or 4-tuple** instead of
    the 2-tuple; it is opened by a :func:`_pack_regulatory_gene` cap (marker ``0x67``)
    carrying exact Class-I integer mask(s) INLINE:

    * **4-tuple** ``(gene_label, gene_leaves, activator_mask, repressor_mask)`` — §129 the
      two KLEIN-4 bit-planes: ``activator_mask`` = conditions the cell_state must have
      PRESENT, ``repressor_mask`` = conditions it must have ABSENT. Per condition the pair
      ``(act_bit, rep_bit)`` is a Klein-4 role (don't-care / activator / repressor / never;
      see :data:`_REGULATORY_GENE_ROLES`). The lac operon is the exemplar (expresses iff
      lactose PRESENT and glucose ABSENT).
    * **3-tuple** ``(gene_label, gene_leaves, activator_mask)`` — §128 activator-only
      (``repressor_mask = 0``); a pure conjunctive AND-gate, BYTE-IDENTICAL to rc128.
    * **2-tuple** ``(gene_label, gene_leaves)`` — UNREGULATED = ALWAYS EXPRESSED
      (``activator = repressor = 0``).

    **Boolean genes (§130 / #730 — the GENERAL gate-type).** For ARBITRARY boolean logic over
    the condition bits (AND / OR / NOT / XOR / any), pass a **3-tuple with a DICT spec**
    ``(gene_label, gene_leaves, {"gate": "boolean", "dnf": [(act, rep), …]})``; it is opened by
    a :func:`_pack_boolean_gene` cap (marker ``0x62``) carrying the gate_type + DNF INLINE. The
    ``"dnf"`` is a disjunctive normal form — an OR of ``(require-present, require-absent)``
    AND-clauses; the gene expresses iff ANY clause matches. Each clause IS an rc129
    activator/repressor pair, so the klein4_mask 4-tuple above is exactly a 1-CLAUSE boolean
    gene (**E1 ⊂ E2**); the ``0x67`` klein4_mask genes stay the compact FAST path, the ``0x62``
    boolean gene is the general escape hatch.

    :func:`gene_express` reads each gene's gate_type and includes the gene IFF the applied
    ``cell_state`` satisfies it — same DNA, different cell_state → different expressed subset
    (the op⊗operand theorem one scale up from the rc127 active telomere). Mixing 2-tuple,
    3-tuple (int mask OR dict boolean spec), and 4-tuple genes is additive + back-compatible.

    **Active telomere (§127 / #726).** Pass ``active_count=N`` (a non-negative int) to
    lead the (single-kernel) chromosome with an :func:`active_telomere` cap carrying an
    exact Hayflick counter INLINE instead of a plain :func:`telomere`. The chromosome
    is then GENUINELY op⊗operand — the telomere (op) governs whether the leaves may
    divide, gated by the count (operand) via :func:`telomere_tick`. Mutually exclusive
    with ``kernel``/``genes`` (a kernel/gene chromosome uses its own cap).
    """
    if coupling is None:
        raise ValueError("chromosome: coupling is required")
    if (leaves is None) == (genes is None):
        raise ValueError("chromosome: pass exactly one of leaves= or genes=")
    if kernel and genes is not None:
        raise ValueError(
            "chromosome: kernel=True is a single-kernel form — pass leaves=, not genes="
        )
    if active_count is not None and (kernel or genes is not None):
        raise ValueError(
            "chromosome: active_count= is a single-kernel telomere form — pass leaves=, "
            "not genes=/kernel= (a kernel/gene chromosome uses its own boundary cap)"
        )
    if centromere is not None and (kernel or genes is not None):
        raise ValueError(
            "chromosome: centromere= is a single-kernel MINT form — pass leaves=, not "
            "genes=/kernel= (§95a: the centromere is an interior anchor on a nuclear "
            "single-kernel chromosome; a gene / kernel chromosome is a different shape)"
        )
    if centromere_at is not None and centromere is None:
        raise ValueError(
            "chromosome: centromere_at= sets the p:q arm-ratio split but needs a "
            "centromere= orientation to place at that split"
        )
    dim = len(list(coupling))
    # §89/v6: a kernel chromosome opens with a KERNEL telomere (0x6B); §127: an
    # active-telomere chromosome opens with an ACTIVE telomere (0x74) carrying its count.
    if active_count is not None:
        cap = _pack_active_telomere(label, active_count, dim)
    elif kernel:
        cap = _kernel_telomere(label, dim=dim)
    else:
        cap = telomere(label, dim=dim)
    if genes is None:
        leaf_list = list(leaves)
        # rc197 (#887): DISPATCH the plain single-kernel path (no genes / kernel /
        # active_count / centromere) to the srmech_genome_chromosome C peer when
        # HAS_NATIVE — byte-identical (the CHROM cap via genome_pack_cap + each turn via
        # the reversible srmech_klein4_bind). The pure list-comp below is the numpy-free
        # fallback + parity oracle; the kernel / active-telomere / gene / MINT forms open
        # their own boundary caps (or an interior centromere) and stay pure here.
        if not kernel and active_count is None and centromere is None:
            leaf_bytes = _leaf_blocks(leaf_list)
            if all(len(b) == dim for b in leaf_bytes):
                native = _native.genome_chromosome_c(
                    label, _coupling_block_bytes(coupling), b"".join(leaf_bytes),
                    len(leaf_bytes), dim)
                if native is not None:
                    return [_hv_from_block(native[i * dim:(i + 1) * dim])
                            for i in range(len(native) // dim)]
        turns = [quad_turn(leaf, coupling) for leaf in leaf_list]
        if centromere is None:
            return [cap] + turns
        # §95a MINT (F1243): a TIER-2 nuclear chromosome — insert the INTERIOR centromere
        # cap at the p:q arm-split. The cap's POSITION in the strand IS the arm-ratio
        # (biology: the centromere position defines the arms); default metacentric =
        # the midpoint (p ≈ q). ``centromere`` is the global 4-way orientation ∈ {0,1,2,3};
        # it rides as the α-satellite repeat-array in the cap (majority-decoded on read).
        split = len(turns) // 2 if centromere_at is None else int(centromere_at)
        if not 0 <= split <= len(turns):
            raise ValueError(
                f"chromosome: centromere_at={centromere_at} out of range "
                f"[0, {len(turns)}] (the arm-split index between the short + long arm)")
        cen_cap = _pack_centromere(centromere, dim)
        return [cap] + turns[:split] + [cen_cap] + turns[split:]
    strand = [cap]
    # §128/§129: a gene MAY carry regulatory MASK(s) — open it with a REGULATORY GENE cap
    # (0x67) instead of a plain GENE cap (0x47):
    #   4-tuple ``(gene_label, gene_leaves, activator_mask, repressor_mask)`` — §129 the two
    #     Klein-4 bit-planes (require-present + require-absent conditions);
    #   3-tuple ``(gene_label, gene_leaves, activator_mask)`` — §128 activator-only (repressor
    #     0); BYTE-IDENTICAL to rc128 (back-compat);
    #   2-tuple ``(gene_label, gene_leaves)`` — an UNREGULATED (always-expressed) plain gene.
    # Mixing arities is additive / back-compatible.
    for gene in genes:
        if len(gene) == 4:
            gene_label, gene_leaves, act_mask, rep_mask = gene
            strand.append(_pack_regulatory_gene(gene_label, act_mask, dim, repressor=rep_mask))
        elif len(gene) == 3:
            gene_label, gene_leaves, spec = gene
            if isinstance(spec, dict):
                # §130/§131/§132 the dict gate-forms: {"gate": "graded", "weights": [...],
                # "denom": D} opens a GRADED GENE cap (0x64, E3 the analog dose-response LEVEL
                # — the ORTHOGONAL axis); {"gate": "threshold", "weights": [...], "threshold":
                # θ} opens a THRESHOLD GENE cap (0x77, E4 the linear-threshold / perceptron
                # gate); any other dict {"gate": "boolean", "dnf": [...]} opens a BOOLEAN GENE
                # cap (0x62, E2 the DNF gate).
                if spec.get("gate") in ("graded", "dose", "level"):
                    strand.append(_graded_gene_cap_from_spec(gene_label, spec, dim))
                elif spec.get("gate") in ("threshold", "linear_threshold"):
                    strand.append(_threshold_gene_cap_from_spec(gene_label, spec, dim))
                else:
                    strand.append(_boolean_gene_cap_from_spec(gene_label, spec, dim))
            else:
                # §128 the FAST klein4_mask path: an int activator-only mask (repressor 0),
                # BYTE-IDENTICAL to rc128 (the 0x67 gene stays the compact common case).
                strand.append(_pack_regulatory_gene(gene_label, spec, dim))
        else:
            gene_label, gene_leaves = gene
            strand.append(_gene_cap(gene_label, dim))
        strand.extend(quad_turn(leaf, coupling) for leaf in gene_leaves)
    return strand


def _boolean_gene_cap_from_spec(gene_label, spec, dim):
    """Build a §130 BOOLEAN GENE cap from a dict gene-spec — the chromosome-builder adapter for
    the GENERAL gate-type. ``spec`` is ``{"gate": "boolean", "dnf": [(act, rep), …]}`` (the
    ``"gate"`` key declares the gate_type; ``"dnf"`` is the disjunctive-normal-form term list, an
    OR of ``(require-present, require-absent)`` AND-clauses). Composes :func:`_pack_boolean_gene`."""
    gate = spec.get("gate", "boolean")
    if gate not in ("boolean", "boolean_dnf"):
        raise ValueError(
            f"boolean gene spec gate {gate!r} is not supported (only 'boolean' / 'boolean_dnf' "
            f"today — the §130 GENERAL gate-type); the fast klein4_mask path uses an int mask")
    if "dnf" not in spec:
        raise ValueError(
            "boolean gene spec must carry a 'dnf' term list [(activator, repressor), …] "
            "(disjunctive normal form: an OR of require-present/require-absent AND-clauses)")
    return _pack_boolean_gene(gene_label, spec["dnf"], dim)


def _threshold_gene_cap_from_spec(gene_label, spec, dim):
    """Build a §131 THRESHOLD GENE cap from a dict gene-spec — the chromosome-builder adapter for
    the E4 linear-threshold gate. ``spec`` is ``{"gate": "threshold", "weights": [w0, w1, …],
    "threshold": θ}`` (the ``"gate"`` key declares the gate_type; ``"weights"`` is the per-
    condition SIGNED integer weight vector — weight ``i`` gates condition bit ``i``; ``"threshold"``
    is the SIGNED integer θ). A gene expresses iff ``Σᵢ weightᵢ·bit_i(cell_state) ≥ θ``. Composes
    :func:`_pack_threshold_gene`."""
    gate = spec.get("gate", "threshold")
    if gate not in ("threshold", "linear_threshold"):
        raise ValueError(
            f"threshold gene spec gate {gate!r} is not supported (only 'threshold' / "
            f"'linear_threshold' today — the §131 E4 gate-type)")
    if "weights" not in spec:
        raise ValueError(
            "threshold gene spec must carry a 'weights' vector [w0, w1, …] (a SIGNED integer "
            "weight per condition bit; an inhibitory input is a NEGATIVE weight)")
    if "threshold" not in spec:
        raise ValueError(
            "threshold gene spec must carry a 'threshold' (a SIGNED integer θ; the gene "
            "expresses iff Σ weightᵢ·bit_i(cell_state) ≥ θ)")
    return _pack_threshold_gene(gene_label, spec["weights"], spec["threshold"], dim)


def _graded_gene_cap_from_spec(gene_label, spec, dim):
    """Build a §132 GRADED (dose-response) GENE cap from a dict gene-spec — the chromosome-builder
    adapter for the E3 analog LEVEL. ``spec`` is ``{"gate": "graded", "weights": [w0, w1, …],
    "denom": D}`` (the ``"gate"`` key declares the gate_type; ``"weights"`` is the per-condition
    SIGNED integer level-weight vector — weight ``i`` doses condition bit ``i``; ``"denom"`` is the
    POSITIVE integer full-expression normalizer). The LEVEL is the reduced exact rational
    ``Σᵢ weightᵢ·bit_i(cell_state) / denom`` clamped to ``[0, 1]``. Composes :func:`_pack_graded_gene`."""
    gate = spec.get("gate", "graded")
    if gate not in ("graded", "dose", "level"):
        raise ValueError(
            f"graded gene spec gate {gate!r} is not supported (only 'graded' / 'dose' / "
            f"'level' today — the §132 E3 analog-level axis)")
    if "weights" not in spec:
        raise ValueError(
            "graded gene spec must carry a 'weights' vector [w0, w1, …] (a SIGNED integer "
            "level-weight per condition bit; an inhibitory input is a NEGATIVE weight)")
    if "denom" not in spec:
        raise ValueError(
            "graded gene spec must carry a 'denom' (a POSITIVE integer — the full-expression "
            "dose; the LEVEL is Σ weightᵢ·bit_i(cell_state) / denom clamped to [0, 1])")
    return _pack_graded_gene(gene_label, spec["weights"], spec["denom"], dim)


def recall(strand, coupling, telomere=None):
    """Recover the kernel's leaves from a capped chromosome strand (F713/F715/§44).

    Walk the ``strand``; skip every CAP leaf — CHROM or GENE, recognised by its
    inline marker (first byte ``> 3``), §44 — and re-bind ``coupling`` (the reversible
    :func:`quad_turn` again) on each coupled data turn to recover the original leaf.
    The exact inverse of :func:`chromosome`::

        recall(chromosome(leaves, one, label=L), one) == leaves

    §44: caps are recognised by their inline marker (the strand self-describes), not
    matched by value — so ``recall`` no longer needs the cap handed to it; the
    ``telomere`` parameter is accepted for back-compat and ignored. (Use :func:`genes`
    on a multi-gene chromosome to keep the per-gene split; ``recall`` flattens.)
    """
    # rc197 (#887): DISPATCH to the srmech_genome_recall C peer when HAS_NATIVE and
    # the strand is uniform fixed-width leaf_dim blocks — byte-identical (skip every
    # cap via genome_cap_kind, re-bind each data turn via the reversible
    # srmech_klein4_bind). recall is gate-agnostic (it flattens across CHROM / GENE /
    # kernel / active-telomere caps alike), so the C peer covers the multi-gene strand
    # too. The pure walk below is the numpy-free fallback + parity oracle, and handles
    # any non-uniform strand (e.g. a variable-width packed turn).
    dim = len(list(coupling))
    blocks = _leaf_blocks(strand)
    if dim > 0 and blocks and all(len(b) == dim for b in blocks):
        native = _native.genome_recall_c(
            b"".join(blocks), len(blocks), dim, _coupling_block_bytes(coupling))
        if native is not None:
            leaf_bytes, n = native
            return [_HV.from_sequence(leaf_bytes[i * dim:(i + 1) * dim], sectors=QUAD)
                    for i in range(n)]
    leaves = []
    for hv in strand:
        if _cap_kind(hv) is not None:   # a CHROM/GENE cap — a delimiter, not data
            continue
        leaves.append(quad_turn(hv, coupling))   # reversible uncouple (bind o bind == id)
    return leaves


def genes(strand, coupling):
    """Recover ``[(gene_label, gene_leaves), …]`` from a multi-gene chromosome (F730/S43).

    The exact inverse of ``chromosome(genes=…, coupling)``. Walk the ``strand``:
    a :func:`_gene_cap` (first byte :data:`GENE_CAP_MARKER` — never a Klein-4 turn)
    opens a new gene whose label is read back INLINE (:func:`_unpack_cap`, no TLV);
    every coupled data turn until the next gene-cap (or the end) is re-bound through
    ``coupling`` (the reversible :func:`quad_turn`) to recover that gene's leaf. The
    leading CHROM cap (the chromosome telomere) is skipped — so ``genes`` needs only
    the strand + ``coupling``, no cap argument::

        genes(chromosome(genes=[("a", la), ("b", lb)], one), one) == [("a", la), ("b", lb)]

    Use :func:`genes` (not :func:`recall`) on a multi-gene chromosome; ``recall``
    flattens across the gene boundaries (§44: scanned by inline marker).
    """
    out = []
    cur_label = None
    cur_leaves = []
    started = False
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                    THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
            # §128/§130/§131: a plain GENE cap (0x47), a REGULATORY GENE cap (0x67), a BOOLEAN
            # GENE cap (0x62) OR a THRESHOLD GENE cap (0x77) opens a gene; its label reads
            # UNIFORMLY (the mask(s) / gate_type + DNF / weights sit AFTER the label NUL, so
            # _unpack_cap reads the label with no special-case). genes() recovers ALL genes
            # gate-agnostically (gene_express() applies the filter).
            if started:
                out.append((cur_label, cur_leaves))
            _marker, cur_label = _unpack_cap(hv)
            cur_leaves = []
            started = True
        elif kind in (CHROM_CAP_MARKER, KERNEL_HEADER_MARKER,
                      KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER):
            continue                            # the chromosome telomere / §60 v5
                                                # header / §89 kernel telomere / §127
                                                # active telomere — skip (not gene data)
        elif not started:
            continue                            # any leading cap before the first gene
        else:
            cur_leaves.append(quad_turn(hv, coupling))   # reversible uncouple
    if started:
        out.append((cur_label, cur_leaves))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# §135 (rc273, F1251) — the GENE COPY-NUMBER (multiplicity) axis. F1251 read
# attested bacterial genomics (Shropshire et al., MPM-verified): IS26-mediated
# amplification raises a resistance gene's COPY NUMBER — the genome stores "how
# many copies", a MULTIPLICITY annotation (a count), NOT N physical duplicated
# strands. amplify(chrom, label, n) records the count on the named plain gene's
# 0x47 cap (in what was NUL padding, RIGHT AFTER the label's NUL — the §129 mask /
# §127 count placement); copy_number_of(chrom, label) reads it (default 1 = a
# plain / pre-rc273 gene = present-once). Additive field, NO new marker, format 15
# stays: a plain 0x47 cap reads as ALWAYS-EXPRESSED regardless of trailing bytes in
# BOTH Python (_gene_expresses) and C (srmech_genome_gene_express returns on the
# marker before reading any field), so the count is transparent to every existing
# reader (gene_express / partition / recall / census) and survives genome_save /
# reload / integrate byte-exact. Class-I/N exact integer; no float; never abs().
# ─────────────────────────────────────────────────────────────────────────────


def amplify(chrom, label, n):
    """Set a gene's COPY NUMBER (multiplicity) to ``n`` — the IS26-amplification analog
    (§135/rc273 / F1251).

    F1251: attested bacterial genomics (Shropshire et al.) measured that IS26-mediated
    amplification raises a resistance gene's COPY NUMBER — the genome stores HOW MANY COPIES.
    ``amplify`` records that count on the named plain gene's cap: it walks ``chrom`` (a
    chromosome strand — from ``chromosome(genes=…)`` — or any genome strand), finds the FIRST
    plain GENE cap (``0x47``) whose inline label equals ``label``, and returns a NEW strand with
    that cap rewritten to carry ``n`` inline (the gene's data turns + every other block are
    byte-copied unchanged). ``n`` is the MULTIPLICITY — a Class-I/N exact integer ``>= 1`` — NOT
    N physical duplicated strands: it is an annotation (a count) on the ONE gene, so the strand
    length is UNCHANGED. This is a §44 self-describing edit — the count rides in what was the
    cap's NUL padding, RIGHT AFTER the label's NUL (the §129 regulatory-mask / §127 active-count
    placement), so ``partition`` / ``recall`` / ``gene_express`` / ``genome_census`` all still
    read the cap as the SAME always-expressed plain gene (the copy-number is transparent to
    them, Python AND C), and the count survives ``genome_save`` / reload / ``integrate``
    byte-exact.

    ``n == 1`` (the default present-once) rewrites to the BYTE-IDENTICAL plain :func:`_gene_cap`
    (no field spent) — so amplifying to 1 is a clean no-op-shaped identity and a plain gene IS
    copy-number 1; only ``n >= 2`` spends the 8-byte field (the §129 dual-read discipline, one
    field over). The on-disk format version STAYS 15 (an additive field in existing padding, no
    new marker). Read the count back with :func:`copy_number_of`.

    Class-I/N exact integer (no float, never ``abs()``). C-DISPATCHED since rc281: the whole op
    has its own C entry point (``srmech_genome_amplify``), so a bare-C host can WRITE the
    copy-number axis rather than merely ignore it. (rc273 shipped this Python-only, reasoning
    that the field is TRANSPARENT to every existing C reader — true, but transparent-to-readers
    is NOT C-host parity; see ``docs/srmech/notes/c_host_parity_audit_rc273.md`` G6.) The result
    is byte-identical whether it came from the native or the pure path. Raises ``ValueError`` if
    ``n < 1`` or no plain gene named ``label`` is found in ``chrom``."""
    strand = list(chrom)
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError(
            f"amplify: n (copy number) must be an exact int (Class-I/N multiplicity); got {n!r}")
    if n < 1:
        raise ValueError(
            f"amplify: n (copy number) must be >= 1 (a gene is present at least once; a "
            f"multiplicity is never signed / never abs()); got {n}")
    # rc281 (§135 / F1251): DISPATCH to the srmech_genome_amplify C peer when the strand
    # is uniform fixed-width leaf_dim blocks. rc273 shipped this op Python-only on the
    # (true) reasoning that the copy-number field is TRANSPARENT to every existing C
    # reader — but transparent-to-readers is NOT C-host parity: without the peer a bare-C
    # host could not WRITE the axis at all. The peer does the WHOLE op (find the first
    # plain 0x47 cap by label, rewrite it, byte-copy the rest), so ADR-0003 holds. The
    # pure walk below is the numpy-free fallback + the byte-parity oracle, and it also
    # handles any non-uniform strand (e.g. a variable-width packed turn) and raises the
    # ValueErrors when the peer DECLINES (returns None).
    blocks = _leaf_blocks(strand)
    dim0 = len(blocks[0]) if blocks else 0
    if dim0 > 0 and all(len(b) == dim0 for b in blocks):
        native = _native.genome_amplify_c(b"".join(blocks), len(blocks), dim0, label, n)
        if native is not None:
            return [_hv_from_block(native[i * dim0:(i + 1) * dim0])
                    for i in range(len(blocks))]
    for i, hv in enumerate(strand):
        if _cap_kind(hv) != GENE_CAP_MARKER:
            continue                                    # only a PLAIN gene carries a copy-number
        _marker, gene_label = _unpack_cap(hv)           # label reads UNIFORMLY past any count
        if gene_label == label:
            dim = len(hv)
            strand[i] = _pack_gene_cap_copy_number(gene_label, n, dim)
            return strand
    raise ValueError(
        f"amplify: no plain gene labeled {label!r} in the strand (amplify records the copy "
        f"number on a plain GENE cap 0x47 — build one with chromosome(genes=[({label!r}, "
        f"leaves), …], coupling))")


def copy_number_of(chrom, label):
    """Read a gene's COPY NUMBER (multiplicity) — the reader companion to :func:`amplify`
    (§135/rc273 / F1251).

    Walks ``chrom`` (a chromosome / genome strand), finds the FIRST plain GENE cap (``0x47``)
    whose inline label equals ``label``, and returns its exact copy-number: the ``uint64``
    big-endian count carried RIGHT AFTER the label's NUL, or ``1`` (present-once, the DEFAULT)
    for a plain gene / a pre-rc273 genome (all-NUL padding == stored 0 == copy-number 1). So a
    gene that was never :func:`amplify`-ed — and every gene in a genome written before rc273 —
    reads as copy-number 1 (back-compat), and a gene amplified to ``n`` reads back exactly ``n``.

    ⚠️ A READ — the strand is byte-identical after this call. Class-I/N exact integer (no float,
    never ``abs()``). C-DISPATCHED since rc281 (``srmech_genome_copy_number``) — the reader half
    of the G6 parity correction, so a bare-C host can GET the axis and not just skip past it.
    Raises ``ValueError`` if no plain gene named ``label`` is found."""
    # rc281 (§135 / F1251): DISPATCH to the srmech_genome_copy_number C peer — the READ
    # half of the pair. Same rationale as amplify: before rc281 a bare-C host could not
    # GET the copy-number axis at all, only ignore it. The peer does the WHOLE op (find
    # the first plain 0x47 cap by label, read the uint64 BE field, absent -> 1). The pure
    # walk below is the fallback + the value-parity oracle and raises when it DECLINES.
    _strand = list(chrom)
    _blocks = _leaf_blocks(_strand)
    _dim0 = len(_blocks[0]) if _blocks else 0
    if _dim0 > 0 and all(len(b) == _dim0 for b in _blocks):
        _native_n = _native.genome_copy_number_c(
            b"".join(_blocks), len(_blocks), _dim0, label)
        if _native_n is not None:
            return _native_n
    for hv in chrom:
        if _cap_kind(hv) != GENE_CAP_MARKER:
            continue
        _marker, gene_label = _unpack_cap(hv)
        if gene_label == label:
            return _gene_copy_number(hv)
    raise ValueError(
        f"copy_number_of: no plain gene labeled {label!r} in the strand (the copy-number axis "
        f"is carried on a plain GENE cap 0x47; a plain / un-amplified gene reads as 1)")


def gene_express(strand, coupling, cell_state):
    """Cell-state-modulated gene expression — a READ-TIME FILTER (§128 / #728; §130 / #730).

    ``strand`` is a multi-gene chromosome (from ``chromosome(genes=…, coupling)`` /
    :func:`genome` with regulatory genes). This op walks the genes and returns ONLY the
    genes the applied ``cell_state`` EXPRESSES — dispatching on each gene's declared
    **gate_type** (§130 the dispatch FAMILY):

    * ``gate_type = klein4_mask`` (§129 E1 — the DEFAULT / FAST common case; a plain ``0x47``
      gene or a Klein-4-mask ``0x67`` regulatory gene) — the exact two-KLEIN-4-bit-plane rule::

        a gene expresses  iff  (cell_state & activator_mask) == activator_mask   # all activators PRESENT
                          and  (cell_state & repressor_mask) == 0                # no repressor PRESENT

    i.e. the gene expresses when the cell-state has ALL of the gene's activator conditions
    present AND NONE of its repressor conditions present. Per condition the ``(act_bit,
    rep_bit)`` pair is a KLEIN-4 role — don't-care ``(0,0)`` / activator ``(1,0)`` / repressor
    ``(0,1)`` / never ``(1,1)`` (a bit set in BOTH masks auto-silences the gene: present AND
    absent is a contradiction). This is the genome's NATIVE Klein-4 alphabet applied to
    regulation. The lac operon is the exemplar (activator = lactose-bit, repressor =
    glucose-bit → expresses iff lactose present AND glucose absent). A PLAIN gene (a §44 GENE
    cap ``0x47``, no masks) is UNREGULATED = ``(0, 0)`` = ALWAYS EXPRESSED — so old /
    plain-gene chromosomes always fully express (back-compat). A rc128 single-mask regulatory
    gene dual-reads as ``activator = mask, repressor = 0`` (a pure all-activator AND-gate,
    identical behaviour). A REGULATORY gene (``0x67``) carries its mask(s) INLINE and is gated.

    * ``gate_type = boolean`` (§130 E2 — the GENERAL escape hatch; a ``0x62`` boolean gene) —
      ARBITRARY boolean logic over the condition bits, encoded as a **DNF** (disjunctive normal
      form): a list of ``(require-present, require-absent)`` AND-clauses; the gene expresses iff
      ANY clause matches (``(cell_state & act) == act`` AND ``(cell_state & rep) == 0``). DNF is
      functionally complete, so ANY boolean function is representable — AND (a 1-clause
      ``[(a|b, 0)]``), OR (``[(a, 0), (b, 0)]``), NOT (``[(0, a)]``), XOR
      (``[(a, b), (b, a)]``), … **E1 ⊂ E2**: the klein4_mask ``(activator, repressor)`` two-mask
      IS exactly a 1-CLAUSE DNF, so E1 is the compact fast special case of E2's general
      disjunction. The empty DNF (0 clauses) is the OR-identity FALSE = never expresses. This is
      the GENERAL case biology's combinatorial cis-regulatory logic needs — a multi-input
      enhancer integrating several TFs (Alberts et al., *MBoC* 4th ed., "How Genetic Switches
      Work", NCBI Bookshelf NBK26872: the *Drosophila eve* gene is regulated by combinatorial
      controls — a COMBINATION of gene regulatory proteins, not a single one, sets expression).

    * ``gate_type = threshold`` (§131 E4 — the LINEAR-THRESHOLD gate; a ``0x77`` threshold gene) —
      a **perceptron**: a per-condition SIGNED integer WEIGHT vector + an integer THRESHOLD; the
      gene expresses iff ``Σᵢ (weightᵢ · bit_i(cell_state)) ≥ threshold`` (the exact integer
      weighted sum of the PRESENT conditions ≥ the threshold; the decision is the SIGN of
      ``Σ − threshold`` — a Class-K sign-branch, NEVER ``abs()``). **SIGNED weights** allow an
      inhibitory input (a repressive TF is a NEGATIVE weight). This is GENUINELY DISTINCT from E2:
      a linear-threshold function (e.g. MAJORITY-of-n = all-ones weights with ``θ = ⌈n/2⌉``, or a
      weighted morphogen dose-sum) needs an EXPONENTIALLY-large DNF, so E4 captures COMPACTLY what
      E2's DNF cannot (linear-threshold functions ⊄ small-DNF). The morphogen-gradient threshold
      model is the exemplar (Alberts et al., *MBoC* 4th ed., "Drosophila and the Molecular Genetics
      of Pattern Formation", NCBI Bookshelf NBK26906: the Dorsal morphogen "turns on or off the
      expression of different sets of genes depending on its concentration" — additive / threshold
      enhancer integration).

    THE op⊗operand THEOREM, one scale up from the rc127 active telomere: rc127 gated ONE
    divide/senesce BINARY by a carried COUNT; here the ``gene_express`` **operator** is
    MODULATED by the ``cell_state`` **operand** to gate a SELECTION over MANY genes — SAME
    DNA, DIFFERENT ``cell_state`` → DIFFERENT expressed subset. That inequality IS the
    theorem (the SAME (operand, op) pattern as :func:`srmech.amsc.op_provenance.carry` and
    :class:`srmech.amsc.coupling.RecoverableFold`, now with a CELL-STATE operand + an
    EXPRESSION operator).

    ⚠️ This is a READ — it NEVER MUTATES THE STRAND (biology does NOT rewrite DNA to
    regulate it; expression reads the regulatory region). The input ``strand`` is
    byte-identical after this call. Returns the EXPRESSED subset as ``[(gene_label,
    gene_leaves), …]`` (the same shape :func:`genes` returns, filtered) in strand order;
    ``gene_leaves`` are uncoupled through ``coupling`` (the reversible :func:`quad_turn`).

    ``cell_state`` is a non-negative exact integer (Class-I bitwise; each set bit a present
    cell-state condition; no float, never ``abs()``). Native-dispatched (byte-identical C
    peer ``srmech_genome_gene_express`` decides each gene's expression); pure Python is the
    complete alternative. Attests differential gene expression as ONE facet (genes have
    other regulation too): the CELL-TYPE-SELECTION facet — Alberts et al., *Molecular Biology
    of the Cell* 4th ed., "How Genetic Switches Work", NCBI Bookshelf NBK26872 ("Different
    selections of gene regulatory proteins are present in different cell types and thereby
    direct the patterns of gene expression that give each cell type its unique
    characteristics"); the activator/repressor (operon) model — Jacob F & Monod J (1961)
    "Genetic regulatory mechanisms in the synthesis of proteins", *J Mol Biol* 3:318-356.
    """
    if not isinstance(cell_state, int) or isinstance(cell_state, bool):
        raise ValueError(
            f"gene_express: cell_state must be an exact int (Class-I bitwise); got "
            f"{cell_state!r}")
    if cell_state < 0:
        raise ValueError(
            f"gene_express: cell_state must be non-negative (a bitmask is never signed; a "
            f"cell-state is never negated, so never abs()); got {cell_state}")
    out = []
    cur_label = None
    cur_leaves = []
    cur_express = False
    started = False
    access_open = True                          # §98 chromatin OUTER gate: euchromatin by default
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                    THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
            if started and cur_express:
                out.append((cur_label, cur_leaves))
            _marker, cur_label = _unpack_cap(hv)
            cur_leaves = []
            # §98 expressed = accessible(region) AND promoter(gene, cell_state): the chromatin
            # access gate is the OUTER gate over the §128-132 promoter (Class-K, no abs).
            cur_express = access_open and _gene_expresses(hv, cell_state)
            started = True
        elif kind == CHROMATIN_MARKER:          # §98/§98.1 access marker — gate the stretch that follows
            _an, _ad = _chromatin_access(hv, cell_state)   # §98.1/G1 cell-state-conditional access
            access_open = _an > 0               # accessible iff the level numerator > 0 (Class-K)
        elif kind in (CHROM_CAP_MARKER, KERNEL_HEADER_MARKER,
                      KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER):
            access_open = True                  # a chromosome boundary resets access (euchromatin)
            continue                            # the chromosome telomere / a header —
                                                # skip (not gene data)
        elif not started:
            continue                            # any leading cap before the first gene
        else:
            cur_leaves.append(quad_turn(hv, coupling))   # reversible uncouple
    if started and cur_express:
        out.append((cur_label, cur_leaves))
    return out


def gene_express_levels(strand, coupling, cell_state):
    """GRADED / ANALOG gene expression LEVEL — a READ-TIME FILTER (§132 / #732; the E3 rung).

    The orthogonal companion to :func:`gene_express`. Where :func:`gene_express` decides *IF* each
    gene expresses (a BINARY set — dispatching on each gene's E1/E2/E4 gate-type) and returns
    ``[(gene_label, gene_leaves), …]``, this op returns each EXPRESSED gene WITH its exact-rational
    expression **LEVEL** ``[(gene_label, gene_leaves, (num, den)), …]`` — *HOW MUCH* it expresses.
    The two reads coexist: real biology is quantitative (analog), not just on/off.

    The LEVEL axis is ORTHOGONAL to the gate-type family — it composes with EVERY gene kind:

    * a **binary** gene (a plain ``0x47`` / klein4-mask ``0x67`` / boolean ``0x62`` / threshold
      ``0x77`` gene) is the DEGENERATE graded case with levels ``{0, 1}``: it is included at LEVEL
      **exact-rational 1** (``(1, 1)`` — fully on) iff its gate PASSES (the SAME §128/§130/§131
      decision :func:`gene_express` uses), and ABSENT otherwise. So every gene :func:`gene_express`
      returns appears here at level 1, and vice versa.
    * a **graded** gene (a ``0x64`` gene, §132) carries a per-condition SIGNED integer LEVEL-WEIGHT
      vector + a POSITIVE integer DENOMINATOR; its LEVEL is the reduced exact rational
      ``Σᵢ (level_weightᵢ · bit_i(cell_state)) / denom`` CLAMPED to ``[0, 1]`` (a Class-K
      sign-branch, never ``abs()``; the fraction reduced by the Class-I gcd). The dose-response IS
      the gate: the gene is included iff its LEVEL ``> 0`` (a zero dose = off), else ABSENT.

    THE THEOREM (the op⊗operand duality, refined to a QUANTITY): the ``cell_state`` **operand**
    MODULATES the **level** the :func:`gene_express_levels` operator reports — SAME DNA, DIFFERENT
    ``cell_state`` → DIFFERENT expression LEVELS (not just a different on/off subset). A morphogen
    at a graded concentration drives a graded transcriptional output.

    ⚠️ This is a READ — it NEVER MUTATES THE STRAND (the input ``strand`` is byte-identical after
    this call; biology reads the regulatory region, it does not rewrite the DNA). Returns the
    EXPRESSED subset ``[(gene_label, gene_leaves, (num, den)), …]`` in strand order, where
    ``(num, den)`` is the reduced exact-rational level (a JSON-native 2-tuple of ints);
    ``gene_leaves`` are uncoupled through ``coupling`` (the reversible :func:`quad_turn`).

    ``cell_state`` is a non-negative exact integer (Class-I bitwise; each set bit a present
    condition; no float, never ``abs()``). Native-dispatched (byte-identical C peer
    ``srmech_genome_gene_express_levels`` computes each gene's exact-rational level); the pure
    Class-N/I integer path is the complete alternative. Attests graded / dose-response gene
    expression as ONE facet (genes have other regulation too): the amount of transcription is tuned
    quantitatively by the bound regulators — Alberts, Johnson, Lewis, Raff, Roberts & Walter,
    *Molecular Biology of the Cell* 4th ed. (Garland Science, 2002), "How Genetic Switches Work" →
    "Gene Activator Proteins Work Synergistically", NCBI Bookshelf NBK26872 (the joint effect of
    several activators on the transcription rate is "not merely the sum … but the product" — a
    graded, analog modulation of the expression level, not a binary switch).
    """
    if not isinstance(cell_state, int) or isinstance(cell_state, bool):
        raise ValueError(
            f"gene_express_levels: cell_state must be an exact int (Class-I bitwise); got "
            f"{cell_state!r}")
    if cell_state < 0:
        raise ValueError(
            f"gene_express_levels: cell_state must be non-negative (a bitmask is never signed; a "
            f"cell-state is never negated, so never abs()); got {cell_state}")
    out = []
    cur_label = None
    cur_leaves = []
    cur_level = (0, 1)
    started = False
    access = (1, 1)                             # §98 chromatin OUTER gate level: euchromatin default
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                    THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
            if started and cur_level[0] > 0:            # expressed iff level > 0
                out.append((cur_label, cur_leaves, cur_level))
            _marker, cur_label = _unpack_cap(hv)
            cur_leaves = []
            # §98 accessibility × promoter-level — the exact-rational PRODUCT (Class-N; the
            # chromatin access level composes MULTIPLICATIVELY over the §132 graded promoter level).
            cur_level = _compose_levels(access, _gene_level(hv, cell_state))
            started = True
        elif kind == CHROMATIN_MARKER:          # §98/§98.1 access marker — the stretch level that follows
            access = _chromatin_access(hv, cell_state)     # §98.1/G1 cell-state-conditional access level
        elif kind in (CHROM_CAP_MARKER, KERNEL_HEADER_MARKER,
                      KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER):
            access = (1, 1)                     # a chromosome boundary resets access (euchromatin)
            continue                            # the chromosome telomere / a header —
                                                # skip (not gene data)
        elif not started:
            continue                            # any leading cap before the first gene
        else:
            cur_leaves.append(quad_turn(hv, coupling))   # reversible uncouple
    if started and cur_level[0] > 0:
        out.append((cur_label, cur_leaves, cur_level))
    return out


def _compose_levels(a, b):
    """The exact-rational PRODUCT ``a × b`` of two reduced ``(num, den)`` levels in ``[0, 1]``,
    reduced by the Class-I gcd (§98 chromatin accessibility × §132 promoter level). Both parts are
    non-negative, so no ``abs()``; NO float. ``(0, 1)`` for a zero numerator (silenced × anything =
    silenced)."""
    num = a[0] * b[0]
    den = a[1] * b[1]
    if num == 0:
        return (0, 1)
    g = _gcd(num, den)                          # Class-I gcd (both positive; no abs)
    return (num // g, den // g)


def _gene_expresses(cap, cell_state):
    """Decide whether the gene opened by ``cap`` EXPRESSES under ``cell_state``
    (§128/§129/§130/§131) — the per-gene read-time filter shared by :func:`gene_express`,
    dispatching on the gate_type (== the cap marker). A plain GENE cap (0x47, no masks) always
    expresses ``(0, 0)``; a KLEIN-4-MASK regulatory gene (0x67) carries the two Klein-4 bit-planes
    ``(activator, repressor)`` and expresses IFF ``(cell_state & activator) == activator`` (ALL
    activators present) AND ``(cell_state & repressor) == 0`` (NO repressor present) — a 'never'
    bit (set in BOTH masks) auto-silences (present AND absent = contradiction). §130: a BOOLEAN
    gene (0x62) carries a DNF and expresses IFF ANY of its ``(act, rep)`` clauses matches (E1 ⊂ E2
    — the klein4_mask two-mask is a 1-clause DNF; the empty DNF is FALSE = never). §131: a
    THRESHOLD gene (0x77) carries a linear-threshold / perceptron gate (a SIGNED integer weight per
    condition + a threshold) and expresses IFF ``Σᵢ weightᵢ·bit_i(cell_state) ≥ threshold`` (the
    decision is the SIGN of ``Σ − threshold`` — Class-K, never ``abs()``; SIGNED weights allow an
    inhibitory input). Native-authoritative when present (byte-identical C peer
    ``srmech_genome_gene_express``); the pure Class-I/N integer path is the complete alternative.
    NO float, NEVER ``abs()``."""
    native = _gene_express_native(cap, cell_state)
    if native is not None:
        return native
    # §130/§131 GATE-TYPE DISPATCH (pure path): a THRESHOLD gene (0x77) evaluates a linear-
    # threshold / perceptron gate (E4); a BOOLEAN gene (0x62) evaluates a DNF (E2 — the general
    # escape hatch); a plain (0x47) / Klein-4-mask (0x67) gene takes the rc129 fast path (E1 — the
    # common case). Dispatch on the cap marker (== the declared gate_type).
    kind = _cap_kind(cap)
    if kind == GRADED_GENE_MARKER:
        # §132 E3: a GRADED gene's BINARY reading is level > 0 (the dose-response IS the gate —
        # a zero dose is off). The exact rational level is reported by gene_express_levels.
        num, _den = _gene_level(cap, cell_state)
        return num > 0
    if kind == THRESHOLD_GENE_MARKER:
        _gate_type, weights, threshold = _threshold_gene_spec(cap)
        return _threshold_expresses(weights, threshold, cell_state)  # Σ w·bit ≥ θ (Class-K sign)
    if kind == BOOLEAN_GENE_MARKER:
        _gate_type, dnf_terms = _boolean_gene_dnf(cap)
        return _dnf_expresses(dnf_terms, cell_state)     # express iff ANY term matches
    activator, repressor = _regulatory_gene_masks(cap)   # (0, 0) for a plain gene
    return ((cell_state & activator) == activator        # ALL activators present
            and (cell_state & repressor) == 0)           # NO repressor present; Class-I, no abs


# ─────────────────────────────────────────────────────────────────────────────
# §133/rc133 (#733) — MODULATOR-RECOVERY (M1 + M2): the INVERSE of gene_express.
# Given an OBSERVED expressed-label set (+ the strand's gene caps), recover the
# two-sided cell-state FLOOR every consistent cell_state must satisfy (M1), and
# forward-CHECK one candidate (M2). It is UNDER-DETERMINED (many cell_states ->
# the SAME expressed subset), so the ONLY honest form is a ONE-SIDED verdict — the
# op_verdict (rc117 op_provenance) EQUAL/UNKNOWN contract: recover the EXACT
# complement we can PROVE, flag the rest UNKNOWN. The exact cell_state is
# irrecoverable BY CONSTRUCTION; naming that honestly IS the finding (the same
# recoverability discipline as op_provenance / RecoverableFold / the #725 null).
# ─────────────────────────────────────────────────────────────────────────────

#: The five INTRA-chromosome gene-cap markers (plain / klein4-mask / boolean /
#: threshold / graded). A block whose first byte is one of these OPENS a gene the
#: modulator ops read; every other block (CHROM cap, kernel header, coupled data
#: turn, …) is skipped.
_GENE_MARKERS = (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                 THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER)

#: The §133 M1 verdict-code → string map (mirrors the C SRMECH_GENOME_MODULATOR_*
#: codes). One-sided, like the rc117 op_verdict EQUAL/UNKNOWN contract.
_MODULATOR_VERDICTS = {0: "UNKNOWN", 1: "PARTIAL", 2: "EXACT"}


def _weighted_ref(weights):
    """The condition bits a THRESHOLD (E4) / GRADED (E3) weight vector READS: the
    OR of ``(1 << i)`` for every NONZERO weight at index ``i < 64`` (bit ``i`` of the
    uint64 cell_state; a weight beyond index 63 gates an always-absent condition, so
    it is not "read"). Class-I bitwise; never ``abs()`` — the weight's SIGN does not
    matter to *which* bit it reads, only its being nonzero."""
    r = 0
    for i, w in enumerate(weights):
        if w != 0 and i < 64:
            r |= (1 << i)
    return r


def _gene_contribution(cap):
    """One gene cap's ``(referenced, floor_on, floor_off)`` (§133) — the per-gene
    read M1 folds. ``referenced`` = the condition bits this gene READS; ``floor_on`` /
    ``floor_off`` = the bits an EXPRESSED instance PROVES on / off (the SOUND floor):

    * E1 (plain ``0x47`` / klein4-mask ``0x67``) — ``referenced = activator | repressor``;
      an expressed E1 gene proves ``floor_on = activator`` (all present) + ``floor_off =
      repressor`` (all absent).
    * E2 (boolean DNF ``0x62``) — ``referenced`` = OR over clauses of ``(act | rep)``; an
      expressed E2 gene proves only the bits set in EVERY clause: ``floor_on`` = the
      INTERSECTION-over-clauses activator, ``floor_off`` = the intersection-over-clauses
      repressor (some clause matched, so those bits held whichever clause it was). The
      empty DNF (never expresses) proves NOTHING.
    * E4 (threshold ``0x77``) / E3 (graded ``0x64``) — ``referenced`` = the nonzero-weight
      indices; NO clean single-bit certainty, so ``floor_on = floor_off = 0`` (that is
      M3's job — do NOT over-claim). Byte-identical to the C ``genome_gene_contribution``.
    Class-I bitwise; no float; never ``abs()``; a READ."""
    kind = _cap_kind(cap)
    if kind == BOOLEAN_GENE_MARKER:
        _gate_type, terms = _boolean_gene_dnf(cap)
        ref = 0
        for act, rep in terms:
            ref |= act | rep
        if not terms:                                    # empty DNF — proves nothing
            return ref, 0, 0
        inter_act, inter_rep = terms[0]
        for act, rep in terms[1:]:
            inter_act &= act
            inter_rep &= rep
        return ref, inter_act, inter_rep
    if kind == THRESHOLD_GENE_MARKER:
        _gate_type, weights, _threshold = _threshold_gene_spec(cap)
        return _weighted_ref(weights), 0, 0              # E4 — ref only
    if kind == GRADED_GENE_MARKER:
        _gate_type, weights, _denom = _graded_gene_spec(cap)
        return _weighted_ref(weights), 0, 0              # E3 — ref only
    activator, repressor = _regulatory_gene_masks(cap)   # E1 (0x47 / 0x67); (0,0) for plain
    return activator | repressor, activator, repressor


def _modulator_recover_pure(strand, labels):
    """The pure Class-I path for :func:`modulator_recover` — recover the two-sided
    floor by walking the strand's gene caps. A gene's floor is applied only when its
    label is EXPRESSED (in ``labels``) AND UNIQUE among the strand's gene caps (a
    duplicated label cannot be attributed to a specific gene — the expressed SET
    collapses duplicates — so NEITHER contributes: SOUND). Byte-identical to the C
    ``srmech_genome_modulator_recover``. No float; never ``abs()``; a READ."""
    expressed_set = set(labels)
    gene_caps = [hv for hv in strand if _cap_kind(hv) in _GENE_MARKERS]
    cap_labels = [_unpack_cap(hv)[1] for hv in gene_caps]
    on = off = ref = 0
    for hv, lab in zip(gene_caps, cap_labels):
        gref, gon, goff = _gene_contribution(hv)
        ref |= gref                                      # every gene reads its bits
        if lab in expressed_set and cap_labels.count(lab) == 1:
            on |= gon                                    # SOUND: proven bits only
            off |= goff
    pinned = on | off
    undetermined = ref & ~pinned                         # referenced bits not pinned
    if pinned == 0:
        verdict = "UNKNOWN"                              # nothing pinned
    elif undetermined == 0:
        verdict = "EXACT"                                # the floor pins every referenced bit
    else:
        verdict = "PARTIAL"
    return {"certain_on": on, "certain_off": off,
            "undetermined": undetermined, "verdict": verdict}


def _modulator_labels(expressed_labels, fn):
    """Coerce ``expressed_labels`` to a ``list[str]`` (the gene-label vocabulary) —
    rejecting a bare ``str`` / ``bytes`` (a common footgun: a single label string is
    NOT a label SET)."""
    if isinstance(expressed_labels, (str, bytes)):
        raise ValueError(
            f"{fn}: expressed_labels must be a SEQUENCE of gene labels (e.g. a list "
            f"of str), not a single {type(expressed_labels).__name__}")
    return [str(label) for label in expressed_labels]


def _modulator_gene_body(strand):
    """The GENE-CAP subset of ``strand`` as one fixed-width byte body (each gene cap
    ``leaf_dim`` bytes; the data turns do NOT gate expression, so they are stripped) —
    the buffer the whole-strand C peers walk uniformly."""
    return b"".join(hv.tobytes() for hv in strand if _cap_kind(hv) in _GENE_MARKERS)


def _modulator_recover_native(strand, coupling, labels):
    """Native dispatch for :func:`modulator_recover` (parity peer
    ``srmech_genome_modulator_recover``): returns the floor dict, or ``None`` on any
    missing symbol / non-OK status / a label carrying a NUL (the blob delimiter) — the
    caller runs the pure path. Native is authoritative when present."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_genome_modulator_recover")):
        return None
    if any("\x00" in label for label in labels):
        return None
    blob = b"".join(label.encode("utf-8") + b"\x00" for label in dict.fromkeys(labels))
    body = _modulator_gene_body(strand)
    leaf_dim = len(list(coupling))
    try:
        on, off, und, verdict = _native.genome_modulator_recover_c(body, leaf_dim, blob)
    except _native.NativeGenomeError:
        return None
    return {"certain_on": on, "certain_off": off, "undetermined": und,
            "verdict": _MODULATOR_VERDICTS[verdict]}


def _modulator_consistent_native(strand, coupling, labels, candidate):
    """Native dispatch for :func:`modulator_consistent` (parity peer
    ``srmech_genome_modulator_consistent``): returns ``"CONSISTENT"``/``"INCONSISTENT"``,
    or ``None`` on any missing symbol / non-OK status (e.g. an int64 threshold-sum
    OVERFLOW) / a candidate beyond the native uint64 domain / a NUL in a label — the
    caller runs the pure path. Native is authoritative when present."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_genome_modulator_consistent")):
        return None
    if candidate < 0 or candidate >= (1 << 64):          # the native cell_state is uint64
        return None
    if any("\x00" in label for label in labels):
        return None
    blob = b"".join(label.encode("utf-8") + b"\x00" for label in dict.fromkeys(labels))
    body = _modulator_gene_body(strand)
    leaf_dim = len(list(coupling))
    try:
        consistent = _native.genome_modulator_consistent_c(body, leaf_dim, blob, candidate)
    except _native.NativeGenomeError:
        return None
    return "CONSISTENT" if consistent else "INCONSISTENT"


def modulator_recover(strand, coupling, expressed_labels):
    """Recover the TWO-SIDED cell-state FLOOR from an OBSERVED expressed set — M1, the
    INVERSE of :func:`gene_express` (§133 / #733).

    :func:`gene_express` is the FORWARD map (cell_state → expressed genes). This is the
    beginning of the INVERSE: GIVEN the observed ``expressed_labels`` (+ the strand's
    gene regulatory specs), recover what EVERY cell_state that could have produced that
    expression must look like. It is UNDER-DETERMINED (many cell_states → the same
    expressed subset), so the exact cell_state is IRRECOVERABLE BY CONSTRUCTION — the
    only honest form is the ONE-SIDED FLOOR, the same recoverability discipline as
    :func:`srmech.amsc.op_provenance.op_provenance_hash`'s op_verdict EQUAL/UNKNOWN
    contract, :class:`srmech.amsc.coupling.RecoverableFold`, and the #725 null:
    **recover the EXACT complement we can PROVE, flag the rest UNKNOWN.**

    The floor (sharpened by the rc129 activator/repressor two-mask):

    * **certain_on** — the bits EVERY consistent cell_state MUST have SET. SOUND
      contributors: each EXPRESSED **E1** gene (klein4-mask ``0x67`` / plain ``0x47``)
      proves its activator bits are on → OR their activator masks. Each EXPRESSED **E2**
      gene (boolean DNF ``0x62``) proves ≥ 1 clause matched → the bits set in EVERY
      clause's activator (the INTERSECTION-over-clauses activator) are certain-on.
    * **certain_off** — the bits every consistent state MUST have CLEAR: OR of expressed
      E1 repressor masks + the intersection-over-clauses repressor of expressed E2 genes.
    * **E4 threshold / E3 graded / UN-expressed genes contribute NOTHING** to the clean
      floor (a failed threshold / an absent gene is a DISJUNCTION of conditions — no clean
      single-bit certainty; that is M3's job). Do NOT over-claim from them.
    * **undetermined** — the referenced condition bits (the union of bits ANY gene reads)
      minus ``certain_on ∪ certain_off``.
    * **verdict** — ``"EXACT"`` if ``certain_on ∪ certain_off`` covers ALL referenced bits
      (the floor fully determines the state), ``"PARTIAL"`` if some bits are pinned,
      ``"UNKNOWN"`` if none — mirroring op_verdict's one-sidedness (NEVER claim a bit's
      value it can't prove).

    **SOUNDNESS (the load-bearing contract):** for EVERY cell_state that
    :func:`modulator_consistent` reports CONSISTENT with ``expressed_labels``,
    ``(state & certain_on) == certain_on`` AND ``(state & certain_off) == 0``. A gene's
    floor is applied only when its label is expressed AND UNIQUE among the strand's gene
    caps (a duplicated label cannot be attributed → neither contributes). M1 NEVER
    over-claims a bit.

    ⚠️ A READ — never mutates the strand (the input is byte-identical after). ``coupling``
    is the leaf-width anchor (M1 reads only the gene CAPS, which are not coupled).
    ``expressed_labels`` is a sequence of gene-label strings. Returns
    ``{"certain_on": int, "certain_off": int, "undetermined": int, "verdict": str}``
    (all JSON-native). Native-dispatched (byte-identical C peer
    ``srmech_genome_modulator_recover``); the pure Class-I path is the complete
    alternative. Attests gene-regulatory-network (GRN) inference — reverse-engineering the
    regulatory state from an expression pattern — as ONE FACET of a real
    biological-computational problem (the inverse of expression; #728 discipline — NOT a
    claim srmech reproduces it): Marbach D, Costello JC, Küffner R, et al., "Wisdom of
    crowds for robust gene network inference", *Nature Methods* 9(8):796-804 (2012), DOI
    10.1038/nmeth.2016 (OA: NIH PMC3512113) — the DREAM5 blind assessment of GRN-inference
    methods."""
    labels = _modulator_labels(expressed_labels, "modulator_recover")
    native = _modulator_recover_native(strand, coupling, labels)
    if native is not None:
        return native
    return _modulator_recover_pure(strand, labels)


def modulator_consistent(strand, coupling, expressed_labels, candidate_cell_state):
    """Forward-CHECK one candidate cell_state — M2, the consistency verdict (§133 / #733).

    Is ``candidate_cell_state`` a cell_state that could have produced ``expressed_labels``?
    Runs the FORWARD :func:`gene_express` on the candidate and compares the produced label
    SET to the observed one::

        set(labels of gene_express(strand, coupling, candidate)) == set(expressed_labels)

    → ``"CONSISTENT"`` else ``"INCONSISTENT"``. **ONE-SIDED** (the op_verdict EQUAL/UNKNOWN
    reuse): CONSISTENT means "could be the state" (MANY candidates may be — expression is
    under-determined), NEVER "it IS the state". Reuses the forward :func:`gene_express`
    (no new gate logic), so it dispatches on each gene's E1/E2/E4 gate-type exactly as the
    forward map does. Pairs with :func:`modulator_recover`: M1's floor is SOUND precisely
    because every state M2 calls CONSISTENT satisfies it.

    ⚠️ A READ — never mutates the strand. ``candidate_cell_state`` is a non-negative exact
    int (Class-I bitwise; each set bit a present condition; no float, never ``abs()``).
    Native-dispatched (byte-identical C peer ``srmech_genome_modulator_consistent``); the
    pure path (reusing :func:`gene_express`) is the complete alternative. Attests
    GRN-inference / consistency-checking of a candidate regulatory state as ONE FACET (the
    inverse of expression; #728 discipline — NOT a claim srmech reproduces it): Marbach et
    al., *Nature Methods* 9(8):796-804 (2012), DOI 10.1038/nmeth.2016 (OA: NIH
    PMC3512113)."""
    if not isinstance(candidate_cell_state, int) or isinstance(candidate_cell_state, bool):
        raise ValueError(
            f"modulator_consistent: candidate_cell_state must be an exact int (Class-I "
            f"bitwise); got {candidate_cell_state!r}")
    if candidate_cell_state < 0:
        raise ValueError(
            f"modulator_consistent: candidate_cell_state must be non-negative (a bitmask "
            f"is never signed, so never abs()); got {candidate_cell_state}")
    labels = _modulator_labels(expressed_labels, "modulator_consistent")
    native = _modulator_consistent_native(strand, coupling, labels, candidate_cell_state)
    if native is not None:
        return native
    produced = {lab for lab, _leaves in gene_express(strand, coupling, candidate_cell_state)}
    return "CONSISTENT" if produced == set(labels) else "INCONSISTENT"


# ─────────────────────────────────────────────────────────────────────────────
# §133/rc134 (#733) — MODULATOR-CONSTRAINT (M3): the COMPLETE inverse of
# gene_express. Where M1 (modulator_recover) gives the SOUND two-sided FLOOR
# from the EXPRESSED genes and M2 (modulator_consistent) forward-CHECKS one
# candidate, M3 returns the EXACT CONSTRAINT characterizing the WHOLE set of
# cell-states consistent with an observed expression — as a COMPACT structured
# constraint, NEVER an enumeration (the solution set can be exponential). It adds
# what M1 left out: (a) the DISJUNCTIVE clauses from UN-expressed genes (an
# un-expressed E1 gene proves "some activator absent OR some repressor present" =
# a nand-clause; an un-expressed E2 gene ANDs one nand-clause per DNF term); (b)
# the FULL expressed-E2 disjunction (M1 only took the sound clause-intersection);
# (c) the general-gate inverse (E4 threshold -> a linear inequality; E3 graded ->
# a level constraint). The exact cell_state is still NOT unique — but the
# CONSTRAINT is the EXACT characterization of the consistent set, and the residual
# multiplicity is the honest-irrecoverability (the op_verdict / #725 discipline).
#
# SOUND: every M2-consistent cell_state satisfies the constraint. COMPLETE
# (satisfies <=> M2-consistent) for the BOOLEAN gate-types E1/E2 at ANY label
# multiplicity AND for a UNIQUE-labelled single E4/E3 gene; SOUND-ONLY (an
# over-approximation, HONESTLY FLAGGED in `sound_only_labels`) for an EXPRESSED
# label that is a genuine CROSS-TYPE disjunction (a duplicated label whose genes
# span boolean AND threshold/graded, or >= 2 threshold/graded genes) — that OR
# has no exact flat-clause form, so its expressed requirement is DROPPED to stay
# sound. Un-expressed labels are COMPLETE for every gate-type (a conjunction of
# exact silence constraints). Class-I bitwise; Class-N for the level/inequality
# integer sums; the inequality SENSE is a Class-K sign-branch (never abs()).
# ─────────────────────────────────────────────────────────────────────────────

#: The exact-satisfiability decision bound (M3). When the count of FREE (referenced
#: but unpinned) condition bits is <= this, `satisfiable` is decided EXACTLY by a
#: bounded search over those bits (an INTERNAL boolean decision — NEVER a returned
#: enumeration; the returned constraint stays compact). Beyond it, `satisfiable`
#: falls back to the SOUND contradiction-detectors (False is always a proof of
#: unsatisfiability; True means "no contradiction proven" — always correct for a
#: real, came-from-a-state expression).
_MODULATOR_SAT_EXACT_BITS = 20


def _popcount(x):
    """The number of set bits of a non-negative int (Class-I bit tally; no float,
    never ``abs()`` — a bitmask is unsigned)."""
    return bin(x).count("1")


def _gene_bool_terms(cap):
    """The list of boolean AND-terms ``[(activator, repressor), …]`` the gene opened
    by ``cap`` contributes (§133 M3). An E1 gene (plain ``0x47`` -> ``(0, 0)`` / klein4-
    mask ``0x67``) is ONE term (its two Klein-4 bit-planes); an E2 boolean gene
    (``0x62``) is its DNF term list (possibly empty = never expresses). A THRESHOLD
    (``0x77``) / GRADED (``0x64``) gene contributes NO boolean term (``[]`` — it is a
    linear-inequality / level constraint, not a mask-clause). Class-I bitwise; a READ."""
    kind = _cap_kind(cap)
    if kind == BOOLEAN_GENE_MARKER:
        _gate_type, terms = _boolean_gene_dnf(cap)
        return list(terms)
    if kind in (THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
        return []                                        # not a boolean mask-clause
    return [_regulatory_gene_masks(cap)]                 # E1 (0x47 -> (0,0) / 0x67)


def _label_has_nonbool(gene_caps, cap_labels, label):
    """Does ``label`` open ANY THRESHOLD (``0x77``) / GRADED (``0x64``) gene cap in the
    strand (§133 M3)? The soundness guard for the expressed-disjunction clause: a
    label that mixes a boolean gene with a threshold/graded gene is a CROSS-TYPE OR
    with no exact flat-clause form, so its boolean terms must NOT be forced (that
    would reject a state that expresses the label via the threshold/graded branch).
    Byte-identical to the C ``genome_label_has_nonbool``. Class-I; a READ."""
    for hv, lab in zip(gene_caps, cap_labels):
        if lab == label and _cap_kind(hv) in (THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
            return True
    return False


def _modulator_constraint_bool_pure(strand, labels):
    """The pure Class-I path for the BOOLEAN part of :func:`modulator_constraint`
    (§133 M3) — the floor (from M1) + the disjunctive CLAUSES. Returns
    ``(certain_on, certain_off, nand_list, or_list)``:

    * ``certain_on`` / ``certain_off`` — M1's SOUND floor (reuses
      :func:`_modulator_recover_pure`; the pinned bits from EXPRESSED UNIQUE E1/E2
      genes).
    * ``nand_list`` — ``[(any_absent, any_present), …]``, one per boolean AND-term of
      each UN-expressed E1/E2 gene (in strand order, term order). Each means
      "(some bit of any_absent is 0) OR (some bit of any_present is 1)" = the
      NEGATION of that AND-term matching = the gene NOT expressing. ALL are ANDed
      (an un-expressed gene must have EVERY clause fail).
    * ``or_list`` — ``[[(present, absent), …], …]``, one per EXPRESSED **pure-boolean**
      label with >= 2 boolean terms (in first-occurrence label order); the label
      expresses iff >= 1 of its terms fully matches (all present-bits set AND all
      absent-bits clear) — the FULL disjunction M1 only intersected. A pure-boolean
      label with a SINGLE term is already pinned by the floor (no clause). A label
      that ALSO opens a threshold/graded cap is a CROSS-TYPE OR (sound-only) — NO
      or-clause is emitted for it (the :func:`_label_has_nonbool` guard).

    Byte-identical to the C ``srmech_genome_modulator_constraint`` boolean emit
    (the SAME strand walk + first-occurrence label order). No float; never
    ``abs()``; a READ."""
    expressed_set = set(labels)
    gene_caps = [hv for hv in strand if _cap_kind(hv) in _GENE_MARKERS]
    cap_labels = [_unpack_cap(hv)[1] for hv in gene_caps]
    floor = _modulator_recover_pure(strand, labels)
    on, off = floor["certain_on"], floor["certain_off"]
    # nand clauses — every UN-expressed E1/E2 gene, in strand order, term order.
    nand_list = []
    for hv, lab in zip(gene_caps, cap_labels):
        if lab in expressed_set:
            continue
        if _cap_kind(hv) in (THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
            continue                                     # not boolean -> an inequality/level
        for act, rep in _gene_bool_terms(hv):
            nand_list.append((act, rep))                 # (some act absent) OR (some rep present)
    # or clauses — each EXPRESSED pure-boolean label (>= 2 terms), first-occurrence order.
    or_list = []
    seen = set()
    for hv, lab in zip(gene_caps, cap_labels):
        if lab in seen:
            continue
        seen.add(lab)
        if lab not in expressed_set:
            continue
        if _label_has_nonbool(gene_caps, cap_labels, lab):
            continue                                     # CROSS-TYPE OR — sound-only, no clause
        terms = []
        for hv2, lab2 in zip(gene_caps, cap_labels):
            if lab2 == lab:
                terms.extend(_gene_bool_terms(hv2))
        if len(terms) >= 2:
            or_list.append(list(terms))                  # the FULL expressed disjunction
    return on, off, nand_list, or_list


def _serialize_bool_constraint(on, off, nand_list, or_list):
    """Canonically serialize the boolean part of an M3 constraint to bytes (§133) —
    the byte-form both the pure Python path and the C peer emit, so Python==C is a
    byte-equality check. Layout (all big-endian, unsigned):

    ``certain_on(u64) certain_off(u64) n_nand(u32) [any_absent(u64) any_present(u64)]*
    n_or(u32) [n_terms(u32) [present(u64) absent(u64)]*]*``. Class-I; no float."""
    out = bytearray()
    out += int(on).to_bytes(8, "big")
    out += int(off).to_bytes(8, "big")
    out += len(nand_list).to_bytes(4, "big")
    for a, p in nand_list:
        out += int(a).to_bytes(8, "big")
        out += int(p).to_bytes(8, "big")
    out += len(or_list).to_bytes(4, "big")
    for terms in or_list:
        out += len(terms).to_bytes(4, "big")
        for pr, ab in terms:
            out += int(pr).to_bytes(8, "big")
            out += int(ab).to_bytes(8, "big")
    return bytes(out)


def _deserialize_bool_constraint(buf):
    """Parse the M3 boolean-constraint byte-form back to
    ``(certain_on, certain_off, nand_list, or_list)`` — the inverse of
    :func:`_serialize_bool_constraint` (used to lift the C peer's emitted bytes into
    the Python structure). Raises ``ValueError`` on a truncated buffer."""
    if len(buf) < 20:
        raise ValueError("M3 boolean-constraint buffer truncated (header)")
    on = int.from_bytes(buf[0:8], "big")
    off = int.from_bytes(buf[8:16], "big")
    n_nand = int.from_bytes(buf[16:20], "big")
    pos = 20
    nand_list = []
    for _ in range(n_nand):
        if pos + 16 > len(buf):
            raise ValueError("M3 boolean-constraint buffer truncated (nand)")
        a = int.from_bytes(buf[pos:pos + 8], "big")
        p = int.from_bytes(buf[pos + 8:pos + 16], "big")
        nand_list.append((a, p))
        pos += 16
    if pos + 4 > len(buf):
        raise ValueError("M3 boolean-constraint buffer truncated (n_or)")
    n_or = int.from_bytes(buf[pos:pos + 4], "big")
    pos += 4
    or_list = []
    for _ in range(n_or):
        if pos + 4 > len(buf):
            raise ValueError("M3 boolean-constraint buffer truncated (or n_terms)")
        n_terms = int.from_bytes(buf[pos:pos + 4], "big")
        pos += 4
        terms = []
        for _t in range(n_terms):
            if pos + 16 > len(buf):
                raise ValueError("M3 boolean-constraint buffer truncated (or term)")
            pr = int.from_bytes(buf[pos:pos + 8], "big")
            ab = int.from_bytes(buf[pos + 8:pos + 16], "big")
            terms.append((pr, ab))
            pos += 16
        or_list.append(terms)
    return on, off, nand_list, or_list


def _modulator_constraint_native(strand, coupling, labels):
    """Native dispatch for the BOOLEAN part of :func:`modulator_constraint` (parity
    peer ``srmech_genome_modulator_constraint``): returns the emitted
    boolean-constraint bytes, or ``None`` on any missing symbol / non-OK status / a
    label with a NUL — the caller runs the pure path. Native is authoritative when
    present (the bytes are byte-identical to :func:`_serialize_bool_constraint` of the
    pure result)."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_genome_modulator_constraint")):
        return None
    if any("\x00" in label for label in labels):
        return None
    blob = b"".join(label.encode("utf-8") + b"\x00" for label in dict.fromkeys(labels))
    body = _modulator_gene_body(strand)
    leaf_dim = len(list(coupling))
    try:
        return _native.genome_modulator_constraint_c(body, leaf_dim, blob)
    except _native.NativeGenomeError:
        return None


def _satisfies_bool(on, off, clauses, cs):
    """Does ``cs`` satisfy the BOOLEAN part of an M3 constraint (§133) — the floor pins
    + every nand / or_terms clause (ALL ANDed)? Class-I bitwise; a READ; no abs."""
    if (cs & on) != on:
        return False                                     # a certain-on bit is clear
    if (cs & off) != 0:
        return False                                     # a certain-off bit is set
    for cl in clauses:
        if cl["kind"] == "nand":
            a, p = cl["any_absent"], cl["any_present"]
            if not ((cs & a) != a or (cs & p) != 0):     # the AND-term matched -> gene expressed
                return False
        else:                                            # or_terms — >= 1 term must fully match
            if not any((cs & t["present"]) == t["present"] and (cs & t["absent"]) == 0
                       for t in cl["terms"]):
                return False
    return True


def _satisfies_full(constraint, cs):
    """Does ``cs`` satisfy the WHOLE M3 constraint (§133) — the boolean part (floor +
    clauses) AND every inequality (E4) AND every level (E3)? This is the runnable
    predicate behind :func:`modulator_constraint_satisfies`; on the COMPLETE gate-types
    it EQUALS ``modulator_consistent(...) == "CONSISTENT"`` exactly. The inequality /
    level tests sum the SIGNED integer weights over the PRESENT condition bits (Class-N
    exact) and branch on the SIGN of ``(sum - threshold)`` — a Class-K sign, never
    ``abs()``."""
    if not _satisfies_bool(constraint["certain_on"], constraint["certain_off"],
                           constraint["clauses"], cs):
        return False
    for ineq in constraint["inequalities"]:
        weights = ineq["weights"]
        total = 0
        for i, w in enumerate(weights):                  # Sum w_i * bit_i(cs), Class-N exact
            if (cs >> i) & 1:
                total += w
        if ineq["sense"] == ">=":                        # E4 EXPRESSED: Sum >= threshold
            if total < ineq["threshold"]:                # Class-K sign of (total - threshold)
                return False
        else:                                            # sense "<" — E4 UN-expressed: Sum < threshold
            if total >= ineq["threshold"]:
                return False
    for lv in constraint["levels"]:
        weights = lv["weights"]
        total = 0
        for i, w in enumerate(weights):                  # the graded dose Sum w_i * bit_i(cs)
            if (cs >> i) & 1:
                total += w
        if lv["positive"]:                               # E3 EXPRESSED: level > 0 <=> dose >= 1
            if total < 1:
                return False
        else:                                            # E3 UN-expressed: level == 0 <=> dose <= 0
            if total > 0:
                return False
    return True


def _modulator_satisfiable(on, off, clauses, inequalities, levels,
                           expressed_set, cap_label_set, free, free_bits):
    """Decide `satisfiable` for an M3 constraint (§133) — is there SOME cell_state that
    satisfies it? Returns ``(bool, note)``. FALSE is always a PROOF of unsatisfiability
    (the sound contradiction-detectors below never fire on a real, came-from-a-state
    expression); when the count of FREE (referenced-but-unpinned) bits is within the
    exact bound it is decided EXACTLY by an INTERNAL bounded search over those bits
    (NEVER a returned enumeration — the returned constraint stays compact). Beyond the
    bound, TRUE means "no contradiction proven" (correct for any real expression), and
    the note says so. Class-I bitwise; no abs."""
    # ---- sound contradiction detectors (FALSE is a proof) ----
    if (on & off) != 0:
        return False, "pin-contradiction (a condition bit is required both SET and CLEAR)"
    for lab in expressed_set:
        if lab not in cap_label_set:
            return False, "an expected label has no gene in the strand (can never be produced)"
    for cl in clauses:
        if cl["kind"] == "or_terms" and len(cl["terms"]) == 0:
            return False, "an expressed label has an empty disjunction (can never express)"
        if cl["kind"] == "nand" and cl["any_absent"] == 0 and cl["any_present"] == 0:
            return False, "an always-on gene is required silent (can never be un-expressed)"
    # ---- exact bounded decision over the FREE referenced bits ----
    if free_bits <= _MODULATOR_SAT_EXACT_BITS:
        cst = {"certain_on": on, "certain_off": off, "clauses": clauses,
               "inequalities": inequalities, "levels": levels}
        positions = [i for i in range(free.bit_length()) if (free >> i) & 1]
        for assign in range(1 << len(positions)):
            cs = on
            for k, pos in enumerate(positions):
                if (assign >> k) & 1:
                    cs |= (1 << pos)
            if _satisfies_full(cst, cs):
                return True, f"exact (a witness exists among the {free_bits} free referenced bit(s))"
        return False, f"exact (no assignment of the {free_bits} free referenced bit(s) satisfies it)"
    return (True, f"conservative ({free_bits} free bits exceed the exact-decision bound "
                  f"{_MODULATOR_SAT_EXACT_BITS}; True = no contradiction proven, not a witness)")


def modulator_constraint(strand, coupling, expressed_labels):
    """The COMPLETE inverse of :func:`gene_express` — M3, the EXACT CONSTRAINT
    characterizing the WHOLE set of cell-states consistent with an observed
    expression (§133 / #733; the last rung of the E-M ladder).

    M1 (:func:`modulator_recover`) gives the SOUND two-sided FLOOR from the EXPRESSED
    genes; M2 (:func:`modulator_consistent`) forward-checks one candidate. **M3
    returns the EXACT constraint** — a COMPACT structured object, NEVER an
    enumeration (the consistent set can be exponential). It adds what M1 left out:

    * **UN-expressed genes.** An un-expressed **E1** gene (activator ``a``, repressor
      ``r``) PROVES ``(cs & a) != a`` OR ``(cs & r) != 0`` (some activator absent OR
      some repressor present) — a DISJUNCTIVE ``nand`` clause. An un-expressed **E2**
      gene ANDs one ``nand`` clause per DNF term (all clauses must fail).
    * **The FULL expressed-E2 disjunction.** M1 only took the SOUND
      intersection-over-clauses; M3 adds the exact ``or_terms`` disjunction (an
      expressed label with >= 2 boolean terms expresses iff >= 1 term fully matches).
    * **The general-gate inverse.** An EXPRESSED **E4** threshold gene ->
      ``Sum wᵢ·bit_i(cs) >= θ`` (a linear inequality); UN-expressed -> ``Sum < θ``. An
      **E3** graded gene EXPRESSED -> ``Sum wᵢ·bit_i(cs) >= 1`` (level > 0), UN-expressed
      -> ``Sum <= 0`` (level 0). These are CONSTRAINT-SATISFACTION, not a mask-OR.

    Returns a JSON-native ``dict``::

        {"certain_on": int, "certain_off": int,          # M1's floor (the pinned bits)
         "clauses": [{"kind": "nand", "any_absent": int, "any_present": int}
                     | {"kind": "or_terms", "terms": [{"present": int, "absent": int}, …]}, …],
         "inequalities": [{"weights": [int, …], "threshold": int, "sense": ">=" | "<"}, …],
         "levels": [{"weights": [int, …], "denom": int, "positive": bool}, …],
         "satisfiable": bool, "free_bits": int, "solution_note": str,
         "sound_complete": bool, "sound_only_labels": [str, …]}

    All ``clauses`` / ``inequalities`` / ``levels`` are ANDed (a conjunction); a
    ``cs`` satisfies the constraint iff it satisfies EVERY one (run
    :func:`modulator_constraint_satisfies` to check a candidate).

    **SOUND** — every ``cs`` that :func:`modulator_consistent` reports CONSISTENT with
    ``expressed_labels`` satisfies the returned constraint. **COMPLETE** (``satisfies``
    <=> M2-CONSISTENT) for the **boolean** gate-types **E1/E2** at ANY label
    multiplicity, and for a **unique single E4/E3** gene; **SOUND-ONLY** (an
    over-approximation, HONESTLY reported in ``sound_only_labels`` with
    ``sound_complete = False``) for an EXPRESSED label that is a genuine CROSS-TYPE
    disjunction (a duplicated label spanning boolean AND threshold/graded, or >= 2
    threshold/graded genes) — that OR has no exact flat-clause form, so its expressed
    requirement is DROPPED to stay sound. UN-expressed labels are COMPLETE for EVERY
    gate-type (a conjunction of exact silence constraints).

    ``satisfiable`` is ``True`` iff SOME cell-state satisfies the constraint (a real,
    came-from-a-state expression is always satisfiable; a hand-supplied inconsistent
    expressed set — e.g. two genes that can't co-express — is ``False``): FALSE is
    always a PROOF (the sound detectors), and within the free-bit bound it is decided
    EXACTLY (see ``solution_note``). ``free_bits`` = the count of referenced-but-unpinned
    condition bits; ``solution_note`` characterizes the solution-set SIZE HONESTLY and
    NEVER enumerates it.

    ⚠️ A READ — never mutates the strand (byte-identical after). ``coupling`` is the
    leaf-width anchor (M3 reads only the gene CAPS). Native-dispatched: the C peer
    ``srmech_genome_modulator_constraint`` emits the BOOLEAN part (floor + clauses)
    byte-identically; the inequalities / levels / satisfiability are computed in the
    exact pure Class-N/I path (the owed-C is the E4/E3 emit). Class-I bitwise; Class-N
    for the integer sums; the inequality SENSE is a Class-K sign (never ``abs()``).
    Attests gene-regulatory-network (GRN) inference — inferring the COMPLETE
    regulatory-input constraint from an expression profile, a constraint-satisfaction
    view of the inverse problem — as ONE FACET (#728 discipline, NOT a claim srmech
    reproduces it): Marbach D, Costello JC, Küffner R, et al., "Wisdom of crowds for
    robust gene network inference", *Nature Methods* 9(8):796-804 (2012), DOI
    10.1038/nmeth.2016 (OA: NIH PMC3512113) — the DREAM5 blind assessment of
    GRN-inference methods."""
    labels = _modulator_labels(expressed_labels, "modulator_constraint")
    expressed_set = set(labels)
    # ---- boolean part (floor + clauses): native (byte-identical) or pure ----
    native_bytes = _modulator_constraint_native(strand, coupling, labels)
    if native_bytes is not None:
        on, off, nand_list, or_list = _deserialize_bool_constraint(native_bytes)
    else:
        on, off, nand_list, or_list = _modulator_constraint_bool_pure(strand, labels)
    clauses = []
    for a, p in nand_list:
        clauses.append({"kind": "nand", "any_absent": a, "any_present": p})
    for terms in or_list:
        clauses.append({"kind": "or_terms",
                        "terms": [{"present": pr, "absent": ab} for pr, ab in terms]})
    # ---- referenced bits + per-label gate-type families (for sound-only + E4/E3) ----
    gene_caps = [hv for hv in strand if _cap_kind(hv) in _GENE_MARKERS]
    cap_labels = [_unpack_cap(hv)[1] for hv in gene_caps]
    referenced = 0
    families = {}                                        # label -> [n_bool_terms, n_thr, n_grad]
    for hv, lab in zip(gene_caps, cap_labels):
        gref, _gon, _goff = _gene_contribution(hv)
        referenced |= gref
        fam = families.setdefault(lab, [0, 0, 0])
        kind = _cap_kind(hv)
        if kind == THRESHOLD_GENE_MARKER:
            fam[1] += 1
        elif kind == GRADED_GENE_MARKER:
            fam[2] += 1
        else:
            fam[0] += len(_gene_bool_terms(hv))
    # ---- inequalities (E4) + levels (E3), respecting the sound-only guard ----
    inequalities = []
    levels = []
    for hv, lab in zip(gene_caps, cap_labels):
        kind = _cap_kind(hv)
        if kind == THRESHOLD_GENE_MARKER:
            _gt, weights, threshold = _threshold_gene_spec(hv)
            nb, nt, ng = families[lab]
            if lab not in expressed_set:                 # UN-expressed: MANDATORY, complete
                inequalities.append({"weights": list(weights), "threshold": threshold,
                                     "sense": "<"})
            elif nb == 0 and nt == 1 and ng == 0:        # EXPRESSED pure single threshold: complete
                inequalities.append({"weights": list(weights), "threshold": threshold,
                                     "sense": ">="})
            # else EXPRESSED sound-only cross-type OR -> drop (flagged), stay sound
        elif kind == GRADED_GENE_MARKER:
            _gt, weights, _denom = _graded_gene_spec(hv)
            nb, nt, ng = families[lab]
            if lab not in expressed_set:                 # UN-expressed: MANDATORY, complete
                levels.append({"weights": list(weights), "denom": _denom, "positive": False})
            elif nb == 0 and nt == 0 and ng == 1:        # EXPRESSED pure single graded: complete
                levels.append({"weights": list(weights), "denom": _denom, "positive": True})
            # else EXPRESSED sound-only -> drop (flagged), stay sound
    # ---- sound-only labels: EXPRESSED labels that are NOT a complete case ----
    sound_only = []
    for lab in dict.fromkeys(cap_labels):                # first-occurrence, de-duplicated
        if lab not in expressed_set:
            continue                                     # UN-expressed is always complete
        nb, nt, ng = families[lab]
        complete = ((nt == 0 and ng == 0)                # pure boolean (any multiplicity)
                    or (nb == 0 and nt == 1 and ng == 0)  # a single threshold
                    or (nb == 0 and nt == 0 and ng == 1))  # a single graded
        if not complete:
            sound_only.append(lab)
    sound_complete = (len(sound_only) == 0)
    # ---- size note (never enumerate) + satisfiability ----
    pinned = on | off
    free = referenced & ~pinned
    free_bits = _popcount(free)
    satisfiable, sat_note = _modulator_satisfiable(
        on, off, clauses, inequalities, levels, expressed_set, set(cap_labels), free, free_bits)
    n_nand = sum(1 for c in clauses if c["kind"] == "nand")
    n_or = sum(1 for c in clauses if c["kind"] == "or_terms")
    solution_note = (
        f"solution set NOT enumerated (compact constraint returned): {free_bits} undetermined "
        f"referenced bit(s) -> <= 2^{free_bits} expression-equivalence classes, cut by {n_nand} "
        f"nand-clause(s) + {n_or} or-clause(s) + {len(inequalities)} inequality(ies) + "
        f"{len(levels)} level(s); non-referenced bits are unconstrained (fully free). "
        f"satisfiable: {sat_note}.")
    return {"certain_on": on, "certain_off": off, "clauses": clauses,
            "inequalities": inequalities, "levels": levels,
            "satisfiable": satisfiable, "free_bits": free_bits,
            "solution_note": solution_note,
            "sound_complete": sound_complete, "sound_only_labels": sound_only}


def _modulator_constraint_satisfies_native(constraint, candidate):
    """Native dispatch for the BOOLEAN part of :func:`modulator_constraint_satisfies`
    (parity peer ``srmech_genome_modulator_constraint_satisfies``): serialize the
    constraint's floor + clauses, ask the C checker whether ``candidate`` satisfies the
    boolean part; returns ``True``/``False`` or ``None`` on any missing symbol / non-OK
    status / out-of-uint64-domain candidate — the caller runs the pure boolean check
    (identical result)."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_genome_modulator_constraint_satisfies")):
        return None
    if candidate < 0 or candidate >= (1 << 64):
        return None
    nand_list = [(c["any_absent"], c["any_present"]) for c in constraint["clauses"]
                 if c["kind"] == "nand"]
    or_list = [[(t["present"], t["absent"]) for t in c["terms"]]
               for c in constraint["clauses"] if c["kind"] == "or_terms"]
    # any mask beyond the native uint64 field -> defer to the exact pure path
    for a, p in nand_list:
        if a >= (1 << 64) or p >= (1 << 64):
            return None
    for terms in or_list:
        for pr, ab in terms:
            if pr >= (1 << 64) or ab >= (1 << 64):
                return None
    if constraint["certain_on"] >= (1 << 64) or constraint["certain_off"] >= (1 << 64):
        return None
    buf = _serialize_bool_constraint(constraint["certain_on"], constraint["certain_off"],
                                     nand_list, or_list)
    try:
        return _native.genome_modulator_constraint_satisfies_c(buf, candidate)
    except _native.NativeGenomeError:
        return None


def modulator_constraint_satisfies(constraint, candidate_cell_state):
    """Does ``candidate_cell_state`` satisfy an M3 ``constraint`` (§133 / #733)? — the
    runnable checker that makes the SOUND-AND-COMPLETE claim TESTABLE. Evaluates the
    whole constraint: the floor pins (``certain_on`` set, ``certain_off`` clear) AND
    every ``nand`` / ``or_terms`` clause AND every inequality (E4) AND every level (E3),
    ALL ANDed. On the COMPLETE gate-types this EQUALS
    ``modulator_consistent(strand, coupling, expressed_labels, candidate) == "CONSISTENT"``
    exactly; for a SOUND-ONLY (cross-type-OR) label it is a sound over-approximation
    (True for every consistent state, possibly True for a few inconsistent ones — the
    dropped disjunct).

    ``constraint`` is the dict :func:`modulator_constraint` returned;
    ``candidate_cell_state`` is a non-negative exact int (Class-I bitwise; no float,
    never ``abs()``). Native-dispatched (the C peer
    ``srmech_genome_modulator_constraint_satisfies`` checks the BOOLEAN part
    byte-identically; the inequality / level checks are the exact pure Class-N path);
    returns ``bool``. The inequality SENSE is a Class-K sign-branch, never ``abs()``."""
    if not isinstance(candidate_cell_state, int) or isinstance(candidate_cell_state, bool):
        raise ValueError(
            f"modulator_constraint_satisfies: candidate_cell_state must be an exact int "
            f"(Class-I bitwise); got {candidate_cell_state!r}")
    if candidate_cell_state < 0:
        raise ValueError(
            f"modulator_constraint_satisfies: candidate_cell_state must be non-negative (a "
            f"bitmask is never signed, so never abs()); got {candidate_cell_state}")
    if not isinstance(constraint, dict):
        raise ValueError(
            f"modulator_constraint_satisfies: constraint must be the dict modulator_constraint "
            f"returned; got {type(constraint).__name__}")
    native_bool = _modulator_constraint_satisfies_native(constraint, candidate_cell_state)
    if native_bool is not None:
        # C decided the BOOLEAN part; AND the exact inequality / level checks (owed-C).
        if not native_bool:
            return False
        return _satisfies_full({"certain_on": constraint["certain_on"],
                                "certain_off": constraint["certain_off"],
                                "clauses": [], "inequalities": constraint["inequalities"],
                                "levels": constraint["levels"]}, candidate_cell_state)
    return _satisfies_full(constraint, candidate_cell_state)


def plasmid(kernels=None, coupling=None, *, chromosomes=None):
    """Pack many kernels into ONE telomere-partitioned strand of pure PLASMID chromosomes —
    biology's plasmid (F715; the rc260 rename of the old ``genome``, §95.2 / #1407).

    The **all-plasmid** builder: each ``(label, leaves)`` kernel becomes a telomere-capped
    Tier-1 plasmid :func:`chromosome` (append-friendly, NO centromere — biology's small,
    appendable plasmid), all concatenated into one self-describing strand. This is the
    explicit "I want plain plasmids" constructor; :func:`genome` is the biology-aware umbrella
    that PICKS plasmid-vs-nuclear per kernel (rc260), and :func:`mint` is its explicit alias.
    Recover with :func:`partition`.

    **Single gene per chromosome (F715, unchanged).** Pass ``kernels`` — a mapping
    ``{label: leaves}`` or a sequence of ``(label, leaves)`` pairs (insertion order
    is the strand order). Returns the flat strand (``list`` of Klein-4 vectors).

    **Several genes per chromosome that PERSIST (F732/S43.1 / §44).** Pass
    ``chromosomes=[(label, [(gene_label, gene_leaves), …]), …]`` instead of
    ``kernels``: each chromosome becomes a telomere-capped region whose genes are
    opened by fixed-width INLINE :func:`_gene_cap` boundaries (§44). Returns ONE
    self-describing strand (NO ``gene_index`` sidecar). Persist with
    ``genome_save(strand, path, coupling)`` and page one chromosome's genes back with
    :func:`genome_genes`. ``coupling`` is always required.
    """
    if coupling is None:
        raise ValueError("plasmid: coupling is required")
    if (kernels is None) == (chromosomes is None):
        raise ValueError("plasmid: pass exactly one of kernels= or chromosomes=")
    if chromosomes is None:
        items = list(kernels.items()) if isinstance(kernels, dict) else list(kernels)
        # rc198 (#887): DISPATCH the plain multi-kernel assemble to the
        # srmech_genome_genome C peer when HAS_NATIVE — each kernel → a CHROM-capped
        # chromosome (via the rc197 srmech_genome_chromosome), all concatenated in
        # kernel order, BYTE-IDENTICAL to the pure loop (the numpy-free fallback +
        # parity oracle). The §44 chromosomes= multi-gene form opens its own gene caps
        # and stays pure (handled below). Any non-uniform / over-long-label kernel
        # returns None and re-runs the pure path (which raises the exact ValueError).
        dim = len(list(coupling))
        per_kernel = [_leaf_blocks(list(leaves)) for _, leaves in items]
        if dim > 0 and all(len(b) == dim for kb in per_kernel for b in kb):
            native = _native.genome_genome_c(
                [label for label, _ in items], _coupling_block_bytes(coupling),
                b"".join(b"".join(kb) for kb in per_kernel),
                [len(kb) for kb in per_kernel], dim)
            if native is not None:
                return [_hv_from_block(native[i * dim:(i + 1) * dim])
                        for i in range(len(native) // dim)]
        strand = []
        for label, leaves in items:
            strand.extend(chromosome(leaves, coupling, label=label))
        return strand
    # §44 multi-gene: ONE self-describing strand — each chromosome a telomere-capped
    # region with INLINE fixed-width gene-caps (no gene_index sidecar; the gene
    # boundaries + labels are recovered by scanning the strand).
    strand = []
    for label, genes_list in chromosomes:
        strand.extend(chromosome(coupling=coupling, label=label, genes=genes_list))
    return strand


def _kernel_content_bytes(leaves):
    """The content-address preimage of a kernel — its leaves serialised to the on-disk
    fixed-width blocks (§95c mint). The SAME bytes ``genome_save`` writes for these turns,
    so C + Python content-address a kernel identically (the mint orientation is derived
    from this, so it must be byte-stable)."""
    return b"".join(_leaf_blocks(list(leaves)))


def _mint_orientation(leaves):
    """The GLOBAL 4-way orientation the tooling assigns a NUCLEAR chromosome (§95c) — the
    kernel's content-address folded to a Klein-4 sector: ``sha256(content)[0] & 3``
    (Class A content-address → Class C chirality). Deterministic + attested (it IS the
    content-address — no magic number), and C-parity-trivial (the first digest byte & 3,
    the same ``srmech_sha256_hex`` on the same bytes)."""
    digest = _sha256_bytes(_kernel_content_bytes(leaves))     # 64-char hex (Class A)
    return int(digest[0:2], 16) & 3                            # first digest byte & 3


def _mint_shape(leaves):
    """Which SHAPE the tooling PICKS for a kernel (§95c / F1244 / #1407), MODELING BIOLOGY
    — the decision is the ATTESTED :func:`encode_shape` criterion (F715, keyed to 256=2**8
    + the Klein-4 order 4), never a hand-picked threshold:

    * ``tome`` / ``mobius`` (≤ 4 leaves) — PLASMID-scale → ``('plasmid', 1, False)``: a Tier-1
      append-only plasmid chromosome, no centromere (biology's small appendable plasmid).
    * ``quad_strand`` (≥ 5 leaves) — EUKARYOTIC-CHROMOSOME-scale → ``('nuclear', 2, True)``: a
      Tier-2 nuclear chromosome with an interior centromere (biology mints a centromere when a
      chromosome is big enough to need a segregation anchor).

    Returns ``(shape_name, tier, mint_centromere)`` — ``shape_name`` is the derived cap_kind
    (rc271 (F1251): plasmid (was "stick") / nuclear (was "minted")). "We don't pick the shape;
    the kernel's biology-analog scale does" — an empty kernel (0 leaves) reads as a tome (plasmid)."""
    n_leaves = len(list(leaves))
    shape = encode_shape(max(1, n_leaves) * LEAF_CAP)["shape"]   # n=leaves*256 → leaves exact
    if shape == "quad_strand":
        return "nuclear", 2, True
    return "plasmid", 1, False


def mint_plan(kernels):
    """WATCH the tooling pick each kernel's chromosome SHAPE (§95c / F1244) — introspection
    that BUILDS NOTHING (so we can see the choice before committing, F1244 "we watch it
    happen so we know it does it"). The genome architecture "builds into chromosomes as they
    fit": we don't pick the shape, the kernel's biology-analog scale (via the attested
    :func:`encode_shape`, :func:`_mint_shape`) does.

    ``kernels`` is a ``{label: leaves}`` mapping or ``(label, leaves)`` sequence (the
    :func:`mint` input). Returns, in kernel order,
    ``[{'label', 'n_leaves', 'shape', 'tier', 'centromere': bool, 'orientation', 'reason'}, …]``
    — ``orientation`` is the assigned global which-way for nuclear kernels (``None`` for
    plasmids)."""
    items = list(kernels.items()) if isinstance(kernels, dict) else list(kernels)
    plan = []
    for label, leaves in items:
        leaves_list = list(leaves)
        _shape, tier, mint_cen = _mint_shape(leaves_list)
        n_leaves = len(leaves_list)
        plan.append({
            "label": label, "n_leaves": n_leaves, "shape": _shape, "tier": tier,
            "centromere": mint_cen,
            "orientation": _mint_orientation(leaves_list) if mint_cen else None,
            "reason": (f"quad_strand ({n_leaves} leaves) → eukaryotic-chromosome-scale "
                       f"→ mint a Tier-2 centromere" if mint_cen else
                       f"{encode_shape(max(1, n_leaves) * LEAF_CAP)['shape']} "
                       f"({n_leaves} leaves) → plasmid-scale → Tier-1 plasmid (append-only)"),
        })
    return plan


def genome(kernels=None, coupling=None, *, chromosomes=None, progress=None):
    """Build a genome — the BIOLOGY-AWARE UMBRELLA that lets the TOOLING pick each
    chromosome's SHAPE by modeling biology (rc260 rename, §95.2 / §95c / F1244 / #1407).

    ``genome`` is the umbrella noun + the default smart constructor: per kernel the tooling
    DECIDES plasmid-vs-nuclear (we don't dictate) by :func:`encode_shape`'s attested criterion
    (F715 — no magic number). A PLASMID-scale kernel (tome/mobius, ≤ 4 leaves) stays a
    **Tier-1 PLASMID** chromosome (append-friendly, no centromere); a EUKARYOTIC-CHROMOSOME-scale
    kernel (quad_strand, ≥ 5 leaves) is **MINTED** as a **Tier-2 NUCLEAR** chromosome with an
    interior :func:`centromere` carrying its global orientation (content-address folded to a
    Klein-4 sector). Same signature + return as before (a flat telomere-partitioned strand,
    recovered with :func:`partition`); the READER is format-agnostic (:func:`partition` /
    :func:`centromere_of` handle either shape).

    **rc260 rename (BREAKING — §95.2 feedback 2):** ``genome`` was the pure all-plasmid builder;
    it is now the biology-aware umbrella (the old ``mint`` behaviour). For the explicit
    all-plasmid build use :func:`plasmid` (biology's plasmid); :func:`mint` is the explicit alias
    of this umbrella (the structured build). See the per-kernel picks with :func:`mint_plan`.
    The ``chromosomes=`` multi-gene form is a different structure (genes) and defers to
    :func:`plasmid`."""
    if coupling is None:
        raise ValueError("genome: coupling is required")
    if (kernels is None) == (chromosomes is None):
        raise ValueError("genome: pass exactly one of kernels= or chromosomes=")
    if chromosomes is not None:
        # the multi-gene form is not a §95a mint shape (genes are a different structure);
        # build it as pure plasmids — no centromere selection applies.
        return plasmid(coupling=coupling, chromosomes=chromosomes)
    items = list(kernels.items()) if isinstance(kernels, dict) else list(kernels)
    dim = len(list(coupling))
    # §95a/rc258 (#1407): DISPATCH the whole mint assemble to the srmech_genome_mint C peer
    # when HAS_NATIVE — 1:1 C↔Python byte parity (user direction 2026-07-16). The per-kernel
    # plasmid-vs-centromere selection (attested encode_shape), the content-address orientation
    # (srmech_sha256_hex), and the interior centromere pack all mirror in C. The pure loop
    # below is the numpy-free oracle + the non-uniform-width fallback.
    per_kernel = [_leaf_blocks(list(leaves)) for _, leaves in items]
    if dim > 0 and all(len(b) == dim for kb in per_kernel for b in kb):
        # §101: progress= (Python-only kwarg) threads the per-kernel MINTING tick into
        # the srmech_genome_mint_progress C loop via the ctypes trampoline. On cancel
        # genome_mint_c returns the VALID PARTIAL bytes (whole chromosomes so far).
        native = _native.genome_mint_c(
            [label for label, _ in items], _coupling_block_bytes(coupling),
            b"".join(b"".join(kb) for kb in per_kernel),
            [len(kb) for kb in per_kernel], dim, progress=progress)
        if native is not None:
            return [_hv_from_block(native[i * dim:(i + 1) * dim])
                    for i in range(len(native) // dim)]
    strand = []
    for i, (label, leaves) in enumerate(items):
        if progress is not None and progress(
                {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_MINTING,
                 "done": i, "total": len(items)}):
            return strand              # §101 valid partial: i complete chromosomes
        leaves_list = list(leaves)
        _shape, _tier, mint_cen = _mint_shape(leaves_list)
        if mint_cen:
            strand.extend(chromosome(leaves_list, coupling, label=label,
                                     centromere=_mint_orientation(leaves_list)))
        else:
            strand.extend(chromosome(leaves_list, coupling, label=label))
    return strand


def mint(kernels=None, coupling=None, *, chromosomes=None, progress=None):
    """Explicit alias for :func:`genome` — the biology-aware tooling-picks build (rc260 /
    §95c / #1407).

    :func:`genome` is the umbrella noun (the default smart constructor); ``mint`` is the
    explicit "structured build" name for the SAME tooling-picks behaviour (kept for the
    mint-vs-append vocabulary of F1243/§95c). :func:`plasmid` is the pure all-plasmid builder.
    See the per-kernel picks with :func:`mint_plan`. Byte-identical to :func:`genome`.

    §101 ``progress`` (Python-only kwarg; forwarded to :func:`genome`): a per-kernel
    heartbeat + graceful-abort — a truthy return CANCELS and returns the VALID PARTIAL
    strand (the whole chromosomes minted so far)."""
    return genome(kernels, coupling, chromosomes=chromosomes, progress=progress)


def partition(strand, coupling, labels=None):
    """Recover every kernel from a multi-kernel genome strand — the inverse of
    :func:`genome` (F715 / §44).

    Walk the ``strand``; each CHROM cap (inline marker :data:`CHROM_CAP_MARKER`,
    §44) starts a new chromosome partition and its label is read back INLINE
    (:func:`_unpack_cap` — no sidecar). The coupled data turns until the next CHROM
    cap are that kernel's leaves (re-bound through ``coupling`` — the reversible
    :func:`quad_turn`); intervening GENE caps are skipped as gene delimiters, so a
    multi-gene chromosome FLATTENS to its concatenated leaves (use :func:`genes` to
    keep the per-gene split). Returns ``{label: leaves}``::

        partition(genome({"a": A, "b": B}, one), one) == {"a": A, "b": B}

    §44: chromosomes are DISCOVERED by scanning inline CHROM caps — ``partition`` no
    longer needs the label set handed to it (the strand self-describes). ``labels``
    is accepted for back-compat: when given, it FILTERS the result to that subset
    (and orders it), so old call-sites that passed the full list still round-trip.
    """
    # rc198 (#887): DISPATCH to the srmech_genome_partition C peer when HAS_NATIVE and
    # the strand is uniform fixed-width leaf_dim blocks — byte-identical (open a
    # partition per CHROM / kernel-telomere / active-telomere cap, skip gene / header
    # caps, re-bind each data turn through coupling). The caller builds the
    # {label: leaves} dict here (dict overwrite-on-duplicate-label, exactly like the
    # pure walk's out[current] = []) + applies the labels= filter. The pure walk below
    # is the numpy-free fallback + parity oracle (and any non-uniform strand).
    dim = len(list(coupling))
    blocks = _leaf_blocks(strand)
    if dim > 0 and blocks and all(len(b) == dim for b in blocks):
        native = _native.genome_partition_c(
            b"".join(blocks), len(blocks), dim, _coupling_block_bytes(coupling))
        if native is not None:
            leaf_bytes, part_labels, part_counts = native
            out = {}
            i = 0
            for label, count in zip(part_labels, part_counts):
                out[label] = [
                    _HV.from_sequence(leaf_bytes[(i + j) * dim:(i + j + 1) * dim],
                                      sectors=QUAD)
                    for j in range(count)]
                i += count
            if labels is not None:
                return {label: out[label] for label in labels if label in out}
            return out
    out = {}
    current = None
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in (CHROM_CAP_MARKER, KERNEL_TELOMERE_MARKER,
                    ACTIVE_TELOMERE_MARKER, DIPLOID_TELOMERE_MARKER):
            # a telomere cap (plain / §89 kernel / §127 active / §95b diploid) — start a
            # partition. _unpack_cap reads the label (bytes [1:] up to the first NUL) UNIFORMLY
            # — the active telomere's count sits AFTER that NUL, so the label is exact.
            _marker, current = _unpack_cap(hv)
            out[current] = []
        elif kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                      THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER, KERNEL_HEADER_MARKER,
                      CENTROMERE_CAP_MARKER):
            continue                            # a gene delimiter (§44 plain / §128
                                                # regulatory / §130 boolean / §131 threshold /
                                                # §132 graded) / §60 v5 header / §95a the
                                                # interior centromere anchor —
                                                # skip, not a coupled data turn
                                                # not data; flatten past it
        elif current is not None:
            out[current].append(quad_turn(hv, coupling))   # reversible uncouple
    if labels is not None:
        return {label: out[label] for label in labels if label in out}
    return out


# ─────────────────────────────────────────────────────────────────────────────
# §60 (rc121, issue #1245 REOPENED) — the SIZE-AGNOSTIC KERNEL TRANSLATION LAYER.
# Store / recall a flat Klein-4 kernel of ARBITRARY dimension D through the genome,
# with D SELF-RECORDED in the strand (the §60 kernel header, marker 0x4B) so the
# reconstruction is EXACT for any D with NO caller-supplied length — siona's
# 8192-dim Klein-4 kernels, the 1000-symbol non-multiple case, and an MB-scale
# kernel all round-trip through the ONE pack/unpack surface. The genome quad-strand
# was ALREADY dimension-agnostic on storage/read (the LEAF_CAP=256 is planning-only,
# never assumed on the read path); this closes the two remaining gaps: W1 (record
# the TRUE length D self-describingly) and W2 (ship the chunk/reconstruct ops).
# ─────────────────────────────────────────────────────────────────────────────


def _default_coupling(leaf_dim):
    """The deterministic default coupling invariant a header-recorded ``leaf_dim``
    reconstructs — an all-ones Klein-4 vector of width ``leaf_dim`` (sectors=4). So
    :func:`kernel_unpack` can uncouple a :func:`kernel_pack` strand that used the
    default ``coupling`` without the caller re-supplying it."""
    return _HV.from_sequence([1] * int(leaf_dim), sectors=QUAD)


def _validate_kernel_symbols(data):
    """``data`` → a validated ``list[int]`` of Klein-4 sector symbols ``{0,1,2,3}``,
    raising ``ValueError`` on any symbol out of range (the §60 sharp-edge guard —
    ``HV.from_sequence(sectors=4)`` accepts ``>3`` in memory but only Klein-4 turns
    bit-pack, so reject before packing)."""
    syms = [int(x) for x in data]
    for i, s in enumerate(syms):
        if s < 0 or s > 3:
            raise ValueError(
                f"kernel: symbol {s} at position {i} is not a Klein-4 sector "
                f"(0..3) — element_type='klein4' packs only Klein-4 kernels"
            )
    return syms


def _kernel_v6_leaves(syms, leaf_dim, et_code):
    """The §89/v6 leaf list for a validated Klein-4 kernel ``syms`` — the header LEAF
    (uniformly-Klein-4 :func:`_pack_kernel_header_klein4`) followed by the content
    leaves (``leaf_dim``-wide, final leaf zero-padded — the ``encode_shape``
    ceil-division criterion generalised to ``leaf_dim``). EVERY leaf is 100 % Klein-4,
    so ``[header, *content]`` rides the plain coupled-turn path: :func:`kernel_pack`
    caps it with a KERNEL telomere, :func:`genome_append_kernel` appends it O(1)."""
    D = len(syms)
    header = _pack_kernel_header_klein4(D, leaf_dim, et_code, leaf_dim)
    leaves = [header]
    i = 0
    while i < D:
        block = syms[i:i + leaf_dim]
        if len(block) < leaf_dim:
            block = block + [0] * (leaf_dim - len(block))
        leaves.append(_HV.from_sequence(block, sectors=QUAD))
        i += leaf_dim
    return leaves


#: The chromosome-BOUNDARY cap markers — a cap in this set OPENS a chromosome (carries a
#: label inline), as opposed to the interior caps (gene / centromere) that sit inside one.
#: CHROM (0x43) / kernel-telomere (0x6B) / active-telomere (0x74) / diploid (0x44).
_CHROM_BOUNDARY_MARKERS = (CHROM_CAP_MARKER, KERNEL_TELOMERE_MARKER,
                           ACTIVE_TELOMERE_MARKER, DIPLOID_TELOMERE_MARKER)


def _integrate_coheres(host, provirus):
    """The DEFAULT structural compatibility predicate for :func:`integrate` (§95.1d / F1244 /
    F1251) — does the ``provirus`` COHERE with the ``host`` genome enough to integrate?

    F1244's coherency-translation contract is that host + provirus were coupled through the SAME
    ``coupling`` (the shared k=3 invariant): that is why integration is FREE (no re-coupling). The
    ``coupling`` has width == the leaf_dim, and EVERY block (cap or coupled turn) in a strand is
    that leaf_dim wide, so the strand-visible NECESSARY condition for "coupled through the same
    invariant" is an EQUAL coupling WIDTH. Two genomes at DIFFERENT widths were coupled through
    DIFFERENT invariants — they cannot cohere (an incompatible replicon: the F1251 CG258 case,
    where the plasmid's replication architecture is segregated from the clonal lineage), so
    integration is honest-declined. This is a Class-K/C coherency read — an EQUALITY of the two
    coupling widths — NOT a magnitude (never ``abs(w_host - w_provirus)``; we compare, we do not
    measure a distance). An EMPTY host coheres with any provirus (nothing to be incompatible
    with — the empty-host integrate returns the bare provirus, as rc262 did). This is the
    DEFAULT; a caller supplies a domain replicon-/lineage-compatibility predicate via
    ``integrate``'s ``compatible`` hook (e.g. a same-width but different-lineage CG258 barrier).
    Returns ``True`` (cohere → integrate) or ``False`` (incompatible → honest-decline)."""
    if not host:
        return True                                    # empty host — any provirus integrates
    return len(host[0]) == len(provirus[0])            # equal coupling width == same-invariant


def integrate(host, provirus, *, at=None, compatible=None):
    """Integrate a PROVIRUS (a chromosome strand) INTO a host genome-strand — the
    viral-integration analog (§95.1d / F1244 / #1407), the coherency-translation-layer capstone.

    Biology: a retrovirus (a Tier-1 PLASMID genome — telomere-capped, no centromere, §95c)
    integrates into a eukaryote's DNA (Tier-2 — NUCLEAR / DIPLOID) and is thereafter part of it.
    We watch it happen, so there is ONE shared cascade spanning the levels. In srmech that
    coherence is FREE: rc258 centromere, rc259 diploid, and the mint umbrella ALL couple every
    turn through the SAME ``coupling`` (one k=3 cascade at different rungs, ADR-0005), so a plasmid
    provirus simply becomes another chromosome in the host genome and everything still recovers
    — :func:`partition` recovers every chromosome, :func:`centromere_of` still reads the host's
    nuclear chromosome, :func:`recover_diploid` still recovers its diploid, and the integrated
    provirus recovers too. That is the translation between the Tier-1 and Tier-2 levels: it needs
    no conversion because they are the same cascade.

    **§135/rc273 (F1251) — the COMPATIBILITY GATE.** Horizontal transfer has EMPIRICAL BOUNDARIES:
    F1251 read attested bacterial genomics (Shropshire et al.) — CG307 plasmids are shared with
    other clonal groups EXCEPT CG258, which stays SEGREGATED. HGT is NOT universal; some hosts
    exchange, some don't. So ``integrate`` now CHECKS host↔provirus compatibility BEFORE splicing
    and HONEST-DECLINES on incompatibility — it returns ``None`` (a clean refuse, inform-don't-
    crash, mirroring :func:`telomere_tick`'s senescence), leaving the host UNCHANGED, rather than
    forcing every element into every host. The DEFAULT predicate (:func:`_integrate_coheres`) is
    the F1244 coherence contract made checkable: host + provirus must share the COUPLING WIDTH
    (== the ``coupling`` / leaf_dim), because two genomes at different widths were coupled through
    different invariants and cannot cohere (an incompatible replicon — the CG258 analog). Pass an
    explicit ``compatible=`` hook — a callable ``(host, provirus) -> bool`` — to supply a domain
    replicon-/lineage-compatibility predicate (e.g. a same-width but different-lineage barrier);
    it is checked IN ADDITION to the width coherence (both must pass). A COMPATIBLE provirus
    integrates EXACTLY as rc262 did (the gate adds ONLY a refuse path — full back-compat).

    ``host`` is a genome strand (any mix of plasmid / nuclear / diploid chromosomes, from
    :func:`genome` / :func:`plasmid` / :func:`mint`); ``provirus`` is a chromosome strand opening
    with a boundary cap (from :func:`chromosome` / :func:`plasmid` / :func:`mint` /
    :func:`diploid`). ``at`` = the host CHROMOSOME INDEX to insert the provirus BEFORE (0-based;
    default ``None`` = integrate after the last chromosome). **Both must have been coupled through
    the SAME ``coupling``** — the coherence contract (the shared cascade). This is strand splicing:
    the provirus's turns are ALREADY coupled, so integration is a composition of self-describing
    blocks, no re-coupling. Returns the combined genome strand on a COMPATIBLE integration (recover
    with :func:`partition`), or ``None`` on an incompatible one (the honest-decline; host
    unchanged).

    Class-C (the integration/orientation) ∘ Class-K (the coherency-width equality gate) ∘
    composition of the C-built chromosome strands. A C-only host integrates identically via the
    ``srmech_genome_integrate`` C peer (rc276 / G4): it scans the host's fixed-width blocks for
    chromosome-boundary caps, resolves the SAME ``at`` → locus, applies the SAME width-coherence
    gate, and concatenates the two genomes' self-describing regions (byte-identical blocks) at the
    chromosome boundary — no manifest needed (the strand self-describes on the block scan). When
    ``HAS_NATIVE`` this Python path DISPATCHES the splice to that peer (byte-identical whether
    native or pure — the differential proof). The ``compatible=`` hook stays a Python-layer
    affordance (a callable cannot cross the C wire, so it is checked here, around the dispatch).
    Never ``abs()`` (the gate is an equality read, not a magnitude).
    """
    host = list(host)
    provirus = list(provirus)
    if not provirus or _cap_kind(provirus[0]) not in _CHROM_BOUNDARY_MARKERS:
        raise ValueError(
            "integrate: provirus must be a chromosome strand opening with a boundary cap "
            "(from chromosome / plasmid / mint / diploid)")
    bounds = [i for i, hv in enumerate(host) if _cap_kind(hv) in _CHROM_BOUNDARY_MARKERS]
    if host and _cap_kind(host[0]) not in _CHROM_BOUNDARY_MARKERS:
        raise ValueError(
            "integrate: host is not a well-formed genome strand (no leading chromosome cap)")
    # §135/rc273 (F1251): the COMPATIBILITY GATE — check coherence BEFORE integrating and
    # HONEST-DECLINE (return None, host unchanged) on incompatibility. The default width-coherence
    # predicate + an optional caller-supplied replicon-/lineage-compatibility hook (both must
    # pass). A compatible integration proceeds EXACTLY as rc262 (the gate adds only a refuse path).
    if not _integrate_coheres(host, provirus):
        return None                                    # incompatible replicon (CG258 analog) — refuse
    if compatible is not None and not compatible(host, provirus):
        return None                                    # caller lineage/replicon barrier — refuse
    if at is None:
        locus = len(host)                              # integrate after the last chromosome
    else:
        if not isinstance(at, int) or not 0 <= at <= len(bounds):
            raise ValueError(
                "integrate: at={!r} out of range [0, {}] (host chromosome index)".format(
                    at, len(bounds)))
        locus = bounds[at] if at < len(bounds) else len(host)
    # rc276 (#891 / G4): DISPATCH the SPLICE to the srmech_genome_integrate C peer when
    # HAS_NATIVE + uniform fixed-width leaf_dim blocks — byte-identical (scan the host's
    # boundary caps, resolve the SAME at→locus, concatenate whole self-describing blocks).
    # A bare-C host runs the whole op via that peer; here it proves native == pure. The
    # width gate + compatible hook already passed above, so the C peer integrates (its own
    # gate returns integrated=1). The pure block splice below is the numpy-free fallback +
    # parity oracle (and any non-uniform-width strand). NEVER abs() (an equality read).
    host_blocks = _leaf_blocks(host)
    prov_blocks = _leaf_blocks(provirus)
    prov_dim = len(prov_blocks[0])
    host_dim = len(host_blocks[0]) if host_blocks else prov_dim
    if (all(len(b) == host_dim for b in host_blocks)
            and all(len(b) == prov_dim for b in prov_blocks)):
        native = _native.genome_integrate_c(
            b"".join(host_blocks), len(host_blocks), host_dim,
            b"".join(prov_blocks), len(prov_blocks), prov_dim,
            -1 if at is None else at)
        if native is not None:
            out_bytes, integrated = native
            if integrated:
                return [_hv_from_block(out_bytes[i * prov_dim:(i + 1) * prov_dim])
                        for i in range(len(out_bytes) // prov_dim)]
    return host[:locus] + provirus + host[locus:]


def kernel_pack(data, *, leaf_dim=LEAF_CAP, label="kernel", coupling=None,
                element_type="klein4"):
    """Pack a flat Klein-4 kernel of ANY dimension into a self-describing strand (§89).

    ``data`` is the flat kernel — a sequence of Klein-4 sector symbols ``{0,1,2,3}``
    (an :class:`HV`, ``list[int]``, ``bytes``, …). It is chunked into ``leaf_dim``-wide
    leaves (the final leaf zero-padded to ``leaf_dim``; the ``encode_shape`` ceil-
    division criterion, generalised to ``leaf_dim``), led by the UNIFORMLY-KLEIN-4 §89
    KERNEL HEADER LEAF that SELF-RECORDS the kernel's TRUE length ``D``, its
    ``element_type`` (``"klein4"`` today — the genome-native 2-bit symbol, so the
    element codec is identity) and its ``leaf_dim``, all coupled through ``coupling``
    into a KERNEL-telomere-capped :func:`chromosome`. Returns the flat strand
    (``list`` of Klein-4 ``HV`` s): ``[kernel_telomere, klein4_header, turn0, turn1, …]``.

    §89/rc126 (format v6, issue #1261): the header is now a 100 % Klein-4 LEAF
    (base-4-encoded fields, :func:`_pack_kernel_header_klein4`), distinguished by the
    ``0x6B`` KERNEL telomere + its reserved position (first turn after the cap) — NOT
    the v5 ``0x4B`` byte-TLV block. So the store is UNIFORMLY Klein-4: every data leaf
    couples + bit-packs identically, and the whole kernel rides the plain coupled-turn
    append path (:func:`genome_append_kernel`). A v5 byte-TLV header stays READABLE
    (:func:`kernel_unpack` dual-reads); this writer no longer emits one.

    Recover the EXACT kernel — trimmed to the true ``D``, no external length needed —
    with :func:`kernel_unpack`. Persist with ``genome_save(strand, path, coupling)``
    and unpack from the directory with ``kernel_unpack(path, coupling)``.

    ``leaf_dim`` defaults to :data:`LEAF_CAP` (256, the tome width); it must be at
    least :data:`_KERNEL_HEADER_KLEIN4_SYMS` (52) so the base-4 header fits one leaf.
    ``coupling`` defaults to the deterministic all-ones invariant
    (:func:`_default_coupling`) that :func:`kernel_unpack` reconstructs from the
    header's ``leaf_dim``; pass a custom ``coupling`` (width ``leaf_dim``) only if you
    pass the SAME one to unpack.
    """
    if element_type not in _ELEMENT_TYPE_CODES:
        raise ValueError(
            f"kernel_pack: unknown element_type {element_type!r}; declared types are "
            f"{sorted(_ELEMENT_TYPE_CODES)} (element_type is a §60 header enum)"
        )
    et_code = _ELEMENT_TYPE_CODES[element_type]
    if not isinstance(leaf_dim, int) or isinstance(leaf_dim, bool) \
            or leaf_dim < _KERNEL_HEADER_KLEIN4_SYMS:
        raise ValueError(
            f"kernel_pack: leaf_dim must be an int >= {_KERNEL_HEADER_KLEIN4_SYMS} "
            f"(so the §89 uniformly-Klein-4 kernel header fits one leaf); got "
            f"{leaf_dim!r}"
        )
    syms = _validate_kernel_symbols(data)
    if coupling is None:
        coupling = _default_coupling(leaf_dim)
    elif len(list(coupling)) != leaf_dim:
        raise ValueError(
            f"kernel_pack: coupling dim {len(list(coupling))} != leaf_dim {leaf_dim}"
        )
    leaves = _kernel_v6_leaves(syms, leaf_dim, et_code)
    # [kernel_telomere, coupled_klein4_header, coupled content turns…]
    return chromosome(leaves, coupling, label=label, kernel=True)


def kernel_unpack(strand_or_path, coupling=None):
    """Recover the EXACT flat Klein-4 kernel from a §89/§60 strand or genome path.

    The inverse of :func:`kernel_pack`. ``strand_or_path`` is either the in-memory
    strand :func:`kernel_pack` returned, or a genome DIRECTORY that a
    ``genome_save`` of one wrote. Recalls the coupled leaves, reads the kernel's TRUE
    length ``D`` from its header, and TRIMS to ``D`` — so the returned ``list[int]``
    equals the exact packed kernel of ANY dimension, with NO caller-supplied length
    (W1 closed). Three self-describing formats read in ONE walk (the rc114 dual-read
    pattern, one layer up):

    * **§89/v6** (this writer): a KERNEL telomere (``0x6B``) opens the chromosome; the
      FIRST coupled turn after it is the uniformly-Klein-4 header LEAF
      (:func:`_pack_kernel_header_klein4`). Recall uncouples it to ``leaves[0]``; its
      base-4 fields give ``D`` / ``element_type`` / ``leaf_dim``, and ``leaves[1:]``
      are the content.
    * **§60/v5** (READ-ONLY back-compat): a ``0x4B`` byte-TLV header block (skipped by
      recall as a marker cap); its big-endian fields give ``D``.
    * **no header** (any pre-rc121 genome): read as ``element_type=klein4`` with
      ``D = leaf_count × leaf_dim`` — no trim, no migration.

    ``coupling`` (the coupling invariant) is optional: for a genome PATH with a present
    manifest it is resolved from the manifest cache; otherwise (an in-memory strand, or
    a manifest-less directory) it defaults to the deterministic all-ones invariant
    reconstructed from the leaf width — matching :func:`kernel_pack`'s default. Pass
    ``coupling`` explicitly if you packed with a custom one.
    """
    if isinstance(strand_or_path, (str, Path)):
        strand, coupling, _labels = genome_load(strand_or_path, coupling=coupling)
    else:
        strand = list(strand_or_path)
    # v5 byte-TLV header (marker 0x4B), if any — READ-ONLY back-compat.
    header_v5 = next(
        (hv for hv in strand if _cap_kind(hv) == KERNEL_HEADER_MARKER), None)
    # v6 KERNEL telomere (0x6B) → the first coupled turn is the Klein-4 header LEAF.
    has_kernel_telomere = any(
        _cap_kind(hv) == KERNEL_TELOMERE_MARKER for hv in strand)
    if coupling is None:
        # Reconstruct the default coupling invariant from the leaf width (v5 header's
        # recorded leaf_dim, else the first data turn's width — both == leaf_dim).
        if header_v5 is not None:
            _d, hdr_leaf_dim, _et = _unpack_kernel_header(header_v5)
            coupling = _default_coupling(hdr_leaf_dim)
        else:
            width = next((len(hv) for hv in strand if _cap_kind(hv) is None), 0)
            coupling = _default_coupling(width)
    leaves = recall(strand, coupling)      # skips every cap (incl. the v5 0x4B header
                                          # + the 0x6B kernel telomere); uncouples turns
    if header_v5 is not None:
        # v5: recall already skipped the 0x4B marker block, so `leaves` is content.
        flat = [int(x) for lf in leaves for x in lf]
        true_len, _ld, _et = _unpack_kernel_header(header_v5)
        return flat[:true_len]                    # trim to the TRUE length D (W1)
    if has_kernel_telomere and leaves:
        # v6: leaves[0] is the uncoupled Klein-4 header LEAF; leaves[1:] the content.
        true_len, _ld, _et = _unpack_kernel_header_klein4(leaves[0])
        flat = [int(x) for lf in leaves[1:] for x in lf]
        return flat[:true_len]                    # trim to the TRUE length D (W1)
    # No header (pre-rc121): full-dim, D = leaf_count × leaf_dim (back-compat).
    return [int(x) for lf in leaves for x in lf]


# ─────────────────────────────────────────────────────────────────────────────
# §127 (rc127, #726) — the ACTIVE TELOMERE gate: operand(count) MODULATES operator.
# telomere_tick reads the active telomere's count (operand) and its behaviour (the
# operator) is SELECTED by that operand — count>0 proceeds + decrements (a divide),
# count==0 refuses (Hayflick senescence). This is the theorem #726 asked for: the
# chromosome is GENUINELY op⊗operand (not the passive op-slot the #726 probe found).
# ─────────────────────────────────────────────────────────────────────────────


def _telomere_tick_native(cap):
    """Native dispatch for the cap-tick (parity peer ``srmech_genome_telomere_tick``):
    ``cap`` (an active-telomere ``HV``) → ``(senescent, count_after, new_cap_bytes)``,
    or ``None`` on any missing symbol / non-OK status (the caller runs the pure path).
    Native is authoritative when present; the pure path is the complete alternative."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_genome_telomere_tick")):
        return None
    try:
        return _native.genome_telomere_tick_c(cap.tobytes(), len(cap))
    except _native.NativeGenomeError:
        return None


def _gene_express_native(cap, cell_state):
    """Native dispatch for the §128 per-gene expression decision (parity peer
    ``srmech_genome_gene_express``): ``cap`` (a plain GENE / regulatory-gene ``HV``) +
    ``cell_state`` → ``True``/``False`` (does the gene express?), or ``None`` on any missing
    symbol / non-OK status (the caller runs the pure Class-I bitwise path). Native is
    authoritative when present; the pure path is the complete alternative."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_genome_gene_express")):
        return None
    try:
        return _native.genome_gene_express_c(cap.tobytes(), len(cap), cell_state)
    except _native.NativeGenomeError:
        return None


def _gene_level_native(cap, cell_state):
    """Native dispatch for the §132 per-gene expression LEVEL (parity peer
    ``srmech_genome_gene_express_levels``): ``cap`` (a plain / regulatory / boolean / threshold /
    graded gene ``HV``) + ``cell_state`` → the exact-rational ``(num, den)`` level (a binary gene
    → ``(1, 1)`` if its gate passes else ``(0, 1)``; a graded gene → its clamped reduced
    dose-response rational), or ``None`` on any missing symbol / non-OK status (e.g. an int64
    dose-accumulate OVERFLOW → the caller runs the exact pure Class-N/I path). Native is
    authoritative when present; the pure path is the complete alternative."""
    from . import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_genome_gene_express_levels")):
        return None
    try:
        return _native.genome_gene_express_levels_c(cap.tobytes(), len(cap), cell_state)
    except _native.NativeGenomeError:
        return None


# ── #1390 item 2: graph_to_kernel / kernel_to_graph ─────────────────────────
# A domain-free codec that serialises a sparse SIGNED INTEGER graph (the
# directed Class-L Laplacian — vocab_size + edge list + int weights[metric] +
# signed charges[direction], with an optional node_ids label table + extras
# metadata) into a Klein-4 symbol stream for kernel_pack, and inverts it
# BYTE-EXACT. Faithful port of R-RBS-LM-GRAPH2KERNEL: each int is base-4 digits
# behind a 2-symbol length header (Class-K zig-zag sign on the charge). The
# format is SELF-DESCRIBING (count headers) so undirected (charges=None),
# unlabeled (node_ids=None) and metadata-free (extras=()) all round-trip.
# Klein-4 is ONLY the 2-bit on-disk alphabet (F1221 disk rule — no bind/bundle
# HV object is stored). Byte-identical C peer: srmech_graph_kernel_encode /
# srmech_graph_kernel_decode.

#: The 2-symbol base-4 length header caps each serialised int at 15 base-4
#: digits = 30 bits (#1390 item 2 / F1227 note): a co-occurrence weight or
#: vocab id >= 2**30 overflows it and raises. Document the cap; a wide-int
#: header mode is a future extension.
_GRAPH_KERNEL_MAX_DIGITS = 15


def _graph_zig(n):
    """Class-K pin-slot: signed int -> non-negative (zig-zag; NOT the builtin)."""
    return (n << 1) if n >= 0 else ((-n) << 1) - 1


def _graph_unzig(z):
    """Inverse zig-zag: non-negative -> signed int (Class-K)."""
    return (z >> 1) if (z & 1) == 0 else -((z + 1) >> 1)


def _graph_ints_to_syms(ints):
    """Flat non-negative int list -> Klein-4 symbols {0,1,2,3}: each int as
    base-4 digits behind a 2-symbol length header (<=15 digits/int)."""
    syms = []
    for n in ints:
        digs = []
        x = n
        while True:
            digs.append(x & 3)
            x >>= 2
            if x == 0:
                break
        if len(digs) > _GRAPH_KERNEL_MAX_DIGITS:
            raise ValueError(
                f"graph_to_kernel: value {n} needs {len(digs)} base-4 digits > "
                f"the {_GRAPH_KERNEL_MAX_DIGITS}-digit (30-bit) cap of the "
                f"2-symbol length header"
            )
        syms.append(len(digs) & 3)
        syms.append((len(digs) >> 2) & 3)
        syms += digs
    return syms


def _graph_syms_to_ints(syms):
    """Inverse of :func:`_graph_ints_to_syms` (2-symbol header + base-4 digits)."""
    ints, i = [], 0
    while i + 2 <= len(syms):
        ln = syms[i] + (syms[i + 1] << 2)
        i += 2
        if ln == 0 or i + ln > len(syms):
            break
        v = 0
        for k in range(ln):
            v |= syms[i + k] << (2 * k)
        ints.append(v)
        i += ln
    return ints


def _graph_kernel_encode(vocab_size, edges, weights, ch, nid, ex):
    """Assemble the payload int stream + encode to Klein-4 syms (the C-peer
    boundary). Native ``srmech_graph_kernel_encode`` when loaded, else pure."""
    from . import _native
    if _native.has_native_graph_kernel_codec():
        native = _native.graph_kernel_encode_c(vocab_size, edges, weights, ch, nid, ex)
        if native is not None:
            return native
    payload = [vocab_size, len(nid)] + nid + [len(ex)] + ex + [len(edges)]
    for (i, j), w, c in zip(edges, weights, ch):
        payload += [i, j, w, _graph_zig(c)]
    return _graph_ints_to_syms(payload)


def _graph_kernel_decode(syms):
    """Decode Klein-4 syms -> the graph dict (the C-peer boundary). Native
    ``srmech_graph_kernel_decode`` when loaded, else pure."""
    from . import _native
    if _native.has_native_graph_kernel_codec():
        native = _native.graph_kernel_decode_c(syms)
        if native is not None:
            return native
    it = _graph_syms_to_ints(syms)
    p = 0
    vocab_size = it[p]; p += 1
    n_nid = it[p]; p += 1
    node_ids = it[p:p + n_nid]; p += n_nid
    n_ex = it[p]; p += 1
    extras = it[p:p + n_ex]; p += n_ex
    ne = it[p]; p += 1
    edges, weights, charges = [], [], []
    for _ in range(ne):
        i, j, w, zc = it[p], it[p + 1], it[p + 2], it[p + 3]; p += 4
        edges.append((i, j))
        weights.append(w)
        charges.append(_graph_unzig(zc))
    return {"vocab_size": vocab_size, "edges": edges, "weights": weights,
            "charges": charges, "node_ids": list(node_ids), "extras": list(extras)}


def graph_to_kernel(vocab_size, edges, weights, charges=None, *,
                    node_ids=None, extras=(), leaf_dim, label, coupling):
    """Serialise a directed SIGNED integer graph -> a packed genome chromosome
    (Klein-4 leaves) + its true symbol count (#1390 item 2).

    ``edges``: ``[(i, j), ...]``; ``weights``: ``[int, ...]`` (metric);
    ``charges``: ``[signed int, ...]`` or ``None`` (direction); ``node_ids``:
    ``[int, ...]`` or ``None`` (a label table, e.g. glyph ids); ``extras``:
    ``(int, ...)`` caller metadata (e.g. a start anchor). Returns
    ``(strand, n_syms)`` — persist the strand with ``genome_save`` and pass
    ``n_syms`` to :func:`kernel_to_graph`. The payload<->symbol codec dispatches
    to the byte-identical C peer ``srmech_graph_kernel_encode`` when loaded; the
    pure body is the complete alternative + parity oracle. Faithful port of
    R-RBS-LM-GRAPH2KERNEL."""
    if len(edges) != len(weights):
        raise ValueError(
            f"graph_to_kernel: edges/weights length mismatch "
            f"({len(edges)} != {len(weights)})"
        )
    ch = list(charges) if charges is not None else [0] * len(edges)
    if len(ch) != len(edges):
        raise ValueError(
            f"graph_to_kernel: charges length {len(ch)} != edges {len(edges)}"
        )
    nid = list(node_ids) if node_ids is not None else []
    ex = list(extras)
    syms = _graph_kernel_encode(vocab_size, [tuple(e) for e in edges],
                                list(weights), ch, nid, ex)
    strand = kernel_pack(syms, leaf_dim=leaf_dim, label=label, coupling=coupling)
    return strand, len(syms)


def kernel_to_graph(chroms, coupling, n_syms):
    """Inverse of :func:`graph_to_kernel`: a packed chromosome (or genome path)
    + its ``n_syms`` -> the directed signed graph dict
    ``{vocab_size, edges, weights, charges, node_ids, extras}`` (#1390 item 2).
    ``n_syms`` trims the leaf-dim padding :func:`kernel_unpack` restores."""
    syms = list(kernel_unpack(chroms, coupling))[:n_syms]
    return _graph_kernel_decode(syms)


def mint_strand(strand, coupling, *, orientation=None, centromere_at=None,
                repeats=CENTROMERE_DEFAULT_REPEATS, handle="cen", progress=None):
    """MINT an ALREADY-PACKED strand — splice a §95a interior CENTROMERE (``0x58``) into it
    at the p:q arm-split, turning a Tier-1 PLASMID into a Tier-2 NUCLEAR chromosome (§100 GAP 1 /
    PR#687 F1249).

    The :func:`mint` umbrella mints a chromosome AT BUILD TIME from raw leaves; ``mint_strand``
    mints a strand that is ALREADY PACKED — a :func:`kernel_pack` / :func:`graph_to_kernel`
    strand (the corpus directed-graph store), any :func:`chromosome`, or one nuclear COMMUNITY —
    WITHOUT re-minting it from leaves. This is the capability §100 GAP 1 named as missing:
    ``chromosome(packed_strand, centromere=…)`` REJECTS an already-packed strand (it treats the
    strand as raw leaves and :func:`quad_turn` binds the 256-sector telomere cap →
    ``"klein-4 elements must be in {0,1,2,3}"``), and there was no ``centromere=`` hook on
    :func:`graph_to_kernel` — so a directed-graph chromosome could not be given a p:q centromere
    (``simplewiki_directed.genome`` censused ``{plasmid: 2, nuclear: 0}``). ``mint_strand`` is the
    missing splice; it is also the foundation for §100 GAP 2 (mint each NUCLEAR community) and the
    streaming reader (a nuclear chromosome IS the eukaryotic/nuclear DNA).

    The centromere is an INTERIOR cap; :func:`recall` / :func:`kernel_unpack` /
    :func:`kernel_to_graph` ALL skip caps (§44), so minting is TRANSPARENT to the payload — the
    recovered kernel / graph is **BYTE-IDENTICAL** with or without the centromere.

    * ``centromere_at`` — the arm-split measured in DATA TURNS (the cap goes AFTER that many data
      turns; ``0 <= centromere_at <= n_turns``). Default the METACENTRIC midpoint ``n_turns // 2``,
      matching :func:`chromosome`'s mint default — POSITION IS the p:q arm-ratio (biology: the
      centromere position defines the arms), so a 30-turn strand mints ``(15, 15)`` and a 9-turn
      strand ``(4, 5)``. Recover the p:q with :func:`centromere_of`.
    * ``orientation`` — the GLOBAL 4-way which-way ∈ ``{0,1,2,3}`` (Class-C chirality). Default the
      content-address fold ``sha256(recovered leaves)[0] & 3`` — the SAME Class-A→Class-C rule
      :func:`mint` assigns (:func:`_mint_orientation`), applied to the strand's OWN recovered
      leaves, so it is deterministic + attested (it IS the content-address, no magic number).
    * ``repeats`` / ``handle`` — the α-satellite repeat-array size + the CENP-A inline epigenetic
      address, passed through to :func:`centromere`.

    rc277 (§100 GAP 1 / G5): DISPATCHES the WHOLE op (data-turn scan → content-address orientation
    → centromere cap → single-block splice) to the byte-identical C peer ``srmech_genome_mint_strand``
    when ``HAS_NATIVE`` — a bare-C host PROMOTES a strand end-to-end via that ONE call (the cap-writer
    ``srmech_genome_centromere`` already had a C peer; before rc277 its glue was Python-only). The
    pure path (the native-dispatched :func:`centromere` cap-writer + a block splice, like
    :func:`integrate` — self-describing blocks concatenated, no re-coupling) is the numpy-free
    fallback + parity oracle, so the minted strand is byte-identical whether native or pure (the
    parity contract). After minting, ``genome_save`` +
    :func:`genome_census` report the chromosome as ``nuclear`` (the ``0x58`` is present). Raises if
    the strand is empty, does not OPEN with a chromosome-boundary cap (pass a :func:`chromosome` /
    :func:`kernel_pack` / :func:`graph_to_kernel` strand, NOT raw leaves), or ALREADY carries a
    centromere (re-minting would double the anchor). Class A (the content-address orientation) ∘
    Class C (the which-way) ∘ Class K (position = p:q). numpy-free; no ``abs()``."""
    strand = list(strand)
    if not strand:
        raise ValueError("mint_strand: strand is empty — nothing to mint")
    if _cap_kind(strand[0]) not in _CHROM_BOUNDARY_MARKERS:
        raise ValueError(
            "mint_strand: strand must OPEN with a chromosome-boundary cap (a CHROM / kernel / "
            "active / diploid telomere) — pass an ALREADY-PACKED strand (chromosome / kernel_pack "
            "/ graph_to_kernel), NOT raw leaves (raw leaves go through mint / chromosome(centromere=))"
        )
    if any(_cap_kind(hv) == CENTROMERE_CAP_MARKER for hv in strand):
        raise ValueError(
            "mint_strand: strand already carries an interior centromere (0x58) — it is already "
            "minted; re-minting would double the arm-split anchor"
        )
    # §101: a single pre-op gate — a splice has no meaningful partial, so a truthy
    # progress return DECLINES cleanly, returning the valid UNMODIFIED pre-mint strand
    # (the recall decode below is the op's cost; the honest-decline avoids it).
    if progress is not None and progress(
            {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_MINTING,
             "done": 0, "total": 1}):
        return strand
    dim = len(list(coupling))
    # §95a: POSITION is the p:q arm-ratio, measured in DATA TURNS (the non-cap leaves) — the SAME
    # units centromere_of reads back (p = data turns BEFORE the cap, q = data turns AFTER). The
    # opening telomere + any interior gene caps are skipped; the metacentric default splits the
    # data turns in half (chromosome()'s mint default).
    data_positions = [i for i, hv in enumerate(strand) if _cap_kind(hv) is None]
    n_turns = len(data_positions)
    split = n_turns // 2 if centromere_at is None else int(centromere_at)
    if not 0 <= split <= n_turns:
        raise ValueError(
            f"mint_strand: centromere_at={centromere_at} out of range [0, {n_turns}] "
            f"(the arm-split index in DATA turns between the short + long arm)"
        )
    # rc277 (#891-peer / G5): DISPATCH the whole scan → orientation → cap → splice to the
    # srmech_genome_mint_strand C peer when HAS_NATIVE + uniform fixed-width leaf_dim blocks
    # — byte-identical (the recall-derived content-address orientation, the SAME native
    # centromere cap-writer, the SAME block splice). A bare-C host PROMOTES a strand end-to-
    # end via that ONE peer; here it proves native == pure. The pure path below is the numpy-
    # free fallback + parity oracle (a non-uniform-width strand, a NUL/over-long handle, or a
    # bad orientation/repeats falls through so its exact ValueError surfaces). NEVER abs()
    # (the split is a position, the orientation a content-address sector — no magnitude).
    raw_handle = handle.encode("utf-8") if isinstance(handle, str) else bytes(handle)
    blocks = _leaf_blocks(strand)
    if (dim > 0 and blocks and b"\x00" not in raw_handle
            and all(len(b) == dim for b in blocks)):
        native = _native.genome_mint_strand_c(
            b"".join(blocks), len(blocks), dim, _coupling_block_bytes(coupling),
            split, orientation, repeats, raw_handle)
        if native is not None:
            return [_hv_from_block(native[i * dim:(i + 1) * dim])
                    for i in range(len(native) // dim)]
    if orientation is None:
        # Class A content-address → Class C chirality: sha256(the strand's OWN recovered leaves)
        # [0] & 3 — the SAME rule mint() assigns a nuclear chromosome (_mint_orientation), so the
        # which-way is deterministic + attested (no magic number). recall skips every cap, so this
        # is the content the payload decode also sees.
        orientation = _mint_orientation(recall(strand, coupling))
    # Native-dispatched cap-writer (byte-identical C peer srmech_genome_centromere); the splice is
    # pure block concatenation, so the minted strand is byte-identical to a C-produced one.
    cen_cap = centromere(orientation, repeats=repeats, handle=handle, dim=dim)
    insert_at = data_positions[split] if split < n_turns else len(strand)
    return strand[:insert_at] + [cen_cap] + strand[insert_at:]


# ─────────────────────────────────────────────────────────────────────────────
# §100 GAP 2 (PR#687 F1250-F1251) — PARTITION A GRAPH BY ITS OWN STRUCTURE.
#
# The mint() umbrella decides each kernel's chromosome SHAPE by LEAF-COUNT (a
# ≤4-leaf kernel → a plasmid, a ≥5-leaf kernel → a nuclear chromosome). §100 GAP 2:
# for a directed relational GRAPH the builder must instead find the data's OWN
# nuclear-core vs plasmid-periphery split FROM ITS RELATIONAL STRUCTURE — biology
# does not size a chromosome by how many genes it has, it reads the community
# topology (a stable clonal CORE + a mobile ACCESSORY genome; F1251, attested
# bacterial genomics: a small stable core + a large mobile accessory).
#
# The criterion is triple-grounded + settled (§100.1 / F1250 / F1251):
#
#  * METRIC = degree-normalized PARTICIPATION, the fraction of a node's incident
#    edge-mass that CROSSES a community boundary. (F1053 first used the clustering
#    coefficient; §100.1/F1250 MEASURED that clustering is unimodal at the 831k
#    word-graph scale and washes out — participation is the read-INDEPENDENT
#    discriminator that survives.) HIGH participation = a community-bridging shared
#    service = PLASMID / organelle (F1059's power source); LOW participation = a node
#    embedded in ONE community = NUCLEAR (the stable topical core).
#  * DECISION = MEASURE the antimode gap in the participation distribution. Genuinely
#    BIMODAL → split into nuclear (low) + plasmid (high); UNIMODAL (no clean antimode)
#    → ACCEPT ONE-DNA-TYPE, do NOT force a split (F1250: the word graph is "one
#    bridged content mass" + a small peripheral part — one dominant DNA type).
#  * SHAPE = an ASYMMETRIC minority nuclear core (~16/84 — F1251). Even when it splits,
#    expect a SMALL nuclear core + a LARGE plasmid remainder, not 50/50.
#  * SCOPE = a FULL-GRAPH community assignment (out-of-core recursive_cut: you need the
#    periphery to see the nuclear cliques).
# ─────────────────────────────────────────────────────────────────────────────

#: Default histogram resolution for the participation antimode (§100 GAP 2). 16 bins
#: over [0, 1] is fine enough to resolve a clean nuclear/plasmid valley yet coarse
#: enough that a single bridged mass reads as ONE contiguous mode (F1250).
_PARTITION_DEFAULT_BINS = 16


def _partition_validate_graph(n, edges, weights, charges):
    """Validate + materialise ``(edge_list, weight_list, charge_list)`` for §100 GAP
    2 (integer edge metric — no float in the participation math). ``weights`` default
    to unit multiplicity; every weight must be a NON-NEGATIVE integer (the co-occurrence
    metric graph_to_kernel stores), and ``charges`` (signed direction) ride through
    unchanged for the builder round-trip. O(|E|) sparse — NEVER the dense n×n structure."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError(f"genome_partition: n must be a non-negative int; got {n!r}")
    edge_list = [(int(u), int(v)) for (u, v) in edges]
    for i, (u, v) in enumerate(edge_list):
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(
                f"genome_partition: edge {i} = ({u}, {v}) outside node range [0, {n})")
    if weights is None:
        weight_list = [1] * len(edge_list)
    else:
        weight_list = []
        for w in weights:
            iw = int(w)
            if iw != w:
                raise ValueError(
                    "genome_partition: weights must be integers (the edge metric / "
                    "co-occurrence count) — participation is an exact rational, no float")
            if iw < 0:
                raise ValueError("genome_partition: weights must be non-negative")
            weight_list.append(iw)
        if len(weight_list) != len(edge_list):
            raise ValueError(
                f"genome_partition: weights length {len(weight_list)} != n_edges "
                f"{len(edge_list)}")
    if charges is None:
        charge_list = [0] * len(edge_list)
    else:
        charge_list = [int(c) for c in charges]
        if len(charge_list) != len(edge_list):
            raise ValueError(
                f"genome_partition: charges length {len(charge_list)} != n_edges "
                f"{len(edge_list)}")
    return edge_list, weight_list, charge_list


def _partition_participation(n, edge_list, weight_list, community):
    """Per-node PARTICIPATION as an exact integer pair ``(cross, tot)`` (§100 GAP 2).

    Streams the sparse edge list ONCE (O(|E|), never the dense structure): ``tot[v]`` =
    the total incident edge-mass of ``v``; ``cross[v]`` = the incident edge-mass that
    crosses to a node in a DIFFERENT community. participation(v) = ``cross[v]/tot[v]`` ∈
    [0, 1] — an exact non-negative rational (Class-N), NEVER ``abs()``. Only the two
    O(n) accumulators are resident. A self-loop is fully internal (same community); an
    isolated node has ``tot == 0`` → participation ``(0, 1)`` (no bridging)."""
    cross = [0] * n
    tot = [0] * n
    for (u, v), w in zip(edge_list, weight_list):
        tot[u] += w
        tot[v] += w
        if community[u] != community[v]:
            cross[u] += w
            cross[v] += w
    return cross, tot


def _partition_bin(cross_v, tot_v, n_bins):
    """The participation histogram bin of one node — pure INTEGER arithmetic (no float):
    ``floor(participation · n_bins)`` clamped to ``[0, n_bins-1]``. ``tot == 0`` (isolated)
    → bin 0 (participation 0). ``cross == tot`` (fully bridging) → the top bin."""
    if tot_v <= 0:
        return 0
    b = (cross_v * n_bins) // tot_v
    if b >= n_bins:
        return n_bins - 1
    return b


def _side_argmax(counts, lo, hi):
    """The bin of the maximum count in ``counts[lo:hi+1]`` (lowest index on a tie) — the
    dominant mode of one side of an antimode gap. Pure integer; no float."""
    best = lo
    for b in range(lo, hi + 1):
        if counts[b] > counts[best]:
            best = b
    return best


def _partition_antimode(counts):
    """MEASURE the antimode of the participation histogram — the settled §100 GAP 2
    bimodal/unimodal DECISION (F1250), pure integer, deterministic, no float.

    Walks the GAPS between consecutive OCCUPIED bins. A gap is a real antimode iff it is
    at least one bin WIDE (a genuine empty separation, not adjacent bins), the DOMINANT
    mode on EACH side is a real mode (≥ 2 nodes), and the in-gap valley is empty-relative
    (``2·valley < min(peak_low, peak_high)``). The distribution is BIMODAL iff such a gap
    exists; we split at the WIDEST qualifying gap (ties → the larger smaller-mode, then the
    lower bin) so the split isolates the true high-participation PLASMID tail from the whole
    low mass — even when a few near-core nodes form a spurious middle cluster (which stays
    NUCLEAR). A single contiguous mass has no wide empty-relative gap → UNIMODAL (one bridged
    content mass, F1250) — we do NOT force a split.

    Returns ``{bimodal, threshold_bin, peak_low_bin, peak_high_bin, valley_count, gap,
    mode_bin}``. ``threshold_bin`` is the low occupied bin at the split (plasmid iff a node's
    bin is strictly ABOVE it). On unimodal, ``threshold_bin`` is ``None`` and ``mode_bin`` is
    the single dominant mode (its half of [0,1] fixes the one-DNA-type)."""
    n_bins = len(counts)
    occupied = [b for b in range(n_bins) if counts[b] > 0]
    # the single dominant mode (lowest index on a tie) — the one-DNA-type anchor.
    mode_bin = 0
    for b in range(n_bins):
        if counts[b] > counts[mode_bin]:
            mode_bin = b
    unimodal = {"bimodal": False, "threshold_bin": None, "peak_low_bin": None,
                "peak_high_bin": None, "valley_count": None, "gap": 0, "mode_bin": mode_bin}
    if len(occupied) < 2:
        return unimodal
    best = None                                   # (width, smaller_mode, lo_occ, hi_occ)
    for k in range(len(occupied) - 1):
        lo_occ = occupied[k]
        hi_occ = occupied[k + 1]
        width = hi_occ - lo_occ
        if width < 2:                             # adjacent occupied bins — no empty gap
            continue
        peak_low_bin = _side_argmax(counts, 0, lo_occ)
        peak_high_bin = _side_argmax(counts, hi_occ, n_bins - 1)
        peak_low = counts[peak_low_bin]
        peak_high = counts[peak_high_bin]
        smaller = peak_low if peak_low < peak_high else peak_high
        if smaller < 2:                           # a side with no real mode
            continue
        valley = min(counts[lo_occ + 1:hi_occ])   # the in-gap antimode (empty here)
        if 2 * valley < smaller:                  # a genuine empty-relative valley
            cand = (width, smaller, lo_occ, hi_occ)
            if best is None or cand[:2] > best[:2]:
                best = cand
    if best is None:
        return unimodal
    _width, smaller, lo_occ, hi_occ = best
    peak_low_bin = _side_argmax(counts, 0, lo_occ)
    peak_high_bin = _side_argmax(counts, hi_occ, n_bins - 1)
    valley = min(counts[lo_occ + 1:hi_occ])
    gap = smaller - valley                          # both non-negative; NEVER abs()
    return {"bimodal": True, "threshold_bin": lo_occ, "peak_low_bin": peak_low_bin,
            "peak_high_bin": peak_high_bin, "valley_count": valley, "gap": gap,
            "mode_bin": mode_bin}


def _reduce_pair(num, den):
    """A non-negative ``(num, den)`` reduced by the Class-I gcd; ``den == 0`` → ``(0, 1)``
    (an isolated node has no participation). Numpy-free; no ``abs()`` (both non-negative)."""
    if den <= 0:
        return (0, 1)
    g = _gcd(num, den) or 1
    return (num // g, den // g)


def genome_partition(n, edges, weights=None, charges=None, *,
                     work_dir=None, max_tome=256, n_bins=_PARTITION_DEFAULT_BINS,
                     max_iters=250, progress=None):
    """PARTITION a directed relational GRAPH into nuclear-core vs plasmid-periphery BY
    ITS OWN STRUCTURE — the §100 GAP 2 read (PR#687 / F1250 / F1251). Builds NOTHING (an
    introspectable read, like :func:`mint_plan` — "we watch it happen"); :func:`genome_from_graph`
    is the builder that consumes this to mint the genome.

    Where :func:`mint_plan` decides a kernel's shape by LEAF-COUNT (≤4 → plasmid, ≥5 →
    nuclear), THIS finds the split from the graph's relational TOPOLOGY: it runs the
    out-of-core spectral community partition (:func:`~srmech.amsc.laplacian.recursive_cut` —
    peak RAM = the largest sub-graph, never the dense n×n structure), measures each node's
    degree-normalized **participation** (the fraction of its incident edge-mass that CROSSES
    a community boundary — HIGH = a community-bridging PLASMID/mobile accessory; LOW = a
    NUCLEAR node embedded in one community), then MEASURES the antimode of that distribution:

    * **BIMODAL** (a clean antimode valley) → SPLIT. Each recursive_cut community contributes
      its embedded-core NUCLEAR nodes (participation below the antimode) as a nuclear group and
      its bridging PLASMID nodes (above the antimode) as a plasmid group. Expect an ASYMMETRIC
      minority nuclear core + majority plasmid remainder (F1251 — NOT 50/50).
    * **UNIMODAL** (no clean antimode) → ACCEPT ONE-DNA-TYPE. Do NOT force a split — every
      community is one group of the single dominant type (F1250: "one bridged content mass").

    The classification is per-NODE (participation is robust even when recursive_cut absorbs a
    bridge node into a community — a bridge still crosses to the other community); a group is a
    ``(community, type)`` slice, so the builder mints each nuclear community and keeps each
    plasmid community as a stick/plasmid chromosome.

    Parameters
    ----------
    n : int
        Node count (nodes are ``0..n-1``).
    edges : Iterable[Tuple[int, int]]
        Directed edges ``(u, v)`` (treated as undirected for community detection +
        boundary-crossing — a relation bridges regardless of its direction).
    weights : Optional[Iterable[int]]
        Per-edge INTEGER metric (co-occurrence count); default unit multiplicity. The
        participation ratio is exact-rational (Class-N) — non-integer weights are rejected.
    charges : Optional[Iterable[int]]
        Per-edge signed direction; carried through for :func:`genome_from_graph` (unused by
        the participation read — a relation bridges regardless of sign; sign stays Class-C).
    work_dir : Optional[str]
        Scratch dir for recursive_cut's on-disk tomes (caller owns it; not auto-deleted).
    max_tome : int
        recursive_cut leaf size — a sub-graph with ``≤ max_tome`` nodes is a community. Smaller
        exposes finer communities (a natural community must stay WHOLE, else over-splitting a
        clique inflates its participation).
    n_bins : int
        Participation-histogram resolution for the antimode (default 16).
    max_iters : int
        Per-bisection power-iteration cap (forwarded to recursive_cut).

    Returns
    -------
    Dict[str, object]
        An introspectable partition::

            {"n", "n_communities", "bimodal": bool, "one_dna_type": None|"nuclear"|"plasmid",
             "antimode": {bins, counts, threshold_bin, peak_low_bin, peak_high_bin,
                          valley_count, gap, bimodal},
             "participation": [(num, den), … per node 0..n-1],   # exact reduced rationals
             "communities": [[node, …], …],                       # the recursive_cut tomes
             "groups": [{"community", "type": "nuclear"|"plasmid", "nodes": [...],
                         "size", "participation": (num, den)}, …],
             "counts": {"nuclear": N, "plasmid": M},              # per-community-group
             "node_counts": {"nuclear": x, "plasmid": y},
             "work_dir"}

    Composes the C-dispatched :func:`~srmech.amsc.laplacian.recursive_cut`
    (fiedler_sparse_file) with a thin PURE participation + antimode read (O(|E|) + O(n),
    exact integer, numpy-free, never ``abs()``) — native==pure holds because the whole read
    is deterministic over the native community assignment. Class L (spectral community) ∘
    Class N (the exact participation rational) ∘ Class K (the antimode boundary)."""
    from srmech.amsc.laplacian import recursive_cut       # lazy — avoid import cycle

    edge_list, weight_list, _charge_list = _partition_validate_graph(
        n, edges, weights, charges)
    if not isinstance(n_bins, int) or isinstance(n_bins, bool) or n_bins < 2:
        raise ValueError(f"genome_partition: n_bins must be an int >= 2; got {n_bins!r}")

    # SCOPE — the full-graph out-of-core community assignment (never the dense structure).
    # §101: progress= threads the PARTITIONING heartbeat into recursive_cut (the dominant
    # cost). On cancel the community assignment is still valid → return a CLEAN partial.
    cut = recursive_cut(n, edge_list, weight_list, max_tome=max_tome,
                        work_dir=work_dir, max_iters=max_iters, progress=progress)
    if cut.get("status") == GENOME_STATUS_CANCELLED:
        communities = [sorted(t) for t in cut["tomes"]]
        return {
            "n": n, "n_communities": len(communities), "bimodal": False,
            "one_dna_type": None, "antimode": None, "participation": [],
            "communities": communities, "groups": [],
            "counts": {"nuclear": 0, "plasmid": 0},
            "node_counts": {"nuclear": 0, "plasmid": 0},
            "work_dir": cut["work_dir"], "status": GENOME_STATUS_CANCELLED,
        }
    communities = [sorted(t) for t in cut["tomes"]]
    community = [0] * n
    for cid, tome in enumerate(cut["tomes"]):
        for nid in tome:
            community[nid] = cid

    # METRIC — per-node participation (the degree-normalized boundary-crossing fraction).
    cross, tot = _partition_participation(n, edge_list, weight_list, community)
    participation = [_reduce_pair(cross[v], tot[v]) for v in range(n)]

    # DECISION — measure the antimode of the participation distribution.
    counts = [0] * n_bins
    node_bin = [0] * n
    for v in range(n):
        b = _partition_bin(cross[v], tot[v], n_bins)
        node_bin[v] = b
        counts[b] += 1
    am = _partition_antimode(counts)

    # CLASSIFY — per-node nuclear (low participation) vs plasmid (high participation).
    if am["bimodal"]:
        threshold_bin = am["threshold_bin"]
        one_dna_type = None
        node_type = ["plasmid" if node_bin[v] > threshold_bin else "nuclear"
                     for v in range(n)]
    else:
        # ACCEPT ONE-DNA-TYPE — the whole assigned to the single dominant type (F1250):
        # a mode in the LOW half of [0,1] reads nuclear (embedded), else plasmid (bridging).
        one_dna_type = "nuclear" if am["mode_bin"] * 2 < n_bins else "plasmid"
        node_type = [one_dna_type] * n

    # GROUPS — each community sliced into its nuclear core + plasmid periphery (SHAPE:
    # asymmetric — a small nuclear core, a large plasmid remainder, never forced 50/50).
    groups = []
    for cid, tome in enumerate(communities):
        for gtype in ("nuclear", "plasmid"):
            members = [v for v in tome if node_type[v] == gtype]
            if not members:
                continue
            gc = sum(cross[v] for v in members)
            gt = sum(tot[v] for v in members)
            groups.append({
                "community": cid, "type": gtype, "nodes": members,
                "size": len(members), "participation": _reduce_pair(gc, gt),
            })

    counts_by_type = {"nuclear": 0, "plasmid": 0}
    for g in groups:
        counts_by_type[g["type"]] += 1
    node_counts = {"nuclear": sum(1 for t in node_type if t == "nuclear"),
                   "plasmid": sum(1 for t in node_type if t == "plasmid")}

    return {
        "n": n,
        "n_communities": len(communities),
        "bimodal": am["bimodal"],
        "one_dna_type": one_dna_type,
        "antimode": {
            "bins": n_bins, "counts": counts, "threshold_bin": am["threshold_bin"],
            "peak_low_bin": am["peak_low_bin"], "peak_high_bin": am["peak_high_bin"],
            "valley_count": am["valley_count"], "gap": am["gap"], "bimodal": am["bimodal"],
        },
        "participation": participation,
        "communities": communities,
        "groups": groups,
        "counts": counts_by_type,
        "node_counts": node_counts,
        "work_dir": cut["work_dir"],
        "status": GENOME_STATUS_OK,
    }


def _induced_subgraph(nodes, edge_list, weight_list, charge_list):
    """The sub-graph INDUCED on ``nodes`` (a community), RELABELLED to local ids
    ``0..k-1`` — the §100 GAP 2 builder's per-community store unit. Keeps every edge with
    BOTH endpoints in ``nodes`` (a cross-community bridge edge is not in any single
    induced sub-graph — it is represented by the bridge node's PLASMID classification),
    carrying its weight + signed charge. Returns ``{vocab_size, edges, weights, charges,
    node_ids}`` — ``node_ids`` is the original id table so :func:`kernel_to_graph` recovers
    the mapping. O(|E|); numpy-free."""
    local = {orig: i for i, orig in enumerate(nodes)}
    edges = []
    weights = []
    charges = []
    for (u, v), w, c in zip(edge_list, weight_list, charge_list):
        lu = local.get(u)
        lv = local.get(v)
        if lu is not None and lv is not None:
            edges.append((lu, lv))
            weights.append(w)
            charges.append(c)
    return {"vocab_size": len(nodes), "edges": edges, "weights": weights,
            "charges": charges, "node_ids": list(nodes)}


def genome_from_graph(n, edges, weights=None, charges=None, *, coupling,
                      path=None, leaf_dim=None, max_tome=256,
                      n_bins=_PARTITION_DEFAULT_BINS, centromere_at=None,
                      progress=None, attestation=None):
    """BUILD a multi-chromosome genome from a directed graph, PARTITIONED BY ITS OWN
    STRUCTURE — the §100 GAP 2 builder (PR#687 / F1250 / F1251). "Hand a graph, get
    nuclear + plasmid from its structure."

    Runs :func:`genome_partition`, then for EACH classified group packs its induced
    sub-graph (:func:`_induced_subgraph` → :func:`graph_to_kernel`) into a chromosome:

    * a **nuclear** community is MINTED (:func:`mint_strand` splices a ``0x58`` centromere →
      a Tier-2 nuclear chromosome, the stable clonal core);
    * a **plasmid** community is KEPT as a Tier-1 plasmid chromosome (append-only, no
      centromere — the mobile accessory).

    All chromosomes concatenate into one self-describing strand (each opens with its
    kernel-telomere boundary cap). If ``path`` is given the strand is persisted with
    :func:`genome_save` and censused — ``genome_census`` reports the MEASURED
    ``{nuclear: N, plasmid: M}``. The genome is BYTE-EXACT per community:
    :func:`kernel_to_graph` on any chromosome (with its ``n_syms``) recovers that community's
    induced sub-graph exactly (the interior centromere is skipped on read, §44).

    Parameters
    ----------
    n, edges, weights, charges
        The directed signed graph (as :func:`genome_partition`).
    coupling : HV
        The coupling invariant (width ``leaf_dim``); required.
    path : Optional[str|Path]
        If given, ``genome_save`` the assembled strand there and include the census in the
        return; else only the in-memory strand + metadata are returned.
    leaf_dim : Optional[int]
        The leaf (tome) width to chunk each chromosome into (default ``len(coupling)``; must
        be ≥ 52 for the kernel header).
    max_tome, n_bins
        Forwarded to :func:`genome_partition`.
    centromere_at : Optional[int]
        The nuclear arm-split forwarded to :func:`mint_strand` (default the metacentric
        midpoint of each minted community).
    attestation : Optional[dict]
        When ``path`` is given, a caller MPR SOURCE-attestation forwarded to
        :func:`genome_save` — the provided fields OVERRIDE the srmech default written into
        ``manifest.json`` (override-only over the five source-identity fields
        ``source_doi`` / ``source_url`` / ``license`` / ``retrieved_at`` /
        ``response_sha256``). For an attested corpus genome (e.g. a simplewiki dump whose
        true source is ``https://dumps.wikimedia.org/simplewiki/latest/`` under
        CC-BY-SA-4.0) this records the REAL provenance genome-natively, in the only
        legitimate place (no sidecar files, §41/F1300). A malformed override raises. No
        effect when ``path`` is None (nothing is persisted).

    Returns
    -------
    Dict[str, object]
        ``{"strand", "chromosomes": [{"label", "type", "community", "n_syms", "nodes"}, …],
        "partition", "counts": {"nuclear", "plasmid"}, "path"(if saved), "census"(if saved)}``.

    Composes :func:`genome_partition` (composition-of-C) + the C-dispatched
    :func:`graph_to_kernel` + :func:`mint_strand` (composition-of-C) + :func:`genome_save` —
    numpy-free; no ``abs()``. Class L (partition) ∘ Class A/C/K (the mint)."""
    if coupling is None:
        raise ValueError("genome_from_graph: coupling is required")
    if leaf_dim is None:
        leaf_dim = len(list(coupling))

    edge_list, weight_list, charge_list = _partition_validate_graph(
        n, edges, weights, charges)
    # §101: progress= threads the heartbeat into the partition (PARTITIONING) AND the
    # per-group mint loop below (MINTING). A cancelled partition short-circuits here.
    part = genome_partition(n, edge_list, weight_list, charge_list,
                            max_tome=max_tome, n_bins=n_bins, progress=progress)
    if part.get("status") == GENOME_STATUS_CANCELLED:
        return {"strand": [], "chromosomes": [], "partition": part,
                "counts": {"nuclear": 0, "plasmid": 0},
                "status": GENOME_STATUS_CANCELLED}

    strand = []
    chromosomes = []
    groups = part["groups"]
    for gi, g in enumerate(groups):
        if progress is not None and progress(
                {"struct_size": _PROGRESS_STRUCT_SIZE, "phase": _PHASE_MINTING,
                 "done": gi, "total": len(groups)}):
            # §101 CLEAN partial: whole chromosomes minted so far == a valid (shorter)
            # genome strand. Do NOT genome_save on cancel — no half-written body on disk.
            return {"strand": strand, "chromosomes": chromosomes, "partition": part,
                    "counts": {"nuclear": sum(1 for c in chromosomes
                                              if c["type"] == "nuclear"),
                               "plasmid": sum(1 for c in chromosomes
                                              if c["type"] == "plasmid")},
                    "status": GENOME_STATUS_CANCELLED}
        nodes = g["nodes"]
        sub = _induced_subgraph(nodes, edge_list, weight_list, charge_list)
        # a UNIQUE, self-describing label per chromosome (type + community + slot).
        label = f"{g['type']}_c{g['community']}_{gi}"
        chrom, n_syms = graph_to_kernel(
            sub["vocab_size"], sub["edges"], sub["weights"], sub["charges"],
            node_ids=sub["node_ids"], leaf_dim=leaf_dim, label=label, coupling=coupling)
        if g["type"] == "nuclear":
            # MINT the nuclear community — a Tier-2 nuclear chromosome (0x58 centromere).
            chrom = mint_strand(chrom, coupling, centromere_at=centromere_at)
        strand.extend(chrom)
        chromosomes.append({"label": label, "type": g["type"],
                            "community": g["community"], "n_syms": n_syms,
                            "nodes": nodes})

    out = {
        "strand": strand,
        "chromosomes": chromosomes,
        "partition": part,
        "counts": dict(part["counts"]),
        "status": GENOME_STATUS_OK,
    }
    if path is not None and strand:
        genome_save(strand, path, coupling, attestation=attestation)
        out["path"] = str(path)
        out["census"] = genome_census(str(path), coupling=coupling)
    return out


def telomere_tick(strand):
    """The divide/gate op — the ACTIVE TELOMERE's count MODULATES the operator (§127/#726).

    ``strand`` is a chromosome strand that OPENS with an :func:`active_telomere` cap (a
    ``0x74`` marker carrying an exact Hayflick count inline). This op reads that count
    (the **operand**) and its behaviour (the **operator**) is SELECTED by it — the same
    ``telomere_tick`` call proceeds or refuses depending ONLY on the operand:

    * **count > 0 → DIVIDE.** Decrement the count by exactly 1 (the telomere SHORTENS),
      and return the DAUGHTER strand — the same coupled leaves led by an active telomere
      of count ``count - 1`` (the telomere GOVERNS the leaves without decoding them:
      biology shortens the cap, it does not re-synthesise the genes). Status
      :data:`TELOMERE_DIVIDED`.
    * **count == 0 → SENESCENCE.** Refuse HONESTLY — no daughter (``daughter=None``) —
      with status :data:`TELOMERE_SENESCENT` (the inform-don't-crash / honest-decline
      pattern: a clean verdict, NEVER a crash). This is the Hayflick limit
      (Hayflick & Moorhead 1961; Hayflick 1965) — a cell that has exhausted its
      replicative counter stops dividing.

    An active telomere of count ``N`` therefore allows EXACTLY ``N`` divides, then the
    ``N+1``-th refuses. THE op⊗operand DUALITY, made testable: op = the gating rule
    here, operand = the count, FUSED in the ONE cap — the SAME ``(operand, op)`` pattern
    as :func:`srmech.amsc.op_provenance.carry` and
    :class:`srmech.amsc.coupling.RecoverableFold`, but with an ACTIVE op (the operand
    changes how the operator works), which is precisely why the chromosome is now a
    GENUINE op⊗operand (in #726 a plain telomere was a passive op-slot).

    Returns a status dict::

        {"status": "divided"|"senescent", "label": <chromosome label>,
         "count_before": N, "count_after": N-1 (divided) | 0 (senescent),
         "daughter": <daughter strand> | None}

    Needs NO ``coupling`` — the count lives in the cap, so the gate reads it from the
    bare strand (§44 self-description). Native-dispatched (byte-identical C peer
    ``srmech_genome_telomere_tick``); pure Python is the complete alternative. Raises
    ``ValueError`` if ``strand`` does not open with an active telomere.
    """
    strand = list(strand)
    if not strand:
        raise ValueError("telomere_tick: empty strand has no telomere to tick")
    cap = strand[0]
    if _cap_kind(cap) != ACTIVE_TELOMERE_MARKER:
        raise ValueError(
            "telomere_tick: strand does not open with an active telomere (0x74) — "
            "build one with chromosome(leaves, coupling, active_count=N)")
    label = _active_telomere_label(cap)
    dim = len(cap)
    native = _telomere_tick_native(cap)
    if native is not None:
        senescent, count_after, new_cap_bytes = native
        count_before = _active_telomere_count(cap)
        if senescent:
            return {"status": TELOMERE_SENESCENT, "label": label,
                    "count_before": count_before, "count_after": count_before,
                    "daughter": None}
        daughter = [_hv_from_block(bytes(new_cap_bytes))] + strand[1:]
        return {"status": TELOMERE_DIVIDED, "label": label,
                "count_before": count_before, "count_after": count_after,
                "daughter": daughter}
    # pure path — the complete alternative when there is no C.
    count = _active_telomere_count(cap)
    if count == 0:
        return {"status": TELOMERE_SENESCENT, "label": label,
                "count_before": 0, "count_after": 0, "daughter": None}
    daughter_cap = _pack_active_telomere(label, count - 1, dim)
    return {"status": TELOMERE_DIVIDED, "label": label,
            "count_before": count, "count_after": count - 1,
            "daughter": [daughter_cap] + strand[1:]}


# ─────────────────────────────────────────────────────────────────────────────
# UPSTREAM §41 — genome persistence (disk save / load / catalog / append /
# window). The helix grows ON DISK: a genome directory is
#
#   path/manifest.json   an MPRRecord (MPR v1) describing the chromosome set —
#                        the CATALOG (leaf_dim, per-chromosome cap_sha256 /
#                        leaf_count / byte_offset / byte_len, body_sha256). Read
#                        the manifest WITHOUT touching the body (genome_catalog).
#   path/turns.bin       the append-only flat body: every strand element (a cap
#                        or a coupled turn) is one self-describing block whose
#                        FIRST byte keys its kind + width — a leaf_dim-byte cap,
#                        a §55/v3 BIT-PACKED data turn (1 + ceil(leaf_dim/4)
#                        bytes, 4 Klein-4 symbols per byte), or a legacy v2
#                        leaf_dim-byte byte-per-symbol turn. No length prefixes —
#                        chromosome boundaries live in the manifest as
#                        byte_offset/byte_len (and rebuild by scan).
#
# Bounding == integrity: every read re-hashes the bytes it read (via
# sha256_bytes) against the stored body / chromosome / cap hash; a mismatch is a
# GenomeBoundingError. RAM is bounded by the largest single chromosome — load
# streams block-by-block, window seeks to one chromosome's region.
# ─────────────────────────────────────────────────────────────────────────────

#: MPR on-disk format version for a genome directory (bumped on a body layout
#: change). 1 == content-address telomere caps + manifest-described boundaries.
#: 2 (§44) == self-describing fixed-width strand: chromosome + gene boundaries are
#: INLINE packed caps scanned-for in the body (the strand is the SSoT; the manifest
#: is an optional derived ``.fai``-style cache, rebuildable by scanning the body).
#: 3 (§55/rc114, issue #1245) == BIT-PACKED data turns: a data turn is written as
#: ``[PACKED_TURN_MARKER] + ceil(leaf_dim/4)`` bytes (4 Klein-4 symbols per byte —
#: the measured 4.03x byte-per-symbol bloat removed), while cap blocks keep their
#: v2 ``leaf_dim``-byte inline layout. The strand stays self-describing (every
#: block's FIRST byte keys kind + width), so the walk reads v2, v3, and MIXED
#: bodies alike — back-compat is structural, not a converter. ``n_turns`` counts
#: strand BLOCKS (== v2's ``body_len / leaf_dim`` on a v2 body); ``body_sha256``
#: stays the whole-``turns.bin`` hash in v3 (unchanged semantics).
#: 4 (§56/rc115) == the manifest carries a ``regions`` array + the region-chain
#: ``body_sha256`` (O(1)-append integrity).
#: 5 (§60/rc121, issue #1245 REOPENED) == the SIZE-AGNOSTIC KERNEL HEADER: a
#: :func:`kernel_pack` strand may carry a ``KERNEL_HEADER_MARKER`` (``0x4B``) block
#: SELF-RECORDING the kernel's true length ``D`` + ``element_type`` + ``leaf_dim`` (so
#: an arbitrary-``D`` Klein-4 kernel reconstructs EXACTLY). The block is one more
#: self-describing kind in the SAME walk (its first byte keys it), so v2 / v3 / v4
#: bodies — and any v5 body with NO header — read UNCHANGED (a header-less body
#: defaults to ``element_type=klein4``, ``D = leaf_count × leaf_dim``): back-compat
#: is STRUCTURAL, not a converter (the rc114 dual-read pattern, one layer up).
#: 6 (§89/rc126, issue #1261) == the UNIFORMLY-KLEIN-4 KERNEL HEADER: a
#: :func:`kernel_pack` strand now opens with a ``KERNEL_TELOMERE_MARKER`` (``0x6B``)
#: cap and carries the header as a 100 %-Klein-4 coupled LEAF (base-4-encoded ``D`` +
#: ``element_type`` + ``leaf_dim``, :func:`_pack_kernel_header_klein4`) — the ``0x4B``
#: byte-TLV residue is GONE, so the store is uniformly Klein-4 and the O(1)
#: :func:`genome_append_kernel` rides the plain coupled-turn append. The ``0x6B`` cap
#: is one more self-describing kind in the SAME walk (its first byte keys it), so v2 /
#: v3 / v4 bodies — AND any v5 ``0x4B`` byte-TLV header — read UNCHANGED (dual-read):
#: back-compat is STRUCTURAL, never a converter. Every genome_save stamps the current
#: version (a v6 writer stamps 6 even for a non-kernel genome), as every prior bump.
#: 7 (§127/rc127, #726) == the ACTIVE TELOMERE: a chromosome MAY open with an
#: ``ACTIVE_TELOMERE_MARKER`` (``0x74``) cap carrying an exact Hayflick COUNT inline (a
#: descending replicative counter that :func:`telomere_tick` reads to gate a divide —
#: the op⊗operand cap that makes the chromosome a genuine op⊗operand theorem, #726). The
#: ``0x74`` cap is one more self-describing kind in the SAME walk (its first byte keys
#: it, its label read UNIFORMLY, its count after the label NUL), so v2 / v3 / v4 / v5 /
#: v6 bodies read UNCHANGED (dual-read — the walker gains ONE branch): back-compat is
#: STRUCTURAL, never a converter. A plain-telomere (no ``0x74``) genome saved by the v7
#: writer is byte-identical to the v6 writer's EXCEPT the ``format_version`` field (the
#: same version-stamp discipline every prior bump used — a v7 writer stamps 7).
#: 8 (§128/rc128, #728) == the REGULATORY GENE: an intra-chromosome gene MAY be opened by a
#: ``REGULATORY_GENE_MARKER`` (``0x67``) cap carrying an exact regulatory MASK inline (the
#: gene's "regulatory region / promoter" that :func:`gene_express` reads to gate which genes
#: express under an applied ``cell_state`` — the op⊗operand theorem one scale up from the v7
#: active telomere: the cell-state operand modulates the expression operator over MANY
#: genes, #728). Unlike the v6/v7 CHROMOSOME-boundary caps, the ``0x67`` cap is an
#: INTRA-chromosome gene delimiter (a gene-analog of the plain GENE cap ``0x47``); it is one
#: more self-describing kind in the SAME walk (its first byte keys it, its label read
#: UNIFORMLY, its mask after the label NUL), so v2 / v3 / v4 / v5 / v6 / v7 bodies read
#: UNCHANGED (dual-read — the walker gains ONE branch): back-compat is STRUCTURAL, never a
#: converter. A plain-gene (no ``0x67``) genome saved by the v8 writer is byte-identical to
#: the v7 writer's EXCEPT the ``format_version`` field (the same version-stamp discipline
#: every prior new-block-kind bump used — a v8 writer stamps 8), and every plain gene ALWAYS
#: EXPRESSES (an unregulated gene == a regulatory gene with mask 0).
#: 9 (§130/rc130, #730) == the BOOLEAN GENE: an intra-chromosome gene MAY be opened by a
#: ``BOOLEAN_GENE_MARKER`` (``0x62``) cap carrying ARBITRARY boolean regulatory logic inline (a
#: DNF — an OR of ``(require-present, require-absent)`` AND-clauses — that :func:`gene_express`
#: evaluates to gate which genes express, the GENERAL case of the v8 klein4-mask gene; #730). It
#: is the GENERAL gate-type in the rc129 dispatch FAMILY — the ``0x67`` klein4-mask gene stays
#: the fast common case; the ``0x62`` boolean gene is the escape hatch (E1 ⊂ E2: the klein4-mask
#: two-mask IS a 1-term DNF). Unlike the rc129 ``0x67`` extension (which reused an EXISTING
#: marker → no bump), this is a NEW marker byte = a new block KIND, so it bumps v8 → v9 exactly
#: as every prior new-marker bump did (rc127 ``0x74`` v6→v7, rc128 ``0x67`` v7→v8). The ``0x62``
#: cap is one more self-describing kind in the SAME walk (its first byte keys it, its label read
#: UNIFORMLY, its gate_type + DNF after the label NUL), so v2 / v3 / v4 / v5 / v6 / v7 / v8 bodies
#: read UNCHANGED (dual-read — the walker gains ONE branch): back-compat is STRUCTURAL, never a
#: converter. A plain / klein4-mask genome saved by the v9 writer is byte-identical to the v8
#: writer's EXCEPT the ``format_version`` field (the same version-stamp discipline every prior
#: new-block-kind bump used — a v9 writer stamps 9).
#: 10 (§131/rc131, #731) == the THRESHOLD GENE: an intra-chromosome gene MAY be opened by a
#: ``THRESHOLD_GENE_MARKER`` (``0x77``) cap carrying a LINEAR-THRESHOLD (perceptron) gate inline —
#: a per-condition SIGNED integer WEIGHT vector + an integer THRESHOLD that :func:`gene_express`
#: evaluates as ``Σᵢ weightᵢ·bit_i(cell_state) ≥ threshold`` to gate which genes express (#731). It
#: is the THIRD gate-type in the rc129 dispatch FAMILY (E1 klein4_mask ``0x67`` / E2 boolean_dnf
#: ``0x62`` / E4 threshold ``0x77``) — GENUINELY DISTINCT from E2 (a linear-threshold function
#: like MAJORITY-of-n needs an EXPONENTIAL DNF, so E4 captures compactly what E2's DNF cannot;
#: linear-threshold ⊄ small-DNF). This is a NEW marker byte = a new block KIND, so it bumps
#: v9 → v10 exactly as every prior new-marker bump did (rc127 ``0x74`` v6→v7, rc128 ``0x67``
#: v7→v8, rc130 ``0x62`` v8→v9). The ``0x77`` cap is one more self-describing kind in the SAME
#: walk (its first byte keys it, its label read UNIFORMLY, its gate_type + weights + threshold
#: after the label NUL), so v2..v9 bodies read UNCHANGED (dual-read — the walker gains ONE
#: branch): back-compat is STRUCTURAL, never a converter. A plain / klein4-mask / boolean genome
#: saved by the v10 writer is byte-identical to the v9 writer's EXCEPT the ``format_version``
#: field (the same version-stamp discipline every prior new-block-kind bump used — a v10 writer
#: stamps 10).
#: 11 (§132/rc132, #732) == the GRADED (dose-response) GENE: an intra-chromosome gene MAY be opened
#: by a ``GRADED_GENE_MARKER`` (``0x64``) cap carrying an ANALOG (dose-response) EXPRESSION LEVEL
#: inline — a per-condition SIGNED integer LEVEL-WEIGHT vector + a POSITIVE integer DENOMINATOR that
#: :func:`gene_express_levels` evaluates as the reduced exact rational ``Σᵢ level_weightᵢ·bit_i(
#: cell_state) / denom`` clamped to ``[0, 1]`` to report HOW MUCH each gene expresses (#732). It is
#: the **E3 GRADED LEVEL** rung — an ORTHOGONAL AXIS on top of the E1/E2/E4 gate-type family (the
#: gate-types decide IF; E3 decides HOW MUCH — analog output, real biology). This is a NEW marker
#: byte = a new block KIND, so it bumps v10 → v11 exactly as every prior new-marker bump did (rc127
#: ``0x74`` v6→v7, rc128 ``0x67`` v7→v8, rc130 ``0x62`` v8→v9, rc131 ``0x77`` v9→v10). The ``0x64``
#: cap is one more self-describing kind in the SAME walk (its first byte keys it, its label read
#: UNIFORMLY, its gate_type + n_weights + denom + weights after the label NUL), so v2..v10 bodies
#: read UNCHANGED (dual-read — the walker gains ONE branch): back-compat is STRUCTURAL, never a
#: converter. A plain / klein4-mask / boolean / threshold genome saved by the v11 writer is
#: byte-identical to the v10 writer's EXCEPT the ``format_version`` field (the same version-stamp
#: discipline every prior new-block-kind bump used — a v11 writer stamps 11).
#: v12 (O(1) genome-native append): the on-disk manifest is now HEAD-ONLY — it drops the
#: per-chromosome ``chromosomes`` / ``regions`` arrays (a plaintext table-of-contents, the
#: ADR-0003 regression) and keeps only the O(1) head (``format_version`` / ``leaf_dim`` /
#: ``n_turns`` / ``n_chromosomes`` / ``coupling`` / ``body_sha256`` chain head). The catalog
#: is DERIVED by scanning the self-describing body (``_catalog_data`` rebuilds it), so
#: ``genome_append`` rewrites only the tiny head (O(1)) instead of the whole array (the
#: O(N^2) wall). The BODY format is UNCHANGED (v2..v11 bodies read identically); a v≤11
#: manifest that still carries the arrays is read verbatim (back-compat), and the first v12
#: append rewrites it head-only. A v12 writer stamps 12.
#: v13 (§95a/rc258 centromere, #1407 / F1243): a NUCLEAR (Tier-2) chromosome carries an
#: INTERIOR ``CENTROMERE_CAP_MARKER`` (0x58) cap between its two arms — the global
#: orientation-chirality anchor (α-satellite repeat-array). It is one more self-describing
#: cap kind in the SAME walk (a byte > 3, distinct from every prior marker), so v2..v12
#: bodies read UNCHANGED (dual-read — the walker gains ONE branch): back-compat is
#: STRUCTURAL, never a converter. A plasmid (append) genome with NO 0x58 cap is byte-identical
#: to the v12 writer EXCEPT the ``format_version`` field. A v13 writer stamps 13.
#: v15 (§98/rc268 chromatin, #1422 / F1246-F1247): a chromosome MAY carry an INTERIOR
#: ``CHROMATIN_MARKER`` (0x48) cap — biology's epigenetic ACCESS gate above the coupled-turn
#: content (euchromatin/heterochromatin), set/cleared IN-PLACE by :func:`condense` /
#: :func:`decondense`. One more self-describing interior cap in the SAME walk (a byte > 3,
#: distinct from every prior marker), so v2..v14 bodies read UNCHANGED (dual-read — the walker
#: gains ONE branch): back-compat is STRUCTURAL. A chromatin-FREE genome saved by the v15 writer
#: is byte-identical to the v14 writer EXCEPT the ``format_version`` field. A v15 writer stamps 15.
GENOME_FORMAT_VERSION = 15

#: rc115 (#1245 ask (b)) — the empty-body chain seed H₀ = sha256(b"") (a derived
#: constant, not magic: THE well-known empty-string digest). The whole-body
#: ``body_sha256`` of a v4 manifest is the REGION CHAIN Hₙ = sha256(Hₙ₋₁ ‖ regionₙ)
#: folded over the per-chromosome region digests in body order — O(1)-maintainable
#: on append (extend from the prior head) yet re-verifiable from the file (re-hash
#: each region, re-fold). §44 stays intact: the chain is a pure function of the
#: body + leaf_dim, so a rebuild-by-scan reproduces it byte-identically. See the
#: manifest-format note in the CHANGELOG (rc115) for the (i)-lazy-vs-(ii)-chain
#: rationale (we chose (ii): (i)'s staleness flag is NOT body-derivable → breaks §44).
_EMPTY_SHA = _sha256_bytes(b"")

#: The data_schema_id the genome manifest's MPRRecord carries (resolves to the
#: genome-manifest data shape — format_version / leaf_dim / chromosomes / hashes).
GENOME_MANIFEST_SCHEMA_ID = "srmech://schema/genome_manifest/v1"

# §43: the data_schema_id of a single-chromosome .chr bundle (genome_export). A .chr
# is one self-contained MPR record (MPR v1) carrying the chromosome's region +
# coupling — re-importable self-verifying.
GENOME_CHR_SCHEMA_ID = "srmech://schema/genome_chromosome/v1"

_MANIFEST_NAME = "manifest.json"
_BODY_NAME = "turns.bin"


class GenomeBoundingError(Exception):
    """A genome read crossed its integrity bound — the bytes read do not hash to
    the value the manifest committed (whole-genome ``body_sha256``, a windowed
    chromosome region hash, or a telomere ``cap_sha256``).

    Bounding IS integrity here: every paged read re-hashes exactly the bytes it
    touched and checks them against the manifest before handing them back, so a
    flipped / truncated / re-ordered body byte surfaces as this error instead of
    a silently-corrupt strand. Raised by :func:`genome_load` and
    :func:`genome_window`.
    """


def _raise_native_genome(exc):
    """Translate a native ``srmech_genome_*`` failure into a
    :class:`GenomeBoundingError` — §49 / rc154: native is AUTHORITATIVE when
    present, so there is NO "fall back to pure-Python" (pure-Python is the
    complete ALTERNATIVE that runs only when there is no C at all). The cheap,
    caller-facing ``ValueError`` cases (label absent, coupling width) are
    validated in Python BEFORE the native call, so a native non-OK status here
    is an integrity / state failure."""
    raise GenomeBoundingError(
        f"native genome operation failed (SRMECH_ERR status {exc.status}) — "
        f"native is authoritative when present (no pure-Python fallback)"
    ) from exc


def _leaf_blocks(strand) -> List[bytes]:
    """Serialise a strand (list of Klein-4 vectors) to its fixed-width leaf
    blocks — one ``leaf_dim``-byte block per element (cap or coupled turn).

    Each element is a Klein-4 vector over ``{0,1,2,3}``; we store one byte per
    position via the HV's own ``tobytes`` (numpy-free; ``HV.from_sequence`` for a
    plain list/tuple). All blocks in one genome share ``leaf_dim`` so the body is
    a flat fixed-width concatenation with NO length prefixes.
    """
    blocks: List[bytes] = []
    for hv in strand:
        if isinstance(hv, _HV):
            blocks.append(hv.tobytes())
        else:
            blocks.append(_HV.from_sequence(hv).tobytes())
    return blocks


def _hv_from_block(block: bytes) -> _HV:
    """Reconstruct one strand element (an :class:`HV`) from a ``leaf_dim``-byte
    block — the numpy-free inverse of :meth:`HV.tobytes`.

    §44: a block is one of two kinds, told apart by its FIRST byte. A CHROM/GENE
    cap OR a §60 KERNEL HEADER (first byte a marker ``> 3``) is a packed
    ``sectors=256`` inline block (matching :func:`_pack_cap` / :func:`_pack_kernel_header`,
    so it reconstructs byte-AND-sectors identical); every other block is a Klein-4
    data turn (``sectors=QUAD``, bytes ``0..3``). Reading the first byte suffices
    because the marker bytes are out of the Klein-4 range — that IS the
    self-describing-strand property."""
    first = block[0] if block else -1
    sectors = 256 if first in (
        CHROM_CAP_MARKER, GENE_CAP_MARKER, REGULATORY_GENE_MARKER,
        BOOLEAN_GENE_MARKER, THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER,
        KERNEL_HEADER_MARKER,
        KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER,
        CENTROMERE_CAP_MARKER, DIPLOID_TELOMERE_MARKER,
        CHROMATIN_MARKER) else QUAD   # §95a/§95b/§98 caps
    return _HV.from_sequence(block, sectors=sectors)


def _block_is_cap(block: bytes) -> bool:
    """True if a ``leaf_dim``-byte block is a non-data MARKER block — a CHROM/GENE cap,
    a §60 v5 KERNEL HEADER, or a §89 KERNEL TELOMERE (first byte ``> 3``) — rather than
    a Klein-4 data turn. §44's scan predicate over raw bytes; a cap is stored VERBATIM
    (never bit-packed) and excluded from the data-turn count. §89: the v6 Klein-4
    header is a coupled DATA turn (first byte ``0..3``), NOT a cap — it bit-packs and
    counts like content; the ``0x6B`` kernel telomere is the cap that flags it. §127:
    the ``0x74`` active telomere is a chromosome-boundary cap (like CHROM/kernel), so it
    is stored VERBATIM and excluded from the data-turn count (its count is NOT a turn).
    §128: the ``0x67`` regulatory gene is an intra-chromosome gene delimiter cap (like the
    plain GENE cap), so it too is stored VERBATIM and excluded from the data-turn count (its
    mask is NOT a turn). §130: the ``0x62`` boolean gene is likewise an intra-chromosome gene
    delimiter cap (like the ``0x67`` regulatory gene), stored VERBATIM + excluded from the
    data-turn count (its gate_type + DNF are NOT a turn). §131: the ``0x77`` threshold gene is
    likewise an intra-chromosome gene delimiter cap, stored VERBATIM + excluded from the data-turn
    count (its gate_type + weights + threshold are NOT a turn). §132: the ``0x64`` graded gene is
    likewise an intra-chromosome gene delimiter cap, stored VERBATIM + excluded from the data-turn
    count (its gate_type + level-weights + denom are NOT a turn)."""
    return bool(block) and block[0] in (
        CHROM_CAP_MARKER, GENE_CAP_MARKER, REGULATORY_GENE_MARKER,
        BOOLEAN_GENE_MARKER, THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER,
        KERNEL_HEADER_MARKER,
        KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER,
        CENTROMERE_CAP_MARKER, DIPLOID_TELOMERE_MARKER,
        CHROMATIN_MARKER)   # §95a/§95b/§98 caps (a chromatin cap is stored VERBATIM, not a turn)


# ─────────────────────────────────────────────────────────────────────────────
# §55/rc114 (format v3) — the bit-packed on-disk block layer. In MEMORY a data
# turn stays one byte per Klein-4 symbol (the HV carrier, `_leaf_blocks` /
# `_hv_from_block` unchanged); ON DISK a v3 data turn is
# ``[PACKED_TURN_MARKER] + ceil(leaf_dim/4)`` bytes — 4 symbols per byte. Cap
# blocks keep their v2 ``leaf_dim``-byte inline layout (their label capacity is
# a format width, §44). The walker below reads v2 / v3 / MIXED bodies alike:
# a block's FIRST byte keys both its kind and its width, so back-compat is a
# property of the walk, not a converter.
# ─────────────────────────────────────────────────────────────────────────────

def _packed_payload_len(leaf_dim: int) -> int:
    """Payload bytes of one v3 packed data turn: ``ceil(leaf_dim / 4)`` (pure
    integer — 4 two-bit Klein-4 lanes per byte)."""
    return (int(leaf_dim) + 3) // 4


#: 4 Klein-4 symbols (the 4-byte group, each byte 0..3) → the packed byte
#: (first symbol in the HIGH lanes). The 256-entry table lets :func:`_pack_turn_block`
#: pack a group with ONE dict lookup instead of four per-symbol shifts — a measured
#: ~4x on the 1,024x256 chromosome (rc115 #1245(b); the packer is on the append hot
#: path). Byte-for-byte identical to the per-symbol form; a non-Klein-4 group is
#: simply absent from the table (KeyError → the ValueError below).
_PACK4 = {
    bytes((a, b, c, d)): (a << 6) | (b << 4) | (c << 2) | d
    for a in range(4) for b in range(4) for c in range(4) for d in range(4)
}


def _pack_turn_block(mem_block: bytes) -> bytes:
    """One in-memory byte-per-symbol data turn → its v3 on-disk packed block
    ``[PACKED_TURN_MARKER] + payload``. Symbol ``i`` → payload byte ``i // 4``,
    shift ``6 - 2*(i % 4)`` (first symbol in the HIGH lanes); the unused low
    lanes of a partial final byte are zero (canonical — the round-trip stays
    byte-exact both ways). Raises ``ValueError`` on a non-Klein-4 symbol.

    rc115 (#1245(b)): packs 4 symbols per :data:`_PACK4` lookup (the 2-bit lane
    IS the format; the table is the per-group codec). A partial final group is
    zero-padded to 4 before lookup — the unused low lanes stay zero (canonical)."""
    n = len(mem_block)
    pad = (-n) % 4
    grp = mem_block + bytes(pad) if pad else mem_block
    table = _PACK4
    try:
        return bytes([PACKED_TURN_MARKER]) + bytes(
            [table[grp[i:i + 4]] for i in range(0, len(grp), 4)])
    except KeyError:
        # A symbol > 3 slipped into a group — report its exact position (the slow
        # per-symbol scan runs only on the error path, never on the hot path).
        for i, sym in enumerate(mem_block):
            if sym > 3:
                raise ValueError(
                    f"genome v3 packing: data-turn symbol {sym} at position {i} "
                    f"is not a Klein-4 sector (0..3) — only Klein-4 turns bit-pack"
                ) from None
        raise


#: byte → its 4 unpacked Klein-4 symbols (high lanes first) — the v3 unpack table.
_UNPACK_LANES = tuple(
    bytes(((b >> 6) & 3, (b >> 4) & 3, (b >> 2) & 3, b & 3)) for b in range(256)
)


def _unpack_turn_payload(payload: bytes, leaf_dim: int) -> bytes:
    """A v3 packed payload → the in-memory byte-per-symbol data turn (exact
    inverse of :func:`_pack_turn_block`; the partial-final-byte tail truncates
    to ``leaf_dim``)."""
    return b"".join(_UNPACK_LANES[c] for c in payload)[:leaf_dim]


def _disk_block(mem_block: bytes, leaf_dim: int) -> bytes:
    """One in-memory ``leaf_dim``-byte block → its on-disk v3 form: caps pass
    through verbatim (their inline-label layout is the §44 format), data turns
    bit-pack (:func:`_pack_turn_block`)."""
    if len(mem_block) != leaf_dim:
        raise ValueError(
            f"genome: leaf block width {len(mem_block)} != leaf_dim {leaf_dim} "
            f"(every in-memory leaf is a fixed-width block)"
        )
    if _block_is_cap(mem_block):
        return bytes(mem_block)
    return _pack_turn_block(mem_block)


#: Every block-kind marker byte that keys a LEAF-WIDE (``leaf_dim``-byte) on-disk
#: block — §95a/§95b/§98 caps plus the §60 kernel header. ONE tuple shared by the
#: strict :func:`_walk_region_blocks` and the rc280 prefix walker
#: :func:`_walk_region_prefix_blocks`, so the two can never drift on which
#: markers are leaf-wide (a drift would mis-stride one walker against the other).
_LEAF_WIDE_BLOCK_MARKERS = (
    CHROM_CAP_MARKER, GENE_CAP_MARKER, REGULATORY_GENE_MARKER,
    BOOLEAN_GENE_MARKER, THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER,
    KERNEL_HEADER_MARKER,
    KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER,
    CENTROMERE_CAP_MARKER, DIPLOID_TELOMERE_MARKER,
    CHROMATIN_MARKER,
)


def _walk_region_blocks(region: bytes, leaf_dim: int, *, context: str = "genome"):
    """Walk a raw on-disk byte region block-by-block — the dual-format (v2 |
    v3 | mixed) walker. Yields ``(raw_block, decoded_block)`` where ``raw_block``
    is the on-disk bytes and ``decoded_block`` the in-memory byte-per-symbol
    form (caps decode to themselves). A block's FIRST byte keys its kind + width:
    ``CHROM_CAP_MARKER``/``GENE_CAP_MARKER``/``KERNEL_HEADER_MARKER`` (§60) → a
    ``leaf_dim``-byte inline block; ``PACKED_TURN_MARKER`` → a
    ``1 + ceil(leaf_dim/4)``-byte v3 packed turn; ``0..3`` → a legacy v2
    ``leaf_dim``-byte byte-per-symbol turn. Anything else (or a block running past
    the region end) is a :class:`GenomeBoundingError`."""
    plen = _packed_payload_len(leaf_dim)
    k, n = 0, len(region)
    while k < n:
        kind = region[k]
        if kind in _LEAF_WIDE_BLOCK_MARKERS or kind <= 3:
            end = k + leaf_dim
            if end > n:
                raise GenomeBoundingError(
                    f"{context}: truncated {leaf_dim}-byte block at offset {k} "
                    f"(region ends at {n})"
                )
            blk = region[k:end]
            yield blk, blk
        elif kind == PACKED_TURN_MARKER:
            end = k + 1 + plen
            if end > n:
                raise GenomeBoundingError(
                    f"{context}: truncated packed turn at offset {k} "
                    f"(needs {1 + plen} bytes, region ends at {n})"
                )
            yield region[k:end], _unpack_turn_payload(region[k + 1:end], leaf_dim)
        else:
            raise GenomeBoundingError(
                f"{context}: unrecognised block kind byte {kind} at offset {k} "
                f"(not a CHROM/GENE cap, a packed turn, or a Klein-4 symbol)"
            )
        k = end


def _split_into_chromosomes(strand, labels=None) -> List[Tuple[str, list]]:
    """Walk a flat genome strand and split it into ``[(label, [cap, *blocks]), …]``
    by SCANNING its inline CHROM caps (§44), preserving strand order.

    §44: a chromosome starts at each CHROM cap (inline marker
    :data:`CHROM_CAP_MARKER`); its label is read back inline (:func:`_unpack_cap`)
    — the strand self-describes, no label set is needed. Intervening GENE caps stay
    WITH their chromosome (gene boundaries are intra-chromosome). ``labels`` is
    accepted for back-compat: when given, it VALIDATES the scanned set matches (no
    orphan turns before the first cap; the scanned labels equal the requested set).
    """
    if not strand:
        raise ValueError("genome persistence: empty strand has no chromosomes")
    chroms: List[Tuple[str, list]] = []
    current_label: Optional[str] = None
    current_blocks: Optional[list] = None
    for hv in strand:
        if _cap_kind(hv) in (CHROM_CAP_MARKER, KERNEL_TELOMERE_MARKER,
                             ACTIVE_TELOMERE_MARKER, DIPLOID_TELOMERE_MARKER):
            if current_label is not None:
                chroms.append((current_label, current_blocks))
            _marker, current_label = _unpack_cap(hv)
            current_blocks = [hv]            # the cap leads the chromosome region
        else:
            if current_label is None:
                raise ValueError(
                    "genome persistence: strand has turns before its first CHROM "
                    "cap — not a well-formed §44 genome strand"
                )
            current_blocks.append(hv)        # a data turn OR an intra-chrom GENE cap
    if current_label is not None:
        chroms.append((current_label, current_blocks))
    seen = [lbl for lbl, _ in chroms]
    if labels is not None and sorted(seen) != sorted(set(labels)):
        raise ValueError(
            f"genome persistence: strand chromosomes {seen!r} do not match the "
            f"requested labels {list(labels)!r}"
        )
    return chroms


def _chain_step(acc_hex: str, region_hex: str) -> str:
    """One region-chain fold step Hₙ = sha256(Hₙ₋₁ ‖ regionₙ) — the whole-body
    integrity value's O(1)-maintainable update. Both operands are 64-char hex
    digests; the raw 32-byte values are concatenated (the spec's ``‖``) and
    re-hashed (rc115 #1245(b))."""
    return _sha256_bytes(bytes.fromhex(acc_hex) + bytes.fromhex(region_hex))


def _region_chain(region_hexes) -> str:
    """Fold the per-chromosome region digests (in body order) into the whole-body
    ``body_sha256`` chain head, seeded by :data:`_EMPTY_SHA` (H₀ = sha256(b"")).
    A genome with no regions hashes to the empty-body digest — the same value the
    v2/v3 whole-body ``sha256`` gives for an empty body."""
    acc = _EMPTY_SHA
    for rh in region_hexes:
        acc = _chain_step(acc, rh)
    return acc


def _build_manifest_data(leaf_dim, coupling_blocks, chrom_specs, body_bytes,
                         n_turns):
    """Assemble the manifest ``data`` block — §44's optional DERIVED catalog.

    ``chrom_specs`` is a list of ``(label, cap_sha256, leaf_count, byte_offset,
    byte_len, cap_kind)`` tuples (byte_offset/byte_len index into ``turns.bin``;
    ``leaf_count`` counts DATA turns only, excluding the chromosome's CHROM cap and
    any intra-chromosome GENE caps; ``cap_kind`` ∈ {"plasmid","nuclear","diploid"} is the
    §96 derived classification). ``coupling_blocks`` is the single
    ``leaf_dim``-byte block of coupling. ``n_turns`` is the strand BLOCK count
    (caps + data turns — §55/v3: blocks are variable-width on disk, so the count
    is scanned, no longer ``body_len / leaf_dim``).

    §44: this manifest is a derived ``.fai``-style cache — every field is
    rebuildable by scanning the self-describing body (the strand is the SSoT).
    The intra-chromosome gene structure lives INLINE in the body (GENE caps), NOT
    here, so there is no gene-index sidecar.

    rc115 (#1245(b) — format v4): one ``regions`` entry per chromosome — its byte
    span + ``sha256`` (the full-region digest, == the chromosome's ``.chr``/AMSC
    provenance unit). ``body_sha256`` is the region CHAIN (:func:`_region_chain`),
    NOT the whole-body digest, so an append maintains it in O(1) (extend the head)
    while it stays re-verifiable from the file and body-derivable (§44)."""
    return _build_manifest_data_from_hexes(
        leaf_dim, coupling_blocks, chrom_specs,
        _region_hexes_from_body(chrom_specs, body_bytes), n_turns)


def _region_hexes_from_body(chrom_specs, body_bytes):
    """Each region's full digest, sliced out of an in-RAM body — the whole-body way to
    get what :func:`_scan_body_stream` folds incrementally (rc282). Same hexes, same
    order; this one needs every byte resident, which is why the head-only catalog read
    uses the streaming peer instead."""
    return [_sha256_bytes(bytes(body_bytes[int(off):int(off) + int(ln)]))
            for (_label, _cap, _lc, off, ln, _ck) in chrom_specs]


def _build_manifest_data_from_hexes(leaf_dim, coupling_blocks, chrom_specs,
                                    region_hexes, n_turns):
    """Assemble the manifest ``data`` from ALREADY-COMPUTED per-region digests (rc282).

    The single assembly point for :func:`_build_manifest_data` (whole-body) and the
    streaming head-only catalog read, so the two cannot produce different catalogs for
    the same body — the property the ``body_sha256`` chain check relies on."""
    regions = [
        {"byte_offset": int(off), "byte_len": int(ln), "sha256": rh}
        for (_label, _cap, _lc, off, ln, _ck), rh in zip(chrom_specs, region_hexes)
    ]
    return {
        "format_version": GENOME_FORMAT_VERSION,
        "leaf_dim": int(leaf_dim),
        "n_turns": int(n_turns),
        "coupling": {
            "sha256": _sha256_bytes(coupling_blocks),
            "hex": coupling_blocks.hex(),
        },
        "body_sha256": _region_chain(region_hexes),
        "regions": regions,
        "chromosomes": [
            {
                "label": label,
                "cap_sha256": cap_sha256,
                "leaf_count": int(leaf_count),
                "byte_offset": int(byte_offset),
                "byte_len": int(byte_len),
                "cap_kind": cap_kind,
            }
            for (label, cap_sha256, leaf_count, byte_offset, byte_len, cap_kind)
            in chrom_specs
        ],
    }


def _build_head_data(leaf_dim, coupling_block, n_turns, n_chromosomes, body_sha256):
    """The v12 HEAD-ONLY manifest ``data`` — the O(1) head with NO per-chromosome
    ``chromosomes`` / ``regions`` arrays. Those are a plaintext table-of-contents
    (ADR-0003) and the O(N^2) append wall; they are DERIVED by scanning the
    self-describing body (:func:`_scan_body_to_chrom_specs`) whenever the full catalog
    is needed. ``body_sha256`` is the region-CHAIN head (:func:`_region_chain`), so an
    append folds one region onto it in O(1) and it stays body-derivable +
    re-verifiable. ``n_chromosomes`` is kept in the head so a threaded/cold append and
    a catalog read know the count without the array."""
    return {
        "format_version": GENOME_FORMAT_VERSION,
        "leaf_dim": int(leaf_dim),
        "n_turns": int(n_turns),
        "n_chromosomes": int(n_chromosomes),
        "coupling": {
            "sha256": _sha256_bytes(coupling_block),
            "hex": coupling_block.hex(),
        },
        "body_sha256": body_sha256,
    }


def _read_head(path, coupling=None) -> dict:
    """The cheap manifest HEAD (``leaf_dim`` / ``n_turns`` / ``n_chromosomes`` /
    ``body_sha256`` chain head / ``coupling``) — what an O(1) append needs, WITHOUT
    deriving the per-chromosome catalog. For a v12 head-only manifest this is an O(1)
    file read; for a legacy v≤11 full manifest it reads the whole file once (the
    one-time migration cost of the first v12 append) and back-fills ``n_chromosomes``
    from the array. A manifest-less genome is scanned once (O(n), one-time)."""
    path = Path(path)
    if (path / _MANIFEST_NAME).exists():
        head = dict(_read_manifest(path))
    else:
        if coupling is None:
            raise GenomeBoundingError(
                f"genome at {str(path)!r} has no {_MANIFEST_NAME} and no coupling= was "
                f"given: pass the genome's coupling= so the head can be scanned from "
                f"{_BODY_NAME}"
            )
        head = dict(_rebuild_manifest_from_body(
            (path / _BODY_NAME).read_bytes(), len(list(coupling)), coupling))
    head.setdefault("n_chromosomes", len(head.get("chromosomes", [])))
    return head


#: The attestation fields a caller MAY override via ``genome_save(attestation=…)`` /
#: ``genome_from_graph(attestation=…)`` — the SOURCE-identity fields (WHERE the encoded
#: corpus came from). The remaining four attestation fields — ``parser_version`` /
#: ``parser_rule_hash`` / ``collector_descriptor_path`` / ``collector_descriptor_hash`` —
#: identify the ENCODER (srmech itself) and stay srmech-owned, so a caller can attest a
#: real corpus source WITHOUT being able to misreport which srmech version / rule wrote
#: the bytes. ``response_sha256`` is overridable (an MPR's response_sha256 = the hash of
#: the upstream RESPONSE, i.e. the corpus dump); genome body integrity is anchored on the
#: separate ``data["body_sha256"]`` field, NOT this one, so an override cannot weaken it.
_ATTESTATION_SOURCE_FIELDS = frozenset((
    "source_doi", "source_url", "license", "retrieved_at", "response_sha256",
))


def _merge_source_attestation(defaults, override):
    """OVERRIDE-ONLY merge of a caller SOURCE-attestation over the srmech defaults.

    A provided field REPLACES its default; an ABSENT field keeps its default (so a
    partial dict never blanks a field — a caller passing only ``source_url`` keeps the
    srmech ``license`` etc. rather than nulling them). Only the five
    :data:`_ATTESTATION_SOURCE_FIELDS` may be set: any other key — a typo like
    ``source_uri``, or an attempt to overwrite an ENCODER-identity field — is REJECTED
    with a clear error, so the very misattribution this parameter exists to prevent can
    never be introduced silently. The merged block is validated as a whole MPR by the
    caller (:func:`_manifest_record`), so an empty / non-string value is rejected there."""
    if not isinstance(override, dict):
        raise TypeError(
            "genome attestation override must be a dict of MPR source fields, "
            f"got {type(override).__name__}"
        )
    merged = dict(defaults)
    for key, value in override.items():
        if key not in _ATTESTATION_SOURCE_FIELDS:
            raise ValueError(
                f"genome attestation: {key!r} is not an overridable source field "
                f"(allowed: {sorted(_ATTESTATION_SOURCE_FIELDS)}; the four encoder-"
                f"identity fields — parser_version / parser_rule_hash / "
                f"collector_descriptor_path / collector_descriptor_hash — are srmech-owned)"
            )
        merged[key] = value
    return merged


def _manifest_record(data, *, attestation=None) -> _MPRRecord:
    """Wrap a genome manifest ``data`` block in an MPRRecord (MPR v1) — the
    on-disk catalog format. ``attestation.response_sha256`` IS the body hash
    (``body_sha256``) by default; ``parser_version`` is the srmech version string. The
    record satisfies :func:`srmech.amsc.format.validate_mpr_record`.

    ``attestation`` (optional): a caller MPR SOURCE-attestation whose provided fields
    OVERRIDE the srmech defaults (override-only, per :func:`_merge_source_attestation`) —
    for an attested corpus genome (e.g. a simplewiki dump under CC-BY-SA-4.0) whose true
    source is NOT ``srmech.net/genome/persistence``. Only the five
    :data:`_ATTESTATION_SOURCE_FIELDS` may be overridden; a bad override (non-dict,
    unknown key, or a value that makes the merged block an invalid MPR) RAISES — a
    caller-supplied attestation that would produce an invalid MPR is never written."""
    body_sha = data["body_sha256"]
    parser_version = f"srmech {_SRMECH_VERSION}"
    rule_hash = _sha256_bytes(
        f"genome_persistence/v{GENOME_FORMAT_VERSION}".encode("utf-8")
    )
    descriptor_hash = _sha256_bytes(GENOME_MANIFEST_SCHEMA_ID.encode("utf-8"))
    attest = {
        "source_doi": "10.0/srmech.genome.persistence",
        "source_url": "https://srmech.net/genome/persistence",
        "license": "CC0",
        "retrieved_at": "1970-01-01T00:00:00Z",
        "response_sha256": body_sha,
        "parser_version": parser_version,
        "parser_rule_hash": rule_hash,
        "collector_descriptor_path": "srmech/amsc/genome.py",
        "collector_descriptor_hash": descriptor_hash,
    }
    if attestation is not None:
        attest = _merge_source_attestation(attest, attestation)
    record = _MPRRecord(
        mpr_version="1.0",
        data=data,
        data_schema_id=GENOME_MANIFEST_SCHEMA_ID,
        attestation=attest,
        rendering={
            "human_readable_name": "srmech genome (on-disk chromosome set)",
            "cite_as": "srmech genome persistence (UPSTREAM §41)",
            "purpose": (
                "A telomere-partitioned genome persisted as a fixed-width body "
                "(turns.bin) + an MPR-attested manifest catalog."
            ),
        },
    )
    _validate_mpr_record(record)
    return record


def _read_manifest(path) -> dict:
    """Read + parse ``path/manifest.json`` into its ``data`` block (the catalog).

    Reads ONLY the manifest file (never opens ``turns.bin``) — this is the
    catalog read. Round-trips through :class:`MPRRecord` so the on-disk shape is
    validated as a real MPR record before its ``data`` is returned."""
    manifest_path = Path(path) / _MANIFEST_NAME
    text = manifest_path.read_text(encoding="utf-8")
    payload = json.loads(text)
    record = _MPRRecord(
        mpr_version=str(payload.get("mpr_version", "")),
        data=dict(payload.get("data", {})),
        data_schema_id=str(payload.get("data_schema_id", "")),
        attestation=dict(payload.get("attestation", {})),
        rendering=dict(payload.get("rendering", {})),
    )
    _validate_mpr_record(record)
    return record.data


def _write_manifest(path, record) -> None:
    """Serialise an MPRRecord to ``path/manifest.json`` (JSON/MPR catalog).

    Uses the MPRRecord's own canonical ``to_json_line`` payload + ``json.dumps``
    with LF newline so the catalog is byte-stable across platforms (the same
    discipline ``format.write_ndjson`` uses)."""
    manifest_path = Path(path) / _MANIFEST_NAME
    payload = json.loads(record.to_json_line())   # the MPRRecord's own to-dict path
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    manifest_path.write_text(text + "\n", encoding="utf-8", newline="\n")


def _coupling_block_bytes(coupling) -> bytes:
    """The ``leaf_dim``-byte block for ``coupling`` (the width the body lacks inline) —
    the native ``srmech_genome_*`` calls take it as raw bytes."""
    return bytes(_leaf_blocks([coupling])[0])


def _coupling_bytes_or_empty(coupling) -> bytes:
    """``coupling`` as bytes, or ``b""`` when it is ``None`` — for the native genome
    reads (``load`` / ``window`` / ``catalog`` / ``explode`` / ``pack`` / ``import``)
    where ``coupling`` is only consulted as the §44 rebuild width (a present manifest
    needs none, so an empty ``coupling`` maps to the C ``NULL,0``)."""
    return b"" if coupling is None else _coupling_block_bytes(coupling)


def genome_save(strand, path, coupling, labels=None, *, attestation=None) -> dict:
    """Persist a genome ``strand`` to ``path/`` (a DIRECTORY) — UPSTREAM §41 / §44.

    ``attestation`` (optional keyword) — a caller MPR SOURCE-attestation whose provided
    fields OVERRIDE the srmech default written into ``manifest.json`` (override-only over
    the five source-identity fields; see :func:`_merge_source_attestation`). With no
    ``attestation`` the manifest carries the srmech default and the save is byte-identical
    to before. Because the genome directory is the SSoT (no sidecar files, §41/F1300),
    the manifest is the ONLY legitimate home for an attested corpus genome's true source,
    so this is a genome-NATIVE provenance override, not a sidecar. A malformed override
    (non-dict / unknown key / invalid-MPR value) RAISES before any bytes reach disk.

    Splits the flat genome ``strand`` into its chromosomes by SCANNING its inline
    CHROM caps (§44 — the strand self-describes; labels are recovered inline),
    writes the self-describing fixed-width body to ``path/turns.bin`` (every strand
    element a ``leaf_dim``-byte block — a CHROM/GENE cap or a coupled data turn),
    and writes the DERIVED catalog to ``path/manifest.json``. ``coupling`` (the held
    invariant) is content-addressed into the manifest (its hash + hex) so a load can
    re-anchor without re-deriving it. Returns the manifest ``data`` dict.

    §44: the strand (``turns.bin``) is the SSoT — the manifest is an optional
    ``.fai``-style cache, every field rebuildable by scanning the body. Multi-gene
    chromosomes (from ``genome(chromosomes=…)``) carry their gene boundaries INLINE
    as GENE caps in the body; there is NO gene-index sidecar (page the genes back by
    SCANNING with :func:`genome_genes`). ``labels`` is optional and back-compat: when
    given it VALIDATES the scanned chromosome set matches.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    leaf_dim = len(list(coupling))
    chroms = _split_into_chromosomes(strand, labels)

    body = bytearray()
    chrom_specs: List[Tuple[str, str, int, int, int, str]] = []
    n_turns = 0
    for label, blocks in chroms:
        byte_offset = len(body)
        leaf_blocks = _leaf_blocks(blocks)
        for blk in leaf_blocks:
            # §55/v3: caps stay leaf_dim-wide verbatim; data turns bit-pack
            # (4 Klein-4 symbols per byte) — _disk_block validates the width.
            body.extend(_disk_block(blk, leaf_dim))
        n_turns += len(leaf_blocks)
        byte_len = len(body) - byte_offset
        cap_block = leaf_blocks[0]                # the CHROM cap leads the region
        cap_sha256 = _sha256_bytes(cap_block)
        # §44: leaf_count = DATA turns only — exclude the CHROM cap AND any inline
        # GENE caps (the gene structure lives inline, not as a turn count).
        leaf_count = sum(1 for blk in leaf_blocks if not _block_is_cap(blk))
        # §96: cap_kind — provisional on the opener (0x44 diploid else plasmid),
        # nuclear when an interior §95a centromere is present (byte-identical to the
        # on-disk _scan_body_to_chrom_specs classification). rc271 (F1251): the
        # field's own names — plasmid (was "stick") / nuclear (was "minted").
        cap_kind = ("diploid"
                    if _cap_kind(leaf_blocks[0]) == DIPLOID_TELOMERE_MARKER
                    else "plasmid")
        if any(_cap_kind(blk) == CENTROMERE_CAP_MARKER for blk in leaf_blocks):
            cap_kind = "nuclear"
        chrom_specs.append(
            (label, cap_sha256, leaf_count, byte_offset, byte_len, cap_kind)
        )

    body_bytes = bytes(body)
    coupling_block = _leaf_blocks([coupling])[0]
    # The full DERIVED catalog — the RETURN value (callers get chromosomes/regions);
    # on disk only the v12 HEAD is written (the arrays are re-derivable, ADR-0003).
    data = _build_manifest_data(leaf_dim, coupling_block, chrom_specs, body_bytes,
                                n_turns)
    head = _build_head_data(leaf_dim, coupling_block, n_turns, len(chrom_specs),
                            data["body_sha256"])

    # §49/rc154: native C save writes turns.bin + the head-only manifest byte-
    # identically for a genome of ANY size (the C carves its scratch from the caller
    # arena — no compiled-in cap). Native is authoritative when present; the pure-
    # Python path below is the complete alternative ONLY when there is no C.
    # §41 provenance: a caller ``attestation=`` OVERRIDE (an attested corpus genome's
    # true source) is applied by the PURE manifest write — the native ``srmech_genome_save``
    # writes the srmech DEFAULT MPR and takes no override, so the override path writes the
    # (already-materialised) ``body_bytes`` + the overridden manifest from Python, producing
    # an on-disk manifest BYTE-IDENTICAL to what a byte-identical C save would emit for the
    # same override (the two projections do NOT diverge; the capability is the invariant,
    # ADR-0009). With no override the native fast path is unchanged (byte-identical to before).
    if attestation is None and _native.has_native_genome():
        try:
            _native.genome_save_c(str(path), body_bytes, leaf_dim, bytes(coupling_block))
            return data
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)

    # Build + VALIDATE the record BEFORE any bytes hit disk, so a malformed caller
    # attestation is rejected (no half-written genome). attestation=None reproduces the
    # default record exactly.
    record = _manifest_record(head, attestation=attestation)
    (path / _BODY_NAME).write_bytes(body_bytes)
    _write_manifest(path, record)                     # v12: HEAD-ONLY on disk
    return data


def _rebuild_manifest_from_body(body_bytes, leaf_dim, coupling):
    """Reconstruct the manifest ``data`` block by SCANNING ``turns.bin`` alone — §44.

    The strand is the SSoT: every manifest field (the per-chromosome ``label`` /
    ``byte_offset`` / ``byte_len`` / ``cap_sha256`` / ``leaf_count``, the
    ``body_sha256`` and ``n_turns``) is derivable by walking the self-describing
    fixed-width body. ``leaf_dim`` — the block width — is the one thing the body does
    NOT carry inline; it comes from ``coupling`` (``len(coupling)``), the genome's
    identity key. The returned dict is byte-for-byte what :func:`genome_save` wrote
    (same scan + spec accumulation), so a regenerated manifest is identical — that is
    what makes ``manifest.json`` a true optional ``.fai``-style cache (drop it, ship
    ``turns.bin`` alone, rebuild on load)."""
    leaf_dim = int(leaf_dim)
    if leaf_dim <= 0:
        raise GenomeBoundingError(
            f"genome rebuild-by-scan: leaf_dim {leaf_dim} is not a positive block "
            f"width (is coupling's width right?)"
        )
    if not body_bytes:
        raise ValueError("genome persistence: empty strand has no chromosomes")
    chrom_specs, n_turns = _scan_body_to_chrom_specs(bytes(body_bytes), leaf_dim)
    one = coupling if isinstance(coupling, _HV) else _HV.from_sequence(coupling)
    coupling_block = _leaf_blocks([one])[0]
    return _build_manifest_data(leaf_dim, coupling_block, chrom_specs,
                                bytes(body_bytes), n_turns)


def _scan_body_to_chrom_specs(body_bytes, leaf_dim):
    """Walk ``turns.bin`` → ``(chrom_specs, n_turns)`` — the §44 body-scan shared by
    :func:`_rebuild_manifest_from_body` and the v12 head-only :func:`_catalog_data`
    rebuild. ``chrom_specs`` is the ``(label, cap_sha256, leaf_count, byte_offset,
    byte_len)`` list; ``n_turns`` the BLOCK count.

    §55/v3: walk the RAW on-disk bytes (v2 | v3 | mixed) — offsets, hashes and counts
    come from the stored blocks VERBATIM (a legacy byte-per-symbol turn is never
    re-encoded, so the derived catalog matches the body as written).

    §96: each spec's 6th field is the derived ``cap_kind`` ∈ {"plasmid","nuclear",
    "diploid"} — PROVISIONAL on the opening cap (a §95b diploid telomere ``0x44`` →
    "diploid", else "plasmid"), OVERWRITTEN to "nuclear" by an interior §95a centromere
    (``0x58``). nuclear > diploid > plasmid (a diploid PAIR carries a centromere, so it
    reads "nuclear" — the R-RBS-LM reference's centromere-first classify). rc271
    (F1251): the field's own names — plasmid (was "stick") / nuclear (was "minted").
    This rides the EXISTING scan (no extra pass, byte-identical to the C genome_scan_chroms)."""
    state = _ScanState()
    for raw, decoded in _walk_region_blocks(
            bytes(body_bytes), leaf_dim, context="genome rebuild-by-scan"):
        state.fold(raw, decoded)
    return state.finish()


#: The block markers that OPEN a chromosome region — the §44 CHROM cap and the §60 /
#: §127 / §95b telomere kinds. The ONE predicate both the in-memory
#: (:func:`_scan_body_to_chrom_specs`) and the STREAMING (:func:`_scan_body_stream`)
#: catalog derivations use to find a region boundary, so the two cannot drift apart.
_REGION_OPEN_MARKERS = (CHROM_CAP_MARKER, KERNEL_TELOMERE_MARKER,
                        ACTIVE_TELOMERE_MARKER, DIPLOID_TELOMERE_MARKER)


class _ScanState:
    """The §44 body-scan STATE MACHINE, fed ONE block at a time (rc282).

    Extracted verbatim from :func:`_scan_body_to_chrom_specs` so the whole-body scan
    and the STREAMING scan share one implementation rather than two that must be kept
    in step — a derived catalog is identical whichever drives it, which is the
    property the ``body_sha256`` chain check depends on."""

    def __init__(self):
        self.chrom_specs: List[Tuple[str, str, int, int, int, str]] = []
        # cur = [label, cap_sha256, leaf_count, offset, length, cap_kind]
        self.cur: Optional[list] = None
        self.n_turns = 0
        self.offset = 0

    def fold(self, raw, decoded):
        """Fold ONE on-disk block. Returns True iff it OPENED a new region (the signal
        a streaming caller uses to close the previous region's digest)."""
        opened = False
        self.n_turns += 1
        if decoded[0] in _REGION_OPEN_MARKERS:
            if self.cur is not None:
                self.chrom_specs.append(tuple(self.cur))
            # the label is bytes [1:] up to the first NUL — UNIFORM across all telomere
            # kinds (the §127 active telomere's count sits AFTER that NUL).
            label = decoded[1:].split(b"\x00", 1)[0].decode("utf-8")
            cap_kind = "diploid" if decoded[0] == DIPLOID_TELOMERE_MARKER else "plasmid"
            self.cur = [label, _sha256_bytes(raw), 0, self.offset, 0, cap_kind]
            opened = True
        elif self.cur is None:
            raise ValueError(
                "genome persistence: strand has turns before its first CHROM "
                "cap — not a well-formed §44 genome strand"
            )
        elif decoded[0] == CENTROMERE_CAP_MARKER:
            self.cur[5] = "nuclear"           # §96: an interior centromere mints (wins)
        elif (decoded[0] != GENE_CAP_MARKER
              and decoded[0] != REGULATORY_GENE_MARKER
              and decoded[0] != BOOLEAN_GENE_MARKER
              and decoded[0] != THRESHOLD_GENE_MARKER
              and decoded[0] != GRADED_GENE_MARKER
              and decoded[0] != KERNEL_HEADER_MARKER
              and decoded[0] != CHROMATIN_MARKER
              and decoded[0] != CENTROMERE_CAP_MARKER):
            self.cur[2] += 1                  # a data turn (packed or legacy); a GENE
                                              # cap (§44 plain / §128 regulatory / §130
                                              # boolean / §131 threshold / §132 graded),
                                              # §60 v5 header, or §95a interior centromere
                                              # is not a turn
                                              # (the §89 v6 Klein-4 header IS a coupled turn)
        self.cur[4] += len(raw)
        self.offset += len(raw)
        return opened

    def finish(self):
        """Close the last open region and return ``(chrom_specs, n_turns)``."""
        if self.cur is not None:
            self.chrom_specs.append(tuple(self.cur))
            self.cur = None
        return self.chrom_specs, self.n_turns


def _stream_body_blocks(f, leaf_dim, *, context="genome"):
    """Walk a genome body block-by-block from an ALREADY-OPEN handle (rc282) — the
    streaming mirror of :func:`_walk_region_blocks`.

    Yields the SAME ``(raw, decoded)`` pairs, in the same order, for the same bytes;
    the difference is that only ONE block is ever resident, so a caller can derive a
    catalog without the whole body in RAM. ``f`` is a buffered binary handle, so the
    per-block reads coalesce into ordinary sequential I/O — no extra syscalls."""
    plen = _packed_payload_len(leaf_dim)
    offset = 0
    while True:
        first = f.read(1)
        if not first:
            return
        kind = first[0]
        if kind in _LEAF_WIDE_BLOCK_MARKERS or kind <= 3:
            rest = f.read(leaf_dim - 1)
            if len(rest) != leaf_dim - 1:
                raise GenomeBoundingError(
                    f"{context}: truncated {leaf_dim}-byte block at offset {offset} "
                    f"(got {1 + len(rest)} bytes)"
                )
            blk = first + rest
            yield blk, blk
            offset += leaf_dim
        elif kind == PACKED_TURN_MARKER:
            payload = f.read(plen)
            if len(payload) != plen:
                raise GenomeBoundingError(
                    f"{context}: truncated packed turn at offset {offset} "
                    f"(needs {1 + plen} bytes, got {1 + len(payload)})"
                )
            yield first + payload, _unpack_turn_payload(payload, leaf_dim)
            offset += 1 + plen
        else:
            raise GenomeBoundingError(
                f"{context}: unrecognised block kind byte {kind} at offset {offset} "
                f"(not a CHROM/GENE cap, a packed turn, or a Klein-4 symbol)"
            )


def _scan_body_stream(f, leaf_dim, *, context="genome rebuild-by-scan"):
    """Derive ``(chrom_specs, n_turns, region_hexes)`` by STREAMING the body (rc282).

    The catalog-derivation counterpart of :func:`_scan_body_to_chrom_specs` +
    :func:`_region_hexes_from_body`, computed in ONE forward pass with **RAM bounded
    by the largest single REGION** rather than by the whole file. That is the same
    bound :func:`_read_region` / :func:`genome_window` already advertise, so it adds
    no new assumption; it just stops the head-only catalog read from being the one
    place that slurps every byte of ``turns.bin`` into memory at once.

    A region's digest is folded the moment the NEXT region opens, so at most one
    region's bytes are held. ``_sha256_bytes`` has no streaming API (see
    :func:`genome_load`), which is why the bound is one region and not one block."""
    state = _ScanState()
    region = bytearray()
    region_hexes: List[str] = []
    for raw, decoded in _stream_body_blocks(f, leaf_dim, context=context):
        if state.fold(raw, decoded) and region:
            region_hexes.append(_sha256_bytes(bytes(region)))
            region.clear()
        region.extend(raw)
    if region:
        region_hexes.append(_sha256_bytes(bytes(region)))
    chrom_specs, n_turns = state.finish()
    return chrom_specs, n_turns, region_hexes


def _catalog_data(path, coupling=None) -> dict:
    """The manifest ``data`` for a genome at ``path`` — §44's "manifest is an
    optional ``.fai`` cache; the strand is the SSoT".

    Returns the FULL catalog (with the per-chromosome ``chromosomes`` / ``regions``
    arrays) regardless of on-disk format:

    - **v≤11 full manifest** — read the arrays verbatim (back-compat; never opens
      ``turns.bin``).
    - **v12 HEAD-ONLY manifest** — read the O(1) head, then DERIVE the arrays by
      STREAMING the self-describing body (:func:`_scan_body_stream`), using the
      head's ``leaf_dim`` + ``coupling`` (no ``coupling=`` needed). This is where the
      ADR-0003 "catalog is derived, never a stored plaintext TOC" contract is paid.
      rc282: the derivation is a single forward pass with RAM bounded by the largest
      REGION. It previously did ``turns.bin.read_bytes()`` — the ENTIRE body resident
      at once — and since every store written today is head-only, that was the branch
      every catalog read took.
    - **no manifest** — REBUILD from the body (needs ``coupling=`` for the leaf width).

    So a genome can be shipped as ``turns.bin`` alone (tar one file) + its ``coupling``;
    the manifest is an optional ``.fai`` head, never the SSoT."""
    path = Path(path)
    if (path / _MANIFEST_NAME).exists():
        head = _read_manifest(path)
        if "chromosomes" in head:
            return head                        # v2..v11 full manifest — verbatim (back-compat)
        # v12 head-only (no chromosomes array): derive the arrays from the body. leaf_dim +
        # coupling come from the head, so this needs no coupling= argument.
        leaf_dim = int(head["leaf_dim"])
        coupling_block = bytes.fromhex(head["coupling"]["hex"])
        # rc282: ONE streamed forward pass — RAM bounded by the largest REGION, not by
        # the whole file. Byte-identical catalog to the old whole-body slurp (both drive
        # the same _ScanState and the same _build_manifest_data_from_hexes assembly).
        with _open_body_ro(path / _BODY_NAME) as f:
            chrom_specs, n_turns, region_hexes = _scan_body_stream(f, leaf_dim)
        data = _build_manifest_data_from_hexes(leaf_dim, coupling_block, chrom_specs,
                                               region_hexes, n_turns)
        # INTEGRITY: the head stores the ``body_sha256`` region-CHAIN head (the Merkle
        # root of the body). A body corruption re-derives a DIFFERENT chain → mismatch
        # with the committed head → raise (whole-body granularity; the per-region
        # digests are derived, not stored — ADR-0003).
        if data["body_sha256"] != head.get("body_sha256"):
            raise GenomeBoundingError(
                f"genome at {str(path)!r}: {_BODY_NAME} body_sha256 chain "
                f"{data['body_sha256']} != the manifest head's committed "
                f"{head.get('body_sha256')} — the body was modified out of band"
            )
        return data
    if coupling is None:
        raise GenomeBoundingError(
            f"genome at {str(path)!r} has no {_MANIFEST_NAME} and no coupling= was "
            f"given: §44 makes the manifest an optional .fai cache, but rebuilding it "
            f"by scanning {_BODY_NAME} needs the leaf width (= len(coupling)) — pass "
            f"the genome's coupling="
        )
    body_bytes = (path / _BODY_NAME).read_bytes()
    return _rebuild_manifest_from_body(body_bytes, len(list(coupling)), coupling)


# ── rc271 (F1251) VALUE-ALIAS presentation layer ─────────────────────────────
# PART A adopted the field's own names (plasmid / nuclear) as the CANONICAL §96
# cap_kind / census type values. This layer lets a user whose domain prefers the
# old srmech names (stick / minted) — or any other vocabulary — opt in with a
# canonical→preferred mapping, applied as a PURE PYTHON PRESENTATION layer OVER the
# canonical census/registry/catalog output. The C layer + on-disk format stay
# canonical only (plasmid/nuclear); the alias is a uniform post-transform on BOTH
# the native and the pure result, so native==pure holds at the canonical level and
# the alias never touches storage/format/ABI. Analogous to rc261's dsl/_alias.py
# (which aliases FUNCTION names → callables); this aliases the TYPE-VALUE strings.

#: The canonical §96 cap_kind / census type values (rc271 field vocabulary, F1251).
_CANONICAL_TYPE_VALUES = ("plasmid", "nuclear", "diploid")

#: The ACTIVE canonical→preferred type-value mapping. Session-global presentation
#: state; the default (empty) emits the canonical plasmid/nuclear/diploid names.
_TYPE_ALIASES: Dict[str, str] = {}


def _normalise_type_aliases(mapping) -> Dict[str, str]:
    """Validate + copy a canonical→preferred type-value mapping. Keys MUST be
    canonical §96 values ({plasmid, nuclear, diploid}); values MUST be non-empty
    strings (the user's preferred display name). Returns a fresh dict."""
    if not isinstance(mapping, dict):
        raise TypeError(
            "type aliases must be a dict mapping canonical_type -> preferred_name; "
            "got " + type(mapping).__name__)
    out: Dict[str, str] = {}
    for canon, preferred in mapping.items():
        if canon not in _CANONICAL_TYPE_VALUES:
            raise ValueError(
                "type-alias key {!r} is not a canonical cap_kind — must be one of "
                "{}".format(canon, _CANONICAL_TYPE_VALUES))
        if not isinstance(preferred, str) or not preferred:
            raise ValueError(
                "type-alias value for {!r} must be a non-empty string; got "
                "{!r}".format(canon, preferred))
        out[canon] = preferred
    return out


def set_type_aliases(mapping) -> Dict[str, str]:
    """Install a canonical→preferred cap_kind / census TYPE-VALUE alias (rc271 / F1251).

    ``mapping`` maps a canonical §96 type value ({plasmid, nuclear, diploid}) to the
    display string you want in its place — e.g.
    ``{"nuclear": "minted", "plasmid": "stick"}`` restores the pre-rc271 srmech names.
    The alias is a PURE PYTHON PRESENTATION layer applied OVER the canonical output of
    :func:`genome_census` / :func:`genome_registry` / :func:`genome_catalog` (the
    per-chromosome ``cap_kind`` / ``type`` field VALUES and the census ``types`` dict
    KEYS); the C layer + on-disk format stay canonical (plasmid/nuclear) — no storage /
    format / ABI change, and native==pure still holds at the canonical level (the alias
    is the SAME post-transform on both paths). REPLACES any prior mapping (not merged).
    Returns the installed mapping. Clear with :func:`clear_type_aliases`; load from a
    TOML file with :func:`load_type_aliases_toml`. Session-global; default is canonical."""
    global _TYPE_ALIASES
    _TYPE_ALIASES = _normalise_type_aliases(mapping)
    return dict(_TYPE_ALIASES)


def clear_type_aliases() -> None:
    """Remove any active type-value alias — :func:`genome_census` /
    :func:`genome_registry` / :func:`genome_catalog` emit the canonical
    plasmid / nuclear / diploid names again (rc271 / F1251)."""
    global _TYPE_ALIASES
    _TYPE_ALIASES = {}


def load_type_aliases_toml(path) -> Dict[str, str]:
    """Read a ``[genome.type_aliases]`` TOML table, INSTALL it, and return the mapping
    (rc271 / F1251) — the on-disk counterpart of :func:`set_type_aliases` (one load
    call opts in). The section maps each canonical value to its preferred display name::

        [genome.type_aliases]
        nuclear = "minted"
        plasmid = "stick"

    A top-level ``[type_aliases]`` table is also accepted. Parsing routes through the C
    ``srmech_toml`` parser when native (the DSL's :func:`_toml_loads_native`), falling
    back to the stdlib ``tomllib`` / ``tomli`` (same dict, same decode error) — the
    rc261 :func:`load_aliases_toml` shape. numpy-free; no external libs."""
    from srmech.dsl._toml_chain import _toml, _toml_loads_native
    spec = Path(path).read_text(encoding="utf-8")
    data = _toml_loads_native(spec)
    if data is None:
        data = _toml.loads(spec)
    section: Dict = {}
    if isinstance(data, dict):
        genome_tbl = data.get("genome")
        if isinstance(genome_tbl, dict) and isinstance(
                genome_tbl.get("type_aliases"), dict):
            section = genome_tbl["type_aliases"]
        elif isinstance(data.get("type_aliases"), dict):
            section = data["type_aliases"]
    return set_type_aliases(section)


def _alias_type_value(v):
    """Map one canonical cap_kind value to the active user alias (identity if no
    alias is active or the value is unmapped)."""
    return _TYPE_ALIASES.get(v, v) if _TYPE_ALIASES else v


def _apply_type_aliases_to_catalog(cat: dict) -> dict:
    """Rewrite the per-chromosome ``cap_kind`` VALUES of a CANONICAL catalog dict to
    the active alias, IN PLACE (identity when no alias). The catalog dict is freshly
    built per call (native ``json.loads`` or the pure derivation), so in-place rewrite
    is safe — it never mutates shared/cached state."""
    if not _TYPE_ALIASES:
        return cat
    for e in cat.get("chromosomes", []):
        if "cap_kind" in e:
            e["cap_kind"] = _alias_type_value(e["cap_kind"])
    return cat


def _apply_type_aliases_to_census(cen: dict) -> dict:
    """Rewrite a CANONICAL census dict to the active alias, IN PLACE: the ``types``
    dict KEYS and each chromosome's ``type`` VALUE (identity when no alias)."""
    if not _TYPE_ALIASES:
        return cen
    types = cen.get("types")
    if isinstance(types, dict):
        cen["types"] = {_alias_type_value(k): v for k, v in types.items()}
    for c in cen.get("chromosomes", []):
        if "type" in c:
            c["type"] = _alias_type_value(c["type"])
    return cen


def _apply_type_aliases_to_registry(reg: dict) -> dict:
    """Rewrite every per-genome census in a CANONICAL registry dict to the active
    alias, IN PLACE (identity when no alias)."""
    if not _TYPE_ALIASES:
        return reg
    for cen in reg.get("genomes", []):
        _apply_type_aliases_to_census(cen)
    return reg


def _canonical_catalog(path, coupling=None) -> dict:
    """The native-or-pure catalog ``data`` at the CANONICAL cap_kind level (NO type
    alias) — the internal peer of :func:`genome_catalog`. The public ``genome_catalog``
    wraps this with the type-alias presentation; the census / registry roll-ups consume
    the CANONICAL data so they count by the canonical key, and the alias is applied ONCE
    at the public boundary (never double-applied through a re-aliased catalog)."""
    # §49: native C catalog (parse manifest.json, or §44 rebuild-by-scan) → the same
    # canonical JSON the pure path produces; native is authoritative when present (no fallback).
    if _native.has_native_genome():
        try:
            text = _native.genome_catalog_c(
                str(Path(path)), _coupling_bytes_or_empty(coupling))
            return json.loads(text)["data"]
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    return _catalog_data(path, coupling)


def genome_catalog(path, *, coupling=None) -> dict:
    """Read the catalog of a genome at ``path`` — UPSTREAM §41 / §44.

    Returns the manifest ``data`` dict (``leaf_dim`` / ``n_turns`` /
    ``body_sha256`` / per-chromosome ``cap_sha256`` / ``leaf_count`` /
    ``byte_offset`` / ``byte_len`` / ``cap_kind`` / ``coupling`` hash+hex).

    **What this costs (rc282 — the previous wording here was false).** This docstring
    used to say the catalog read "NEVER opens ``turns.bin``" when a manifest is
    present. That is true ONLY of a v≤11 FULL manifest, which stored the chromosome
    array verbatim. Since v12 the on-disk manifest is HEAD-ONLY — the per-chromosome
    array is a plaintext table-of-contents and ADR-0003 forbids storing one — so it is
    DERIVED by scanning the self-describing body. **Every store written today is
    head-only, so this call reads ``turns.bin`` end to end.** rc282 makes that scan
    STREAMED (RAM bounded by the largest region rather than the whole file); it does
    not, and cannot without a format change, make it read fewer BYTES. Use
    :func:`_read_head` when the O(1) head is all you need.

    §44: when the manifest is ABSENT, the catalog is likewise REBUILT by scanning the
    body (the strand is the SSoT, the manifest an optional ``.fai`` cache); that
    rebuild needs ``coupling=`` (its length is the leaf width).

    rc271 (F1251): the per-chromosome ``cap_kind`` is the field-canonical
    ``plasmid`` / ``nuclear`` / ``diploid``; an active :func:`set_type_aliases` /
    :func:`load_type_aliases_toml` mapping re-presents those values here (a pure
    Python post-transform; the C layer stays canonical).
    """
    return _apply_type_aliases_to_catalog(_canonical_catalog(path, coupling))


def _census_topology(types, total_leaves, n_chromosomes) -> str:
    """The §96 STRUCTURAL topology read (biology-native; INTEGER compare, no float /
    libm) — byte-identical to the C ``genome_census_topology``:

    * any nuclear / diploid chromosome → ``"nuclear-like"`` (a eukaryotic nucleus).
    * else ``n>0`` and ``total_leaves <= 8*n`` → ``"organelle-like"`` (a small
      all-plasmid mitochondrion / chloroplast plasmid genome).
    * else ``n>0`` → ``"plasmid/prokaryote-like"`` (all plasmid, no centromere).
    * else → ``"empty"``.

    srmech reads the SHAPE (the cap_kind counts); the caller assigns the ROLE."""
    if types["nuclear"] or types["diploid"]:
        return "nuclear-like"
    if n_chromosomes and int(total_leaves) <= 8 * int(n_chromosomes):
        return "organelle-like"
    if n_chromosomes:
        return "plasmid/prokaryote-like"
    return "empty"


def _census_from_catalog(cat, path) -> dict:
    """Roll one genome's catalog (which now carries per-chromosome ``cap_kind``,
    §96) UP into the census shape — cheap, NO extra body read (the pure-Python peer
    of the C ``genome_census``). Returns ``{path, n_chromosomes, types, chromosomes,
    total_leaves, topology}`` byte-identical to the native tree."""
    entries = cat.get("chromosomes", [])
    types = {"plasmid": 0, "nuclear": 0, "diploid": 0}
    chromosomes = []
    total_leaves = 0
    for e in entries:
        kind = e.get("cap_kind", "plasmid")
        leaf_count = int(e.get("leaf_count", 0))
        total_leaves += leaf_count
        if kind in types:
            types[kind] += 1
        chromosomes.append(
            {"label": e["label"], "type": kind, "leaf_count": leaf_count}
        )
    n_chromosomes = types["plasmid"] + types["nuclear"] + types["diploid"]
    return {
        "path": str(path),
        "n_chromosomes": n_chromosomes,
        "types": types,
        "chromosomes": chromosomes,
        "total_leaves": total_leaves,
        "topology": _census_topology(types, total_leaves, n_chromosomes),
    }


def genome_census(path, *, coupling=None) -> dict:
    """Census ONE genome — the biology-native per-genome roll-up (UPSTREAM §96).

    Answers "what is IN this genome, and how does it partition?" the way biology
    asks it: how many chromosomes, of which TYPE (``plasmid`` accessory/mobile
    plasmid-scale / ``nuclear`` core eukaryotic-centromere / ``diploid`` pair), how
    many total leaves, and a STRUCTURAL nuclear-vs-organelle ``topology`` read.
    rc271 (F1251): the field's own names — ``plasmid`` (was ``stick``) / ``nuclear``
    (was ``minted``); opt back into the old names with :func:`set_type_aliases` /
    :func:`load_type_aliases_toml`. Returns::

        {"path", "n_chromosomes", "types": {"plasmid", "nuclear", "diploid"},
         "chromosomes": [{"label", "type", "leaf_count"}, …],
         "total_leaves", "topology"}

    A thin roll-up over :func:`genome_catalog` (which carries the derived
    ``cap_kind`` per chromosome, §96) — the TYPE rides the catalog's ONE body scan,
    no O(n) per-chromosome loads. srmech reads the SHAPE (the inline cap markers);
    the caller assigns the ROLE. ``coupling=`` is only needed for a manifest-less
    genome (the catalog rebuild width). numpy-free."""
    # §96: native C census (byte-identical CANONICAL tree) when present; else the pure
    # roll-up over the CANONICAL catalog (itself native-accelerated). Native is
    # authoritative. rc271: the type-value alias is a uniform PRESENTATION post-transform
    # applied to the CANONICAL result of EITHER path (so native==pure at the canonical
    # level and the alias rides identically on both). The pure path reads
    # _canonical_catalog (NOT the alias-applying public genome_catalog) so the roll-up
    # counts by the canonical key before the alias is applied once here.
    if _native.has_native_genome() and _native.has_native_genome_census():
        try:
            text = _native.genome_census_c(
                str(Path(path)), _coupling_bytes_or_empty(coupling))
            return _apply_type_aliases_to_census(json.loads(text))
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    return _apply_type_aliases_to_census(
        _census_from_catalog(_canonical_catalog(path, coupling=coupling), path))


def _is_genome_dir(p) -> bool:
    """1 iff ``p`` is a genome directory — holds BOTH ``turns.bin`` and
    ``manifest.json`` (the §96 registry's genome-dir filter)."""
    p = Path(p)
    return p.is_dir() and (p / _BODY_NAME).exists() and (p / _MANIFEST_NAME).exists()


def genome_registry(root, *, coupling=None) -> dict:
    """Census a ROOT of genomes — the cell / melange census (UPSTREAM §96, ADR-0006).

    Scans ``root`` for genome directories (a dir holding BOTH ``turns.bin`` and
    ``manifest.json``), censuses each (:func:`genome_census`), and returns them
    sorted by name::

        {"root", "n_genomes", "genomes": [<census per genome>, …]}

    This is the "cell": which genome is the NUCLEUS (nuclear / diploid chromosomes)
    vs an ORGANELLE (a small all-plasmid plasmid-like genome — a mitochondrion /
    chloroplast). A dir that OPENS but has no genome subdirs yields ``n_genomes``
    0. ``coupling=`` is only needed for manifest-less genomes. numpy-free.

    A ``root`` that CANNOT BE OPENED — absent, permission denied, or not a
    directory — raises :class:`GenomeBoundingError` (rc294), in BOTH projections
    and with the same exception type. Through rc292 the compiled projection
    answered ``{"n_genomes": 0}`` with a success status for those inputs while
    this scripting one raised ``FileNotFoundError``; a typo'd corpus path was
    reported as an empty corpus. Per ADR-0009 the SPLIT was the defect, and this
    surface was the outlier in its own family — :func:`genome_census` on an
    absent path already raised. The ``n_genomes`` 0 promise was always about an
    EMPTY dir, never an absent one, so it is unchanged."""
    # §96: native C registry (PAL dir scan + per-genome census, one byte-identical
    # CANONICAL tree) when present; else the pure os/pathlib scan + per-dir census
    # roll-up over the CANONICAL catalog. rc271: the type-value alias is applied ONCE
    # to the CANONICAL registry tree of EITHER path (native==pure at the canonical level).
    if _native.has_native_genome() and _native.has_native_genome_registry():
        try:
            text = _native.genome_registry_c(
                str(Path(root)), _coupling_bytes_or_empty(coupling))
            return _apply_type_aliases_to_registry(json.loads(text))
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    root_str = str(Path(root))          # normalise identically to the native call above
    # rc294 (ADR-0009): an unopenable root ERRORS in this projection too, and as
    # the SAME exception type the native path raises via _raise_native_genome —
    # GenomeBoundingError, the family's type (genome_census / genome_catalog
    # already raise it here). Raising the bare OSError would leave the two
    # projections agreeing that this is an error but disagreeing about what KIND,
    # which is the same ADR-0009 defect one layer in. The OSError is chained, so
    # the ENOENT-vs-EACCES detail a caller needs for diagnosis is not lost.
    try:
        entries = list(Path(root).iterdir())
    except OSError as exc:
        raise GenomeBoundingError(
            f"genome registry root {root_str!r} cannot be opened ({exc.strerror}) "
            f"— an unreadable / absent / non-directory root is an ERROR, not an "
            f"empty registry (an EMPTY dir that opens yields n_genomes 0)"
        ) from exc
    names = sorted(p.name for p in entries if _is_genome_dir(p))
    # §96: build each child path as ``root + "/" + name`` — MIRROR the C ``genome_join``
    # (``srmech_genome_registry``) byte-for-byte — and roll up via ``_census_from_catalog``
    # DIRECTLY over ``_catalog_data`` (the CANONICAL catalog, NOT ``genome_census`` whose
    # ``str(Path())`` would re-normalise the "/" join back to "\\" on Windows and diverge
    # from the native tree; ``_census_from_catalog`` keeps the path string verbatim). The
    # path field is an identifier, not reopened per-OS — Windows accepts "/" too. Sorting
    # p.name matches C ``genome_sort_names``. The alias is applied ONCE to the whole tree.
    return _apply_type_aliases_to_registry({
        "root": root_str,
        "n_genomes": len(names),
        "genomes": [
            _census_from_catalog(
                _catalog_data(f"{root_str}/{n}", coupling=coupling), f"{root_str}/{n}")
            for n in names
        ],
    })


def _verify_body_integrity(body_bytes, data) -> None:
    """Bound the WHOLE body against the manifest — the whole-genome integrity
    bound, format-aware (rc115 #1245(b)).

    v4 (a ``regions`` array present): re-hash EACH region's byte span against its
    stored ``sha256``, confirm the regions TILE ``[0, len(body))`` contiguously (no
    gap / overlap / trailing bytes), and re-fold the region digests into the
    ``body_sha256`` CHAIN — a flipped / truncated / re-ordered byte fails one of
    those checks. This is the O(1)-append hash contract's re-verification path: the
    per-region digests ARE the provenance units, the chain is the whole-body head.

    v2 / v3 (no ``regions``): the legacy whole-body ``sha256(body) == body_sha256``
    check (back-compat — a pre-rc115 genome carries the whole-body digest)."""
    regions = data.get("regions")
    expected = data["body_sha256"]
    if regions is None:                              # v2 / v3 whole-body digest
        got = _sha256_bytes(bytes(body_bytes))
        if got != expected:
            raise GenomeBoundingError(
                f"genome body integrity bound failed: turns.bin hashes to {got} "
                f"but the manifest committed body_sha256={expected} (a flipped / "
                f"truncated / re-ordered body byte)"
            )
        return
    n = len(body_bytes)
    expect_off = 0
    region_hexes = []
    for r in regions:
        off, ln = int(r["byte_offset"]), int(r["byte_len"])
        if off != expect_off:
            raise GenomeBoundingError(
                f"genome body integrity bound failed: region at byte_offset {off} "
                f"does not tile the body (expected offset {expect_off} — a gap, "
                f"overlap, or re-ordered region)"
            )
        seg = bytes(body_bytes[off:off + ln])
        if len(seg) != ln:
            raise GenomeBoundingError(
                f"genome body integrity bound failed: region [{off}, {off + ln}) "
                f"runs past the body end ({n} bytes) — a truncated body"
            )
        got = _sha256_bytes(seg)
        if got != r["sha256"]:
            raise GenomeBoundingError(
                f"genome region integrity bound failed: region [{off}, {off + ln}) "
                f"hashes to {got} but the manifest committed sha256={r['sha256']} "
                f"(a flipped / re-ordered region byte)"
            )
        region_hexes.append(got)
        expect_off = off + ln
    if expect_off != n:
        raise GenomeBoundingError(
            f"genome body integrity bound failed: the regions tile {expect_off} "
            f"bytes but turns.bin is {n} bytes (trailing un-attested bytes)"
        )
    got_chain = _region_chain(region_hexes)
    if got_chain != expected:
        raise GenomeBoundingError(
            f"genome body integrity bound failed: the region chain folds to "
            f"{got_chain} but the manifest committed body_sha256={expected}"
        )


def _resolve_coupling(data, override=None):
    """Recover ``coupling`` for a load — §44's "manifest cache + load-param fallback".

    Prefer a caller-supplied ``override`` (an :class:`HV` / sequence — for when the
    manifest cache is absent or a different anchor is held); otherwise rebuild it
    from the manifest's stored block and verify its content-address bound (a
    mismatch is a :class:`GenomeBoundingError`)."""
    if override is not None:
        return override if isinstance(override, _HV) else _HV.from_sequence(override)
    one_block = bytes.fromhex(data["coupling"]["hex"])
    if _sha256_bytes(one_block) != data["coupling"]["sha256"]:
        raise GenomeBoundingError(
            "genome coupling integrity bound failed: stored hex does not hash to "
            "the manifest coupling.sha256"
        )
    return _hv_from_block(one_block)


def genome_load(path, *, labels=None, coupling=None):
    """Reconstruct a genome from ``path/`` — UPSTREAM §41 / §44. Returns
    ``(strand, coupling, labels)``.

    ``labels=None`` loads the WHOLE genome: streams ``turns.bin`` block-by-block
    (RAM bounded by the active block, not the whole file held as one giant
    object) and re-hashes the streamed body against the manifest's
    ``body_sha256`` — a mismatch is a :class:`GenomeBoundingError`. A subset
    ``labels=[…]`` is a paged read: it seeks to each requested chromosome's
    ``byte_offset`` and reads only its ``byte_len`` bytes (RAM bounded by the
    largest single chromosome), re-hashing that region's cap against
    ``cap_sha256``. The returned strand is byte-for-byte the saved strand for the
    requested chromosomes (in manifest order). ``coupling`` is rebuilt from the
    manifest's stored block (and verified against its stored hash) unless a
    ``coupling=`` override is supplied (§44 — the manifest is an optional cache). When
    ``manifest.json`` is ABSENT the catalog is reconstructed by scanning
    ``turns.bin`` (§44 — the strand is the SSoT); that rebuild REQUIRES ``coupling=``
    (its length is the leaf width), so you can load a tar of ``turns.bin`` alone.
    """
    path = Path(path)
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    body_path = path / _BODY_NAME

    # §44: coupling from the manifest cache (verify its content-address bound) or
    # the caller-supplied override.
    coupling = _resolve_coupling(data, coupling)

    chrom_entries = list(data["chromosomes"])
    all_labels = [c["label"] for c in chrom_entries]

    if labels is None:
        # §49/rc154: native C whole-genome load (reads turns.bin into one arena-
        # sized buffer + re-hashes the body against the manifest's body_sha256);
        # Python decodes the verified bytes block-by-block. Native is authoritative
        # when present (no fallback); the streaming read below is the no-native impl.
        if _native.has_native_genome():
            try:
                body = _native.genome_load_c(
                    str(path), bytes(_leaf_blocks([coupling])[0]),
                    body_path.stat().st_size)
                # §55/v3: decode the verified body with the dual-format walker
                # (v2 byte-per-symbol | v3 bit-packed | mixed).
                strand = [
                    _hv_from_block(decoded)
                    for _raw, decoded in _walk_region_blocks(
                        body, leaf_dim, context="genome_load")
                ]
                return strand, coupling, all_labels
            except _native.NativeGenomeError as exc:
                _raise_native_genome(exc)
        # Whole-genome streaming read: one block at a time (§55/v3: the block's
        # FIRST byte keys its kind + width — caps and legacy turns are leaf_dim
        # bytes, packed turns 1 + ceil(leaf_dim/4)). Hashing incrementally is not
        # available via sha256_bytes (no streaming API), so we accumulate the
        # body bytes we STREAM (block-by-block, never building an intermediate
        # giant HV/strand object) and verify the whole-body hash.
        strand: List[_HV] = []
        body_acc = bytearray()
        plen = _packed_payload_len(leaf_dim)
        with body_path.open("rb") as f:
            while True:
                first = f.read(1)
                if not first:
                    break
                kind = first[0]
                if kind in (CHROM_CAP_MARKER, GENE_CAP_MARKER, REGULATORY_GENE_MARKER,
                            BOOLEAN_GENE_MARKER, THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER,
                            KERNEL_HEADER_MARKER,
                            KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER,
                            CENTROMERE_CAP_MARKER, DIPLOID_TELOMERE_MARKER,
                            CHROMATIN_MARKER) \
                        or kind <= 3:
                    rest = f.read(leaf_dim - 1)
                    if len(rest) != leaf_dim - 1:
                        raise GenomeBoundingError(
                            f"genome body truncated: trailing {1 + len(rest)} "
                            f"bytes are not a whole leaf_dim={leaf_dim} block"
                        )
                    block = first + rest
                    decoded = block
                elif kind == PACKED_TURN_MARKER:
                    payload = f.read(plen)
                    if len(payload) != plen:
                        raise GenomeBoundingError(
                            f"genome body truncated: trailing {1 + len(payload)} "
                            f"bytes are not a whole packed turn ({1 + plen} bytes)"
                        )
                    block = first + payload
                    decoded = _unpack_turn_payload(payload, leaf_dim)
                else:
                    raise GenomeBoundingError(
                        f"genome body: unrecognised block kind byte {kind} at "
                        f"offset {len(body_acc)}"
                    )
                body_acc.extend(block)
                strand.append(_hv_from_block(decoded))
        _verify_body_integrity(bytes(body_acc), data)
        return strand, coupling, all_labels

    # Subset paged read: seek to each requested chromosome's region.
    want = list(labels)
    by_label = {c["label"]: c for c in chrom_entries}
    missing = [lbl for lbl in want if lbl not in by_label]
    if missing:
        raise ValueError(
            f"genome_load: labels {missing!r} are not in the genome "
            f"(have {all_labels!r})"
        )
    out_strand: List[_HV] = []
    # Manifest order for the requested subset (stable, not call order).
    ordered = [c for c in chrom_entries if c["label"] in set(want)]
    with body_path.open("rb") as f:
        for entry in ordered:
            f.seek(int(entry["byte_offset"]))
            region = f.read(int(entry["byte_len"]))
            if len(region) != int(entry["byte_len"]):
                raise GenomeBoundingError(
                    f"genome chromosome {entry['label']!r} region truncated: read "
                    f"{len(region)} of {entry['byte_len']} bytes"
                )
            cap_block = region[:leaf_dim]
            if _sha256_bytes(cap_block) != entry["cap_sha256"]:
                raise GenomeBoundingError(
                    f"genome chromosome {entry['label']!r} cap integrity bound "
                    f"failed: region cap hashes differently from cap_sha256"
                )
            out_strand.extend(
                _hv_from_block(decoded)
                for _raw, decoded in _walk_region_blocks(
                    region, leaf_dim, context=f"genome_load({entry['label']!r})")
            )
    return out_strand, coupling, [c["label"] for c in ordered]


@contextlib.contextmanager
def _body_handle(path, f=None):
    """Yield a read-only handle on the genome body — the caller's ALREADY-OPEN ``f``
    when one is supplied (**zero** syscalls), else one opened for the duration of the
    block (rc282).

    The single seam every per-region read pages through, so a loop over P regions can
    hold ONE handle instead of paying P opens, while a lone call still Just Works. The
    handle is only ever seek+read — a genome read leaves the file byte-identical."""
    if f is not None:
        yield f
        return
    with _open_body_ro(Path(path) / _BODY_NAME) as opened:
        yield opened


def _read_region(path, entry, leaf_dim, f=None) -> bytes:
    """Page in ONE chromosome's region bytes (seek + bounded read + cap-hash
    check). Shared by :func:`genome_window` / :func:`genome_genes` — RAM is bounded
    by the single chromosome; the leading CHROM cap is re-hashed against the
    manifest's ``cap_sha256`` (a mismatch is a :class:`GenomeBoundingError`).

    ``f`` — an ALREADY-OPEN body handle (rc282); omit it for the open-once-here
    convenience path. Same bytes, same bound, either way."""
    with _body_handle(path, f) as fh:
        fh.seek(int(entry["byte_offset"]))
        region = fh.read(int(entry["byte_len"]))
    if len(region) != int(entry["byte_len"]):
        raise GenomeBoundingError(
            f"genome region {entry['label']!r} truncated "
            f"({len(region)} of {entry['byte_len']} bytes)"
        )
    cap_block = region[:leaf_dim]
    if _sha256_bytes(cap_block) != entry["cap_sha256"]:
        raise GenomeBoundingError(
            f"genome chromosome {entry['label']!r}: cap integrity bound failed"
        )
    return region


# ── §102 / rc280 TARGETED REGION READ ────────────────────────────────────────
# The §89 graph-kernel payload is emitted by _graph_kernel_encode as
#
#     [vocab_size, n_node_ids] + node_ids + [n_extras] + extras + [n_edges] + edges…
#
# so the node_ids label table is a strict PREFIX of the stream, and the edges —
# which are the BULK of a co-occurrence section — sit strictly AFTER it. A reader
# that only wants node_ids therefore never has to touch the edge bytes at all.
# Two on-disk properties make paging just that prefix sound, with NO format change:
#
#   1. quad_turn is a per-leaf REVERSIBLE Klein-4 XOR bind against coupling — leaf k
#      uncouples from leaf k alone. There is no chaining across turns, so a prefix
#      of the coupled leaves uncouples to exactly the prefix of the symbol stream.
#   2. _read_region's integrity bound is the leading CHROM/kernel cap, which is the
#      region's FIRST leaf_dim bytes — so it is present in, and paid identically by,
#      every prefix of at least one block.
#
# This is what turns section_counts from O(P * whole section) into O(P * node_ids).

#: The widest ONE serialised int in the graph-kernel stream: a 2-symbol length
#: header + at most :data:`_GRAPH_KERNEL_MAX_DIGITS` base-4 digits. Used only as the
#: LAST-RESORT width when nothing has been measured yet — sizing every read at this
#: worst case would be badly over-pessimistic (a small vocab id costs 5 symbols, not
#: 17), which would read the whole region and defeat the targeted read entirely.
_GRAPH_KERNEL_MAX_INT_SYMS = 2 + _GRAPH_KERNEL_MAX_DIGITS

#: The first-pass probe width in SYMBOLS — one leaf's worth. Enough to carry the two
#: leading ints (``vocab_size`` + ``n_node_ids``) plus a run of node_ids, so the very
#: first read both learns how many ids there are AND measures what an id actually
#: costs on this genome. Subsequent passes size from that measurement.
_NODE_IDS_PROBE_SYMS = 64

#: How many leading ints precede the node_ids table: ``vocab_size``, ``n_node_ids``.
_NODE_IDS_HEADER_INTS = 2


def _walk_region_prefix_blocks(region: bytes, leaf_dim: int):
    """Walk a region BYTE-PREFIX block-by-block, STOPPING CLEANLY at the last
    COMPLETE block (§102/rc280).

    The strict :func:`_walk_region_blocks` raises :class:`GenomeBoundingError` on a
    block that runs past the end — correct for a whole region, wrong for a
    deliberately truncated read, where a partial trailing block is EXPECTED (a byte
    prefix does not in general end on a block boundary). Same strides, same decode,
    same unrecognised-marker rejection; only the trailing-partial case differs, so a
    corrupt marker is still caught. Yields ``(raw_block, decoded_block)``."""
    plen = _packed_payload_len(leaf_dim)
    k, n = 0, len(region)
    while k < n:
        kind = region[k]
        if kind in _LEAF_WIDE_BLOCK_MARKERS or kind <= 3:
            end = k + leaf_dim
            if end > n:
                return                        # trailing PARTIAL block — stop clean
            yield region[k:end], region[k:end]
        elif kind == PACKED_TURN_MARKER:
            end = k + 1 + plen
            if end > n:
                return                        # trailing PARTIAL block — stop clean
            yield region[k:end], _unpack_turn_payload(region[k + 1:end], leaf_dim)
        else:
            raise GenomeBoundingError(
                f"genome region prefix: unrecognised block kind byte {kind} at "
                f"offset {k} (not a cap, a packed turn, or a Klein-4 symbol)"
            )
        k = end


def _read_region_prefix(path, entry, leaf_dim, max_bytes, f=None) -> bytes:
    """Page in ONLY the leading ``max_bytes`` bytes of ONE chromosome's region
    (§102/rc280) — seek + bounded read + the SAME leading-cap integrity bound
    :func:`_read_region` pays.

    The cap is the region's first ``leaf_dim`` bytes, so any prefix of at least one
    block still re-hashes it against the manifest's ``cap_sha256`` — the targeted
    read is NOT a weaker read, it is the same bound over fewer bytes. ``max_bytes``
    is clamped to the region's true ``byte_len`` (asking for more is not an error,
    it just reads the whole region) and floored at one block.

    ``f`` — an ALREADY-OPEN body handle (rc282). rc280 fixed this read's ASYMPTOTICS
    and left a syscall constant: this function opened ``turns.bin`` on every call and
    :func:`_section_node_ids` calls it in a growth loop, so a scan paid a measured
    **2.0 opens per section** — O(P) opens for what is one file. Pass the scan's own
    handle and the whole pass costs ONE open. Omitting it keeps the convenience path
    (open for the duration of this call), so no caller breaks; the BYTES read and the
    integrity bound paid are identical either way."""
    byte_len = int(entry["byte_len"])
    want = byte_len if max_bytes > byte_len else max_bytes
    if want < leaf_dim:
        want = leaf_dim if leaf_dim < byte_len else byte_len
    with _body_handle(path, f) as fh:
        fh.seek(int(entry["byte_offset"]))
        region = fh.read(want)
    if len(region) != want:
        raise GenomeBoundingError(
            f"genome region {entry['label']!r} truncated "
            f"({len(region)} of {want} prefix bytes)"
        )
    if _sha256_bytes(region[:leaf_dim]) != entry["cap_sha256"]:
        raise GenomeBoundingError(
            f"genome chromosome {entry['label']!r}: cap integrity bound failed"
        )
    return region


def _prefix_syms(region, leaf_dim, coupling):
    """The flat Klein-4 symbol stream carried by a region (or region PREFIX) —
    caps skipped, every data turn uncoupled through ``coupling``, the §89 header
    leaf consumed for the kernel's TRUE length ``D`` and the content trimmed to it.

    The prefix-safe mirror of what :func:`kernel_unpack` does for a whole strand:
    ``leaves[0]`` is the uniformly-Klein-4 header leaf, ``leaves[1:]`` the content.
    Trimming to ``D`` matters even here — a SHORT section's last leaf carries pad
    symbols that would otherwise decode as spurious trailing ints."""
    leaves = [_hv_from_block(dec)
              for _raw, dec in _walk_region_prefix_blocks(region, leaf_dim)
              if not _block_is_cap(dec)]
    if not leaves:
        return []
    unc = [quad_turn(hv, coupling) for hv in leaves]
    true_len, _ld, _et = _unpack_kernel_header_klein4(unc[0])
    flat = [int(x) for lf in unc[1:] for x in lf]
    return flat[:true_len] if true_len < len(flat) else flat


def _prefix_bytes_for_syms(n_syms, leaf_dim, byte_len):
    """The region-prefix BYTE budget for ``n_syms`` payload symbols: the leading cap +
    the §89 header leaf + enough content turns. Clamped to the region's real length.

    Turns are sized at the **v3 packed** width (``1 + ceil(leaf_dim/4)``), the NARROWER
    of the two on-disk turn forms — i.e. this estimate is deliberately OPTIMISTIC. The
    asymmetry is the point: :func:`_section_node_ids` wraps this in a growth loop, so
    under-reading merely costs one more bounded read, while over-reading costs I/O on
    every section of every scan. Sizing for the wider v2 byte-per-symbol turn would
    inflate every estimate ~3.8x at ``leaf_dim=64`` and page most of the region — which
    is exactly the cost this whole targeted read exists to avoid."""
    turn = 1 + _packed_payload_len(leaf_dim)
    n_turns = (n_syms + leaf_dim - 1) // leaf_dim
    need = leaf_dim + turn * (n_turns + 1)     # cap + header leaf + content turns
    return byte_len if need > byte_len else need


def _graph_prefix_ints(syms):
    """``(ints, n_syms_consumed)`` — :func:`_graph_syms_to_ints` plus how many symbols
    the complete ints actually occupied. The consumed count is what lets the targeted
    read MEASURE this genome's real cost-per-int instead of assuming the worst case."""
    ints, i = [], 0
    n = len(syms)
    while i + 2 <= n:
        ln = syms[i] + (syms[i + 1] << 2)
        if ln == 0 or i + 2 + ln > n:
            break
        v = 0
        for k in range(ln):
            v |= syms[i + 2 + k] << (2 * k)
        ints.append(v)
        i += 2 + ln
    return ints, i


def _section_node_ids(path, entry, leaf_dim, coupling, f=None):
    """The GLOBAL ``node_ids`` label table of ONE §89 graph-kernel section, read by
    paging ONLY the node_ids region — never the section's edges (§102/rc280).

    The read GROWS to fit rather than sizing for the worst case. A serialised int is
    2 symbols of length header plus 1–15 base-4 digits, so a worst-case budget is
    ~3.4x too big for the id widths a real corpus produces — big enough that it would
    page the whole region and save nothing. Instead:

    1. a one-leaf PROBE prefix, decoded to recover ``n_node_ids`` AND to MEASURE the
       mean symbols-per-int actually used by this genome;
    2. a re-read sized from that measurement (with a symbol of slack per int), and if
       that still falls short, geometric growth — so the loop always makes progress
       and terminates at the whole region in the limit.

    Typical case: two bounded reads totalling ~the node_ids extent, independent of how
    many EDGES the section carries. Byte-identical to the ``node_ids`` a full
    :func:`_graph_kernel_decode` of the same section returns — never short (a short
    table would silently UNDER-count, which is why every path here either satisfies
    ``n_node_ids`` or ends up having read the entire region).

    ``f`` — an ALREADY-OPEN body handle (rc282). The growth loop above is exactly why
    this matters: every iteration was a fresh ``open`` of ``turns.bin``, so the
    TYPICAL two-read case cost **2 opens per section** and a P-section scan paid 2P
    opens of one file. The loop now runs entirely inside ONE handle — the caller's
    when supplied, otherwise one opened here for the whole loop (so even a lone call
    is 1 open, not 2). Bytes read and bounds paid are unchanged."""
    byte_len = int(entry["byte_len"])
    want = _prefix_bytes_for_syms(_NODE_IDS_PROBE_SYMS, leaf_dim, byte_len)
    with _body_handle(path, f) as fh:
        while True:
            ints, used = _graph_prefix_ints(
                _prefix_syms(_read_region_prefix(path, entry, leaf_dim, want, fh),
                             leaf_dim, coupling))
            at_end = want >= byte_len
            if len(ints) >= _NODE_IDS_HEADER_INTS:
                n_nid = int(ints[1])
                if n_nid <= 0:
                    return []
                need = _NODE_IDS_HEADER_INTS + n_nid
                if len(ints) >= need:
                    return [int(v) for v in ints[_NODE_IDS_HEADER_INTS:need]]
                # MEASURED width (round up, +1 symbol of slack), not the 17-symbol
                # worst case — this keeps the read proportional to node_ids.
                per = ((used + len(ints) - 1) // len(ints)) + 1 if ints \
                    else _GRAPH_KERNEL_MAX_INT_SYMS
                grow = _prefix_bytes_for_syms(need * per, leaf_dim, byte_len)
                if at_end:
                    raise GenomeBoundingError(
                        f"genome chromosome {entry['label']!r}: its §89 payload "
                        f"declares {n_nid} node_ids but only "
                        f"{len(ints) - _NODE_IDS_HEADER_INTS} are present in the "
                        f"whole {byte_len}-byte region — the section is malformed "
                        f"(a SHORT node_ids table would silently under-count)"
                    )
            else:
                if at_end:
                    return []                   # a section carrying no payload at all
                grow = 0                        # nothing decoded yet — just double
            if grow <= want:                    # guarantee forward progress
                grow = want * 2
            want = byte_len if grow > byte_len else grow


def _region_leaves(path, entry, leaf_dim, f=None):
    """One chromosome's stored DATA turns, paged against an ALREADY-DERIVED catalog
    ``entry`` (§102/rc280) — the catalog-once counterpart of :func:`genome_window`.

    :func:`genome_window` re-derives the whole catalog on EVERY call, and on a v12
    head-only manifest that means re-reading and re-Merkle-folding the entire body
    per chromosome. A caller looping over P chromosomes pays O(P × body) for what is
    O(body) of actual work. Deriving :func:`_catalog_data` once and calling this per
    chromosome is byte-identical and removes that quadratic term. Same bounded read,
    same leading-cap integrity bound, same cap-skipping walk.

    ``f`` — an ALREADY-OPEN body handle (rc282); pass the loop's handle so P regions
    cost ONE open rather than P."""
    return [
        _hv_from_block(decoded)
        for _raw, decoded in _walk_region_blocks(
            _read_region(path, entry, leaf_dim, f), leaf_dim,
            context=f"_region_leaves({entry['label']!r})")
        if not _block_is_cap(decoded)
    ]


def _region_strand(region, leaf_dim) -> List["_HV"]:
    """Reconstruct a region's full HV strand (every block — caps + data turns).
    §55/v3: decoded with the dual-format walker (v2 | v3 | mixed blocks)."""
    return [
        _hv_from_block(decoded)
        for _raw, decoded in _walk_region_blocks(
            region, leaf_dim, context="genome region")
    ]


def genome_window(path, label, *, coupling=None):
    """Page in ONLY one chromosome's leaves from ``path/`` — UPSTREAM §41 / §44.

    Seeks to the chromosome ``label``'s ``byte_offset`` and reads only its
    ``byte_len`` bytes (RAM bounded by that one chromosome), re-hashing the region
    cap against the manifest's ``cap_sha256`` — a mismatch is a
    :class:`GenomeBoundingError`. Returns the chromosome's stored DATA turns (the
    coupled leaves) as a list of Klein-4 vectors, in order — §44 skips EVERY cap by
    its inline marker (the leading CHROM cap AND any intra-chromosome GENE caps), so
    a multi-gene chromosome's window FLATTENS to its data turns (use
    :func:`genome_genes` to keep the per-gene split). The disk-paging counterpart of
    reaching into one partition of the genome. §44: when ``manifest.json`` is ABSENT
    the offsets are reconstructed by scanning ``turns.bin`` (the strand is the SSoT);
    pass ``coupling=`` (its length is the leaf width) for that manifest-less path.
    """
    path = Path(path)
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    by_label = {c["label"]: c for c in data["chromosomes"]}
    if label not in by_label:
        raise ValueError(
            f"genome_window: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    # §49: native C window (seek + bounded read + cap-integrity check) returns the whole
    # region; Python skips the caps to the DATA turns. native is authoritative when present (no fallback).
    if _native.has_native_genome():
        try:
            region = _native.genome_window_c(
                str(path), label, _coupling_bytes_or_empty(coupling),
                (path / _BODY_NAME).stat().st_size)
            return [
                _hv_from_block(decoded)
                for _raw, decoded in _walk_region_blocks(
                    region, leaf_dim, context=f"genome_window({label!r})")
                if not _block_is_cap(decoded)
            ]
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    region = _read_region(path, by_label[label], leaf_dim)
    leaves: List[_HV] = []
    for _raw, decoded in _walk_region_blocks(
            region, leaf_dim, context=f"genome_window({label!r})"):
        if _block_is_cap(decoded):              # skip CHROM lead cap + GENE caps
            continue
        leaves.append(_hv_from_block(decoded))
    return leaves


def genome_genes(path, label, *, coupling=None):
    """Page ONE multi-gene chromosome's genes back from ``path/`` — F732/S43.1 / §44.

    The disk counterpart of the in-memory :func:`genes`: pages in only that
    chromosome's region (RAM-bounded + cap-integrity-checked), then SCANS it for the
    inline GENE caps (§44 — no gene-index sidecar; the gene boundaries + labels live
    in the body) and re-binds ``coupling`` (rebuilt + hash-verified from the manifest
    cache, or a ``coupling=`` override) to recover ``[(gene_label, gene_leaves), …]``
    — exactly what ``genes(chromosome(genes=…, one), one)`` returns in memory.
    Raises ``ValueError`` if the chromosome has NO inline GENE caps (it is a
    single-kernel chromosome — use :func:`genome_window` / :func:`partition`)::

        s = genome(chromosomes=[("g", [("rules", R), ("board", B)])], one)
        genome_save(s, path, one)
        genome_genes(path, "g") == [("rules", R), ("board", B)]

    §44: when ``manifest.json`` is ABSENT the offsets are reconstructed by scanning
    ``turns.bin`` (the strand is the SSoT) — ``coupling=`` is required there (and is
    needed anyway to uncouple the genes).
    """
    path = Path(path)
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    by_label = {c["label"]: c for c in data["chromosomes"]}
    if label not in by_label:
        raise ValueError(
            f"genome_genes: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    coupling = _resolve_coupling(data, coupling)
    region = _read_region(path, by_label[label], leaf_dim)
    region_strand = _region_strand(region, leaf_dim)
    if not any(_cap_kind(hv) in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                                 THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER)
               for hv in region_strand):
        raise ValueError(
            f"genome_genes: chromosome {label!r} has no inline GENE caps — it is a "
            f"single-kernel chromosome; use genome_window / partition"
        )
    # §44/§128: scan the inline gene structure — genes() skips the leading CHROM cap and
    # splits on the GENE caps (plain 0x47 / regulatory 0x67), uncoupling each data turn
    # through coupling (use gene_express() to also apply the regulatory-mask filter).
    return genes(region_strand, coupling)


# ─────────────────────────────────────────────────────────────────────────────
# §134/rc135 (#1273, siona green-light) — DEMAND-LOADED gene expression: the two
# ops that make the #736 probe SHIPPABLE (bounded RAM WITHOUT bounded availability
# via demand-load). gene_express_plan computes the EXPRESSED set + on-disk byte
# ranges WITHOUT touching content (an offset-only LOAD-PLAN); genome_genes_expressed
# then SEEKS + loads + decodes ONLY the expressed byte-ranges → BYTE-IDENTICAL to the
# expressed subset of a full genome_genes filtered by gene_express, WITHOUT loading
# the unexpressed. The ops READ the existing rc115 v4 manifest offsets + the delivered
# E1/E2/E4/E3 inline gates — NO format addition (v11 stays).
# ─────────────────────────────────────────────────────────────────────────────


def _open_body_ro(body_path):
    """Open a genome body (``turns.bin``) READ-ONLY — the single seam EVERY genome read
    pages its bytes through (rc282), so a caller can MEASURE bytes-touched (the
    bounded-I/O proof). Returns an open binary file the caller ``with``-closes; NEVER
    writes (the ops are reads — the file is byte-identical after).

    Opens via ``Path.open``, deliberately, NOT ``builtins.open``. Instrumentation in
    this package's own suite hooks ``Path.open`` to prove region-bounded I/O, and a
    ``builtins.open`` here is invisible to that hook — a seam that silently stops
    observing is worse than no seam, because the assertions keep passing. Every other
    body read in this module already went through ``Path.open``; this one now agrees."""
    return Path(body_path).open("rb")


def _plan_validate_cell_state(op, cell_state):
    """Shared cell_state guard for the §134 demand-load ops — a cell-state is a
    non-negative Class-I bitmask (each set bit a present condition; no float, never
    ``abs()`` — a bitmask is never negated)."""
    if not isinstance(cell_state, int) or isinstance(cell_state, bool):
        raise ValueError(
            f"{op}: cell_state must be an exact int (Class-I bitwise); got "
            f"{cell_state!r}")
    if cell_state < 0:
        raise ValueError(
            f"{op}: cell_state must be non-negative (a bitmask is never signed; a "
            f"cell-state is never negated, so never abs()); got {cell_state}")


def _plan_close_gene(plan, pending, end_pos, cell_state):
    """Close the STRAND-variant skeleton-scan's pending gene at ``end_pos`` — append
    ``(label, byte_offset, byte_len)`` to ``plan`` iff the region was ACCESSIBLE at the gene's
    OPEN (§98 chromatin outer gate — the access state captured in ``pending`` when the gene cap was
    reached, so a marker AFTER the cap does not retro-silence it) AND the gene's cap EXPRESSES under
    ``cell_state`` (the SAME §128/§130/§131 decision :func:`gene_express` uses; the gate reads only
    the cap, never a decoded leaf)."""
    lbl, cap_hv, gstart, access_open = pending
    if access_open and _gene_expresses(cap_hv, cell_state):
        plan.append((lbl, gstart, end_pos - gstart))


def gene_express_plan(strand_or_path, coupling, cell_state):
    """The offset-only LOAD-PLAN for demand-loaded gene expression — §134/rc135
    (#1273, siona green-light; the #736 probe made shippable).

    Computes the EXPRESSED set + each expressed unit's ON-DISK byte-range WITHOUT
    reading content (never decodes a leaf) — the plan a partial-load reader
    (:func:`genome_genes_expressed`) then seeks. Returns
    ``[(label, byte_offset, byte_len), …]`` for the expressed genes / regions.

    Two variants, dispatched on the input:

    * **PATH variant (variant b — the PRIMARY demand-load case):** ``strand_or_path``
      is a genome directory (with the rc115 v4 manifest). For each chromosome REGION the
      plan seeks to the manifest ``byte_offset`` and reads ONLY the region's head GATE cap
      (the SECOND block, one ``leaf_dim``-byte cap right after the CHROM cap), evaluates its
      inline gate (E1 ``0x67`` / E2 ``0x62`` / E4 ``0x77`` / E3 ``0x64`` — the delivered
      gates) against ``cell_state``, and includes the EXPRESSED regions'
      ``(chromosome_label, byte_offset, byte_len)``. It MUST NOT read the region body —
      the PLAN reads are bounded RAM AND bounded I/O (bytes-touched ≪ full body).
      **Scope of that claim (rc282):** it covers the plan's own per-region reads. The
      catalog derivation that PRECEDES them scans the whole body on a v12+ head-only
      manifest (see :func:`genome_catalog`), so end-to-end bytes-READ for the path
      variant is not ≪ full body — only the per-region gate reads are. A region with no head gene
      cap (a single-kernel chromosome, ``byte_len < 2·leaf_dim``) is not a gated community
      and is skipped. This is the siona community=chromosome layout: the per-chromosome
      head gate IS the community gate. Mixed E1/E2/E4/E3 gate-types across chromosomes are
      the delivered gates — the plan gates by the inline mask regardless of kind. **§98/rc269
      chromatin OUTER gate (§98.1/rc274 cell-state-conditional):** if the head slot is a CHROMATIN
      cap (``0x48``), its COMPUTED accessibility under ``cell_state`` (:func:`_chromatin_access` —
      a constitutive cap is constant; a §98.1/G1 FACULTATIVE cap fires per cell_state) gates the
      whole region — a SILENCED (accessibility numerator ``0`` under this cell_state) region is
      SKIPPED at plan time having touched ONLY the chromatin cap (its gene gate cap is NEVER read —
      even fewer bytes than the §134 read; the cell-state gate rides IN the already-paged cap, so
      the skip stays a SINGLE-SEEK bounded-I/O read); an OPEN (accessible) region advances one slot
      and reads the gene gate as before. A chromatin-FREE region is byte-for-byte the rc135 read.
      WHICH regions are condensed is now a FUNCTION of cell_state (facultative heterochromatin).
    * **STRAND variant (variant a — the in-memory fallback):** ``strand_or_path`` is an
      in-memory strand (a list of Klein-4 vectors). The plan SKELETON-SCANS it — walking
      blocks, computing each block's ON-DISK byte span (a cap is ``leaf_dim`` bytes; a data
      turn is the §55/v3 bit-packed ``1 + ceil(leaf_dim/4)`` bytes — the payload is SEEKED
      PAST, never decoded), splitting on the inline GENE caps, and delimiting each EXPRESSED
      gene's byte-range ``(gene_label, byte_offset, byte_len)`` (the gene cap + its data
      turns, in the on-disk layout :func:`genome_save` would write). The expressed-label set
      equals :func:`gene_express`'s on the same strand + cell_state.

    ⚠️ A READ — the strand / file is byte-identical after this call. ``cell_state`` is a
    non-negative exact int (Class-I bitwise; no float, never ``abs()``). The PATH variant
    is native-dispatched (byte-identical C peer ``srmech_genome_gene_express_plan`` reads
    only the head gate caps + emits the same offset plan); pure Python is the complete
    alternative. NO format addition — the ops read the existing caps/manifest (v11 stays).
    """
    _plan_validate_cell_state("gene_express_plan", cell_state)
    assert GENOME_FORMAT_VERSION == 15      # a READ of existing caps/manifest
    #  (v13 centromere 0x58 + v15 chromatin 0x48 are INTERIOR caps; BOTH the STRAND plan and —
    #   as of §98/rc269 — the PATH demand-load plan read the chromatin OUTER gate: a condensed
    #   region is skipped at plan time on a single head-slot seek, never touching its gene gate)
    if isinstance(strand_or_path, (str, Path)) or hasattr(strand_or_path, "__fspath__"):
        return _gene_express_plan_path(Path(strand_or_path), coupling, cell_state)
    return _gene_express_plan_strand(strand_or_path, coupling, cell_state)


def _gene_express_plan_path(path, coupling, cell_state):
    """PATH variant (b): the DEMAND-LOAD plan — read ONLY each region's head cap(s) via the
    manifest ``byte_offset`` (a seek); NEVER the region body (bounded I/O). §98/rc269: a HEAD
    CHROMATIN cap (``0x48``) is the OUTER access gate over the §134 gene gate — a CONDENSED
    (silenced) region is SKIPPED at plan time having touched ONLY its chromatin cap (its gene
    gate cap is NEVER read); an OPEN region advances one slot and reads the gene gate as before;
    a chromatin-FREE region's read + plan are byte-for-byte the rc135 read."""
    if _native.has_native_genome():
        try:
            return _native.genome_gene_express_plan_c(
                str(path), cell_state, _coupling_bytes_or_empty(coupling))
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    # The catalog read. On a v12+ HEAD-ONLY manifest — which is EVERY store written
    # today — this DOES read turns.bin: the chromosome table is derived by scanning the
    # body (ADR-0003, no stored plaintext TOC). A comment here used to claim the
    # opposite ("never opens turns.bin"); it was false, and it is plausibly how the
    # whole-body slurp this rc removed survived review. Only a v<=11 full manifest is
    # body-free. The BOUNDED-I/O claim below is about the per-region PLAN reads (head
    # caps only), not about deriving the catalog.
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    plan = []
    with _open_body_ro(path / _BODY_NAME) as f:
        for c in data["chromosomes"]:
            off, ln = int(c["byte_offset"]), int(c["byte_len"])
            if _plan_path_head_expresses(f, off, ln, leaf_dim, cell_state):
                plan.append((c["label"], off, ln))
    return plan


def _plan_path_head_expresses(f, off, ln, leaf_dim, cell_state):
    """§134/§98 — seek the region head from the ALREADY-OPEN body ``f`` and decide inclusion
    WITHOUT reading the body (bounded I/O). Reads the block at ``off + leaf_dim`` (the head slot
    right after the CHROM cap). A HEAD CHROMATIN cap (``0x48``, rc269) is the OUTER gate: if it is
    SILENCED (accessibility numerator ``== 0`` — the SAME Class-K predicate :func:`gene_express` /
    the STRAND plan use, NEVER ``abs()``) the region is SKIPPED reading ONLY that cap; if it is
    OPEN the gene gate is the NEXT slot (``off + 2·leaf_dim``). Then the unchanged §134 gene-gate
    decision: True iff the gate block is a GENE marker AND :func:`_gene_expresses` under
    ``cell_state``. A READ — never decodes a leaf, never touches the body."""
    if ln < 2 * leaf_dim:                       # no head GENE cap → not a gated community
        return False
    gate_off = off + leaf_dim                   # skip the CHROM cap → the head slot
    f.seek(gate_off)
    head_block = f.read(leaf_dim)
    if len(head_block) < leaf_dim:
        return False
    if head_block[0] == CHROMATIN_MARKER:       # §98/§98.1 HEAD chromatin cap — the OUTER access gate
        _an, _ad = _chromatin_access(_hv_from_block(head_block), cell_state)  # §98.1/G1 conditional
        access_open = _an > 0                   # accessible iff level numerator > 0 (Class-K, no abs)
        if not access_open:
            return False                        # heterochromatin → SKIP (gene gate NEVER read)
        gate_off += leaf_dim                    # euchromatin → the gene gate is the NEXT slot
        if gate_off + leaf_dim > off + ln:      # no room for a gene cap after the chromatin cap
            return False
        f.seek(gate_off)
        head_block = f.read(leaf_dim)
        if len(head_block) < leaf_dim:
            return False
    if head_block[0] not in _GENE_MARKERS:
        return False                            # the head block is not a gene cap
    return _gene_expresses(_hv_from_block(head_block), cell_state)


def _gene_express_plan_strand(strand, coupling, cell_state):
    """STRAND variant (a): the in-memory skeleton-scan — walk the strand's blocks
    computing their ON-DISK byte spans, gate each gene by its cap, and delimit each
    EXPRESSED gene's byte-range. Never decodes a data-turn payload (seeks past it)."""
    leaf_dim = len(list(coupling))
    turn_width = 1 + _packed_payload_len(leaf_dim)   # §55/v3 on-disk packed-turn width
    plan = []
    pos = 0
    pending = None                              # (label, cap_hv, gene_byte_start)
    access_open = True                          # §98 chromatin OUTER gate: euchromatin by default
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in _GENE_MARKERS:
            if pending is not None:
                _plan_close_gene(plan, pending, pos, cell_state)
            _marker, lbl = _unpack_cap(hv)
            pending = (lbl, hv, pos, access_open)   # capture the access state at the gene's OPEN
            pos += leaf_dim
        elif kind == CHROMATIN_MARKER:          # §98/§98.1 access marker — a leaf_dim cap; gates the stretch
            _an, _ad = _chromatin_access(hv, cell_state)   # §98.1/G1 cell-state-conditional access
            access_open = _an > 0               # accessible iff the level numerator > 0 (Class-K)
            pos += leaf_dim
        elif kind in (CHROM_CAP_MARKER, KERNEL_HEADER_MARKER,
                      KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER):
            if pending is not None:             # a chromosome boundary closes the gene
                _plan_close_gene(plan, pending, pos, cell_state)
                pending = None
            access_open = True                  # a chromosome boundary resets access (euchromatin)
            pos += leaf_dim
        else:
            pos += turn_width                   # a data turn — SEEK PAST its packed payload
    if pending is not None:
        _plan_close_gene(plan, pending, pos, cell_state)
    return plan


def _plan_read_region(f, entry, leaf_dim):
    """Seek + bounded read of ONE chromosome region from an ALREADY-OPEN body file (the
    §134 partial-load reader's per-region page — RAM + I/O bounded by that one region),
    the leading CHROM cap re-hashed against the manifest ``cap_sha256`` (the §45
    :class:`GenomeBoundingError` bound). Reads only ``byte_len`` bytes from ``byte_offset``
    — the unexpressed regions are never touched."""
    off, ln = int(entry["byte_offset"]), int(entry["byte_len"])
    f.seek(off)
    region = f.read(ln)
    if len(region) != ln:
        raise GenomeBoundingError(
            f"genome region {entry['label']!r} truncated "
            f"({len(region)} of {ln} bytes)")
    if _sha256_bytes(region[:leaf_dim]) != entry["cap_sha256"]:
        raise GenomeBoundingError(
            f"genome chromosome {entry['label']!r}: cap integrity bound failed")
    return region


def genome_genes_expressed(path, coupling, cell_state):
    """The PARTIAL-LOAD reader for demand-loaded gene expression — §134/rc135 (#1273).

    Uses :func:`gene_express_plan` (the PATH / variant-b plan) to SEEK + load + decode ONLY
    the EXPRESSED chromosome regions, then filters each region's genes by
    :func:`gene_express` — returning ``[(gene_label, gene_leaves), …]`` BYTE-IDENTICAL to
    the expressed subset of a full ``gene_express`` over the whole genome, WITHOUT loading
    the unexpressed regions (bounded RAM AND bounded I/O). In the siona community=chromosome
    layout the per-chromosome head gate IS the community gate, so an unexpressed community
    (head gate off) contributes no expressed gene — skipping its region is exact.

    ⚠️ A READ — the file is byte-identical after this call (biology reads the regulatory
    region, it does not rewrite the DNA). ``cell_state`` is a non-negative exact int (Class-I
    bitwise; no float, never ``abs()``). The plan is native-dispatched (the C peer
    ``srmech_genome_gene_express_plan``); the per-region load + :func:`gene_express` decode
    are the exact pure path — the leaves are byte-identical whether the plan came from C or
    Python. NO format addition (the reader reads the existing v4 manifest + caps; v11 stays).
    """
    _plan_validate_cell_state("genome_genes_expressed", cell_state)
    assert GENOME_FORMAT_VERSION == 15      # a READ of existing caps/manifest
    #  (the PATH demand-load reader's per-region chromatin single-seek skip (§98) is deferred to
    #   rc269; today it reads the §134 gene-gate-only plan — a chromatin-free genome is unaffected)
    path = Path(path)
    plan = _gene_express_plan_path(path, coupling, cell_state)   # the expressed communities
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    coupling_hv = _resolve_coupling(data, coupling)
    by_label = {c["label"]: c for c in data["chromosomes"]}
    out = []
    with _open_body_ro(path / _BODY_NAME) as f:
        for (chrom_label, _off, _ln) in plan:
            region = _plan_read_region(f, by_label[chrom_label], leaf_dim)
            region_strand = _region_strand(region, leaf_dim)
            for gene in gene_express(region_strand, coupling_hv, cell_state):
                out.append(gene)
    return out


def genome_append(path, label, leaves, coupling, *, kernel=False, catalog=None) -> dict:
    """Append ONE chromosome to an existing genome at ``path/`` in O(1) — UPSTREAM
    §41 / §56 (rc115 #1245(b)) + v12 (the O(1) genome-native rewrite). Returns the
    full catalog ``data`` dict (unchanged shape: ``chromosomes`` / ``regions`` / … ).

    **What hits disk is O(1):** the new chromosome's blocks TAIL-EXTEND
    ``path/turns.bin`` (append-only — prior body bytes are never read, rewritten, or
    re-hashed) and the tiny v12 HEAD manifest is rewritten (``n_turns`` /
    ``n_chromosomes`` / the O(1) ``body_sha256`` chain fold). The per-chromosome
    ``chromosomes`` / ``regions`` arrays are **never written to disk** — they are a
    plaintext table-of-contents (ADR-0003) and were the O(N²) append wall; they are
    DERIVED by scanning the self-describing body when a catalog is read.

    **The ``catalog=`` argument has three modes — thread it to keep the whole call
    O(1) (the streaming shape); do NOT loop with the default or you rebuild the
    catalog every call (the O(n²) wall):**

    * ``catalog=None`` (default) — a **cold one-off** append. The disk write is O(1),
      but the returned full catalog is DERIVED from the body once (O(n)). Fine for a
      single append; looping this way is O(n²).
    * ``catalog=<dict>`` — **thread a prior return** (the streaming loop). The returned
      dict is mutate-appended one entry in memory — O(1), N appends → O(N) total::

          data = genome_save(strand, path, one)          # or genome_append(..., catalog=None)
          for lbl, lv in items:
              data = genome_append(path, lbl, lv, one, catalog=data)   # each O(1)

    * ``catalog="load"`` — **resume a streaming loop with no prior return in hand**
      (§95.2 / #1407). Reads the full threadable catalog from disk ONCE (O(n)), does
      the append, and returns a dict to thread for the rest of the loop (O(1)/append)::

          data = "load"
          for lbl, lv in items:                          # first call O(n), the rest O(1)
              data = genome_append(path, lbl, lv, one, catalog=data)

    An empty / partial ``catalog={}`` (a dict with no ``leaf_dim``) is NOT a genome
    catalog — it raises a clear ``ValueError`` pointing at these modes, never a bare
    ``KeyError`` (the §95.2 footgun fix).

    Labels are content-addresses (ADR-0003), so there is **no O(n) duplicate-label
    scan** — the caller owns label uniqueness (a duplicate label is last-wins on
    read, exactly as two identical content-addresses would be).

    §89/rc126: ``kernel=True`` opens the appended chromosome with a KERNEL telomere
    (``0x6B``) — used by :func:`genome_append_kernel`.
    """
    path = Path(path)
    # §95.2 / #1407 ergonomics — three explicit catalog MODES (see the docstring):
    #   catalog=None      cold one-off append (O(1) disk; O(n) catalog derived for the return)
    #   catalog=<dict>    thread a prior return — O(1) mutate-append (the streaming loop)
    #   catalog="load"    RESUME a streaming loop with no prior return in hand: read the full
    #                     threadable catalog from disk ONCE (O(n)), then thread it (O(1)/append)
    if catalog == "load":
        catalog = _catalog_data(path, coupling)      # O(n) once → a threadable catalog dict
    if catalog is not None and "leaf_dim" not in catalog:
        # the catalog={} / partial-dict footgun — a clear message, not a bare KeyError.
        raise ValueError(
            "genome_append: the catalog dict has no 'leaf_dim', so it is not a genome "
            "catalog. To resume a streaming append with no prior return in hand, pass "
            "catalog=\"load\" (reads the catalog from disk once, then thread the return "
            "for O(1) appends); pass catalog=None for a one-off cold append; or pass the "
            "dict returned by a prior genome_save/genome_append call to thread it."
        )
    # The O(1) head — the threaded in-memory catalog, else a cheap head read (O(1) for
    # a v12 head-only manifest; a one-time O(n) read/scan on the FIRST append to a
    # legacy v≤11 / manifest-less genome, which then becomes v12 head-only).
    head = catalog if catalog is not None else _read_head(path, coupling)
    leaf_dim = int(head["leaf_dim"])
    if len(list(coupling)) != leaf_dim:
        raise ValueError(
            f"genome_append: coupling dim {len(list(coupling))} != genome leaf_dim "
            f"{leaf_dim}"
        )

    new_strand = chromosome(leaves, coupling, label=label, kernel=kernel)
    new_blocks = _leaf_blocks(new_strand)
    # §55/v3: the appended region is the packed on-disk form (caps verbatim, data
    # turns bit-packed) — _disk_block validates each width.
    appended = b"".join(_disk_block(blk, leaf_dim) for blk in new_blocks)
    coupling_block = _leaf_blocks([coupling])[0]
    body_path = path / _BODY_NAME

    # Legacy v2/v3 (format_version < 4): the head's body_sha256 is a WHOLE-BODY digest,
    # NOT the region chain, so it cannot be folded in O(1). The FIRST append MIGRATES —
    # tail-extend, then rebuild the v12 head (chain) from the grown body (O(n), once);
    # every subsequent append reads the v12 head and is O(1). (A threaded catalog is
    # already v12-chain, so it never takes this branch.)
    if catalog is None and int(head.get("format_version", GENOME_FORMAT_VERSION)) < 4:
        if _native.has_native_genome():
            try:
                _native.genome_append_c(str(path), label, appended, leaf_dim,
                                        bytes(coupling_block))
            except _native.NativeGenomeError as exc:
                _raise_native_genome(exc)
        else:
            with body_path.open("ab") as f:
                f.write(appended)
            grown = body_path.read_bytes()
            data = _rebuild_manifest_from_body(grown, leaf_dim, coupling)
            mig_head = _build_head_data(leaf_dim, coupling_block, data["n_turns"],
                                        len(data["chromosomes"]), data["body_sha256"])
            _write_manifest(path, _manifest_record(mig_head))
        return _catalog_data(path, coupling)

    byte_offset = body_path.stat().st_size          # O(1) stat = the PRIOR body size
    region_sha256 = _sha256_bytes(appended)
    new_body_sha = _chain_step(head["body_sha256"], region_sha256)
    new_n_turns = int(head["n_turns"]) + len(new_blocks)
    new_n_chrom = int(head.get("n_chromosomes", len(head.get("chromosomes", [])))) + 1
    new_chrom = {
        "label": label,
        "cap_sha256": _sha256_bytes(new_blocks[0]),
        "leaf_count": len(new_blocks) - 1,
        "byte_offset": byte_offset,
        "byte_len": len(appended),
    }
    new_region = {
        "byte_offset": byte_offset,
        "byte_len": len(appended),
        "sha256": region_sha256,
    }
    head_data = _build_head_data(leaf_dim, coupling_block, new_n_turns, new_n_chrom,
                                 new_body_sha)

    # Write the DNA + the O(1) head. Native C append is AUTHORITATIVE when present —
    # it tail-extends turns.bin + writes the head, no whole-body / whole-catalog
    # rewrite. Otherwise the pure path does the same tail-extend + head write.
    if _native.has_native_genome():
        try:
            _native.genome_append_c(str(path), label, appended, leaf_dim,
                                    bytes(coupling_block))
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    else:
        with body_path.open("ab") as f:
            f.write(appended)                       # O(1) tail-extend
        _write_manifest(path, _manifest_record(head_data))   # O(1) HEAD-ONLY

    # Return the full catalog dict (unchanged shape).
    if catalog is not None:
        # O(1): mutate-append the in-memory catalog + advance the head fields.
        catalog.setdefault("chromosomes", []).append(new_chrom)
        catalog.setdefault("regions", []).append(new_region)
        catalog["n_turns"] = new_n_turns
        catalog["n_chromosomes"] = new_n_chrom
        catalog["body_sha256"] = new_body_sha
        catalog["format_version"] = GENOME_FORMAT_VERSION
        return catalog
    # Cold call: derive the full catalog from the body once (O(n)) — disk stayed O(1).
    return _catalog_data(path, coupling)


def genome_append_kernel(path, label, hv, *, element_type="klein4",
                         coupling=None, catalog=None) -> dict:
    """Append a newly-taught kernel — WITH its §89 header — to a genome in O(1)
    amortised (§89/rc126, issue #1261). The uniformly-Klein-4 payoff of format v6.

    ``hv`` is the flat kernel (a sequence of Klein-4 sector symbols ``{0,1,2,3}`` — an
    :class:`HV`, ``list[int]``, ``bytes``, …) of ANY dimension ``D``. It is chunked
    into ``leaf_dim``-wide leaves (the genome's ``leaf_dim``, final leaf zero-padded)
    LED by the uniformly-Klein-4 §89 header LEAF that SELF-RECORDS ``D`` +
    ``element_type`` + ``leaf_dim`` (:func:`_pack_kernel_header_klein4`). Because that
    header is a 100 %-Klein-4 leaf, ``[header, *content]`` is just a list of Klein-4
    leaves — so this FALLS OUT of :func:`genome_append` (``kernel=True``): the chromosome
    tail-extends ``turns.bin`` and folds one region onto the ``body_sha256`` chain in
    O(1), no whole-body re-hash/re-scan. Recover the EXACT kernel (trimmed to ``D``)
    with :func:`kernel_unpack` / :func:`genome_window`-then-decode.

    This is the deliverable a downstream ``teach a kernel → append it`` loop was about
    to hand-roll: before v6 the §60 ``0x4B`` byte-TLV header could NOT ride
    :func:`genome_append` (unbinding it via klein4_bind failed "must be in {0,1,2,3}");
    v6 makes the header a Klein-4 leaf, so appending a kernel WITH its header is native.

    ``coupling`` (the coupling invariant) is optional when ``path`` has a manifest (it
    is resolved from the manifest cache) and REQUIRED for a manifest-less genome (its
    length is the leaf width). ``element_type`` is the declared header enum
    (``"klein4"`` today). Returns the updated manifest ``data`` dict. Raises
    ``ValueError`` if ``label`` already exists or a symbol is not a Klein-4 sector.
    """
    if element_type not in _ELEMENT_TYPE_CODES:
        raise ValueError(
            f"genome_append_kernel: unknown element_type {element_type!r}; declared "
            f"types are {sorted(_ELEMENT_TYPE_CODES)} (element_type is a §89 header enum)"
        )
    et_code = _ELEMENT_TYPE_CODES[element_type]
    path = Path(path)
    head = catalog if catalog is not None else _read_head(path, coupling)   # O(1) head
    leaf_dim = int(head["leaf_dim"])
    if leaf_dim < _KERNEL_HEADER_KLEIN4_SYMS:
        raise ValueError(
            f"genome_append_kernel: genome leaf_dim {leaf_dim} < "
            f"{_KERNEL_HEADER_KLEIN4_SYMS} — the §89 kernel header does not fit one leaf"
        )
    if coupling is None:
        coupling = _resolve_coupling(head, None)    # from the head (coupling hash+hex)
    syms = _validate_kernel_symbols(hv)
    leaves = _kernel_v6_leaves(syms, leaf_dim, et_code)   # [klein4_header, *content]
    return genome_append(path, label, leaves, coupling, kernel=True, catalog=catalog)


def _write_body_and_manifest(path, body_bytes, leaf_dim, coupling) -> dict:
    """Commit a spliced body to ``turns.bin`` + re-derive its ``.fai`` manifest — §44/§45.

    The shared write-path for the in-place edits (:func:`genome_remove` /
    :func:`genome_replace`): the genome's chromosomes have already been excised /
    replaced at the BYTE level (no kernel is decoded or re-coupled — biology excises,
    it does not re-synthesize), so all that is left is to commit the new ``body_bytes``
    and rebuild the DERIVED manifest by SCANNING it (§44 — the strand is the SSoT). The
    rebuild (:func:`_rebuild_manifest_from_body`) runs FIRST so a bad splice raises
    before either file is touched; the returned ``data`` dict is byte-for-byte what
    :func:`genome_save` would write for the same body."""
    leaf_dim = int(leaf_dim)
    body_bytes = bytes(body_bytes)
    # §44: rebuild-by-scan validates the splice (whole multiple of leaf_dim, cap-led
    # regions) BEFORE anything is written — a corrupt edit never lands on disk.
    data = _rebuild_manifest_from_body(body_bytes, leaf_dim, coupling)
    coupling_block = bytes.fromhex(data["coupling"]["hex"])
    head = _build_head_data(leaf_dim, coupling_block, data["n_turns"],
                            len(data["chromosomes"]), data["body_sha256"])
    (Path(path) / _BODY_NAME).write_bytes(body_bytes)
    _write_manifest(path, _manifest_record(head))     # v12: HEAD-ONLY on disk
    return data


def genome_remove(path, label, *, coupling=None) -> dict:
    """Excise ONE chromosome from a genome IN PLACE — UPSTREAM §45.

    Biology excises; it does not re-synthesize. Finds the chromosome ``label``'s region
    in the self-describing body (§44 — its CHROM cap + data turns occupy
    ``[byte_offset, byte_offset + byte_len)``), splices THAT byte span out of
    ``turns.bin``, and leaves every OTHER chromosome's coupled body bytes byte-identical
    (no kernel is decoded / re-coupled — the surviving turns are the same bytes, only
    relocated). The derived ``.fai`` manifest is rebuilt by scanning the spliced body
    (§44 — ``body_sha256`` / ``n_turns`` and every survivor's ``byte_offset`` are
    recomputed; the manifest stays an optional cache). Returns the updated manifest
    ``data`` dict.

    The whole on-disk body is re-hashed against the committed ``body_sha256`` BEFORE the
    edit (never splice a corrupt body — a :class:`GenomeBoundingError`). ``coupling`` is
    needed only when ``manifest.json`` is ABSENT (§44 — its length is the leaf width for
    the rebuild-by-scan); with the manifest present it may be omitted. Raises
    ``ValueError`` if ``label`` is not in the genome, or if it is the genome's ONLY
    chromosome (a genome keeps >= 1 chromosome — remove the directory instead).
    """
    path = Path(path)
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    chrom_entries = list(data["chromosomes"])
    by_label = {c["label"]: c for c in chrom_entries}
    if label not in by_label:
        raise ValueError(
            f"genome_remove: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    if len(chrom_entries) == 1:
        raise ValueError(
            f"genome_remove: {label!r} is the genome's only chromosome — a genome "
            f"keeps >= 1 chromosome; remove the genome directory instead"
        )
    one = _resolve_coupling(data, coupling)
    # §49/rc154: native C remove (find the region + splice the span out in place +
    # re-derive the manifest, byte-identical); native is authoritative (no fallback).
    if _native.has_native_genome():
        try:
            _native.genome_remove_c(str(path), label, bytes(_leaf_blocks([one])[0]))
            return _catalog_data(path, one)     # full derived catalog (v12 head-only on disk)
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    entry = by_label[label]
    off, byte_len = int(entry["byte_offset"]), int(entry["byte_len"])
    body = (path / _BODY_NAME).read_bytes()
    _verify_body_integrity(body, data)                   # integrity bound before edit
    new_body = body[:off] + body[off + byte_len:]        # splice the span out in place
    return _write_body_and_manifest(path, new_body, leaf_dim, one)  # rebuild → v4 regions+chain


def genome_replace(path, label, leaves, coupling) -> dict:
    """Replace ONE chromosome's content IN PLACE — UPSTREAM §45.

    Splices the chromosome ``label``'s old byte span out of ``turns.bin`` and a FRESH
    telomere-capped :func:`chromosome` (``leaves`` coupled through ``coupling``, same
    ``label``) IN at the same position — every OTHER chromosome's coupled body bytes
    stay byte-identical (an in-place edit, NOT a whole-genome re-pack). The derived
    manifest is rebuilt by scanning the new body (§44 — the strand is the SSoT). Returns
    the updated manifest ``data`` dict.

    ``coupling`` is REQUIRED here — it both re-couples the new ``leaves`` into the
    chromosome AND supplies the leaf width for the §44 rebuild — and must match the
    genome's ``leaf_dim``. The on-disk body is re-hashed against the committed
    ``body_sha256`` before the edit (a :class:`GenomeBoundingError` on mismatch). Raises
    ``ValueError`` if ``label`` is not in the genome.
    """
    path = Path(path)
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    if len(list(coupling)) != leaf_dim:
        raise ValueError(
            f"genome_replace: coupling dim {len(list(coupling))} != genome leaf_dim "
            f"{leaf_dim}"
        )
    by_label = {c["label"]: c for c in data["chromosomes"]}
    if label not in by_label:
        raise ValueError(
            f"genome_replace: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    # §55/v3: the fresh region is written in the packed on-disk form.
    new_region = b"".join(
        _disk_block(blk, leaf_dim)
        for blk in _leaf_blocks(chromosome(leaves, coupling, label=label))
    )
    # §49/rc154: native C replace (splice old span out + fresh region in at the same
    # position + manifest re-derive, byte-identical); native is authoritative (no
    # fallback).
    if _native.has_native_genome():
        try:
            _native.genome_replace_c(
                str(path), label, new_region, leaf_dim,
                bytes(_leaf_blocks([coupling])[0]))
            return _catalog_data(path, coupling)    # full derived catalog
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    entry = by_label[label]
    off, byte_len = int(entry["byte_offset"]), int(entry["byte_len"])
    body = (path / _BODY_NAME).read_bytes()
    _verify_body_integrity(body, data)                   # integrity bound before edit
    new_body = body[:off] + new_region + body[off + byte_len:]
    return _write_body_and_manifest(path, new_body, leaf_dim, coupling)


# ────────────────────────────────────────────────────────────────────────
# §43 file-management — the chromosome as a single bundleable .chr file.
#
# A .chr is ONE self-contained MPR-attested file (MPR v1) carrying a
# chromosome's fixed-width region (CHROM cap + coupled data turns) + coupling
# (the width the body lacks inline). It composes srmech.amsc.format (the
# MPRRecord + sha256 content-address) — NOT a parallel attestation: tar it, ship
# it, genome_import it self-verifying. The strand stays the SSoT (§44); a .chr
# round-trips byte-identically.
# ────────────────────────────────────────────────────────────────────────


def _chr_data(label, leaf_dim, leaf_count, cap_sha256, coupling_block, region):
    """Assemble the .chr ``data`` block for ONE chromosome region — §43.

    Carries the chromosome's identity (label / leaf_dim / leaf_count / the cap
    hash), coupling (sha256 + hex — so the bundle is re-couplable standalone), and
    the region itself (sha256 + hex — the CHROM cap + coupled turns, the body
    bytes verbatim). The region hex makes the .chr a single self-contained file."""
    return {
        "format_version": GENOME_FORMAT_VERSION,
        "leaf_dim": int(leaf_dim),
        "label": label,
        "leaf_count": int(leaf_count),
        "cap_sha256": cap_sha256,
        "coupling": {"sha256": _sha256_bytes(coupling_block), "hex": coupling_block.hex()},
        "region": {"sha256": _sha256_bytes(bytes(region)), "hex": bytes(region).hex()},
    }


def _chr_record(data) -> _MPRRecord:
    """Wrap a .chr ``data`` block in an MPRRecord (MPR v1) — §43.

    ``attestation.response_sha256`` IS the chromosome region hash
    (``region.sha256``), so :func:`genome_import` re-hashes the region and
    self-verifies. Mirrors :func:`_manifest_record`; the record satisfies
    :func:`srmech.amsc.format.validate_mpr_record`."""
    region_sha = data["region"]["sha256"]
    parser_version = f"srmech {_SRMECH_VERSION}"
    rule_hash = _sha256_bytes(
        f"genome_chromosome/v{GENOME_FORMAT_VERSION}".encode("utf-8")
    )
    descriptor_hash = _sha256_bytes(GENOME_CHR_SCHEMA_ID.encode("utf-8"))
    record = _MPRRecord(
        mpr_version="1.0",
        data=data,
        data_schema_id=GENOME_CHR_SCHEMA_ID,
        attestation={
            "source_doi": "10.0/srmech.genome.chromosome",
            "source_url": "https://srmech.net/genome/chromosome",
            "license": "CC0",
            "retrieved_at": "1970-01-01T00:00:00Z",
            "response_sha256": region_sha,
            "parser_version": parser_version,
            "parser_rule_hash": rule_hash,
            "collector_descriptor_path": "srmech/amsc/genome.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        rendering={
            "human_readable_name": f"srmech chromosome bundle ({data['label']})",
            "cite_as": "srmech genome chromosome bundle (UPSTREAM §43)",
            "purpose": (
                "One self-contained, MPR-attested chromosome: its fixed-width "
                "region (CHROM cap + coupled turns) + coupling, re-importable "
                "self-verifying."
            ),
        },
    )
    _validate_mpr_record(record)
    return record


def _write_mpr_file(path, record) -> None:
    """Serialise an MPRRecord to ``path`` (one JSON object + LF) — byte-stable,
    the same canonical form :func:`_write_manifest` uses for manifest.json."""
    payload = json.loads(record.to_json_line())
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    Path(path).write_text(text + "\n", encoding="utf-8", newline="\n")


def _read_chr(path) -> _MPRRecord:
    """Read + validate a .chr file into its MPRRecord — §43. Raises
    :class:`GenomeBoundingError` if it is not a chromosome bundle (wrong
    data_schema_id) or fails MPR-v1 structure validation."""
    text = Path(path).read_text(encoding="utf-8")
    payload = json.loads(text)
    record = _MPRRecord(
        mpr_version=str(payload.get("mpr_version", "")),
        data=dict(payload.get("data", {})),
        data_schema_id=str(payload.get("data_schema_id", "")),
        attestation=dict(payload.get("attestation", {})),
        rendering=dict(payload.get("rendering", {})),
    )
    _validate_mpr_record(record)
    if record.data_schema_id != GENOME_CHR_SCHEMA_ID:
        raise GenomeBoundingError(
            f"genome_import: {str(path)!r} is not a chromosome bundle "
            f"(data_schema_id {record.data_schema_id!r} != {GENOME_CHR_SCHEMA_ID!r})"
        )
    return record


def genome_export(path, label, out, *, coupling=None) -> dict:
    """Export ONE chromosome as a single self-contained ``.chr`` file — UPSTREAM §43.

    Reads the chromosome ``label``'s fixed-width region (CHROM cap + coupled data
    turns; cap re-hashed against the manifest ``cap_sha256``) and writes it — together
    with ``coupling`` — to ``out`` as ONE MPR-attested record (MPR v1; the
    ``response_sha256`` IS the region hash). So a chromosome is a self-contained,
    content-addressed unit: ``tar`` it, ship it, :func:`genome_import` it
    self-verifying — realising the §43 "chromosome as a bundleable file" goal on top of
    the §44 self-describing strand. Returns the ``.chr`` ``data`` block. §44: pass
    ``coupling=`` to export from a manifest-less source genome (the catalog is rebuilt by
    scanning ``turns.bin``).

    Raises ``ValueError`` if ``label`` is not in the genome.
    """
    path = Path(path)
    data = _catalog_data(path, coupling)
    leaf_dim = int(data["leaf_dim"])
    by_label = {c["label"]: c for c in data["chromosomes"]}
    if label not in by_label:
        raise ValueError(
            f"genome_export: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    # §49: native C export (read the region + build the MPR-attested .chr, byte-
    # identical); Python re-reads it for the returned ``data``. ANY native error falls
    # back to the pure-Python build.
    if _native.has_native_genome():
        try:
            _native.genome_export_c(
                str(path), label, str(out), _coupling_bytes_or_empty(coupling))
            return _read_chr(Path(out)).data
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    entry = by_label[label]
    region = _read_region(path, entry, leaf_dim)            # cap-integrity checked
    one_block = bytes.fromhex(data["coupling"]["hex"])
    chr_data = _chr_data(label, leaf_dim, int(entry["leaf_count"]),
                         entry["cap_sha256"], one_block, region)
    _write_mpr_file(Path(out), _chr_record(chr_data))
    return chr_data


def genome_import(chr_path, dest, *, coupling=None) -> dict:
    """Import a ``.chr`` chromosome bundle into a genome at ``dest`` — UPSTREAM §43.

    Reads the MPR-attested ``.chr`` (:func:`genome_export`'s output), RE-HASHES its
    region and its ``coupling`` and compares them against the bundle's own attestation —
    a mismatch is a :class:`GenomeBoundingError` (self-verifying). Then:

    * if ``dest`` has NO genome yet, the ``.chr`` SEEDS a fresh one (its region becomes
      ``turns.bin`` verbatim, its ``coupling`` the coupling invariant);
    * if ``dest`` already holds a genome, the chromosome is APPENDED byte-for-byte —
      which REQUIRES the same coupling invariant (the dest ``coupling`` must match the
      ``.chr`` ``coupling``) and a fresh ``label``. The manifest is re-derived by scanning
      the grown body (§44 — the strand is the SSoT).

    Returns the dest manifest ``data`` dict. ``coupling=`` is only consulted for a
    manifest-less existing ``dest`` (§44 rebuild width); the bundle carries its own.
    """
    dest = Path(dest)
    # rc154: cheap, caller-facing validation runs in Python BEFORE the native call so a
    # native non-OK status is unambiguously an integrity failure (GenomeBoundingError). A
    # duplicate label is an ordinary usage error (ValueError) — but the native BAD_INPUT
    # status cannot distinguish it from a coupling mismatch — so it is checked here against
    # the dest's chromosomes. A coupling mismatch (integrity) takes PRECEDENCE: the
    # ValueError is only raised when the coupling invariant matches (otherwise we fall
    # through to native, which reports the mismatch as a GenomeBoundingError).
    record = _read_chr(chr_path)
    cdata = record.data
    label = cdata["label"]
    one_block = bytes.fromhex(cdata["coupling"]["hex"])
    body_path = dest / _BODY_NAME
    if body_path.exists():
        one_for_scan = coupling if coupling is not None else _hv_from_block(one_block)
        dest_data = _catalog_data(dest, one_for_scan)
        if (dest_data["coupling"]["sha256"] == cdata["coupling"]["sha256"]
                and any(c["label"] == label for c in dest_data["chromosomes"])):
            raise ValueError(
                f"genome_import: chromosome {label!r} already exists in the dest genome"
            )
    # §49/rc154: native C import is AUTHORITATIVE when present (re-hash the bundle
    # self-verifying, SEED a fresh dest or APPEND byte-for-byte; Python re-reads the dest
    # manifest for the return). A native non-OK status is an integrity bound →
    # GenomeBoundingError (flipped byte / coupling mismatch / leaf_dim mismatch).
    if _native.has_native_genome():
        try:
            dest.mkdir(parents=True, exist_ok=True)   # native SEED save needs the dir
            _native.genome_import_c(
                str(chr_path), str(dest), _coupling_bytes_or_empty(coupling))
            return _catalog_data(dest, coupling)    # full derived catalog
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    # pure-Python alternative (no C present) — full integrity bounds on the already-read
    # bundle, then SEED or APPEND.
    region = bytes.fromhex(cdata["region"]["hex"])
    if (_sha256_bytes(region) != cdata["region"]["sha256"] or
            record.attestation.get("response_sha256") != cdata["region"]["sha256"]):
        raise GenomeBoundingError(
            "genome_import: chromosome region integrity bound failed — the .chr's "
            "region does not hash to its attested response_sha256 (a flipped byte)"
        )
    if _sha256_bytes(one_block) != cdata["coupling"]["sha256"]:
        raise GenomeBoundingError(
            "genome_import: coupling integrity bound failed in the .chr (stored hex "
            "does not hash to coupling.sha256)"
        )
    leaf_dim = int(cdata["leaf_dim"])
    one = _hv_from_block(one_block)
    if not body_path.exists():
        # SEED a fresh genome — the region IS the whole body (byte-for-byte;
        # §55/v3: written VERBATIM, so a legacy v2 .chr region seeds a legacy
        # body — never re-encoded — exactly like the native C seed).
        dest.mkdir(parents=True, exist_ok=True)
        return _write_body_and_manifest(dest, region, leaf_dim, one)
    # APPEND into the existing genome — same coupling invariant + fresh label.
    dest_data = _catalog_data(dest, coupling if coupling is not None else one)
    if int(dest_data["leaf_dim"]) != leaf_dim:
        raise GenomeBoundingError(
            f"genome_import: dest leaf_dim {dest_data['leaf_dim']} != .chr leaf_dim "
            f"{leaf_dim}"
        )
    if dest_data["coupling"]["sha256"] != cdata["coupling"]["sha256"]:
        raise GenomeBoundingError(
            "genome_import: coupling mismatch — the chromosome is coupled to a "
            "different invariant than the dest genome (re-couple before importing)"
        )
    if any(c["label"] == label for c in dest_data["chromosomes"]):
        raise ValueError(
            f"genome_import: chromosome {label!r} already exists in the dest genome"
        )
    dest_body = body_path.read_bytes()
    _verify_body_integrity(dest_body, dest_data)             # bound before grow
    return _write_body_and_manifest(dest, dest_body + region, leaf_dim, one)


def genome_explode(path, out_dir, *, coupling=None) -> list:
    """Explode a packed genome into a directory of loose ``.chr`` files — UPSTREAM §43.

    The packed→loose half of git's object model: a genome's ``turns.bin`` (the
    "packfile") is written out as ONE self-contained, content-addressed ``.chr``
    bundle per chromosome (the "loose objects"), named ``<out_dir>/<label>.chr``.
    Each ``.chr`` is :func:`genome_export`'s output — an MPR-attested, self-verifying
    bundle — so the loose form is inspectable and shippable chromosome-by-chromosome.
    :func:`genome_pack` is the inverse.

    Returns a list of ``{"label", "path", "region_sha256"}`` dicts (in the genome's
    chromosome order). ``coupling=`` explodes from a manifest-less source (§44).
    Raises ``ValueError`` if a chromosome label is not filename-safe (would not make
    a clean ``<label>.chr`` loose object).
    """
    path = Path(path)
    out_dir = Path(out_dir)
    data = _catalog_data(path, coupling)
    out_dir.mkdir(parents=True, exist_ok=True)
    labels = [e["label"] for e in data["chromosomes"]]
    for label in labels:
        if "/" in label or "\\" in label or label in ("", ".", ".."):
            raise ValueError(
                f"genome_explode: chromosome label {label!r} is not filename-safe "
                f"(cannot become a <label>.chr loose object)"
            )
    # §49/rc154: native C explode (one MPR-attested <label>.chr per chromosome, byte-
    # identical); Python re-reads each bundle's region hash for the returned list.
    # Native is authoritative when present (no fallback).
    if _native.has_native_genome():
        try:
            _native.genome_explode_c(
                str(path), str(out_dir), _coupling_bytes_or_empty(coupling))
            return [
                {"label": label, "path": str(out_dir / f"{label}.chr"),
                 "region_sha256":
                     _read_chr(out_dir / f"{label}.chr").data["region"]["sha256"]}
                for label in labels
            ]
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    written = []
    for label in labels:
        chr_path = out_dir / f"{label}.chr"
        cdata = genome_export(path, label, chr_path, coupling=coupling)
        written.append({
            "label": label,
            "path": str(chr_path),
            "region_sha256": cdata["region"]["sha256"],
        })
    return written


def genome_pack(loose_dir, dest, *, coupling=None) -> dict:
    """Pack a directory of loose ``.chr`` files into one packed genome — UPSTREAM §43.

    The loose→packed inverse of :func:`genome_explode` (git ``repack``-like). Every
    ``*.chr`` bundle in ``loose_dir`` is :func:`genome_import`-ed into ``dest`` in
    CANONICAL sorted-label order, so the packed ``turns.bin`` is a well-defined
    function of the chromosome SET — like a content-addressed packfile, insertion
    order is not preserved (a packed genome is canonicalised to sorted-label order).
    The first import SEEDS ``dest`` (when it has no genome yet); the rest APPEND
    byte-for-byte; all the bundles MUST share one coupling invariant (the same
    ``coupling``) — a mismatched ``.chr`` is a :class:`GenomeBoundingError`, and a
    duplicate label is a ``ValueError``.

    A packed genome is byte-identical to its source iff the source was already in
    canonical sorted-label order; otherwise pack re-canonicalises while preserving
    every chromosome's bytes (round-trips by content, verifiable per-chromosome with
    :func:`genome_window`). Returns the dest manifest ``data`` dict. ``coupling=`` is
    only the §44 rebuild width for a manifest-less existing ``dest``.

    Raises ``ValueError`` if ``loose_dir`` holds no ``.chr`` files.
    """
    loose_dir = Path(loose_dir)
    dest = Path(dest)
    chr_files = sorted(loose_dir.glob("*.chr"))
    if not chr_files:
        raise ValueError(f"genome_pack: no .chr files in {str(loose_dir)!r}")
    # Canonical order: sort by the label stored INSIDE each bundle (robust to
    # externally-named .chr files; agrees with filename order for explode output).
    keyed = sorted((_read_chr(cf).data["label"], cf) for cf in chr_files)
    # rc154: cheap, caller-facing validation runs in Python BEFORE the native call. Two
    # bundles sharing a label cannot both pack — a packed genome's labels are unique — so
    # this is an ordinary usage error (ValueError), checked here so a native non-OK status
    # is unambiguously an integrity failure (a mismatched coupling → GenomeBoundingError).
    seen, dups = set(), set()
    for label, _cf in keyed:
        (dups if label in seen else seen).add(label)
    if dups:
        raise ValueError(
            f"genome_pack: duplicate chromosome label(s) {sorted(dups)!r} across the "
            f"loose .chr bundles (a packed genome's chromosome labels must be unique)"
        )
    # §49/rc154: native C pack is AUTHORITATIVE when present (scan *.chr, sort by each
    # bundle's inner label, import each in canonical order, byte-identical). Pack is
    # MULTI-STEP (one import per bundle) so it is NOT atomic — a mismatched bundle would
    # fail AFTER earlier ones were written. So native packs into a TEMP dir and the real
    # ``dest`` is only adopted on full success (a native error leaves ``dest`` pristine
    # and raises a GenomeBoundingError). Only the fresh-``dest`` case routes natively (an
    # existing ``dest`` is an APPEND the temp-pack can't see — that stays the pure path).
    if _native.has_native_genome() and not (dest / _BODY_NAME).exists():
        scratch = Path(tempfile.mkdtemp())
        try:
            _native.genome_pack_c(
                str(loose_dir), str(scratch), _coupling_bytes_or_empty(coupling))
            dest.mkdir(parents=True, exist_ok=True)
            (dest / _BODY_NAME).write_bytes((scratch / _BODY_NAME).read_bytes())
            (dest / _MANIFEST_NAME).write_bytes(
                (scratch / _MANIFEST_NAME).read_bytes())
            return _catalog_data(dest, coupling)    # full derived catalog
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)                                       # real dest untouched
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    # rc115 (#1245 ask (b)) — SINGLE-PASS compaction (pure-Python: no C, or an
    # APPEND into an existing dest). Read every .chr region ONCE in canonical order,
    # concatenate them (after any existing dest body), then write turns.bin + rebuild
    # the manifest ONCE. O(total body) — NOT the old O(N²) of importing each bundle
    # (which re-read + re-hashed the whole growing dest body per bundle).
    body = bytearray()
    one_block = None
    leaf_dim = None
    dest_labels: set = set()
    if (dest / _BODY_NAME).exists():
        # APPEND into an existing dest: seed the concatenation with its body and
        # adopt its coupling invariant + leaf width (genome_import's bounds).
        dest_data = _catalog_data(dest, coupling)
        one_block = bytes.fromhex(dest_data["coupling"]["hex"])
        leaf_dim = int(dest_data["leaf_dim"])
        dest_labels = {c["label"] for c in dest_data["chromosomes"]}
        body.extend((dest / _BODY_NAME).read_bytes())
    for lbl, cf in keyed:
        cdata = _read_chr(cf).data
        region = bytes.fromhex(cdata["region"]["hex"])
        cone = bytes.fromhex(cdata["coupling"]["hex"])
        # self-verify the bundle: region + coupling hash against its own attestation.
        if (_sha256_bytes(region) != cdata["region"]["sha256"] or
                _read_chr(cf).attestation.get("response_sha256")
                != cdata["region"]["sha256"]):
            raise GenomeBoundingError(
                f"genome_pack: chromosome {lbl!r} region integrity bound failed — "
                f"the .chr does not hash to its attested response_sha256"
            )
        if _sha256_bytes(cone) != cdata["coupling"]["sha256"]:
            raise GenomeBoundingError(
                f"genome_pack: chromosome {lbl!r} coupling integrity bound failed"
            )
        if one_block is None:
            one_block, leaf_dim = cone, int(cdata["leaf_dim"])
        elif cone != one_block:
            raise GenomeBoundingError(
                f"genome_pack: chromosome {lbl!r} is coupled to a different coupling "
                f"than the pack (all bundles must share one coupling invariant)"
            )
        elif int(cdata["leaf_dim"]) != leaf_dim:
            raise GenomeBoundingError(
                f"genome_pack: chromosome {lbl!r} leaf_dim {cdata['leaf_dim']} != "
                f"pack leaf_dim {leaf_dim}"
            )
        if lbl in dest_labels:
            raise ValueError(
                f"genome_pack: chromosome {lbl!r} already exists in the dest genome"
            )
        dest_labels.add(lbl)
        body.extend(region)
    dest.mkdir(parents=True, exist_ok=True)
    return _write_body_and_manifest(dest, bytes(body), leaf_dim,
                                    _hv_from_block(one_block))


#: §43 — the AMSC row schema id for a registered chromosome source. Each row is the
#: chromosome's already-attested provenance (region sha256), NOT a re-attestation.
_GENOME_CHR_ROW_SCHEMA_ID = "srmech.genome_chromosome.row.v1"


def _toml_basic(s) -> str:
    """Quote ``s`` as a TOML basic-string value (escape ``\\`` / ``"`` / controls)."""
    out = str(s).replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
    return f'"{out}"'


def _chr_descriptor_toml(label, leaf_dim) -> str:
    """Build the per-chromosome AMSC ``descriptor.toml`` (literature_curated) — §43.

    Composes the existing AMSC descriptor contract (F729): the chromosome's own MPR
    attestation (its ``.chr`` / its ``row.ndjson`` region sha256) IS the provenance;
    this descriptor REGISTERS it, it does not mint a parallel attestation (F730)."""
    name = _toml_basic(
        f"srmech genome chromosome {label} (leaf_dim={int(leaf_dim)}; "
        f"UPSTREAM §43 .chr bundle)"
    )
    return (
        "# Auto-generated by srmech.amsc.genome.genome_register_attested "
        "(UPSTREAM §43).\n"
        "# REGISTERS an already-MPR-attested chromosome .chr bundle with the AMSC\n"
        "# catalog; it does NOT mint a parallel attestation (F730 — the bundle's\n"
        "# own attestation.response_sha256 == the region hash is the provenance).\n"
        "[source]\n"
        f"key = {_toml_basic(label)}\n"
        f"human_readable_name = {name}\n"
        'purpose = "self-contained MPR-attested genome chromosome region bundle '
        'registered as an AMSC attested source"\n'
        'license = "CC0-1.0"\n'
        'homepage = "https://github.com/lemonforest/mlehaptics"\n'
        "\n[fetch]\n"
        'adapter = "literature_curated"\n'
        'ndjson_path = "row.ndjson"\n'
        "\n[parse]\n"
        "require_per_row_source_doi = false\n"
        "\n[schema]\n"
        f"data_schema_id = {_toml_basic(_GENOME_CHR_ROW_SCHEMA_ID)}\n"
        "\n[rendering]\n"
        'cite_as_template = "srmech genome chromosome {schema.row_label} '
        '(region sha256 attested in the .chr bundle); retrieved '
        '{retrieved_at:%Y-%m-%d}."\n'
        'purpose_template = "attested chromosome {schema.row_label} region bundle"\n'
        "\n[attestation]\n"
        "hash_response = true\n"
        'hash_algorithm = "sha256"\n'
        "required_fields = [\n"
        '    "license", "retrieved_at", "response_sha256", "parser_version",\n'
        '    "parser_rule_hash", "collector_descriptor_path",\n'
        '    "collector_descriptor_hash",\n'
        "]\n"
    )


def genome_register_attested(chr_dir, amsc_root, *, source) -> dict:
    """Register a dir of loose ``.chr`` bundles as AMSC attested sources — UPSTREAM §43.

    The §43 bundling↔AMSC compose (F729): for every ``<label>.chr`` in ``chr_dir``
    (a :func:`genome_explode` output), write a per-chromosome
    ``<amsc_root>/<label>/descriptor.toml`` + ``row.ndjson``, then call
    :func:`srmech.amsc.catalog.register_attested_root` so each chromosome appears in
    :func:`srmech.amsc.catalog.list_attested_sources` (one AMSC source per
    chromosome, keyed by its label). The chromosome's OWN MPR attestation — carried
    in its ``.chr`` (``attestation.response_sha256`` == the region hash) and echoed
    into its ``row.ndjson`` — IS the provenance; this surfaces it through the AMSC
    catalog, it does NOT mint a parallel attestation (F730). The ``literature_curated``
    adapter (no live fetch; NDJSON committed directly; per-row provenance already
    present) is the natural fit.

    Returns ``{"ok", "amsc_root", "source", "chromosomes": [{"label", "source_key",
    "descriptor_path", "row_path", "region_sha256"}, ...], "register": {...}}``.
    Raises ``ValueError`` if ``chr_dir`` holds no ``.chr`` files or a chromosome
    label is not a filename-safe AMSC source key."""
    from srmech.amsc.catalog import register_attested_root

    chr_dir = Path(chr_dir)
    amsc_root = Path(amsc_root)
    chr_files = sorted(chr_dir.glob("*.chr"))
    if not chr_files:
        raise ValueError(
            f"genome_register_attested: no .chr files in {str(chr_dir)!r}"
        )
    amsc_root.mkdir(parents=True, exist_ok=True)
    chromosomes = []
    for cf in chr_files:
        record = _read_chr(cf)
        label = record.data["label"]
        if "/" in label or "\\" in label or label in ("", ".", ".."):
            raise ValueError(
                f"genome_register_attested: chromosome label {label!r} is not a "
                f"filename-safe AMSC source key"
            )
        leaf_dim = int(record.data["leaf_dim"])
        region_sha = record.data["region"]["sha256"]
        one_sha = record.data["coupling"]["sha256"]
        src_dir = amsc_root / label
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "descriptor.toml").write_text(
            _chr_descriptor_toml(label, leaf_dim), encoding="utf-8", newline="\n"
        )
        row = {
            "row_label": label,
            "leaf_dim": leaf_dim,
            "region_sha256": region_sha,       # the .chr's existing attestation
            "coupling_sha256": one_sha,
            "chr_filename": cf.name,
            "data_schema_id": record.data_schema_id,
        }
        (src_dir / "row.ndjson").write_text(
            json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8", newline="\n",
        )
        chromosomes.append({
            "label": label,
            "source_key": label,
            "descriptor_path": str(src_dir / "descriptor.toml"),
            "row_path": str(src_dir / "row.ndjson"),
            "region_sha256": region_sha,
        })
    register = register_attested_root(amsc_root, source=str(source))
    return {
        "ok": True,
        "amsc_root": str(amsc_root),
        "source": str(source),
        "chromosomes": chromosomes,
        "register": register,
    }
