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
           (every turn coupled through the_one — reversible klein4_bind)
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
from srmech.amsc.hdc import klein4_random as _klein4_random
from srmech.amsc.hv import HV as _HV
from srmech.amsc.tlv import tlv_pack as _tlv_pack
from srmech.amsc.tlv import tlv_unpack as _tlv_unpack
from srmech.version import __version__ as _SRMECH_VERSION

__all__ = [
    "encode_shape", "quad_turn", "telomere", "chromosome",
    "recall",
    "genes",
    "genome", "partition",
    "genome_save", "genome_load", "genome_catalog", "genome_append",
    "genome_append_kernel",
    "genome_window", "genome_genes",
    "gene_express_plan", "genome_genes_expressed",
    "genome_remove", "genome_replace",
    "genome_export", "genome_import",
    "genome_explode", "genome_pack",
    "genome_register_attested",
    "kernel_pack", "kernel_unpack",
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
#: (klein4_random of a label-hash — bytes 0..3, NOT scan-recognisable without the
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
#: through ``the_one`` like any content leaf and bit-packs like any data turn on disk
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
    leaves = (n + LEAF_CAP - 1) // LEAF_CAP          # ceil(n / 256), pure integer
    depth = _ceil_log4(leaves)
    shape = "tome" if depth == 0 else "mobius" if depth == 1 else "quad_strand"
    return {"n": n, "shape": shape, "leaves": leaves, "depth": depth, "leaf_cap": LEAF_CAP}


def quad_turn(turn, the_one):
    """Couple one helix turn through ``the_one`` — the genome's turn operation (F713).

    The turn is bound to ``the_one`` (the held invariant) by the **reversible**
    Klein-4 bind (``V4 = (F2)^2`` XOR, so ``quad_turn(quad_turn(t, one), one) ==
    t``): the duality held WITHOUT collapse, numpy-free. ``the_one`` is the shared
    invariant present in every turn's coupling — so a chromosome navigates across
    its turns through ``the_one`` and recovers any turn by re-binding it.

    ``turn`` and ``the_one`` are Klein-4 vectors (e.g. from
    :func:`srmech.amsc.hdc.klein4_random`); returns the coupled turn (a Klein-4
    ``HV``). Class-M (bind) ∘ Class-C (the chirality the Klein-4 sectors carry).

    Each turn sits in the native 4-sector biaxial "+"
    (:func:`srmech.amsc.cascade.parallel_sector_dispatch`, CAP=4); that dispatch
    and the base-4 leaf addressing assemble at the chromosome level. Per the F712
    caveat the 4-way is ONE chirality level, the deeper tree is radix addressing.
    """
    return _klein4_bind(turn, the_one)


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
        KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER) else None


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
    couples through ``the_one`` and bit-packs like any content turn (the store stays
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
    the turns it caps (:func:`chromosome` passes ``len(the_one)`` automatically).

    §44 REPLACES the pre-§43.1 content-address cap (``klein4_random`` of a label
    hash — bytes ``0..3``, NOT scan-recognisable without already knowing the label,
    which forced a label↔cap sidecar). Integrity (the old cap's one-way hash) moves
    to the optional derived manifest, not the body.
    """
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
    :func:`chromosome` passes ``len(the_one)`` automatically). Same ``label`` + same
    ``count`` → same cap. Recover the count from the bare strand with
    :func:`_active_telomere_count`; tick it with :func:`telomere_tick`.
    """
    return _pack_active_telomere(label, count, dim)


def chromosome(leaves=None, the_one=None, *, label="chromosome", genes=None,
               kernel=False, active_count=None):
    """Pack a kernel — or SEVERAL genes — into a telomere-capped strand (F713/F715/F730).

    **Single kernel (shipped F713/F715 behaviour, unchanged).** Pass ``leaves``
    (each a Klein-4 vector, one tome). They become a helix of QUAD-TURNS, each
    coupled through ``the_one`` (the reversible :func:`quad_turn`), led by a
    :func:`telomere` cap derived from ``label``::

        [telomere(label, dim), quad_turn(leaf0, the_one), quad_turn(leaf1, the_one), ...]

    Recover with :func:`recall`.

    **Several genes (F730/S43.1 / §44).** Pass ``genes=[(gene_label, gene_leaves),
    …]`` instead of ``leaves``: each gene is opened by a fixed-width INLINE
    :func:`_gene_cap` (telomere-analog for the gene), all inside ONE telomere-capped
    chromosome — every element a ``leaf_dim``-byte block, the strand SELF-DESCRIBES::

        [telomere(label, dim),
         gene_cap('rules'), quad_turn(r0, one), quad_turn(r1, one),
         gene_cap('board'), quad_turn(b0, one), ...]

    Recover the ``[(gene_label, gene_leaves), …]`` list with :func:`genes`. Pass
    **exactly one** of ``leaves`` or ``genes``; ``the_one`` is always required
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
    if the_one is None:
        raise ValueError("chromosome: the_one is required")
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
    dim = len(list(the_one))
    # §89/v6: a kernel chromosome opens with a KERNEL telomere (0x6B); §127: an
    # active-telomere chromosome opens with an ACTIVE telomere (0x74) carrying its count.
    if active_count is not None:
        cap = _pack_active_telomere(label, active_count, dim)
    elif kernel:
        cap = _kernel_telomere(label, dim=dim)
    else:
        cap = telomere(label, dim=dim)
    if genes is None:
        return [cap] + [quad_turn(leaf, the_one) for leaf in leaves]
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
        strand.extend(quad_turn(leaf, the_one) for leaf in gene_leaves)
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


def recall(strand, the_one, telomere=None):
    """Recover the kernel's leaves from a capped chromosome strand (F713/F715/§44).

    Walk the ``strand``; skip every CAP leaf — CHROM or GENE, recognised by its
    inline marker (first byte ``> 3``), §44 — and re-bind ``the_one`` (the reversible
    :func:`quad_turn` again) on each coupled data turn to recover the original leaf.
    The exact inverse of :func:`chromosome`::

        recall(chromosome(leaves, one, label=L), one) == leaves

    §44: caps are recognised by their inline marker (the strand self-describes), not
    matched by value — so ``recall`` no longer needs the cap handed to it; the
    ``telomere`` parameter is accepted for back-compat and ignored. (Use :func:`genes`
    on a multi-gene chromosome to keep the per-gene split; ``recall`` flattens.)
    """
    leaves = []
    for hv in strand:
        if _cap_kind(hv) is not None:   # a CHROM/GENE cap — a delimiter, not data
            continue
        leaves.append(quad_turn(hv, the_one))   # reversible uncouple (bind o bind == id)
    return leaves


def genes(strand, the_one):
    """Recover ``[(gene_label, gene_leaves), …]`` from a multi-gene chromosome (F730/S43).

    The exact inverse of ``chromosome(genes=…, the_one)``. Walk the ``strand``:
    a :func:`_gene_cap` (first byte :data:`GENE_CAP_MARKER` — never a Klein-4 turn)
    opens a new gene whose label is read back INLINE (:func:`_unpack_cap`, no TLV);
    every coupled data turn until the next gene-cap (or the end) is re-bound through
    ``the_one`` (the reversible :func:`quad_turn`) to recover that gene's leaf. The
    leading CHROM cap (the chromosome telomere) is skipped — so ``genes`` needs only
    the strand + ``the_one``, no cap argument::

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
            cur_leaves.append(quad_turn(hv, the_one))   # reversible uncouple
    if started:
        out.append((cur_label, cur_leaves))
    return out


def gene_express(strand, the_one, cell_state):
    """Cell-state-modulated gene expression — a READ-TIME FILTER (§128 / #728; §130 / #730).

    ``strand`` is a multi-gene chromosome (from ``chromosome(genes=…, the_one)`` /
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
    ``gene_leaves`` are uncoupled through ``the_one`` (the reversible :func:`quad_turn`).

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
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                    THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
            if started and cur_express:
                out.append((cur_label, cur_leaves))
            _marker, cur_label = _unpack_cap(hv)
            cur_leaves = []
            cur_express = _gene_expresses(hv, cell_state)   # §130 dispatch on gate_type
            started = True
        elif kind in (CHROM_CAP_MARKER, KERNEL_HEADER_MARKER,
                      KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER):
            continue                            # the chromosome telomere / a header —
                                                # skip (not gene data)
        elif not started:
            continue                            # any leading cap before the first gene
        else:
            cur_leaves.append(quad_turn(hv, the_one))   # reversible uncouple
    if started and cur_express:
        out.append((cur_label, cur_leaves))
    return out


def gene_express_levels(strand, the_one, cell_state):
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
    ``gene_leaves`` are uncoupled through ``the_one`` (the reversible :func:`quad_turn`).

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
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                    THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER):
            if started and cur_level[0] > 0:            # expressed iff level > 0
                out.append((cur_label, cur_leaves, cur_level))
            _marker, cur_label = _unpack_cap(hv)
            cur_leaves = []
            cur_level = _gene_level(hv, cell_state)     # §132 exact-rational (num, den)
            started = True
        elif kind in (CHROM_CAP_MARKER, KERNEL_HEADER_MARKER,
                      KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER):
            continue                            # the chromosome telomere / a header —
                                                # skip (not gene data)
        elif not started:
            continue                            # any leading cap before the first gene
        else:
            cur_leaves.append(quad_turn(hv, the_one))   # reversible uncouple
    if started and cur_level[0] > 0:
        out.append((cur_label, cur_leaves, cur_level))
    return out


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


def _modulator_recover_native(strand, the_one, labels):
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
    leaf_dim = len(list(the_one))
    try:
        on, off, und, verdict = _native.genome_modulator_recover_c(body, leaf_dim, blob)
    except _native.NativeGenomeError:
        return None
    return {"certain_on": on, "certain_off": off, "undetermined": und,
            "verdict": _MODULATOR_VERDICTS[verdict]}


def _modulator_consistent_native(strand, the_one, labels, candidate):
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
    leaf_dim = len(list(the_one))
    try:
        consistent = _native.genome_modulator_consistent_c(body, leaf_dim, blob, candidate)
    except _native.NativeGenomeError:
        return None
    return "CONSISTENT" if consistent else "INCONSISTENT"


def modulator_recover(strand, the_one, expressed_labels):
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

    ⚠️ A READ — never mutates the strand (the input is byte-identical after). ``the_one``
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
    native = _modulator_recover_native(strand, the_one, labels)
    if native is not None:
        return native
    return _modulator_recover_pure(strand, labels)


def modulator_consistent(strand, the_one, expressed_labels, candidate_cell_state):
    """Forward-CHECK one candidate cell_state — M2, the consistency verdict (§133 / #733).

    Is ``candidate_cell_state`` a cell_state that could have produced ``expressed_labels``?
    Runs the FORWARD :func:`gene_express` on the candidate and compares the produced label
    SET to the observed one::

        set(labels of gene_express(strand, the_one, candidate)) == set(expressed_labels)

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
    native = _modulator_consistent_native(strand, the_one, labels, candidate_cell_state)
    if native is not None:
        return native
    produced = {lab for lab, _leaves in gene_express(strand, the_one, candidate_cell_state)}
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


def _modulator_constraint_native(strand, the_one, labels):
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
    leaf_dim = len(list(the_one))
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


def modulator_constraint(strand, the_one, expressed_labels):
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

    ⚠️ A READ — never mutates the strand (byte-identical after). ``the_one`` is the
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
    native_bytes = _modulator_constraint_native(strand, the_one, labels)
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
    ``modulator_consistent(strand, the_one, expressed_labels, candidate) == "CONSISTENT"``
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


def genome(kernels=None, the_one=None, *, chromosomes=None):
    """Pack many kernels into ONE telomere-partitioned strand — the genome (F715).

    The top-level storage object: each ``(label, leaves)`` kernel becomes a
    telomere-capped :func:`chromosome` (coupled through ``the_one``), and all the
    chromosomes are concatenated into a single strand — the **chromosome set**.
    The per-kernel telomere caps delimit + protect the partitions, so one strand
    holds many kernels (verified in F715: ``astronomy`` / ``geography`` /
    ``music`` on one strand). Recover any kernel — or all of them — with
    :func:`partition`.

    **Single gene per chromosome (F715, unchanged).** Pass ``kernels`` — a mapping
    ``{label: leaves}`` or a sequence of ``(label, leaves)`` pairs (insertion order
    is the strand order). Returns the flat strand (``list`` of Klein-4 vectors) — a
    genome strand IS a strand, just with multiple caps.

    **Several genes per chromosome that PERSIST (F732/S43.1 / §44).** Pass
    ``chromosomes=[(label, [(gene_label, gene_leaves), …]), …]`` instead of
    ``kernels``: each chromosome becomes a telomere-capped region whose genes are
    opened by fixed-width INLINE :func:`_gene_cap` boundaries (§44). Returns ONE
    self-describing strand (NO ``gene_index`` sidecar, no 2-tuple — the gene
    boundaries + labels live INLINE in the strand, recovered by scanning). Persist
    with ``genome_save(strand, path, the_one)`` and page one chromosome's genes back
    with :func:`genome_genes` (which scans the region for gene-caps). ``the_one`` is
    always required.
    """
    if the_one is None:
        raise ValueError("genome: the_one is required")
    if (kernels is None) == (chromosomes is None):
        raise ValueError("genome: pass exactly one of kernels= or chromosomes=")
    if chromosomes is None:
        items = list(kernels.items()) if isinstance(kernels, dict) else list(kernels)
        strand = []
        for label, leaves in items:
            strand.extend(chromosome(leaves, the_one, label=label))
        return strand
    # §44 multi-gene: ONE self-describing strand — each chromosome a telomere-capped
    # region with INLINE fixed-width gene-caps (no gene_index sidecar; the gene
    # boundaries + labels are recovered by scanning the strand).
    strand = []
    for label, genes_list in chromosomes:
        strand.extend(chromosome(the_one=the_one, label=label, genes=genes_list))
    return strand


def partition(strand, the_one, labels=None):
    """Recover every kernel from a multi-kernel genome strand — the inverse of
    :func:`genome` (F715 / §44).

    Walk the ``strand``; each CHROM cap (inline marker :data:`CHROM_CAP_MARKER`,
    §44) starts a new chromosome partition and its label is read back INLINE
    (:func:`_unpack_cap` — no sidecar). The coupled data turns until the next CHROM
    cap are that kernel's leaves (re-bound through ``the_one`` — the reversible
    :func:`quad_turn`); intervening GENE caps are skipped as gene delimiters, so a
    multi-gene chromosome FLATTENS to its concatenated leaves (use :func:`genes` to
    keep the per-gene split). Returns ``{label: leaves}``::

        partition(genome({"a": A, "b": B}, one), one) == {"a": A, "b": B}

    §44: chromosomes are DISCOVERED by scanning inline CHROM caps — ``partition`` no
    longer needs the label set handed to it (the strand self-describes). ``labels``
    is accepted for back-compat: when given, it FILTERS the result to that subset
    (and orders it), so old call-sites that passed the full list still round-trip.
    """
    out = {}
    current = None
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in (CHROM_CAP_MARKER, KERNEL_TELOMERE_MARKER,
                    ACTIVE_TELOMERE_MARKER):
            # a telomere cap (plain / §89 kernel / §127 active) — start a partition.
            # _unpack_cap reads the label (bytes [1:] up to the first NUL) UNIFORMLY —
            # the active telomere's count sits AFTER that NUL, so the label is exact.
            _marker, current = _unpack_cap(hv)
            out[current] = []
        elif kind in (GENE_CAP_MARKER, REGULATORY_GENE_MARKER, BOOLEAN_GENE_MARKER,
                      THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER, KERNEL_HEADER_MARKER):
            continue                            # a gene delimiter (§44 plain / §128
                                                # regulatory / §130 boolean / §131 threshold /
                                                # §132 graded) /
                                                # §60 v5 header —
                                                # not data; flatten past it
        elif current is not None:
            out[current].append(quad_turn(hv, the_one))   # reversible uncouple
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


def _default_the_one(leaf_dim):
    """The deterministic default coupling invariant a header-recorded ``leaf_dim``
    reconstructs — an all-ones Klein-4 vector of width ``leaf_dim`` (sectors=4). So
    :func:`kernel_unpack` can uncouple a :func:`kernel_pack` strand that used the
    default ``the_one`` without the caller re-supplying it."""
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


def kernel_pack(data, *, leaf_dim=LEAF_CAP, label="kernel", the_one=None,
                element_type="klein4"):
    """Pack a flat Klein-4 kernel of ANY dimension into a self-describing strand (§89).

    ``data`` is the flat kernel — a sequence of Klein-4 sector symbols ``{0,1,2,3}``
    (an :class:`HV`, ``list[int]``, ``bytes``, …). It is chunked into ``leaf_dim``-wide
    leaves (the final leaf zero-padded to ``leaf_dim``; the ``encode_shape`` ceil-
    division criterion, generalised to ``leaf_dim``), led by the UNIFORMLY-KLEIN-4 §89
    KERNEL HEADER LEAF that SELF-RECORDS the kernel's TRUE length ``D``, its
    ``element_type`` (``"klein4"`` today — the genome-native 2-bit symbol, so the
    element codec is identity) and its ``leaf_dim``, all coupled through ``the_one``
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
    with :func:`kernel_unpack`. Persist with ``genome_save(strand, path, the_one)``
    and unpack from the directory with ``kernel_unpack(path, the_one)``.

    ``leaf_dim`` defaults to :data:`LEAF_CAP` (256, the tome width); it must be at
    least :data:`_KERNEL_HEADER_KLEIN4_SYMS` (52) so the base-4 header fits one leaf.
    ``the_one`` defaults to the deterministic all-ones invariant
    (:func:`_default_the_one`) that :func:`kernel_unpack` reconstructs from the
    header's ``leaf_dim``; pass a custom ``the_one`` (width ``leaf_dim``) only if you
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
    if the_one is None:
        the_one = _default_the_one(leaf_dim)
    elif len(list(the_one)) != leaf_dim:
        raise ValueError(
            f"kernel_pack: the_one dim {len(list(the_one))} != leaf_dim {leaf_dim}"
        )
    leaves = _kernel_v6_leaves(syms, leaf_dim, et_code)
    # [kernel_telomere, coupled_klein4_header, coupled content turns…]
    return chromosome(leaves, the_one, label=label, kernel=True)


def kernel_unpack(strand_or_path, the_one=None):
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

    ``the_one`` (the coupling invariant) is optional: for a genome PATH with a present
    manifest it is resolved from the manifest cache; otherwise (an in-memory strand, or
    a manifest-less directory) it defaults to the deterministic all-ones invariant
    reconstructed from the leaf width — matching :func:`kernel_pack`'s default. Pass
    ``the_one`` explicitly if you packed with a custom one.
    """
    if isinstance(strand_or_path, (str, Path)):
        strand, the_one, _labels = genome_load(strand_or_path, the_one=the_one)
    else:
        strand = list(strand_or_path)
    # v5 byte-TLV header (marker 0x4B), if any — READ-ONLY back-compat.
    header_v5 = next(
        (hv for hv in strand if _cap_kind(hv) == KERNEL_HEADER_MARKER), None)
    # v6 KERNEL telomere (0x6B) → the first coupled turn is the Klein-4 header LEAF.
    has_kernel_telomere = any(
        _cap_kind(hv) == KERNEL_TELOMERE_MARKER for hv in strand)
    if the_one is None:
        # Reconstruct the default coupling invariant from the leaf width (v5 header's
        # recorded leaf_dim, else the first data turn's width — both == leaf_dim).
        if header_v5 is not None:
            _d, hdr_leaf_dim, _et = _unpack_kernel_header(header_v5)
            the_one = _default_the_one(hdr_leaf_dim)
        else:
            width = next((len(hv) for hv in strand if _cap_kind(hv) is None), 0)
            the_one = _default_the_one(width)
    leaves = recall(strand, the_one)      # skips every cap (incl. the v5 0x4B header
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

    Needs NO ``the_one`` — the count lives in the cap, so the gate reads it from the
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
            "build one with chromosome(leaves, the_one, active_count=N)")
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
GENOME_FORMAT_VERSION = 11

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
# the_one — re-importable self-verifying.
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
    caller-facing ``ValueError`` cases (label absent, the_one width) are
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
        KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER) else QUAD
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
        KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER)


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
        if kind in (CHROM_CAP_MARKER, GENE_CAP_MARKER, REGULATORY_GENE_MARKER,
                    BOOLEAN_GENE_MARKER, THRESHOLD_GENE_MARKER, GRADED_GENE_MARKER,
                    KERNEL_HEADER_MARKER,
                    KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER) or kind <= 3:
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
                             ACTIVE_TELOMERE_MARKER):
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


