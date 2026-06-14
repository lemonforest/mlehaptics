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
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

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
    "encode_shape", "quad_turn", "telomere", "chromosome", "recall",
    "genes",
    "genome", "partition",
    "genome_save", "genome_load", "genome_catalog", "genome_append",
    "genome_window", "genome_genes",
    "genome_remove", "genome_replace",
    "genome_export", "genome_import",
    "genome_explode", "genome_pack",
    "genome_register_attested",
    "GenomeBoundingError",
    "LEAF_CAP", "QUAD", "MOBIUS_CAP",
    "CHROM_CAP_MARKER", "GENE_CAP_MARKER", "GENE_FRAME_TAG",
]

#: §44 (F733) — INLINE FIXED-WIDTH cap markers. The genome body is a uniformly
#: fixed-width strand of ``leaf_dim``-byte blocks; a block's FIRST BYTE classifies
#: it. A Klein-4 data turn only ever holds sector indices ``{0, 1, 2, 3}`` (``HV``
#: sectors=4), so any first byte ``> 3`` is a CAP, scanned for (never a data turn).
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
    """The cap marker (``CHROM_CAP_MARKER`` / ``GENE_CAP_MARKER``) of a strand
    element, or ``None`` for a Klein-4 data turn (first byte ``0..3``) — the §44
    scan classifier."""
    first = int(hv[0]) if len(hv) else -1
    return first if first in (CHROM_CAP_MARKER, GENE_CAP_MARKER) else None


def _unpack_cap(hv):
    """``(marker, label)`` from a fixed-width cap leaf — the inverse of
    :func:`_pack_cap`; the label is bytes ``[1:]`` up to the first NUL."""
    raw = hv.tobytes()
    return raw[0], raw[1:].split(b"\x00", 1)[0].decode("utf-8")


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


def _gene_cap(gene_label, dim):
    """The intra-chromosome GENE boundary cap — a fixed-width INLINE leaf (§44,
    replaces the §43 TLV ``_gene_header``). ``[GENE_CAP_MARKER] + label, NUL-padded``
    to ``dim``: scanned for (first byte ``> 3``, distinct from the CHROM cap marker
    and from data turns), label recoverable inline. Telomere caps the chromosome,
    the gene-cap caps the gene — nested fixed-width inline framing, no length prefix
    (so no offset sidecar; biology's own wire-format)."""
    return _pack_cap(GENE_CAP_MARKER, gene_label, dim)


def chromosome(leaves=None, the_one=None, *, label="chromosome", genes=None):
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
    """
    if the_one is None:
        raise ValueError("chromosome: the_one is required")
    if (leaves is None) == (genes is None):
        raise ValueError("chromosome: pass exactly one of leaves= or genes=")
    dim = len(list(the_one))
    cap = telomere(label, dim=dim)
    if genes is None:
        return [cap] + [quad_turn(leaf, the_one) for leaf in leaves]
    strand = [cap]
    for gene_label, gene_leaves in genes:
        strand.append(_gene_cap(gene_label, dim))
        strand.extend(quad_turn(leaf, the_one) for leaf in gene_leaves)
    return strand


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
        if kind == GENE_CAP_MARKER:
            if started:
                out.append((cur_label, cur_leaves))
            _marker, cur_label = _unpack_cap(hv)
            cur_leaves = []
            started = True
        elif kind == CHROM_CAP_MARKER:
            continue                            # the chromosome telomere cap — skip
        elif not started:
            continue                            # any leading cap before the first gene
        else:
            cur_leaves.append(quad_turn(hv, the_one))   # reversible uncouple
    if started:
        out.append((cur_label, cur_leaves))
    return out


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
        if kind == CHROM_CAP_MARKER:            # a telomere cap — start a new partition
            _marker, current = _unpack_cap(hv)
            out[current] = []
        elif kind == GENE_CAP_MARKER:           # a gene delimiter — not data; flatten
            continue
        elif current is not None:
            out[current].append(quad_turn(hv, the_one))   # reversible uncouple
    if labels is not None:
        return {label: out[label] for label in labels if label in out}
    return out


# ─────────────────────────────────────────────────────────────────────────────
# UPSTREAM §41 — genome persistence (disk save / load / catalog / append /
# window). The helix grows ON DISK: a genome directory is
#
#   path/manifest.json   an MPRRecord (MPR v1) describing the chromosome set —
#                        the CATALOG (leaf_dim, per-chromosome cap_sha256 /
#                        leaf_count / byte_offset / byte_len, body_sha256). Read
#                        the manifest WITHOUT touching the body (genome_catalog).
#   path/turns.bin       the append-only flat body: every strand element (a cap
#                        or a coupled turn) is a FIXED-WIDTH leaf_dim-byte block
#                        (values 0..3). No length prefixes — chromosome
#                        boundaries live in the manifest as byte_offset/byte_len.
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
GENOME_FORMAT_VERSION = 2

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
    cap (first byte a marker ``> 3``) is a packed ``sectors=256`` cap leaf (matching
    :func:`_pack_cap`, so it reconstructs byte-AND-sectors identical); every other
    block is a Klein-4 data turn (``sectors=QUAD``, bytes ``0..3``). Reading the
    first byte suffices because the marker bytes are out of the Klein-4 range —
    that IS the self-describing-strand property."""
    first = block[0] if block else -1
    sectors = 256 if first in (CHROM_CAP_MARKER, GENE_CAP_MARKER) else QUAD
    return _HV.from_sequence(block, sectors=sectors)


