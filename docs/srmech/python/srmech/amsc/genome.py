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
    "GenomeBoundingError",
    "LEAF_CAP", "QUAD", "MOBIUS_CAP", "GENE_FRAME_TAG",
]

#: Class-B TLV tag marking an intra-chromosome GENE-frame header (F730/S43). A
#: Klein-4 turn/cap only ever holds sector indices ``{0, 1, 2, 3}`` (``HV``
#: sectors=4), so any strand element whose first byte is this tag (``> 3``) is
#: unambiguously a gene header, never a data turn or a telomere cap. ``0x47``
#: = ASCII ``'G'`` (Gene). The cheaper internal delimiter — the telomere stays
#: the chromosome boundary cap, the tlv frame delimits genes inside it.
GENE_FRAME_TAG = 0x47

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


def telomere(label, dim=64):
    """The non-data content-address CAP that delimits a chromosome (F715).

    A telomere is biology's repetitive non-coding chromosome-end cap — here a
    deterministic, content-addressed Klein-4 sentinel derived from ``label``
    (Class A content-address -> Class M Klein-4 carrier). It marks and protects a
    partition boundary and carries no kernel data. Same ``label`` -> same cap (so
    a chromosome is recalled / partitioned by matching its cap), distinct labels
    -> distinct caps. ``dim`` is the Klein-4 vector length — match the turns it
    caps (:func:`chromosome` passes ``len(the_one)`` automatically).
    """
    raw = label.encode("utf-8") if isinstance(label, str) else bytes(label)
    seed = int(_sha256_bytes(raw)[:16], 16)   # content-address -> deterministic seed
    return _klein4_random(dim, seed=seed)


def _gene_header(gene_label):
    """The intra-chromosome GENE delimiter (F730/S43): a tlv-framed header ``HV``.

    ``tlv_pack(GENE_FRAME_TAG, label-bytes)`` (Class-B) carried as a byte ``HV``
    (``sectors=256``). Its first byte is :data:`GENE_FRAME_TAG` (``> 3``), so it
    is distinguishable from any Klein-4 data turn / telomere cap (bytes ``≤ 3``),
    and — unlike the one-way content-address cap — the **label is recoverable**
    verbatim via :func:`tlv_unpack` (that is why a gene is tlv-framed, not capped)."""
    raw = gene_label.encode("utf-8") if isinstance(gene_label, str) else bytes(gene_label)
    return _HV.from_sequence(_tlv_pack(GENE_FRAME_TAG, raw), sectors=256)