def _build_manifest_data(leaf_dim, the_one_blocks, chrom_specs, body_bytes,
                         n_turns):
    """Assemble the manifest ``data`` block — §44's optional DERIVED catalog.

    ``chrom_specs`` is a list of ``(label, cap_sha256, leaf_count, byte_offset,
    byte_len)`` tuples (byte_offset/byte_len index into ``turns.bin``;
    ``leaf_count`` counts DATA turns only, excluding the chromosome's CHROM cap and
    any intra-chromosome GENE caps). ``the_one_blocks`` is the single
    ``leaf_dim``-byte block of the_one. ``n_turns`` is the strand BLOCK count
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
    regions = []
    region_hexes = []
    for (_label, _cap, _lc, byte_offset, byte_len) in chrom_specs:
        off, ln = int(byte_offset), int(byte_len)
        rh = _sha256_bytes(bytes(body_bytes[off:off + ln]))
        region_hexes.append(rh)
        regions.append({"byte_offset": off, "byte_len": ln, "sha256": rh})
    return {
        "format_version": GENOME_FORMAT_VERSION,
        "leaf_dim": int(leaf_dim),
        "n_turns": int(n_turns),
        "the_one": {
            "sha256": _sha256_bytes(the_one_blocks),
            "hex": the_one_blocks.hex(),
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
            }
            for (label, cap_sha256, leaf_count, byte_offset, byte_len) in chrom_specs
        ],
    }


def _manifest_record(data) -> _MPRRecord:
    """Wrap a genome manifest ``data`` block in an MPRRecord (MPR v1) — the
    on-disk catalog format. ``attestation.response_sha256`` IS the body hash
    (``body_sha256``); ``parser_version`` is the srmech version string. The
    record satisfies :func:`srmech.amsc.format.validate_mpr_record`."""
    body_sha = data["body_sha256"]
    parser_version = f"srmech {_SRMECH_VERSION}"
    rule_hash = _sha256_bytes(
        f"genome_persistence/v{GENOME_FORMAT_VERSION}".encode("utf-8")
    )
    descriptor_hash = _sha256_bytes(GENOME_MANIFEST_SCHEMA_ID.encode("utf-8"))
    record = _MPRRecord(
        mpr_version="1.0",
        data=data,
        data_schema_id=GENOME_MANIFEST_SCHEMA_ID,
        attestation={
            "source_doi": "10.0/srmech.genome.persistence",
            "source_url": "https://srmech.net/genome/persistence",
            "license": "CC0",
            "retrieved_at": "1970-01-01T00:00:00Z",
            "response_sha256": body_sha,
            "parser_version": parser_version,
            "parser_rule_hash": rule_hash,
            "collector_descriptor_path": "srmech/amsc/genome.py",
            "collector_descriptor_hash": descriptor_hash,
        },
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


def _the_one_block_bytes(the_one) -> bytes:
    """The ``leaf_dim``-byte block for ``the_one`` (the width the body lacks inline) —
    the native ``srmech_genome_*`` calls take it as raw bytes."""
    return bytes(_leaf_blocks([the_one])[0])


def _the_one_bytes_or_empty(the_one) -> bytes:
    """``the_one`` as bytes, or ``b""`` when it is ``None`` — for the native genome
    reads (``load`` / ``window`` / ``catalog`` / ``explode`` / ``pack`` / ``import``)
    where ``the_one`` is only consulted as the §44 rebuild width (a present manifest
    needs none, so an empty ``the_one`` maps to the C ``NULL,0``)."""
    return b"" if the_one is None else _the_one_block_bytes(the_one)


def genome_save(strand, path, the_one, labels=None) -> dict:
    """Persist a genome ``strand`` to ``path/`` (a DIRECTORY) — UPSTREAM §41 / §44.

    Splits the flat genome ``strand`` into its chromosomes by SCANNING its inline
    CHROM caps (§44 — the strand self-describes; labels are recovered inline),
    writes the self-describing fixed-width body to ``path/turns.bin`` (every strand
    element a ``leaf_dim``-byte block — a CHROM/GENE cap or a coupled data turn),
    and writes the DERIVED catalog to ``path/manifest.json``. ``the_one`` (the held
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

    leaf_dim = len(list(the_one))
    chroms = _split_into_chromosomes(strand, labels)

    body = bytearray()
    chrom_specs: List[Tuple[str, str, int, int, int]] = []
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
        chrom_specs.append(
            (label, cap_sha256, leaf_count, byte_offset, byte_len)
        )

    body_bytes = bytes(body)
    the_one_block = _leaf_blocks([the_one])[0]

    # §49/rc154: native C save writes turns.bin + manifest.json byte-identically
    # for a genome of ANY size (the C carves its scratch from the caller arena —
    # no compiled-in cap). Native is authoritative when present; the pure-Python
    # path below is the complete alternative ONLY when there is no C (no fallback).
    if _native.has_native_genome():
        try:
            _native.genome_save_c(str(path), body_bytes, leaf_dim, bytes(the_one_block))
            return _read_manifest(path)
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)

    (path / _BODY_NAME).write_bytes(body_bytes)
    data = _build_manifest_data(leaf_dim, the_one_block, chrom_specs, body_bytes,
                                n_turns)
    record = _manifest_record(data)
    _write_manifest(path, record)
    return data


