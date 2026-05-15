"""Channel-basis byte-parity test (v0.6.1, Tier 2a foundation).

Pins agreement between the Python `_research/portable_prng` +
``np.exp(1j * phi)`` pipeline and the C ``es_channel_basis`` entry
point. This is the foundation that lets Tier 2b (HD encode +
observer-bind + eclipse projection) produce byte-identical output
between BIP and C paths.

Skipped when the native binary isn't loaded.
"""

from __future__ import annotations

import math

import numpy as np
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


def _py_basis(seed: int, D: int) -> np.ndarray:
    """Python-side reference basis: splitmix64 phases → complex64 unit vectors."""
    phases = splitmix64_phases(seed, D)
    return np.array([np.exp(1j * p) for p in phases], dtype=np.complex64)


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
    assert c.dtype == np.complex64
    assert py.dtype == np.complex64
    assert c.shape == py.shape == (D,)
    # Strictest possible check: byte-identical complex64 arrays.
    assert np.array_equal(c, py), (
        f"channel-basis byte mismatch at seed={seed}, D={D}: "
        f"max |c-py| = {np.max(np.abs(c - py))}"
    )


def test_channel_basis_unit_magnitude() -> None:
    """Each basis element has |z| = 1 (unit-magnitude complex). The
    np.float32 truncation of cos/sin can land slightly off unity; the
    tolerance reflects that.
    """
    basis = _native_bip.native_channel_basis(2026, 4096)
    mags = np.abs(basis)
    # float32 worst-case: cos²+sin² rounds to within ~1e-6 of 1.0
    assert np.max(np.abs(mags - 1.0)) < 1e-6, (
        f"basis not unit-magnitude: max|mag-1|={np.max(np.abs(mags-1.0))}"
    )


def test_channel_basis_distinct_seeds_distinct_bases() -> None:
    """Different seeds produce different bases (sanity check the PRNG
    isn't degenerate for nearby seeds 2026, 2027, 2028)."""
    a = _native_bip.native_channel_basis(2026, 1024)
    b = _native_bip.native_channel_basis(2027, 1024)
    c = _native_bip.native_channel_basis(2028, 1024)
    # Different bases should NOT be elementwise close.
    assert np.max(np.abs(a - b)) > 0.1
    assert np.max(np.abs(b - c)) > 0.1
    assert np.max(np.abs(a - c)) > 0.1


# ──────────────────────────────────────────────────────────────────────
# v0.29.0rc1 — TURN_INTEGER byte-parity (Tier 2a route #2)
# ──────────────────────────────────────────────────────────────────────


def _py_turn_integer_basis(seed: int, D: int) -> np.ndarray:
    """Python-side reference TURN_INTEGER basis (complex64).

    Mirrors `c/src/es_channel_bases.c::es_channel_basis_turn_integer_route`
    via `splitmix64_turn_integer_basis()` + complex64 cast.
    """
    pairs = splitmix64_turn_integer_basis(seed, D)
    return np.array(
        [complex(re, im) for re, im in pairs],
        dtype=np.complex64,
    )


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
    assert c.dtype == np.complex64
    assert py.dtype == np.complex64
    assert c.shape == py.shape == (D,)
    assert np.array_equal(c, py), (
        f"TURN_INTEGER channel-basis byte mismatch at seed={seed}, D={D}: "
        f"max |c-py| = {np.max(np.abs(c - py))}"
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