def chromosome(leaves=None, the_one=None, *, label="chromosome", genes=None):
    """Pack a kernel — or SEVERAL genes — into a telomere-capped strand (F713/F715/F730).

    **Single kernel (shipped F713/F715 behaviour, unchanged).** Pass ``leaves``
    (each a Klein-4 vector, one tome). They become a helix of QUAD-TURNS, each
    coupled through ``the_one`` (the reversible :func:`quad_turn`), led by a
    :func:`telomere` cap derived from ``label``::

        [telomere(label, dim), quad_turn(leaf0, the_one), quad_turn(leaf1, the_one), ...]

    Recover with :func:`recall`.

    **Several genes (F730/S43).** Pass ``genes=[(gene_label, gene_leaves), …]``
    instead of ``leaves``: each gene's leaves are framed by a tlv :func:`_gene_header`
    (the cheaper internal delimiter), all inside ONE telomere-capped chromosome::

        [telomere(label, dim),
         gene_header('rules'), quad_turn(r0, one), quad_turn(r1, one),
         gene_header('board'), quad_turn(b0, one), ...]

    Recover the ``[(gene_label, gene_leaves), …]`` list with :func:`genes`. Pass
    **exactly one** of ``leaves`` or ``genes``; ``the_one`` is always required
    (the shared invariant every turn is coupled through).
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
        strand.append(_gene_header(gene_label))
        strand.extend(quad_turn(leaf, the_one) for leaf in gene_leaves)
    return strand


def recall(strand, the_one, telomere):
    """Recover the kernel's leaves from a telomere-capped chromosome strand (F713/F715).

    Walk the ``strand``; skip every element equal to the ``telomere`` cap (the
    non-data delimiter) and re-bind ``the_one`` (the reversible :func:`quad_turn`
    again) on each coupled data turn to recover the original leaf. The exact
    inverse of :func:`chromosome`::

        recall(chromosome(leaves, one, label=L), one, telomere(L, len(one))) == leaves

    Matching the cap by value (not by position) is what lets one ``recall`` /
    partition reach into a multi-chromosome genome strand in a later brick.
    """
    cap = list(telomere)
    leaves = []
    for hv in strand:
        if list(hv) == cap:            # the content-address cap — a delimiter, not data
            continue
        leaves.append(quad_turn(hv, the_one))   # reversible uncouple (bind o bind == id)
    return leaves


def genes(strand, the_one):
    """Recover ``[(gene_label, gene_leaves), …]`` from a multi-gene chromosome (F730/S43).

    The exact inverse of ``chromosome(genes=…, the_one)``. Walk the ``strand``:
    a :data:`GENE_FRAME_TAG` header (first byte ``> 3`` — never a Klein-4 turn)
    opens a new gene whose label is read back with :func:`tlv_unpack`; every
    coupled data turn until the next header (or the end) is re-bound through
    ``the_one`` (the reversible :func:`quad_turn`) to recover that gene's leaf.
    Leading element(s) before the first gene header are the chromosome's
    telomere cap (a delimiter, not data) and are skipped — so ``genes`` needs
    only the strand + ``the_one``, no cap argument::

        genes(chromosome(genes=[("a", la), ("b", lb)], one), one) == [("a", la), ("b", lb)]

    Use :func:`genes` (not :func:`recall`) on a multi-gene chromosome; ``recall``
    would treat the gene headers as data turns.
    """
    out = []
    cur_label = None
    cur_leaves = []
    started = False
    for hv in strand:
        first = int(hv[0]) if len(hv) else -1   # Klein-4 turns are bytes <= 3
        if first == GENE_FRAME_TAG:
            if started:
                out.append((cur_label, cur_leaves))
            _tag, value, _next = _tlv_unpack(hv.tobytes())
            cur_label = value.decode("utf-8")
            cur_leaves = []
            started = True
        elif not started:
            continue                            # leading telomere cap — skip the delimiter
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

    **Several genes per chromosome that PERSIST (F732/S43.1).** Pass
    ``chromosomes=[(label, [(gene_label, gene_leaves), …]), …]`` instead of
    ``kernels``: each chromosome's genes are FLATTENED into one telomere-capped
    region, so the body is byte-identical to the single-kernel genome of the
    concatenated leaves — the gene boundaries are NOT stored as data turns / gene
    headers (unlike in-memory :func:`chromosome` ``genes=``). Returns the 2-tuple
    ``(strand, gene_index)`` where ``gene_index = {label: [(gene_label,
    leaf_count), …]}`` records where each gene's leaves sit. Persist BOTH:
    ``genome_save(strand, path, the_one, labels, gene_index=gene_index)`` writes the
    index into the manifest (the body unchanged), and :func:`genome_genes` pages one
    chromosome's genes back. ``the_one`` is always required.
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
    # Multi-gene: flatten each chromosome's genes into one telomere-capped region
    # (no gene-header turns in the body) + a parallel gene_index. The body is
    # byte-identical to genome([(label, concat-of-all-gene-leaves)], the_one); the
    # gene boundaries live ONLY in the manifest (genome_save gene_index=).
    strand = []
    gene_index: Dict[str, List[Tuple[str, int]]] = {}
    for label, genes_list in chromosomes:
        per_gene = [(gl, list(gleaves)) for gl, gleaves in genes_list]
        all_leaves = [leaf for _gl, gleaves in per_gene for leaf in gleaves]
        strand.extend(chromosome(all_leaves, the_one, label=label))
        gene_index[label] = [(str(gl), len(gleaves)) for gl, gleaves in per_gene]
    return strand, gene_index


def partition(strand, the_one, labels):
    """Recover every kernel from a multi-kernel genome strand — the inverse of
    :func:`genome` (F715).

    Walk the ``strand``; each element equal to one of ``labels``' telomere caps
    starts a new chromosome partition, and the coupled turns until the next cap
    are that kernel's leaves (re-bound through ``the_one`` — the reversible
    :func:`quad_turn`). Returns ``{label: leaves}``. ``partition`` knows ALL the
    caps, so (unlike a single-cap :func:`recall`) it does not mistake one
    chromosome's cap for another's data::

        partition(genome({"a": A, "b": B}, one), one, ["a", "b"]) == {"a": A, "b": B}
    """
    dim = len(list(the_one))
    cap_to_label = {tuple(int(x) for x in telomere(label, dim=dim)): label for label in labels}
    out = {}
    current = None
    for hv in strand:
        key = tuple(int(x) for x in hv)
        if key in cap_to_label:                 # a telomere cap — start a new partition
            current = cap_to_label[key]
            out[current] = []
        elif current is not None:
            out[current].append(quad_turn(hv, the_one))   # reversible uncouple
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
#: change). 1 == fixed-width leaf_dim-byte blocks, manifest-described boundaries.
GENOME_FORMAT_VERSION = 1

#: The data_schema_id the genome manifest's MPRRecord carries (resolves to the
#: genome-manifest data shape — format_version / leaf_dim / chromosomes / hashes).
GENOME_MANIFEST_SCHEMA_ID = "srmech://schema/genome_manifest/v1"

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
    """Reconstruct one Klein-4 vector (an :class:`HV`) from a ``leaf_dim``-byte
    block — the numpy-free inverse of :meth:`HV.tobytes` (Klein-4 sectors=4)."""
    return _HV.from_sequence(block, sectors=QUAD)


def _split_into_chromosomes(strand, labels) -> List[Tuple[str, list]]:
    """Walk a flat genome strand and split it into ``[(label, [cap, *turns]), …]``
    by its telomere caps (the on-disk chromosome layout), preserving strand order.

    Uses the SAME cap-matching as :func:`partition` (a block equal to a known
    label's telomere starts a new chromosome). Validates the strand actually
    decomposes against the supplied ``labels`` (no orphan turns before the first
    cap; every label present once)."""
    if not strand:
        raise ValueError("genome persistence: empty strand has no chromosomes")
    leaf_dim = len(list(strand[0]))
    cap_to_label = {
        tuple(int(x) for x in telomere(label, dim=leaf_dim)): label
        for label in labels
    }
    chroms: List[Tuple[str, list]] = []
    current_label: Optional[str] = None
    current_blocks: Optional[list] = None
    for hv in strand:
        key = tuple(int(x) for x in hv)
        if key in cap_to_label:
            if current_label is not None:
                chroms.append((current_label, current_blocks))
            current_label = cap_to_label[key]
            current_blocks = [hv]            # the cap leads the chromosome region
        else:
            if current_label is None:
                raise ValueError(
                    "genome persistence: strand has data turns before its first "
                    "telomere cap — labels do not match the strand"
                )
            current_blocks.append(hv)
    if current_label is not None:
        chroms.append((current_label, current_blocks))
    seen = [lbl for lbl, _ in chroms]
    if sorted(seen) != sorted(set(labels)):
        raise ValueError(
            f"genome persistence: strand chromosomes {seen!r} do not match the "
            f"requested labels {list(labels)!r}"
        )
    return chroms


def _build_manifest_data(leaf_dim, the_one_blocks, chrom_specs, body_bytes,
                         gene_index=None):
    """Assemble the manifest ``data`` block (the §41 catalog payload).

    ``chrom_specs`` is a list of ``(label, cap_sha256, leaf_count, byte_offset,
    byte_len)`` tuples (byte_offset/byte_len index into ``turns.bin``).
    ``the_one_blocks`` is the single ``leaf_dim``-byte block of the_one.

    ``gene_index`` (F732/S43.1, optional) is ``{label: [(gene_label, leaf_count),
    …]}`` — for a multi-gene chromosome it adds an optional ``"genes"`` field
    (``[[gene_label, leaf_count], …]``) to that chromosome's entry, recording the
    intra-chromosome gene boundaries WITHOUT touching the fixed-width body. A
    single-gene chromosome omits the field entirely (the on-disk shape of a
    single-kernel genome is byte-identical to before)."""
    gene_index = gene_index or {}
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
                **(
                    {"genes": [[str(gl), int(n)] for gl, n in gene_index[label]]}
                    if label in gene_index else {}
                ),
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


def genome_save(strand, path, the_one, labels, *, gene_index=None) -> dict:
    """Persist a genome ``strand`` to ``path/`` (a DIRECTORY) — UPSTREAM §41.

    Splits the flat genome ``strand`` into its telomere-delimited chromosomes
    (by ``labels``, the same way :func:`partition` does), writes the fixed-width
    body to ``path/turns.bin`` (every strand element a ``leaf_dim``-byte block,
    cap inline as a leaf), and writes the MPR-attested catalog to
    ``path/manifest.json``. ``the_one`` (the held invariant) is content-addressed
    into the manifest (its hash + hex) so a load can re-anchor without re-deriving
    it. Returns the manifest ``data`` dict.

    ``labels`` are the chromosome labels whose telomere caps partition the strand
    (in any order; the strand's own order is preserved on disk).

    ``gene_index`` (F732/S43.1, optional) is the ``{label: [(gene_label,
    leaf_count), …]}`` returned alongside the strand by ``genome(chromosomes=…)``:
    it records each multi-gene chromosome's intra-chromosome gene boundaries in
    the manifest (an optional ``genes`` field per chromosome) WITHOUT changing the
    fixed-width body — page the genes back with :func:`genome_genes`. Each named
    chromosome's gene leaf-counts must sum to its stored ``leaf_count`` (the body
    turns it actually holds), else a ``ValueError``.
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
                    f"{leaf_dim} (every leaf is a fixed-width Klein-4 vector)"
                )
            body.extend(blk)
        byte_len = len(body) - byte_offset
        cap_block = leaf_blocks[0]                # the telomere cap leads the region
        cap_sha256 = _sha256_bytes(cap_block)
        leaf_count = len(leaf_blocks) - 1         # data turns (excludes the cap)
        chrom_specs.append(
            (label, cap_sha256, leaf_count, byte_offset, byte_len)
        )

    body_bytes = bytes(body)
    (path / _BODY_NAME).write_bytes(body_bytes)

    if gene_index:
        spec_leaf_count = {lbl: int(lc) for (lbl, _c, lc, _o, _l) in chrom_specs}
        for lbl, gidx in gene_index.items():
            if lbl not in spec_leaf_count:
                raise ValueError(
                    f"genome_save: gene_index label {lbl!r} is not a chromosome "
                    f"of this strand ({list(spec_leaf_count)!r})"
                )
            total = sum(int(n) for _gl, n in gidx)
            if total != spec_leaf_count[lbl]:
                raise ValueError(
                    f"genome_save: chromosome {lbl!r} gene leaf-counts sum to "
                    f"{total} but the strand holds {spec_leaf_count[lbl]} data "
                    f"turns (the genes must tile the chromosome exactly)"
                )

    the_one_block = _leaf_blocks([the_one])[0]
    data = _build_manifest_data(
        leaf_dim, the_one_block, chrom_specs, body_bytes, gene_index=gene_index
    )
    record = _manifest_record(data)
    _write_manifest(path, record)
    return data


