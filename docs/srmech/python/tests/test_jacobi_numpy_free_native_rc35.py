"""v0.7.5rc35 — jacobi_eigvals numpy-FREE native dispatch (UPSTREAM §38 / F708).

The bound ``srmech_jacobi_eigvals`` C symbol is reachable without numpy: the
numpy-absent branch of :func:`laplacian.jacobi_eigvals` now marshals a
``list[list[float]]`` into a flat ctypes ``double`` buffer and calls it
(~49× faster than the pure-Python Jacobi cascade at n=256; 1.4 s vs 68 s),
falling back to the cascade only when there is no native lib / n too large /
non-OK status. Before rc35 the numpy-absent path ran pure-Python unconditionally
even though the C symbol was bound.
"""
from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as _lap

_S = [[3.0, 1.0, 0.0], [1.0, 2.0, -1.0], [0.0, -1.0, 4.0]]
_REF = sorted(float(v) for v in np.linalg.eigvalsh(np.array(_S, dtype=float)))
_DIAG = [[float(i + 1) if i == j else 0.0 for j in range(5)] for i in range(5)]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native libsrmech")
def test_native_listmarshal_matches_numpy():
    """The numpy-free list-marshalling helper hits the C symbol + is correct."""
    ev = _lap._jacobi_eigvals_native_listmarshal([row[:] for row in _S], 3, 100, 1e-12)
    assert ev is not None and isinstance(ev, list)
    assert max(abs(ev[i] - _REF[i]) for i in range(3)) < 1e-9
    # caller's matrix is untouched (the ctypes buffer is the in-place work array)
    assert _S == [[3.0, 1.0, 0.0], [1.0, 2.0, -1.0], [0.0, -1.0, 4.0]]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native libsrmech")
def test_native_listmarshal_diag_exact():
    ev = _lap._jacobi_eigvals_native_listmarshal([row[:] for row in _DIAG], 5, 100, 1e-12)
    assert ev is not None
    assert max(abs(ev[i] - (i + 1)) for i in range(5)) < 1e-9


def test_numpy_absent_branch_dispatches_and_is_correct(monkeypatch):
    """Force the numpy-absent branch; it must still return correct (sorted,
    list[float]) eigenvalues — via the native list-marshal when HAS_NATIVE,
    else srmech's pure-Python Jacobi cascade. Either way: no numpy, correct."""
    monkeypatch.setattr(_lap, "np", None)
    ev = _lap.jacobi_eigvals([row[:] for row in _S], 100, 1e-12)
    assert isinstance(ev, list)
    assert max(abs(ev[i] - _REF[i]) for i in range(3)) < 1e-9
