"""BIP-and-lift HD pipeline (v0.7.0, Tier 2b).

The original `EphemerisHDCInstrument.encode_state` propagates phases via
`scipy.linalg.expm` of a state-dependent Laplacian — an FPU-only path
that diverges from the BIP integer encoder. For the C/Python parity
story we want a single propagation path on both sides, with the FPU
hyperdimensional state derived from the same 52-body integer phases
the BIP / native-C encoder produces.

This module is that bridge:

  1. Call the BIP encoder (Python or C) to get 52 × uint32 phase
     residues.
  2. Convert each uint32 phase to a residue in [0, D) via
     ``round(phi / 2**32 * D) mod D``.
  3. For each body, fetch a deterministic complex64 channel basis
     (from the portable splitmix64 PRNG that v0.6.1 added).
  4. Sum ``np.roll(basis_i, residue_i) / sqrt(D)`` across bodies.
  5. Normalise to unit norm.

Step 3's PRNG matches the C-side ``es_channel_basis`` byte-for-byte,
so the Python BIP-and-lift output and the C ``es_encode_state_hd``
output agree within float-ULP. (The reference instrument's old
matrix-expm path uses ``numpy.random.default_rng`` for its bases and
produces different bytes; that path is kept under
``backend="fpu-ref"`` for backwards compatibility.)

Observer bind and eclipse projection are pure HDC algebra (no SPICE,
no skyfield) and implemented identically on both sides; this module
exposes them at the Python level so the bridge can dispatch on
``backend`` cleanly.
"""

from __future__ import annotations

import math
import struct
from typing import List, Optional

from .portable_prng import splitmix64_phases


def _f32(x: float) -> float:
    """Round a Python float to float32 precision (IEEE-754 nearest-even).

    ``complex(_f32(cos), _f32(sin))`` equals ``np.complex64(np.exp(1j*p))``
    byte-for-byte (validated): the channel basis stays a byte-identical
    complex64 array after the numpy-removal flip.
    """
    return struct.unpack("f", struct.pack("f", x))[0]


def _roll(v: List[complex], k: int) -> List[complex]:
    """``numpy.roll(v, k)`` semantics for a Python list (verified equal)."""
    n = len(v)
    k %= n
    return v[-k % n:] + v[:-k % n]


def _norm(v: List[complex]) -> float:
    """Euclidean norm of a complex vector (``numpy.linalg.norm`` for 1-D)."""
    return math.sqrt(sum((z.real * z.real + z.imag * z.imag) for z in v))

__all__ = [
    "BODY_BASIS_SEED_BASE",
    "OBSERVER_COORD_BASIS_SEED",
    "SYZYGY_NODE_BASIS_SEED",
    "COPRIME_LAT",
    "COPRIME_LON",
    "channel_basis",
    "encode_state_hd",
    "bind_observer",
    "syzygy_operator",
    "eclipse_probability",
]

# Seeds — SSOT mirrored from `EphemerisHDCInstrument`. The C side reads
# these via the higher-level functions in `es_hd_state.c`; the integer
# constants are kept identical so the byte-parity test suite holds.
BODY_BASIS_SEED_BASE: int = 2026
OBSERVER_COORD_BASIS_SEED: int = 9999
SYZYGY_NODE_BASIS_SEED: int = 777

# Coprime weights for the observer roll. Same as
# `ephemeris_reference_instrument.COPRIME_LAT/LON`.
COPRIME_LAT: int = 67
COPRIME_LON: int = 7


def channel_basis(seed: int, D: int) -> List[complex]:
    """Generate a deterministic complex64 channel basis of dimension D.

    Returns a length-``D`` ``list[complex]`` whose elements are
    float32-truncated (complex64-equivalent) values. Bit-identical to
    the previous ``np.complex64(np.exp(1j*phi))`` path (validated via
    ``struct.pack`` byte compare) and to ``es_channel_basis`` on the C
    side after the complex64 cast.

    v0.31.0rc4: numpy-free. ``_f32`` applies the same IEEE-754
    nearest-even float32 rounding numpy's complex64 cast did.
    """
    phases = splitmix64_phases(int(seed) & ((1 << 64) - 1), int(D))
    return [complex(_f32(math.cos(phi)), _f32(math.sin(phi))) for phi in phases]


def _phase_uint32_to_residue(phi: int, D: int) -> int:
    """Convert a uint32 phase residue to an integer residue in [0, D).

    Mirrors the Python ref instrument's
    ``int((phase_rad / 2π) * D) % D`` step, but operating on the
    uint32 phase residue directly:
        residue = round((phi / 2**32) * D) mod D

    Round-to-nearest-even matches both numpy's `np.round` half-even
    and `lround()` in C (when the C side uses `(int64_t)((phi *
    (uint64_t)D + (1ULL << 31)) >> 32)` for round-half-up; the
    half-even tie case never arises from the BIP encoder's output
    because uint32 values land on integer indices via a deterministic
    multiplication, not a halfway-between-two-bins).
    """
    # `(phi * D + 2**31) >> 32` is the standard banker's-rounding-free
    # round-half-up equivalent; for our use case the half-even tie
    # never arises (phi is a 32-bit integer; the pre-rounding value
    # `phi * D / 2**32` is rational with denominator 2**32, so a tie
    # at exactly half requires phi*D mod 2**32 == 2**31, which has
    # measure zero in practice).
    return int(((int(phi) * int(D) + (1 << 31)) >> 32) % D)