def _rebuild_manifest_from_body(body_bytes, leaf_dim, the_one):
    """Reconstruct the manifest ``data`` block by SCANNING ``turns.bin`` alone — §44.

    The strand is the SSoT: every manifest field (the per-chromosome ``label`` /
    ``byte_offset`` / ``byte_len`` / ``cap_sha256`` / ``leaf_count``, the
    ``body_sha256`` and ``n_turns``) is derivable by walking the self-describing
    fixed-width body. ``leaf_dim`` — the block width — is the one thing the body does
    NOT carry inline; it comes from ``the_one`` (``len(the_one)``), the genome's
    identity key. The returned dict is byte-for-byte what :func:`genome_save` wrote
    (same scan + spec accumulation), so a regenerated manifest is identical — that is
    what makes ``manifest.json`` a true optional ``.fai``-style cache (drop it, ship
    ``turns.bin`` alone, rebuild on load)."""
    leaf_dim = int(leaf_dim)
    if leaf_dim <= 0:
        raise GenomeBoundingError(
            f"genome rebuild-by-scan: leaf_dim {leaf_dim} is not a positive block "
            f"width (is the_one's width right?)"
        )
    if not body_bytes:
        raise ValueError("genome persistence: empty strand has no chromosomes")
    # §55/v3: walk the RAW on-disk bytes (v2 | v3 | mixed) — offsets, hashes and
    # counts come from the stored blocks VERBATIM (a legacy byte-per-symbol turn
    # is never re-encoded, so the rebuilt manifest matches the body as written).
    chrom_specs: List[Tuple[str, str, int, int, int]] = []
    cur: Optional[list] = None      # [label, cap_sha256, leaf_count, offset, length]
    n_turns = 0
    offset = 0
    for raw, decoded in _walk_region_blocks(
            bytes(body_bytes), leaf_dim, context="genome rebuild-by-scan"):
        n_turns += 1
        if decoded[0] in (CHROM_CAP_MARKER, KERNEL_TELOMERE_MARKER,
                          ACTIVE_TELOMERE_MARKER):
            if cur is not None:
                chrom_specs.append(tuple(cur))
            # the label is bytes [1:] up to the first NUL — UNIFORM across all telomere
            # kinds (the §127 active telomere's count sits AFTER that NUL).
            label = decoded[1:].split(b"\x00", 1)[0].decode("utf-8")
            cur = [label, _sha256_bytes(raw), 0, offset, 0]
        elif cur is None:
            raise ValueError(
                "genome persistence: strand has turns before its first CHROM "
                "cap — not a well-formed §44 genome strand"
            )
        elif (decoded[0] != GENE_CAP_MARKER
              and decoded[0] != REGULATORY_GENE_MARKER
              and decoded[0] != BOOLEAN_GENE_MARKER
              and decoded[0] != THRESHOLD_GENE_MARKER
              and decoded[0] != GRADED_GENE_MARKER
              and decoded[0] != KERNEL_HEADER_MARKER):
            cur[2] += 1                       # a data turn (packed or legacy); a GENE
                                              # cap (§44 plain / §128 regulatory / §130
                                              # boolean / §131 threshold / §132 graded) or
                                              # §60 v5 header is not a turn
                                              # (the §89 v6 Klein-4 header IS a coupled turn)
        cur[4] += len(raw)
        offset += len(raw)
    if cur is not None:
        chrom_specs.append(tuple(cur))
    one = the_one if isinstance(the_one, _HV) else _HV.from_sequence(the_one)
    the_one_block = _leaf_blocks([one])[0]
    return _build_manifest_data(leaf_dim, the_one_block, chrom_specs,
                                bytes(body_bytes), n_turns)


