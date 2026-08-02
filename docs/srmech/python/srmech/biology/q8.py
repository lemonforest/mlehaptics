"""Q8 — the DISCRETE quaternion group ``Q₈ = {±1, ±i, ±j, ±k}`` as 3-bit
bytes (0.9.0rc310): the discrete peer of the CONTINUOUS ``ℍ`` surface in
:mod:`srmech.physics.qm.quaternion`. Where ``qm.quaternion`` carries float64
quaternions (the 4×4 ``L_q``/``R_q`` operators, the ``exp(μθ)`` twiddle),
this module carries a Q₈ element in a single ``uint8`` and multiplies it in
pure INTEGER bit-arithmetic — no floats, so no FMA / FP-contraction concern.

THE ENCODING. A byte ``q ∈ {0..7}`` is ``q = (sign_bit << 2) | v4_coset``:

- ``v4_coset = q & 3`` ∈ ``{0,1,2,3}`` = the basis coset ``{1, i, j, k}``
- ``sign_bit = q >> 2`` ∈ ``{0,1}`` = the center ``{+, −}``

so ``0=+1, 1=+i, 2=+j, 3=+k, 4=−1, 5=−i, 6=−j, 7=−k``, and ``V4 = q & 3`` is
the abelian projection (the F380 / in-repo R21 homomorphism ``π: Q₈ → V4 =
Z₂ × Z₂``).

THE PRODUCT (the cocycle of the central extension ``1 → Z₂ → Q₈ → V4 → 1``).
The product of two signed basis units factors through the extension,

    ``(s_a · e_{x_a})(s_b · e_{x_b}) = (s_a ⊕ s_b ⊕ F[x_a][x_b]) · e_{x_a ⊕ x_b}``,

where ``F[x_a][x_b]`` is the cocycle sign bit — ``1`` iff the Cayley–Dickson
basis product ``e_{x_a}·e_{x_b}`` carries the ``−1`` sign. ``F`` is the dim-4
restriction of the SAME cocycle
:func:`srmech.cascade.cayley_dickson.cd_basis_product` computes (this
module DERIVES ``F`` from it — no hand-entered magic table), so ``q8_mult``
reproduces genuine ``Q₈``: NON-abelian (``q8_mult(1,2)=3`` but
``q8_mult(2,1)=7``), ``i² = j² = k² = 4`` (``−1``), associative over all
``8×8×8``, and the abelian projection is EXACT —
``(a·b) & 3 == (a&3) ⊕ (b&3)`` for all ``a,b`` (the F380/R21 homomorphism,
and why the future Q₈-genome sequence-read is backward-faithful).

Relationship to :func:`srmech.math.hdc.klein4_bind`: ``klein4_bind`` is the
abelian ``V4`` XOR binder (the HDC value algebra); ``q8_mult`` is its
NON-abelian central extension. ``q8_project_v4`` is exactly the homomorphism
that collapses this module onto that one — ``π(q8_mult(a, b)) ==
klein4_bind(π(a), π(b))``.

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``q8_mult`` / ``q8_bind`` — **Class M** (group / HDC bind) ∘ **Class I**
  (the ``V4`` XOR coset + the ``Z₂`` sign as an exclusive-or; the sign is a
  group-encoding BIT computed by ``⊕``, never an ``abs()``).
- ``q8_conjugate`` — **Class C** (chirality / orientation): the group
  inverse, ``q8_mult(a, q8_conjugate(a)) == 0`` for every ``a``.
- ``q8_project_v4`` — **Class I** (the abelian ``V4`` coset read; the
  ``π: Q₈ → V4`` homomorphism).

Same-rc C peers (everything-mirrors): ``srmech_q8_mult`` / ``srmech_q8_bind``
/ ``srmech_q8_conjugate`` / ``srmech_q8_project_v4`` — byte-for-byte identical
with the pure paths here (these are EXACT integer ops, so native == pure is
definitional, and the parity gate re-verifies it).

Canonical SSoT: the Q₈ / Cayley–Dickson convention is the octonion module's
(Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205,
arXiv:math/0105155 — §1); the Klein-4 bridge is the in-repo R21 proof
(``docs/srmech/rbs_lm_research/R-RBS-LM-R21_klein4_is_quaternion_units_mod_sign.py``).
"""

