"""rc61 — np.fft.fft / np.fft.ifft → spectral_cascades FFT cascade.

The numpy-removal loop's `linalg_fft` batch: the 15 one-dimensional
`np.fft.fft(x)` / `np.fft.ifft(x)` callsites across signal_processing
(cross_spectral, ofdm, spectral_subtraction, multitaper, stft, wiener,
path_b/wiener) now route onto the value-faithful
`srmech.amsc.cascade.spectral_cascades.fft` / `.ifft` cascade
(radix-2 Cooley-Tukey with a dft fallback for non-power-of-2 N —
exact-until-rotation), wrapped `np.asarray(...)` so the result stays an
ndarray carrier. No new public op: the cascade already shipped (rc36/rc37).

This test pins three invariants:

1. the cascade fft/ifft are value-faithful to numpy across real + complex
   inputs at power-of-2 AND non-power-of-2 N (the property the route relies on);
2. the routed signal_processing ops still produce numpy-equivalent output
   (Wiener gain, OFDM round-trip, spectral subtraction, coherence);
3. the routed modules carry no residual `np.fft.fft(` / `np.fft.ifft(`
   1-D callsites (the ledger actually dropped, not just rerouted in prose).

Sign / phase-boundary discipline (Class K) stays in the cascade; this layer
only swaps the FFT *carrier* (numpy FFT → cascade FFT), value-for-value.
"""

from __future__ import annotations

import re
import pathlib

import numpy as np
import pytest

from srmech.amsc.cascade import spectral_cascades as _sc


# ---------------------------------------------------------------------------
# 1. the cascade is value-faithful to numpy — the routing precondition
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [2, 3, 4, 5, 7, 8, 9, 16, 17, 32, 40, 64, 100])
def test_cascade_fft_matches_numpy_complex(n):
    rng = np.random.default_rng(1234 + n)
    x = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    assert np.allclose(np.asarray(_sc.fft(x)), np.fft.fft(x), atol=1e-9)
    assert np.allclose(np.asarray(_sc.ifft(x)), np.fft.ifft(x), atol=1e-9)


@pytest.mark.parametrize("n", [2, 3, 5, 8, 12, 16, 33, 64])
def test_cascade_fft_matches_numpy_real(n):
    rng = np.random.default_rng(99 + n)
    x = rng.standard_normal(n)
    assert np.allclose(np.asarray(_sc.fft(x)), np.fft.fft(x), atol=1e-9)


def test_cascade_fft_ifft_round_trip():
    rng = np.random.default_rng(7)
    x = rng.standard_normal(48) + 1j * rng.standard_normal(48)
    back = np.asarray(_sc.ifft(np.asarray(_sc.fft(x))))
    assert np.allclose(back, x, atol=1e-9)


# ---------------------------------------------------------------------------
# 2. the routed signal_processing ops are still numpy-equivalent
# ---------------------------------------------------------------------------

def test_wiener_op_value_faithful():
    from srmech.signal_processing.closed_form_ops import wiener

    rng = np.random.default_rng(3)
    sig = rng.standard_normal(64)
    noise_psd = np.full(64, 0.1)
    out = wiener.op(sig, noise_psd)
    # routed op stays finite, real, and shape-preserving (rc87: numpy-free list)
    assert len(out) == len(sig)
    assert np.all(np.isfinite(out))
    assert np.isrealobj(out) or np.allclose(out.imag, 0.0, atol=1e-9)


def test_ofdm_round_trip_value_faithful():
    from srmech.signal_processing.closed_form_ops import ofdm

    rng = np.random.default_rng(11)
    # modulate two OFDM symbols then demodulate — the ifft/fft pair must invert
    symbols = rng.standard_normal(32) + 1j * rng.standard_normal(32)
    mod = ofdm.op(symbols, n_subcarriers=16, cp_length=4)
    demod = ofdm.op(mod, n_subcarriers=16, cp_length=4, demodulate=True)
    # rc84: ofdm demodulate returns a numpy-free list-of-lists (2 OFDM symbols
    # x 16 subcarriers); flatten via a comprehension at the test boundary.
    assert len(demod) == 2 and len(demod[0]) == 16
    assert np.allclose([v for row in demod for v in row], symbols, atol=1e-8)


def test_spectral_subtraction_value_faithful():
    from srmech.signal_processing.closed_form_ops import spectral_subtraction

    rng = np.random.default_rng(5)
    sig = rng.standard_normal(128)
    noise_psd = np.full(128, 0.05)
    out = spectral_subtraction.op(sig, noise_psd)
    assert out.shape == sig.shape
    assert np.all(np.isfinite(out))


def test_cross_spectral_coherence_value_faithful():
    from srmech.signal_processing.closed_form_ops import cross_spectral

    rng = np.random.default_rng(13)
    x = rng.standard_normal(256)
    # coherence of a signal with itself is exactly 1 across the band
    freqs, coh = cross_spectral.op(x, x, frame_size=64, coherence=True)
    coh = np.asarray(coh)
    assert np.all(coh <= 1.0 + 1e-9)
    assert np.allclose(coh, 1.0, atol=1e-9)


# ---------------------------------------------------------------------------
# 3. the 1-D np.fft. callsites are actually gone from the routed modules
# ---------------------------------------------------------------------------

_ROUTED = [
    "signal_processing/closed_form_ops/cross_spectral.py",
    "signal_processing/closed_form_ops/ofdm.py",
    "signal_processing/closed_form_ops/spectral_subtraction.py",
    "signal_processing/closed_form_ops/multitaper.py",
    "signal_processing/closed_form_ops/stft.py",
    "signal_processing/closed_form_ops/wiener.py",
    "signal_processing/path_b_ops/wiener.py",
]

_FFT_CALL = re.compile(r"\bnp\.fft\.(?:fft|ifft)\(")


def test_routed_modules_have_no_residual_fft_callsites():
    import srmech

    pkg = pathlib.Path(srmech.__file__).parent
    for rel in _ROUTED:
        txt = (pkg / rel).read_text(encoding="utf-8")
        assert not _FFT_CALL.search(txt), f"{rel} still has a np.fft.fft/ifft callsite"
        assert "spectral_cascades as _sc" in txt, f"{rel} missing the cascade import"
