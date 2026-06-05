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
need ``coupling_sq = (Σ_sources (2·bits − 1))²`` and previously inlined it
as bare numpy with a docstring note that the operation IS Class K + L.

Canonical SSoT: the bipolar / spatter-code convention — Kanerva (2009)
*Hyperdimensional Computing*, Cognitive Computation 1, 139.
"""

from __future__ import annotations

from typing import Sequence

# numpy is the [scientific] extra (v0.7.0). This module mixes a numpy-free
# path with ndarray-typed ops; the lazy proxy keeps the module importable
# on a plain install and only the ndarray ops raise the [scientific] hint.
from srmech._scientific import lazy_numpy as _lazy_numpy
np = _lazy_numpy("srmech.amsc.coupling")


def signed_sum_squared(sources: Sequence) -> np.ndarray:
    """Squared signed-sum coupling score across a stack of bit-arrays.

    Args:
        sources: A non-empty sequence of equal-length 1-D arrays, each
            holding bits in ``{0, 1}``.

    Returns:
        ``int64`` array (same length as each source): per position,
        ``(Σ_sources (2·bit − 1))²`` — the squared signed-sum, i.e. the
        Class-L magnitude-square of the Class-K bipolar-projected sum.
        Range ``[0, n_sources²]``; ``n_sources²`` = full agreement,
        ``0`` = balanced (equal +1 / −1 across sources).

    Raises:
        ValueError: empty ``sources``, mismatched lengths, non-1-D input,
            or values outside ``{0, 1}``.
    """
    if len(sources) == 0:
        raise ValueError(
            "coupling.signed_sum_squared: requires at least one source"
        )
    arrs = [np.asarray(s, dtype=np.int64) for s in sources]
    n = arrs[0].size
    if n == 0:
        raise ValueError("coupling.signed_sum_squared: sources must be non-empty")
    for i, a in enumerate(arrs):
        if a.ndim != 1:
            raise ValueError(
                f"coupling.signed_sum_squared: source {i} must be 1-D "
                f"(got ndim {a.ndim})"
            )
        if a.size != n:
            raise ValueError(
                f"coupling.signed_sum_squared: source {i} length {a.size} "
                f"!= {n}"
            )
        if not bool(np.isin(a, (0, 1)).all()):
            raise ValueError(
                f"coupling.signed_sum_squared: source {i} must hold bits "
                f"in {{0, 1}}"
            )
    # Class K — bipolar sign-projection {0,1} -> {-1,+1}; sum across sources.
    signed_sum = np.sum(np.stack([2 * a - 1 for a in arrs]), axis=0)
    # Class L — signed-magnitude-squared (no abs(); the square is sign-agnostic).
    return (signed_sum * signed_sum).astype(np.int64)


__all__ = ["signed_sum_squared"]
