"""Class M — HDC binary spatter codes (BSC).

Closes the 14-class C parity roster in srmech rc8.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: Class M is
the binding operation that uncompresses LoE-content along its compression
axis. Substrate-coupling operation in the 14-class primitive vocabulary;
**NOT** the LoE-content itself (which lives at 1D_t per the identity reading
in MFO §VII.1.2). Class C ∘ Class M composes the full LoE-uncompression
kernel — Class C iteration drives Class M binding to produce event-stream
from compressed-cascade laws-content.

Canonical SSoT (per ``[[feedback_science_is_ssot_not_project]]``):
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Rachkovskij (2001) *Representation and processing of structures with
  binary sparse distributed codes*, Neural Comput Appl 9, 322.

Operations:

- :func:`bind` — component-wise XOR; commutative, associative, self-inverse.
- :func:`bundle` — majority across an odd number of vectors.
- :func:`permute` — cyclic bit-rotation.
- :func:`similarity` — ``1 - 2 * hamming(a, b) / D`` in ``[-1, 1]``.
"""

from __future__ import annotations

import ctypes
from typing import Sequence

import numpy as np

from . import _native


# Canonical HDC dimension default. Higher D = better noise tolerance;
# 1024 bits (128 bytes) is the standard "small" canonical value per
# Kanerva 2009; production HDC typically uses 1000-10000 bits.
DEFAULT_HDC_BYTES: int = 128

MAX_BUNDLE_N: int = 257  # mirror of SRMECH_HDC_MAX_BUNDLE_N in srmech.h


def _check_pair(a: bytes, b: bytes, op: str) -> None:
    if len(a) != len(b):
        raise ValueError(
            f"hdc.{op}: vector lengths must match (got {len(a)} vs {len(b)})"
        )
    if len(a) == 0:
        raise ValueError(f"hdc.{op}: vectors must be non-empty")


def bind(a: bytes, b: bytes) -> bytes:
    """Component-wise XOR of two BSC vectors.

    Commutative: ``bind(a, b) == bind(b, a)``.
    Associative: ``bind(a, bind(b, c)) == bind(bind(a, b), c)``.
    Self-inverse: ``bind(a, bind(a, b)) == b``.

    Args:
        a, b: BSC vectors as byte strings of identical length.

    Returns:
        Bound vector (same length).

    Raises:
        ValueError: lengths differ or are zero.
    """
    _check_pair(a, b, "bind")
    n = len(a)
    if _native.HAS_NATIVE:
        out = (ctypes.c_uint8 * n)()
        a_buf = (ctypes.c_uint8 * n).from_buffer_copy(a)
        b_buf = (ctypes.c_uint8 * n).from_buffer_copy(b)
        rc = _native.LIB.srmech_hdc_bind(a_buf, b_buf, n, out)
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_hdc_bind returned status {rc}")
        return bytes(out)
    return bytes(x ^ y for x, y in zip(a, b))


def bundle(vectors: Sequence[bytes]) -> bytes:
    """Bitwise majority across an odd number of BSC vectors.

    Each output bit is the majority of the corresponding bit across all
    input vectors. BSC convention requires an odd vector count for clean
    majority; even counts raise ``ValueError`` (caller can pad with a
    deterministic tie-breaker vector).

    Args:
        vectors: Sequence of BSC vectors (all same length, non-empty,
            odd count).

    Returns:
        Bundled vector (same length as inputs).

    Raises:
        ValueError: empty sequence, even count, mismatched lengths, or
            zero-length vectors.
    """
    n_vectors = len(vectors)
    if n_vectors == 0:
        raise ValueError("hdc.bundle: vectors sequence must be non-empty")
    if (n_vectors & 1) == 0:
        raise ValueError(
            f"hdc.bundle: n_vectors must be odd (got {n_vectors})"
        )
    if n_vectors > MAX_BUNDLE_N:
        raise ValueError(
            f"hdc.bundle: n_vectors {n_vectors} exceeds MAX_BUNDLE_N {MAX_BUNDLE_N}"
        )
    n_bytes = len(vectors[0])
    if n_bytes == 0:
        raise ValueError("hdc.bundle: vectors must be non-empty")
    for i, v in enumerate(vectors):
        if len(v) != n_bytes:
            raise ValueError(
                f"hdc.bundle: vector {i} has length {len(v)}, expected {n_bytes}"
            )
    if _native.HAS_NATIVE:
        out = (ctypes.c_uint8 * n_bytes)()
        # Build the const uint8_t **vectors array.
        buf_type = ctypes.c_uint8 * n_bytes
        buffers = [buf_type.from_buffer_copy(v) for v in vectors]
        ptr_array_type = ctypes.POINTER(ctypes.c_uint8) * n_vectors
        ptr_array = ptr_array_type(
            *(ctypes.cast(b, ctypes.POINTER(ctypes.c_uint8)) for b in buffers)
        )
        rc = _native.LIB.srmech_hdc_bundle(ptr_array, n_vectors, n_bytes, out)
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_hdc_bundle returned status {rc}")
        return bytes(out)
    # Pure-Python fallback.
    threshold = (n_vectors + 1) // 2
    result = bytearray(n_bytes)
    for byte_i in range(n_bytes):
        for bit in range(8):
            count = sum((v[byte_i] >> bit) & 1 for v in vectors)
            if count >= threshold:
                result[byte_i] |= (1 << bit)
    return bytes(result)


