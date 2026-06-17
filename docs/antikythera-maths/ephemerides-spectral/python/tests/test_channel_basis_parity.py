"""Channel-basis byte-parity test (v0.6.1, Tier 2a foundation).

Pins agreement between the Python `_research/portable_prng` +
float32-truncated unit-phasor pipeline and the C ``es_channel_basis``
entry point. This is the foundation that lets Tier 2b (HD encode +
observer-bind + eclipse projection) produce byte-identical output
between BIP and C paths.

Skipped when the native binary isn't loaded.
"""

from __future__ import annotations

import math
import struct

import pytest

from ephemerides_spectral import _native_bip
from ephemerides_spectral._research.portable_prng import (
    splitmix64_phases, splitmix64_uniform_2pi, splitmix64_next,
    splitmix64_turn_integer_basis,
)


pytestmark = pytest.mark.skipif(
    not _native_bip.HAS_NATIVE,
    reason="native library not loaded; channel-basis parity requires C path",
)


# v0.31.0rc4: numpy-free oracle helpers. The bases are list[complex] whose
# components are float32-truncated; comparison is byte-for-byte via
# struct.pack (interleaved float32 (re, im) per element).
def _f32(x: float) -> float:
    return struct.unpack("f", struct.pack("f", float(x)))[0]


def _c64_bytes(arr) -> bytes:
    buf = bytearray()
    for z in arr:
        zc = complex(z)
        buf += struct.pack("<ff", zc.real, zc.imag)
    return bytes(buf)


def _max_abs_diff(a, b) -> float:
    return max((abs(complex(x) - complex(y)) for x, y in zip(a, b)), default=0.0)


def _py_basis(seed: int, D: int):
    """Python-side reference basis: splitmix64 phases → complex64 unit vectors.

    float32-truncated (complex64-equivalent) via _f32 — byte-identical to
    the old ``np.complex64(np.exp(1j*p))`` path (validated).
    """
    phases = splitmix64_phases(seed, D)
    return [complex(_f32(math.cos(p)), _f32(math.sin(p))) for p in phases]


# ──────────────────────────────────────────────────────────────────────
# splitmix64 stand-alone parity (just the integer PRNG)
# ──────────────────────────────────────────────────────────────────────


def test_splitmix64_first_outputs_known_values() -> None:
    """The first 4 outputs from seed=0 are well-known splitmix64 values.

    Pinned reference values come from the canonical splitmix64
    implementation (Vigna 2013); both the Python port and the C port
    must reproduce them.
    """
    expected = [
        0xE220A8397B1DCDAF,
        0x6E789E6AA1B965F4,
        0x06C45D188009454F,
        0xF88BB8A8724C81EC,
    ]
    state = 0
    for ref in expected:
        state, u = splitmix64_next(state)
        assert u == ref, f"splitmix64({state=}) = {u:#x}; expected {ref:#x}"


def test_splitmix64_uniform_2pi_in_range() -> None:
    """Conversion stays in [0, 2π) for a representative sweep."""
    state = 12345
    for _ in range(100):
        state, u = splitmix64_next(state)
        x = splitmix64_uniform_2pi(u)
        assert 0.0 <= x < 2.0 * math.pi


# ──────────────────────────────────────────────────────────────────────
# Channel-basis byte-parity (the Tier 2a deliverable)
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("seed,D", [
    (2026, 1024),       # body 0 (sun)
    (2026 + 5, 1024),   # body 5 (e.g. jupiter)
    (2026 + 37, 1024),  # body 37 (last body)
    (777, 1024),        # syzygy node basis seed
    (9999, 1024),       # topocentric coord basis seed
    (2026, 65536),      # production-D for body 0
])
def test_channel_basis_byte_identical_py_vs_c(seed: int, D: int) -> None:
    """C and Python produce byte-identical complex64 channel bases.

    This is the Tier 2a parity guarantee. Bit-exact agreement on the
    basis bytes is what makes Tier 2b's HD encode / observer-bind /
    eclipse projection produce byte-identical output between the two
    paths.
    """
    c = _native_bip.native_channel_basis(seed, D)
    py = _py_basis(seed, D)
    assert len(c) == len(py) == D
    # Strictest possible check: byte-identical complex64 buffers.
    assert _c64_bytes(c) == _c64_bytes(py), (
        f"channel-basis byte mismatch at seed={seed}, D={D}: "
        f"max |c-py| = {_max_abs_diff(c, py)}"
    )


def test_channel_basis_unit_magnitude() -> None:
    """Each basis element has |z| = 1 (unit-magnitude complex). The
    float32 truncation of cos/sin can land slightly off unity; the
    tolerance reflects that.
    """
    basis = _native_bip.native_channel_basis(2026, 4096)
    max_mag_err = max(abs(abs(complex(z)) - 1.0) for z in basis)
    # float32 worst-case: cos²+sin² rounds to within ~1e-6 of 1.0
    assert max_mag_err < 1e-6, (
        f"basis not unit-magnitude: max|mag-1|={max_mag_err}"
    )


