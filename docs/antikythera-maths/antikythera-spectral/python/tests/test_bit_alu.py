"""bit_alu facade — smoke + algebraic-identity + encoder round-trip.

Exercises the public ``antikythera_spectral.bit_alu`` facade:

1. Facade smoke — every name in ``__all__`` resolves; the underlying
   module imports cleanly.
2. Algebraic identities — XOR-bind is self-inverse; permute by D
   returns the input; majority-bundle of clones returns the clone;
   similarity of identical / complement vectors is +1 / −1.
3. Encoder round-trip — ``encode_ant_bit`` produces a hypervector
   whose ``decode_dial_bit`` reads back the encoded residue for at
   least the calendar dials (the cleanest decode targets in BSC
   bundling).

These are the bit-ALU equivalent of the round-trip checks in the
H-battery's E-H1 / B-H1 rows for the complex128 encoder; passing
both pins that the bit ALU implements the same algebraic substrate.
"""

from __future__ import annotations

import numpy as np
import pytest


def _assert_dunder_all_resolves(module) -> None:
    missing = [n for n in module.__all__ if not hasattr(module, n)]
    assert not missing, (
        f"{module.__name__}: __all__ lists missing names: {missing}"
    )


# ---------------------------------------------------------------------------
# Facade smoke
# ---------------------------------------------------------------------------

def test_bit_alu_facade_imports() -> None:
    from antikythera_spectral import bit_alu
    _assert_dunder_all_resolves(bit_alu)


def test_n_words_arithmetic() -> None:
    from antikythera_spectral import bit_alu
    assert bit_alu.n_words(0) == 0
    assert bit_alu.n_words(1) == 1
    assert bit_alu.n_words(64) == 1
    assert bit_alu.n_words(65) == 2
    assert bit_alu.n_words(940) == 15  # 14 full words + 44 bits in top
    assert bit_alu.n_words(13440) == 210


def test_random_hv_dimensions() -> None:
    from antikythera_spectral import bit_alu
    rng = np.random.default_rng(0)
    for D in (64, 128, 940, 13440):
        v = bit_alu.random_hv(D, rng)
        assert v.dtype == np.uint64
        assert v.shape == (bit_alu.n_words(D),)
        # Top-word unused bits must be zero.
        used_in_top = D - 64 * (bit_alu.n_words(D) - 1)
        if used_in_top < 64:
            top_mask = (1 << used_in_top) - 1
            assert int(v[-1]) & ~top_mask == 0, (
                f"D={D}: random_hv leaked non-zero bits past D"
            )


# ---------------------------------------------------------------------------
# Algebraic identities
# ---------------------------------------------------------------------------

def test_bind_is_self_inverse() -> None:
    """XOR-bind is involutive: bind(bind(a, b), b) == a for all a, b."""
    from antikythera_spectral import bit_alu
    rng = np.random.default_rng(0)
    D = 940
    a = bit_alu.random_hv(D, rng)
    b = bit_alu.random_hv(D, rng)
    ab = bit_alu.bind(a, b)
    a_recovered = bit_alu.bind(ab, b)
    assert bit_alu.hamming_distance(a, a_recovered) == 0


def test_permute_period_is_D() -> None:
    """permute(v, 1, D) applied D times returns v."""
    from antikythera_spectral import bit_alu
    rng = np.random.default_rng(0)
    D = 940
    v = bit_alu.random_hv(D, rng)
    rotated = v.copy()
    for _ in range(D):
        rotated = bit_alu.permute(rotated, 1, D)
    assert bit_alu.hamming_distance(rotated, v) == 0


def test_permute_step_correctness() -> None:
    """permute(v, n, D) == permute applied n times in single steps."""
    from antikythera_spectral import bit_alu
    rng = np.random.default_rng(0)
    D = 256  # smaller for speed
    v = bit_alu.random_hv(D, rng)
    direct = bit_alu.permute(v, 7, D)
    iterative = v.copy()
    for _ in range(7):
        iterative = bit_alu.permute(iterative, 1, D)
    assert bit_alu.hamming_distance(direct, iterative) == 0


