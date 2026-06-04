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

import concurrent.futures
import ctypes
import os
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


def polar_random(D: int, rng=None, seed: "int | None" = None):
    """Random polar hypervector of dimension ``D`` with elements in {-1, 0, +1}.

    Args:
        D: Vector dimension (positive).
        rng: Optional ``numpy.random.Generator`` for in-process Python
            callers. A ``Generator`` cannot cross JSON-RPC nor be expressed
            in an Anthropic tool schema; use ``seed`` from those callers.
        seed: Optional integer seed. When given (and ``rng`` is not), the
            generator is built internally as ``np.random.default_rng(seed)``,
            so MCP / Anthropic callers can obtain a DETERMINISTIC vector
            (srmech's bit-exact / attestation discipline). **Precedence:**
            an explicit ``rng`` wins over ``seed`` if both are supplied.

    Returns:
        ``int8`` array of shape ``(D,)`` with elements drawn uniformly from
        ``{-1, 0, +1}``.
    """
    if D <= 0:
        raise ValueError("hdc.polar_random: D must be positive")
    if rng is None:
        rng = np.random.default_rng(seed)
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


def klein4_random(D: int, rng=None, seed: "int | None" = None):
    """Random Klein-4 hypervector of dimension ``D`` with elements in {0,1,2,3}.

    Args:
        D: Vector dimension (positive).
        rng: Optional ``numpy.random.Generator`` for in-process Python
            callers. A ``Generator`` cannot cross JSON-RPC nor be expressed
            in an Anthropic tool schema; use ``seed`` from those callers.
        seed: Optional integer seed. When given (and ``rng`` is not), the
            generator is built internally as ``np.random.default_rng(seed)``,
            so MCP / Anthropic callers can obtain a DETERMINISTIC vector
            (srmech's bit-exact / attestation discipline). **Precedence:**
            an explicit ``rng`` wins over ``seed`` if both are supplied.
    """
    if D <= 0:
        raise ValueError("hdc.klein4_random: D must be positive")
    if rng is None:
        rng = np.random.default_rng(seed)
    return rng.integers(0, 4, size=D, dtype=np.uint8)


# ── Klein-4 sector / chunk parallel dispatch (v0.6.0rc13; §11.3) ──────────
#
# The klein4_* ops gain an optional ``sectors=`` / ``parallel=`` / ``mode=``
# flag that runs the op across ``n_sectors`` (≤4) lanes concurrently
# (``ThreadPoolExecutor``; GIL-releasing numpy bodies overlap). TWO modes:
#
#   mode="chunk"     — DATA-PARALLEL: split the D-length vector(s) into
#                      ``n_sectors`` contiguous position-slices, run the op
#                      per slice on its own thread, concatenate. BIT-IDENTICAL
#                      to the serial op (the value-preserving DEFAULT).
#   mode="chirality" — F233 4-SECTOR: conjugate the body by each of the ≤4
#                      Klein-4 chirality-sector flips ``T_s`` — the klein4
#                      vector's OWN XOR-flips (NOT the signed-real cascade
#                      transforms): s=0 identity, s=1 iω₇ (XOR 1), s=2 γ₅
#                      (XOR 2), s=3 CPT (XOR 3); each an involution, so the
#                      sector dual is ``T_s(body(T_s(v)))``. Recombine:
#                      bind/bundle → ``klein4_bundle`` of the ≤4 duals;
#                      similarity → sector-0 (value-transparent).
#
# Default-ON when ``os.cpu_count() >= 4`` (sectors=None → 4, else 1). With the
# chunk default every op is value-preserving, so default-on changes only the
# EXECUTION path, never the result.
#
# CO-EQUAL PARITY (``[[feedback_c_python_co_equal_parity_not_callback]]``):
# this is self-contained Python orchestration over the pure-Python/numpy
# klein4 ops — it does NOT route through the C peer, and a standalone-C
# klein4 sector dispatch (a C dispatch running C bodies, NEVER a Python
# callback) is the tracked C-parity follow-up. No ``abs()`` (XOR / majority).

#: Klein-4 sector XOR-flip masks, indexed by sector 0..3 — matching the F233
#: SECTOR_LABELS order (0=(+,+) identity, 1=(+,−) iω₇, 2=(−,+) γ₅, 3=(−,−) CPT).
_KLEIN4_SECTOR_MASKS = (0, 1, 2, 3)


def _klein4_default_sectors() -> int:
    """Default-on policy: 4 sectors when the machine has ≥4 cores, else 1."""
    cores = os.cpu_count() or 1
    assert cores >= 1, "os.cpu_count() must be positive"
    return 4 if cores >= 4 else 1


def _klein4_resolve_sectors(sectors, parallel) -> int:
    """Resolve the lane count from ``sectors=`` / ``parallel=`` (→ 1..4).

    ``sectors`` (int 1..4) wins; else ``parallel`` (True→4 / False→1); else the
    default-on policy. ``sectors=1`` is the plain serial op.
    """
    if sectors is not None:
        if not isinstance(sectors, int) or isinstance(sectors, bool):
            raise ValueError(
                f"klein4: sectors must be an int in 1..4; got {sectors!r}"
            )
        if sectors < 1 or sectors > 4:
            raise ValueError(f"klein4: sectors must be in 1..4; got {sectors}")
        return sectors
    if parallel is True:
        return 4
    if parallel is False:
        return 1
    return _klein4_default_sectors()


