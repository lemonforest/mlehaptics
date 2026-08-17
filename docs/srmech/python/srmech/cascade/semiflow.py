"""Finite semiflows — the TABULATED arrow (rc427, `#T1130`).

Class **E** (orbit / index catalog) then Class **D** (permutation pattern).

A finite self-map ``f : S -> S`` on an ``n``-element carrier iterated forever
is a **semiflow**: a transient of ``index`` steps during which the image
strictly shrinks, then a permutation of the surviving image forever after
(the *rho* shape).  ``index == 0`` is exactly the case where ``f`` is already
a bijection — where the map is a GROUP action and there is no arrow.

RATIONALE — REWRITTEN, and the correction matters
=================================================
The first specification justified this op by "it consumes a Cayley table
:func:`srmech.cascade.unit_loop` already produces".  That justification is
**measurably vacuous** and is retracted here rather than quietly dropped.  A
loop's Cayley table is a **Latin square by axiom** — every row and every
column is a permutation — so every row of a ``unit_loop`` table is a bijection
and this op can only ever return ``index = 0`` on one.  Measured at dims 4, 8,
16 and 32: 4/4, 8/8, 16/16, 32/32 rows are permutations.  The one carrier the
original rationale named is the one class where the instrument is guaranteed
to find nothing.

The real feeders are the maps that genuinely lose information:

* ``srmech.biology.q8.q8_project_v4`` — the shipped non-injective idempotent
  self-map (8 -> 4 on the Q8 byte carrier), index 1, period 1.
* ``x -> mod_pow(a, x, n)`` and ``x -> (c*x) mod n`` — the multiplicative
  arrows.  :func:`srmech.math.cyclic.mod_mul_arrow` gives the SAME two numbers
  in closed form for the specific ``(c*x) mod n`` family; this op is the
  tabulated peer that takes any self-map at all and has to iterate. No ``abs()`` — every quantity here is a non-negative count.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from ..amsc.format import sha256_bytes

__all__ = ["finite_semiflow"]


def _coerce_map(table: Sequence[Any]) -> List[int]:
    """Validate a self-map table: a length-``n`` sequence of ints in ``[0, n)``."""
    rows = list(table)
    n = len(rows)
    if n == 0:
        raise ValueError("finite_semiflow: table must be non-empty")
    out: List[int] = []
    for x, v in enumerate(rows):
        if not isinstance(v, int) or isinstance(v, bool):
            raise TypeError(
                f"finite_semiflow: table[{x}] must be int; "
                f"got {type(v).__name__}")
        if not 0 <= v < n:
            raise ValueError(
                f"finite_semiflow: table[{x}] = {v} is outside [0, {n}) — "
                f"the table must be a self-map of its own index set")
        out.append(v)
    return out


def finite_semiflow(table: Sequence[int]) -> Dict[str, Any]:
    """The rho SHAPE of the finite self-map ``f`` given by ``table``.

    Args:
        table: ``table[x]`` is ``f(x)``; a length-``n`` list of ints in
            ``[0, n)``.  Any self-map of a finite set, given as its graph.

    Returns:
        A dict with

        * ``order`` — ``n``, the carrier size.
        * ``index`` — the TRANSIENT length: the least ``k`` with
          ``|f^k(S)| == |f^{k+1}(S)|``.  ``0`` iff ``f`` is a permutation.
        * ``period`` — the order of ``f`` restricted to the eventual image
          (which is a permutation of it), i.e. the least ``p > 0`` with
          ``f^{index+p} == f^{index}``.
        * ``eventual_size`` — ``|f^index(S)|``.
        * ``eventual_image`` — that image as a sorted index list.  Reported as
          a **SET**, not only a count: the round this op ships in exists
          because two censuses agreed on a count and disagreed on the set.
        * ``eventual_image_sha256`` — Class-A content address of the image
          set (the newline-joined decimal indices, UTF-8), so two runs can be
          compared without shipping the set around.
        * ``is_permutation`` — ``index == 0``.
        * ``semigroup_not_group`` — ``index > 0``: ``f`` has no inverse in the
          semigroup it generates.  THIS is the arrow predicate.
        * ``kernel_orders`` — the preimage-size histogram of the FIRST step,
          ``{preimage_size: how_many_targets}``.  The shape of what one
          application destroys — never which element, for the reason
          :func:`srmech.math.cyclic.mod_mul_arrow` states at length.
          Its keys are ``int`` in-process; **over the MCP wire they arrive
          as the decimal strings JSON object keys must be** (``{2: 4}`` →
          ``{"2": 4}``), so a wire client keys on ``str``.

    Example — the shipped non-injective self-map::

        finite_semiflow(list(q8_project_v4(bytes(range(8)))))
        # -> index 1, period 1, eventual_size 4, semigroup_not_group True
        #    q8_project_v4 takes a SEQUENCE of Q8 bytes and returns bytes;
        #    it is not an elementwise int -> int map.

    and its negative control, any row of a Latin square::

        finite_semiflow(unit_loop(8)["cayley_table"][3])
        # -> index 0, period 4, eventual_size 16, semigroup_not_group False

    Note:
        Iterative by necessity — an arbitrary self-map has no closed form.
        For the specific ``(c*x) mod n`` family, prefer the closed-form
        :func:`srmech.math.cyclic.mod_mul_arrow`, which returns the same
        index and period without touching a single element.
    """
    f = _coerce_map(table)
    n = len(f)

    image = list(range(n))
    index = 0
    while True:
        nxt = sorted({f[x] for x in image})
        if len(nxt) == len(image):
            break
        image = nxt
        index += 1

    # Period: the order of the permutation f restricted to `image`.
    period = 1
    cur = {x: f[x] for x in image}
    while any(cur[x] != x for x in image):
        cur = {x: f[cur[x]] for x in image}
        period += 1

    hits: Dict[int, int] = {}
    for x in range(n):
        hits[f[x]] = hits.get(f[x], 0) + 1
    kernel_orders: Dict[int, int] = {}
    for size in hits.values():
        kernel_orders[size] = kernel_orders.get(size, 0) + 1

    digest = sha256_bytes("\n".join(str(x) for x in image).encode("utf-8"))
    return {
        "order": n,
        "index": index,
        "period": period,
        "eventual_size": len(image),
        "eventual_image": image,
        "eventual_image_sha256": digest,
        "is_permutation": index == 0,
        "semigroup_not_group": index > 0,
        "kernel_orders": kernel_orders,
    }
