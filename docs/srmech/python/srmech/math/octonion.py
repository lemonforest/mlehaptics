"""Octonion — the DISCRETE octonion Moufang loop ``{±e₀, ±e₁, …, ±e₇}`` as
4-bit bytes (0.9.0rc324): the Cayley–Dickson rung ABOVE the Q₈ group
(:mod:`srmech.biology.q8`), the byte-exact discrete peer of the CONTINUOUS ``𝕆``
surface in :mod:`srmech.qm.octonion` (the float64 ODFT twiddle). Where
``qm.octonion`` carries float64 octonions, this module carries one signed basis
unit in a single ``uint8`` and multiplies it in pure INTEGER bit-arithmetic —
no floats, so no FMA / FP-contraction concern.

THE ENCODING. A byte ``o ∈ {0..15}`` is ``o = (sign_bit << 3) | index``:

- ``index = o & 7`` ∈ ``{0..7}`` = the basis index ``e₀ … e₇`` (the FULL
  octonion — indices ``4..7`` are the non-quaternionic units the associative
  Q₈ sub-block ``0..3`` cannot reach)
- ``sign_bit = o >> 3`` ∈ ``{0,1}`` = the center ``{+, −}``

so ``0=+e₀ (=+1), 1=+e₁, …, 7=+e₇, 8=−e₀ (=−1), 9=−e₁, …, 15=−e₇``. The 16
values ARE the Moufang loop ``{±e₀..±e₇}`` — the closure of the octonion basis
units under signed product.

THE PRODUCT. The signed basis-unit product factors exactly like Q₈'s central
extension, one Cayley–Dickson rung up::

    (s_a · e_{x_a})(s_b · e_{x_b}) = (s_a ⊕ s_b ⊕ F[x_a][x_b]) · e_{x_a ⊕ x_b}

with ``x = o & 7`` the basis index, ``s = o >> 3`` the center sign, and
``F[x_a][x_b] = 1`` iff the Cayley–Dickson basis product ``e_{x_a} · e_{x_b}``
carries the ``−1`` sign — the SAME generative cocycle
:func:`srmech.cascade.cayley_dickson.cd_basis_product` computes at
``dim=8`` (this module DERIVES ``F`` from it — no hand-entered magic table, so
it cannot drift from the octonion algebra it claims). The result index is
ALWAYS ``x_a ⊕ x_b`` (the Fano ⊕-structure); the sign carries the orientation.

NON-ASSOCIATIVE, and that is the point. Unlike Q₈, the octonions are NON-
associative — but this per-slot carrier holds ONE signed basis unit per slot,
and the Moufang loop ``{±e₀..±e₇}`` has the INVERSE PROPERTY: ``(x·y)·y⁻¹ = x``
for every loop element (Artin: any two loop elements generate an associative
subalgebra, and ``y⁻¹ = conj(y)`` lives in ``⟨y⟩``). So the RIGHT-conjugate
decouple ``oct_mult(oct_mult(turn, one), conj(one)) == turn`` holds BYTE-EXACT
per slot, and the carrier round-trips exactly. Non-associativity only bites for
products of ``≥ 3`` INDEPENDENT basis units — the fiber/associator channel the
LATER rc reads, NOT this carrier.

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``oct_mult`` / ``oct_bind`` — **Class M** (loop / HDC bind) ∘ **Class I**
  (the ⊕ index + the ``Z₂`` sign as an exclusive-or; the sign is a group-
  encoding BIT computed by ``⊕``, never an ``abs()``).
- ``oct_conjugate`` — **Class C** (chirality / orientation): the loop inverse,
  ``oct_mult(a, oct_conjugate(a)) == 0`` for every ``a``.

Same-rc C peers (everything-mirrors): ``srmech_oct_mult`` / ``srmech_oct_bind``
/ ``srmech_oct_conjugate`` — byte-for-byte identical with the pure paths here
(these are EXACT integer ops, so native == pure is definitional, and the parity
gate re-verifies it on all ``16 × 16`` pairs).

Canonical SSoT: the octonion / Cayley–Dickson convention is Baez, J.C. (2002)
*The Octonions*, Bull. Amer. Math. Soc. 39, 145-205, arXiv:math/0105155 (§1–§2,
the Fano-plane sign structure).
"""

from __future__ import annotations