def _catalog_data(path, the_one=None) -> dict:
    """The manifest ``data`` for a genome at ``path`` — §44's "manifest is an
    optional ``.fai`` cache; the strand is the SSoT".

    Fast path: when ``manifest.json`` exists, read it (cheap — never opens
    ``turns.bin``). Fallback: when it is ABSENT, REBUILD the catalog by scanning
    ``turns.bin`` (:func:`_rebuild_manifest_from_body`) — which needs ``the_one``
    (its length IS ``leaf_dim``, the block width the body does not carry inline), so
    a missing-manifest load with no ``the_one=`` raises a helpful
    :class:`GenomeBoundingError` rather than a bare ``FileNotFoundError``. So a
    genome can be shipped as ``turns.bin`` ALONE (tar one file) and loaded with its
    ``the_one`` — no sidecar required."""
    path = Path(path)
    if (path / _MANIFEST_NAME).exists():
        return _read_manifest(path)
    if the_one is None:
        raise GenomeBoundingError(
            f"genome at {str(path)!r} has no {_MANIFEST_NAME} and no the_one= was "
            f"given: §44 makes the manifest an optional .fai cache, but rebuilding it "
            f"by scanning {_BODY_NAME} needs the leaf width (= len(the_one)) — pass "
            f"the genome's the_one="
        )
    body_bytes = (path / _BODY_NAME).read_bytes()
    return _rebuild_manifest_from_body(body_bytes, len(list(the_one)), the_one)


def genome_catalog(path, *, the_one=None) -> dict:
    """Read the catalog of a genome at ``path`` — UPSTREAM §41 / §44.

    Returns the manifest ``data`` dict (``leaf_dim`` / ``n_turns`` /
    ``body_sha256`` / per-chromosome ``cap_sha256`` / ``leaf_count`` /
    ``byte_offset`` / ``byte_len`` / ``the_one`` hash+hex). When ``manifest.json``
    is present this is the cheap catalog read — it NEVER opens ``turns.bin`` (you can
    enumerate a genome's chromosomes, sizes, and integrity hashes without paging in
    any body bytes). §44: when the manifest is ABSENT, the catalog is REBUILT by
    scanning the self-describing body (the strand is the SSoT, the manifest an
    optional ``.fai`` cache); that rebuild needs ``the_one=`` (its length is the leaf
    width) and reads ``turns.bin`` once.
    """
    # §49: native C catalog (parse manifest.json, or §44 rebuild-by-scan) → the same
    # canonical JSON the pure path produces; native is authoritative when present (no fallback).
    if _native.has_native_genome():
        try:
            text = _native.genome_catalog_c(
                str(Path(path)), _the_one_bytes_or_empty(the_one))
            return json.loads(text)["data"]
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    return _catalog_data(path, the_one)


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


