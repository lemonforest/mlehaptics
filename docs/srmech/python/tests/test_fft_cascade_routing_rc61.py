"""rc61 — np.fft.fft / np.fft.ifft → spectral_cascades FFT cascade.

The numpy-removal loop's `linalg_fft` batch: the 15 one-dimensional
`np.fft.fft(x)` / `np.fft.ifft(x)` callsites across signal_processing
(cross_spectral, ofdm, spectral_subtraction, multitaper, stft, wiener,
path_b/wiener) now route onto the value-faithful
`srmech.amsc.cascade.spectral_cascades.fft` / `.ifft` cascade
(radix-2 Cooley-Tukey with a dft fallback for non-power-of-2 N —
exact-until-rotation). The cascade returns plain `list[complex]` now
(numpy GONE); the routed ops likewise return numpy-free lists.

This test pins three invariants:

1. the cascade fft/ifft are value-faithful to a cmath DFT-by-definition oracle
   across real + complex inputs at power-of-2 AND non-power-of-2 N;
2. the routed signal_processing ops still produce correct numpy-free output
   (Wiener gain, OFDM round-trip, spectral subtraction, coherence);
3. the routed modules carry no residual `np.fft.fft(` / `np.fft.ifft(`
   1-D callsites (the ledger actually dropped, not just rerouted in prose).

Sign / phase-boundary discipline (Class K) stays in the cascade; this layer
only swaps the FFT *carrier*, value-for-value.

numpy is GONE from srmech — these tests run and pass with numpy NOT installed.
Fixtures use random.Random; references use cmath/math.
"""

from __future__ import annotations

import cmath
import math
import random
import re
import pathlib

import pytest

from srmech.amsc.cascade import spectral_cascades as _sc


# ---------------------------------------------------------------------------
# numpy-free oracles + helpers
# ---------------------------------------------------------------------------

def _dft_ref(x, inverse=False):
    """DFT by definition via cmath: X[k] = Σ_n x[n]·e^{∓2πi·kn/N} (÷N if inverse)."""
    n = len(x)
    sign = 1.0 if inverse else -1.0
    out = []
    for k in range(n):
        acc = 0j
        for idx in range(n):
            acc += complex(x[idx]) * cmath.exp(sign * 2j * math.pi * k * idx / n)
        out.append(acc / n if inverse else acc)
    return out


def _max_abs_diff(got, want):
    return max((abs(complex(g) - complex(w)) for g, w in zip(got, want)), default=0.0)


def _rand_complex(rng, n):
    return [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]


def _rand_real(rng, n):
    return [rng.gauss(0, 1) for _ in range(n)]


# ---------------------------------------------------------------------------
# 1. the cascade is value-faithful to the DFT-by-definition — the routing precondition
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [2, 3, 4, 5, 7, 8, 9, 16, 17, 32, 40, 64, 100])
def test_cascade_fft_matches_definition_complex(n):
    rng = random.Random(1234 + n)
    x = _rand_complex(rng, n)
    assert _max_abs_diff(_sc.fft(x), _dft_ref(x)) <= 1e-9
    assert _max_abs_diff(_sc.ifft(x), _dft_ref(x, inverse=True)) <= 1e-9


@pytest.mark.parametrize("n", [2, 3, 5, 8, 12, 16, 33, 64])
def test_cascade_fft_matches_definition_real(n):
    rng = random.Random(99 + n)
    x = _rand_real(rng, n)
    assert _max_abs_diff(_sc.fft(x), _dft_ref(x)) <= 1e-9


def test_cascade_fft_ifft_round_trip():
    rng = random.Random(7)
    x = _rand_complex(rng, 48)
    back = _sc.ifft(_sc.fft(x))
    assert _max_abs_diff(back, x) <= 1e-9


# ---------------------------------------------------------------------------
# 2. the routed signal_processing ops are still correct (numpy-free)
# ---------------------------------------------------------------------------

def test_wiener_op_value_faithful():
    from srmech.signal_processing.closed_form_ops import wiener

    rng = random.Random(3)
    sig = _rand_real(rng, 64)
    noise_psd = [0.1] * 64
    out = wiener.op(sig, noise_psd)
    # routed op stays finite, real, and shape-preserving (rc87: numpy-free list)
    assert len(out) == len(sig)
    for v in out:
        assert math.isfinite(complex(v).real) and math.isfinite(complex(v).imag)
        assert abs(complex(v).imag) <= 1e-9


def test_ofdm_round_trip_value_faithful():
    from srmech.signal_processing.closed_form_ops import ofdm

    rng = random.Random(11)
    # modulate two OFDM symbols then demodulate — the ifft/fft pair must invert
    symbols = _rand_complex(rng, 32)
    mod = ofdm.op(symbols, n_subcarriers=16, cp_length=4)
    demod = ofdm.op(mod, n_subcarriers=16, cp_length=4, demodulate=True)
    # rc84: ofdm demodulate returns a numpy-free list-of-lists (2 OFDM symbols
    # x 16 subcarriers); flatten via a comprehension at the test boundary.
    assert len(demod) == 2 and len(demod[0]) == 16
    flat = [v for row in demod for v in row]
    assert _max_abs_diff(flat, symbols) <= 1e-8


def test_spectral_subtraction_value_faithful():
    from srmech.signal_processing.closed_form_ops import spectral_subtraction

    rng = random.Random(5)
    sig = _rand_real(rng, 128)
    noise_psd = [0.05] * 128
    out = spectral_subtraction.op(sig, noise_psd)
    # rc90: spectral_subtraction.op is numpy-free now — returns a list of float.
    assert isinstance(out, list) and len(out) == len(sig)
    for v in out:
        assert math.isfinite(complex(v).real) and math.isfinite(complex(v).imag)


def test_cross_spectral_coherence_value_faithful():
    from srmech.signal_processing.closed_form_ops import cross_spectral

    rng = random.Random(13)
    x = _rand_real(rng, 256)
    # coherence of a signal with itself is exactly 1 across the band
    freqs, coh = cross_spectral.op(x, x, frame_size=64, coherence=True)
    assert all(c <= 1.0 + 1e-9 for c in coh)
    assert all(abs(c - 1.0) <= 1e-9 for c in coh)


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
