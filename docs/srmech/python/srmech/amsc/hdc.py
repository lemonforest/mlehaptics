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
import random as _random
from array import array
from typing import Sequence

# rc125 (#564): this module is numpy-FREE. The polar {-1,0,+1} ops carry their
# vectors as stdlib ``array('b')`` (int8) buffers, the Klein-4 family as
# ``array('B')`` / :class:`HV`, and the Moufang loop family as ``list[float]`` /
# :class:`Mat` — every kernel a pure-Python / ctypes-marshalled cascade, no
# top-level numpy import and no lazy numpy proxy.

from . import _native
from .hv import HV
from .mat import Mat
from .q import Q


# Canonical HDC dimension default. Higher D = better noise tolerance;
# 1024 bits (128 bytes) is the standard "small" canonical value per
# Kanerva 2009; production HDC typically uses 1000-10000 bits.
DEFAULT_HDC_BYTES: int = 128


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
    # No n_vectors cap: the native count accumulator is uint32 and the
    # pure-Python loop is unbounded — bound is the caller's RAM either way.
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


def bundle_with_ties(vectors: Sequence[bytes]) -> "tuple[bytes, bytes]":
    """Bitwise majority across ANY number of BSC vectors, with the tie state
    surfaced explicitly (UPSTREAM_NOTES rbs_nn Note 1).

    :func:`bundle` requires an odd count so ties cannot occur. This accepts any
    ``N`` (the even-count case is the point) and returns ``(majority, ties)``:

    * ``majority`` — one bit per position, ``1`` where **strictly** more than
      half the inputs are set, else ``0`` (a tie resolves to ``0``; for odd
      ``N`` this byte equals :func:`bundle`'s output exactly).
    * ``ties`` — one bit per position, ``1`` where the set / unset counts are
      **exactly equal** (only possible for even ``N``), else ``0``.

    A tie is a **Class K event**: the bundle accumulator crosses zero there (the
    derivative-sign-flip / phase-boundary of MFO §VII.6.12.1). Surfacing it lets
    a cascade track how close a bundled state is to a phase-boundary tie —
    without changing the binary-byte storage form. **No ``abs()``** — counts
    only (the sign boundary IS the tie bit).

    Args:
        vectors: Sequence of BSC vectors (all same length, non-empty). Any
            count (odd or even) is accepted.

    Returns:
        ``(majority, ties)`` — two byte vectors, each the input length.

    Raises:
        ValueError: empty sequence, mismatched lengths, or zero-length vectors.
    """
    n_vectors = len(vectors)
    if n_vectors == 0:
        raise ValueError("hdc.bundle_with_ties: vectors sequence must be non-empty")
    # No n_vectors cap — bound is the caller's RAM (counts only, no scratch).
    n_bytes = len(vectors[0])
    if n_bytes == 0:
        raise ValueError("hdc.bundle_with_ties: vectors must be non-empty")
    for i, v in enumerate(vectors):
        if len(v) != n_bytes:
            raise ValueError(
                f"hdc.bundle_with_ties: vector {i} has length {len(v)}, "
                f"expected {n_bytes}"
            )
    majority = bytearray(n_bytes)
    ties = bytearray(n_bytes)
    for byte_i in range(n_bytes):
        for bit in range(8):
            count = sum((v[byte_i] >> bit) & 1 for v in vectors)
            two = count * 2
            if two > n_vectors:                 # strict majority set
                majority[byte_i] |= (1 << bit)
            elif two == n_vectors:              # exact tie — the Class K event
                ties[byte_i] |= (1 << bit)
    return bytes(majority), bytes(ties)


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


def _hdc_hamming_native(a: bytes, b: bytes):
    """Native integer bit-Hamming distance over two byte buffers → int (or
    ``None`` if the symbol is absent / the call fails). The count the C kernel
    computes BEFORE the similarity float divide (UPSTREAM §61; F868)."""
    if not hasattr(_native.LIB, "srmech_hdc_hamming"):
        return None
    n = len(a)
    a_buf = (ctypes.c_uint8 * n).from_buffer_copy(a)
    b_buf = (ctypes.c_uint8 * n).from_buffer_copy(b)
    out = ctypes.c_uint32()
    rc = _native.LIB.srmech_hdc_hamming(a_buf, b_buf, n, ctypes.byref(out))
    if rc != _native.SRMECH_OK:
        return None
    return int(out.value)


def _hdc_hamming_core(a: bytes, b: bytes) -> int:
    """The exact integer bit-Hamming distance (native fast path when present,
    else pure-Python popcount). The blow-up-free quantity recall ranks on (F868):
    ``similarity = 1 - 2 * hamming / D`` with ``D = 8 * len(a)``."""
    if _native.HAS_NATIVE:
        h = _hdc_hamming_native(a, b)
        if h is not None:
            return h
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def hamming(a: bytes, b: bytes) -> int:
    """BSC bit-Hamming distance: the **raw integer** count of differing bits
    (UPSTREAM §61; F868). ``similarity = 1 - 2 * hamming(a, b) / (8 * len(a))``.

    This is the float-free, blow-up-free quantity recall ranks on — argmax over
    integer distances needs no division and never leaves the integers (F868
    mechanism #1). The C kernel already computes this count before its float
    divide, so exposing it is additive and C-paired (native ``srmech_hdc_hamming``).

    Raises:
        ValueError: lengths differ or are zero.
    """
    _check_pair(a, b, "hamming")
    return _hdc_hamming_core(a, b)


def similarity(a: bytes, b: bytes) -> "Q":
    """Normalized BSC similarity in ``[-1, 1]`` as the EXACT :class:`~srmech.amsc.q.Q`.

    ``similarity(a, b) = 1 - 2 * hamming(a, b) / D = (D - 2*hamming) / D`` where
    ``D = 8 * len(a)`` — both integers, so the return is the exact ``Q`` carrier:
    it compares like a float (``similarity(a, a) == 1.0``), ranks correctly, and
    collapses to a decimal only at the display boundary via ``float(s)`` — never a
    lossy mid-cascade ``float`` (the stay-rational discipline, F868,
    `[[feedback_stay_rational_collapse_only_at_display]]`). For the raw integer
    bit-distance (the blow-up-free recall key) use :func:`hamming`.

    +1 = identical; 0 = orthogonal (Hamming distance D/2); -1 = bit-complementary.

    Raises:
        ValueError: lengths differ or are zero.
    """
    _check_pair(a, b, "similarity")
    n = len(a)
    D = n * 8
    ham = _hdc_hamming_core(a, b)
    return Q(D - 2 * ham, D)


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


#: ctypes int8 pointer alias for the native polar-op marshalling (numpy-free).
_I8P = ctypes.POINTER(ctypes.c_int8)


def _as_polar(v, op: str) -> "array":
    """Validate + copy a polar value into an ``array('b')`` (int8) buffer.

    Accepts any 1-D sequence (``array('b')`` / list / tuple — the carrier is
    agnostic about the source shape); elements must be in ``{-1, 0, +1}``. The
    numpy-free path — ``np`` is never imported or touched here (rc125)."""
    src = v.buffer if isinstance(v, HV) else v
    buf = array("b")
    try:
        for x in src:
            xi = int(x)
            if xi not in (-1, 0, 1):
                raise ValueError(f"hdc.{op}: polar elements must be in {{-1, 0, +1}}")
            buf.append(xi)
    except (TypeError, OverflowError) as exc:
        raise ValueError(f"hdc.{op}: polar vector must be a 1-D sequence of ints") from exc
    if len(buf) == 0:
        raise ValueError(f"hdc.{op}: polar vector must be non-empty")
    return buf


def _check_polar_pair(a, b, op: str):
    a = _as_polar(a, op)
    b = _as_polar(b, op)
    if len(a) != len(b):
        raise ValueError(
            f"hdc.{op}: vector lengths must match (got {len(a)} vs {len(b)})"
        )
    return a, b


def polar_random(D: int, rng=None, seed: "int | None" = None):
    """Random polar hypervector of dimension ``D`` with elements in {-1, 0, +1}.

    Args:
        D: Vector dimension (positive).
        rng: Optional ``random.Random`` (or numpy ``Generator``) for in-process
            callers. A generator cannot cross JSON-RPC nor be expressed in an
            Anthropic tool schema; use ``seed`` from those callers.
        seed: Optional integer seed. When given (and ``rng`` is not), the
            generator is built internally as ``random.Random(seed)``, so MCP /
            Anthropic callers can obtain a DETERMINISTIC vector (srmech's
            bit-exact / attestation discipline). **Precedence:** an explicit
            ``rng`` wins over ``seed`` if both are supplied.

    Returns:
        An ``array('b')`` of length ``D`` with elements drawn uniformly from
        ``{-1, 0, +1}`` (rc125: numpy-free stdlib ``random``).
    """
    if D <= 0:
        raise ValueError("hdc.polar_random: D must be positive")
    if rng is not None and hasattr(rng, "integers"):
        # Back-compat numpy ``Generator`` path: the caller already holds numpy,
        # so this branch may use it (coerced to a stdlib int8 buffer).
        return array("b", (int(x) for x in rng.integers(-1, 2, size=D)))
    r = rng if rng is not None else _random.Random(seed)
    return array("b", (r.randrange(-1, 2) for _ in range(D)))