def genome_catalog(path) -> dict:
    """Read ONLY the manifest catalog of a genome at ``path`` — UPSTREAM §41.

    Returns the manifest ``data`` dict (``leaf_dim`` / ``n_turns`` /
    ``body_sha256`` / per-chromosome ``cap_sha256`` / ``leaf_count`` /
    ``byte_offset`` / ``byte_len`` / ``the_one`` hash+hex). This NEVER opens
    ``turns.bin`` — it is the cheap catalog read (you can enumerate a genome's
    chromosomes, sizes, and integrity hashes without paging in any body bytes).
    """
    return _read_manifest(path)


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


def genome_load(path, *, labels=None):
    """Reconstruct a genome from ``path/`` — UPSTREAM §41. Returns
    ``(strand, the_one, labels)``.

    ``labels=None`` loads the WHOLE genome: streams ``turns.bin`` block-by-block
    (RAM bounded by the active block, not the whole file held as one giant
    object) and re-hashes the streamed body against the manifest's
    ``body_sha256`` — a mismatch is a :class:`GenomeBoundingError`. A subset
    ``labels=[…]`` is a paged read: it seeks to each requested chromosome's
    ``byte_offset`` and reads only its ``byte_len`` bytes (RAM bounded by the
    largest single chromosome), re-hashing that region's cap against
    ``cap_sha256``. The returned strand is byte-for-byte the saved strand for the
    requested chromosomes (in manifest order); ``the_one`` is rebuilt from the
    manifest's stored block (and verified against its stored hash).
    """
    path = Path(path)
    data = _read_manifest(path)
    leaf_dim = int(data["leaf_dim"])
    body_path = path / _BODY_NAME

    # Rebuild the_one from the manifest (verify its own content-address bound).
    one_block = bytes.fromhex(data["the_one"]["hex"])
    if _sha256_bytes(one_block) != data["the_one"]["sha256"]:
        raise GenomeBoundingError(
            "genome the_one integrity bound failed: stored hex does not hash to "
            "the manifest the_one.sha256"
        )
    the_one = _hv_from_block(one_block)

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


