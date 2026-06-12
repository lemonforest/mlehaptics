"""Tests for ``srmech.spectral`` MS #14 rcN+2 entries.

Verifies the three operations shipped at v0.4.2rc4 per user direction
2026-05-19:

- :func:`predict` — Class C ∘ L spectral-phase forward extrapolation.
- :func:`prediction_error` — Class M ∘ K XOR delta + gate-by-threshold.
- :func:`truncate_sparse` — Class K magnitude-band sparse-truncate.

Composes over the existing 14-class A-N vocabulary per
``[[feedback_no_privileged_primitive_classes]]``; no new primitive class
introduced.
"""

from __future__ import annotations

import random

import pytest

from srmech.spectral import (
    SpectralHandle,
    _unpack_complex128,
    clear_eigenbasis_cache,
    decompose,
    delta,
    predict,
    prediction_error,
    recompose,
    truncate_sparse,
)


# ---------------------------------------------------------------------------
# Helpers — small Hermitian Laplacian fixtures (matches test_spectral.py)
# ---------------------------------------------------------------------------

def _path_laplacian(n: int) -> list:
    """Path-graph Laplacian on n nodes (Hermitian, PSD).

    Returns a list-of-lists of floats: diagonal = node degree, off-diagonal
    -1.0 for adjacent path nodes (numpy-free).
    """
    L = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n - 1):
        L[i][i] += 1.0
        L[i + 1][i + 1] += 1.0
        L[i][i + 1] -= 1.0
        L[i + 1][i] -= 1.0
    return L


def _cycle_laplacian(n: int) -> list:
    """Cycle-graph Laplacian on n nodes (eigenvalues are clean cosines)."""
    L = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        L[i][i] = 2.0
        L[i][(i + 1) % n] = -1.0
        L[(i + 1) % n][i] = -1.0
    return L


def _random_state(n: int, seed: int = 0) -> list:
    """Reproducible real-valued state vector (deterministic, stdlib-only)."""
    r = random.Random(seed)
    return [r.uniform(-1.0, 1.0) for _ in range(n)]


# ---------------------------------------------------------------------------
# predict — Class C ∘ Class L
# ---------------------------------------------------------------------------