def polar_bind(a, b):
    """Polar bind: element-wise sign-product with 0 **absorbing**.

    ``bind(a, b)[i] = a[i] * b[i]``. On the ±1 sub-alphabet this is the same
    sign-product as bipolar bind (commutative, associative, self-inverse). The
    0 state is absorbing — ``0 * x = 0`` — so an "uncertain" (dead-band)
    position stays uncertain after binding.

    rc125 (numpy-free): the int8 sign-product is a pure-Python comprehension
    over ``array('b')`` buffers; the native peer is fed those buffers directly
    (buffer-protocol ctypes cast, no numpy contiguous-array copy). Returns an
    ``array('b')``.
    """
    a, b = _check_polar_pair(a, b, "polar_bind")
    n = len(a)
    # rc12: dispatch the int8 element-wise sign-product to the C peer when
    # present (bit-identical to the ``a[i]*b[i]`` below — integer arithmetic, no
    # float — which stays the Pyodide / no-native fallback). #928 cheap-win #5.
    if (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_polar_bind")):
        a_c = (ctypes.c_int8 * n).from_buffer_copy(a)
        b_c = (ctypes.c_int8 * n).from_buffer_copy(b)
        out = (ctypes.c_int8 * n)()
        rc = _native.LIB.srmech_polar_bind(
            ctypes.cast(a_c, _I8P), ctypes.cast(b_c, _I8P),
            ctypes.c_uint32(n), ctypes.cast(out, _I8P))
        if rc == _native.SRMECH_OK:
            return array("b", out)
    return array("b", (a[i] * b[i] for i in range(n)))


def polar_unbind(c, a):
    """Polar unbind: ``unbind(c, a)[i] = c[i] * a[i]`` (the same sign-product).

    Self-inverse on the ±1 sub-alphabet (``a * a = 1``), so
    ``unbind(bind(a, b), a) == b`` wherever ``a[i] != 0``. Where ``a[i] == 0``
    the original is **not** recoverable (0 is destructive) — matching the
    dead-band semantics: anything bound through an uncertain position is gone.

    rc125 (numpy-free): pure-Python int8 product over ``array('b')``."""
    c, a = _check_polar_pair(c, a, "polar_unbind")
    return array("b", (c[i] * a[i] for i in range(len(c))))


def polar_bundle(*vectors):
    """Polar bundle: sticky majority across vectors; ties resolve to 0.

    Per-position ``sign(sum_i v_i)`` — positive sum → +1, negative → -1, exact
    tie (sum == 0, including all-zero) → **0**. Unlike bipolar bundle, no
    odd-count restriction is needed: the 0 state absorbs ties as a first-class
    "uncertain" output rather than forcing a hard ±1 choice.

    rc125 (numpy-free): the per-position sign-of-sum is a Class-K pin-slot
    branch over a pure-Python column sum (no sign ufunc); returns ``array('b')``.

    Raises:
        ValueError: empty call or mismatched lengths.
    """
    if len(vectors) == 0:
        raise ValueError("hdc.polar_bundle: requires at least one vector")
    arrs = [_as_polar(v, "polar_bundle") for v in vectors]
    n = len(arrs[0])
    for i, arr in enumerate(arrs):
        if len(arr) != n:
            raise ValueError(
                f"hdc.polar_bundle: vector {i} has length {len(arr)}, expected {n}"
            )
    # rc12: dispatch the per-position sticky-majority (sign-of-sum, tie -> 0) to
    # the C peer when present (bit-identical to the sign-of-sum below, which
    # stays the Pyodide / no-native fallback). #928 cheap-win #5.
    if (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_polar_bundle")):
        n_vectors = len(arrs)
        bufs = [(ctypes.c_int8 * n).from_buffer_copy(v) for v in arrs]
        ptr_array = (_I8P * n_vectors)(*(ctypes.cast(b, _I8P) for b in bufs))
        out = (ctypes.c_int8 * n)()
        rc = _native.LIB.srmech_polar_bundle(
            ptr_array, ctypes.c_uint32(n_vectors), ctypes.c_uint32(n),
            ctypes.cast(out, _I8P))
        if rc == _native.SRMECH_OK:
            return array("b", out)
    # Class-K sign (pin-slot at zero): + sector / 0 boundary / - sector, via the
    # sign of the integer column sum — bit-identical to the sign ufunc. No abs().
    out = array("b", bytes(n))
    for i in range(n):
        total = sum(arr[i] for arr in arrs)
        out[i] = 1 if total > 0 else (-1 if total < 0 else 0)
    return out


def polar_similarity(a, b, skip_zero: bool = True) -> "Q":
    """Polar match-fraction similarity — exact rational :class:`~srmech.amsc.q.Q`.

    ``skip_zero=True`` (default): match-fraction over only the positions where
    **both** vectors are non-zero (0 = "no information", excluded). Returns the
    exact ``Q(0, 1)`` when there are no jointly-informative positions.

    ``skip_zero=False``: plain match-fraction over all positions (``0 == 0``
    counts as a match — neutral-credit semantics).

    The match-fraction is exactly ``matches / D`` (both integers), so the return
    is the exact ``Q`` carrier — it compares like a float (``s == 0.75``) and
    ranks correctly, and you collapse to a decimal only at the display boundary
    with ``float(s)`` (the stay-rational discipline, F868,
    `[[feedback_stay_rational_collapse_only_at_display]]`).

    rc125 (numpy-free): pure-Python counting over ``array('b')`` buffers."""
    a, b = _check_polar_pair(a, b, "polar_similarity")
    n = len(a)
    if skip_zero:
        informative = [i for i in range(n) if a[i] != 0 and b[i] != 0]
        matches = sum(1 for i in informative if a[i] == b[i])
        return Q(matches, len(informative)) if informative else Q(0, 1)
    matches = sum(1 for i in range(n) if a[i] == b[i])
    return Q(matches, n)


def polar_density(v) -> "Q":
    """Fraction of non-zero (informative) positions — exact rational
    :class:`~srmech.amsc.q.Q`.

    ``Q(1, 1)`` = fully bipolar (no dead-band); lower = more positions resting in
    the Class-K dead-band / uncertain state. The density is exactly
    ``nonzero / n`` (both integers), so it stays the exact ``Q`` carrier and
    collapses to a decimal only via ``float(d)`` (stay-rational, F868).

    rc125 (numpy-free): pure-Python count over ``array('b')``."""
    arr = _as_polar(v, "polar_density")
    n = len(arr)
    return Q(sum(1 for x in arr if x != 0), n) if n else Q(0, 1)


def polar_from_real(arr, threshold: float = 0.0, dead_band: float = 0.0):
    """Bridge real-valued data into a polar HDC vector via ``sign_quantise``.

    Wraps :func:`srmech.signal_processing.path_b_ops.sign_quantise.op` — the
    existing Class-K threshold projection — and lifts its ``{-1, 0, +1}`` output
    into the ``amsc.hdc`` namespace. With ``dead_band > 0`` the near-threshold
    zone maps to 0 (the asymptotic-DOF pin-slot rejection zone); with
    ``dead_band == 0`` the output is strict bipolar (ties favour +1 per
    ``sign_quantise``).

    rc125 (numpy-free): ``sign_quantise.op`` returns a numpy-free list (the
    rc94 flip); it is collected into an ``array('b')`` (was an int8 ndarray)."""
    from ..signal_processing.path_b_ops import sign_quantise

    out = sign_quantise.op(arr, threshold=threshold, dead_band=dead_band)
    return array("b", (int(x) for x in out))


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
    """Validate a Klein-4 value into an ``array('B')`` buffer (numpy-free).

    rc125: the prior numpy ``asarray(..., uint8)`` path is the stdlib
    :func:`_as_klein4_buf` — kept as a thin alias for the few legacy callers
    of this name (elements in ``{0, 1, 2, 3}``)."""
    return _as_klein4_buf(v, op)


# ── numpy-free Klein-4 core (v0.7.0rc29; UPSTREAM §22/§22b) ───────────────
# The Klein-4 carrier is the first family to go numpy-free: ops validate to a
# stdlib ``array('B')`` working buffer and return an :class:`HV` handle (no
# implicit ndarray escapes — the §22 boundary-type lever). The kernels
# below are pure-Python byte ops; no ``np`` is touched on this path.

def _as_klein4_buf(v, op: str) -> "array":
    """Validate + copy a Klein-4 value into an ``array('B')`` working buffer.

    Accepts an :class:`HV`, ``bytes`` / ``bytearray`` / ``array('B')``, or a
    ``list`` / ``tuple`` / generator of ints (the carrier is agnostic about the
    source shape). Elements must be in ``{0, 1, 2, 3}``. The numpy-free path —
    ``np`` is never imported or touched here."""
    src = v.buffer if isinstance(v, HV) else v
    # Fast path: an existing uint8 buffer (HV.buffer / array('B') / bytes /
    # bytearray — the common klein4 case). Bulk-copy at C speed, then range-check
    # in a single C-level pass (max() over the array) rather than a per-element
    # Python loop. This is what lets the native bind/bundle/similarity dispatch
    # below actually win — otherwise the per-element validation dominates the op.
    if isinstance(src, (bytes, bytearray)) or (
            isinstance(src, array) and src.typecode == "B"):
        buf = array("B", src)
        if len(buf) == 0:
            raise ValueError(f"hdc.{op}: klein-4 vector must be non-empty")
        if max(buf) > 3:   # uint8 is already ≥ 0, so > 3 ⇒ outside {0, 1, 2, 3}
            raise ValueError(
                f"hdc.{op}: klein-4 elements must be in {{0, 1, 2, 3}}")
        return buf
    # General path: a list / tuple / generator of ints — validate per element.
    buf = array("B")
    try:
        for x in src:
            xi = int(x)
            if xi < 0 or xi > 3:
                raise ValueError(
                    f"hdc.{op}: klein-4 elements must be in {{0, 1, 2, 3}}"
                )
            buf.append(xi)
    except (TypeError, OverflowError) as exc:
        raise ValueError(
            f"hdc.{op}: klein-4 vector must be a 1-D sequence of ints"
        ) from exc
    if len(buf) == 0:
        raise ValueError(f"hdc.{op}: klein-4 vector must be non-empty")
    return buf


def _store_buf(store, op: str) -> "array":
    """Copy a 1-D uint8 store (HV / bytes / array / list — agnostic source) into an
    ``array('B')`` — the lenient buffer used by the holographic decode (elements
    are any uint8, not restricted to ``{0, 1, 2, 3}``). Numpy-free."""
    src = store.buffer if isinstance(store, HV) else store
    buf = array("B")
    try:
        for x in src:
            buf.append(int(x))
    except (TypeError, OverflowError) as exc:
        raise ValueError(f"hdc.{op}: store must be a 1-D sequence of uint8") from exc
    return buf


def _xor_buf(a: "array", b: "array") -> "array":
    """Element-wise XOR of two equal-length ``array('B')`` buffers."""
    return array("B", (x ^ y for x, y in zip(a, b)))


def _xor_const_buf(a: "array", mask: int) -> "array":
    """XOR every element of ``a`` with a constant ``mask`` (0 → unchanged copy)."""
    return array("B", a) if mask == 0 else array("B", (x ^ mask for x in a))


def _table_buf(a: "array", table) -> "array":
    """Relabel every element of ``a`` through a length-4 lookup ``table``."""
    return array("B", (table[x] for x in a))


def _majority_buf(arrs) -> "array":
    """Per-position 2-bit majority vote over equal-length ``array('B')`` buffers.

    Each Klein-4 element is two independent bits; a bit is set only when its
    1-count is strictly greater than ``len(arrs) // 2`` (an exact tie → 0).
    The numpy-free kernel behind :func:`klein4_bundle` / the holographic +
    triality majorities. No ``abs()``."""
    n = len(arrs[0])
    half = len(arrs) // 2
    out = array("B", bytes(n))
    for i in range(n):
        c0 = 0
        c1 = 0
        for a in arrs:
            x = a[i]
            c0 += x & 1
            c1 += (x >> 1) & 1
        out[i] = ((1 if c1 > half else 0) << 1) | (1 if c0 > half else 0)
    return out


def klein4_random(D: int, rng=None, seed: "int | None" = None):
    """Random Klein-4 hypervector of dimension ``D`` with elements in {0,1,2,3}.

    Args:
        D: Vector dimension (positive).
        rng: Optional ``numpy.random.Generator`` for in-process Python
            callers. A ``Generator`` cannot cross JSON-RPC nor be expressed
            in an Anthropic tool schema; use ``seed`` from those callers.
        seed: Optional integer seed. When given (and ``rng`` is not), the
            generator is built internally as ``random.Random(seed)`` (rc125:
            stdlib, numpy-free), so MCP / Anthropic callers can obtain a
            DETERMINISTIC vector (srmech's bit-exact / attestation discipline).
            **Precedence:** an explicit ``rng`` wins over ``seed`` if both are
            supplied.
    """
    if D <= 0:
        raise ValueError("hdc.klein4_random: D must be positive")
    if rng is not None and hasattr(rng, "integers"):
        # Back-compat numpy ``Generator`` path: the caller already holds numpy,
        # so this branch may use it (coerced to a stdlib uint8 buffer — no numpy
        # name in THIS module). The default (seed / None) path below is
        # numpy-free (stdlib ``random``) — the §22 numpy-optional core.
        return HV(array("B", (int(x) for x in rng.integers(0, 4, size=D))), sectors=4)
    r = rng if rng is not None else _random.Random(seed)
    return HV(array("B", (r.randrange(4) for _ in range(D))), sectors=4)


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


def _klein4_sector_flip(s, buf: "array") -> "array":
    """Apply the Klein-4 sector flip ``T_s`` (an involution: XOR with mask s)."""
    return _xor_const_buf(buf, _KLEIN4_SECTOR_MASKS[s])


def _klein4_chirality_duals(body, buf: "array", n_sectors):
    """The ≤4 sector duals ``T_s(body(T_s(v)))`` (F233). Serial — the pure-Python
    bodies are GIL-bound, so threading would not overlap (UPSTREAM caveat)."""
    return [
        _klein4_sector_flip(s, body(_klein4_sector_flip(s, buf)))
        for s in range(n_sectors)
    ]


def _klein4_bundle_core(arrs) -> "array":
    """Per-bit majority over equal-length klein4 buffers — the serial bundle
    kernel (the public :func:`klein4_bundle` wraps it in an :class:`HV`)."""
    n = len(arrs[0])
    for i, a in enumerate(arrs):
        if len(a) != n:
            raise ValueError(
                f"hdc.klein4_bundle: vector {i} has length {len(a)}, expected {n}"
            )
    return _majority_buf(arrs)


# --- §53 / F818: native dispatch for the Class-M klein4 core ----------------
# The C srmech_klein4_bind / _bundle / _similarity ship in libsrmech (and are
# ctypes-bound in _native); these marshal the array('B') klein4 buffers (codes
# 0..3) to the native uint8 surface so the per-token HDC walk runs at C speed
# (~100–1000× the pure-Python XOR/majority/match-count at D≈10⁴). The pure-Python
# bodies remain the COMPLETE, bit-identical alternative for no-C environments.


def _klein4_bind_native(a: "array", b: "array") -> "array":
    """Native sector-XOR bind over two array('B') klein4 buffers → array('B')."""
    n = len(a)
    ca = (ctypes.c_uint8 * n).from_buffer_copy(a)
    cb = (ctypes.c_uint8 * n).from_buffer_copy(b)
    out = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_klein4_bind(ca, cb, ctypes.c_uint32(n), out)
    if rc != _native.SRMECH_OK:
        return None
    return array("B", bytes(out))


def _klein4_bundle_native(arrs) -> "array":
    """Native per-bit majority bundle over ≥1 equal-length array('B') buffers."""
    n_vec = len(arrs)
    dim = len(arrs[0])
    cbufs = [(ctypes.c_uint8 * dim).from_buffer_copy(a) for a in arrs]
    ptrs = (ctypes.POINTER(ctypes.c_uint8) * n_vec)(
        *[ctypes.cast(c, ctypes.POINTER(ctypes.c_uint8)) for c in cbufs])
    out = (ctypes.c_uint8 * dim)()
    rc = _native.LIB.srmech_klein4_bundle(
        ptrs, ctypes.c_uint32(n_vec), ctypes.c_uint32(dim), out)
    if rc != _native.SRMECH_OK:
        return None
    return array("B", bytes(out))


def _klein4_similarity_native(a: "array", b: "array"):
    """Native match-fraction similarity over two array('B') buffers → float."""
    n = len(a)
    ca = (ctypes.c_uint8 * n).from_buffer_copy(a)
    cb = (ctypes.c_uint8 * n).from_buffer_copy(b)
    out = ctypes.c_double()
    rc = _native.LIB.srmech_klein4_similarity(
        ca, cb, ctypes.c_uint32(n), ctypes.byref(out))
    if rc != _native.SRMECH_OK:
        return None
    return float(out.value)


def _klein4_match_count_native(a: "array", b: "array"):
    """Native exact integer match count over two array('B') buffers → int (or
    ``None`` if the symbol is absent / the call fails). The count is what the C
    kernel computes before the float divide (UPSTREAM §61; F868)."""
    if not hasattr(_native.LIB, "srmech_klein4_match_count"):
        return None
    n = len(a)
    ca = (ctypes.c_uint8 * n).from_buffer_copy(a)
    cb = (ctypes.c_uint8 * n).from_buffer_copy(b)
    out = ctypes.c_uint32()
    rc = _native.LIB.srmech_klein4_match_count(
        ca, cb, ctypes.c_uint32(n), ctypes.byref(out))
    if rc != _native.SRMECH_OK:
        return None
    return int(out.value)


def _klein4_triality_native(buf: "array", inverse: bool) -> "array":
    """Native order-3 triality relabel over an array('B') buffer → array('B').
    The C uses the SAME forward / inverse 3-cycle tables as the pure path."""
    n = len(buf)
    cin = (ctypes.c_uint8 * n).from_buffer_copy(buf)
    out = (ctypes.c_uint8 * n)()
    rc = _native.LIB.srmech_klein4_triality_cycle(
        cin, ctypes.c_uint32(n), ctypes.c_int(1 if inverse else 0), out)
    if rc != _native.SRMECH_OK:
        return None
    return array("B", bytes(out))


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
    a = _as_klein4_buf(a, "klein4_bind")
    b = _as_klein4_buf(b, "klein4_bind")
    if len(a) != len(b):
        raise ValueError(
            f"hdc.klein4_bind: lengths must match (got {len(a)} vs {len(b)})"
        )
    if mode not in ("chunk", "chirality"):
        raise ValueError(
            f"klein4_bind: mode must be 'chunk' or 'chirality'; got {mode!r}"
        )
    _klein4_resolve_sectors(sectors, parallel)  # validate the lane flags
    # XOR is sector-transparent: chunk == serial, and the F233 chirality dual
    # T_s(T_s(a) XOR b) collapses to a XOR b for every sector. So all modes
    # yield the plain XOR; sectors=/parallel= stay accepted value-no-op flags
    # (pure-Python bodies don't overlap under the GIL anyway — UPSTREAM caveat).
    if len(a) >= 1 and _native.has_native_klein4_bind():   # §53: native fast path
        out = _klein4_bind_native(a, b)
        if out is not None:
            return HV(out, sectors=4)
    return HV(_xor_buf(a, b), sectors=4)


def klein4_unbind(c, a):
    """Klein-4 unbind: self-inverse XOR, so ``unbind(bind(a, b), a) == b``."""
    return klein4_bind(c, a)


def klein4_unbundle(bundle, key):
    """Klein-4 unbundle: recover a bound value from a bundle (superposition) —
    the dual of :func:`klein4_bundle`.

    A record is built by bundling bound key→value pairs,
    ``S = bundle(bind(k1, v1), …, bind(kn, vn))``. Binding a key **back** against
    the superposition recovers that key's value plus crosstalk from the other
    terms: ``unbundle(S, ki) == unbind(S, ki) == bind(S, ki)`` (self-inverse XOR).
    This works precisely *because the bundle keeps the relationship* — the bound
    pairs are still present in ``S``; it needs neither the individual pre-bundle
    vectors nor a separate index. For a single bound pair it is **exact**
    (``unbundle(bind(k, v), k) == v``); inside a multi-pair bundle the result is
    the value-plus-crosstalk estimate.

    Clean up the estimate to the exact stored value with :func:`klein4_similarity`
    against a codebook of candidate values
    (``argmax_v similarity(unbundle(S, key), v)``) — recoverable up to the HDC
    bundle capacity. So ``bundle``'s dual is **unbundle + similarity-cleanup**, a
    structured bind-back recovery — NOT a blind query. (Class M is reversible,
    capacity-bounded; the per-class reversibility audit is corrected accordingly.)

    Args:
        bundle: A Klein-4 superposition (uint8 ``{0,1,2,3}``), e.g. from
            :func:`klein4_bundle`.
        key: The binding key (uint8 ``{0,1,2,3}``, same length as ``bundle``).

    Returns:
        The recovered value + crosstalk (uint8 ``{0,1,2,3}``); denoise via
        :func:`klein4_similarity` against your codebook.
    """
    return klein4_bind(bundle, key)


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
    arrs = [_as_klein4_buf(v, "klein4_bundle") for v in vectors]
    if mode not in ("chunk", "chirality"):
        raise ValueError(
            f"klein4_bundle: mode must be 'chunk' or 'chirality'; got {mode!r}"
        )
    n_sectors = _klein4_resolve_sectors(sectors, parallel)
    if mode == "chunk" or n_sectors <= 1:
        # chunk splits positions → bit-identical to the plain serial majority.
        if len(arrs[0]) >= 1 and _native.has_native_klein4_bind():  # §53: native
            out = _klein4_bundle_native(arrs)
            if out is not None:
                return HV(out, sectors=4)
        return HV(_klein4_bundle_core(arrs), sectors=4)
    # chirality (F233): bundle the T_s-conjugated inputs, inv_T_s (=T_s) each,
    # then majority the ≤4 — meaningful only for chirality-asymmetric inputs.
    duals = [
        _klein4_sector_flip(s, _klein4_bundle_core([_klein4_sector_flip(s, a) for a in arrs]))
        for s in range(n_sectors)
    ]
    return HV(_klein4_bundle_core(duals), sectors=4)


# ── §59 / F861: continuous-phase Klein-4 (population-code phase key + bind) ──
# The chirality-native analogue of HRR / polar phase: a continuous phase
# ``frac ∈ [0, 1)`` is encoded as a half-window of one V4 element on a slot
# offset ``round(frac·D) mod D`` (population coding), then BOUND into a value
# with ``klein4_bind``. The key property is exactly rational:
#   ``klein4_similarity(phase_bind(h, 0), phase_bind(h, Δφ)) == 1 − 2·circ_dist(Δφ)``
# because the ``h`` cancels under the XOR bind, leaving the integer overlap of
# the two slot-windows over ``D`` — :func:`klein4_similarity` keeps it a ``Q``
# (stay-rational, F868). Reversible (same phase twice = identity) + σ-mirror
# (``±φ`` equidistant from the base). No new primitive class: Class-M bind over
# a Class-K-style sector pattern. numpy-free; carrier = one HV.


def _klein4_phase_start(D: int, frac) -> int:
    """Integer slot offset ``round(frac·D) mod D`` (the F861 population-code
    phase offset). ``frac`` is a float phase in ``[0, 1)`` (values outside wrap
    circularly via the ``mod D``)."""
    return round(float(frac) * D) % D


def _klein4_phase_key_native(D: int, start: int, width: int, elem: int):
    """Native window-fill of the phase-key buffer → ``array('B')`` (or ``None``
    if the symbol is absent / the call fails — the pure path is the complete
    bit-identical alternative)."""
    if not hasattr(_native.LIB, "srmech_klein4_phase_key"):
        return None
    out = (ctypes.c_uint8 * D)()
    rc = _native.LIB.srmech_klein4_phase_key(
        ctypes.c_uint32(D), ctypes.c_uint32(start),
        ctypes.c_uint32(width), ctypes.c_uint8(elem), out)
    if rc != _native.SRMECH_OK:
        return None
    return array("B", bytes(out))


def _klein4_phase_key_core(D: int, start: int, width: int, elem: int) -> "array":
    """Pure-Python window fill: ``elem`` on the circular slot-window
    ``[start, start+width) mod D``, 0 elsewhere (bit-identical to the C peer).
    No ``abs()`` — a plain modular write loop."""
    buf = array("B", bytes(D))
    for j in range(width):
        buf[(start + j) % D] = elem
    return buf


def klein4_phase_key(D, frac, *, elem=2, width=None):
    """A continuous-phase Klein-4 key (UPSTREAM §59; F861).

    The V4 element ``elem`` (default 2 = the γ₅ axis) is written on a
    ``width``-wide circular slot-window starting at ``round(frac·D) mod D``,
    with identity (0) everywhere else — "continuous phase from discrete-per-slot
    sectors via population coding."

    Args:
        D: Vector dimension (positive).
        frac: Phase fraction in ``[0, 1)`` (a float; values outside wrap mod 1).
        elem: The Klein-4 code in ``{0, 1, 2, 3}`` written across the window
            (default 2 = γ₅).
        width: Window width in slots (default the half-window ``D // 2``, which
            gives the measured ``1 − 2·circ_dist`` similarity law).
    """
    D = int(D)
    if D <= 0:
        raise ValueError("hdc.klein4_phase_key: D must be positive")
    if not isinstance(elem, int) or isinstance(elem, bool) or elem < 0 or elem > 3:
        raise ValueError(
            "hdc.klein4_phase_key: elem must be a Klein-4 code in {0, 1, 2, 3}; "
            f"got {elem!r}")
    w = D // 2 if width is None else int(width)
    if w < 0 or w > D:
        raise ValueError(
            f"hdc.klein4_phase_key: width must be in 0..D ({D}); got {w}")
    start = _klein4_phase_start(D, frac)
    out = _klein4_phase_key_native(D, start, w, elem)
    if out is None:
        out = _klein4_phase_key_core(D, start, w, elem)
    return HV(out, sectors=4)


def klein4_phase_bind(hv, frac, *, elem=2, width=None):
    """Bind a continuous phase ``frac`` into a Klein-4 hypervector (UPSTREAM §59):
    ``klein4_bind(hv, klein4_phase_key(len(hv), frac, elem, width))``.

    Reversible (``phase_bind(phase_bind(h, φ), φ) == h``); σ-mirror (``+φ`` and
    ``−φ`` are equidistant from the base); and
    ``klein4_similarity(phase_bind(h, 0), phase_bind(h, Δφ))`` is the EXACT
    rational ``1 − 2·circ_dist(Δφ)`` — the integer half-window overlap over
    ``D`` (a :class:`Q`, never a lossy float). The chirality-native analogue of
    HRR / polar phase, built only from a slot-window key + :func:`klein4_bind`.
    """
    buf = _as_klein4_buf(hv, "klein4_phase_bind")
    key = klein4_phase_key(len(buf), frac, elem=elem, width=width)
    return klein4_bind(HV(buf, sectors=4), key)


# ── §58 / F837: capacity-bounded chunk-set + max-resonance read ─────────────
# A reusable VSA cleanup-memory. Instead of superposing N bound key→value pairs
# into ONE over-stuffed bundle (crosstalk grows with N), the binds are split
# into a LIST of capacity-bounded bundles (≤ C binds each). Recall probes every
# chunk and takes the MAX resonance over the chunk-set — the F837 fix that took
# the resolver read from 3.3% → 96.7% rank-1. The capacity C is EXPOSED (a
# non-monotonic sweet-spot, F839 correction), NOT hardcoded. LM-agnostic: the
# ROUTING / per-doc k* / autoregressive loop / argmax stay in the caller (the
# §58.1 / F839 boundary). Composes klein4_bind/bundle/similarity — no new class.


def _klein4_chunk_resolve_native(chunk_bufs, key_buf, cand_bufs, D):
    """Native max-resonance read → per-candidate best integer match-count (or
    ``None`` if the symbol is absent / the call fails). The C returns the COUNT
    (the F868 stay-rational ranking key) before the ``/D`` divide."""
    if not hasattr(_native.LIB, "srmech_klein4_chunk_resolve"):
        return None
    n_chunks = len(chunk_bufs)
    n_cand = len(cand_bufs)
    chunks_flat = (ctypes.c_uint8 * (n_chunks * D)).from_buffer_copy(
        b"".join(bytes(c) for c in chunk_bufs))
    cand_flat = (ctypes.c_uint8 * (n_cand * D)).from_buffer_copy(
        b"".join(bytes(c) for c in cand_bufs))
    ckey = (ctypes.c_uint8 * D).from_buffer_copy(bytes(key_buf))
    out = (ctypes.c_uint32 * n_cand)()
    rc = _native.LIB.srmech_klein4_chunk_resolve(
        chunks_flat, ctypes.c_uint32(n_chunks), ckey, ctypes.c_uint32(D),
        cand_flat, ctypes.c_uint32(n_cand), out)
    if rc != _native.SRMECH_OK:
        return None
    return [int(x) for x in out]


def _klein4_chunk_resolve_core(chunk_bufs, key_buf, cand_bufs):
    """Pure-Python max-resonance read → per-candidate best integer match-count
    (bit-identical to the C peer). bind = XOR; match-count = agreeing positions;
    take the MAX over the chunk-set. No ``abs()``."""
    bound = [_xor_buf(ch, key_buf) for ch in chunk_bufs]
    out = []
    for cand in cand_bufs:
        best = 0
        for bd in bound:
            mc = sum(1 for x, y in zip(bd, cand) if x == y)
            if mc > best:
                best = mc
        out.append(best)
    return out


def klein4_chunk_bundle(vectors, capacity):
    """Build a CAPACITY-BOUNDED chunk-set from a list of (bound) vectors
    (UPSTREAM §58; F837): consecutive groups of ≤ ``capacity`` vectors, each
    reduced with :func:`klein4_bundle`. Returns a ``list`` of :class:`HV`
    chunks — the cleanup-memory that avoids the single-bundle crosstalk.

    ``capacity`` is exposed (a non-monotonic sweet-spot per tome, F839), not
    hardcoded. numpy-free; carrier cost = ``ceil(len(vectors) / capacity)``
    bundles.
    """
    bufs = [_as_klein4_buf(v, "klein4_chunk_bundle") for v in vectors]
    if not bufs:
        raise ValueError("hdc.klein4_chunk_bundle: requires at least one vector")
    C = int(capacity)
    if C < 1:
        raise ValueError(f"hdc.klein4_chunk_bundle: capacity must be ≥ 1; got {C}")
    n = len(bufs[0])
    for i, b in enumerate(bufs):
        if len(b) != n:
            raise ValueError(
                f"hdc.klein4_chunk_bundle: vector {i} has length {len(b)}, "
                f"expected {n}")
    chunks = []
    for i in range(0, len(bufs), C):
        group = bufs[i:i + C]
        chunks.append(klein4_bundle(*group))   # native-dispatched bundle
    return chunks


def klein4_chunk_resolve(chunks, key, candidates):
    """Max-resonance read over a capacity-bounded chunk-set (UPSTREAM §58; F837).

    For each candidate, returns the **MAX over chunks** of
    ``klein4_similarity(klein4_bind(chunk, key), candidate)`` — one EXACT
    :class:`Q` per candidate (stay-rational, F868: the recall ranks on the
    integer match-count; ``Q(count, D)`` only names the fraction). The
    LM-agnostic VSA cleanup-memory; the routing / argmax stays in the caller.
    Native-dispatched via ``srmech_klein4_chunk_resolve`` (the recall hot path).
    """
    chunk_bufs = [_as_klein4_buf(c, "klein4_chunk_resolve") for c in chunks]
    cand_bufs = [_as_klein4_buf(c, "klein4_chunk_resolve") for c in candidates]
    if not chunk_bufs:
        raise ValueError("hdc.klein4_chunk_resolve: requires at least one chunk")
    if not cand_bufs:
        raise ValueError("hdc.klein4_chunk_resolve: requires at least one candidate")
    key_buf = _as_klein4_buf(key, "klein4_chunk_resolve")
    D = len(key_buf)
    for label, bufs in (("chunk", chunk_bufs), ("candidate", cand_bufs)):
        for i, b in enumerate(bufs):
            if len(b) != D:
                raise ValueError(
                    f"hdc.klein4_chunk_resolve: {label} {i} has length {len(b)}, "
                    f"expected {D} (the key length)")
    counts = _klein4_chunk_resolve_native(chunk_bufs, key_buf, cand_bufs, D)
    if counts is None:
        counts = _klein4_chunk_resolve_core(chunk_bufs, key_buf, cand_bufs)
    return [Q(c, D) for c in counts]


# ── §60 / F864: byte/glyph-level Klein-4 encoder (morphology, no English bias) ─
# The word-atomic encoder (whole token → one orthogonal random HV) has no
# sub-word structure (sim('cat','cats') ≈ chance). The byte/glyph core composes
# a word vector from POSITION-BOUND per-byte vectors — restoring morphology
# (sim('cat','cats') ≫ chance) while stripping the English/whitespace privilege
# (it hashes raw UTF-8 bytes, the universal-script alphabet). Composes
# klein4_random (the 256-byte vocab + position keys) + klein4_bind + klein4_
# bundle — no new primitive class. The per-byte / per-position vector minting
# rides the python_only ``klein4_random`` (stdlib-MT determinism by design); a
# standalone-C MT19937 to make the whole minting+encode native is the tracked
# follow-up. numpy-free; carrier = one HV.

#: Seed namespace for position role-keys — disjoint from the 0..255 byte vocab.
_KLEIN4_POS_SEED_BASE = 0x10000


def _klein4_pos_key(D, pos):
    """A deterministic Klein-4 position role-vector for slot ``pos`` (UPSTREAM
    §60): ``klein4_random`` over a position-namespaced seed
    (``0x10000 + pos``), so it never collides with the 256-byte alphabet
    (seeds 0..255). The role half of the role-filler bind in
    :func:`klein4_encode_bytes` — an internal helper (a seeded
    :func:`klein4_random`, so not a separately-exposed public op).
    """
    D = int(D)
    if D <= 0:
        raise ValueError("hdc._klein4_pos_key: D must be positive")
    p = int(pos)
    if p < 0:
        raise ValueError(f"hdc._klein4_pos_key: pos must be ≥ 0; got {p}")
    return klein4_random(D, seed=_KLEIN4_POS_SEED_BASE + p)


def klein4_encode_bytes(data, D):
    """Byte-composed Klein-4 vector (UPSTREAM §60; F864): a bundle of
    POSITION-BOUND per-byte random vectors —
    ``bundle_i( klein4_bind(klein4_random(D, seed=byte_i), pos_key(D, i)) )``.

    Each byte ``b`` maps to ``klein4_random(D, seed=b)`` (the 256-byte vocab);
    binding with a deterministic position role-vector (an internal seeded
    :func:`klein4_random`) gives the role-filler, and the per-byte binds are
    bundled into one :class:`HV`. This restores **morphology** —
    ``klein4_similarity(encode_bytes(b"cat"), encode_bytes(b"cats"))`` ≫ the
    Klein-4 chance level, because the shared prefix bytes occupy the same
    positions — while stripping the word-atomic English/whitespace privilege
    (it hashes raw UTF-8, the universal-script alphabet). The language core is
    byte-level; an English kernel sits on top (F764). numpy-free.

    Args:
        data: The byte string to encode (``bytes`` / ``bytearray``; a ``str``
            is UTF-8 encoded). Must be non-empty.
        D: Vector dimension (positive).
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif not isinstance(data, (bytes, bytearray)):
        raise TypeError(
            "hdc.klein4_encode_bytes: data must be bytes / bytearray / str")
    if len(data) == 0:
        raise ValueError("hdc.klein4_encode_bytes: data must be non-empty")
    D = int(D)
    if D <= 0:
        raise ValueError("hdc.klein4_encode_bytes: D must be positive")
    bound = [klein4_bind(klein4_random(D, seed=b), _klein4_pos_key(D, i))
             for i, b in enumerate(data)]
    return klein4_bundle(*bound)


def _klein4_check(a, b, mode, op):
    """Shared validation for the klein4 match-fraction family — coerce both to
    klein4 buffers, length-match, mode-check; returns ``(a, b, n)``."""
    a = _as_klein4_buf(a, op)
    b = _as_klein4_buf(b, op)
    if len(a) != len(b):
        raise ValueError(
            f"hdc.{op}: lengths must match (got {len(a)} vs {len(b)})")
    if mode not in ("chunk", "chirality"):
        raise ValueError(
            f"{op}: mode must be 'chunk' or 'chirality'; got {mode!r}")
    return a, b, len(a)


def _klein4_match_count_core(a, b):
    """The exact integer count of positions where ``a == b`` (native fast path
    when present, else pure-Python). The blow-up-free quantity recall ranks on
    (F868): ``similarity = count / len``."""
    if len(a) >= 1 and _native.has_native_klein4_bind():
        c = _klein4_match_count_native(a, b)
        if c is not None:
            return c
    return sum(1 for x, y in zip(a, b) if x == y)


def klein4_similarity(a, b, *, sectors=None, parallel=None, mode="chunk") -> "Q":
    """Klein-4 similarity: fraction of positions where ``a == b`` (0 = orthogonal,
    1 = identical) — the exact rational :class:`~srmech.amsc.q.Q`. All four
    states are informative — there is no skip state.

    The similarity is exactly ``matches / D`` with both integers, so the return
    is the exact ``Q`` carrier: it compares like a float (``klein4_similarity(a,
    a) == 1.0``), ranks correctly (``max`` over candidates is exact), and
    collapses to a decimal only at the display boundary via ``float(s)`` — never
    a lossy mid-cascade ``float`` (the stay-rational discipline, F868,
    `[[feedback_stay_rational_collapse_only_at_display]]`). For the raw integer
    count (the blow-up-free recall-ranking key) use :func:`klein4_match_count`.

    The rc13 ``sectors=`` / ``parallel=`` / ``mode=`` flag fans the comparison
    across ≤4 concurrent lanes (default-ON at ≥4 cores) and ALWAYS returns the
    same value as the serial op. ``mode="chunk"`` (default) splits the positions
    and sums per-slice match counts (bit-identical); ``mode="chirality"`` runs
    the F233 4-sector dispatch and recombines via **sector-0** (value-transparent
    — XOR-flipping both sides preserves equality, so every sector equals the
    plain similarity anyway).
    """
    a, b, n = _klein4_check(a, b, mode, "klein4_similarity")
    _klein4_resolve_sectors(sectors, parallel)  # validate the lane flags
    if n == 0:
        return Q(0, 1)
    return Q(_klein4_match_count_core(a, b), n)


def klein4_match_count(a, b, *, sectors=None, parallel=None, mode="chunk") -> int:
    """Klein-4 match count: the **raw integer** number of positions where
    ``a == b`` (UPSTREAM §61; F868). ``klein4_similarity = count / len(a)``.

    This is the float-free, blow-up-free quantity recall ranks on — argmax over
    integer counts needs no division and no decimal (F868 mechanism #1), so the
    resonator never has to leave the integers. The C kernel already computes this
    count before its float divide, so exposing it is additive and C-paired
    (native ``srmech_klein4_match_count``).
    """
    a, b, _n = _klein4_check(a, b, mode, "klein4_match_count")
    _klein4_resolve_sectors(sectors, parallel)
    return _klein4_match_count_core(a, b)


def klein4_bundle_accumulate(acc, v):
    """Fold ONE Klein-4 vector ``v`` into a fixed-width accumulator — the STREAMING
    form of the batch :func:`klein4_bundle` (UPSTREAM §50; F758).

    The batch bundle needs every vector resident at once; this folds one at a time
    into a bounded per-coordinate symbol tally, so a holographic store of N
    relationships **never materialises the N inputs** and stays fixed-width (it
    grows with the #coordinates ``D``, not the #folded vectors). That is the fix for
    "why is the HDC object growing to gigs?" — superposition, not an explicit edge
    list.

    ``acc`` is an :class:`array.array` of type ``'I'`` (uint32), width ``1 + 2*D``:
    ``acc[0]`` is the count ``n`` of folded vectors; ``acc[1 : 1+D]`` and
    ``acc[1+D : 1+2*D]`` are the per-coordinate running 1-counts of bit-0 and bit-1.
    Pass ``acc=None`` on the first fold to create a fresh accumulator sized to ``v``.
    Returns ``acc`` (mutated IN PLACE and returned, so ``acc =
    klein4_bundle_accumulate(acc, v)`` reads cleanly in a loop). The accumulator is
    the caller's memory — its width is the architecture (``1 + 2*D`` uint32), no
    compiled-in cap. Native-dispatched when present (the standalone-C kernel runs
    the fold at corpus scale); pure-Python is the complete alternative.
    """
    buf = _as_klein4_buf(v, "klein4_bundle_accumulate")
    d = len(buf)
    if d == 0:
        raise ValueError("hdc.klein4_bundle_accumulate: vector must be non-empty")
    if acc is None:
        acc = array("I", bytes(4 * (1 + 2 * d)))   # n + c0[D] + c1[D], all zero
    elif len(acc) != 1 + 2 * d:
        raise ValueError(
            f"hdc.klein4_bundle_accumulate: acc width {(len(acc) - 1) // 2} != "
            f"vector length {d} (an accumulator is bound to one dimension)"
        )
    if _native.HAS_NATIVE and hasattr(
        _native.LIB, "srmech_klein4_bundle_accumulate"
    ):
        acc_c = (ctypes.c_uint32 * len(acc)).from_buffer(acc)
        v_c = (ctypes.c_uint8 * d).from_buffer_copy(buf)
        rc = _native.LIB.srmech_klein4_bundle_accumulate(acc_c, v_c, d)
        if rc != _native.SRMECH_OK:
            raise ValueError(
                f"srmech_klein4_bundle_accumulate returned status {rc}"
            )
        return acc
    # Pure-Python alternative (no C): per-coordinate 2-bit running tally.
    acc[0] += 1
    for i in range(d):
        x = buf[i]
        acc[1 + i] += x & 1
        acc[1 + d + i] += (x >> 1) & 1
    return acc


def klein4_bundle_resolve(acc):
    """Resolve a fixed-width accumulator (:func:`klein4_bundle_accumulate`) to the
    bundled Klein-4 vector — argmax-per-coordinate (UPSTREAM §50; F758).

    Per coordinate, each of the 2 bits is set iff its 1-count is STRICTLY greater
    than ``n // 2`` (an exact tie → 0) — **bit-identical** to
    :func:`klein4_bundle` over the same vectors. Returns the :class:`HV` carrier
    (the SAME return as :func:`klein4_bundle`), so a resolved bundle drops straight
    into a genome leaf (a tome-leaf, §50.1) or a :func:`klein4_similarity` cleanup.
    An empty accumulator (``n == 0``) resolves to the all-zero vector. Native-
    dispatched when present; pure-Python is the complete alternative.
    """
    if acc is None or len(acc) < 3 or (len(acc) % 2) == 0:
        raise ValueError(
            "hdc.klein4_bundle_resolve: acc must be a (1 + 2*D) uint32 accumulator"
        )
    d = (len(acc) - 1) // 2
    if _native.HAS_NATIVE and hasattr(_native.LIB, "srmech_klein4_bundle_resolve"):
        out = (ctypes.c_uint8 * d)()
        acc_c = (ctypes.c_uint32 * len(acc)).from_buffer_copy(acc)
        rc = _native.LIB.srmech_klein4_bundle_resolve(acc_c, out, d)
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_klein4_bundle_resolve returned status {rc}")
        return HV(array("B", bytes(out)), sectors=4)
    # Pure-Python alternative (no C): strict per-bit majority, tie → 0.
    half = acc[0] // 2
    out = array("B", bytes(d))
    for i in range(d):
        b0 = 1 if acc[1 + i] > half else 0
        b1 = 1 if acc[1 + d + i] > half else 0
        out[i] = (b1 << 1) | b0
    return HV(out, sectors=4)


def _cooc_token_seed(token, base_seed):
    """Deterministic 32-bit seed for a token's atomic Klein-4 code — FNV-1a over the
    token's UTF-8 bytes, mixed with ``base_seed``. Stable across runs and streams so
    a co-occurrence readout reconstructs the same code (the cleanup key)."""
    h = 0x811C9DC5
    for byte in str(token).encode("utf-8"):
        h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
    return (h ^ (base_seed & 0xFFFFFFFF)) & 0xFFFFFFFF


def cooccurrence_fold(tokens, *, window, dim, seed=0):
    """Holographic co-occurrence store — the §50 DUAL of the explicit-edge §17-U1
    ``cooccurrence_edges`` (UPSTREAM §50; F758).

    Folds every ``(token, neighbour)`` co-occurrence within ``±window`` into a
    per-token fixed-width Klein-4 bundle, WITHOUT ever building the edge list, so
    the store grows with the **VOCABULARY** (corpus-sublinear, Heaps' law) not the
    **#edges** (corpus-linear). Each distinct token gets a stable random atomic code
    (``klein4_random(dim, seed=…)`` keyed deterministically by the token, §
    :func:`_cooc_token_seed`); a token's bundle is the
    :func:`klein4_bundle_accumulate` superposition of its co-occurring neighbours'
    codes.

    Returns ``{"bundles": {token: HV}, "codes": {token: HV}, "vocab": [token, …],
    "n_tokens": int}``. Read out a relationship with ``klein4_similarity(
    result["bundles"][a], result["codes"][b])`` — high similarity ⇒ ``b`` co-occurs
    with ``a`` (cleanup memory). The bundle is LOSSY (superposition crosstalk; F584)
    — the bounded associative TAIL to §17-U1's small exact working set; together the
    two are the F119/F529 two-tier at the srmech-primitive level.
    """
    if window < 1:
        raise ValueError(f"hdc.cooccurrence_fold: window must be >= 1; got {window}")
    if dim < 1:
        raise ValueError(f"hdc.cooccurrence_fold: dim must be >= 1; got {dim}")
    toks = list(tokens)
    n = len(toks)
    codes = {}
    vocab = []

    def code_for(tok):
        c = codes.get(tok)
        if c is None:
            c = klein4_random(dim, seed=_cooc_token_seed(tok, seed))
            codes[tok] = c
            vocab.append(tok)
        return c

    for tok in toks:               # stable vocab order = first appearance
        code_for(tok)

    # Native fast-path (rc165): the corpus-linear windowed fold runs in ONE C
    # call — the per-token string→code mapping above stays Python (vocab-scale,
    # sublinear), only the O(n·window·dim) accumulation goes native. Same
    # accumulators, so the resolved bundles are bit-identical to the loop below.
    if _native.has_native_klein4_fold() and n >= 2:
        m = len(vocab)
        stride = 1 + 2 * dim
        vocab_index = {t: k for k, t in enumerate(vocab)}
        codes_buf = array("B")
        for t in vocab:            # flat m*dim code table, vocab order
            codes_buf.frombytes(bytes(_as_klein4_buf(codes[t],
                                                     "hdc.cooccurrence_fold")))
        tok_arr = array("I", (vocab_index[t] for t in toks))
        out_accs = array("I", bytes(4 * m * stride))
        codes_c = (ctypes.c_uint8 * len(codes_buf)).from_buffer(codes_buf)
        tok_c = (ctypes.c_uint32 * n).from_buffer(tok_arr)
        accs_c = (ctypes.c_uint32 * len(out_accs)).from_buffer(out_accs)
        rc = _native.LIB.srmech_klein4_cooccurrence_fold(
            codes_c, m, tok_c, n, window, dim, accs_c)
        if rc != _native.SRMECH_OK:
            raise ValueError(
                f"srmech_klein4_cooccurrence_fold returned status {rc}")
        bundles = {}
        for k, t in enumerate(vocab):
            base = k * stride
            if out_accs[base] > 0:          # token folded >= 1 neighbour
                bundles[t] = klein4_bundle_resolve(out_accs[base:base + stride])
        return {"bundles": bundles, "codes": codes, "vocab": vocab,
                "n_tokens": n}

    # Pure-Python alternative (no C / pre-rc165 lib): the windowed fold loop.
    accs = {}
    for i, t in enumerate(toks):
        lo = i - window if i - window > 0 else 0
        hi = i + window + 1 if i + window + 1 < n else n
        ai = accs.get(t)
        for j in range(lo, hi):
            if j != i:
                ai = klein4_bundle_accumulate(ai, code_for(toks[j]))
        if ai is not None:
            accs[t] = ai
    bundles = {t: klein4_bundle_resolve(a) for t, a in accs.items()}
    return {"bundles": bundles, "codes": codes, "vocab": vocab, "n_tokens": n}


def klein4_chirality_flip_gamma5(v):
    """Flip the γ₅ axis: XOR with the bit-1 sector mask (2)."""
    return HV(_xor_const_buf(_as_klein4_buf(v, "klein4_chirality_flip_gamma5"), 2),
              sectors=4)


def klein4_chirality_flip_omega7(v):
    """Flip the iω₇ axis: XOR with the bit-0 sector mask (1)."""
    return HV(_xor_const_buf(_as_klein4_buf(v, "klein4_chirality_flip_omega7"), 1),
              sectors=4)


def klein4_cpt_mirror(v):
    """CPT mirror: flip BOTH chirality axes (XOR with 3)."""
    return HV(_xor_const_buf(_as_klein4_buf(v, "klein4_cpt_mirror"), 3), sectors=4)


# γ₅ = bit 1 (XOR mask 2), iω₇ = bit 0 (XOR mask 1) — the SAME bit layout the
# chirality flips use. Projecting onto an axis extracts that one bit per element.
_KLEIN4_PROJECT_AXIS_BITS = {"gamma5": 1, "iomega7": 0}


def klein4_project_axis(v, *, axis="gamma5"):
    """Project a Klein-4 hypervector onto ONE chirality axis → bipolar {-1,+1}.

    The **asymptotic-DoF render** (F350/F354): the 2-DoF Klein-4 carrier
    (γ₅ ⊕ iω₇) collapses to a 1-DoF bipolar ``{-1, +1}`` vector along the chosen
    axis — exactly the F350 bipolar render that drops the OTHER axis (and with
    it that axis's self-error-correction; F354 axis-split: the collapsed observer
    is structurally blind to errors on the projected-out axis). Per-element
    bit→sign: a clear bit (0) → ``+1``, a set bit (1) → ``-1`` (the standard
    bipolar encoding; the Class-K sign render — no ``abs()``).

    ``axis`` is a CO-EQUAL, non-privileged convention (cf. endianness): both
    ``"gamma5"`` (bit 1) and ``"iomega7"`` (bit 0) are first-class, relating by
    the Class-K axis swap. The default ``"gamma5"`` is the surviving-axis of the
    F354 collapse — a documented convention, not a privileged truth.

    Class K (asymptotic-DoF / bipolar sign render) ∘ Class C (chirality-axis
    selection). Numpy-free pure bit ops.

    Parameters
    ----------
    v
        A Klein-4 value: an :class:`HV`, ``bytes`` / ``array('B')`` / list of
        ints in ``{0, 1, 2, 3}``.
    axis
        ``"gamma5"`` (bit 1) or ``"iomega7"`` (bit 0). Co-equal.

    Returns
    -------
    list[int]
        The bipolar projection, one ``+1`` / ``-1`` per element.

    Raises
    ------
    ValueError
        If ``axis`` is neither ``"gamma5"`` nor ``"iomega7"`` (or an element is
        outside ``{0, 1, 2, 3}``, propagated from the Klein-4 validator).
    """
    try:
        shift = _KLEIN4_PROJECT_AXIS_BITS[axis]
    except (KeyError, TypeError):
        raise ValueError(
            "klein4_project_axis: axis must be 'gamma5' or 'iomega7'; "
            f"got {axis!r}"
        )
    buf = _as_klein4_buf(v, "klein4_project_axis")
    # bit 0 → +1, bit 1 → -1 — the Class-K bipolar sign render (no abs()).
    return [1 - 2 * ((x >> shift) & 1) for x in buf]


# The order-3 triality cycle on the Klein-4 carrier (the S₃ = Aut(V₄)
# generator). The three non-identity involutions cycle iω₇(1) → γ₅(2) →
# CPT(3) → iω₇(1), fixing identity(0). Pure uint8 relabel via a length-4
# lookup; applying it three times is the identity (T∘T∘T = id; T² = T⁻¹).
# Plain tuples (numpy-free; consumed by ``_table_buf``).
_KLEIN4_TRIALITY_FORWARD = (0, 2, 3, 1)
_KLEIN4_TRIALITY_INVERSE = (0, 3, 1, 2)


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
    buf = _as_klein4_buf(v, "klein4_triality_cycle")
    if len(buf) >= 1 and _native.has_native_klein4_triality_cycle():  # §53: native
        out = _klein4_triality_native(buf, inverse)
        if out is not None:
            return HV(out, sectors=4)
    table = _KLEIN4_TRIALITY_INVERSE if inverse else _KLEIN4_TRIALITY_FORWARD
    return HV(_table_buf(buf, table), sectors=4)


def klein4_sector_count(v):
    """Per-sector occupancy ``[n0, n1, n2, n3]`` — substrate attestation of the
    chirality-sector distribution. Returns a stdlib ``list[int]`` (numpy-free)."""
    buf = _as_klein4_buf(v, "klein4_sector_count")
    counts = [0, 0, 0, 0]
    for x in buf:
        counts[x] += 1
    return counts


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
    buf = _as_klein4_buf(v, "klein4_holographic_encode")
    if not isinstance(replicas, int) or isinstance(replicas, bool) or replicas < 2:
        raise ValueError(f"replicas must be int >= 2; got {replicas!r}")
    out = array("B")
    for _ in range(replicas):
        out.extend(buf)
    return HV(out, sectors=4)


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
    s = _store_buf(store, "klein4_holographic_decode")
    if not isinstance(replicas, int) or isinstance(replicas, bool) or replicas < 2:
        raise ValueError(f"replicas must be int >= 2; got {replicas!r}")
    n = len(s)
    if n == 0 or n % replicas != 0:
        raise ValueError(
            f"store length {n} must be a positive multiple of replicas {replicas}"
        )
    D = n // replicas  # block s[r*D : (r+1)*D] is replica r (replica-major)
    if erased is None:
        # Blind: per-position majority over the ``replicas`` copies (ties → lowest).
        out = array("B", bytes(D))
        for i in range(D):
            counts = [0, 0, 0, 0]
            for r in range(replicas):
                counts[s[r * D + i]] += 1
            best, best_c = 0, counts[0]
            for state in range(1, 4):
                if counts[state] > best_c:
                    best, best_c = state, counts[state]
            out[i] = best
        return HV(out, sectors=4)
    # Known-location erasure: first surviving replica per position.
    mask = list(erased)  # bool per store position (list / np bool array / etc.)
    if len(mask) != n:
        raise ValueError(f"erased mask length {len(mask)} != store length {n}")
    out = array("B", bytes(D))
    for i in range(D):
        chosen = None
        for r in range(replicas):
            if not mask[r * D + i]:
                chosen = s[r * D + i]
                break
        if chosen is None:
            raise ValueError(
                "klein4_holographic_decode: a position has all replicas erased; "
                "unrecoverable (erasure exceeded (replicas-1)/replicas)"
            )
        out[i] = chosen
    return HV(out, sectors=4)


# ---------------------------------------------------------------------------
# Explicit order-3 triality-recursion corrector (#797 op (a1); F359 contract).
#
# The order-2 Klein-4 store is k=2-DETECT natively (F294: no Z3, 3∤4) — two
# views can DETECT a mismatch but cannot say which is right. k=3-CORRECT needs
# the order-3 triality (τ³=I) past the 4-cap: this is the EXPLICIT corrector
# path (op (a2) klein4_holographic_* is the *measured substitute* that corrects
# with no Z3). The store carries the order-3 triality ORBIT of the value —
# {v, T(v), T²(v)} for T = ``klein4_triality_cycle`` — so the third vote is the
# triality orbit's third element (block2 = T²v), NOT an external 3rd render.
# Decode brings all three orbit-blocks back to the common frame by INVERTING
# the triality (T⁻¹ on block1, T⁻² = T on block2) and takes the 2-of-3 majority,
# correcting one error. The correction is ATTRIBUTABLE to the order-3 op: with
# the triality disabled (no inverse), the three raw orbit-blocks {v, Tv, T²v}
# disagree on every non-zero sector → majority mangles them → you fall back to
# k=2-DETECT. Class-home: M (the orbit replication bind) ∘ C (orientation:
# T⁻¹/T to the common frame) ∘ C (the majority selection). No abs().
#
# F359 5-bar contract (the falsifiable bars; the canonical §20/F359 figures are
# NOT on the read-only research branch, so this is built to the bars):
#   (1) blind unknown-location correction beats the F353 holographic 0.25
#       baseline (single-error recovery is exact);
#   (2) the 3rd vote is the order-3 triality orbit of the same value;
#   (3) C/Python parity (Python-first; the standalone-C peer is the next voxel);
#   (4) disable the order-3 op → degrade to k=2-DETECT (correction attributable
#       to the triality, not to plain replication);
#   (5) WIDTH-step only — one 4-cap crossing (order-2 → order-3). The continuum
#       count-recursion is open math; ``depth != 1`` is out-of-domain and RAISES
#       rather than fabricating a recursion the substrate doesn't license.
# ---------------------------------------------------------------------------

_KLEIN4_TRIALITY_ORBIT = 3   # the order-3 triality orbit has exactly 3 elements


def klein4_triality_encode(v):
    """Encode a Klein-4 store as its order-3 triality orbit (#797 op (a1); F359).

    Returns a length ``len(v) * 3`` uint8 store holding the order-3 triality
    orbit ``[v, T(v), T²(v)]`` for ``T = klein4_triality_cycle`` (orbit-major).
    Paired with :func:`klein4_triality_correct`: the third block (``T²v``) is the
    triality orbit's third element — the order-3 third vote past the order-2
    4-cap — NOT an externally-rendered copy.

    Class-home **M** (orbit replication bind) ∘ **I** (the order-3 cycle that
    generates the orbit). No ``abs()``; pure uint8 relabel.

    Args:
        v: A Klein-4 hypervector (uint8, elements ``{0, 1, 2, 3}``).

    Returns:
        uint8 store of length ``len(v) * 3`` = ``[v | T(v) | T²(v)]``.
    """
    buf = _as_klein4_buf(v, "klein4_triality_encode")
    t1 = _table_buf(buf, _KLEIN4_TRIALITY_FORWARD)   # T(v)
    t2 = _table_buf(t1, _KLEIN4_TRIALITY_FORWARD)    # T²(v)
    out = array("B", buf)
    out.extend(t1)
    out.extend(t2)
    return HV(out, sectors=4)


def klein4_triality_correct(store, *, depth=1):
    """Correct a Klein-4 store via the order-3 triality 2-of-3 majority (op (a1)).

    Inverse-with-correction of :func:`klein4_triality_encode`. Reshapes the
    store into the three orbit-blocks ``[b0, b1, b2]`` (supposed ``[v, Tv, T²v]``),
    brings each back to the common ``v``-frame by INVERTING the triality —
    ``b0``, ``T⁻¹(b1)``, ``T⁻²(b2) = T(b2)`` — and takes the per-position 2-of-3
    majority (ties broken toward the lowest sector index). One corrupted block
    (or one error) is outvoted by the two agreeing frames, so a single error is
    corrected exactly: k=3-CORRECT where the bare order-2 store is only
    k=2-DETECT.

    The correction is **attributable to the order-3 triality**: without the
    inverse-to-frame step the three raw orbit-blocks ``{v, Tv, T²v}`` disagree on
    every non-zero sector, so a naive majority does not recover ``v`` (bar 4).

    WIDTH-step only (bar 5): ``depth`` must be 1 (the single order-2 → order-3
    4-cap crossing). The continuum count-recursion is open math; any other
    ``depth`` raises ``NotImplementedError`` rather than fabricating it.

    Args:
        store: uint8 store of length divisible by 3 (from
            :func:`klein4_triality_encode`).
        depth: Recursion depth; only ``1`` (the width-step) is in-domain.

    Returns:
        The reconstructed length ``len(store)//3`` uint8 vector.

    Raises:
        NotImplementedError: if ``depth != 1`` (continuum-recursion is out of
            domain — the width-only contract, F359 bar 5).
        ValueError: if the store length is not a positive multiple of 3.
    """
    if depth != 1:
        raise NotImplementedError(
            "klein4_triality_correct: only the width-step (depth=1) is in "
            "domain; the continuum count-recursion is open math (F359 bar 5)"
        )
    s = _as_klein4_buf(store, "klein4_triality_correct")
    n = len(s)
    if n % _KLEIN4_TRIALITY_ORBIT != 0:
        raise ValueError(
            f"store length {n} must be a positive multiple of 3 "
            "(the order-3 triality orbit)"
        )
    D = n // _KLEIN4_TRIALITY_ORBIT
    b0 = s[0:D]
    b1 = s[D:2 * D]
    b2 = s[2 * D:3 * D]
    # Invert the triality to bring every orbit-block back to the v-frame:
    #   frame0 = b0; frame1 = T⁻¹(b1) = T²(b1); frame2 = T⁻²(b2) = T(b2).
    frame1 = _table_buf(b1, _KLEIN4_TRIALITY_INVERSE)  # T⁻¹(Tv) = v
    frame2 = _table_buf(b2, _KLEIN4_TRIALITY_FORWARD)  # T⁻²(T²v) = T(T²v) = v
    # Per-position 2-of-3 majority over the four Klein-4 sectors (ties → lowest).
    out = array("B", bytes(D))
    for i in range(D):
        counts = [0, 0, 0, 0]
        counts[b0[i]] += 1
        counts[frame1[i]] += 1
        counts[frame2[i]] += 1
        best, best_c = 0, counts[0]
        for state in range(1, 4):
            if counts[state] > best_c:
                best, best_c = state, counts[state]
        out[i] = best
    return HV(out, sectors=4)


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
    """Bare octonion conjugate (no validation; for internal recursion).

    rc125 (numpy-free): operates on a plain ``list[float]`` — negate the seven
    imaginary axes, keep the real anchor ``arr[0]`` (Class C, no ``abs()``)."""
    return [arr[0]] + [-arr[i] for i in range(1, len(arr))]


def _loop_bind_raw(a_, b_):
    """Bare Cayley-Dickson product (no validation; the recursion engine).

    rc125 (numpy-free): operates on plain ``list[float]`` — the half-splits are
    list slices and the assembly is list ``+`` concatenation (the prior
    concatenation of two halves)."""
    n = len(a_) // 2
    if n == 0:
        return [a_[0] * b_[0]]
    a, b = a_[:n], a_[n:]
    c, d = b_[:n], b_[n:]
    lo = _vsub(_loop_bind_raw(a, c), _loop_bind_raw(_loop_conj_raw(d), b))
    hi = _vadd(_loop_bind_raw(d, a), _loop_bind_raw(b, _loop_conj_raw(c)))
    return lo + hi


def _vadd(u, v):
    """Element-wise add of two equal-length float lists (numpy-free)."""
    return [u[i] + v[i] for i in range(len(u))]


def _vsub(u, v):
    """Element-wise subtract of two equal-length float lists (numpy-free)."""
    return [u[i] - v[i] for i in range(len(u))]


def _vscale(u, s):
    """Scalar-multiply a float list (numpy-free)."""
    return [x * s for x in u]


def _as_loop(v, op: str):
    """Coerce to a 1-D ``list[float]`` whose length is a power of two (the
    Cayley-Dickson recursion bottoms out at length 1). Numpy-free."""
    try:
        arr = [float(x) for x in v]
    except TypeError as exc:  # 0-D scalar / non-iterable
        raise AssertionError(f"{op}: expected a 1-D vector") from exc
    n = len(arr)
    assert n >= 1 and (n & (n - 1)) == 0, (
        f"{op}: length {n} is not a power of two (Cayley-Dickson carrier)"
    )
    return arr


def _loop_basis(i, dim):
    """The ``i``-th standard basis vector of length ``dim`` as a ``list[float]``."""
    v = [0.0] * dim
    v[i] = 1.0
    return v


def _reject_hd_block_misuse(arr, op):
    """Guard the single-element loop ops against silent HD-vector misuse (F-§12.1).

    ``loop_conj`` / ``loop_inv`` act on ONE Cayley-Dickson element. An HD
    block-octonion vector (a multiple of LOOP_DIM wider than one octonion)
    silently passes ``_as_loop`` — 2048 = 256·8 is also a power of two — and
    would be treated as a single 2048-D element, so the GLOBAL conj/inv is NOT
    the per-block octonion result the HD layout means (err ≈ ‖·‖, no exception).
    Raise instead, and point at the per-block ``*_hd`` op. ``arr`` is a
    ``list[float]`` (numpy-free)."""
    size = len(arr)
    if size > LOOP_DIM and size % LOOP_DIM == 0:
        raise ValueError(
            f"{op}: length {size} is a multiple of LOOP_DIM ({LOOP_DIM}) "
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


def _cbuf(seq, n):
    """A ``(c_double * n)`` ctypes buffer filled from ``seq`` (numpy-free
    marshalling for the native loop ops — no numpy contiguous-array copy)."""
    return (ctypes.c_double * n)(*(float(v) for v in seq))


def _from_cbuf(c_out, n):
    """A ``list[float]`` copy of a ``(c_double * n)`` native output buffer."""
    return [float(c_out[i]) for i in range(n)]


def _try_native_loop_conj(arr):
    if len(arr) != LOOP_DIM or not _loop_native_ready("srmech_loop_conj_f64"):
        return None
    c_x = _cbuf(arr, LOOP_DIM)
    c_out = (ctypes.c_double * LOOP_DIM)()
    rc = _native.LIB.srmech_loop_conj_f64(
        ctypes.cast(c_x, _DBLP), ctypes.c_size_t(LOOP_DIM),
        ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(c_out, LOOP_DIM)


def _try_native_loop_bind(a_, b_):
    if (len(a_) != LOOP_DIM or len(b_) != LOOP_DIM
            or not _loop_native_ready("srmech_loop_bind_f64")):
        return None
    c_x = _cbuf(a_, LOOP_DIM)
    c_y = _cbuf(b_, LOOP_DIM)
    c_out = (ctypes.c_double * LOOP_DIM)()
    rc = _native.LIB.srmech_loop_bind_f64(
        ctypes.cast(c_x, _DBLP), ctypes.cast(c_y, _DBLP),
        ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(c_out, LOOP_DIM)


def _try_native_loop_bind_hd(a_, b_):
    """Whole-array native HD bind — ONE ``srmech_loop_bind_hd_f64`` call binds
    ALL NB 8-blocks (internally N-way-SIMD across blocks: AVX W=4 / SSE2 W=2 /
    scalar remainder), replacing the Python per-block ``loop_bind`` loop. a_,
    b_ are flat float ``list``\\ s of equal length, a positive multiple of
    LOOP_DIM. Returns the flat result (NB·8) as a ``list[float]``, or None to
    fall back to the per-block path (lib absent / symbol missing / non-OK).
    rc125 (numpy-free): marshals via ``(c_double * n)`` ctypes buffers — pointers
    cross once (the F292 graft's win); ``out`` is a fresh buffer, so it never
    aliases the inputs (the C contract)."""
    n = len(a_)
    if (n == 0 or n % LOOP_DIM != 0 or len(b_) != n
            or not _loop_native_ready("srmech_loop_bind_hd_f64")):
        return None
    nb = n // LOOP_DIM
    xc = _cbuf(a_, n)
    yc = _cbuf(b_, n)
    out = (ctypes.c_double * n)()
    rc = _native.LIB.srmech_loop_bind_hd_f64(
        ctypes.cast(xc, _DBLP), ctypes.cast(yc, _DBLP),
        ctypes.c_size_t(nb), ctypes.cast(out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(out, n)


def _try_native_loop_conj_hd(a_):
    """Whole-array native HD conjugate — ONE ``srmech_loop_conj_hd_f64`` call
    conjugates ALL NB 8-blocks, replacing the Python per-block ``_loop_conj_raw``
    loop. a_ is a flat float ``list``, a positive multiple of LOOP_DIM. Returns
    the flat result as a ``list[float]``, or None to fall back (numpy-free
    ctypes marshalling)."""
    n = len(a_)
    if (n == 0 or n % LOOP_DIM != 0
            or not _loop_native_ready("srmech_loop_conj_hd_f64")):
        return None
    nb = n // LOOP_DIM
    xc = _cbuf(a_, n)
    out = (ctypes.c_double * n)()
    rc = _native.LIB.srmech_loop_conj_hd_f64(
        ctypes.cast(xc, _DBLP), ctypes.c_size_t(nb), ctypes.cast(out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(out, n)


def _try_native_loop_inv_hd(a_):
    """Whole-array native HD Moufang inverse — ONE ``srmech_loop_inv_hd_f64`` call
    inverts ALL NB 8-blocks. None on fall-back; a zero block makes the C peer
    return BAD_INPUT → None here → the Python fallback raises (the contract).
    rc125 (numpy-free): ctypes-buffer marshalling, ``list[float]`` out."""
    n = len(a_)
    if (n == 0 or n % LOOP_DIM != 0
            or not _loop_native_ready("srmech_loop_inv_hd_f64")):
        return None
    nb = n // LOOP_DIM
    xc = _cbuf(a_, n)
    out = (ctypes.c_double * n)()
    rc = _native.LIB.srmech_loop_inv_hd_f64(
        ctypes.cast(xc, _DBLP), ctypes.c_size_t(nb), ctypes.cast(out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(out, n)


def _try_native_loop_unbind_hd(a_, b_):
    """Whole-array native HD LEFT-unbind — ONE ``srmech_loop_unbind_hd_f64`` call
    computes conj(aₖ)·bₖ over ALL NB blocks. None on fall-back. rc125
    (numpy-free): ctypes-buffer marshalling, ``list[float]`` out."""
    n = len(a_)
    if (n == 0 or n % LOOP_DIM != 0 or len(b_) != n
            or not _loop_native_ready("srmech_loop_unbind_hd_f64")):
        return None
    nb = n // LOOP_DIM
    ac = _cbuf(a_, n)
    bc = _cbuf(b_, n)
    out = (ctypes.c_double * n)()
    rc = _native.LIB.srmech_loop_unbind_hd_f64(
        ctypes.cast(ac, _DBLP), ctypes.cast(bc, _DBLP),
        ctypes.c_size_t(nb), ctypes.cast(out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(out, n)


def _try_native_loop_runbind_hd(a_, b_):
    """Whole-array native HD RIGHT-unbind — ONE ``srmech_loop_runbind_hd_f64``
    call computes bₖ·conj(aₖ) over ALL NB blocks. None on fall-back. rc125
    (numpy-free): ctypes-buffer marshalling, ``list[float]`` out."""
    n = len(a_)
    if (n == 0 or n % LOOP_DIM != 0 or len(b_) != n
            or not _loop_native_ready("srmech_loop_runbind_hd_f64")):
        return None
    nb = n // LOOP_DIM
    ac = _cbuf(a_, n)
    bc = _cbuf(b_, n)
    out = (ctypes.c_double * n)()
    rc = _native.LIB.srmech_loop_runbind_hd_f64(
        ctypes.cast(ac, _DBLP), ctypes.cast(bc, _DBLP),
        ctypes.c_size_t(nb), ctypes.cast(out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(out, n)


def _try_native_loop_inv(arr):
    if len(arr) != LOOP_DIM or not _loop_native_ready("srmech_loop_inv_f64"):
        return None
    c_x = _cbuf(arr, LOOP_DIM)
    c_out = (ctypes.c_double * LOOP_DIM)()
    rc = _native.LIB.srmech_loop_inv_f64(
        ctypes.cast(c_x, _DBLP), ctypes.c_size_t(LOOP_DIM),
        ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(c_out, LOOP_DIM)


def _try_native_cross7(a_, b_):
    if (len(a_) != LOOP_DIM or len(b_) != LOOP_DIM
            or not _loop_native_ready("srmech_cross7_f64")):
        return None
    c_x = _cbuf(a_, LOOP_DIM)
    c_y = _cbuf(b_, LOOP_DIM)
    c_out = (ctypes.c_double * LOOP_DIM)()
    rc = _native.LIB.srmech_cross7_f64(
        ctypes.cast(c_x, _DBLP), ctypes.cast(c_y, _DBLP),
        ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(c_out, LOOP_DIM)


def _try_native_g2_three_form(xa, ya, za):
    if (len(xa) != LOOP_DIM or len(ya) != LOOP_DIM or len(za) != LOOP_DIM
            or not _loop_native_ready("srmech_g2_three_form_f64")):
        return None
    c_x = _cbuf(xa, LOOP_DIM)
    c_y = _cbuf(ya, LOOP_DIM)
    c_z = _cbuf(za, LOOP_DIM)
    c_out = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_g2_three_form_f64(
        ctypes.cast(c_x, _DBLP), ctypes.cast(c_y, _DBLP),
        ctypes.cast(c_z, _DBLP), ctypes.c_size_t(LOOP_DIM),
        ctypes.byref(c_out))
    if rc != _native.SRMECH_OK:
        return None
    return float(c_out.value)


def _try_native_loop_associator(aa, bb, cc):
    if (len(aa) != LOOP_DIM or len(bb) != LOOP_DIM or len(cc) != LOOP_DIM
            or not _loop_native_ready("srmech_loop_associator_f64")):
        return None
    c_a = _cbuf(aa, LOOP_DIM)
    c_b = _cbuf(bb, LOOP_DIM)
    c_c = _cbuf(cc, LOOP_DIM)
    c_out = (ctypes.c_double * LOOP_DIM)()
    rc = _native.LIB.srmech_loop_associator_f64(
        ctypes.cast(c_a, _DBLP), ctypes.cast(c_b, _DBLP), ctypes.cast(c_c, _DBLP),
        ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    return _from_cbuf(c_out, LOOP_DIM)


def _flat_to_mat(flat):
    """A ``LOOP_DIM × LOOP_DIM`` real :class:`Mat` from a row-major flat list
    (the native loop-operator output; numpy-free)."""
    rows = [[flat[k * LOOP_DIM + j] for j in range(LOOP_DIM)]
            for k in range(LOOP_DIM)]
    return Mat.from_rows(rows, is_complex=False)


def _try_native_loop_left_op(arr):
    if len(arr) != LOOP_DIM or not _loop_native_ready("srmech_loop_left_op_f64"):
        return None
    c_a = _cbuf(arr, LOOP_DIM)
    c_out = (ctypes.c_double * (LOOP_DIM * LOOP_DIM))()
    rc = _native.LIB.srmech_loop_left_op_f64(
        ctypes.cast(c_a, _DBLP), ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    flat = [float(c_out[i]) for i in range(LOOP_DIM * LOOP_DIM)]
    return _flat_to_mat(flat)


def _try_native_loop_right_op(arr):
    if len(arr) != LOOP_DIM or not _loop_native_ready("srmech_loop_right_op_f64"):
        return None
    c_a = _cbuf(arr, LOOP_DIM)
    c_out = (ctypes.c_double * (LOOP_DIM * LOOP_DIM))()
    rc = _native.LIB.srmech_loop_right_op_f64(
        ctypes.cast(c_a, _DBLP), ctypes.c_size_t(LOOP_DIM), ctypes.cast(c_out, _DBLP))
    if rc != _native.SRMECH_OK:
        return None
    flat = [float(c_out[i]) for i in range(LOOP_DIM * LOOP_DIM)]
    return _flat_to_mat(flat)


def loop_conj(x):
    """Octonion conjugate x̄ — negate the imaginary part, keep the real anchor
    ``x[0]``. The Class-C orientation flip that powers the unbind. Single
    element only — an HD block-octonion vector raises (use ``loop_conj_hd``).
    Dispatches to the native ``srmech_loop_conj_f64`` for the dim-8 octonion."""
    arr = _as_loop(x, "loop_conj")
    _reject_hd_block_misuse(arr, "loop_conj")
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

    rc125 (numpy-free): operands are coerced to ``list[float]`` and the result is
    a ``list[float]`` (was an ndarray).
    """
    a_ = _as_loop(x, "loop_bind")
    b_ = _as_loop(y, "loop_bind")
    assert len(a_) == len(b_), "loop_bind: operands must have equal length"
    native = _try_native_loop_bind(a_, b_)
    if native is not None:
        return native
    return _loop_bind_raw(a_, b_)


def loop_inv(x):
    """Moufang inverse x⁻¹ = x̄ / ⟨x,x⟩ — the unbind key. For a unit octonion
    (⟨x,x⟩ = 1) this is just the conjugate; ``loop_bind(x, loop_inv(x))`` = e₀.
    Class-K clean: the norm² gate, never ``abs()``. Single element only — an HD
    block-octonion vector raises (use ``loop_inv_hd``).

    rc125 (numpy-free): the norm² gate is the numpy-free ``mat_dot`` (the
    prior numpy-carrier ``dense_dot_real``); returns a ``list[float]``."""
    arr = _as_loop(x, "loop_inv")
    _reject_hd_block_misuse(arr, "loop_inv")
    from srmech.amsc.laplacian import mat_dot  # numpy-free inner product
    nsq = mat_dot(arr, arr)
    assert nsq > 0.0, "loop_inv: zero vector has no inverse (Moufang division)"
    native = _try_native_loop_inv(arr)
    if native is not None:
        return native
    return _vscale(_loop_conj_raw(arr), 1.0 / nsq)


def loop_left_op(a):
    """Left-multiplication operator L_a(x) = a·x (the (4:3) ordering) as a
    dim×dim :class:`Mat`. L_a ≠ R_a ≠ R_aᵀ — the operational chirality.

    rc125 (numpy-free): returns a real ``Mat`` (was an ndarray); the fallback
    column-stacks the per-basis binds into a row-major nested list."""
    arr = _as_loop(a, "loop_left_op")
    dim = len(arr)
    native = _try_native_loop_left_op(arr)
    if native is not None:
        return native
    cols = [_loop_bind_raw(arr, _loop_basis(k, dim)) for k in range(dim)]
    # column-stack: row i, column k is cols[k][i].
    rows = [[cols[k][i] for k in range(dim)] for i in range(dim)]
    return Mat.from_rows(rows, is_complex=False)


def loop_right_op(a):
    """Right-multiplication operator R_a(x) = x·a (the (3:4) mirror ordering) as
    a dim×dim :class:`Mat`.

    rc125 (numpy-free): returns a real ``Mat`` (was an ndarray)."""
    arr = _as_loop(a, "loop_right_op")
    dim = len(arr)
    native = _try_native_loop_right_op(arr)
    if native is not None:
        return native
    cols = [_loop_bind_raw(_loop_basis(k, dim), arr) for k in range(dim)]
    rows = [[cols[k][i] for k in range(dim)] for i in range(dim)]
    return Mat.from_rows(rows, is_complex=False)


def loop_associator(a, b, c):
    """(a·b)·c − a·(b·c) = the Class-K associator RESIDUE of the loop bind.

    Zero inside an associative (quaternionic / Fano-line) region, nonzero
    outside = the (4:3)|(3:4) boundary. Identity: ``loop_associator(a, x, b)`` =
    −(``[L_a, R_b]`` · x). The K-residue is what makes the loop bind carry order
    / nesting / direction the commutative ``klein4_bind`` XOR washes out (F274).

    rc125 (numpy-free): returns a ``list[float]`` (was an ndarray)."""
    aa = _as_loop(a, "loop_associator")
    bb = _as_loop(b, "loop_associator")
    cc = _as_loop(c, "loop_associator")
    native = _try_native_loop_associator(aa, bb, cc)
    if native is not None:
        return native
    return _vsub(_loop_bind_raw(_loop_bind_raw(aa, bb), cc),
                 _loop_bind_raw(aa, _loop_bind_raw(bb, cc)))


def cross7(x, y):
    """The 7-D cross product x×y = Im(loop_bind(x, y)) — the imaginary part of
    the octonion product (drop the e₀ real anchor). For imaginary x, y this is
    ½(x·y − y·x). Antisymmetric (x×y = −y×x); the Class-M bind ∘ Class-C
    ordering with the symmetric part Re(x·y) = −⟨x,y⟩ projected off. Identity:
    ‖x×y‖² = ‖x‖²‖y‖² − ⟨x,y⟩². Ground-truth derived FROM the shipped loop_bind
    (F281); NO new class.

    rc125 (numpy-free): returns a ``list[float]`` (was an ndarray)."""
    a_ = _as_loop(x, "cross7")
    b_ = _as_loop(y, "cross7")
    assert len(a_) == len(b_), "cross7: operands must have equal length"
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
    NO new class. Returns a scalar.

    rc125 (numpy-free): the contraction is the numpy-free ``mat_dot`` (the
    prior numpy-carrier ``dense_dot_real``)."""
    xa = _as_loop(x, "g2_three_form")
    ya = _as_loop(y, "g2_three_form")
    za = _as_loop(z, "g2_three_form")
    assert len(xa) == len(ya) and len(xa) == len(za), (
        "g2_three_form: operands must have equal length")
    native = _try_native_g2_three_form(xa, ya, za)
    if native is not None:
        return native
    from srmech.amsc.laplacian import mat_dot  # numpy-free inner product
    yz = cross7(ya, za)
    return mat_dot(xa, yz)


def _as_hd(v, op: str) -> "list":
    """Coerce ``v`` to a flat ``list[float]`` whose length is a positive
    multiple of LOOP_DIM (the HD block-octonion carrier). Numpy-free."""
    arr = [float(x) for x in v]
    n = len(arr)
    assert n and n % LOOP_DIM == 0, (
        f"{op}: length must be a positive multiple of {LOOP_DIM}")
    return arr


def _hd_blocks(arr):
    """Split a flat HD ``list[float]`` into NB length-LOOP_DIM block lists."""
    return [arr[k * LOOP_DIM:(k + 1) * LOOP_DIM]
            for k in range(len(arr) // LOOP_DIM)]


def _concat(blocks):
    """Concatenate a list of float-list blocks into one flat ``list[float]``
    (the numpy-free concatenation)."""
    out = []
    for b in blocks:
        out.extend(b)
    return out


def loop_bind_hd(x, y):
    """Block-octonion HD bind — the direct sum ⊕ of NB independent dim-8 octonion
    loop_binds (D = NB·8; the canonical HD width is 2048 = 256·8). Block-DIAGONAL:
    block k of the result is exactly the shipped ``loop_bind`` of the two k-th
    8-blocks; nothing couples blocks (#811/F289). Carries order / tree / direction
    (the F274 non-commutative structure) at NO capacity cost vs the commutative
    Klein-4 XOR bind (capacity-free, #812/F277). Class M (per-block loop_bind =
    M∘C with a Class-K residue) over a direct-sum TILE layout — NO new class.
    Operand length must be a positive multiple of LOOP_DIM (8).

    rc125 (numpy-free): operates on ``list[float]`` (was an ndarray)."""
    a_ = _as_hd(x, "loop_bind_hd")
    b_ = _as_hd(y, "loop_bind_hd")
    assert len(a_) == len(b_), "loop_bind_hd: operands must have equal length"
    native = _try_native_loop_bind_hd(a_, b_)
    if native is not None:
        return native
    xb = _hd_blocks(a_)
    yb = _hd_blocks(b_)
    return _concat([loop_bind(xb[k], yb[k]) for k in range(len(xb))])


def loop_unbind_hd(a, b):
    """The HD unbind — per-block Moufang left-division conj(a_k)·b_k. For ``a``
    built from unit-per-block octonions (the HD regime), this recovers v from
    ``loop_bind_hd(a, v)`` exactly: conj(a)·(a·v) = v by alternativity. Uses the
    shipped ``loop_conj`` + ``loop_bind`` block-wise; Class-K clean (conjugate +
    bind, no abs()). #811/F289.

    rc125 (numpy-free): operates on ``list[float]`` (was an ndarray)."""
    a_ = _as_hd(a, "loop_unbind_hd")
    b_ = _as_hd(b, "loop_unbind_hd")
    assert len(a_) == len(b_), "loop_unbind_hd: operands must have equal length"
    native = _try_native_loop_unbind_hd(a_, b_)
    if native is not None:
        return native
    ab = _hd_blocks(a_)
    bb = _hd_blocks(b_)
    return _concat([loop_bind(loop_conj(ab[k]), bb[k]) for k in range(len(ab))])


def loop_conj_hd(x):
    """Per-block HD octonion conjugate — the direct sum ⊕ of NB independent
    dim-8 ``loop_conj``s. THE missing atom under ``loop_bind_hd`` /
    ``loop_unbind_hd`` (#811/F289): the single-element ``loop_conj`` is GLOBAL
    (one Cayley-Dickson element) and silently wrong on an HD block-octonion
    vector (F-§12.1) — this is the per-block form. Class C (orientation flip)
    over the direct-sum TILE layout; NO new class. Length must be a positive
    multiple of LOOP_DIM (8).

    rc125 (numpy-free): operates on ``list[float]`` (was an ndarray)."""
    a_ = _as_hd(x, "loop_conj_hd")
    native = _try_native_loop_conj_hd(a_)
    if native is not None:
        return native
    xb = _hd_blocks(a_)
    return _concat([_loop_conj_raw(xb[k]) for k in range(len(xb))])


def loop_inv_hd(x):
    """Per-block HD Moufang inverse — the direct sum ⊕ of NB independent dim-8
    ``loop_inv``s (x̄ₖ / ⟨xₖ,xₖ⟩ per block). The per-block unbind key:
    ``loop_unbind_hd(x, loop_bind_hd(x, v)) == v``, and for ANY (not only unit)
    per-block x, ``loop_bind_hd(x, loop_inv_hd(x))`` is the per-block e₀. The
    single-element ``loop_inv`` is GLOBAL and silently wrong on an HD vector
    (F-§12.1); this is the per-block form. Class-K clean (per-block norm² gate,
    never abs()); NO new class. Length must be a positive multiple of
    LOOP_DIM (8).

    rc125 (numpy-free): the per-block norm² gate is the numpy-free
    ``mat_dot``; operates on ``list[float]`` (was an ndarray)."""
    a_ = _as_hd(x, "loop_inv_hd")
    native = _try_native_loop_inv_hd(a_)
    if native is not None:
        return native
    from srmech.amsc.laplacian import mat_dot  # numpy-free inner product
    xb = _hd_blocks(a_)
    out = []
    for k in range(len(xb)):
        blk = xb[k]
        nsq = mat_dot(blk, blk)
        assert nsq > 0.0, (
            f"loop_inv_hd: block {k} is the zero vector (no Moufang inverse)")
        out.append(_vscale(_loop_conj_raw(blk), 1.0 / nsq))
    return _concat(out)


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
    multiple of LOOP_DIM (8).

    rc125 (numpy-free): operates on ``list[float]`` (was an ndarray)."""
    a_ = _as_hd(a, "loop_runbind_hd")
    b_ = _as_hd(b, "loop_runbind_hd")
    assert len(a_) == len(b_), "loop_runbind_hd: operands must have equal length"
    native = _try_native_loop_runbind_hd(a_, b_)
    if native is not None:
        return native
    ab = _hd_blocks(a_)
    bb = _hd_blocks(b_)
    return _concat([loop_bind(bb[k], loop_conj(ab[k])) for k in range(len(ab))])


__all__ = [
    "DEFAULT_HDC_BYTES",
    "POLAR_STATES",
    "KLEIN4_STATES",
    "bind",
    "bundle",
    "bundle_with_ties",
    "permute",
    "similarity",
    "hamming",
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
    "klein4_unbundle",
    "klein4_bundle",
    "klein4_similarity",
    "klein4_match_count",
    "klein4_bundle_accumulate",
    "klein4_bundle_resolve",
    "klein4_phase_key",
    "klein4_phase_bind",
    "klein4_chunk_bundle",
    "klein4_chunk_resolve",
    "klein4_encode_bytes",
    "cooccurrence_fold",
    "klein4_chirality_flip_gamma5",
    "klein4_project_axis",
    "klein4_chirality_flip_omega7",
    "klein4_cpt_mirror",
    "klein4_triality_cycle",
    "klein4_sector_count",
    "klein4_holographic_encode",
    "klein4_holographic_decode",
    "klein4_triality_encode",
    "klein4_triality_correct",
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