import ctypes
import functools
from typing import List, Sequence, Tuple

from srmech import _native
from srmech.math.hv import HV as _HV  # noqa: F401  (parity with q8; carrier HV type)

#: The octonion loop alphabet size (4 bits: 3 for the e₀..e₇ index, 1 for the
#: center sign). The 16 values are the Moufang loop {±e₀..±e₇}.
_OCT_N = 16

#: The basis-index alphabet (the 8 octonion units e₀..e₇, dim of the algebra).
_OCT_DIM = 8


@functools.lru_cache(maxsize=1)
def _build_sign_table() -> Tuple[Tuple[int, ...], ...]:
    """The ``8×8`` Cayley–Dickson cocycle sign table ``F`` (cached).

    ``F[x_a][x_b] = 1`` iff the basis product ``e_{x_a} · e_{x_b}`` carries the
    ``−1`` sign — DERIVED from
    :func:`srmech.cascade.cayley_dickson.cd_basis_product` at ``dim=8``
    (the SAME generative cocycle ``qm.octonion`` builds its structure from), so
    there is no hand-entered constant to drift. The result index is always
    ``x_a ⊕ x_b`` (the Fano ⊕-structure), which this module relies on for the
    index lane; the sign is the only non-trivial content, and it is exactly
    ``F``. The ``dim=4`` restriction of THIS table is exactly Q₈'s ``F``.
    """
    from srmech.cascade.cayley_dickson import cd_basis_product
    table: List[Tuple[int, ...]] = []
    for xa in range(_OCT_DIM):
        row: List[int] = []
        for xb in range(_OCT_DIM):
            idx, sign = cd_basis_product(_OCT_DIM, xa, xb)
            # idx is always xa ^ xb (the Fano ⊕); F is the sign bit.
            assert idx == (xa ^ xb)
            row.append(0 if sign == 1 else 1)
        table.append(tuple(row))
    return tuple(table)


def _native_ready(symbol: str) -> bool:
    """True iff the native lib is loaded AND exports ``symbol`` (numpy-free)."""
    return bool(
        _native.HAS_NATIVE and _native.LIB is not None
        and hasattr(_native.LIB, symbol)
    )


def _check_element(o: int, op: str) -> int:
    """Coerce ``o`` to an ``int`` and assert it is a valid octonion loop element
    (``0..15``)."""
    oi = int(o)
    if not (0 <= oi < _OCT_N):
        raise ValueError(
            f"{op}: an octonion element must be an int in [0, 16); got {o!r}"
        )
    return oi


def _as_oct_buffer(buf: Sequence[int], op: str, name: str) -> bytes:
    """Coerce ``buf`` to ``bytes`` of valid octonion elements (numpy-free).

    Accepts any 1-D sequence of ints (``bytes`` / ``bytearray`` / ``list`` /
    ``tuple``); every element must be a valid octonion byte (``0..15``).
    Returns a ``bytes`` object so the native and pure paths consume the
    identical buffer (the parity contract)."""
    try:
        out = bytes(_check_element(b, op) for b in buf)
    except TypeError as exc:  # non-iterable
        raise ValueError(
            f"{op}: {name} must be a 1-D sequence of octonion bytes; got {buf!r}"
        ) from exc
    return out


def oct_mult(a: int, b: int) -> int:
    """The octonion loop product ``a · b`` of two 4-bit bytes (the discrete peer
    of the ``𝕆`` product, one Cayley–Dickson rung above :func:`q8_mult`).

    ``(s_a · e_{x_a})(s_b · e_{x_b}) = (s_a ⊕ s_b ⊕ F[x_a][x_b]) · e_{x_a ⊕ x_b}``
    with ``x = o & 7`` the basis index, ``s = o >> 3`` the center sign, and
    ``F`` the Cayley–Dickson cocycle at ``dim=8`` (:func:`_build_sign_table`).
    ``0`` (``+e₀``) is the identity; ``e_i² = −1`` (``= byte 8``) for every
    ``i ≠ 0``. The product is NON-associative over ``≥ 3`` independent units
    (the octonion associator), but the index lane is exact: ``(a·b)&7 ==
    (a&7)^(b&7)``.

    Class M (loop bind) ∘ Class I (the ⊕ index + the ``Z₂`` sign ⊕; no
    ``abs()`` — the sign is a group ⊕-bit). Dispatches to the same-rc C peer
    ``srmech_oct_mult`` (byte-exact pure fallback otherwise).

    Args:
        a: An octonion element (int in ``[0, 16)``).
        b: An octonion element (int in ``[0, 16)``).

    Returns:
        The product ``a · b`` as an octonion byte (int in ``[0, 16)``).

    Raises:
        ValueError: if ``a`` or ``b`` is not a valid octonion element.
    """
    ai = _check_element(a, "oct_mult")
    bi = _check_element(b, "oct_mult")
    if _native_ready("srmech_oct_mult"):
        return int(_native.LIB.srmech_oct_mult(
            ctypes.c_uint8(ai), ctypes.c_uint8(bi)))
    f = _build_sign_table()
    xa, xb = ai & 7, bi & 7
    sign = (ai >> 3) ^ (bi >> 3) ^ f[xa][xb]
    return (sign << 3) | (xa ^ xb)


