"""v0.7.0rc30 — the cascade layer is numpy-absent-safe (UPSTREAM §22, step 2).

`srmech.amsc.{cyclic, primes, rational, format}` are already numpy-free (0
usages); the cascade layer's only numpy was `compose.autocorrelation`'s
no-native FFT fallback, which now degrades to a numpy-free direct
circular-autocorrelation sum so a numpy-absent install runs the cascade ops.

(#564 capstone: numpy has been removed entirely from srmech — there is no
numpy oracle and no numpy-marshalling native callback path left. The former
``test_autocorrelation_matches_numpy_fft_when_present`` (numpy-oracle) and
``test_chiral_dual_native_degrades_without_numpy`` (an obsolete numpy callback
path, ``_try_native_chiral_dual``, that no longer exists) have been deleted.)
"""
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


def test_autocorrelation_empty():
    assert _compose.autocorrelation([]) == []


def test_autocorrelation_numpy_free_fallback(monkeypatch):
    """Force the native path unavailable → the pure-Python circular-
    autocorrelation sum (no numpy, no FFT) still produces the right answer."""
    monkeypatch.setattr(_compose, "_try_native_autocorrelation", lambda x: None)
    x = [1.0, 2.0, 3.0, 4.0]
    r = _compose.autocorrelation(x)
    ref = _ref_autocorr(x)
    assert len(r) == len(ref)
    for a, b in zip(r, ref):
        assert abs(a - b) < 1e-9


def test_cyclic_primes_rational_format_import_numpy_free():
    """The four already-numpy-free core modules carry no `import numpy` at all
    (audit-lock: they must stay numpy-free)."""
    import importlib
    import inspect
    for name in ("cyclic", "primes", "rational", "format"):
        mod = importlib.import_module(f"srmech.amsc.{name}")
        src = inspect.getsource(mod)
        assert "import numpy" not in src, f"srmech.amsc.{name} gained an import numpy"