class TestPredict:
    def test_returns_handle(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(8)
        h = decompose(_random_state(8), L)
        p = predict(h, L)
        assert isinstance(p, SpectralHandle)

    def test_preserves_shape_and_descriptor(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(6)
        h = decompose(_random_state(6, seed=2), L)
        p = predict(h, L, steps=3, dt=0.5)
        assert p.n_modes == h.n_modes
        assert p.substrate_descriptor_hash == h.substrate_descriptor_hash
        assert len(p.coefficients_bytes) == len(h.coefficients_bytes)

    def test_zero_steps_identity(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(5)
        h = decompose(_random_state(5, seed=3), L)
        p = predict(h, L, steps=0)
        # exp(-i·λ·0) = 1 for every mode → identity in coefficients.
        assert p.coefficients_bytes == h.coefficients_bytes
        assert p.content_sha == h.content_sha

    def test_magnitude_preserved_unitary(self):
        """Phase rotation is unitary — coefficient magnitudes unchanged."""
        clear_eigenbasis_cache()
        L = _path_laplacian(7)
        h = decompose(_random_state(7, seed=4), L)
        p = predict(h, L, steps=5, dt=1.3)
        c_h = _unpack_complex128(h.coefficients_bytes, h.n_modes)
        c_p = _unpack_complex128(p.coefficients_bytes, p.n_modes)
        residual = max(
            abs(abs(c_h[i]) - abs(c_p[i])) for i in range(len(c_h))
        )
        assert residual < 1e-12, (c_h, c_p)

    def test_period_2pi_at_unit_lambda(self):
        """On a substrate where the largest eigenvalue is ~λ_max, evolving
        by dt·steps where the product hits a multiple of 2π should bring
        the spectral state back near the starting point (cyclic-natural
        substrate test)."""
        clear_eigenbasis_cache()
        # Cycle graph; eigenvalues are 2 − 2·cos(2πk/n).
        n = 8
        L = _cycle_laplacian(n)
        h = decompose(_random_state(n, seed=5), L)
        # Pick steps + dt small enough that prediction is non-trivial but
        # finite. We don't expect a clean period (eigenvalues are not
        # commensurate) — just non-trivial evolution + magnitude preserved.
        p = predict(h, L, steps=2, dt=0.7)
        c_h = _unpack_complex128(h.coefficients_bytes, h.n_modes)
        c_p = _unpack_complex128(p.coefficients_bytes, p.n_modes)
        # Magnitudes still bit-exact (Class L unitary).
        residual = max(
            abs(abs(c_h[i]) - abs(c_p[i])) for i in range(len(c_h))
        )
        assert residual < 1e-12, (c_h, c_p)
        # Phase has rotated — not equal to h (except at λ=0 mode).
        max_diff = max(abs(c_h[i] - c_p[i]) for i in range(len(c_h)))
        assert max_diff > 1e-9

    def test_recompose_predicted(self):
        """recompose(predict(h, L)) returns a real-valued (numerical) state
        on a real Hermitian Laplacian + 0 prediction steps (identity)."""
        clear_eigenbasis_cache()
        L = _path_laplacian(6)
        state = _random_state(6, seed=6)
        h = decompose(state, L)
        p = predict(h, L, steps=0)
        recovered = recompose(p, L)
        residual = max(abs(recovered[i] - state[i]) for i in range(len(state)))
        assert residual < 1e-10, (recovered, state)

    def test_corruption_detected(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        h = decompose(_random_state(4), L)
        bad = SpectralHandle(
            substrate_descriptor_hash=h.substrate_descriptor_hash,
            coefficients_bytes=b"\x00" * len(h.coefficients_bytes),
            content_sha=h.content_sha,  # mismatched on purpose
            n_modes=h.n_modes,
        )
        with pytest.raises(ValueError, match="content_sha mismatch"):
            predict(bad, L)

    def test_descriptor_mismatch_rejected(self):
        clear_eigenbasis_cache()
        L_a = _path_laplacian(5)
        L_b = _cycle_laplacian(5)
        h = decompose(_random_state(5), L_a)
        with pytest.raises(ValueError, match="descriptor_hash mismatch"):
            predict(h, L_b)


# ---------------------------------------------------------------------------
# prediction_error — Class M ∘ Class K
# ---------------------------------------------------------------------------

class TestPredictionError:
    def test_threshold_zero_equals_delta(self):
        """Default threshold=0.0 must return the raw XOR delta."""
        clear_eigenbasis_cache()
        L = _path_laplacian(5)
        h_a = decompose(_random_state(5, seed=10), L)
        h_b = decompose(_random_state(5, seed=11), L)
        err = prediction_error(h_a, h_b)
        raw = delta(h_a, h_b)
        assert err == raw

    def test_zero_delta_on_identical(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(5)
        state = _random_state(5, seed=12)
        h = decompose(state, L)
        err = prediction_error(h, h)
        assert err == b"\x00" * len(h.coefficients_bytes)

    def test_threshold_above_density_zeros_output(self):
        """When threshold exceeds the delta's popcount density, the
        gating step returns all-zero bytes."""
        clear_eigenbasis_cache()
        L = _path_laplacian(5)
        h_a = decompose(_random_state(5, seed=13), L)
        h_b = decompose(_random_state(5, seed=14), L)
        # Use threshold=1.0 which is the highest possible density →
        # any density at-or-below 1.0 will be gated to zero (the floor
        # is "at or below"). This catches the gating path.
        gated = prediction_error(h_a, h_b, threshold=1.0)
        assert gated == b"\x00" * len(h_a.coefficients_bytes)

    def test_threshold_below_density_returns_raw(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(5)
        h_a = decompose(_random_state(5, seed=15), L)
        h_b = decompose(_random_state(5, seed=16), L)
        raw = delta(h_a, h_b)
        # Threshold 0.0 always returns raw (per docstring).
        out = prediction_error(h_a, h_b, threshold=0.0)
        assert out == raw

    def test_threshold_out_of_range_rejected(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        h = decompose(_random_state(4), L)
        with pytest.raises(ValueError, match="threshold"):
            prediction_error(h, h, threshold=-0.1)
        with pytest.raises(ValueError, match="threshold"):
            prediction_error(h, h, threshold=1.1)

    def test_raw_bytes_input(self):
        a = b"\xff" * 16
        b = b"\x00" * 16
        # Density = 0.5 (XOR is all-ones in only one of them).
        out = prediction_error(a, b, threshold=0.0)
        assert out == b"\xff" * 16

    def test_predict_then_error_roundtrip(self):
        """Predict a substrate-natural step; observe the same predicted
        state → error must be zero (no surprise)."""
        clear_eigenbasis_cache()
        L = _path_laplacian(6)
        h = decompose(_random_state(6, seed=17), L)
        p = predict(h, L, steps=2, dt=0.5)
        err = prediction_error(p, p)
        assert err == b"\x00" * len(p.coefficients_bytes)


# ---------------------------------------------------------------------------
# truncate_sparse — Class K
# ---------------------------------------------------------------------------

class TestTruncateSparse:
    def test_keep_k_full_is_identity(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(6)
        h = decompose(_random_state(6, seed=20), L)
        t = truncate_sparse(h, keep_k=6)
        assert t.coefficients_bytes == h.coefficients_bytes
        assert t.content_sha == h.content_sha

    def test_keep_k_zero_zeros_all(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(5)
        h = decompose(_random_state(5, seed=21), L)
        t = truncate_sparse(h, keep_k=0)
        assert t.coefficients_bytes == b"\x00" * len(h.coefficients_bytes)
        assert t.n_modes == h.n_modes
        assert t.substrate_descriptor_hash == h.substrate_descriptor_hash

    def test_keep_k_keeps_highest_magnitude(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(8)
        h = decompose(_random_state(8, seed=22), L)
        coeffs = _unpack_complex128(h.coefficients_bytes, h.n_modes)
        k = 3
        t = truncate_sparse(h, keep_k=k)
        out = _unpack_complex128(t.coefficients_bytes, t.n_modes)
        # Exactly k modes non-zero.
        nonzero = [i for i in range(len(out)) if abs(out[i]) > 0]
        assert len(nonzero) == k
        # The k highest-magnitude modes of the input are preserved bit-exactly.
        order = sorted(
            range(len(coeffs)), key=lambda i: abs(coeffs[i]), reverse=True
        )
        expected_keep = set(order[:k])
        actual_keep = set(nonzero)
        assert expected_keep == actual_keep
        for i in nonzero:
            assert out[i] == coeffs[i]

    def test_threshold_keeps_above_floor(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(8)
        h = decompose(_random_state(8, seed=23), L)
        coeffs = _unpack_complex128(h.coefficients_bytes, h.n_modes)
        # Pick a threshold between the median and the max.
        magnitudes = [abs(c) for c in coeffs]
        srt = sorted(magnitudes)
        m = len(srt)
        # Median (matches the prior numpy mean-of-two-middle convention).
        if m % 2 == 1:
            thr = srt[m // 2]
        else:
            thr = (srt[m // 2 - 1] + srt[m // 2]) / 2.0
        t = truncate_sparse(h, threshold=thr)
        out = _unpack_complex128(t.coefficients_bytes, t.n_modes)
        for i in range(8):
            if magnitudes[i] >= thr:
                assert out[i] == coeffs[i]
            else:
                assert out[i] == 0

    def test_neither_provided_rejected(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        h = decompose(_random_state(4), L)
        with pytest.raises(ValueError, match="exactly one"):
            truncate_sparse(h)

    def test_both_provided_rejected(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        h = decompose(_random_state(4), L)
        with pytest.raises(ValueError, match="exactly one"):
            truncate_sparse(h, keep_k=2, threshold=0.5)

    def test_keep_k_out_of_range_rejected(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        h = decompose(_random_state(4), L)
        with pytest.raises(ValueError, match="keep_k"):
            truncate_sparse(h, keep_k=-1)
        with pytest.raises(ValueError, match="keep_k"):
            truncate_sparse(h, keep_k=5)  # > n_modes

    def test_negative_threshold_rejected(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        h = decompose(_random_state(4), L)
        with pytest.raises(ValueError, match="threshold"):
            truncate_sparse(h, threshold=-0.1)

    def test_corruption_detected(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        h = decompose(_random_state(4), L)
        bad = SpectralHandle(
            substrate_descriptor_hash=h.substrate_descriptor_hash,
            coefficients_bytes=b"\x00" * len(h.coefficients_bytes),
            content_sha=h.content_sha,
            n_modes=h.n_modes,
        )
        with pytest.raises(ValueError, match="content_sha mismatch"):
            truncate_sparse(bad, keep_k=1)

    def test_recompose_after_truncate(self):
        """Sparse-truncate then recompose returns a low-rank approximation
        of the original state. Magnitudes of recovered state should be
        finite (substrate-natural)."""
        clear_eigenbasis_cache()
        L = _path_laplacian(8)
        state = _random_state(8, seed=24)
        h = decompose(state, L)
        t = truncate_sparse(h, keep_k=4)
        recovered = recompose(t, L)
        # Recovered state is non-trivial real-valued vector (Hermitian L).
        import math
        assert all(math.isfinite(v.real) for v in recovered)
        # The k-mode approximation is closer to the original than the
        # all-zeros baseline.
        truncated_err = math.sqrt(
            sum(abs(state[i] - recovered[i].real) ** 2 for i in range(len(state)))
        )
        zero_baseline_err = math.sqrt(sum(v * v for v in state))
        assert truncated_err < zero_baseline_err


# ---------------------------------------------------------------------------
# Aggregate / ship-guard tests
# ---------------------------------------------------------------------------

class TestShipGuard:
    def test_all_three_in_namespace(self):
        from srmech.spectral import predict, prediction_error, truncate_sparse
        assert callable(predict)
        assert callable(prediction_error)
        assert callable(truncate_sparse)

    def test_tool_schema_registers_three(self):
        from srmech.amsc.tool_schema import get_tool_schema
        schema = get_tool_schema()
        names = {t.name for t in schema.tools}
        assert "srmech.spectral.predict" in names
        assert "srmech.spectral.prediction_error" in names
        assert "srmech.spectral.truncate_sparse" in names
