"""v0.7.5rc35 — jacobi_eigvals numpy-FREE native dispatch (UPSTREAM §38 / F708).

The bound ``srmech_jacobi_eigvals`` C symbol is reachable without numpy: the
numpy-absent branch of :func:`laplacian.jacobi_eigvals` marshals a
``list[list[float]]`` into a flat ctypes ``double`` buffer and calls it
(~49× faster than the pure-Python Jacobi cascade at n=256; 1.4 s vs 68 s),
falling back to the cascade only when there is no native lib / n too large /
non-OK status.

Post-#564 numpy is GONE from srmech entirely (no ``laplacian.np`` attribute),
so the "numpy-absent branch" is simply the default path. The reference
spectrum is hand-computed (no numpy oracle): srmech's own pure-Python Jacobi
cascade is the substrate-native eigenvalue path and is used as the oracle.
"""
from __future__ import annotations

import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as _lap

_S = [[3.0, 1.0, 0.0], [1.0, 2.0, -1.0], [0.0, -1.0, 4.0]]
# Oracle: srmech's OWN pure-Python Jacobi cascade (the substrate-native
# eigenvalue path), NOT numpy LAPACK. The matrix is real-symmetric, so the
# cascade converges to the true spectrum to round-off.
_REF = sorted(_lap._jacobi_eigvals_py([row[:] for row in _S]))
_DIAG = [[float(i + 1) if i == j else 0.0 for j in range(5)] for i in range(5)]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native libsrmech")
def test_native_listmarshal_matches_cascade():
    """The numpy-free list-marshalling helper hits the C symbol + agrees with
    srmech's own Jacobi cascade (the native ↔ cascade parity)."""
    ev = _lap._jacobi_eigvals_native_listmarshal([row[:] for row in _S], 3, 100, 1e-12)
    assert ev is not None and isinstance(ev, list)
    assert max(abs(ev[i] - _REF[i]) for i in range(3)) < 1e-9
    # caller's matrix is untouched (the ctypes buffer is the in-place work array)
    assert _S == [[3.0, 1.0, 0.0], [1.0, 2.0, -1.0], [0.0, -1.0, 4.0]]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native libsrmech")
def test_native_listmarshal_diag_exact():
    # A diagonal matrix's eigenvalues ARE its (sorted) diagonal: {1,2,3,4,5}.
    ev = _lap._jacobi_eigvals_native_listmarshal([row[:] for row in _DIAG], 5, 100, 1e-12)
    assert ev is not None
    assert max(abs(ev[i] - (i + 1)) for i in range(5)) < 1e-9


def test_numpy_free_branch_dispatches_and_is_correct():
    """Post-#564 the public ``jacobi_eigvals`` is numpy-free by default; it
    returns correct (sorted, ``list[float]``) eigenvalues — via the native
    list-marshal when ``HAS_NATIVE``, else srmech's pure-Python Jacobi cascade.
    Either way: no numpy, correct."""
    assert not hasattr(_lap, "np")     # numpy is gone, not merely monkeypatched
    ev = _lap.jacobi_eigvals([row[:] for row in _S], 100, 1e-12)
    assert isinstance(ev, list)
    assert max(abs(ev[i] - _REF[i]) for i in range(3)) < 1e-9
