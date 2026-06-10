"""rc70 — the FFT op-family runs 1-D numpy-FREE (carrier-removal flip #1, #564).

The numpy-MATH sweep made `_fft_carrier`'s transform ride the numpy-free 1-D
`spectral_cascades` cascade; rc70 flips the carrier shaping too: the common
1-D / default-axis path is numpy-free (list → cascade → list), and the leaf +
its thin wrappers (`closed_form_ops.{fft,ifft,rfft,spectrogram}`,
`path_b_ops.{fft,ifft,rfft}`) drop their top-level `import numpy`.

These tests HIDE numpy (`monkeypatch.setitem(sys.modules, "numpy", None)`) and
prove the 1-D FFT family still computes — returning the framework-native list —
and that it is value-faithful to the numpy result computed with numpy present.
This is the honest decrement: not merely loadable numpy-free, but *runnable*.
"""

from __future__ import annotations

import sys
import cmath

import pytest

from srmech.signal_processing import _fft_carrier as _fc


def _ref_dft(x):
    """The defining 1-D DFT X[k] = Σ_n x[n]·exp(-2πi kn/N) (numpy-free oracle)."""
    n = len(x)
    return [
        sum(complex(x[m]) * cmath.exp(-2j * cmath.pi * k * m / n) for m in range(n))
        for k in range(n)
    ]


def test_fft_1d_runs_with_numpy_hidden(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)  # `import numpy` → ImportError
    x = [1.0, -2.0, 3.0, 0.5, -1.5, 2.0, 4.0, -3.0]
    got = _fc.fft(x)
    assert isinstance(got, list)  # framework-native carrier, not ndarray
    ref = _ref_dft(x)
    for a, b in zip(got, ref):
        assert abs(a - b) < 1e-9


def test_ifft_round_trip_with_numpy_hidden(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    back = _fc.ifft(_fc.fft(x))
    assert isinstance(back, list)
    for a, b in zip(back, x):
        assert abs(a - b) < 1e-9


def test_rfft_half_spectrum_with_numpy_hidden(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    x = [0.7, -1.1, 2.3, 0.0, 4.4, -2.2, 1.0, -0.5]
    half = _fc.rfft(x)
    assert isinstance(half, list) and len(half) == len(x) // 2 + 1
    ref = _ref_dft(x)[: len(x) // 2 + 1]
    for a, b in zip(half, ref):
        assert abs(a - b) < 1e-9


def test_rfft_rejects_complex_with_numpy_hidden(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    with pytest.raises(TypeError, match="does not accept complex"):
        _fc.rfft([1 + 1j, 2 + 0j, 3 - 1j, 4 + 0j])


def test_fftfreq_with_numpy_hidden(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    got = _fc.fftfreq(8, d=0.5)
    assert isinstance(got, list)
    # [0,1,2,3,-4,-3,-2,-1] · 1/(8·0.5) = ·0.25
    assert got == pytest.approx([0.0, 0.25, 0.5, 0.75, -1.0, -0.75, -0.5, -0.25])


def test_n_pad_and_truncate_with_numpy_hidden(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)
    x = [1.0, 2.0, 3.0]
    # zero-pad to 4 then DFT
    got = _fc.fft(x, n=4)
    ref = _ref_dft([1.0, 2.0, 3.0, 0.0])
    assert len(got) == 4
    for a, b in zip(got, ref):
        assert abs(a - b) < 1e-9
    # truncate to 2
    got2 = _fc.fft(x, n=2)
    ref2 = _ref_dft([1.0, 2.0])
    for a, b in zip(got2, ref2):
        assert abs(a - b) < 1e-9


def test_flipped_modules_have_no_top_level_numpy_import():
    """The 8 flipped FFT modules must not carry a top-level `import numpy`."""
    import srmech

    root = __import__("pathlib").Path(srmech.__file__).parent
    flipped = [
        "signal_processing/_fft_carrier.py",
        "signal_processing/closed_form_ops/fft.py",
        "signal_processing/closed_form_ops/ifft.py",
        "signal_processing/closed_form_ops/rfft.py",
        "signal_processing/closed_form_ops/spectrogram.py",
        "signal_processing/path_b_ops/fft.py",
        "signal_processing/path_b_ops/ifft.py",
        "signal_processing/path_b_ops/rfft.py",
    ]
    for rel in flipped:
        for line in (root / rel).read_text(encoding="utf-8").splitlines():
            assert not (
                line.startswith("import numpy") or line.startswith("from numpy")
            ), f"{rel} still has a top-level numpy import"