def encode_state_hd(phases_uint32, D: int) -> List[complex]:
    """Lift 38 × uint32 BIP phase residues to a D-dim hypervector.

    Parameters
    ----------
    phases_uint32 : sequence of int
        Output of ``EphemerisBIPInstrument.encode_state(jd_tdb)`` — one
        uint32 per body in alphabetical name order (``array('I')`` /
        list / any indexable of int).
    D : int
        Hypervector dimension (typically 65536).

    Returns
    -------
    list[complex]
        Length-D unit-norm hypervector. Matches the C
        ``es_encode_state_hd`` output for the same `phases_uint32`
        within HD parity tolerance (1e-5).

    v0.31.0rc4: numpy-free. The complex64 channel bases are byte-
    identical; the superposition accumulates in Python ``complex``
    (float64) — more accurate than the old complex64 accumulation,
    well within the 1e-5 HD-parity tolerance the bridge / native
    parity test enforces.
    """
    n = len(phases_uint32)
    state: List[complex] = [0j] * D
    sqrt_D = math.sqrt(D)
    inv = 1.0 / sqrt_D
    for i in range(n):
        seed = BODY_BASIS_SEED_BASE + i
        basis = channel_basis(seed, D)
        residue = _phase_uint32_to_residue(int(phases_uint32[i]), D)
        # Body bases ship pre-divided by sqrt(D) in the ref instrument;
        # we apply the scaling here at the lift step rather than in the
        # raw `channel_basis` primitive (which the C side leaves
        # un-scaled too, keeping the basis primitive minimal).
        rolled = _roll(basis, residue)
        for k in range(D):
            state[k] += rolled[k] * inv
    norm = _norm(state)
    if norm > 0.0:
        state = [z / norm for z in state]
    return state


def bind_observer(state: List[complex],
                  body_idx: int,
                  lat_deg: float,
                  lon_deg: float,
                  D: int) -> List[complex]:
    """Topocentric observer-bind via HDC algebra.

    Mirrors ``EphemerisHDCInstrument.bind_observer`` but with the
    splitmix64 channel bases (so Python BIP-and-lift and the C twin
    produce byte-identical output).

    v0.31.0rc4: numpy-free. Element-wise complex products over Python
    lists; HD-parity tolerance (1e-5).
    """
    body_basis = channel_basis(BODY_BASIS_SEED_BASE + int(body_idx), D)
    sqrt_D = math.sqrt(D)
    inv = 1.0 / sqrt_D

    lat_res = int(((lat_deg + 90.0) / 180.0) * D) % D
    lon_res = int(((lon_deg + 180.0) / 360.0) * D) % D

    coord_basis = channel_basis(OBSERVER_COORD_BASIS_SEED, D)
    coord_op = _roll(coord_basis, (lat_res * COPRIME_LAT + lon_res * COPRIME_LON) % D)

    # observer_op = (body_basis / sqrt_D) * coord_op ; result = state * observer_op * sqrt_D
    out: List[complex] = [0j] * D
    for k in range(D):
        observer_op_k = (body_basis[k] * inv) * coord_op[k]
        out[k] = state[k] * observer_op_k * sqrt_D
    return out


def syzygy_operator(D: int,
                    sun_basis: Optional[List[complex]] = None,
                    moon_basis: Optional[List[complex]] = None) -> List[complex]:
    """Build the syzygy operator: normalised sum of sun + moon + node bases.

    Sun and Moon body indices are 0-based positions in the alphabetical
    body-name order; for the v0.5.0+ 38-body roster they're not
    body 0 / body 1, so callers must pass the bases (or pass body
    indices and let the helper resolve them — but body-name resolution
    crosses the bridge, so we keep this primitive raw).

    v0.31.0rc4: numpy-free. ``sun_basis`` / ``moon_basis`` are
    ``list[complex]`` (already complex64-truncated from
    ``channel_basis``).
    """
    if sun_basis is None or moon_basis is None:
        raise ValueError(
            "syzygy_operator requires sun_basis + moon_basis "
            "(callers resolve body indices upstream)"
        )
    sqrt_D = math.sqrt(D)
    inv = 1.0 / sqrt_D
    node_basis = channel_basis(SYZYGY_NODE_BASIS_SEED, D)
    s_op: List[complex] = [
        sun_basis[k] * inv + moon_basis[k] * inv + node_basis[k] * inv
        for k in range(D)
    ]
    norm = _norm(s_op)
    if norm > 0.0:
        s_op = [z / norm for z in s_op]
    return s_op


def eclipse_probability(state: List[complex],
                        D: int,
                        sun_body_idx: int,
                        moon_body_idx: int) -> float:
    """|<state, syzygy_operator>|.

    The bases for the sun/moon channels are pulled fresh from
    splitmix64 — same seeds as `encode_state_hd` uses. Caller
    supplies the integer body indices (0-based, alphabetical).

    v0.31.0rc4: numpy-free. ``vdot`` = sum of ``conj(state) * s_op``
    (conjugate-linear in the first argument, matching ``np.vdot``).
    """
    sun_b = channel_basis(BODY_BASIS_SEED_BASE + int(sun_body_idx), D)
    moon_b = channel_basis(BODY_BASIS_SEED_BASE + int(moon_body_idx), D)
    s_op = syzygy_operator(D, sun_basis=sun_b, moon_basis=moon_b)
    acc = sum(state[k].conjugate() * s_op[k] for k in range(D))
    return math.hypot(acc.real, acc.imag)
