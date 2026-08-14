"""Cascade **leaves** — the framing / access / assembly inventory the
`#T1114` census measured missing (v0.9.0rc420).

Rung 3 of the `#T1114` arc catalogued six distinct blockers between the 20
cascade-catalog descriptors and an executable ADR-0008 §2 chain; two of them
were *inventory* gaps rather than engine gaps:

- **BLK-FRAMING** — no registered framing/assembly primitives: tuple-pack
  (``pair``), byte-slice / int-parse (the ``encode_loe_content`` stride),
  string assembly (``str_concat`` / ``utf8_encode``).
- the **indexed-map leaf set** (rung 4 ``inventory_probe``) — LENGTH
  (``seq_len``), DYNAMIC element access (``seq_get`` — the shipped reference
  grammar's ``[N]`` indexer is literal-only, so a computed index can only
  enter through an op), and the scalar/vector accumulation leaves
  (``f64_add`` / ``vec_add`` / ``vec_scale``) that serve as fold bodies.

Two further leaves close measured value-divergences between a naive chain
and its shipped op:

- :func:`dead_band` — the Class-K dead-band gate ``best_rational_signed``
  applies BEFORE scaling (``magnitude < _ZERO_BAND -> the carrier's zero``).
  Without it a declared chain diverges from the shipped op in the
  (sub-dead-band magnitude x huge ``fine_scale`` / huge ``max_denominator``)
  corner.
- :func:`orientation_compose` — the fold body for ``net_chirality``.
  MEASURED (rc420): a bare fold of :func:`srmech.cascade.atoms.reorient`
  is NOT value-identical to the shipped op — ``net_chirality([0, -1]) == 0``
  but ``reorient(reorient(1, orientation=0), orientation=-1) == -1``,
  because ``reorient``'s ``orientation == 0`` branch is a NO-OP while the
  shipped loop's ``o == 0`` guard is ABSORBING. The zero-absorption branch
  is descriptor-static, so it exiles into this op instance (the
  ``_control_flow`` exile discipline), which then folds correctly.

**Class letters are CLASSIFICATION, not addressing** (the rc420 BLK-REGMAP
resolution): these leaves are reachable from a chain step by dotted op name
(``op = "srmech.cascade.leaves.seq_len"``) regardless of which letter the
step declares. The honest classifications are recorded per-op below.

**No ``abs()``** anywhere, per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``; no
``numpy`` / ``math`` / ``fractions`` / ``decimal``.
"""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

from .atoms import reorient


def seq_len(seq: Sequence) -> int:
    """Class B (framing): the length of a sized sequence.

    The L in TLV — a frame's element count, fixed at the moment the frame is
    read. This is the leaf every indexed-map chain uses to pin ``n`` at
    entry (the totality argument: ``n`` is data-SIZED, never
    data-dependent). Rejects unsized iterables by construction (``len``
    raises ``TypeError``), which is exactly the map form's entry contract.
    """
    return len(seq)


def seq_get(seq: Sequence, i: int):
    """Class E (catalog lookup): dynamic element access ``seq[i]``.

    The reference grammar's ``[N]`` indexer is literal-only (a descriptor
    can spell ``@step[0].output[1]`` but never ``x[@idx.k]``), so a COMPUTED
    index enters a chain only through an op — this one. Lookup-by-position
    is the degenerate catalog lookup: the catalog is the sequence, the key
    is the index.
    """
    return seq[i]


def pair(first, second) -> Tuple:
    """Class B (framing): assemble two values into a 2-tuple.

    A chain returns only its FINAL step's output, so a declared
    ``tuple[int, int]`` return can only be built by a step — this one.
    Proposed by the `#T1114` rung-1 inversion spike, measured load-bearing
    for ``best_rational_signed`` (the ``(signed_numerator, denominator)``
    assembly), registered rc420.
    """
    return (first, second)


def str_concat(prefix: str, text: str) -> str:
    """Class F (render): concatenate two strings — the degenerate template.

    The one string-assembly step the shipped cascades need (the
    ``encode_loe_content`` mint names ``"LoE.content." + content`` /
    ``"LoE.substrate." + substrate``). :func:`srmech.math.template.render`
    is the general Class-F primitive but is bytes-typed; this leaf is the
    str-typed prefix-concat special case.
    """
    return prefix + text


def utf8_encode(text: str) -> bytes:
    """Class B (framing): UTF-8 encode a string to bytes.

    The str -> bytes framing boundary (the shipped
    ``content.encode("utf-8")`` step of ``encode_loe_content``).
    """
    return text.encode("utf-8")


def byte_slice(data: bytes, start: int, stop: int) -> bytes:
    """Class B (framing): the byte-range ``data[start:stop]``.

    The framing half of the ``encode_loe_content`` stride
    (``sha256(content)[0:8]``); measured missing at `#T1114` rung 3
    (BLK-FRAMING).
    """
    return data[start:stop]