def oct_conjugate(a: int) -> int:
    """The octonion conjugate / loop inverse ``conj(a)``.

    ``conj(a) = a`` for the real center (index ``0``, self-inverse), else
    ``a ⊕ 8`` (flip an imaginary unit's sign bit). It is the loop inverse:
    ``oct_mult(a, oct_conjugate(a)) == 0`` for every ``a`` (and, by the Moufang
    inverse property, on the left too). Class C (chirality / orientation); a
    plain sign-bit flip (no ``abs()``), the discrete mirror of
    :func:`srmech.cascade.cayley_dickson.cd_conjugate`. Dispatches to the
    same-rc C peer ``srmech_oct_conjugate`` (byte-exact pure fallback).

    Args:
        a: An octonion element (int in ``[0, 16)``).

    Returns:
        The conjugate ``conj(a)`` as an octonion byte.

    Raises:
        ValueError: if ``a`` is not a valid octonion element.
    """
    ai = _check_element(a, "oct_conjugate")
    if _native_ready("srmech_oct_conjugate"):
        return int(_native.LIB.srmech_oct_conjugate(ctypes.c_uint8(ai)))
    return ai if (ai & 7) == 0 else ai ^ 8


def oct_bind(turn: Sequence[int], one: Sequence[int]) -> bytes:
    """Elementwise octonion bind ``out[i] = oct_mult(turn[i], one[i])`` over two
    equal-length octonion byte buffers.

    The buffer form of :func:`oct_mult` — the discrete peer of a per-slot ``𝕆``
    bind. ``turn`` and ``one`` are any 1-D sequences of octonion bytes
    (``bytes`` / ``bytearray`` / ``list``) of equal length; the result is
    ``bytes``. Class M (loop bind). Dispatches to the same-rc C peer
    ``srmech_oct_bind`` (which documents the same out-aliasing contract;
    byte-exact pure fallback).

    Args:
        turn: The left operand buffer (the "which-way" factor; Class C intent).
        one: The right operand buffer (the identity-anchored factor).

    Returns:
        The elementwise product as ``bytes`` of length ``len(turn)``.

    Raises:
        ValueError: on a length mismatch or a non-octonion byte.
    """
    t = _as_oct_buffer(turn, "oct_bind", "turn")
    o = _as_oct_buffer(one, "oct_bind", "one")
    if len(t) != len(o):
        raise ValueError(
            f"oct_bind: turn and one must be equal length; got {len(t)} and "
            f"{len(o)}"
        )
    n = len(t)
    if n and _native_ready("srmech_oct_bind"):
        c_turn = (ctypes.c_uint8 * n).from_buffer_copy(t)
        c_one = (ctypes.c_uint8 * n).from_buffer_copy(o)
        c_out = (ctypes.c_uint8 * n)()
        rc = _native.LIB.srmech_oct_bind(c_turn, c_one, ctypes.c_uint32(n), c_out)
        if rc == _native.SRMECH_OK:
            return bytes(c_out)
    f = _build_sign_table()
    out = bytearray(n)
    for i in range(n):
        a, b = t[i], o[i]
        xa, xb = a & 7, b & 7
        sign = (a >> 3) ^ (b >> 3) ^ f[xa][xb]
        out[i] = (sign << 3) | (xa ^ xb)
    return bytes(out)


__all__ = [
    "oct_bind",
    "oct_conjugate",
    "oct_mult",
]
