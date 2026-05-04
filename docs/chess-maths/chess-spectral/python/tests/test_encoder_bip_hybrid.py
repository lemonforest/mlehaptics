"""1.12.0 immolation: BIP-hybrid encoder (B-spike-2).

The §20.15 acceptance gate for B-spike-2:
  * Cosine-sim ≥ 99.5% median, ≥ 95% worst-case on a test corpus
    at 8-bit magnitude quantization.
  * Sign portion preserved exactly.

Empirical finding from this PR (worth recording in §20.18):
  * 8-bit hybrid passes both thresholds for both 2D and 4D.
  * 4-bit hybrid passes for 2D but lands at ~0.994 median for 4D
    canonical OC startpos — just under the 99.5% bar. The 45056-
    dim 4D encoder accumulates more cumulative quantization error
    than the 640-dim 2D encoder at the same per-dim bit budget.

Tests in this file:

  * Sign-bit packing / unpacking round-trip
  * 4-bit nibble packing / unpacking round-trip
  * Hybrid round-trip recovers same dims, dtype, and signs exactly
  * Per-channel magnitude scaling: max(abs(decoded[ch])) ≤
    magnitude_scales[ch]
  * §20.15 acceptance gate at 8-bit on a 7-FEN 2D corpus
  * §20.15 acceptance gate at 8-bit on 4D canonical OC startpos
  * 4-bit 2D corpus passes (research finding)
  * 4-bit 4D fails 99.5% (research finding — documented but not gating)
  * Storage budget matches documented values
  * Cosine-similarity between two hybrid vectors approximates the
    cosine-sim between their float32 originals
  * Error cases: invalid magnitude_bits, malformed input
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import fen_to_pos, encode_640   # noqa: E402
from chess_spectral.encoder_bip_hybrid import (   # noqa: E402
    SpectralBIPHybrid2D, SpectralBIPHybrid4D,
    encode_2d_bip_hybrid, decode_2d_bip_hybrid,
    encode_4d_bip_hybrid, decode_4d_bip_hybrid,
    cosine_similarity_hybrid_2d, cosine_similarity_hybrid_4d,
    round_trip_cosine_sim_2d, round_trip_cosine_sim_4d,
    storage_bytes_2d, storage_bytes_4d,
    DEFAULT_MAGNITUDE_BITS, VALID_MAGNITUDE_BITS,
    N_CHANNELS_2D, CHANNEL_DIM_2D,
    N_CHANNELS_4D, CHANNEL_DIM_4D,
    _pack_signs, _unpack_signs,
    _pack_4bit, _unpack_4bit,
)


# ─── Layout sanity ──────────────────────────────────────────────────


def test_immolation_default_magnitude_bits_is_eight():
    """The §20.15 acceptance gate is set against 8-bit magnitude."""
    assert DEFAULT_MAGNITUDE_BITS == 8


def test_immolation_valid_magnitude_bits_includes_4_and_8():
    assert 4 in VALID_MAGNITUDE_BITS
    assert 8 in VALID_MAGNITUDE_BITS


def test_immolation_storage_budgets_match_docstring_values():
    # 2D: 80 sign + 40 scales + (640 / 320) magnitudes
    assert storage_bytes_2d(8) == 80 + 40 + 640
    assert storage_bytes_2d(4) == 80 + 40 + 320
    # 4D: 5632 sign + 44 scales + (45056 / 22528) magnitudes
    assert storage_bytes_4d(8) == 5632 + 44 + 45056
    assert storage_bytes_4d(4) == 5632 + 44 + 22528


def test_immolation_storage_budget_compression_ratios():
    """At 8-bit: 2D ~3.4x, 4D ~3.6x. At 4-bit: 2D ~5.8x, 4D ~6.4x."""
    float_2d = 640 * 4
    float_4d = 45056 * 4
    assert 3.0 < float_2d / storage_bytes_2d(8) < 4.0
    assert 5.0 < float_2d / storage_bytes_2d(4) < 6.0
    assert 3.0 < float_4d / storage_bytes_4d(8) < 4.0
    assert 6.0 < float_4d / storage_bytes_4d(4) < 7.0


# ─── Bit-packing helpers ────────────────────────────────────────────


def test_immolation_sign_pack_unpack_round_trip_640():
    rng = np.random.default_rng(20260504)
    signs = rng.integers(0, 2, size=640, dtype=np.uint8)
    packed = _pack_signs(signs)
    assert len(packed) == 80
    recovered = _unpack_signs(packed, 640)
    np.testing.assert_array_equal(recovered, signs)


def test_immolation_sign_pack_unpack_round_trip_45056():
    rng = np.random.default_rng(20260504)
    signs = rng.integers(0, 2, size=45056, dtype=np.uint8)
    packed = _pack_signs(signs)
    assert len(packed) == 5632
    recovered = _unpack_signs(packed, 45056)
    np.testing.assert_array_equal(recovered, signs)


def test_immolation_sign_pack_specific_pattern():
    """All-zero signs should pack to all-zero bytes; all-ones signs
    should pack to 0xFF bytes."""
    zero_signs = np.zeros(640, dtype=np.uint8)
    assert _pack_signs(zero_signs) == bytes(80)
    one_signs = np.ones(640, dtype=np.uint8)
    assert _pack_signs(one_signs) == bytes([0xFF] * 80)


def test_immolation_4bit_pack_unpack_round_trip():
    rng = np.random.default_rng(20260504)
    values = rng.integers(0, 16, size=640, dtype=np.uint8)
    packed = _pack_4bit(values)
    assert len(packed) == 320
    recovered = _unpack_4bit(packed, 640)
    np.testing.assert_array_equal(recovered, values)


def test_immolation_4bit_pack_specific_pattern():
    """Pack [0, 1, 2, 3] → [0x10, 0x32]."""
    values = np.array([0, 1, 2, 3], dtype=np.uint8)
    packed = _pack_4bit(values)
    assert list(packed) == [0x10, 0x32]


# ─── 2D round-trip ──────────────────────────────────────────────────


_REPRESENTATIVE_2D_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "8/8/8/4k3/4P3/4K3/8/8 w - - 0 1",
    "8/8/8/4k3/8/8/4R3/4K3 w - - 0 1",
    "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11",
    "8/3P4/8/8/8/8/4k3/4K3 w - - 0 1",
]


@pytest.mark.parametrize("fen", _REPRESENTATIVE_2D_FENS)
def test_immolation_2d_hybrid_round_trip_shape_and_dtype(fen):
    """Encode → decode produces a 640-dim float64 array."""
    pos = fen_to_pos(fen)
    h = encode_2d_bip_hybrid(pos)
    dec = decode_2d_bip_hybrid(h)
    assert dec.shape == (640,)
    assert dec.dtype == np.float64


@pytest.mark.parametrize("fen", _REPRESENTATIVE_2D_FENS)
@pytest.mark.parametrize("bits", [4, 8])
def test_immolation_2d_sign_bit_preserved_exactly(fen, bits):
    """The SIGN BIT in sign_packed is preserved exactly for every
    dim — that's the BIP-clean property. The DECODED value's sign
    can be 0 (sign-less) when the magnitude quantizes to zero;
    that's a known property of low-bit quantization, not a
    sign-preservation failure.

    This test verifies the load-bearing claim: the encoded sign
    bit equals the original sign for every dim, regardless of
    whether the magnitude rounds to zero.
    """
    pos = fen_to_pos(fen)
    original = encode_640(pos)
    h = encode_2d_bip_hybrid(pos, magnitude_bits=bits)
    # Read the sign bits back out of the packed bytes directly.
    sign_bits = _unpack_signs(h.sign_packed, 640)
    # sign_bits[i] = 1 iff original[i] < 0.
    expected = (original < 0).astype(np.uint8)
    np.testing.assert_array_equal(sign_bits, expected)


@pytest.mark.parametrize("fen", _REPRESENTATIVE_2D_FENS)
@pytest.mark.parametrize("bits", [4, 8])
def test_immolation_2d_decoded_sign_matches_where_magnitude_nonzero(fen, bits):
    """Where the decoded magnitude is non-zero, the decoded sign
    matches the original sign. Where magnitude rounds to zero (low-
    bit quantization on small-magnitude dims), the decoded value is
    0.0 and has no sign — that's the documented quantization-to-zero
    behavior, not a sign-preservation bug.
    """
    pos = fen_to_pos(fen)
    original = encode_640(pos)
    h = encode_2d_bip_hybrid(pos, magnitude_bits=bits)
    decoded = decode_2d_bip_hybrid(h)
    # Only check sign agreement where decoded is non-zero.
    nonzero_decoded = decoded != 0
    sign_orig = np.sign(original[nonzero_decoded])
    sign_dec = np.sign(decoded[nonzero_decoded])
    np.testing.assert_array_equal(sign_orig, sign_dec)


@pytest.mark.parametrize("fen", _REPRESENTATIVE_2D_FENS)
def test_immolation_2d_per_channel_max_bounds(fen):
    """For every channel, max(abs(decoded[ch])) ≤ magnitude_scales[ch]
    (the per-channel max from the original is preserved as the upper
    bound of the decoded magnitude)."""
    pos = fen_to_pos(fen)
    h = encode_2d_bip_hybrid(pos, magnitude_bits=8)
    decoded = decode_2d_bip_hybrid(h)
    for ch_idx in range(N_CHANNELS_2D):
        start = ch_idx * CHANNEL_DIM_2D
        sl = slice(start, start + CHANNEL_DIM_2D)
        max_decoded = float(np.abs(decoded[sl]).max())
        scale = float(h.magnitude_scales[ch_idx])
        # Allow tiny floating-point slack (1e-9 relative).
        assert max_decoded <= scale * (1.0 + 1e-9), (
            f"channel {ch_idx}: decoded max {max_decoded} exceeds "
            f"scale {scale}"
        )


# ─── §20.15 acceptance gate — 2D ────────────────────────────────────


def test_immolation_2d_8bit_acceptance_gate():
    """**Acceptance**: ≥ 99.5% median + ≥ 95% worst-case on the
    representative 7-FEN corpus at 8-bit magnitude.

    Empirically observed (1.12.0 first ship): median ≈ 0.999996,
    worst ≈ 0.999996 — well above both thresholds.
    """
    sims = [
        round_trip_cosine_sim_2d(fen_to_pos(fen), magnitude_bits=8)
        for fen in _REPRESENTATIVE_2D_FENS
    ]
    median_sim = float(np.median(sims))
    worst_sim = float(min(sims))
    assert median_sim >= 0.995, (
        f"2D 8-bit median cosine-sim {median_sim:.6f} < 0.995 acceptance "
        f"threshold; sims = {sims}"
    )
    assert worst_sim >= 0.95, (
        f"2D 8-bit worst-case cosine-sim {worst_sim:.6f} < 0.95 acceptance "
        f"threshold; sims = {sims}"
    )


def test_immolation_2d_4bit_passes_corpus():
    """4-bit hybrid also passes on 2D's 640-dim encoder.

    Empirically observed: median ≈ 0.998924, worst ≈ 0.998729 —
    still above both 99.5% and 95% thresholds. 4D 4-bit is the
    case that struggles (see test below).
    """
    sims = [
        round_trip_cosine_sim_2d(fen_to_pos(fen), magnitude_bits=4)
        for fen in _REPRESENTATIVE_2D_FENS
    ]
    median_sim = float(np.median(sims))
    worst_sim = float(min(sims))
    assert median_sim >= 0.995, (
        f"2D 4-bit median {median_sim:.6f} below 99.5% threshold"
    )
    assert worst_sim >= 0.95, (
        f"2D 4-bit worst {worst_sim:.6f} below 95% threshold"
    )


# ─── 4D round-trip ──────────────────────────────────────────────────


def test_immolation_4d_hybrid_round_trip_canonical_oc():
    """4D round trip on canonical Oana-Chiru §3.3 starting position."""
    from chess_spectral_4d import initial_position
    gs = initial_position()
    pos4 = dict(gs.position.items())
    h = encode_4d_bip_hybrid(pos4, magnitude_bits=8)
    decoded = decode_4d_bip_hybrid(h)
    assert decoded.shape == (45056,)
    assert decoded.dtype == np.float64


def test_immolation_4d_8bit_acceptance_gate_canonical_oc():
    """**Acceptance**: 4D 8-bit hybrid ≥ 99.5% on canonical OC.

    Empirically observed: 0.999979.
    """
    from chess_spectral_4d import initial_position
    gs = initial_position()
    pos4 = dict(gs.position.items())
    sim = round_trip_cosine_sim_4d(pos4, magnitude_bits=8)
    assert sim >= 0.995, (
        f"4D 8-bit cosine-sim {sim:.6f} < 0.995 acceptance threshold"
    )


def test_immolation_4d_4bit_misses_99_5_threshold_research_finding():
    """**Research finding** (notebook §20.18): 4D 4-bit hybrid misses
    the 99.5% threshold but stays above 95%.

    Empirically observed: 0.994358 — just below 99.5%, well above
    95%. The 45056-dim 4D encoder accumulates more cumulative
    quantization error at 4-bit than the 640-dim 2D encoder.

    This test gates the FINDING: if 4D 4-bit suddenly hits 99.5%,
    something changed (better — re-evaluate the recommendation
    that 8-bit is the safe 4D default). If it suddenly drops below
    95%, something broke (worse — investigate).
    """
    from chess_spectral_4d import initial_position
    gs = initial_position()
    pos4 = dict(gs.position.items())
    sim = round_trip_cosine_sim_4d(pos4, magnitude_bits=4)
    # The finding: 0.994 < sim < 0.999. Tighter bound than the
    # 99.5% / 95% acceptance gates because we want to lock in the
    # specific empirical observation.
    assert 0.99 < sim < 0.999, (
        f"4D 4-bit cosine-sim {sim:.6f} outside the [0.99, 0.999] "
        f"empirical band; the §20.18 finding shifted — investigate"
    )


# ─── Cosine-similarity between two hybrid vectors ───────────────────


def test_immolation_cosine_sim_two_hybrid_vectors_2d():
    """cos_sim(hybrid(A), hybrid(B)) approximates cos_sim(A, B)
    closely. The §20.15 acceptance bounds the per-vector round-trip
    error; pair-wise sim error is bounded by approximately twice that."""
    pos_a = fen_to_pos(_REPRESENTATIVE_2D_FENS[0])
    pos_b = fen_to_pos(_REPRESENTATIVE_2D_FENS[1])
    a = encode_640(pos_a)
    b = encode_640(pos_b)
    sim_float = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    sim_hybrid = cosine_similarity_hybrid_2d(
        encode_2d_bip_hybrid(pos_a, magnitude_bits=8),
        encode_2d_bip_hybrid(pos_b, magnitude_bits=8),
    )
    # Allow up to 1% absolute deviation (the float baseline is
    # ~0.6, so 1% is ~0.006 absolute — generous for 8-bit).
    assert abs(sim_float - sim_hybrid) < 0.01, (
        f"hybrid cos-sim {sim_hybrid:.6f} deviates from float "
        f"{sim_float:.6f} by more than 1%"
    )


def test_immolation_cosine_sim_self_is_one_2d():
    """cos_sim(hybrid(A), hybrid(A)) ≈ 1.0 (modulo quantization)."""
    pos = fen_to_pos(_REPRESENTATIVE_2D_FENS[0])
    h = encode_2d_bip_hybrid(pos, magnitude_bits=8)
    sim = cosine_similarity_hybrid_2d(h, h)
    assert sim >= 0.999, f"self cos-sim {sim:.6f} should be ≥ 0.999"


# ─── Error cases ─────────────────────────────────────────────────────


def test_immolation_invalid_magnitude_bits_raises():
    pos = fen_to_pos(_REPRESENTATIVE_2D_FENS[0])
    with pytest.raises(ValueError):
        encode_2d_bip_hybrid(pos, magnitude_bits=16)
    with pytest.raises(ValueError):
        encode_2d_bip_hybrid(pos, magnitude_bits=2)


def test_immolation_storage_bytes_invalid_bits_raises():
    with pytest.raises(ValueError):
        storage_bytes_2d(16)
    with pytest.raises(ValueError):
        storage_bytes_4d(2)


# ─── Sign portion BIP-clean property ────────────────────────────────


def test_immolation_zero_vector_round_trip():
    """An all-zero spectral vector encodes to all-zero magnitudes
    and trivial scales, decodes back to all-zero."""
    # Build a synthetic "empty" hybrid via _hybrid_encode_2d on a
    # zero vector, since fen_to_pos always gives at least kings.
    from chess_spectral.encoder_bip_hybrid import _hybrid_encode_2d
    zero = np.zeros(640, dtype=np.float64)
    h = _hybrid_encode_2d(zero, magnitude_bits=8)
    decoded = decode_2d_bip_hybrid(h)
    np.testing.assert_array_equal(decoded, zero)


def test_immolation_sign_bit_storage_exact_on_corpus():
    """The sign BIT (in sign_packed) is exactly preserved for every
    dim across the corpus, at every magnitude budget. This is the
    BIP-clean property — sign storage is algebraically exact;
    magnitude is the only loss source.

    Distinct from sign agreement on the decoded round trip:
    decoded values can have sign 0 (sign-less) when their
    magnitude quantizes to zero, but the underlying sign BIT is
    still preserved correctly in storage.
    """
    for fen in _REPRESENTATIVE_2D_FENS:
        pos = fen_to_pos(fen)
        original = encode_640(pos)
        for bits in (4, 8):
            h = encode_2d_bip_hybrid(pos, magnitude_bits=bits)
            sign_bits = _unpack_signs(h.sign_packed, 640)
            expected = (original < 0).astype(np.uint8)
            np.testing.assert_array_equal(
                sign_bits, expected,
                err_msg=f"{fen} @ {bits}-bit",
            )