def int_parse_le(data: bytes) -> int:
    """Class B (framing): parse bytes as a little-endian unsigned integer.

    The int-parse half of the ``encode_loe_content`` stride
    (``int.from_bytes(digest[0:8], "little")``); measured missing at
    `#T1114` rung 3 (BLK-FRAMING).
    """
    return int.from_bytes(data, "little")


def f64_add(a: float, b: float) -> float:
    """Class M (accumulate): scalar ``a + b`` — the fold body for a plain Σ.

    The DSL classifies fold/reduce as Class M (cross-class bind: accumulator
    + element each step); this is the scalar accumulator those forms bind.
    A LEFT fold from a ``0.0`` seed reproduces the shipped
    ``coupling_sum += term`` order bit-exactly (``0.0 + t == t``, then the
    identical add order).
    """
    return a + b


def vec_add(a: Sequence[float], b: Sequence[float]) -> List[float]:
    """Class M (accumulate): elementwise vector ``a + b`` — the Σ_m fold body
    for the hypercomplex DFT chains.

    A LEFT fold from a zero seed reproduces the shipped ``acc[i] += term[i]``
    order bit-exactly (``0.0 + t == t``; then the identical per-slot add
    order).

    Raises:
        ValueError: ``a`` and ``b`` have different lengths. Elementwise
            addition of mismatched vectors is undefined, and the two
            orientations were not even failing the same way.

    Note:
        rc431 (`#T1129`) -- **this was a silent wrong answer**, the worst defect
        class this project recognises. The body ranged over ``len(a)`` alone, so
        ``vec_add([1.0], [1.0, 2.0])`` RETURNED ``[2.0]``: ``b``'s tail was
        dropped with no error, no warning and a plausible-looking result, on a
        public registry op. The mirror orientation
        ``vec_add([1.0, 2.0], [1.0])`` leaked a bare ``IndexError`` from the
        comprehension instead -- so the same malformed call was silently wrong
        one way round and noisily wrong the other, which is why neither
        orientation had ever been noticed. Guarding on equal length is the only
        answer that is correct in both: there is no length at which dropping a
        tail is the right elementwise sum. Repair precedent: ``coupled.py:187``
        (``all streams must have equal length``).
    """
    if len(a) != len(b):
        raise ValueError(
            f"vec_add: a and b must have equal length; got {len(a)} and "
            f"{len(b)} (elementwise addition of mismatched vectors is "
            f"undefined -- this silently truncated to len(a) before rc431)")
    return [a[i] + b[i] for i in range(len(a))]


def vec_scale(v: Sequence[float], s: float) -> List[float]:
    """Class M (accumulate): elementwise ``v * s`` — mirrors the shipped DFT
    output scale ``[acc[i] * scale for i in range(dim)]`` bit-exactly.
    """
    return [v[i] * s for i in range(len(v))]


def dead_band(value, band):
    """Class K (pin-slot dead-band): gate a non-negative magnitude at a band.

    Returns ``value`` unchanged when ``value >= band``, else ``value``'s own
    zero (``value * 0`` — type-preserving over ``int`` / ``float`` / exact
    carriers, mirroring the ``pin_slot_at_zero`` origin discipline; NaN
    propagates as NaN, never silently read as zero).

    This is the ``_ZERO_BAND`` branch of ``best_rational_signed`` exiled to
    its own op instance so a declared chain carries the SAME dead-band the
    shipped op applies. Measured (rc420): without this step a
    ``pin_slot -> scale_round -> best_rational`` chain diverges from the
    shipped op when a sub-dead-band magnitude meets a large-enough
    ``fine_scale`` + ``max_denominator``.

    The input contract is a Class-K MAGNITUDE (already non-negative — the
    second element of a ``pin_slot_at_zero`` result); the comparison is a
    plain ``>=`` on that non-negative domain, so no sign branch and no
    ``abs()`` is involved.
    """
    if value >= band:
        return value
    return value * 0


def orientation_compose(acc: int, orientation: int) -> int:
    """Class C (cascade-orientation): one step of the net-chirality product.

    ``0`` when ``orientation == 0`` (a zero-crossing collapses net
    handedness — ABSORBING), else ``reorient(acc, orientation=orientation)``
    (the Class-C sign re-application). Folding this op left over an
    orientation list from a ``+1`` seed IS ``net_chirality`` — verified
    value-identical (rc420) where a bare ``reorient`` fold is NOT
    (``reorient``'s ``orientation == 0`` branch is a no-op, so it cannot
    absorb; measured: ``net_chirality([0, -1]) == 0`` but the bare fold
    returns ``-1``).

    Positionally fold-shaped ``(acc, elem)`` on purpose, so both the DSL
    ``fold``/``reduce`` and the ADR-0008 §2 fold step bind it directly.
    """
    if orientation == 0:
        return 0
    return reorient(acc, orientation=orientation)


__all__ = [
    "byte_slice",
    "dead_band",
    "f64_add",
    "int_parse_le",
    "orientation_compose",
    "pair",
    "seq_get",
    "seq_len",
    "str_concat",
    "utf8_encode",
    "vec_add",
    "vec_scale",
]
