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
are the cascade PRIMITIVES the later user-authored class layer binds to (a
class-descriptor TOML declares fields + methods-as-op-refs; srmech's
config-driven loader constructs the class; DSL/CLI/tool_schema become
class-aware — the genome storage object as the seed worked-instance). The
**genome** (multi-kernel, telomere-partitioned strand of chromosomes) assembles
in a subsequent brick.
"""
from __future__ import annotations

from typing import Dict

from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.amsc.hdc import klein4_bind as _klein4_bind
from srmech.amsc.hdc import klein4_random as _klein4_random

__all__ = [
    "encode_shape", "quad_turn", "telomere", "chromosome", "recall",
    "LEAF_CAP", "QUAD", "MOBIUS_CAP",
]

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


def chromosome(leaves, the_one, *, label="chromosome"):
    """Pack one kernel into a telomere-capped strand — a chromosome (F713/F715).

    The kernel's ``leaves`` (each a Klein-4 vector, one tome) become a helix of
    QUAD-TURNS, each coupled through ``the_one`` (the reversible :func:`quad_turn`),
    led by a :func:`telomere` cap derived from ``label``. The returned strand is::

        [telomere(label, dim), quad_turn(leaf0, the_one), quad_turn(leaf1, the_one), ...]

    Recover the kernel with :func:`recall`. The cap delimits and protects the
    chromosome, so many chromosomes pack onto one genome strand (a later brick).
    ``the_one`` is the shared invariant every turn is coupled through.
    """
    dim = len(list(the_one))
    cap = telomere(label, dim=dim)
    return [cap] + [quad_turn(leaf, the_one) for leaf in leaves]


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