from __future__ import annotations

import ctypes
import functools
import json as _json
from typing import List, Sequence, Tuple

from srmech import _native
from srmech.math.hv import HV as _HV

#: The Q8 alphabet size (3 bits: 2 for the V4 coset, 1 for the center sign).
_Q8_N = 8


@functools.lru_cache(maxsize=1)
def _build_f_table() -> Tuple[Tuple[int, ...], ...]:
    """The ``4×4`` central-extension cocycle sign table ``F`` (cached).

    ``F[x_a][x_b] = 1`` iff the Cayley–Dickson basis product
    ``e_{x_a} · e_{x_b}`` carries the ``−1`` sign — DERIVED from
    :func:`srmech.cascade.cayley_dickson.cd_basis_product` at ``dim=4``
    (the SAME generative cocycle ``qm.quaternion`` builds its structure table
    from), so there is no hand-entered constant to drift. The result index is
    always ``x_a ⊕ x_b`` (the ``V4`` XOR), which this module relies on for the
    abelian projection; the sign is the only non-trivial content, and it is
    exactly ``F``.
    """
    from srmech.cascade.cayley_dickson import cd_basis_product
    table: List[Tuple[int, ...]] = []
    for xa in range(4):
        row: List[int] = []
        for xb in range(4):
            idx, sign = cd_basis_product(4, xa, xb)
            # idx is always xa ^ xb (the V4 homomorphism); F is the sign bit.
            row.append(0 if sign == 1 else 1)
        table.append(tuple(row))
    return tuple(table)


def _native_ready(symbol: str) -> bool:
    """True iff the native lib is loaded AND exports ``symbol`` (numpy-free)."""
    return bool(
        _native.HAS_NATIVE and _native.LIB is not None
        and hasattr(_native.LIB, symbol)
    )


def _check_element(q: int, op: str) -> int:
    """Coerce ``q`` to an ``int`` and assert it is a valid Q8 element (0..7)."""
    qi = int(q)
    if not (0 <= qi < _Q8_N):
        raise ValueError(
            f"{op}: a Q8 element must be an int in [0, 8); got {q!r}"
        )
    return qi


def _as_q8_buffer(buf: Sequence[int], op: str, name: str) -> bytes:
    """Coerce ``buf`` to ``bytes`` of valid Q8 elements (numpy-free).

    Accepts any 1-D sequence of ints (``bytes`` / ``bytearray`` / ``list`` /
    ``tuple``); every element must be a valid Q8 byte (0..7). Returns a
    ``bytes`` object so the native and pure paths consume the identical
    buffer (the parity contract)."""
    try:
        out = bytes(_check_element(b, op) for b in buf)
    except TypeError as exc:  # non-iterable
        raise ValueError(
            f"{op}: {name} must be a 1-D sequence of Q8 bytes; got {buf!r}"
        ) from exc
    return out


