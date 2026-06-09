"""v0.7.5rc36 — numpy-FREE native dispatch for the Class-L graph BUILD ops
(UPSTREAM §38, completing the rc35 jacobi work).

`dense_adjacency` / `dense_laplacian` / `normalized_laplacian` previously
dispatched to the bound C `srmech_graph_*` symbol only when numpy was present;
numpy-absent fell to the pure-Python builder. rc36 adds
`_build_matrix_native_listmarshal` (Python list → flat ctypes buffers → reshape)
so the numpy-absent install reaches the same C builder. (Build is O(edges)-cheap;
this is the carrier-removal consistency win, not the perf-critical eig.)
"""
from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as _lap

_EDGES = [(0, 1), (1, 2), (2, 3), (0, 3), (1, 3)]
_WTS = [1.0, 2.0, 1.5, 0.5, 3.0]
_N = 4
_FNS = {
    "srmech_graph_dense_adjacency": _lap.dense_adjacency,
    "srmech_graph_dense_laplacian": _lap.dense_laplacian,
    "srmech_graph_normalized_laplacian": _lap.normalized_laplacian,
}


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native libsrmech")
def test_listmarshal_matches_numpy_native_build():
    el = [(int(u), int(v)) for u, v in _EDGES]
    for fn, pub in _FNS.items():
        ref = pub(_N, _EDGES, _WTS)  # numpy present → C native via numpy marshal
        m = _lap._build_matrix_native_listmarshal(fn, _N, el, list(_WTS))
        assert m is not None and isinstance(m, list)
        err = max(abs(m[i][j] - float(ref[i][j])) for i in range(_N) for j in range(_N))
        assert err < 1e-12, (fn, err)


def test_numpy_absent_build_dispatches_and_is_correct(monkeypatch):
    # references computed WITH numpy first (the C-native numpy path)
    refs = {fn: pub(_N, _EDGES, _WTS) for fn, pub in _FNS.items()}
    monkeypatch.setattr(_lap, "np", None)
    for fn, pub in _FNS.items():
        out = pub(_N, _EDGES, _WTS)  # numpy-absent → list[list[float]] (native or pure-Python)
        assert isinstance(out, list)
        ref = refs[fn]
        err = max(abs(out[i][j] - float(ref[i][j])) for i in range(_N) for j in range(_N))
        assert err < 1e-12, (fn, err)
