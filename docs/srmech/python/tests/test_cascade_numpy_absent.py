"""v0.7.0rc30 — the cascade layer is numpy-absent-safe (UPSTREAM §22, step 2).

`srmech.amsc.{cyclic, primes, rational, format}` are already numpy-free (0
usages); the cascade layer's only numpy was (a) `compose.autocorrelation`'s
no-native FFT fallback and (b) `atoms._try_native_chiral_dual`'s float-list
accel path (the C callback marshals via numpy views). Both now degrade to a
numpy-free path so a numpy-absent install runs the cascade ops.
"""
import sys

import pytest

from srmech.amsc.cascade import atoms as _atoms
from srmech.amsc.cascade import compose as _compose


def _ref_autocorr(x):
    """The defining circular autocorrelation r[k] = Σ_n x[n]·x[(n+k) mod n]."""
    n = len(x)
    return [sum(x[i] * x[(i + k) % n] for i in range(n)) for k in range(n)]


def test_autocorrelation_matches_definition():
    x = [1.0, -2.0, 3.0, 0.5, -1.5, 2.0, 4.0, -3.0]
    got = _compose.autocorrelation(x)
    ref = _ref_autocorr(x)
    assert len(got) == len(x)
    for a, b in zip(got, ref):
        assert abs(a - b) < 1e-9
    # r[0] is the energy Σ x²
    assert abs(got[0] - sum(v * v for v in x)) < 1e-9


def test_autocorrelation_matches_numpy_fft_when_present():
    np = pytest.importorskip("numpy")
    x = [0.7, -1.1, 2.3, 0.0, 4.4, -2.2]
    ref = np.real(np.fft.ifft(np.abs(np.fft.fft(np.asarray(x, dtype=float))) ** 2))
    got = _compose.autocorrelation(x)
    for a, b in zip(got, ref.tolist()):
        assert abs(a - b) < 1e-9


def test_autocorrelation_empty():
    assert _compose.autocorrelation([]) == []


def test_autocorrelation_numpy_free_fallback(monkeypatch):
    """Force BOTH the native path and numpy unavailable → the pure-Python
    circular-autocorrelation sum still produces the right answer."""
    monkeypatch.setattr(_compose, "_try_native_autocorrelation", lambda x: None)
    monkeypatch.setitem(sys.modules, "numpy", None)  # `import numpy` → ImportError
    x = [1.0, 2.0, 3.0, 4.0]
    r = _compose.autocorrelation(x)
    assert r == pytest.approx(_ref_autocorr(x))


def test_chiral_dual_native_degrades_without_numpy(monkeypatch):
    """`_try_native_chiral_dual` needs numpy for the callback marshalling;
    with numpy absent it must return None (→ the op's pure-Python fallback),
    NOT raise ImportError."""
    monkeypatch.setitem(sys.modules, "numpy", None)
    out = _atoms._try_native_chiral_dual(lambda v: v, [1.0, 2.0, 3.0])
    assert out is None


def test_cyclic_primes_rational_format_import_numpy_free():
    """The four already-numpy-free core modules carry no `import numpy` at all
    (audit-lock: they must stay numpy-free)."""
    import importlib
    import inspect
    for name in ("cyclic", "primes", "rational", "format"):
        mod = importlib.import_module(f"srmech.amsc.{name}")
        src = inspect.getsource(mod)
        assert "import numpy" not in src, f"srmech.amsc.{name} gained an import numpy"
