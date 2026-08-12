"""Finite-group / finite-loop censuses on a Cayley table (rc427, `#T1130`).

Two ops:

* :func:`conjugacy_census` — Class **E** (orbit catalog) then **D** (pattern)
  then **N** (exact-ℚ rate).  The commuting-pair count, the conjugacy-class
  count, the commuting probability as an exact rational, and — the reason the
  op exists — an **associativity guard** in front of all of it.
* :func:`dihedral_group` — Class **I** (cyclic) with a Class-**K** pin-slot
  reflection.  The carrier the censuses need and could not otherwise reach.

WHY THE GUARD IS THE OP
=======================
"Number of conjugacy classes" is only well defined when conjugation is well
defined, and on a NON-associative loop it is not: ``(g·x)·g⁻¹`` and
``g·(x·g⁻¹)`` are different maps, so the orbit count depends on a bracketing
nobody declared.  Worse, the group **class equation** — ``|{(a,b) : ab = ba}|
= k(G)·|G|`` — is a theorem about GROUPS and simply false on a loop, yet an op
that reports ``k`` and lets a caller multiply by ``|G|`` gives a wrong answer
with no error signal.  Measured on the shipped unit loops, left bracketing::

    carrier   k(G)·|G|  (what the group identity predicts)   actual commuting pairs
    M16        144                                            88
    M32        544                                           184

— silently wrong by 56 and by 360.  This op reports both numbers and the
``class_equation_agrees`` flag between them, so the disagreement is data
rather than a trap.  That flag IS the non-group detector.

numpy-free; no ``abs()``; exact ℚ via :class:`srmech.math.q.Q`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..amsc.format import sha256_bytes
from ..math.q import Q
from .composites import cyclic_mod_add

__all__ = ["conjugacy_census", "dihedral_group"]


def _coerce_table(name: str, cayley_table: Sequence[Sequence[int]]) -> List[List[int]]:
    """Validate an ``n x n`` Cayley table of element indices."""
    rows = [list(r) for r in cayley_table]
    n = len(rows)
    if n == 0:
        raise ValueError(f"{name}: cayley_table must be non-empty")
    for i, row in enumerate(rows):
        if len(row) != n:
            raise ValueError(
                f"{name}: cayley_table must be square; row {i} has "
                f"{len(row)} cells, expected {n}")
        for j, v in enumerate(row):
            if not isinstance(v, int) or isinstance(v, bool):
                raise TypeError(
                    f"{name}: cayley_table[{i}][{j}] must be int; "
                    f"got {type(v).__name__}")
            if not 0 <= v < n:
                raise ValueError(
                    f"{name}: cayley_table[{i}][{j}] = {v} outside [0, {n})")
    return rows


def _identity(tbl: List[List[int]]) -> Optional[int]:
    """The two-sided identity index, or ``None`` if the table has none."""
    n = len(tbl)
    for e in range(n):
        if all(tbl[e][x] == x and tbl[x][e] == x for x in range(n)):
            return e
    return None


def _inverses(tbl: List[List[int]], e: int) -> Optional[List[int]]:
    """Two-sided inverses ``inv[x]`` against identity ``e``, or ``None`` when
    any element lacks one (left and right inverse disagreeing counts as
    lacking — a quasigroup can have both and they need not coincide)."""
    n = len(tbl)
    inv: List[int] = []
    for x in range(n):
        found = [y for y in range(n) if tbl[x][y] == e and tbl[y][x] == e]
        if len(found) != 1:
            return None
        inv.append(found[0])
    return inv


def _orbits(images: List[List[int]], n: int) -> List[List[int]]:
    """Orbit partition of ``range(n)`` under the maps ``images[g]``,
    as a sorted list of sorted blocks."""
    label = list(range(n))

    def root(x: int) -> int:
        while label[x] != x:
            label[x] = label[label[x]]
            x = label[x]
        return x

    for g in range(n):
        for x in range(n):
            a, b = root(x), root(images[g][x])
            if a != b:
                label[b] = a
    blocks: Dict[int, List[int]] = {}
    for x in range(n):
        blocks.setdefault(root(x), []).append(x)
    return sorted(sorted(v) for v in blocks.values())


def _partition_bytes(blocks: List[List[int]]) -> bytes:
    return "\n".join(",".join(str(x) for x in b) for b in blocks).encode("utf-8")


def conjugacy_census(cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """Commuting pairs, conjugacy classes and the commuting probability of a
    finite magma given by its Cayley table — **guarded by associativity**.

    Args:
        cayley_table: the ``n x n`` table; ``cayley_table[i][j]`` is the index
            of the product of elements ``i`` and ``j``.  A Cayley table, not a
            callable: a callable cannot cross the JSON-RPC boundary (the
            shipped contract publishes JSON-schema ``null`` for
            ``host_callable``, so over the wire the only legal value is
            absence), and these operands ARE the semantics.
            :func:`srmech.cascade.unit_loop` and :func:`dihedral_group` both
            hand back exactly this shape.

    Returns:
        A dict with

        * ``order`` — ``n``.
        * ``is_associative`` / ``has_identity`` / ``has_inverses`` /
          ``is_group`` — the guard.  ``is_group`` is all three together.
        * ``commuting_pairs`` — ``|{(a, b) : ab = ba}|``, counted, never
          inferred from ``k``.
        * ``commuting_probability`` — ``commuting_pairs / n²`` as an exact
          :class:`srmech.math.q.Q`, plus ``commuting_probability_str``.
        * ``k_classes`` — the number of conjugacy classes under LEFT
          bracketing ``x -> (g·x)·g⁻¹``.  ``None`` when the table has no
          two-sided inverses.
        * ``k_classes_right`` — the same under ``x -> g·(x·g⁻¹)``, and
          ``bracketing_agrees``, which compares the two **PARTITIONS** and not
          their two counts.  On an associative table they coincide by
          definition; on a loop they need not, and the ambiguity is reported
          rather than resolved by fiat.
        * ``class_equation_pairs`` — ``k_classes · n``: what the GROUP class
          equation predicts ``commuting_pairs`` to be.
        * ``class_equation_agrees`` — whether that prediction is the measured
          count.  **This is the non-group detector.**  It fires on the
          octonion unit loop M16 (predicted 144, actual 88) and on M32
          (predicted 544, actual 184).
        * ``class_partition`` — the LEFT-bracketing classes as sorted index
          blocks, and ``class_partition_sha256``, its Class-A content
          address.  Reported as a partition, not only a count: a count of
          classes cannot distinguish two different partitions of the same
          size, and this round exists because exactly that substitution was
          made elsewhere.
        * ``gustafson_5_8`` — whether ``commuting_probability <= 5/8``, and
          ``gustafson_applies`` (true only when ``is_group``).  The 5/8 bound
          is **DERIVED-AND-MEASURED here, not cited**: the arXiv preprint it
          is usually attributed to contains no such bound, so no attestation
          is claimed for it.

    Note:
        ``n³`` associativity check and ``n²`` commuting scan; exact integers
        and exact ℚ throughout, no ``abs()``, no float.
    """
    tbl = _coerce_table("conjugacy_census", cayley_table)
    n = len(tbl)

    is_associative = all(
        tbl[tbl[a][b]][c] == tbl[a][tbl[b][c]]
        for a in range(n) for b in range(n) for c in range(n))
    e = _identity(tbl)
    inv = None if e is None else _inverses(tbl, e)

    commuting_pairs = sum(1 for a in range(n) for b in range(n)
                          if tbl[a][b] == tbl[b][a])
    probability = Q(commuting_pairs, n * n)

    k_left: Optional[int] = None
    k_right: Optional[int] = None
    blocks: List[List[int]] = []
    if inv is not None:
        left_maps = [[tbl[tbl[g][x]][inv[g]] for x in range(n)] for g in range(n)]
        right_maps = [[tbl[g][tbl[x][inv[g]]] for x in range(n)] for g in range(n)]
        blocks = _orbits(left_maps, n)
        right_blocks = _orbits(right_maps, n)
        k_left = len(blocks)
        k_right = len(right_blocks)
        # Compared as PARTITIONS, not as counts. Two different partitions of
        # the same size are the exact substitution this round exists to stop.
        bracketing_agrees = blocks == right_blocks
    else:
        bracketing_agrees = False

    digest = sha256_bytes(_partition_bytes(blocks))
    predicted = None if k_left is None else k_left * n
    is_group = bool(is_associative and e is not None and inv is not None)
    five_eighths = Q(5, 8)
    return {
        "order": n,
        "is_associative": is_associative,
        "has_identity": e is not None,
        "identity": e,
        "has_inverses": inv is not None,
        "is_group": is_group,
        "commuting_pairs": commuting_pairs,
        "commuting_probability": probability,
        "commuting_probability_str": (f"{probability.numerator}/"
                                      f"{probability.denominator}"),
        "k_classes": k_left,
        "k_classes_right": k_right,
        "bracketing_agrees": bracketing_agrees,
        "class_equation_pairs": predicted,
        "class_equation_agrees": (predicted is not None
                                  and predicted == commuting_pairs),
        "class_partition": blocks,
        "class_partition_sha256": digest,
        "gustafson_5_8": not (five_eighths < probability),
        "gustafson_applies": is_group,
    }


#: The two labelling conventions for the dihedral group's reflections.
DIHEDRAL_CONVENTIONS: Tuple[str, ...] = ("reflection_first", "rotation_first")


def _cyclic_negate(i: int, n: int) -> int:
    """The additive inverse in ℤ/n with **no** ``abs()`` and no negative int
    ever formed: the Class-K pin-slot reads the flipped offset as a magnitude
    (``n - i``, non-negative by construction), and Class C re-enters the
    cyclic lane through :func:`srmech.cascade.cyclic_mod_add`, which correctly
    refuses a negative operand."""
    flipped = n - (i % n)                      # Class K — the sign FLIP
    return cyclic_mod_add(flipped, 0, n)       # Class C — re-application


def dihedral_group(n: int, convention: str) -> Dict[str, Any]:
    """The dihedral group ``D_n`` of order ``2n``, as a Cayley table.

    Args:
        n: the rotation order, ``>= 1``.  The group has order ``2n``.
        convention: ``"reflection_first"`` (reflections written ``s·rⁱ``) or
            ``"rotation_first"`` (``rⁱ·s``).  **REQUIRED, and honestly a
            LABELLING decision, not a structural one.**  Measured on ``D_12``:
            the map ``x -> x⁻¹`` is an isomorphism from one table to the other
            on **576/576** products, with identical class sizes
            ``[1,2,2,2,2,2,1,6,6]``; the identity map is not, so the
            instrument can return otherwise.  Two supports offered for a
            structural reading were refuted — "360 of 576 cells differ" is
            exactly ``order² − commuting_pairs`` (it restates
            *non-abelian*, already reported one field away), and a downstream
            13824-vs-5184 split is identical on BOTH tables.  The parameter
            stays required for the same reason
            :func:`srmech.music.relations.prime_form`'s ``convention`` is —
            a caller must say which labels it means — and for no more.

    Returns:
        ``{"n", "order", "convention", "elements", "cayley_table",
        "identity", "rotations", "reflections"}``.  ``elements`` are the
        labels ``["r^0", …, "r^{n-1}", "s·r^0", …]`` (or ``"r^i·s"``);
        ``cayley_table[i][j]`` is the index of the product.

    **Why it ships.**  No group of order 12 or 24 is reachable from srmech at
    all: :func:`srmech.cascade.unit_loop` yields orders ``{4, 8, 16, 32}``
    only, and :func:`srmech.cascade.group_algebra_table` raises
    ``dim must be a power of two`` on 3, 5, 12 and 24 — and is abelian by its
    own docstring besides.  So every non-abelian, non-power-of-two carrier the
    censuses in this module need was unreachable, which made
    :func:`conjugacy_census` and the reversal censuses vacuous outside loops.
    That is the whole justification, and it is enough on its own.

    Note:
        Exact integers; the only sign handling is
        :func:`_cyclic_negate`'s Class-K pin-slot then Class-C re-entry.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"dihedral_group: n must be int; got {type(n).__name__}")
    if n < 1:
        raise ValueError(f"dihedral_group requires n >= 1; got {n}")
    if convention not in DIHEDRAL_CONVENTIONS:
        raise ValueError(
            f"dihedral_group: convention must be one of "
            f"{DIHEDRAL_CONVENTIONS}; got {convention!r}")

    order = 2 * n
    reflection_first = convention == "reflection_first"
    table: List[List[int]] = []
    for a in range(order):
        row: List[int] = []
        ra, sa = a % n, a >= n
        for b in range(order):
            rb, sb = b % n, b >= n
            if not sa and not sb:                    # rᵃ · rᵇ
                row.append(cyclic_mod_add(ra, rb, n))
            elif reflection_first:
                # s·rᵃ with rᵃ·s = s·r⁻ᵃ
                if not sa and sb:                    # rᵃ · (s·rᵇ) = s·r^(b−a)
                    row.append(n + cyclic_mod_add(rb, _cyclic_negate(ra, n), n))
                elif sa and not sb:                  # (s·rᵃ)·rᵇ = s·r^(a+b)
                    row.append(n + cyclic_mod_add(ra, rb, n))
                else:                                # (s·rᵃ)(s·rᵇ) = r^(b−a)
                    row.append(cyclic_mod_add(rb, _cyclic_negate(ra, n), n))
            else:
                # rᵃ·s with s·rᵃ = r⁻ᵃ·s
                if not sa and sb:                    # rᵃ · (rᵇ·s) = r^(a+b)·s
                    row.append(n + cyclic_mod_add(ra, rb, n))
                elif sa and not sb:                  # (rᵃ·s)·rᵇ = r^(a−b)·s
                    row.append(n + cyclic_mod_add(ra, _cyclic_negate(rb, n), n))
                else:                                # (rᵃ·s)(rᵇ·s) = r^(a−b)
                    row.append(cyclic_mod_add(ra, _cyclic_negate(rb, n), n))
        table.append(row)

    labels = [f"r^{i}" for i in range(n)]
    labels += [(f"s·r^{i}" if reflection_first else f"r^{i}·s") for i in range(n)]
    return {
        "n": n,
        "order": order,
        "convention": convention,
        "elements": labels,
        "cayley_table": table,
        "identity": 0,
        "rotations": list(range(n)),
        "reflections": list(range(n, order)),
    }