def _block_is_cap(block: bytes) -> bool:
    """True if a ``leaf_dim``-byte block is a CHROM/GENE cap (first byte a marker
    ``> 3``) rather than a Klein-4 data turn — §44's scan predicate over raw bytes."""
    return bool(block) and block[0] in (CHROM_CAP_MARKER, GENE_CAP_MARKER)


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
        if _cap_kind(hv) == CHROM_CAP_MARKER:
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


def _build_manifest_data(leaf_dim, the_one_blocks, chrom_specs, body_bytes):
    """Assemble the manifest ``data`` block — §44's optional DERIVED catalog.

    ``chrom_specs`` is a list of ``(label, cap_sha256, leaf_count, byte_offset,
    byte_len)`` tuples (byte_offset/byte_len index into ``turns.bin``;
    ``leaf_count`` counts DATA turns only, excluding the chromosome's CHROM cap and
    any intra-chromosome GENE caps). ``the_one_blocks`` is the single
    ``leaf_dim``-byte block of the_one.

    §44: this manifest is a derived ``.fai``-style cache — every field is
    rebuildable by scanning the self-describing body (the strand is the SSoT).
    The intra-chromosome gene structure lives INLINE in the body (GENE caps), NOT
    here, so there is no gene-index sidecar."""
    return {
        "format_version": GENOME_FORMAT_VERSION,
        "leaf_dim": int(leaf_dim),
        "n_turns": len(body_bytes) // int(leaf_dim) if leaf_dim else 0,
        "the_one": {
            "sha256": _sha256_bytes(the_one_blocks),
            "hex": the_one_blocks.hex(),
        },
        "body_sha256": _sha256_bytes(body_bytes),
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
    for label, blocks in chroms:
        byte_offset = len(body)
        leaf_blocks = _leaf_blocks(blocks)
        for blk in leaf_blocks:
            if len(blk) != leaf_dim:
                raise ValueError(
                    f"genome_save: leaf block width {len(blk)} != leaf_dim "
                    f"{leaf_dim} (every leaf is a fixed-width block)"
                )
            body.extend(blk)
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
    (path / _BODY_NAME).write_bytes(body_bytes)

    the_one_block = _leaf_blocks([the_one])[0]
    data = _build_manifest_data(leaf_dim, the_one_block, chrom_specs, body_bytes)
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
    if leaf_dim <= 0 or len(body_bytes) % leaf_dim != 0:
        raise GenomeBoundingError(
            f"genome turns.bin length {len(body_bytes)} is not a whole multiple of "
            f"leaf_dim {leaf_dim} — cannot scan the fixed-width strand (is the_one's "
            f"width right?)"
        )
    strand = [
        _hv_from_block(body_bytes[k:k + leaf_dim])
        for k in range(0, len(body_bytes), leaf_dim)
    ]
    chroms = _split_into_chromosomes(strand)          # scans inline CHROM caps
    chrom_specs: List[Tuple[str, str, int, int, int]] = []
    offset = 0
    for label, blocks in chroms:
        leaf_blocks = _leaf_blocks(blocks)
        byte_len = sum(len(b) for b in leaf_blocks)
        cap_sha256 = _sha256_bytes(leaf_blocks[0])
        leaf_count = sum(1 for b in leaf_blocks if not _block_is_cap(b))
        chrom_specs.append((label, cap_sha256, leaf_count, offset, byte_len))
        offset += byte_len
    one = the_one if isinstance(the_one, _HV) else _HV.from_sequence(the_one)
    the_one_block = _leaf_blocks([one])[0]
    return _build_manifest_data(leaf_dim, the_one_block, chrom_specs, bytes(body_bytes))


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
    return _catalog_data(path, the_one)


def _verify_body_hash(body_bytes, expected_sha) -> None:
    """Re-hash the whole body and raise :class:`GenomeBoundingError` on mismatch
    (the whole-genome integrity bound)."""
    got = _sha256_bytes(body_bytes)
    if got != expected_sha:
        raise GenomeBoundingError(
            f"genome body integrity bound failed: turns.bin hashes to {got} but "
            f"the manifest committed body_sha256={expected_sha} (a flipped / "
            f"truncated / re-ordered body byte)"
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
        # Whole-genome streaming read: one fixed-width block at a time, hashing
        # incrementally is not available via sha256_bytes (no streaming API), so
        # we accumulate the body bytes we STREAM (block-by-block, never building
        # an intermediate giant HV/strand object) and verify the whole-body hash.
        strand: List[_HV] = []
        body_acc = bytearray()
        with body_path.open("rb") as f:
            while True:
                block = f.read(leaf_dim)
                if not block:
                    break
                if len(block) != leaf_dim:
                    raise GenomeBoundingError(
                        f"genome body truncated: trailing {len(block)} bytes are "
                        f"not a whole leaf_dim={leaf_dim} block"
                    )
                body_acc.extend(block)
                strand.append(_hv_from_block(block))
        _verify_body_hash(bytes(body_acc), data["body_sha256"])
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
            for k in range(0, len(region), leaf_dim):
                out_strand.append(_hv_from_block(region[k:k + leaf_dim]))
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
    """Reconstruct a region's full HV strand (every block — caps + data turns)."""
    return [
        _hv_from_block(region[k:k + leaf_dim])
        for k in range(0, len(region), leaf_dim)
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
    region = _read_region(path, by_label[label], leaf_dim)
    leaves: List[_HV] = []
    for k in range(0, len(region), leaf_dim):
        block = region[k:k + leaf_dim]
        if _block_is_cap(block):                # skip CHROM lead cap + GENE caps
            continue
        leaves.append(_hv_from_block(block))
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
    if not any(_cap_kind(hv) == GENE_CAP_MARKER for hv in region_strand):
        raise ValueError(
            f"genome_genes: chromosome {label!r} has no inline GENE caps — it is a "
            f"single-kernel chromosome; use genome_window / partition"
        )
    # §44: scan the inline gene structure — genes() skips the leading CHROM cap and
    # splits on the GENE caps, uncoupling each data turn through the_one.
    return genes(region_strand, the_one)


def genome_append(path, label, leaves, the_one) -> dict:
    """Append ONE chromosome to an existing genome at ``path/`` — UPSTREAM §41.
    The helix grows. Returns the updated manifest ``data`` dict.

    Packs ``leaves`` (the new kernel's Klein-4 leaf vectors) into a
    telomere-capped :func:`chromosome` (coupled through ``the_one``), appends its
    fixed-width blocks to the END of ``path/turns.bin`` (append-only — prior
    chromosomes' body bytes are NEVER rewritten), and rewrites the manifest with
    the new chromosome entry + a recomputed ``body_sha256`` / ``n_turns``. Every
    EXISTING chromosome's manifest entry (``cap_sha256`` / ``byte_offset`` /
    ``leaf_count`` / ``byte_len``) stays byte-identical.
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

    body_path = path / _BODY_NAME
    existing_body = body_path.read_bytes()
    # Integrity bound on what we are appending TO (never grow a corrupt body).
    _verify_body_hash(existing_body, data["body_sha256"])

    new_strand = chromosome(leaves, the_one, label=label)
    new_blocks = _leaf_blocks(new_strand)
    for blk in new_blocks:
        if len(blk) != leaf_dim:
            raise ValueError(
                f"genome_append: leaf block width {len(blk)} != leaf_dim "
                f"{leaf_dim}"
            )
    byte_offset = len(existing_body)
    appended = b"".join(new_blocks)

    # Append-only: open in append-binary so prior bytes are untouched.
    with body_path.open("ab") as f:
        f.write(appended)
    new_body = existing_body + appended

    # Existing chromosome specs carry through byte-identically.
    chrom_specs: List[Tuple[str, str, int, int, int]] = [
        (c["label"], c["cap_sha256"], int(c["leaf_count"]),
         int(c["byte_offset"]), int(c["byte_len"]))
        for c in data["chromosomes"]
    ]
    cap_sha256 = _sha256_bytes(new_blocks[0])
    chrom_specs.append(
        (label, cap_sha256, len(new_blocks) - 1, byte_offset, len(appended))
    )

    one_block = bytes.fromhex(data["the_one"]["hex"])
    new_data = _build_manifest_data(leaf_dim, one_block, chrom_specs, new_body)
    record = _manifest_record(new_data)
    _write_manifest(path, record)
    return new_data


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
    entry = by_label[label]
    off, byte_len = int(entry["byte_offset"]), int(entry["byte_len"])
    body = (path / _BODY_NAME).read_bytes()
    _verify_body_hash(body, data["body_sha256"])         # integrity bound before edit
    new_body = body[:off] + body[off + byte_len:]        # splice the span out in place
    one = _resolve_the_one(data, the_one)
    return _write_body_and_manifest(path, new_body, leaf_dim, one)


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
    entry = by_label[label]
    off, byte_len = int(entry["byte_offset"]), int(entry["byte_len"])
    body = (path / _BODY_NAME).read_bytes()
    _verify_body_hash(body, data["body_sha256"])         # integrity bound before edit
    new_region = b"".join(_leaf_blocks(chromosome(leaves, the_one, label=label)))
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
    record = _read_chr(chr_path)
    cdata = record.data
    region = bytes.fromhex(cdata["region"]["hex"])
    if (_sha256_bytes(region) != cdata["region"]["sha256"] or
            record.attestation.get("response_sha256") != cdata["region"]["sha256"]):
        raise GenomeBoundingError(
            "genome_import: chromosome region integrity bound failed — the .chr's "
            "region does not hash to its attested response_sha256 (a flipped byte)"
        )
    one_block = bytes.fromhex(cdata["the_one"]["hex"])
    if _sha256_bytes(one_block) != cdata["the_one"]["sha256"]:
        raise GenomeBoundingError(
            "genome_import: the_one integrity bound failed in the .chr (stored hex "
            "does not hash to the_one.sha256)"
        )
    leaf_dim = int(cdata["leaf_dim"])
    label = cdata["label"]
    one = _hv_from_block(one_block)
    body_path = dest / _BODY_NAME
    if not body_path.exists():
        # SEED a fresh genome — the region IS the whole body (byte-for-byte).
        dest.mkdir(parents=True, exist_ok=True)
        strand = [
            _hv_from_block(region[k:k + leaf_dim])
            for k in range(0, len(region), leaf_dim)
        ]
        return genome_save(strand, dest, one)
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
    _verify_body_hash(dest_body, dest_data["body_sha256"])   # bound before grow
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
    written = []
    for entry in data["chromosomes"]:
        label = entry["label"]
        if "/" in label or "\\" in label or label in ("", ".", ".."):
            raise ValueError(
                f"genome_explode: chromosome label {label!r} is not filename-safe "
                f"(cannot become a <label>.chr loose object)"
            )
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
    result = None
    for _label, cf in keyed:
        result = genome_import(cf, dest, the_one=the_one)
    return result


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