def genome_window(path, label):
    """Page in ONLY one chromosome's leaves from ``path/`` — UPSTREAM §41.

    Seeks to the chromosome ``label``'s ``byte_offset`` and reads only its
    ``byte_len`` bytes (RAM bounded by that one chromosome), re-hashing the region
    cap against the manifest's ``cap_sha256`` — a mismatch is a
    :class:`GenomeBoundingError`. Returns the chromosome's stored leaves (the
    coupled data turns, the cap excluded) as a list of Klein-4 vectors, in order
    — the disk-paging counterpart of reaching into one partition of the genome.
    """
    path = Path(path)
    data = _read_manifest(path)
    leaf_dim = int(data["leaf_dim"])
    by_label = {c["label"]: c for c in data["chromosomes"]}
    if label not in by_label:
        raise ValueError(
            f"genome_window: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    entry = by_label[label]
    with (path / _BODY_NAME).open("rb") as f:
        f.seek(int(entry["byte_offset"]))
        region = f.read(int(entry["byte_len"]))
    if len(region) != int(entry["byte_len"]):
        raise GenomeBoundingError(
            f"genome_window {label!r}: region truncated "
            f"({len(region)} of {entry['byte_len']} bytes)"
        )
    cap_block = region[:leaf_dim]
    if _sha256_bytes(cap_block) != entry["cap_sha256"]:
        raise GenomeBoundingError(
            f"genome_window {label!r}: cap integrity bound failed"
        )
    leaves: List[_HV] = []
    for k in range(leaf_dim, len(region), leaf_dim):   # skip the leading cap block
        leaves.append(_hv_from_block(region[k:k + leaf_dim]))
    return leaves


def genome_genes(path, label):
    """Page ONE multi-gene chromosome's genes back from ``path/`` — F732/S43.1.

    The disk counterpart of the in-memory :func:`genes`: reads the manifest's
    per-chromosome gene index (the optional ``genes`` field written by
    :func:`genome_save` with ``gene_index=``), pages in only that chromosome's
    window (:func:`genome_window` — RAM-bounded + cap-integrity-checked),
    uncouples each stored turn through ``the_one`` (rebuilt + hash-verified from
    the manifest), and slices the leaves by the index into ``[(gene_label,
    gene_leaves), …]`` — exactly what ``genes(chromosome(genes=…, one), one)``
    returns in memory. Raises ``ValueError`` if the chromosome carries no gene
    index (it is a single-kernel chromosome — use :func:`genome_window` /
    :func:`partition` for those), and :class:`GenomeBoundingError` if the index
    leaf-counts disagree with the paged turns (manifest/body mismatch)::

        s, gi = genome(chromosomes=[("g", [("rules", R), ("board", B)])], one)
        genome_save(s, path, one, ["g"], gene_index=gi)
        genome_genes(path, "g") == [("rules", R), ("board", B)]
    """
    path = Path(path)
    data = _read_manifest(path)
    by_label = {c["label"]: c for c in data["chromosomes"]}
    if label not in by_label:
        raise ValueError(
            f"genome_genes: label {label!r} not in the genome "
            f"(have {list(by_label)!r})"
        )
    gene_idx = by_label[label].get("genes")
    if gene_idx is None:
        raise ValueError(
            f"genome_genes: chromosome {label!r} carries no gene index — it is a "
            f"single-kernel chromosome; use genome_window / partition"
        )
    # Rebuild the_one from the manifest (verify its own content-address bound).
    one_block = bytes.fromhex(data["the_one"]["hex"])
    if _sha256_bytes(one_block) != data["the_one"]["sha256"]:
        raise GenomeBoundingError(
            "genome the_one integrity bound failed: stored hex does not hash to "
            "the manifest the_one.sha256"
        )
    the_one = _hv_from_block(one_block)
    coupled = genome_window(path, label)               # cap-integrity-checked turns
    leaves = [quad_turn(t, the_one) for t in coupled]  # reversible uncouple
    total = sum(int(n) for _gl, n in gene_idx)
    if total != len(leaves):
        raise GenomeBoundingError(
            f"genome_genes {label!r}: gene index leaf-count {total} != "
            f"{len(leaves)} paged turns (manifest / body disagree)"
        )
    out: List[Tuple[str, list]] = []
    pos = 0
    for gene_label, n in gene_idx:
        n = int(n)
        out.append((str(gene_label), leaves[pos:pos + n]))
        pos += n
    return out


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
    data = _read_manifest(path)
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