def _resolve_the_one(data, override=None):
    """Recover ``the_one`` for a load — §44's "manifest cache + load-param fallback".

    Prefer a caller-supplied ``override`` (an :class:`HV` / sequence — for when the
    manifest cache is absent or a different anchor is held); otherwise rebuild it
    from the manifest's stored block and verify its content-address bound (a
    mismatch is a :class:`GenomeBoundingError`)."""
    if override is not None:
        return override if isinstance(override, _HV) else _HV.from_sequence(override)
    one_block = bytes.fromhex(data["the_one"]["hex"])
    if _sha256_bytes(one_block) != data["the_one"]["sha256"]:
        raise GenomeBoundingError(
            "genome the_one integrity bound failed: stored hex does not hash to "
            "the manifest the_one.sha256"
        )
    return _hv_from_block(one_block)


def genome_load(path, *, labels=None, the_one=None):
    """Reconstruct a genome from ``path/`` — UPSTREAM §41 / §44. Returns
    ``(strand, the_one, labels)``.

    ``labels=None`` loads the WHOLE genome: streams ``turns.bin`` block-by-block
    (RAM bounded by the active block, not the whole file held as one giant
    object) and re-hashes the streamed body against the manifest's
    ``body_sha256`` — a mismatch is a :class:`GenomeBoundingError`. A subset
    ``labels=[…]`` is a paged read: it seeks to each requested chromosome's
    ``byte_offset`` and reads only its ``byte_len`` bytes (RAM bounded by the
    largest single chromosome), re-hashing that region's cap against
    ``cap_sha256``. The returned strand is byte-for-byte the saved strand for the
    requested chromosomes (in manifest order). ``the_one`` is rebuilt from the
    manifest's stored block (and verified against its stored hash) unless a
    ``the_one=`` override is supplied (§44 — the manifest is an optional cache). When
    ``manifest.json`` is ABSENT the catalog is reconstructed by scanning
    ``turns.bin`` (§44 — the strand is the SSoT); that rebuild REQUIRES ``the_one=``
    (its length is the leaf width), so you can load a tar of ``turns.bin`` alone.
    """
    path = Path(path)
    data = _catalog_data(path, the_one)
    leaf_dim = int(data["leaf_dim"])
    body_path = path / _BODY_NAME

    # §44: the_one from the manifest cache (verify its content-address bound) or
    # the caller-supplied override.
    the_one = _resolve_the_one(data, the_one)

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
                    str(path), bytes(_leaf_blocks([the_one])[0]),
                    body_path.stat().st_size)
                # §55/v3: decode the verified body with the dual-format walker
                # (v2 byte-per-symbol | v3 bit-packed | mixed).
                strand = [
                    _hv_from_block(decoded)
                    for _raw, decoded in _walk_region_blocks(
                        body, leaf_dim, context="genome_load")
                ]
                return strand, the_one, all_labels
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
                            KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER) \
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
        return strand, the_one, all_labels

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
    return out_strand, the_one, [c["label"] for c in ordered]


def _read_region(path, entry, leaf_dim) -> bytes:
    """Page in ONE chromosome's region bytes (seek + bounded read + cap-hash
    check). Shared by :func:`genome_window` / :func:`genome_genes` — RAM is bounded
    by the single chromosome; the leading CHROM cap is re-hashed against the
    manifest's ``cap_sha256`` (a mismatch is a :class:`GenomeBoundingError`)."""
    with (path / _BODY_NAME).open("rb") as f:
        f.seek(int(entry["byte_offset"]))
        region = f.read(int(entry["byte_len"]))
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


def _region_strand(region, leaf_dim) -> List["_HV"]:
    """Reconstruct a region's full HV strand (every block — caps + data turns).
    §55/v3: decoded with the dual-format walker (v2 | v3 | mixed blocks)."""
    return [
        _hv_from_block(decoded)
        for _raw, decoded in _walk_region_blocks(
            region, leaf_dim, context="genome region")
    ]


def genome_window(path, label, *, the_one=None):
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
    pass ``the_one=`` (its length is the leaf width) for that manifest-less path.
    """
    path = Path(path)
    data = _catalog_data(path, the_one)
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
                str(path), label, _the_one_bytes_or_empty(the_one),
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


def genome_genes(path, label, *, the_one=None):
    """Page ONE multi-gene chromosome's genes back from ``path/`` — F732/S43.1 / §44.

    The disk counterpart of the in-memory :func:`genes`: pages in only that
    chromosome's region (RAM-bounded + cap-integrity-checked), then SCANS it for the
    inline GENE caps (§44 — no gene-index sidecar; the gene boundaries + labels live
    in the body) and re-binds ``the_one`` (rebuilt + hash-verified from the manifest
    cache, or a ``the_one=`` override) to recover ``[(gene_label, gene_leaves), …]``
    — exactly what ``genes(chromosome(genes=…, one), one)`` returns in memory.
    Raises ``ValueError`` if the chromosome has NO inline GENE caps (it is a
    single-kernel chromosome — use :func:`genome_window` / :func:`partition`)::

        s = genome(chromosomes=[("g", [("rules", R), ("board", B)])], one)
        genome_save(s, path, one)
        genome_genes(path, "g") == [("rules", R), ("board", B)]

    §44: when ``manifest.json`` is ABSENT the offsets are reconstructed by scanning
    ``turns.bin`` (the strand is the SSoT) — ``the_one=`` is required there (and is
    needed anyway to uncouple the genes).
    """
    path = Path(path)
    data = _catalog_data(path, the_one)
    leaf_dim = int(data["leaf_dim"])
    by_label = {c["label"]: c for c in data["chromosomes"]}
    if label not in by_label:
        raise ValueError(
            f"genome_genes: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    the_one = _resolve_the_one(data, the_one)
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
    # through the_one (use gene_express() to also apply the regulatory-mask filter).
    return genes(region_strand, the_one)


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
    """Open a genome body (``turns.bin``) READ-ONLY — the single seam the §134
    demand-load plan + partial-load reader page their bytes through, so a caller can
    MEASURE bytes-touched (the bounded-I/O proof). Returns an open binary file the
    caller ``with``-closes; NEVER writes (the ops are reads — the file is byte-identical
    after)."""
    return open(str(body_path), "rb")


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
    ``(label, byte_offset, byte_len)`` to ``plan`` iff the gene's cap EXPRESSES under
    ``cell_state`` (the SAME §128/§130/§131 decision :func:`gene_express` uses; the gate
    reads only the cap, never a decoded leaf)."""
    lbl, cap_hv, gstart = pending
    if _gene_expresses(cap_hv, cell_state):
        plan.append((lbl, gstart, end_pos - gstart))


def gene_express_plan(strand_or_path, the_one, cell_state):
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
      bounded RAM AND bounded I/O (bytes-touched ≪ full body). A region with no head gene
      cap (a single-kernel chromosome, ``byte_len < 2·leaf_dim``) is not a gated community
      and is skipped. This is the siona community=chromosome layout: the per-chromosome
      head gate IS the community gate. Mixed E1/E2/E4/E3 gate-types across chromosomes are
      the delivered gates — the plan gates by the inline mask regardless of kind.
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
    assert GENOME_FORMAT_VERSION == 11      # a READ of existing caps/manifest; no bump
    if isinstance(strand_or_path, (str, Path)) or hasattr(strand_or_path, "__fspath__"):
        return _gene_express_plan_path(Path(strand_or_path), the_one, cell_state)
    return _gene_express_plan_strand(strand_or_path, the_one, cell_state)


def _gene_express_plan_path(path, the_one, cell_state):
    """PATH variant (b): the DEMAND-LOAD plan — read ONLY each region's head gate cap via
    the manifest ``byte_offset`` (a seek); NEVER the region body (bounded I/O)."""
    if _native.has_native_genome():
        try:
            return _native.genome_gene_express_plan_c(
                str(path), cell_state, _the_one_bytes_or_empty(the_one))
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    data = _catalog_data(path, the_one)         # the manifest read — never opens turns.bin
    leaf_dim = int(data["leaf_dim"])
    plan = []
    with _open_body_ro(path / _BODY_NAME) as f:
        for c in data["chromosomes"]:
            off, ln = int(c["byte_offset"]), int(c["byte_len"])
            if ln < 2 * leaf_dim:               # no head GENE cap → not a gated community
                continue
            f.seek(off + leaf_dim)              # skip the CHROM cap → read ONLY the gate cap
            gate_block = f.read(leaf_dim)
            if (len(gate_block) < leaf_dim
                    or gate_block[0] not in _GENE_MARKERS):
                continue                        # the head block is not a gene cap
            if _gene_expresses(_hv_from_block(gate_block), cell_state):
                plan.append((c["label"], off, ln))
    return plan