def q8_mult(a: int, b: int) -> int:
    """The Q₈ group product ``a · b`` of two Q₈ bytes (the discrete peer of the
    ``ℍ`` Hamilton product).

    ``(s_a · e_{x_a})(s_b · e_{x_b}) = (s_a ⊕ s_b ⊕ F[x_a][x_b]) · e_{x_a ⊕ x_b}``
    with ``x = q & 3`` the ``V4`` coset, ``s = q >> 2`` the center sign, and
    ``F`` the Cayley–Dickson cocycle (:func:`_build_f_table`). NON-abelian
    (``q8_mult(1, 2) == 3`` but ``q8_mult(2, 1) == 7``); ``0`` is the identity;
    ``i² = j² = k² = 4`` (``−1``). The abelian projection is exact:
    ``(q8_mult(a, b) & 3) == ((a & 3) ⊕ (b & 3))``.

    Class M (group bind) ∘ Class I (the ``V4`` XOR + the ``Z₂`` sign ⊕; no
    ``abs()``). Dispatches to the same-rc C peer ``srmech_q8_mult`` (byte-exact
    pure fallback otherwise).

    Args:
        a: A Q₈ element (int in ``[0, 8)``).
        b: A Q₈ element (int in ``[0, 8)``).

    Returns:
        The product ``a · b`` as a Q₈ byte (int in ``[0, 8)``).

    Raises:
        ValueError: if ``a`` or ``b`` is not a valid Q₈ element.
    """
    ai = _check_element(a, "q8_mult")
    bi = _check_element(b, "q8_mult")
    if _native_ready("srmech_q8_mult"):
        return int(_native.LIB.srmech_q8_mult(
            ctypes.c_uint8(ai), ctypes.c_uint8(bi)))
    f = _build_f_table()
    xa, xb = ai & 3, bi & 3
    sign = (ai >> 2) ^ (bi >> 2) ^ f[xa][xb]
    return (sign << 2) | (xa ^ xb)


def q8_conjugate(a: int) -> int:
    """The Q₈ conjugate / group inverse ``conj(a)``.

    ``conj(a) = a`` for the center (coset ``0``, self-inverse), else
    ``a ⊕ 4`` (flip an imaginary coset's sign bit). It is the group inverse:
    ``q8_mult(a, q8_conjugate(a)) == 0`` for every ``a`` (and likewise on the
    left). Class C (chirality / orientation); a plain sign-bit flip (no
    ``abs()``), the discrete mirror of
    :func:`srmech.physics.qm.quaternion.quaternion_conjugate`. Dispatches to the
    same-rc C peer ``srmech_q8_conjugate`` (byte-exact pure fallback).

    Args:
        a: A Q₈ element (int in ``[0, 8)``).

    Returns:
        The conjugate ``conj(a)`` as a Q₈ byte.

    Raises:
        ValueError: if ``a`` is not a valid Q₈ element.
    """
    ai = _check_element(a, "q8_conjugate")
    if _native_ready("srmech_q8_conjugate"):
        return int(_native.LIB.srmech_q8_conjugate(ctypes.c_uint8(ai)))
    return ai if (ai & 3) == 0 else ai ^ 4


def q8_bind(turn: Sequence[int], one: Sequence[int]) -> bytes:
    """Elementwise Q₈ bind ``out[i] = q8_mult(turn[i], one[i])`` over two
    equal-length Q₈ byte buffers.

    The buffer form of :func:`q8_mult` — the discrete peer of a per-slot ``ℍ``
    bind. ``turn`` and ``one`` are any 1-D sequences of Q₈ bytes (``bytes`` /
    ``bytearray`` / ``list``) of equal length; the result is ``bytes``. Class M
    (group bind). Dispatches to the same-rc C peer ``srmech_q8_bind`` (which
    documents the same out-aliasing contract; byte-exact pure fallback).

    Args:
        turn: The left operand buffer (the "which-way" factor; Class C intent).
        one: The right operand buffer (the identity-anchored factor).

    Returns:
        The elementwise product as ``bytes`` of length ``len(turn)``.

    Raises:
        ValueError: on a length mismatch or a non-Q₈ byte.
    """
    t = _as_q8_buffer(turn, "q8_bind", "turn")
    o = _as_q8_buffer(one, "q8_bind", "one")
    if len(t) != len(o):
        raise ValueError(
            f"q8_bind: turn and one must be equal length; got {len(t)} and "
            f"{len(o)}"
        )
    n = len(t)
    if n and _native_ready("srmech_q8_bind"):
        c_turn = (ctypes.c_uint8 * n).from_buffer_copy(t)
        c_one = (ctypes.c_uint8 * n).from_buffer_copy(o)
        c_out = (ctypes.c_uint8 * n)()
        rc = _native.LIB.srmech_q8_bind(c_turn, c_one, ctypes.c_uint32(n), c_out)
        if rc == _native.SRMECH_OK:
            return bytes(c_out)
    f = _build_f_table()
    out = bytearray(n)
    for i in range(n):
        a, b = t[i], o[i]
        xa, xb = a & 3, b & 3
        sign = (a >> 2) ^ (b >> 2) ^ f[xa][xb]
        out[i] = (sign << 2) | (xa ^ xb)
    return bytes(out)


