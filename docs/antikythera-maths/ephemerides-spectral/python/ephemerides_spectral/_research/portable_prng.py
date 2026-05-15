"""Portable splitmix64 PRNG — bit-identical between Python and C.

Used by `EphemerisHDCInstrument._initialize_bases` (and the C-side
`es_channel_basis`) so the channel-basis hypervectors are byte-
identical across both runtimes. This is the foundation for Tier 2 of
the C/Python parity programme — `get_local_view` and
`get_eclipse_probability` need the same basis vectors on both sides.

Why splitmix64
==============

The Python ref instrument was originally seeded via
``numpy.random.default_rng(seed).uniform(0, 2π, D)``, which is PCG64
+ numpy's specific double-conversion. Reproducing that bit-exactly in
C is brittle — any numpy bump that touches the algorithm breaks
parity. Splitmix64 is six lines, deterministic, and produces
bit-identical output across any IEEE-754 platform with a `uint64`
multiply.

Algorithm (mirrors c/src/es_prng.c byte-for-byte)::

    state += 0x9E3779B97F4A7C15
    z = state
    z = (z XOR (z >> 30)) * 0xBF58476D1CE4E5B9
    z = (z XOR (z >> 27)) * 0x94D049BB133111EB
    return z XOR (z >> 31)

To convert a uint64 to a [0, 2π) double, take the high 53 bits and
scale: ``(u >> 11) * (2π / 2**53)``. This is the same conversion both
sides use.
"""

from __future__ import annotations

import math
from typing import List, Tuple

__all__ = [
    "splitmix64_next",
    "splitmix64_uniform_2pi",
    "splitmix64_phases",
    # v0.29.0rc1 — TURN_INTEGER channel-basis route (cyclic-group-native
    # quarter-turn decomposition). Python mirror of
    # `c/src/es_channel_bases.c::es_channel_basis_turn_integer_route`,
    # byte-identical after the complex64 cast.
    "splitmix64_turn_integer_basis_element",
    "splitmix64_turn_integer_basis",
]

_INC = 0x9E3779B97F4A7C15
_M1  = 0xBF58476D1CE4E5B9
_M2  = 0x94D049BB133111EB
_MASK = (1 << 64) - 1
_SCALE_2PI = (2.0 * math.pi) / float(1 << 53)


def splitmix64_next(state: int) -> tuple[int, int]:
    """Advance the state by one step; return ``(next_state, output_uint64)``.

    Pure ``int`` arithmetic with explicit 64-bit masking. Mirrors the
    C ``static inline uint64_t es_splitmix64_next(uint64_t *state)``
    bit-for-bit.
    """
    state = (state + _INC) & _MASK
    z = state
    z = ((z ^ (z >> 30)) * _M1) & _MASK
    z = ((z ^ (z >> 27)) * _M2) & _MASK
    z = (z ^ (z >> 31)) & _MASK
    return state, z


def splitmix64_uniform_2pi(u: int) -> float:
    """Convert a splitmix64 uint64 output to a uniform double in [0, 2π).

    Uses the standard ``(u >> 11) * (2π / 2**53)`` conversion: take the
    high 53 bits (the IEEE-754 mantissa width), scale to [0, 2π).
    Identical conversion both sides.
    """
    return (u >> 11) * _SCALE_2PI


def splitmix64_phases(seed: int, n: int) -> List[float]:
    """Generate ``n`` uniform [0, 2π) doubles from ``seed``.

    The Python and C side produce the same `n` values for the same
    `seed`. This is what feeds the channel-basis construction: the
    channel basis for body `i` uses ``seed = 2026 + i`` (the same
    integer constants as the original numpy-seeded version).
    """
    out: List[float] = []
    state = seed & _MASK
    for _ in range(int(n)):
        state, u = splitmix64_next(state)
        out.append(splitmix64_uniform_2pi(u))
    return out


# ─────────────────────────────────────────────────────────────────────
# v0.29.0rc1 — TURN_INTEGER route (cyclic-group-native)
# ─────────────────────────────────────────────────────────────────────
#
# Mirror of `c/src/es_channel_bases.c::es_channel_basis_turn_integer_route`.
# Honours the notebook §1.4 framing: every gear is ℤ/nℤ, quarter
# turns are bit patterns, π should not appear in the global argument
# when the integer cyclic-group arithmetic is already exact.
#
#   phase    = (u >> 32) & 0xFFFFFFFF     # Z_{2^32}, cyclic-group elt
#   quadrant = phase >> 30                # 0..3
#   within   = phase & 0x3FFFFFFF         # 30-bit fraction of quarter
#
#   if within == 0:
#       (re, im) = i^quadrant ∈ {(1,0), (0,1), (-1,0), (0,-1)}    exact
#   else:
#       a       = float(within) · (π/2 / 2^30)                    [0, π/2)
#       (re, im) = i^quadrant · (cos(a), sin(a))                  sign/swap

_PI_HALF_PER_2P30 = math.pi / 2.0 / float(1 << 30)


def splitmix64_turn_integer_basis_element(u: int) -> Tuple[float, float]:
    """Decompose a splitmix64 uint64 output into a TURN_INTEGER basis
    element ``(real, imag)`` in Python double precision.

    Caller casts to ``numpy.complex64`` to match the C-side storage.
    Mirrors the C route byte-for-byte after that cast — both sides
    invoke the same OS libm ``cos``/``sin`` on the same float64
    argument, then round to float32 via IEEE-754 nearest-even.

    The high 32 bits of ``u`` are the cyclic-group element in
    ``Z_{2^32}``; the bottom 32 bits of ``u`` are discarded, matching
    the C side. This is a different bit-extraction strategy from
    ``splitmix64_uniform_2pi`` (which uses ``u >> 11``, the high 53
    bits to fill a float64 mantissa); the difference is the price of
    keeping the structural reduction in the integer cyclic group.
    """
    phase = (u >> 32) & 0xFFFFFFFF
    quadrant = phase >> 30
    within = phase & 0x3FFFFFFF
    if within == 0:
        if quadrant == 0:
            return (1.0, 0.0)
        if quadrant == 1:
            return (0.0, 1.0)
        if quadrant == 2:
            return (-1.0, 0.0)
        return (0.0, -1.0)
    a = float(within) * _PI_HALF_PER_2P30
    c = math.cos(a)
    s = math.sin(a)
    if quadrant == 0:
        return (c, s)
    if quadrant == 1:
        return (-s, c)
    if quadrant == 2:
        return (-c, -s)
    return (s, -c)


def splitmix64_turn_integer_basis(seed: int, n: int) -> List[Tuple[float, float]]:
    """Generate ``n`` TURN_INTEGER channel-basis elements from ``seed``.

    Returns a list of ``(real, imag)`` float64 pairs. Caller casts to
    ``numpy.complex64`` for the byte-parity comparison with the C side
    (see ``tests/test_channel_basis_parity.py``).

    Mirrors ``es_channel_basis_method(seed, out, n,
    ES_BASIS_METHOD_TURN_INTEGER)`` byte-for-byte after the cast.
    """
    out: List[Tuple[float, float]] = []
    state = seed & _MASK
    for _ in range(int(n)):
        state, u = splitmix64_next(state)
        out.append(splitmix64_turn_integer_basis_element(u))
    return out
