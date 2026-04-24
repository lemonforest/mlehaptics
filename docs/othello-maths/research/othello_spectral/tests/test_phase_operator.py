"""Sanity tests for SheafPhaseOperator.

Run:
  cd docs/othello-maths/research
  python -m othello_spectral.tests.test_phase_operator
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from othello_spectral import encode_768  # noqa: E402
from othello_spectral.phase_operator import (  # noqa: E402
    SheafPhaseOperator, VALID_MODES,
)
from othello_spectral.tables import ENCODING_DIM, channel_slice  # noqa: E402


def _starting_state() -> np.ndarray:
    s = np.zeros(64, dtype=int)
    s[3 * 8 + 3] = -1
    s[3 * 8 + 4] = +1
    s[4 * 8 + 3] = +1
    s[4 * 8 + 4] = -1
    return s


def _random_state(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.choice([-1, 0, 1], size=64, p=[0.4, 0.2, 0.4]).astype(int)


def test_identity_preserves_encoding() -> None:
    s = _starting_state()
    base = encode_768(s)
    op = SheafPhaseOperator(mode="identity")
    out = op.apply(base, s)
    assert np.array_equal(out, base), (
        "identity operator must preserve encoding exactly"
    )


def test_strength_zero_is_identity() -> None:
    s = _random_state(seed=7)
    base = encode_768(s)
    for mode in VALID_MODES:
        if mode == "scale_by_feature_coupling":
            continue
        op = SheafPhaseOperator(mode=mode, strength=0.0)
        out = op.apply(base, s)
        assert np.allclose(out, base, atol=1e-12), (
            f"strength=0 on mode {mode!r} should equal identity"
        )


def test_no_state_returns_enc() -> None:
    """apply(enc, state=None) must return the encoding unchanged."""
    enc = encode_768(_starting_state())
    op = SheafPhaseOperator(mode="scale_fiber_by_owner_lambda2")
    out = op.apply(enc, state=None)
    assert np.array_equal(out, enc)


def test_scale_fiber_only_affects_fiber_blocks() -> None:
    """scale_fiber_by_owner_lambda2 should leave irrep channels
    (0-9) untouched and scale ONLY channels 10, 11."""
    s = _random_state(seed=11)
    base = encode_768(s)
    op = SheafPhaseOperator(mode="scale_fiber_by_owner_lambda2")
    out = op.apply(base, s)
    for k in range(10):
        a = base[channel_slice(k)]
        b = out[channel_slice(k)]
        assert np.array_equal(a, b), (
            f"irrep channel {k} should be untouched"
        )
    # Fiber channels should be scaled (but not to zero — check not equal)
    for k in (10, 11):
        a = base[channel_slice(k)]
        b = out[channel_slice(k)]
        if np.any(a != 0):
            assert not np.array_equal(a, b), (
                f"fiber channel {k} should be scaled"
            )


def test_feature_coupling_mode() -> None:
    """scale_by_feature_coupling respects the (12, 8) matrix."""
    s = _random_state(seed=17)
    base = encode_768(s)
    # Identity-like coupling: first 8 channels get a single feature,
    # remaining 4 get zero — just a smoke test for the matmul path.
    M = np.zeros((12, 8), dtype=np.float64)
    for k in range(8):
        M[k, k] = 1.0
    op = SheafPhaseOperator(
        mode="scale_by_feature_coupling", coupling_matrix=M,
    )
    out = op.apply(base, s)
    assert out.shape == (ENCODING_DIM,)
    # Channel 11 has weight M[11] @ features = 0 => block should be zero
    assert np.allclose(out[channel_slice(11)], 0.0, atol=1e-12)


def test_operator_rejects_wrong_shape() -> None:
    op = SheafPhaseOperator(mode="identity")
    try:
        op.apply(np.zeros(10), None)
    except ValueError:
        return
    raise AssertionError("apply() should reject wrong shape")


ALL_TESTS = [
    test_identity_preserves_encoding,
    test_strength_zero_is_identity,
    test_no_state_returns_enc,
    test_scale_fiber_only_affects_fiber_blocks,
    test_feature_coupling_mode,
    test_operator_rejects_wrong_shape,
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
    print("\nall phase-operator tests passed")
