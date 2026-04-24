"""Sanity tests for othello_spectral.encode_768.

Run:
    cd docs/othello-maths/research
    python -m othello_spectral.tests.test_encoder_sanity

Or via pytest:
    pytest othello_spectral/tests/test_encoder_sanity.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


# Allow running this file both as `python -m othello_spectral.tests...`
# and as a bare `pytest` target: ensure research/ is on sys.path so
# that `import othello_spectral` resolves.
_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from othello_spectral import (  # noqa: E402
    CHANNEL_NAMES,
    ENCODING_DIM,
    channel_energies,
    encode_768,
)
from othello_spectral.encoder import channel_block  # noqa: E402
from othello_spectral.tables import N_CHANNELS  # noqa: E402


def _starting_state() -> np.ndarray:
    """Standard Othello opening: d4/e5 white, d5/e4 black."""
    s = np.zeros(64, dtype=int)
    # d4 = (3, 3), e4 = (3, 4), d5 = (4, 3), e5 = (4, 4)
    s[3 * 8 + 3] = -1  # d4 white
    s[3 * 8 + 4] = +1  # e4 black
    s[4 * 8 + 3] = +1  # d5 black
    s[4 * 8 + 4] = -1  # e5 white
    return s


def test_dim_and_dtype() -> None:
    enc = encode_768(_starting_state())
    assert enc.shape == (ENCODING_DIM,), enc.shape
    assert enc.dtype == np.float64, enc.dtype
    assert len(CHANNEL_NAMES) == N_CHANNELS == 12


def test_empty_board_all_zero() -> None:
    enc = encode_768(np.zeros(64, dtype=int))
    assert float(np.max(np.abs(enc))) < 1e-12, (
        "empty board should encode to all zeros"
    )


def test_starting_board_energies() -> None:
    enc = encode_768(_starting_state())
    e = channel_energies(enc)
    # Expected structural facts (verified by direct computation):
    # - magnetisation = [+1, +1, -1, -1] at the 4 centre cells,
    #   net zero.  Projection onto D4-invariant A1 magnetisation
    #   is zero.
    # - occupation = all four centre cells, fully D4-symmetric.  So
    #   occ_A1plus carries all 4 cells' worth of fully-symmetric
    #   content.
    # - Starting magnetisation has a reflection symmetry but is
    #   Z2-odd, so A1- energy is 0 and E- energy is 0.
    assert e["magn_A1minus"] < 1e-18, e["magn_A1minus"]
    assert e["occ_A1plus"] > 0.0, e["occ_A1plus"]
    # Total norm consistent with sum of channels
    total = sum(e.values())
    sq = float(np.dot(enc, enc))
    assert abs(total - sq) < 1e-10, (total, sq)


def test_channel_block_addressing() -> None:
    enc = encode_768(_starting_state())
    # Named access matches positional access
    for i, name in enumerate(CHANNEL_NAMES):
        by_idx = channel_block(enc, i)
        by_name = channel_block(enc, name)
        assert np.array_equal(by_idx, by_name)
        assert by_idx.shape == (64,)


def test_determinism_rerun() -> None:
    s = _starting_state()
    a = encode_768(s)
    b = encode_768(s)
    assert np.array_equal(a, b), "encode_768 should be deterministic"


def test_linearity_under_scaling() -> None:
    # Magnetisation channels are linear in s; occupation channels
    # scale as s^2; fiber channels (L @ s) are linear in s.
    # Use an asymmetric state with non-zero projection on every
    # magnetisation channel (the starting board has A1-/A2- == 0 by
    # symmetry, which would give 0/0 on the ratio check).
    rng = np.random.default_rng(42)
    s = rng.choice([-1, 0, 1], size=64, p=[0.35, 0.3, 0.35]).astype(int)
    enc_s = encode_768(s)
    enc_2s = encode_768(2 * s)

    def _check(block_lo: int, block_hi: int, expected_ratio: float,
               label: str) -> None:
        for i in range(block_lo, block_hi):
            e1 = enc_s[i * 64: (i + 1) * 64]
            e2 = enc_2s[i * 64: (i + 1) * 64]
            mask = np.abs(e1) > 1e-9
            if not mask.any():
                # Channel is identically zero for this state; nothing
                # to check on it.  Other channels carry the test.
                continue
            observed = e2[mask] / e1[mask]
            assert np.allclose(observed, expected_ratio, atol=1e-9), (
                f"{label} channel {i} not {expected_ratio}x: "
                f"observed ratios {observed[:3]}"
            )

    # magn_* channels: linear in s -> 2x
    _check(0, 5, 2.0, "magn")
    # occ_* channels: quadratic -> 4x
    _check(5, 10, 4.0, "occ")
    # fiber_*_s channels: linear -> 2x
    _check(10, 12, 2.0, "fiber")


ALL_TESTS = [
    test_dim_and_dtype,
    test_empty_board_all_zero,
    test_starting_board_energies,
    test_channel_block_addressing,
    test_determinism_rerun,
    test_linearity_under_scaling,
]


if __name__ == "__main__":
    failures = 0
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            print(f"FAIL  {fn.__name__}: {exc}")
            failures += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
            failures += 1
    if failures:
        print(f"\n{failures} failures")
        sys.exit(1)
    print("\nall sanity tests passed")