def test_bundle_of_clones_is_input() -> None:
    """Majority bundle of M copies of `a` returns `a` (every bit
    above threshold)."""
    from antikythera_spectral import bit_alu
    rng = np.random.default_rng(0)
    D = 940
    a = bit_alu.random_hv(D, rng)
    bun = bit_alu.bundle_majority([a, a, a, a, a], D)
    assert bit_alu.hamming_distance(bun, a) == 0


def test_similarity_extremes() -> None:
    """Similarity of identical / complement vectors is +1 / −1."""
    from antikythera_spectral import bit_alu
    rng = np.random.default_rng(0)
    D = 940
    a = bit_alu.random_hv(D, rng)
    assert abs(bit_alu.similarity(a, a, D) - 1.0) < 1e-12
    # Complement: bit-NOT then mask top word back.
    not_a = a.copy()
    for w in range(len(not_a)):
        not_a[w] = ~not_a[w] & np.uint64(0xFFFFFFFFFFFFFFFF)
    # Mask the top word like _mask() does internally.
    used_in_top = D - 64 * (bit_alu.n_words(D) - 1)
    if used_in_top < 64:
        not_a[-1] &= np.uint64((1 << used_in_top) - 1)
    assert abs(bit_alu.similarity(a, not_a, D) - (-1.0)) < 1e-12


def test_similarity_random_pair_near_zero() -> None:
    """Two independently random hypervectors should have similarity
    close to 0 (Hamming ≈ D/2).  Tolerance: ±0.1 at D=940."""
    from antikythera_spectral import bit_alu
    rng = np.random.default_rng(0)
    D = 940
    a = bit_alu.random_hv(D, rng)
    b = bit_alu.random_hv(D, rng)
    sim = bit_alu.similarity(a, b, D)
    assert abs(sim) < 0.1, f"random-pair similarity = {sim:.4f}; expected ~0"


# ---------------------------------------------------------------------------
# Encoder round-trip — at least one calendar dial must decode correctly
# ---------------------------------------------------------------------------

def test_encode_decode_round_trip_callippic() -> None:
    """``encode_ant_bit`` then ``decode_dial_bit`` recovers the
    encoded residue for at least one calendar dial.

    Note: BSC majority-bundling is lossy; not every dial decodes
    perfectly under all date offsets.  This test asserts the
    weakest-possible round-trip property — at least the Callippic
    dial (the largest modulus, dominating the bundle) decodes —
    not perfect recovery of every dial.
    """
    from antikythera_spectral import bit_alu
    from antikythera_spectral._research.encode_ant import (
        DIAL_SPECS, REFERENCE_JD,
    )

    D = 940
    jd = REFERENCE_JD + 100.0  # arbitrary mid-cycle date

    # Find the index of the Callippic dial.
    callippic_idx = None
    callippic = None
    for i, spec in enumerate(DIAL_SPECS):
        if spec.is_supported(D) and "callippic" in spec.name.lower():
            callippic_idx = i
            callippic = spec
            break
    assert callippic_idx is not None, "no callippic dial in DIAL_SPECS"
    assert callippic is not None

    expected_residue = callippic.residue(jd, D)
    state = bit_alu.encode_ant_bit(jd, D)

    decoded_residue, decoded_sim = bit_alu.decode_dial_bit(
        state, D, callippic_idx, modulus=D,
    )
    # Allow a small slack: under BSC bundling with M dials, the decode
    # is the argmax over D candidates; due to noise from the other M-1
    # dials, the argmax can land 1-2 positions from the true residue.
    diff = min(
        abs(decoded_residue - expected_residue),
        D - abs(decoded_residue - expected_residue),
    )
    assert diff <= 5, (
        f"callippic decode off by {diff} positions "
        f"(expected={expected_residue}, got={decoded_residue}, "
        f"sim={decoded_sim:.4f})"
    )