def _gene_express_plan_strand(strand, the_one, cell_state):
    """STRAND variant (a): the in-memory skeleton-scan — walk the strand's blocks
    computing their ON-DISK byte spans, gate each gene by its cap, and delimit each
    EXPRESSED gene's byte-range. Never decodes a data-turn payload (seeks past it)."""
    leaf_dim = len(list(the_one))
    turn_width = 1 + _packed_payload_len(leaf_dim)   # §55/v3 on-disk packed-turn width
    plan = []
    pos = 0
    pending = None                              # (label, cap_hv, gene_byte_start)
    for hv in strand:
        kind = _cap_kind(hv)
        if kind in _GENE_MARKERS:
            if pending is not None:
                _plan_close_gene(plan, pending, pos, cell_state)
            _marker, lbl = _unpack_cap(hv)
            pending = (lbl, hv, pos)            # the gene starts at its cap's byte offset
            pos += leaf_dim
        elif kind in (CHROM_CAP_MARKER, KERNEL_HEADER_MARKER,
                      KERNEL_TELOMERE_MARKER, ACTIVE_TELOMERE_MARKER):
            if pending is not None:             # a chromosome boundary closes the gene
                _plan_close_gene(plan, pending, pos, cell_state)
                pending = None
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


def genome_genes_expressed(path, the_one, cell_state):
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
    assert GENOME_FORMAT_VERSION == 11      # a READ of existing caps/manifest; no bump
    path = Path(path)
    plan = _gene_express_plan_path(path, the_one, cell_state)   # the expressed communities
    data = _catalog_data(path, the_one)
    leaf_dim = int(data["leaf_dim"])
    the_one_hv = _resolve_the_one(data, the_one)
    by_label = {c["label"]: c for c in data["chromosomes"]}
    out = []
    with _open_body_ro(path / _BODY_NAME) as f:
        for (chrom_label, _off, _ln) in plan:
            region = _plan_read_region(f, by_label[chrom_label], leaf_dim)
            region_strand = _region_strand(region, leaf_dim)
            for gene in gene_express(region_strand, the_one_hv, cell_state):
                out.append(gene)
    return out


def genome_append(path, label, leaves, the_one, *, kernel=False) -> dict:
    """Append ONE chromosome to an existing genome at ``path/`` — UPSTREAM §41 /
    §56 (rc115 #1245 ask (b)). The helix grows in O(1) amortised. Returns the
    updated manifest ``data`` dict.

    Packs ``leaves`` (the new kernel's Klein-4 leaf vectors) into a
    telomere-capped :func:`chromosome` (coupled through ``the_one``) and
    TAIL-EXTENDS ``path/turns.bin`` with its fixed-width blocks — append-only,
    prior body bytes are NEVER read, rewritten, or re-hashed. The manifest is
    updated by APPENDING one chromosome entry + one region entry and extending the
    ``body_sha256`` REGION CHAIN in O(1) from its prior head (rc115 #1245(b)) — no
    whole-body re-hash, no whole-body re-scan. Every EXISTING chromosome / region
    entry stays byte-identical; ``n_turns`` grows by the appended block count.

    §56: the per-append cost is bounded by the NEW chromosome's own encoding +
    the manifest rewrite (O(n_chromosomes) small JSON), NOT by the genome's total
    size — so N appends are O(N) total, not O(N²) (F833 super-linear wall closed).
    Appending to a legacy v2/v3 genome (no ``regions`` array) migrates it to v4 by
    a one-time rebuild-by-scan of the grown body; subsequent appends are O(1).

    §89/rc126: ``kernel=True`` opens the appended chromosome with a KERNEL telomere
    (``0x6B``) instead of a plain CHROM cap — used by :func:`genome_append_kernel`,
    where ``leaves[0]`` is the uniformly-Klein-4 §89 header. Because that header is a
    100 %-Klein-4 leaf, it couples + bit-packs on the SAME O(1) append path as any
    content turn (klein4_bind never sees a byte ``> 3``).
    """
    path = Path(path)
    # §44: the_one (required here anyway) supplies the leaf width, so an append
    # works against a manifest-less genome too — the catalog is rebuilt by scanning.
    data = _catalog_data(path, the_one)
    leaf_dim = int(data["leaf_dim"])
    if len(list(the_one)) != leaf_dim:
        raise ValueError(
            f"genome_append: the_one dim {len(list(the_one))} != genome leaf_dim "
            f"{leaf_dim}"
        )
    existing_labels = [c["label"] for c in data["chromosomes"]]
    if label in existing_labels:
        raise ValueError(
            f"genome_append: chromosome {label!r} already exists in the genome"
        )

    new_strand = chromosome(leaves, the_one, label=label, kernel=kernel)
    new_blocks = _leaf_blocks(new_strand)
    # §55/v3: the appended region is written in the packed on-disk form (caps
    # verbatim, data turns bit-packed) — _disk_block validates each width. An
    # append to a v2 genome yields a MIXED body, which the walker reads as-is.
    appended = b"".join(_disk_block(blk, leaf_dim) for blk in new_blocks)

    # §49/§56: native C append is AUTHORITATIVE when present — it tail-extends
    # turns.bin + updates the manifest in O(1) (no whole-body rewrite / re-hash);
    # native is authoritative when present (no fallback).
    if _native.has_native_genome():
        try:
            _native.genome_append_c(
                str(path), label, appended, leaf_dim,
                bytes(_leaf_blocks([the_one])[0]))
            return _read_manifest(path)
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)

    body_path = path / _BODY_NAME
    # §56: byte_offset is the CURRENT body size (a cheap stat) — we never read the
    # prior body. Tail-extend append-only so prior bytes are untouched.
    byte_offset = body_path.stat().st_size
    with body_path.open("ab") as f:
        f.write(appended)

    old_regions = data.get("regions")
    if old_regions is None:
        # Legacy v2/v3 genome (no region partition / whole-body body_sha256): a
        # one-time migration to v4 by rebuilding-by-scan of the grown body (the
        # only path that must touch the whole body — subsequent appends are O(1)).
        grown = body_path.read_bytes()
        new_data = _rebuild_manifest_from_body(grown, leaf_dim, the_one)
        _write_manifest(path, _manifest_record(new_data))
        return new_data

    # v4 O(1) append: extend the chromosome / region lists + the chain head only —
    # the existing entries carry through by REFERENCE (byte-identical), and the new
    # region's digest folds onto the prior body_sha256 chain in O(1).
    cap_sha256 = _sha256_bytes(new_blocks[0])
    region_sha256 = _sha256_bytes(appended)
    new_chrom = {
        "label": label,
        "cap_sha256": cap_sha256,
        "leaf_count": len(new_blocks) - 1,
        "byte_offset": byte_offset,
        "byte_len": len(appended),
    }
    new_region = {
        "byte_offset": byte_offset,
        "byte_len": len(appended),
        "sha256": region_sha256,
    }
    new_data = {
        "format_version": GENOME_FORMAT_VERSION,
        "leaf_dim": leaf_dim,
        "n_turns": int(data["n_turns"]) + len(new_blocks),
        "the_one": dict(data["the_one"]),
        "body_sha256": _chain_step(data["body_sha256"], region_sha256),
        "regions": list(old_regions) + [new_region],
        "chromosomes": list(data["chromosomes"]) + [new_chrom],
    }
    _write_manifest(path, _manifest_record(new_data))
    return new_data