def _klein4_chunk_apply(per_slice, arrs, n_sectors):
    """Data-parallel: split equal-length ``arrs`` into ``n_sectors`` contiguous
    column-slices, run ``per_slice(tuple-of-slices)`` on a thread each, concat.

    Bit-identical to the serial op (the slices partition the positions). Falls
    back to a single serial call when ``n_sectors <= 1`` or the vector is
    shorter than the lane count.
    """
    n = arrs[0].size
    assert all(a.size == n for a in arrs), "klein4 chunk: arrays must share length"
    if n_sectors <= 1 or n < n_sectors:
        return per_slice(arrs)
    bounds = [(i * n) // n_sectors for i in range(n_sectors + 1)]
    slabs = [
        tuple(a[bounds[k]:bounds[k + 1]] for a in arrs) for k in range(n_sectors)
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        parts = list(ex.map(per_slice, slabs))
    return np.concatenate(parts).astype(np.uint8)


def _klein4_sector_flip(s, v):
    """Apply the Klein-4 sector flip ``T_s`` (an involution: XOR with mask s)."""
    m = _KLEIN4_SECTOR_MASKS[s]
    return v if m == 0 else np.bitwise_xor(v, m).astype(np.uint8)


def _klein4_chirality_duals(body, v, n_sectors):
    """Return the ≤4 sector duals ``T_s(body(T_s(v)))`` (ThreadPool; F233)."""
    def _dual(s):
        return _klein4_sector_flip(s, body(_klein4_sector_flip(s, v)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        return list(ex.map(_dual, range(n_sectors)))


def _klein4_bundle_core(arrs):
    """Per-bit majority vote over a list of equal-length klein4 arrays (the
    serial bundle kernel; the public :func:`klein4_bundle` wraps it)."""
    n = arrs[0].size
    for i, arr in enumerate(arrs):
        if arr.size != n:
            raise ValueError(
                f"hdc.klein4_bundle: vector {i} has length {arr.size}, expected {n}"
            )
    stack = np.stack(arrs)
    half = len(arrs) // 2
    bit0 = (np.bitwise_and(stack, 1).sum(axis=0) > half).astype(np.uint8)
    bit1 = (np.right_shift(stack, 1).sum(axis=0) > half).astype(np.uint8)
    return (bit1 * 2 + bit0).astype(np.uint8)


def klein4_bind(a, b, *, sectors=None, parallel=None, mode="chunk"):
    """Klein-4 bind: component-wise (F₂)²-XOR. Commutative, associative,
    self-inverse (``bind(a, bind(a, b)) == b``); identity is 0.

    The rc13 ``sectors=`` / ``parallel=`` / ``mode=`` flag fans the bind across
    ≤4 concurrent lanes (default-ON at ≥4 cores; see the module note above).
    ``mode="chunk"`` (default) is data-parallel + bit-identical; ``mode=
    "chirality"`` runs the F233 4-sector dispatch (which for XOR collapses to
    the same vector, so it is value-transparent + carries the 4-way
    independence). No ``abs()``.
    """
    a = _as_klein4(a, "klein4_bind")
    b = _as_klein4(b, "klein4_bind")
    if a.shape != b.shape:
        raise ValueError(
            f"hdc.klein4_bind: lengths must match (got {a.size} vs {b.size})"
        )
    n_sectors = _klein4_resolve_sectors(sectors, parallel)
    if n_sectors <= 1:
        return np.bitwise_xor(a, b).astype(np.uint8)
    if mode == "chunk":
        return _klein4_chunk_apply(
            lambda sl: np.bitwise_xor(sl[0], sl[1]).astype(np.uint8), (a, b), n_sectors
        )
    if mode == "chirality":
        duals = _klein4_chirality_duals(
            lambda x: np.bitwise_xor(x, b).astype(np.uint8), a, n_sectors
        )
        return _klein4_bundle_core(duals)
    raise ValueError(
        f"klein4_bind: mode must be 'chunk' or 'chirality'; got {mode!r}"
    )


def klein4_unbind(c, a):
    """Klein-4 unbind: self-inverse XOR, so ``unbind(bind(a, b), a) == b``."""
    return klein4_bind(c, a)


def klein4_bundle(*vectors, sectors=None, parallel=None, mode="chunk"):
    """Klein-4 bundle: per-bit majority vote on each of the 2 bits
    independently. Accepts ANY number of vectors ``n >= 1`` (even OR odd —
    there is NO odd-only requirement). A bit is set only when its 1-count
    is strictly greater than ``n // 2``, so an exact tie (``count == n/2``,
    possible only for even ``n``) deterministically resolves to 0 for that
    bit.

    The rc13 ``sectors=`` / ``parallel=`` / ``mode=`` flag fans the reduction
    across ≤4 concurrent lanes (default-ON at ≥4 cores). ``mode="chunk"``
    (default) splits the positions → BIT-IDENTICAL to the serial bundle;
    ``mode="chirality"`` runs the F233 4-sector dispatch (bundle the
    ``T_s``-conjugated inputs, ``inv_T_s`` each, then ``klein4_bundle`` the
    ≤4) — meaningful only for chirality-asymmetric input sets. No ``abs()``.
    """
    if len(vectors) == 0:
        raise ValueError("hdc.klein4_bundle: requires at least one vector")
    arrs = [_as_klein4(v, "klein4_bundle") for v in vectors]
    n_sectors = _klein4_resolve_sectors(sectors, parallel)
    if n_sectors <= 1 or mode == "chunk":
        if n_sectors <= 1:
            return _klein4_bundle_core(arrs)
        # chunk: split positions, majority-vote each slab, concat (bit-exact).
        n = arrs[0].size
        for i, arr in enumerate(arrs):
            if arr.size != n:
                raise ValueError(
                    f"hdc.klein4_bundle: vector {i} has length {arr.size}, "
                    f"expected {n}"
                )
        if n < n_sectors:
            return _klein4_bundle_core(arrs)
        bounds = [(i * n) // n_sectors for i in range(n_sectors + 1)]

        def _vote(k):
            return _klein4_bundle_core([a[bounds[k]:bounds[k + 1]] for a in arrs])

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            parts = list(ex.map(_vote, range(n_sectors)))
        return np.concatenate(parts).astype(np.uint8)
    if mode == "chirality":
        def _sector_bundle(s):
            conj = [_klein4_sector_flip(s, a) for a in arrs]
            return _klein4_sector_flip(s, _klein4_bundle_core(conj))

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            duals = list(ex.map(_sector_bundle, range(n_sectors)))
        return _klein4_bundle_core(duals)
    raise ValueError(
        f"klein4_bundle: mode must be 'chunk' or 'chirality'; got {mode!r}"
    )


def klein4_similarity(a, b, *, sectors=None, parallel=None, mode="chunk") -> float:
    """Klein-4 similarity: fraction of positions where ``a == b`` (0 = orthogonal,
    1 = identical). All four states are informative — there is no skip state.

    The rc13 ``sectors=`` / ``parallel=`` / ``mode=`` flag fans the comparison
    across ≤4 concurrent lanes (default-ON at ≥4 cores) and ALWAYS returns the
    same float as the serial op. ``mode="chunk"`` (default) splits the
    positions and sums per-slice match counts (bit-identical); ``mode=
    "chirality"`` runs the F233 4-sector dispatch and recombines via
    **sector-0** (value-transparent — XOR-flipping both sides preserves
    equality, so every sector equals the plain similarity anyway).
    """
    a = _as_klein4(a, "klein4_similarity")
    b = _as_klein4(b, "klein4_similarity")
    if a.shape != b.shape:
        raise ValueError(
            f"hdc.klein4_similarity: lengths must match (got {a.size} vs {b.size})"
        )
    n_sectors = _klein4_resolve_sectors(sectors, parallel)
    n = a.size
    if n_sectors <= 1 or n == 0:
        return float((a == b).mean())
    if mode == "chunk":
        if n < n_sectors:
            return float((a == b).mean())
        bounds = [(i * n) // n_sectors for i in range(n_sectors + 1)]

        def _matches(k):
            return int((a[bounds[k]:bounds[k + 1]] == b[bounds[k]:bounds[k + 1]]).sum())

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            counts = list(ex.map(_matches, range(n_sectors)))
        return float(sum(counts) / n)
    if mode == "chirality":
        def _sector_sim(s):
            return float(
                (_klein4_sector_flip(s, a) == _klein4_sector_flip(s, b)).mean()
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            sims = list(ex.map(_sector_sim, range(n_sectors)))
        return sims[0]  # sector-0 — value-transparent recombine
    raise ValueError(
        f"klein4_similarity: mode must be 'chunk' or 'chirality'; got {mode!r}"
    )


def klein4_chirality_flip_gamma5(v):
    """Flip the γ₅ axis: XOR with the bit-1 sector mask (2)."""
    return np.bitwise_xor(_as_klein4(v, "klein4_chirality_flip_gamma5"), 2).astype(np.uint8)


def klein4_chirality_flip_omega7(v):
    """Flip the iω₇ axis: XOR with the bit-0 sector mask (1)."""
    return np.bitwise_xor(_as_klein4(v, "klein4_chirality_flip_omega7"), 1).astype(np.uint8)


def klein4_cpt_mirror(v):
    """CPT mirror: flip BOTH chirality axes (XOR with 3)."""
    return np.bitwise_xor(_as_klein4(v, "klein4_cpt_mirror"), 3).astype(np.uint8)


# The order-3 triality cycle on the Klein-4 carrier (the S₃ = Aut(V₄)
# generator). The three non-identity involutions cycle iω₇(1) → γ₅(2) →
# CPT(3) → iω₇(1), fixing identity(0). Pure uint8 relabel via a length-4
# lookup; applying it three times is the identity (T∘T∘T = id; T² = T⁻¹).
_KLEIN4_TRIALITY_FORWARD = np.array([0, 2, 3, 1], dtype=np.uint8)
_KLEIN4_TRIALITY_INVERSE = np.array([0, 3, 1, 2], dtype=np.uint8)


def klein4_triality_cycle(v, *, inverse=False):
    """Cycle the three Klein-4 chirality involutions — the order-3 S₃ generator.

    The V₄-carrier image of the so(8) triality ``8v → 8s → 8c`` (see
    :func:`srmech.qm.triality.triality_cycle`): the three non-identity
    involutions cycle ``iω₇(1) → γ₅(2) → CPT(3) → iω₇(1)``, with identity(0)
    fixed. This is the order-3 generator of ``Aut(V₄) = S₃`` — the "third axis"
    (F182) that the three order-2 flips (:func:`klein4_chirality_flip_gamma5` /
    :func:`klein4_chirality_flip_omega7` / :func:`klein4_cpt_mirror`) cannot
    reach: order-3 cycling of the involutions, NOT a fourth order-2 chirality.

    Class I (cyclic order-3 permutation) — a pure uint8 relabel; no sign, no
    ``abs()``. Applying it three times returns the input (``T∘T∘T = id``);
    ``inverse=True`` is the reverse 3-cycle (``T² = T⁻¹``).

    Args:
        v: A Klein-4 hypervector (uint8 array, elements in ``{0, 1, 2, 3}``).
        inverse: If True, apply the reverse cycle ``iω₇ → CPT → γ₅ → iω₇``.

    Returns:
        The relabelled uint8 array (same shape as ``v``).
    """
    arr = _as_klein4(v, "klein4_triality_cycle")
    table = _KLEIN4_TRIALITY_INVERSE if inverse else _KLEIN4_TRIALITY_FORWARD
    return table[arr].astype(np.uint8)


def klein4_sector_count(v):
    """Per-sector occupancy ``[n0, n1, n2, n3]`` — substrate attestation of the
    chirality-sector distribution."""
    arr = _as_klein4(v, "klein4_sector_count")
    return np.bincount(arr, minlength=4)[:4].astype(np.int64)


# ---------------------------------------------------------------------------
# Holographic erasure code over the Klein-4 store (#797 op (a2); F353).
#
# The order-2 Klein-4 store is k=2-DETECT natively (F294: no Z3, 3∤4). k=3-
# CORRECT needs EITHER the order-3 triality (op (a1)) OR this holographic-
# erasure route, which supplies correction with **no Z3**. Replicate the
# store across ``replicas`` blocks: any ONE surviving replica-block (a
# ``1/replicas`` subregion) reconstructs the whole — the holographic "any
# subregion contains the whole" property at block granularity. At
# ``replicas=4``: erasure-tolerance **3/4** (known-location: drop up to 3 of
# 4 blocks) and blind correction **1/4** (unknown-location: per-position
# majority over 4 copies corrects ≤1 error). These are the F353 measured
# tolerances; the order-2 store + this code is the *measured substitute* for
# the (a1) explicit triality corrector. Class-home: M (replication bind) ∘
# C (the surviving-copy/majority selection). No abs(); pure uint8 relabel +
# count.


def klein4_holographic_encode(v, *, replicas=4):
    """Holographic erasure-encode a Klein-4 store into ``replicas`` copies.

    Returns a length ``len(v) * replicas`` uint8 store (replica-major: the
    input repeated ``replicas`` times). Any single replica-block — a
    ``1/replicas`` subregion — reconstructs the whole (#797 op (a2), F353):
    the order-2 store's k=3-CORRECT via erasure rather than the order-3
    triality (no Z3).

    Args:
        v: A Klein-4 hypervector (uint8, elements {0,1,2,3}).
        replicas: Number of redundant copies (>= 2; default 4 → 3/4
            known-erasure tolerance, 1/4 blind correction).

    Returns:
        uint8 store of length ``len(v) * replicas``.
    """
    arr = _as_klein4(v, "klein4_holographic_encode")
    if not isinstance(replicas, int) or isinstance(replicas, bool) or replicas < 2:
        raise ValueError(f"replicas must be int >= 2; got {replicas!r}")
    return np.tile(arr, replicas).astype(np.uint8)


def klein4_holographic_decode(store, *, replicas=4, erased=None):
    """Reconstruct a Klein-4 store from a holographic erasure encoding.

    Inverse of :func:`klein4_holographic_encode`. Two modes:

    * **known-location erasure** (``erased`` given) — a boolean mask over
      the store (True = erased / missing). Per original position, takes the
      first surviving replica. Recovers **exactly** as long as ≥1 replica
      survives per position — tolerates up to ``replicas-1`` of ``replicas``
      erased (= ``(replicas-1)/replicas``; **3/4** at the default). Raises
      ``ValueError`` if any position has *all* replicas erased.
    * **blind correction** (``erased`` is None) — per original position,
      majority-vote across the ``replicas`` copies (ties broken toward the
      lowest sector index). Corrects up to ``floor((replicas-1)/2)`` errors
      per position; for ``replicas=4`` that is 1 error = **1/4** blind.

    Args:
        store: uint8 store of length divisible by ``replicas``.
        replicas: The replica count used at encode time.
        erased: Optional boolean array over ``store`` (True = erased).

    Returns:
        The reconstructed length ``len(store)//replicas`` uint8 vector.
    """
    s = np.asarray(store, dtype=np.uint8)
    if s.ndim != 1:
        raise ValueError("klein4_holographic_decode: store must be 1-D")
    if not isinstance(replicas, int) or isinstance(replicas, bool) or replicas < 2:
        raise ValueError(f"replicas must be int >= 2; got {replicas!r}")
    if s.size == 0 or s.size % replicas != 0:
        raise ValueError(
            f"store length {s.size} must be a positive multiple of replicas {replicas}"
        )
    D = s.size // replicas
    blocks = s.reshape(replicas, D)
    if erased is None:
        # Blind: per-column majority over the four Klein-4 states.
        counts = np.zeros((D, 4), dtype=np.int64)
        for state in range(4):
            counts[:, state] = (blocks == state).sum(axis=0)
        return counts.argmax(axis=1).astype(np.uint8)
    # Known-location erasure: first surviving replica per column.
    mask = np.asarray(erased, dtype=bool)
    if mask.shape != s.shape:
        raise ValueError(
            f"erased mask shape {mask.shape} != store shape {s.shape}"
        )
    survives = ~mask.reshape(replicas, D)
    if not bool(survives.any(axis=0).all()):
        raise ValueError(
            "klein4_holographic_decode: a position has all replicas erased; "
            "unrecoverable (erasure exceeded (replicas-1)/replicas)"
        )
    first = survives.argmax(axis=0)        # first surviving replica per column
    return blocks[first, np.arange(D)].astype(np.uint8)


# ---------------------------------------------------------------------------
# Loop bind (Moufang) — the k=7 gauge ARITHMETIC (MS #21 / v0.7.0, #814).
#
# The octonion / Cayley-Dickson product: non-commutative AND non-associative,
# so left-order (ab)c != right-order a(bc) — the (4:3)|(3:4) chirality. This is
# the gauge *arithmetic* the triality automorphism (``klein4_triality_cycle``,
# the gauge *symmetry*) is blind to (F271). Class-home: **M** (bind) ∘ **C**
# (the left/right ordering) with a **Class-K associator RESIDUE** — NO new class
# (the 14 A–N hold; Class O stays dissolved). Structure = the **Moufang loop**
# of unit octonions (the non-associative rung above the group/ring; "loop
# replaces ring", substrate-vocabulary discipline).
#
# Canonical SSoT (``[[feedback_science_is_ssot_not_project]]``): Baez, J.C.
# (2002) "The Octonions", Bull. Amer. Math. Soc. 39, 145–205 (octonion product,
# the three Moufang identities, G₂ = Aut(𝕆) = Der(𝕆) = 14, the 7-D cross
# product + the G₂ calibration 3-form); Conway & Smith (2003) "On Quaternions
# and Octonions" (the Moufang division loop).
#
# Class-K discipline: zero-tests via the inner-product norm² ⟨v,v⟩ — never
# ``abs()``, no sign-folding (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
# rc1 is the dim-8 octonion core (division holds; Cayley-Dickson to dim 16+
# introduces zero divisors → loses unbindability). The block-octonion tiling to
# full-D hypervectors (#811 / F276) and the co-equal C peer are later voxels.
# ---------------------------------------------------------------------------

LOOP_DIM = 8  # the octonion / k=7 carrier (division holds at dim ≤ 8)


def _loop_conj_raw(arr):
    """Bare octonion conjugate (no validation; for internal recursion)."""
    y = -arr.copy()
    y[0] = arr[0]
    return y


def _loop_bind_raw(a_, b_):
    """Bare Cayley-Dickson product (no validation; the recursion engine)."""
    n = len(a_) // 2
    if n == 0:
        return a_ * b_
    a, b = a_[:n], a_[n:]
    c, d = b_[:n], b_[n:]
    return np.concatenate([_loop_bind_raw(a, c) - _loop_bind_raw(_loop_conj_raw(d), b),
                           _loop_bind_raw(d, a) + _loop_bind_raw(b, _loop_conj_raw(c))])


def _as_loop(v, op: str):
    """Coerce to a 1-D float ndarray whose length is a power of two (the
    Cayley-Dickson recursion bottoms out at length 1)."""
    arr = np.asarray(v, dtype=float)
    assert arr.ndim == 1, f"{op}: expected a 1-D vector, got ndim {arr.ndim}"
    n = arr.shape[0]
    assert n >= 1 and (n & (n - 1)) == 0, (
        f"{op}: length {n} is not a power of two (Cayley-Dickson carrier)"
    )
    return arr


def _loop_basis(i, dim):
    v = np.zeros(dim)
    v[i] = 1.0
    return v


def _reject_hd_block_misuse(arr, op):
    """Guard the single-element loop ops against silent HD-vector misuse (F-§12.1).

    ``loop_conj`` / ``loop_inv`` act on ONE Cayley-Dickson element. An HD
    block-octonion vector (a multiple of LOOP_DIM wider than one octonion)
    silently passes ``_as_loop`` — 2048 = 256·8 is also a power of two — and
    would be treated as a single 2048-D element, so the GLOBAL conj/inv is NOT
    the per-block octonion result the HD layout means (err ≈ ‖·‖, no exception).
    Raise instead, and point at the per-block ``*_hd`` op."""
    if arr.ndim == 1 and arr.size > LOOP_DIM and arr.size % LOOP_DIM == 0:
        raise ValueError(
            f"{op}: length {arr.size} is a multiple of LOOP_DIM ({LOOP_DIM}) "
            f"wider than one octonion — this is an HD block-octonion vector, "
            f"not one element. The single-element {op} is silently wrong here; "
            f"use {op}_hd for the per-block result (F-§12.1).")


# ── Native dispatch for the dim-8 octonion loop-bind family (v0.7.0rc7) ──
# The C peer (srmech_loop_*_f64 in c/src/srmech_loopbind.c) covers the
# OCTONION carrier only (n == LOOP_DIM == 8); other dims return None here and
# keep the pure-Python recursive path. The HD block wrappers (loop_bind_hd,
# ...) inherit native acceleration for free — they call the per-8-block
# loop_bind / loop_conj, which dispatch through these helpers.
_DBLP = ctypes.POINTER(ctypes.c_double)


def _loop_native_ready(symbol):
    """True iff the native lib is loaded AND exports ``symbol``."""
    return (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, symbol))


def _try_native_loop_conj(arr):
    if arr.size != LOOP_DIM or not _loop_native_ready("srmech_loop_conj_f64"):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    c_x = Arr(*(float(v) for v in arr))
    c_out = Arr()
    rc = _native.LIB.srmech_loop_conj_f64(
        ctypes.cast(c_x, _DBLP), ctypes.c_size_t(LOOP_DIM),
        ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return np.array([float(c_out[i]) for i in range(LOOP_DIM)])


def _try_native_loop_bind(a_, b_):
    if (a_.size != LOOP_DIM or b_.size != LOOP_DIM
            or not _loop_native_ready("srmech_loop_bind_f64")):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    c_x = Arr(*(float(v) for v in a_))
    c_y = Arr(*(float(v) for v in b_))
    c_out = Arr()
    rc = _native.LIB.srmech_loop_bind_f64(
        ctypes.cast(c_x, _DBLP), ctypes.cast(c_y, _DBLP),
        ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return np.array([float(c_out[i]) for i in range(LOOP_DIM)])


def _try_native_loop_bind_hd(a_, b_):
    """Whole-array native HD bind — ONE ``srmech_loop_bind_hd_f64`` call binds
    ALL NB 8-blocks (internally N-way-SIMD across blocks: AVX W=4 / SSE2 W=2 /
    scalar remainder), replacing the Python per-block ``loop_bind`` loop. a_,
    b_ are flat float arrays of equal length, a positive multiple of LOOP_DIM.
    Returns the flat result (NB·8), or None to fall back to the per-block path
    (lib absent / symbol missing / non-OK). No per-element Python loop — pointers
    cross once (this IS the F292 graft's win). ``out`` is a fresh buffer, so it
    never aliases the inputs (the C contract)."""
    n = a_.size
    if (n == 0 or n % LOOP_DIM != 0 or b_.size != n
            or not _loop_native_ready("srmech_loop_bind_hd_f64")):
        return None
    nb = n // LOOP_DIM
    xc = np.ascontiguousarray(a_, dtype=np.float64)
    yc = np.ascontiguousarray(b_, dtype=np.float64)
    out = np.empty(n, dtype=np.float64)
    rc = _native.LIB.srmech_loop_bind_hd_f64(
        xc.ctypes.data_as(_DBLP), yc.ctypes.data_as(_DBLP),
        ctypes.c_size_t(nb), out.ctypes.data_as(_DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return out


def _try_native_loop_conj_hd(a_):
    """Whole-array native HD conjugate — ONE ``srmech_loop_conj_hd_f64`` call
    conjugates ALL NB 8-blocks, replacing the Python per-block ``_loop_conj_raw``
    loop. a_ is a flat float array, a positive multiple of LOOP_DIM. Returns the
    flat result, or None to fall back (lib absent / symbol missing / non-OK)."""
    n = a_.size
    if (n == 0 or n % LOOP_DIM != 0
            or not _loop_native_ready("srmech_loop_conj_hd_f64")):
        return None
    nb = n // LOOP_DIM
    xc = np.ascontiguousarray(a_, dtype=np.float64)
    out = np.empty(n, dtype=np.float64)
    rc = _native.LIB.srmech_loop_conj_hd_f64(
        xc.ctypes.data_as(_DBLP), ctypes.c_size_t(nb), out.ctypes.data_as(_DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return out


def _try_native_loop_inv_hd(a_):
    """Whole-array native HD Moufang inverse — ONE ``srmech_loop_inv_hd_f64`` call
    inverts ALL NB 8-blocks. None on fall-back; a zero block makes the C peer
    return BAD_INPUT → None here → the Python fallback raises (the contract)."""
    n = a_.size
    if (n == 0 or n % LOOP_DIM != 0
            or not _loop_native_ready("srmech_loop_inv_hd_f64")):
        return None
    nb = n // LOOP_DIM
    xc = np.ascontiguousarray(a_, dtype=np.float64)
    out = np.empty(n, dtype=np.float64)
    rc = _native.LIB.srmech_loop_inv_hd_f64(
        xc.ctypes.data_as(_DBLP), ctypes.c_size_t(nb), out.ctypes.data_as(_DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return out


def _try_native_loop_unbind_hd(a_, b_):
    """Whole-array native HD LEFT-unbind — ONE ``srmech_loop_unbind_hd_f64`` call
    computes conj(aₖ)·bₖ over ALL NB blocks. None on fall-back."""
    n = a_.size
    if (n == 0 or n % LOOP_DIM != 0 or b_.size != n
            or not _loop_native_ready("srmech_loop_unbind_hd_f64")):
        return None
    nb = n // LOOP_DIM
    ac = np.ascontiguousarray(a_, dtype=np.float64)
    bc = np.ascontiguousarray(b_, dtype=np.float64)
    out = np.empty(n, dtype=np.float64)
    rc = _native.LIB.srmech_loop_unbind_hd_f64(
        ac.ctypes.data_as(_DBLP), bc.ctypes.data_as(_DBLP),
        ctypes.c_size_t(nb), out.ctypes.data_as(_DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return out


def _try_native_loop_runbind_hd(a_, b_):
    """Whole-array native HD RIGHT-unbind — ONE ``srmech_loop_runbind_hd_f64``
    call computes bₖ·conj(aₖ) over ALL NB blocks. None on fall-back."""
    n = a_.size
    if (n == 0 or n % LOOP_DIM != 0 or b_.size != n
            or not _loop_native_ready("srmech_loop_runbind_hd_f64")):
        return None
    nb = n // LOOP_DIM
    ac = np.ascontiguousarray(a_, dtype=np.float64)
    bc = np.ascontiguousarray(b_, dtype=np.float64)
    out = np.empty(n, dtype=np.float64)
    rc = _native.LIB.srmech_loop_runbind_hd_f64(
        ac.ctypes.data_as(_DBLP), bc.ctypes.data_as(_DBLP),
        ctypes.c_size_t(nb), out.ctypes.data_as(_DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return out


def _try_native_loop_inv(arr):
    if arr.size != LOOP_DIM or not _loop_native_ready("srmech_loop_inv_f64"):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    c_x = Arr(*(float(v) for v in arr))
    c_out = Arr()
    rc = _native.LIB.srmech_loop_inv_f64(
        ctypes.cast(c_x, _DBLP), ctypes.c_size_t(LOOP_DIM),
        ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return np.array([float(c_out[i]) for i in range(LOOP_DIM)])


def _try_native_cross7(a_, b_):
    if (a_.size != LOOP_DIM or b_.size != LOOP_DIM
            or not _loop_native_ready("srmech_cross7_f64")):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    c_x = Arr(*(float(v) for v in a_))
    c_y = Arr(*(float(v) for v in b_))
    c_out = Arr()
    rc = _native.LIB.srmech_cross7_f64(
        ctypes.cast(c_x, _DBLP), ctypes.cast(c_y, _DBLP),
        ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return np.array([float(c_out[i]) for i in range(LOOP_DIM)])


def _try_native_g2_three_form(xa, ya, za):
    if (xa.size != LOOP_DIM or ya.size != LOOP_DIM or za.size != LOOP_DIM
            or not _loop_native_ready("srmech_g2_three_form_f64")):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    c_x = Arr(*(float(v) for v in xa))
    c_y = Arr(*(float(v) for v in ya))
    c_z = Arr(*(float(v) for v in za))
    c_out = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_g2_three_form_f64(
        ctypes.cast(c_x, _DBLP), ctypes.cast(c_y, _DBLP),
        ctypes.cast(c_z, _DBLP), ctypes.c_size_t(LOOP_DIM),
        ctypes.byref(c_out))
    if rc != _native.SRMECH_OK:
        return None
    return float(c_out.value)


def _try_native_loop_associator(aa, bb, cc):
    if (aa.size != LOOP_DIM or bb.size != LOOP_DIM or cc.size != LOOP_DIM
            or not _loop_native_ready("srmech_loop_associator_f64")):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    c_a = Arr(*(float(v) for v in aa))
    c_b = Arr(*(float(v) for v in bb))
    c_c = Arr(*(float(v) for v in cc))
    c_out = Arr()
    rc = _native.LIB.srmech_loop_associator_f64(
        ctypes.cast(c_a, _DBLP), ctypes.cast(c_b, _DBLP), ctypes.cast(c_c, _DBLP),
        ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return np.array([float(c_out[i]) for i in range(LOOP_DIM)])


def _try_native_loop_left_op(arr):
    if arr.size != LOOP_DIM or not _loop_native_ready("srmech_loop_left_op_f64"):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    Mat = ctypes.c_double * (LOOP_DIM * LOOP_DIM)
    c_a = Arr(*(float(v) for v in arr))
    c_out = Mat()
    rc = _native.LIB.srmech_loop_left_op_f64(
        ctypes.cast(c_a, _DBLP), ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    flat = [float(c_out[i]) for i in range(LOOP_DIM * LOOP_DIM)]
    return np.array(flat).reshape(LOOP_DIM, LOOP_DIM)


def _try_native_loop_right_op(arr):
    if arr.size != LOOP_DIM or not _loop_native_ready("srmech_loop_right_op_f64"):
        return None
    Arr = ctypes.c_double * LOOP_DIM
    Mat = ctypes.c_double * (LOOP_DIM * LOOP_DIM)
    c_a = Arr(*(float(v) for v in arr))
    c_out = Mat()
    rc = _native.LIB.srmech_loop_right_op_f64(
        ctypes.cast(c_a, _DBLP), ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    flat = [float(c_out[i]) for i in range(LOOP_DIM * LOOP_DIM)]
    return np.array(flat).reshape(LOOP_DIM, LOOP_DIM)


def loop_conj(x):
    """Octonion conjugate x̄ — negate the imaginary part, keep the real anchor
    ``x[0]``. The Class-C orientation flip that powers the unbind. Single
    element only — an HD block-octonion vector raises (use ``loop_conj_hd``).
    Dispatches to the native ``srmech_loop_conj_f64`` for the dim-8 octonion."""
    arr = np.asarray(x, dtype=float)
    _reject_hd_block_misuse(arr, "loop_conj")
    arr = _as_loop(x, "loop_conj")
    native = _try_native_loop_conj(arr)
    if native is not None:
        return native
    return _loop_conj_raw(arr)


def loop_bind(x, y):
    """THE LOOP BIND (Moufang) = the Cayley-Dickson / octonion product.

    Non-commutative + non-associative ⟹ left-order ``(ab)c`` ≠ right-order
    ``a(bc)`` — the (4:3)|(3:4) chirality (Class C). Class **M** (bind) with the
    Class-C ordering; the non-associativity surfaces as the Class-K associator
    residue (``loop_associator``). The gauge *arithmetic* triality is blind to
    (F271). NO new class. Operands must share a power-of-two length (dim 8 = the
    octonion).
    """
    a_ = _as_loop(x, "loop_bind")
    b_ = _as_loop(y, "loop_bind")
    assert a_.shape == b_.shape, "loop_bind: operands must have equal length"
    native = _try_native_loop_bind(a_, b_)
    if native is not None:
        return native
    return _loop_bind_raw(a_, b_)


def loop_inv(x):
    """Moufang inverse x⁻¹ = x̄ / ⟨x,x⟩ — the unbind key. For a unit octonion
    (⟨x,x⟩ = 1) this is just the conjugate; ``loop_bind(x, loop_inv(x))`` = e₀.
    Class-K clean: the norm² gate, never ``abs()``. Single element only — an HD
    block-octonion vector raises (use ``loop_inv_hd``)."""
    arr = np.asarray(x, dtype=float)
    _reject_hd_block_misuse(arr, "loop_inv")
    arr = _as_loop(x, "loop_inv")
    nsq = float(np.dot(arr, arr))
    assert nsq > 0.0, "loop_inv: zero vector has no inverse (Moufang division)"
    native = _try_native_loop_inv(arr)
    if native is not None:
        return native
    return _loop_conj_raw(arr) / nsq


def loop_left_op(a):
    """Left-multiplication operator L_a(x) = a·x (the (4:3) ordering) as a
    dim×dim matrix. L_a ≠ R_a ≠ R_aᵀ — the operational chirality."""
    arr = _as_loop(a, "loop_left_op")
    dim = arr.shape[0]
    native = _try_native_loop_left_op(arr)
    if native is not None:
        return native
    return np.column_stack([_loop_bind_raw(arr, _loop_basis(k, dim)) for k in range(dim)])


def loop_right_op(a):
    """Right-multiplication operator R_a(x) = x·a (the (3:4) mirror ordering) as
    a dim×dim matrix."""
    arr = _as_loop(a, "loop_right_op")
    dim = arr.shape[0]
    native = _try_native_loop_right_op(arr)
    if native is not None:
        return native
    return np.column_stack([_loop_bind_raw(_loop_basis(k, dim), arr) for k in range(dim)])


def loop_associator(a, b, c):
    """(a·b)·c − a·(b·c) = the Class-K associator RESIDUE of the loop bind.

    Zero inside an associative (quaternionic / Fano-line) region, nonzero
    outside = the (4:3)|(3:4) boundary. Identity: ``loop_associator(a, x, b)`` =
    −(``[L_a, R_b]`` · x). The K-residue is what makes the loop bind carry order
    / nesting / direction the commutative ``klein4_bind`` XOR washes out (F274).
    """
    aa = _as_loop(a, "loop_associator")
    bb = _as_loop(b, "loop_associator")
    cc = _as_loop(c, "loop_associator")
    native = _try_native_loop_associator(aa, bb, cc)
    if native is not None:
        return native
    return (_loop_bind_raw(_loop_bind_raw(aa, bb), cc)
            - _loop_bind_raw(aa, _loop_bind_raw(bb, cc)))


def cross7(x, y):
    """The 7-D cross product x×y = Im(loop_bind(x, y)) — the imaginary part of
    the octonion product (drop the e₀ real anchor). For imaginary x, y this is
    ½(x·y − y·x). Antisymmetric (x×y = −y×x); the Class-M bind ∘ Class-C
    ordering with the symmetric part Re(x·y) = −⟨x,y⟩ projected off. Identity:
    ‖x×y‖² = ‖x‖²‖y‖² − ⟨x,y⟩². Ground-truth derived FROM the shipped loop_bind
    (F281); NO new class."""
    a_ = _as_loop(x, "cross7")
    b_ = _as_loop(y, "cross7")
    assert a_.shape == b_.shape, "cross7: operands must have equal length"
    native = _try_native_cross7(a_, b_)
    if native is not None:
        return native
    prod = _loop_bind_raw(a_, b_)
    prod[0] = 0.0  # Im: drop the e₀ real component (Class-C imaginary projection)
    return prod


def g2_three_form(x, y, z):
    """The associative calibration 3-form φ(x,y,z) = ⟨x, cross7(y,z)⟩
    = ⟨x, Im(y·z)⟩ (Harvey–Lawson). Fully antisymmetric; nonzero (±1) exactly on
    the 7 Fano associative 3-planes, zero on the other 28 of the C(7,3)=35 basis
    triples. The sign/orientation convention is fixed BY the shipped loop_bind
    (not imposed externally; F281). Class (M∘C) ∘ ⟨·,·⟩ contraction (Class-L/M);
    NO new class. Returns a scalar."""
    xa = _as_loop(x, "g2_three_form")
    ya = _as_loop(y, "g2_three_form")
    za = _as_loop(z, "g2_three_form")
    assert xa.shape == ya.shape and xa.shape == za.shape, (
        "g2_three_form: operands must have equal length")
    native = _try_native_g2_three_form(xa, ya, za)
    if native is not None:
        return native
    yz = cross7(ya, za)
    return float(np.dot(xa, yz))


def loop_bind_hd(x, y):
    """Block-octonion HD bind — the direct sum ⊕ of NB independent dim-8 octonion
    loop_binds (D = NB·8; the canonical HD width is 2048 = 256·8). Block-DIAGONAL:
    block k of the result is exactly the shipped ``loop_bind`` of the two k-th
    8-blocks; nothing couples blocks (#811/F289). Carries order / tree / direction
    (the F274 non-commutative structure) at NO capacity cost vs the commutative
    Klein-4 XOR bind (capacity-free, #812/F277). Class M (per-block loop_bind =
    M∘C with a Class-K residue) over a direct-sum TILE layout — NO new class.
    Operand length must be a positive multiple of LOOP_DIM (8)."""
    a_ = np.asarray(x, dtype=float)
    b_ = np.asarray(y, dtype=float)
    assert a_.shape == b_.shape, "loop_bind_hd: operands must have equal length"
    assert a_.ndim == 1 and a_.size and a_.size % LOOP_DIM == 0, (
        f"loop_bind_hd: length must be a positive multiple of {LOOP_DIM}")
    native = _try_native_loop_bind_hd(a_, b_)
    if native is not None:
        return native
    xb = a_.reshape(-1, LOOP_DIM)
    yb = b_.reshape(-1, LOOP_DIM)
    return np.concatenate([loop_bind(xb[k], yb[k]) for k in range(xb.shape[0])])


def loop_unbind_hd(a, b):
    """The HD unbind — per-block Moufang left-division conj(a_k)·b_k. For ``a``
    built from unit-per-block octonions (the HD regime), this recovers v from
    ``loop_bind_hd(a, v)`` exactly: conj(a)·(a·v) = v by alternativity. Uses the
    shipped ``loop_conj`` + ``loop_bind`` block-wise; Class-K clean (conjugate +
    bind, no abs()). #811/F289."""
    a_ = np.asarray(a, dtype=float)
    b_ = np.asarray(b, dtype=float)
    assert a_.shape == b_.shape, "loop_unbind_hd: operands must have equal length"
    assert a_.ndim == 1 and a_.size and a_.size % LOOP_DIM == 0, (
        f"loop_unbind_hd: length must be a positive multiple of {LOOP_DIM}")
    native = _try_native_loop_unbind_hd(a_, b_)
    if native is not None:
        return native
    ab = a_.reshape(-1, LOOP_DIM)
    bb = b_.reshape(-1, LOOP_DIM)
    return np.concatenate(
        [loop_bind(loop_conj(ab[k]), bb[k]) for k in range(ab.shape[0])])


def loop_conj_hd(x):
    """Per-block HD octonion conjugate — the direct sum ⊕ of NB independent
    dim-8 ``loop_conj``s. THE missing atom under ``loop_bind_hd`` /
    ``loop_unbind_hd`` (#811/F289): the single-element ``loop_conj`` is GLOBAL
    (one Cayley-Dickson element) and silently wrong on an HD block-octonion
    vector (F-§12.1) — this is the per-block form. Class C (orientation flip)
    over the direct-sum TILE layout; NO new class. Length must be a positive
    multiple of LOOP_DIM (8)."""
    a_ = np.asarray(x, dtype=float)
    assert a_.ndim == 1 and a_.size and a_.size % LOOP_DIM == 0, (
        f"loop_conj_hd: length must be a positive multiple of {LOOP_DIM}")
    native = _try_native_loop_conj_hd(a_)
    if native is not None:
        return native
    xb = a_.reshape(-1, LOOP_DIM)
    return np.concatenate([_loop_conj_raw(xb[k]) for k in range(xb.shape[0])])


def loop_inv_hd(x):
    """Per-block HD Moufang inverse — the direct sum ⊕ of NB independent dim-8
    ``loop_inv``s (x̄ₖ / ⟨xₖ,xₖ⟩ per block). The per-block unbind key:
    ``loop_unbind_hd(x, loop_bind_hd(x, v)) == v``, and for ANY (not only unit)
    per-block x, ``loop_bind_hd(x, loop_inv_hd(x))`` is the per-block e₀. The
    single-element ``loop_inv`` is GLOBAL and silently wrong on an HD vector
    (F-§12.1); this is the per-block form. Class-K clean (per-block norm² gate,
    never abs()); NO new class. Length must be a positive multiple of
    LOOP_DIM (8)."""
    a_ = np.asarray(x, dtype=float)
    assert a_.ndim == 1 and a_.size and a_.size % LOOP_DIM == 0, (
        f"loop_inv_hd: length must be a positive multiple of {LOOP_DIM}")
    native = _try_native_loop_inv_hd(a_)
    if native is not None:
        return native
    xb = a_.reshape(-1, LOOP_DIM)
    out = []
    for k in range(xb.shape[0]):
        blk = xb[k]
        nsq = float(np.dot(blk, blk))
        assert nsq > 0.0, (
            f"loop_inv_hd: block {k} is the zero vector (no Moufang inverse)")
        out.append(_loop_conj_raw(blk) / nsq)
    return np.concatenate(out)


def loop_runbind_hd(a, b):
    """The HD RIGHT-unbind — per-block Moufang RIGHT-division bₖ·conj(aₖ).
    Where ``loop_unbind_hd`` peels the LEFT factor (recovers v from
    ``loop_bind_hd(a, v)`` = aₖ·vₖ), this peels the RIGHT factor: for ``a``
    built from unit-per-block octonions it recovers v from ``loop_bind_hd(v, a)``
    = vₖ·aₖ exactly, since (vₖ·aₖ)·conj(aₖ) = vₖ·(aₖ·conj(aₖ)) = vₖ by
    alternativity. The RBS-LM sequence store is a left-fold ``(((s₀·s₁)·s₂)…)``;
    right-division is what peels the most-recent element off the right (F-§12.2).
    Uses the shipped ``loop_conj`` + ``loop_bind`` block-wise; Class-K clean
    (conjugate + bind, no abs()). NO new class. Length must be a positive
    multiple of LOOP_DIM (8)."""
    a_ = np.asarray(a, dtype=float)
    b_ = np.asarray(b, dtype=float)
    assert a_.shape == b_.shape, "loop_runbind_hd: operands must have equal length"
    assert a_.ndim == 1 and a_.size and a_.size % LOOP_DIM == 0, (
        f"loop_runbind_hd: length must be a positive multiple of {LOOP_DIM}")
    native = _try_native_loop_runbind_hd(a_, b_)
    if native is not None:
        return native
    ab = a_.reshape(-1, LOOP_DIM)
    bb = b_.reshape(-1, LOOP_DIM)
    return np.concatenate(
        [loop_bind(bb[k], loop_conj(ab[k])) for k in range(ab.shape[0])])


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
    "klein4_triality_cycle",
    "klein4_sector_count",
    "LOOP_DIM",
    "loop_conj",
    "loop_bind",
    "loop_inv",
    "loop_left_op",
    "loop_right_op",
    "loop_associator",
    "cross7",
    "g2_three_form",
    "loop_bind_hd",
    "loop_unbind_hd",
    "loop_conj_hd",
    "loop_inv_hd",
    "loop_runbind_hd",
]