def test_channel_basis_distinct_seeds_distinct_bases() -> None:
    """Different seeds produce different bases (sanity check the PRNG
    isn't degenerate for nearby seeds 2026, 2027, 2028)."""
    a = _native_bip.native_channel_basis(2026, 1024)
    b = _native_bip.native_channel_basis(2027, 1024)
    c = _native_bip.native_channel_basis(2028, 1024)
    # Different bases should NOT be elementwise close.
    assert _max_abs_diff(a, b) > 0.1
    assert _max_abs_diff(b, c) > 0.1
    assert _max_abs_diff(a, c) > 0.1


# ──────────────────────────────────────────────────────────────────────
# v0.29.0rc1 — TURN_INTEGER byte-parity (Tier 2a route #2)
# ──────────────────────────────────────────────────────────────────────


def _py_turn_integer_basis(seed: int, D: int):
    """Python-side reference TURN_INTEGER basis (complex64-truncated list).

    Mirrors `c/src/es_channel_bases.c::es_channel_basis_turn_integer_route`
    via `splitmix64_turn_integer_basis()` + float32 truncation.
    """
    pairs = splitmix64_turn_integer_basis(seed, D)
    return [complex(_f32(re), _f32(im)) for re, im in pairs]


@pytest.mark.parametrize("seed,D", [
    (2026, 1024),       # body 0 (sun)
    (2026 + 5, 1024),   # body 5 (e.g. jupiter)
    (2026 + 37, 1024),  # body 37 (last body)
    (777, 1024),        # syzygy node basis seed
    (9999, 1024),       # topocentric coord basis seed
    (2026, 65536),      # production-D for body 0
])
def test_channel_basis_turn_integer_byte_identical_py_vs_c(
        seed: int, D: int) -> None:
    """C and Python produce byte-identical complex64 TURN_INTEGER bases.

    This is the v0.29.0rc1 dual-path parity guarantee: the TURN_INTEGER
    route — the cyclic-group-native quarter-turn decomposition added
    in this rc — has a Python mirror that matches the C output bit-
    for-bit after the complex64 cast.

    Both sides:
      * Use the same splitmix64 state stream.
      * Extract the top 32 bits of each output as the phase residue
        in Z_{2^32}.
      * Decompose into (quadrant, within) by the same integer split.
      * Dispatch bit-exact (±1, 0) / (0, ±1) when `within == 0`.
      * Compute `cos(a)`, `sin(a)` via the OS libm with the SAME
        scaled argument `a = float(within) · (π/2 / 2^30)`.
      * Apply `i^quadrant` rotation by sign/swap.
      * Cast to float32 via IEEE-754 nearest-even.

    The OS libm + IEEE-754 cast are deterministic shared state across
    CPython and the C library; byte-parity therefore holds on every
    platform we support. Sibling discipline to the LEGACY parity
    above (`test_channel_basis_byte_identical_py_vs_c`).
    """
    c = _native_bip.native_channel_basis_turn_integer(seed, D)
    py = _py_turn_integer_basis(seed, D)
    assert len(c) == len(py) == D
    assert _c64_bytes(c) == _c64_bytes(py), (
        f"TURN_INTEGER channel-basis byte mismatch at seed={seed}, D={D}: "
        f"max |c-py| = {_max_abs_diff(c, py)}"
    )


def test_turn_integer_basis_quarter_turn_dispatch_bit_exact() -> None:
    """Hand-injected quarter-turn phases: forge a uint64 that decomposes
    to `within == 0` at each of the four quadrants, verify the Python
    helper emits exact ±1 / ±i (no float math involved).

    This is a structural check on the Python implementation of the
    quarter-turn dispatch — the C side's behaviour is verified by the
    byte-parity test above; here we verify the Python algorithm
    independently of the splitmix64 stream.
    """
    from ephemerides_spectral._research.portable_prng import (
        splitmix64_turn_integer_basis_element,
    )
    # Quadrant 0: phase = 0, expect (1, 0)
    assert splitmix64_turn_integer_basis_element(0) == (1.0, 0.0)
    # Quadrant 1: phase = 2^30 << 32 = 2^62, expect (0, 1)
    assert splitmix64_turn_integer_basis_element(1 << 62) == (0.0, 1.0)
    # Quadrant 2: phase = 2^31 << 32 = 2^63, expect (-1, 0)
    assert splitmix64_turn_integer_basis_element(1 << 63) == (-1.0, 0.0)
    # Quadrant 3: phase = 3 · 2^30 << 32, expect (0, -1)
    assert splitmix64_turn_integer_basis_element((3 << 30) << 32) == (0.0, -1.0)