def genome_append_kernel(path, label, hv, *, element_type="klein4",
                         the_one=None) -> dict:
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

    ``the_one`` (the coupling invariant) is optional when ``path`` has a manifest (it
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
    data = _catalog_data(path, the_one)           # manifest cache, or §44 rebuild-by-scan
    leaf_dim = int(data["leaf_dim"])
    if leaf_dim < _KERNEL_HEADER_KLEIN4_SYMS:
        raise ValueError(
            f"genome_append_kernel: genome leaf_dim {leaf_dim} < "
            f"{_KERNEL_HEADER_KLEIN4_SYMS} — the §89 kernel header does not fit one leaf"
        )
    if the_one is None:
        the_one = _resolve_the_one(data, None)    # from the manifest cache
    syms = _validate_kernel_symbols(hv)
    leaves = _kernel_v6_leaves(syms, leaf_dim, et_code)   # [klein4_header, *content]
    return genome_append(path, label, leaves, the_one, kernel=True)


def _write_body_and_manifest(path, body_bytes, leaf_dim, the_one) -> dict:
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
    data = _rebuild_manifest_from_body(body_bytes, leaf_dim, the_one)
    (Path(path) / _BODY_NAME).write_bytes(body_bytes)
    _write_manifest(path, _manifest_record(data))
    return data


def genome_remove(path, label, *, the_one=None) -> dict:
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
    edit (never splice a corrupt body — a :class:`GenomeBoundingError`). ``the_one`` is
    needed only when ``manifest.json`` is ABSENT (§44 — its length is the leaf width for
    the rebuild-by-scan); with the manifest present it may be omitted. Raises
    ``ValueError`` if ``label`` is not in the genome, or if it is the genome's ONLY
    chromosome (a genome keeps >= 1 chromosome — remove the directory instead).
    """
    path = Path(path)
    data = _catalog_data(path, the_one)
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
    one = _resolve_the_one(data, the_one)
    # §49/rc154: native C remove (find the region + splice the span out in place +
    # re-derive the manifest, byte-identical); native is authoritative (no fallback).
    if _native.has_native_genome():
        try:
            _native.genome_remove_c(str(path), label, bytes(_leaf_blocks([one])[0]))
            return _read_manifest(path)
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    entry = by_label[label]
    off, byte_len = int(entry["byte_offset"]), int(entry["byte_len"])
    body = (path / _BODY_NAME).read_bytes()
    _verify_body_integrity(body, data)                   # integrity bound before edit
    new_body = body[:off] + body[off + byte_len:]        # splice the span out in place
    return _write_body_and_manifest(path, new_body, leaf_dim, one)  # rebuild → v4 regions+chain


def genome_replace(path, label, leaves, the_one) -> dict:
    """Replace ONE chromosome's content IN PLACE — UPSTREAM §45.

    Splices the chromosome ``label``'s old byte span out of ``turns.bin`` and a FRESH
    telomere-capped :func:`chromosome` (``leaves`` coupled through ``the_one``, same
    ``label``) IN at the same position — every OTHER chromosome's coupled body bytes
    stay byte-identical (an in-place edit, NOT a whole-genome re-pack). The derived
    manifest is rebuilt by scanning the new body (§44 — the strand is the SSoT). Returns
    the updated manifest ``data`` dict.

    ``the_one`` is REQUIRED here — it both re-couples the new ``leaves`` into the
    chromosome AND supplies the leaf width for the §44 rebuild — and must match the
    genome's ``leaf_dim``. The on-disk body is re-hashed against the committed
    ``body_sha256`` before the edit (a :class:`GenomeBoundingError` on mismatch). Raises
    ``ValueError`` if ``label`` is not in the genome.
    """
    path = Path(path)
    data = _catalog_data(path, the_one)
    leaf_dim = int(data["leaf_dim"])
    if len(list(the_one)) != leaf_dim:
        raise ValueError(
            f"genome_replace: the_one dim {len(list(the_one))} != genome leaf_dim "
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
        for blk in _leaf_blocks(chromosome(leaves, the_one, label=label))
    )
    # §49/rc154: native C replace (splice old span out + fresh region in at the same
    # position + manifest re-derive, byte-identical); native is authoritative (no
    # fallback).
    if _native.has_native_genome():
        try:
            _native.genome_replace_c(
                str(path), label, new_region, leaf_dim,
                bytes(_leaf_blocks([the_one])[0]))
            return _read_manifest(path)
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    entry = by_label[label]
    off, byte_len = int(entry["byte_offset"]), int(entry["byte_len"])
    body = (path / _BODY_NAME).read_bytes()
    _verify_body_integrity(body, data)                   # integrity bound before edit
    new_body = body[:off] + new_region + body[off + byte_len:]
    return _write_body_and_manifest(path, new_body, leaf_dim, the_one)


# ────────────────────────────────────────────────────────────────────────
# §43 file-management — the chromosome as a single bundleable .chr file.
#
# A .chr is ONE self-contained MPR-attested file (MPR v1) carrying a
# chromosome's fixed-width region (CHROM cap + coupled data turns) + the_one
# (the width the body lacks inline). It composes srmech.amsc.format (the
# MPRRecord + sha256 content-address) — NOT a parallel attestation: tar it, ship
# it, genome_import it self-verifying. The strand stays the SSoT (§44); a .chr
# round-trips byte-identically.
# ────────────────────────────────────────────────────────────────────────


def _chr_data(label, leaf_dim, leaf_count, cap_sha256, the_one_block, region):
    """Assemble the .chr ``data`` block for ONE chromosome region — §43.

    Carries the chromosome's identity (label / leaf_dim / leaf_count / the cap
    hash), the_one (sha256 + hex — so the bundle is re-couplable standalone), and
    the region itself (sha256 + hex — the CHROM cap + coupled turns, the body
    bytes verbatim). The region hex makes the .chr a single self-contained file."""
    return {
        "format_version": GENOME_FORMAT_VERSION,
        "leaf_dim": int(leaf_dim),
        "label": label,
        "leaf_count": int(leaf_count),
        "cap_sha256": cap_sha256,
        "the_one": {"sha256": _sha256_bytes(the_one_block), "hex": the_one_block.hex()},
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
                "region (CHROM cap + coupled turns) + the_one, re-importable "
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


def genome_export(path, label, out, *, the_one=None) -> dict:
    """Export ONE chromosome as a single self-contained ``.chr`` file — UPSTREAM §43.

    Reads the chromosome ``label``'s fixed-width region (CHROM cap + coupled data
    turns; cap re-hashed against the manifest ``cap_sha256``) and writes it — together
    with ``the_one`` — to ``out`` as ONE MPR-attested record (MPR v1; the
    ``response_sha256`` IS the region hash). So a chromosome is a self-contained,
    content-addressed unit: ``tar`` it, ship it, :func:`genome_import` it
    self-verifying — realising the §43 "chromosome as a bundleable file" goal on top of
    the §44 self-describing strand. Returns the ``.chr`` ``data`` block. §44: pass
    ``the_one=`` to export from a manifest-less source genome (the catalog is rebuilt by
    scanning ``turns.bin``).

    Raises ``ValueError`` if ``label`` is not in the genome.
    """
    path = Path(path)
    data = _catalog_data(path, the_one)
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
                str(path), label, str(out), _the_one_bytes_or_empty(the_one))
            return _read_chr(Path(out)).data
        except _native.NativeGenomeError as exc:
            _raise_native_genome(exc)
    entry = by_label[label]
    region = _read_region(path, entry, leaf_dim)            # cap-integrity checked
    one_block = bytes.fromhex(data["the_one"]["hex"])
    chr_data = _chr_data(label, leaf_dim, int(entry["leaf_count"]),
                         entry["cap_sha256"], one_block, region)
    _write_mpr_file(Path(out), _chr_record(chr_data))
    return chr_data


def genome_import(chr_path, dest, *, the_one=None) -> dict:
    """Import a ``.chr`` chromosome bundle into a genome at ``dest`` — UPSTREAM §43.

    Reads the MPR-attested ``.chr`` (:func:`genome_export`'s output), RE-HASHES its
    region and its ``the_one`` and compares them against the bundle's own attestation —
    a mismatch is a :class:`GenomeBoundingError` (self-verifying). Then:

    * if ``dest`` has NO genome yet, the ``.chr`` SEEDS a fresh one (its region becomes
      ``turns.bin`` verbatim, its ``the_one`` the coupling invariant);
    * if ``dest`` already holds a genome, the chromosome is APPENDED byte-for-byte —
      which REQUIRES the same coupling invariant (the dest ``the_one`` must match the
      ``.chr`` ``the_one``) and a fresh ``label``. The manifest is re-derived by scanning
      the grown body (§44 — the strand is the SSoT).

    Returns the dest manifest ``data`` dict. ``the_one=`` is only consulted for a
    manifest-less existing ``dest`` (§44 rebuild width); the bundle carries its own.
    """
    dest = Path(dest)
    # rc154: cheap, caller-facing validation runs in Python BEFORE the native call so a
    # native non-OK status is unambiguously an integrity failure (GenomeBoundingError). A
    # duplicate label is an ordinary usage error (ValueError) — but the native BAD_INPUT
    # status cannot distinguish it from a the_one mismatch — so it is checked here against
    # the dest's chromosomes. A the_one mismatch (integrity) takes PRECEDENCE: the
    # ValueError is only raised when the coupling invariant matches (otherwise we fall
    # through to native, which reports the mismatch as a GenomeBoundingError).
    record = _read_chr(chr_path)
    cdata = record.data
    label = cdata["label"]
    one_block = bytes.fromhex(cdata["the_one"]["hex"])
    body_path = dest / _BODY_NAME
    if body_path.exists():
        one_for_scan = the_one if the_one is not None else _hv_from_block(one_block)
        dest_data = _catalog_data(dest, one_for_scan)
        if (dest_data["the_one"]["sha256"] == cdata["the_one"]["sha256"]
                and any(c["label"] == label for c in dest_data["chromosomes"])):
            raise ValueError(
                f"genome_import: chromosome {label!r} already exists in the dest genome"
            )
    # §49/rc154: native C import is AUTHORITATIVE when present (re-hash the bundle
    # self-verifying, SEED a fresh dest or APPEND byte-for-byte; Python re-reads the dest
    # manifest for the return). A native non-OK status is an integrity bound →
    # GenomeBoundingError (flipped byte / the_one mismatch / leaf_dim mismatch).
    if _native.has_native_genome():
        try:
            dest.mkdir(parents=True, exist_ok=True)   # native SEED save needs the dir
            _native.genome_import_c(
                str(chr_path), str(dest), _the_one_bytes_or_empty(the_one))
            return _read_manifest(dest)
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
    if _sha256_bytes(one_block) != cdata["the_one"]["sha256"]:
        raise GenomeBoundingError(
            "genome_import: the_one integrity bound failed in the .chr (stored hex "
            "does not hash to the_one.sha256)"
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
    dest_data = _catalog_data(dest, the_one if the_one is not None else one)
    if int(dest_data["leaf_dim"]) != leaf_dim:
        raise GenomeBoundingError(
            f"genome_import: dest leaf_dim {dest_data['leaf_dim']} != .chr leaf_dim "
            f"{leaf_dim}"
        )
    if dest_data["the_one"]["sha256"] != cdata["the_one"]["sha256"]:
        raise GenomeBoundingError(
            "genome_import: the_one mismatch — the chromosome is coupled to a "
            "different invariant than the dest genome (re-couple before importing)"
        )
    if any(c["label"] == label for c in dest_data["chromosomes"]):
        raise ValueError(
            f"genome_import: chromosome {label!r} already exists in the dest genome"
        )
    dest_body = body_path.read_bytes()
    _verify_body_integrity(dest_body, dest_data)             # bound before grow
    return _write_body_and_manifest(dest, dest_body + region, leaf_dim, one)


def genome_explode(path, out_dir, *, the_one=None) -> list:
    """Explode a packed genome into a directory of loose ``.chr`` files — UPSTREAM §43.

    The packed→loose half of git's object model: a genome's ``turns.bin`` (the
    "packfile") is written out as ONE self-contained, content-addressed ``.chr``
    bundle per chromosome (the "loose objects"), named ``<out_dir>/<label>.chr``.
    Each ``.chr`` is :func:`genome_export`'s output — an MPR-attested, self-verifying
    bundle — so the loose form is inspectable and shippable chromosome-by-chromosome.
    :func:`genome_pack` is the inverse.

    Returns a list of ``{"label", "path", "region_sha256"}`` dicts (in the genome's
    chromosome order). ``the_one=`` explodes from a manifest-less source (§44).
    Raises ``ValueError`` if a chromosome label is not filename-safe (would not make
    a clean ``<label>.chr`` loose object).
    """
    path = Path(path)
    out_dir = Path(out_dir)
    data = _catalog_data(path, the_one)
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
                str(path), str(out_dir), _the_one_bytes_or_empty(the_one))
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
        cdata = genome_export(path, label, chr_path, the_one=the_one)
        written.append({
            "label": label,
            "path": str(chr_path),
            "region_sha256": cdata["region"]["sha256"],
        })
    return written


def genome_pack(loose_dir, dest, *, the_one=None) -> dict:
    """Pack a directory of loose ``.chr`` files into one packed genome — UPSTREAM §43.

    The loose→packed inverse of :func:`genome_explode` (git ``repack``-like). Every
    ``*.chr`` bundle in ``loose_dir`` is :func:`genome_import`-ed into ``dest`` in
    CANONICAL sorted-label order, so the packed ``turns.bin`` is a well-defined
    function of the chromosome SET — like a content-addressed packfile, insertion
    order is not preserved (a packed genome is canonicalised to sorted-label order).
    The first import SEEDS ``dest`` (when it has no genome yet); the rest APPEND
    byte-for-byte; all the bundles MUST share one coupling invariant (the same
    ``the_one``) — a mismatched ``.chr`` is a :class:`GenomeBoundingError`, and a
    duplicate label is a ``ValueError``.

    A packed genome is byte-identical to its source iff the source was already in
    canonical sorted-label order; otherwise pack re-canonicalises while preserving
    every chromosome's bytes (round-trips by content, verifiable per-chromosome with
    :func:`genome_window`). Returns the dest manifest ``data`` dict. ``the_one=`` is
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
    # is unambiguously an integrity failure (a mismatched the_one → GenomeBoundingError).
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
                str(loose_dir), str(scratch), _the_one_bytes_or_empty(the_one))
            dest.mkdir(parents=True, exist_ok=True)
            (dest / _BODY_NAME).write_bytes((scratch / _BODY_NAME).read_bytes())
            (dest / _MANIFEST_NAME).write_bytes(
                (scratch / _MANIFEST_NAME).read_bytes())
            return _read_manifest(dest)
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
        dest_data = _catalog_data(dest, the_one)
        one_block = bytes.fromhex(dest_data["the_one"]["hex"])
        leaf_dim = int(dest_data["leaf_dim"])
        dest_labels = {c["label"] for c in dest_data["chromosomes"]}
        body.extend((dest / _BODY_NAME).read_bytes())
    for lbl, cf in keyed:
        cdata = _read_chr(cf).data
        region = bytes.fromhex(cdata["region"]["hex"])
        cone = bytes.fromhex(cdata["the_one"]["hex"])
        # self-verify the bundle: region + the_one hash against its own attestation.
        if (_sha256_bytes(region) != cdata["region"]["sha256"] or
                _read_chr(cf).attestation.get("response_sha256")
                != cdata["region"]["sha256"]):
            raise GenomeBoundingError(
                f"genome_pack: chromosome {lbl!r} region integrity bound failed — "
                f"the .chr does not hash to its attested response_sha256"
            )
        if _sha256_bytes(cone) != cdata["the_one"]["sha256"]:
            raise GenomeBoundingError(
                f"genome_pack: chromosome {lbl!r} the_one integrity bound failed"
            )
        if one_block is None:
            one_block, leaf_dim = cone, int(cdata["leaf_dim"])
        elif cone != one_block:
            raise GenomeBoundingError(
                f"genome_pack: chromosome {lbl!r} is coupled to a different the_one "
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
        one_sha = record.data["the_one"]["sha256"]
        src_dir = amsc_root / label
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "descriptor.toml").write_text(
            _chr_descriptor_toml(label, leaf_dim), encoding="utf-8", newline="\n"
        )
        row = {
            "row_label": label,
            "leaf_dim": leaf_dim,
            "region_sha256": region_sha,       # the .chr's existing attestation
            "the_one_sha256": one_sha,
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
