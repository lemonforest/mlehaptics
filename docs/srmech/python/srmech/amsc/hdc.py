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


__all__ = [
    "DEFAULT_HDC_BYTES",
    "MAX_BUNDLE_N",
    "bind",
    "bundle",
    "permute",
    "similarity",
]