def q8_project_v4(q: Sequence[int]) -> bytes:
    """The abelian projection ``π: Q₈ → V4`` elementwise: ``out[i] = q[i] & 3``.

    Drops the center sign bit, keeping the ``{1, i, j, k}`` coset — the exact
    F380 / R21 homomorphism onto ``klein4``'s value algebra
    (``π(q8_mult(a, b)) == klein4_bind(π(a), π(b))``, tested). ``q`` is any 1-D
    sequence of Q₈ bytes; the result is ``bytes``. Class I (the abelian coset
    read). Dispatches to the same-rc C peer ``srmech_q8_project_v4`` (byte-exact
    pure fallback).

    Args:
        q: A Q₈ byte buffer (``bytes`` / ``bytearray`` / ``list``).

    Returns:
        The ``V4`` cosets as ``bytes`` (each in ``{0, 1, 2, 3}``).

    Raises:
        ValueError: on a non-Q₈ byte.
    """
    qb = _as_q8_buffer(q, "q8_project_v4", "q")
    n = len(qb)
    if n and _native_ready("srmech_q8_project_v4"):
        c_q = (ctypes.c_uint8 * n).from_buffer_copy(qb)
        c_out = (ctypes.c_uint8 * n)()
        rc = _native.LIB.srmech_q8_project_v4(c_q, ctypes.c_uint32(n), c_out)
        if rc == _native.SRMECH_OK:
            return bytes(c_out)
    return bytes(b & 3 for b in qb)


