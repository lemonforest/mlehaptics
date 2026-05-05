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
from typing import List

__all__ = [
    "splitmix64_next",
    "splitmix64_uniform_2pi",
    "splitmix64_phases",
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