def permute(a: bytes, rotate_bits: int) -> bytes:
    """Cyclic bit-rotation of a BSC vector by ``rotate_bits`` positions.

    Negative ``rotate_bits`` rotates the other direction. Result preserves
    ``popcount(a)`` exactly. The permutation is involution-of-its-inverse:
    ``permute(permute(a, k), -k) == a``.

    Args:
        a: BSC vector.
        rotate_bits: Number of bit positions to rotate. Reduced modulo
            ``D = 8 * len(a)``.

    Returns:
        Rotated vector (same length).

    Raises:
        ValueError: zero-length vector.
    """
    n = len(a)
    if n == 0:
        raise ValueError("hdc.permute: vector must be non-empty")
    if _native.HAS_NATIVE:
        out = (ctypes.c_uint8 * n)()
        a_buf = (ctypes.c_uint8 * n).from_buffer_copy(a)
        rc = _native.LIB.srmech_hdc_permute(a_buf, n, rotate_bits, out)
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_hdc_permute returned status {rc}")
        return bytes(out)
    # Pure-Python fallback.
    D = n * 8
    eff = rotate_bits % D
    out = bytearray(n)
    for i in range(D):
        src = (i - eff) % D
        bit_value = (a[src // 8] >> (src % 8)) & 1
        if bit_value:
            out[i // 8] |= (1 << (i % 8))
    return bytes(out)


def similarity(a: bytes, b: bytes) -> float:
    """Normalized BSC similarity in ``[-1, 1]``.

    ``similarity(a, b) = 1 - 2 * hamming(a, b) / D`` where ``D = 8 * len(a)``.
    +1 = identical; 0 = orthogonal (Hamming distance D/2); -1 = bit-complementary.

    Args:
        a, b: BSC vectors of identical length.

    Returns:
        Similarity in ``[-1, 1]``.

    Raises:
        ValueError: lengths differ or are zero.
    """
    _check_pair(a, b, "similarity")
    n = len(a)
    if _native.HAS_NATIVE:
        out = ctypes.c_double(0.0)
        a_buf = (ctypes.c_uint8 * n).from_buffer_copy(a)
        b_buf = (ctypes.c_uint8 * n).from_buffer_copy(b)
        rc = _native.LIB.srmech_hdc_similarity(
            a_buf, b_buf, n, ctypes.byref(out)
        )
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_hdc_similarity returned status {rc}")
        return out.value
    # Pure-Python fallback.
    D = n * 8
    hamming = sum(bin(x ^ y).count("1") for x, y in zip(a, b))
    return 1.0 - 2.0 * hamming / D


# ---------------------------------------------------------------------------
# Polar {-1, 0, +1} variant — rank-1 Class M with an *absorbing* zero
# (Class M ∘ Class K). Per UPSTREAM_NOTES §5 +
# ``[[user_stance_canonical_two_variant_dial_class_m]]``.
#
# Distinct from the bipolar byte-packed BSC above: a polar hypervector is an
# int8 array with elements in {-1, 0, +1}, where 0 is the asymptotic-DOF
# "dead-band / uncertain" state the Class-K pin-slot rejects (per
# ``[[user_stance_asymptotic_dof_sidesteps_infinity]]``). Bind is the
# multiplicative sign-product (0 absorbing); bundle is the sticky majority
# (ties resolve to 0). The 0 is the pin-slot-at-zero made a first-class state,
# so the sign axis is no longer crippled by a missing origin.
#
# Class M variant ladder (UPSTREAM_NOTES §5.1):
#   bipolar  {-1,+1}     F₂ sign-product            (bind/bundle/permute/similarity above)
#   polar    {-1,0,+1}   sign-product, 0 absorbing  (this block)
#   klein-4  (Z₂)²       component-wise XOR          (planned)
#
# Representation note: polar ops use int8 {-1,0,+1} arrays (numpy), NOT the
# bit-packed bytes of the bipolar BSC surface. Native C dispatch for the polar
# ops is wired alongside the C surface in this rc; until then the numpy
# reference path runs.
# ---------------------------------------------------------------------------

POLAR_STATES = (-1, 0, 1)


def _as_polar(v, op: str):
    arr = np.asarray(v, dtype=np.int8)
    if arr.ndim != 1:
        raise ValueError(f"hdc.{op}: polar vector must be 1-D (got ndim {arr.ndim})")
    if arr.size == 0:
        raise ValueError(f"hdc.{op}: polar vector must be non-empty")
    if not bool(np.isin(arr, (-1, 0, 1)).all()):
        raise ValueError(f"hdc.{op}: polar elements must be in {{-1, 0, +1}}")
    return arr


def _check_polar_pair(a, b, op: str):
    a = _as_polar(a, op)
    b = _as_polar(b, op)
    if a.shape != b.shape:
        raise ValueError(
            f"hdc.{op}: vector lengths must match (got {a.size} vs {b.size})"
        )
    return a, b


def polar_random(D: int, rng=None):
    """Random polar hypervector of dimension ``D`` with elements in {-1, 0, +1}.

    Args:
        D: Vector dimension (positive).
        rng: Optional ``numpy.random.Generator``; a fresh default is used if
            omitted.

    Returns:
        ``int8`` array of shape ``(D,)`` with elements drawn uniformly from
        ``{-1, 0, +1}``.
    """
    if D <= 0:
        raise ValueError("hdc.polar_random: D must be positive")
    if rng is None:
        rng = np.random.default_rng()
    return rng.integers(-1, 2, size=D, dtype=np.int8)


def polar_bind(a, b):
    """Polar bind: element-wise sign-product with 0 **absorbing**.

    ``bind(a, b)[i] = a[i] * b[i]``. On the ±1 sub-alphabet this is the same
    sign-product as bipolar bind (commutative, associative, self-inverse). The
    0 state is absorbing — ``0 * x = 0`` — so an "uncertain" (dead-band)
    position stays uncertain after binding.
    """
    a, b = _check_polar_pair(a, b, "polar_bind")
    return (a * b).astype(np.int8)


def polar_unbind(c, a):
    """Polar unbind: ``unbind(c, a)[i] = c[i] * a[i]`` (the same sign-product).

    Self-inverse on the ±1 sub-alphabet (``a * a = 1``), so
    ``unbind(bind(a, b), a) == b`` wherever ``a[i] != 0``. Where ``a[i] == 0``
    the original is **not** recoverable (0 is destructive) — matching the
    dead-band semantics: anything bound through an uncertain position is gone.
    """
    c, a = _check_polar_pair(c, a, "polar_unbind")
    return (c * a).astype(np.int8)


def polar_bundle(*vectors):
    """Polar bundle: sticky majority across vectors; ties resolve to 0.

    Per-position ``sign(sum_i v_i)`` — positive sum → +1, negative → -1, exact
    tie (sum == 0, including all-zero) → **0**. Unlike bipolar bundle, no
    odd-count restriction is needed: the 0 state absorbs ties as a first-class
    "uncertain" output rather than forcing a hard ±1 choice.

    Raises:
        ValueError: empty call or mismatched lengths.
    """
    if len(vectors) == 0:
        raise ValueError("hdc.polar_bundle: requires at least one vector")
    arrs = [_as_polar(v, "polar_bundle") for v in vectors]
    n = arrs[0].size
    for i, arr in enumerate(arrs):
        if arr.size != n:
            raise ValueError(
                f"hdc.polar_bundle: vector {i} has length {arr.size}, expected {n}"
            )
    total = np.sum(np.stack(arrs).astype(np.int32), axis=0)
    return np.sign(total).astype(np.int8)


def polar_similarity(a, b, skip_zero: bool = True) -> float:
    """Polar match-fraction similarity.

    ``skip_zero=True`` (default): match-fraction over only the positions where
    **both** vectors are non-zero (0 = "no information", excluded). Returns
    ``0.0`` when there are no jointly-informative positions.

    ``skip_zero=False``: plain match-fraction over all positions (``0 == 0``
    counts as a match — neutral-credit semantics).
    """
    a, b = _check_polar_pair(a, b, "polar_similarity")
    if skip_zero:
        mask = (a != 0) & (b != 0)
        n = int(mask.sum())
        if n == 0:
            return 0.0
        return float((a[mask] == b[mask]).sum()) / n
    return float((a == b).mean())


def polar_density(v) -> float:
    """Fraction of non-zero (informative) positions — substrate attestation.

    ``1.0`` = fully bipolar (no dead-band); lower = more positions resting in
    the Class-K dead-band / uncertain state.
    """
    arr = _as_polar(v, "polar_density")
    return float((arr != 0).mean())


def polar_from_real(arr, threshold: float = 0.0, dead_band: float = 0.0):
    """Bridge real-valued data into a polar HDC vector via ``sign_quantise``.

    Wraps :func:`srmech.signal_processing.path_b_ops.sign_quantise.op` — the
    existing Class-K threshold projection — and lifts its ``{-1, 0, +1}`` output
    into the ``amsc.hdc`` namespace. With ``dead_band > 0`` the near-threshold
    zone maps to 0 (the asymptotic-DOF pin-slot rejection zone); with
    ``dead_band == 0`` the output is strict bipolar (ties favour +1 per
    ``sign_quantise``).
    """
    from ..signal_processing.path_b_ops import sign_quantise

    out = sign_quantise.op(arr, threshold=threshold, dead_band=dead_band)
    return np.asarray(out, dtype=np.int8)


# ---------------------------------------------------------------------------
# Klein-4 {0,1,2,3} variant — rank-2 abelian Class M over (F₂)² = Z₂×Z₂.
# Per UPSTREAM_NOTES §4 + ``[[user_stance_canonical_two_variant_dial_class_m]]``.
#
# The next rung of the Class-M variant ladder above polar: each position holds
# a 2-bit value (4 states), decomposed as state = γ₅_bit·2 + iω₇_bit. The four
# states map to the four chirality sectors of the MFO §VII.4.1.7 4-way
# (γ₅, iω₇) decomposition:
#   0 = (+1,+1) visible matter   1 = (+1,−1) dark antimatter
#   2 = (−1,+1) visible antimatter  3 = (−1,−1) dark matter
# This is the "quad" (quaternary, DNA-like) substrate; it carries BOTH
# chirality axes where bipolar/polar carry only one. Bind = component-wise
# (F₂)²-XOR; self-inverse, abelian, associative, identity (0,0). uint8 repr.
# ---------------------------------------------------------------------------

KLEIN4_STATES = (0, 1, 2, 3)


def _as_klein4(v, op: str):
    arr = np.asarray(v, dtype=np.uint8)
    if arr.ndim != 1:
        raise ValueError(f"hdc.{op}: klein-4 vector must be 1-D (got ndim {arr.ndim})")
    if arr.size == 0:
        raise ValueError(f"hdc.{op}: klein-4 vector must be non-empty")
    if not bool(np.isin(arr, (0, 1, 2, 3)).all()):
        raise ValueError(f"hdc.{op}: klein-4 elements must be in {{0, 1, 2, 3}}")
    return arr


def klein4_random(D: int, rng=None):
    """Random Klein-4 hypervector of dimension ``D`` with elements in {0,1,2,3}."""
    if D <= 0:
        raise ValueError("hdc.klein4_random: D must be positive")
    if rng is None:
        rng = np.random.default_rng()
    return rng.integers(0, 4, size=D, dtype=np.uint8)


def klein4_bind(a, b):
    """Klein-4 bind: component-wise (F₂)²-XOR. Commutative, associative,
    self-inverse (``bind(a, bind(a, b)) == b``); identity is 0."""
    a = _as_klein4(a, "klein4_bind")
    b = _as_klein4(b, "klein4_bind")
    if a.shape != b.shape:
        raise ValueError(
            f"hdc.klein4_bind: lengths must match (got {a.size} vs {b.size})"
        )
    return np.bitwise_xor(a, b).astype(np.uint8)


def klein4_unbind(c, a):
    """Klein-4 unbind: self-inverse XOR, so ``unbind(bind(a, b), a) == b``."""
    return klein4_bind(c, a)


def klein4_bundle(*vectors):
    """Klein-4 bundle: per-bit majority vote on each of the 2 bits
    independently. Exact ties (count == n/2) resolve to 0 for that bit."""
    if len(vectors) == 0:
        raise ValueError("hdc.klein4_bundle: requires at least one vector")
    arrs = [_as_klein4(v, "klein4_bundle") for v in vectors]
    n = arrs[0].size
    for i, arr in enumerate(arrs):
        if arr.size != n:
            raise ValueError(
                f"hdc.klein4_bundle: vector {i} has length {arr.size}, expected {n}"
            )
    stack = np.stack(arrs)
    half = len(vectors) // 2
    bit0 = (np.bitwise_and(stack, 1).sum(axis=0) > half).astype(np.uint8)
    bit1 = (np.right_shift(stack, 1).sum(axis=0) > half).astype(np.uint8)
    return (bit1 * 2 + bit0).astype(np.uint8)


def klein4_similarity(a, b) -> float:
    """Klein-4 similarity: fraction of positions where ``a == b`` (0 = orthogonal,
    1 = identical). All four states are informative — there is no skip state."""
    a = _as_klein4(a, "klein4_similarity")
    b = _as_klein4(b, "klein4_similarity")
    if a.shape != b.shape:
        raise ValueError(
            f"hdc.klein4_similarity: lengths must match (got {a.size} vs {b.size})"
        )
    return float((a == b).mean())


def klein4_chirality_flip_gamma5(v):
    """Flip the γ₅ axis: XOR with the bit-1 sector mask (2)."""
    return np.bitwise_xor(_as_klein4(v, "klein4_chirality_flip_gamma5"), 2).astype(np.uint8)


def klein4_chirality_flip_omega7(v):
    """Flip the iω₇ axis: XOR with the bit-0 sector mask (1)."""
    return np.bitwise_xor(_as_klein4(v, "klein4_chirality_flip_omega7"), 1).astype(np.uint8)


def klein4_cpt_mirror(v):
    """CPT mirror: flip BOTH chirality axes (XOR with 3)."""
    return np.bitwise_xor(_as_klein4(v, "klein4_cpt_mirror"), 3).astype(np.uint8)


def klein4_sector_count(v):
    """Per-sector occupancy ``[n0, n1, n2, n3]`` — substrate attestation of the
    chirality-sector distribution."""
    arr = _as_klein4(v, "klein4_sector_count")
    return np.bincount(arr, minlength=4)[:4].astype(np.int64)


__all__ = [
    "DEFAULT_HDC_BYTES",
    "MAX_BUNDLE_N",
    "POLAR_STATES",
    "KLEIN4_STATES",
    "bind",
    "bundle",
    "permute",
    "similarity",
    "polar_random",
    "polar_bind",
    "polar_unbind",
    "polar_bundle",
    "polar_similarity",
    "polar_density",
    "polar_from_real",
    "klein4_random",
    "klein4_bind",
    "klein4_unbind",
    "klein4_bundle",
    "klein4_similarity",
    "klein4_chirality_flip_gamma5",
    "klein4_chirality_flip_omega7",
    "klein4_cpt_mirror",
    "klein4_sector_count",
]