def q8_from_one(one, D: int) -> "_HV":
    """**ONE-OCT** — the ``One``'s Q₈ coupling projection: the Q₈ analogue of
    :func:`srmech.math.hdc.klein4_from_one` (§Q8 completeness / rc315).

    Mints the ``sectors=8`` (OCT) coupling ``one`` of leaf dimension ``D`` — a
    Q₈-valued coupling ``bytes ∈ {0..7}`` — so a downstream caller can build a
    SUBSTRATE (Q₈) genome (``chromosome`` / ``mint_strand`` / ``recall`` with
    ``element_type=ELEMENT_TYPE_Q8``) WITHOUT hand-constructing the OCT ``one``. Two
    declared planes, both functions of the ``One``'s three canonical constructor
    integers (``sigma`` / ``theta=(num, den)`` / ``terms``):

    1. **The V4 coset plane** (bits ``0..1``, ``q & 3``) — EXACTLY
       :func:`~srmech.math.hdc.klein4_from_one`'s output on the same ``one``. This is
       the BACKWARD-FAITHFUL bridge, guaranteed BY CONSTRUCTION::

           q8_project_v4(q8_from_one(one, D)) == klein4_from_one(one, D)

       — the F380 / R21 homomorphism ``π: Q₈ → V4`` composed with the minter, so a
       Q₈ genome's V4 shadow is byte-identical to the Klein-4 genome it extends.
    2. **The Z₂ sign plane** (bit ``2``, ``q >> 2``) — a DOMAIN-SEPARATED Class-A
       address of the SAME ``One`` (:func:`~srmech.math.hdc.klein4_address` over a
       ``{"q8_sign": 1, …}`` preimage), taken as bit 0 per slot. So the sign is a
       DECLARED function of substrate parameters (not an undeclared draw), and the
       coupling is genuinely non-abelian (a real Q₈ ``one``, not a degenerate
       all-positive one living in the V4 subgroup). The sign is a group BIT computed
       by Class-A expansion + Class-I parity (``& 1``) — NEVER an ``abs()``.

    **Native + pure by COMPOSITION (no dedicated C symbol; ABI stays 10).** Both
    planes are the outputs of already-C-peered ops — ``srmech_klein4_from_one`` (the
    V4 plane) and ``srmech_klein4_address`` (the sign plane) — so when ``HAS_NATIVE``
    the heavy lifting runs in C and the only Python work is the trivial Class-I/M byte
    interleave ``(sign << 2) | coset``. A bare-C host mints the OCT ``one`` by the
    SAME composition (both sub-op symbols + the interleave loop), so genome-fully-in-C
    holds without a new export. Class A (both content-address planes) ∘ Class C (the
    sign chirality) ∘ Class M (the byte bind). NO ``abs()``.

    Args:
        one: A :class:`~srmech.cascade.one.One` (read structurally: any object
            exposing ``.sigma``, ``.theta`` as a ``(num, den)`` pair, and ``.terms``).
        D: Vector dimension (positive). Free — nothing requires, and nothing gains
            from, divisibility by 14 (see :func:`~srmech.math.hdc.klein4_sector_frame`).

    Returns:
        The OCT coupling ``one`` as an ``HV`` of ``sectors=8`` (bytes ``0..7``).

    Raises:
        ValueError: if ``D`` is not positive, or ``one.theta`` denominator is zero
            (refused before dispatch, the SAME input klein4_from_one refuses).
        TypeError: if ``one`` does not expose ``.sigma`` / ``.theta`` / ``.terms``.
    """
    D = int(D)
    if D <= 0:
        raise ValueError("q8.q8_from_one: D must be positive")
    # Lazy import (the same discipline _build_f_table uses for cd_basis_product): keeps
    # q8 importable before hdc is, and avoids any package-init ordering surprise.
    from srmech.math.hdc import klein4_address, klein4_from_one
    # Plane 1 — the V4 coset plane IS klein4_from_one's output (backward-faithful by
    # construction; klein4_from_one also validates .sigma/.theta/.terms + theta_den != 0).
    v4 = klein4_from_one(one, D)                       # sectors=4 HV, cosets 0..3
    try:
        sigma = int(one.sigma)
        tn, td = (int(x) for x in one.theta)
        terms = int(one.terms)
    except (AttributeError, TypeError, ValueError) as exc:
        raise TypeError(
            "q8.q8_from_one: `one` must expose .sigma, .theta=(num, den) and .terms "
            f"(a cascade One); got {type(one).__name__}") from exc
    # Plane 2 — the Z2 sign plane: a DOMAIN-SEPARATED Class-A address of the same One
    # (the "q8_sign" tag separates it from klein4_from_one's own preimage), bit 0 per
    # slot. A declared function of the substrate parameters, never an undeclared draw.
    sign_preimage = _json.dumps(
        {"q8_sign": 1, "sigma": sigma, "terms": terms, "theta": [tn, td]},
        sort_keys=True, separators=(",", ":")).encode("utf-8")
    sign = klein4_address(D, sign_preimage)            # sectors=4 HV; bit 0 = the sign
    # The Class-I/M interleave: q[i] = (sign_bit[i] << 2) | v4_coset[i]. No abs(); the
    # sign is a group ⊕-bit, the coset the abelian V4 read — exactly the q8 byte layout.
    out = bytes(((int(sign[i]) & 1) << 2) | (int(v4[i]) & 3) for i in range(D))
    return _HV.from_sequence(out, sectors=_Q8_N)       # sectors=8 (OCT)


__all__ = [
    "q8_bind",
    "q8_conjugate",
    "q8_from_one",
    "q8_mult",
    "q8_project_v4",
]
