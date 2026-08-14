"""Reversal censuses — counts are not sets (rc427, `#T1130`).

Class **C** (which-way) then **D** (census) then **A** (SHA-256 of each hit
SET).  Two ops, and both exist for one reason: **a count agreeing is not a
set agreeing, and this project has twice concluded otherwise from a count.**

The measured case that forced them.  On the octonion unit loop M16 the BARE
reversal law and the flat-bracketed CHIRAL law each hold on **2752 of 4096**
ordered triples — identical counts — while succeeding on **different
triples**, 1344 each way.  A count-only instrument declares them equivalent
and is wrong; a control written to guard against exactly that recorded
``bare_equals_chiral: true`` from ``2752 == 2752`` in the same row where its
own set-overlap field said otherwise.

Measured here across the carrier ladder, that equality is worse than
misleading — it is **carrier-specific**.  Q8 scores 320 vs 512, M32 26048 vs
17984, D12 5184 vs 13824.  Only M16 makes the two counts coincide.  The set
disagreement is the durable fact and the equal counts are an accident of one
carrier, which is the strongest possible argument for never letting a count
decide.

So every hit SET here is content-addressed with
:func:`srmech.amsc.format.sha256_bytes` and every comparison is a set
comparison.  The counts are still reported — they are useful — but no verdict
in this module is derived from one.

Both ops take a **Cayley table**, never a callable.  A callable cannot cross
the JSON-RPC boundary: the shipped contract types such a parameter
``host_callable`` and publishes JSON-schema ``null``, so over the wire the
only legal value is absence, and 0 of the 12 shipped callable parameters are
required.  A multiplication and an inversion are the SEMANTICS of these
censuses and cannot be optional, so the table is the only honest carrier.
:func:`srmech.cascade.unit_loop` and :func:`srmech.cascade.dihedral_group`
both return exactly this shape.

numpy-free; no ``abs()``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..amsc.format import sha256_bytes
from .atoms import chiral_flip
from .finite_group import _coerce_table, _identity, _inverses

__all__ = ["reversal_law_census", "anti_automorphism_witnesses"]


def _tuple_bytes(rows: List[Tuple[int, ...]]) -> bytes:
    """Canonical bytes of a SORTED set of index tuples, for content-addressing."""
    return "\n".join(",".join(str(x) for x in r) for r in sorted(rows)).encode("utf-8")


def _require_inverses(name: str, tbl: List[List[int]]) -> Tuple[int, List[int]]:
    e = _identity(tbl)
    if e is None:
        raise ValueError(
            f"{name}: the table has no two-sided identity, so inversion — "
            f"which both reversal laws quantify over — is undefined")
    inv = _inverses(tbl, e)
    if inv is None:
        raise ValueError(
            f"{name}: some element has no unique two-sided inverse, so the "
            f"chiral law has no subject")
    return e, inv


def reversal_law_census(cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """Census the reversal laws over all ordered triples, reporting the **hit
    SETS** and not only their sizes.

    The forward product is ``(a·b)·c``.  Reversing a WORD mirrors its
    bracketing — the reverse of ``(a b) c`` read right-to-left is ``c (b a)``
    — so the mirrored spelling is the honest one, and the flat one is kept
    beside it because a mismatched bracketing is how this comparison went
    wrong before.  Three cells:

    * **BARE** ``(a·b)·c == c·(b·a)`` — Class C alone, the word traversed the
      other way via :func:`srmech.cascade.chiral_flip` and nothing else.
    * **CHIRAL** ``((a·b)·c)⁻¹ == c⁻¹·(b⁻¹·a⁻¹)`` — Class C on the word AND
      inversion of each letter: the anti-automorphism law at length 3,
      mirrored consistently.
    * **CHIRAL-FLAT** ``((a·b)·c)⁻¹ == (c⁻¹·b⁻¹)·a⁻¹`` — the same law read
      with the bracketing left where it was.  **Not** a word reversal.

    Args:
        cayley_table: the ``n x n`` Cayley table.  Needs a two-sided identity
            and unique two-sided inverses; raises ``ValueError`` otherwise,
            because the chiral law has no subject without them.

    Returns:
        ``order`` · ``triples`` (``n³``) · for each of the three laws a count,
        its sorted hit set and its ``sha256`` · the pairwise intersection and
        one-sided difference counts, each with a sha · ``bare_equals_chiral``
        and ``bare_equals_chiral_flat`` as **SET** equalities, each beside its
        count-only twin ``*_counts_agree`` · ``chiral_is_total`` ·
        ``half_inversion_*`` (the negative control).

    **Two things this measures that were previously asserted.**

    1.  ``chiral_is_total`` is ``True`` on every carrier tested — Q8, M16,
        M32, D5, D12.  The chiral law is a THEOREM of these structures, not a
        finding about them, so any claim of the form *"chiral reversal
        succeeds on exactly the forward-success set"* is entailed rather than
        measured, and this field says so on every call.
    2.  ``bare_hits == chiral_flat_hits`` at **2752 = 2752** on M16 while the
        two sets differ by **1344 each way** — the counts-are-not-sets case
        that motivated the whole op.  And measured across the carrier ladder,
        that count coincidence is **carrier-specific**: Q8 320 vs 512,
        M32 26048 vs 17984, D12 5184 vs 13824.  The SET disagreement is the
        durable fact; the equal counts at M16 are an accident of one carrier,
        which is exactly why a count is not allowed to decide.

    Note:
        ``n³`` scan; exact integers, no float, no ``abs()``.
    """
    tbl = _coerce_table("reversal_law_census", cayley_table)
    n = len(tbl)
    _e, inv = _require_inverses("reversal_law_census", tbl)

    bare: List[Tuple[int, ...]] = []
    chiral: List[Tuple[int, ...]] = []
    flat: List[Tuple[int, ...]] = []
    half: List[Tuple[int, ...]] = []
    for a in range(n):
        for b in range(n):
            ab = tbl[a][b]
            for c in range(n):
                forward = tbl[ab][c]
                target = inv[forward]
                back_a, back_b, back_c = chiral_flip((a, b, c))   # Class C
                if tbl[back_a][tbl[back_b][back_c]] == forward:
                    bare.append((a, b, c))
                ia, ib, ic = chiral_flip((inv[a], inv[b], inv[c]))
                if tbl[ia][tbl[ib][ic]] == target:
                    chiral.append((a, b, c))
                if tbl[tbl[ia][ib]][ic] == target:
                    flat.append((a, b, c))
                # CONTROL: invert only the OUTER letters. A law blind to the
                # middle letter would score identically here; it does not.
                ha, hb, hc = chiral_flip((inv[a], b, inv[c]))
                if tbl[ha][tbl[hb][hc]] == target:
                    half.append((a, b, c))

    bare_set, chiral_set, flat_set = set(bare), set(chiral), set(flat)

    def _pair(left: set, right: set, stem: str) -> Dict[str, Any]:
        inter = sorted(left & right)
        lonly = sorted(left - right)
        ronly = sorted(right - left)
        return {
            f"{stem}_intersection": len(inter),
            f"{stem}_intersection_sha256": sha256_bytes(_tuple_bytes(inter)),
            f"{stem}_left_only": len(lonly),
            f"{stem}_left_only_sha256": sha256_bytes(_tuple_bytes(lonly)),
            f"{stem}_right_only": len(ronly),
            f"{stem}_right_only_sha256": sha256_bytes(_tuple_bytes(ronly)),
        }

    out: Dict[str, Any] = {
        "order": n,
        "triples": n ** 3,
        "forward_bracketing": "(a·b)·c",
        "bare_hits": len(bare),
        "bare_sha256": sha256_bytes(_tuple_bytes(bare)),
        "chiral_hits": len(chiral),
        "chiral_sha256": sha256_bytes(_tuple_bytes(chiral)),
        "chiral_flat_hits": len(flat),
        "chiral_flat_sha256": sha256_bytes(_tuple_bytes(flat)),
        "chiral_is_total": len(chiral) == n ** 3,
        "bare_equals_chiral": bare_set == chiral_set,
        "bare_equals_chiral_counts_agree": len(bare) == len(chiral),
        "bare_equals_chiral_flat": bare_set == flat_set,
        "bare_equals_chiral_flat_counts_agree": len(bare) == len(flat),
        "half_inversion_hits": len(half),
        "half_inversion_sha256": sha256_bytes(_tuple_bytes(half)),
        "half_inversion_separates": set(half) != chiral_set,
        "hit_triples": {"bare": bare, "chiral": chiral, "chiral_flat": flat},
    }
    out.update(_pair(bare_set, chiral_set, "bare_vs_chiral"))
    out.update(_pair(bare_set, flat_set, "bare_vs_chiral_flat"))
    return out


def anti_automorphism_witnesses(
        cayley_table: Sequence[Sequence[int]]) -> Dict[str, Any]:
    """The ``n²`` mechanism underneath :func:`reversal_law_census`: which
    ORDERED PAIRS satisfy the anti-automorphism law, as a **SET**.

    Three pair-sets, all measured, never inferred from one another:

    * **ANTI** — ``(a·b)⁻¹ == b⁻¹·a⁻¹``.  The law proper; Class C reverses the
      inverted letters via :func:`srmech.cascade.chiral_flip`.
    * **DIRECT** — ``(a·b)⁻¹ == a⁻¹·b⁻¹``.  The un-reversed spelling.
    * **COMMUTING** — ``a·b == b·a``.

    A prior round asserted that the direct law *"holds exactly on the
    commuting pairs"* **from an equality of counts**.  This op measures the
    two sets and reports ``direct_equals_commuting`` from
    ``set == set`` together with both symmetric-difference sizes, so the
    claim is either witnessed or refuted rather than assumed.

    Args:
        cayley_table: the ``n x n`` Cayley table.  Needs a two-sided identity
            and unique two-sided inverses.

    Returns:
        ``order`` · ``pairs`` (``n²``) · per set a count, the sorted pair list
        and its ``sha256`` · ``anti_holds_totally`` · ``direct_equals_commuting``
        with ``direct_not_commuting`` / ``commuting_not_direct`` ·
        ``anti_equals_commuting`` and its two differences.

    Note:
        ``n²`` scan; exact integers, no ``abs()``.
    """
    tbl = _coerce_table("anti_automorphism_witnesses", cayley_table)
    n = len(tbl)
    _e, inv = _require_inverses("anti_automorphism_witnesses", tbl)

    anti: List[Tuple[int, ...]] = []
    direct: List[Tuple[int, ...]] = []
    commuting: List[Tuple[int, ...]] = []
    for a in range(n):
        for b in range(n):
            target = inv[tbl[a][b]]
            back_a, back_b = chiral_flip((inv[a], inv[b]))        # Class C
            if tbl[back_a][back_b] == target:
                anti.append((a, b))
            if tbl[inv[a]][inv[b]] == target:
                direct.append((a, b))
            if tbl[a][b] == tbl[b][a]:
                commuting.append((a, b))

    anti_set, direct_set, comm_set = set(anti), set(direct), set(commuting)
    return {
        "order": n,
        "pairs": n * n,
        "anti_hits": len(anti),
        "anti_sha256": sha256_bytes(_tuple_bytes(anti)),
        "direct_hits": len(direct),
        "direct_sha256": sha256_bytes(_tuple_bytes(direct)),
        "commuting_hits": len(commuting),
        "commuting_sha256": sha256_bytes(_tuple_bytes(commuting)),
        "anti_holds_totally": len(anti) == n * n,
        "direct_equals_commuting": direct_set == comm_set,
        "direct_not_commuting": len(direct_set - comm_set),
        "commuting_not_direct": len(comm_set - direct_set),
        "anti_equals_commuting": anti_set == comm_set,
        "anti_not_commuting": len(anti_set - comm_set),
        "commuting_not_anti": len(comm_set - anti_set),
        "witness_pairs": {"anti": anti, "direct": direct},
    }
