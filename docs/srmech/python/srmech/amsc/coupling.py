"""Class K ∘ L — signed-sum coupling score.

``signed_sum_squared(sources)``: per-element ``(Σ_sources (2·bit − 1))²``.

The bipolar transform ``2·bit − 1 ∈ {−1, +1}`` is the **Class-K** sign-
projection (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`` —
no ``abs()``; signed arithmetic only); the element-wise sum across sources
then **squared** is the **Class-L** signed-magnitude-squared coupling score
(sign-agnostic coupling strength). This is a **composition** of existing
primitive classes (K then L) operating on a *stack* of bit-arrays — NOT a
new primitive class (the 14-class A–N vocabulary is intact per
``[[feedback_no_privileged_primitive_classes]]``), so it carries no
dedicated C symbol: the underlying Class-K / Class-L primitives are the
ones with C parity, and a composition sequences them in Python.

Per UPSTREAM_NOTES §1.2 (RBS-LM research subtree) — surfaced by
R-RBS-LM-33 weak-coupling-truncate and R-RBS-LM-49 Method C, both of which
need ``coupling_sq = (Σ_sources (2·bits − 1))²``.

numpy-FREE (#564): the score is integer arithmetic over plain Python ``int``
lists — the bipolar sum and its square need no array engine.

Canonical SSoT: the bipolar / spatter-code convention — Kanerva (2009)
*Hyperdimensional Computing*, Cognitive Computation 1, 139.
"""

from __future__ import annotations

from typing import List, Sequence


def signed_sum_squared(sources: Sequence) -> List[int]:
    """Squared signed-sum coupling score across a stack of bit-arrays.

    Args:
        sources: A non-empty sequence of equal-length 1-D sequences, each
            holding bits in ``{0, 1}``.

    Returns:
        A ``list[int]`` (same length as each source): per position,
        ``(Σ_sources (2·bit − 1))²`` — the squared signed-sum, i.e. the
        Class-L magnitude-square of the Class-K bipolar-projected sum.
        Range ``[0, n_sources²]``; ``n_sources²`` = full agreement,
        ``0`` = balanced (equal +1 / −1 across sources).

    Raises:
        ValueError: empty ``sources``, mismatched lengths, or values
            outside ``{0, 1}``.
    """
    if len(sources) == 0:
        raise ValueError(
            "coupling.signed_sum_squared: requires at least one source"
        )
    arrs = [[int(x) for x in s] for s in sources]
    n = len(arrs[0])
    if n == 0:
        raise ValueError("coupling.signed_sum_squared: sources must be non-empty")
    for i, a in enumerate(arrs):
        if len(a) != n:
            raise ValueError(
                f"coupling.signed_sum_squared: source {i} length {len(a)} "
                f"!= {n}"
            )
        for v in a:
            if v not in (0, 1):
                raise ValueError(
                    f"coupling.signed_sum_squared: source {i} must hold bits "
                    f"in {{0, 1}}"
                )
    out: List[int] = []
    for pos in range(n):
        # Class K — bipolar sign-projection {0,1} -> {-1,+1}; sum across sources.
        signed_sum = 0
        for a in arrs:
            signed_sum += 2 * a[pos] - 1
        # Class L — signed-magnitude-squared (no abs(); the square is sign-agnostic).
        out.append(signed_sum * signed_sum)
    return out


__all__ = ["signed_sum_squared"]
