"""v0.7.5rc36 — numpy-FREE native dispatch for the Class-L graph BUILD ops
(UPSTREAM §38, completing the rc35 jacobi work).

``dense_adjacency`` / ``dense_laplacian`` / ``normalized_laplacian`` reach the
bound C ``srmech_graph_*`` builder via ``_build_matrix_native_listmarshal``
(Python list → flat ctypes buffers → reshape) so a numpy-absent install hits
the same C builder. (Build is O(edges)-cheap; this is the carrier-removal
consistency win, not the perf-critical eig.)

Post-#564 numpy is GONE from srmech entirely (no ``laplacian.np`` attribute),
so the public builders are numpy-free by default and return ``list[list[float]]``.
The reference values are hand-computed closed-form matrices (no numpy oracle).
"""
from __future__ import annotations

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


def _ref_adjacency():
    """Closed-form weighted adjacency for (_EDGES, _WTS) — hand-computed."""
    A = [[0.0] * _N for _ in range(_N)]
    for (u, v), w in zip(_EDGES, _WTS):
        A[u][v] += w
        A[v][u] += w
    return A


def _ref_laplacian():
    """L = D − A with D the weighted-degree diagonal — hand-computed."""
    A = _ref_adjacency()
    L = [[-A[i][j] for j in range(_N)] for i in range(_N)]
    for i in range(_N):
        L[i][i] = sum(A[i])      # degree − (−A[i][i]); A diagonal is 0 here
    return L


def _ref_normalized():
    """L_sym = I − D^(−1/2) A D^(−1/2) — hand-computed (all degrees > 0)."""
    A = _ref_adjacency()
    deg = [sum(A[i]) for i in range(_N)]
    Lsym = [[0.0] * _N for _ in range(_N)]
    for i in range(_N):
        for j in range(_N):
            if i == j:
                Lsym[i][j] = 1.0 if deg[i] > 0 else 0.0
            elif deg[i] > 0 and deg[j] > 0:
                Lsym[i][j] = -A[i][j] / ((deg[i] ** 0.5) * (deg[j] ** 0.5))
    return Lsym


_REFS = {
    "srmech_graph_dense_adjacency": _ref_adjacency(),
    "srmech_graph_dense_laplacian": _ref_laplacian(),
    "srmech_graph_normalized_laplacian": _ref_normalized(),
}


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="needs the native libsrmech")
def test_listmarshal_matches_hand_computed_native_build():
    el = [(int(u), int(v)) for u, v in _EDGES]
    for fn in _FNS:
        ref = _REFS[fn]
        m = _lap._build_matrix_native_listmarshal(fn, _N, el, list(_WTS))
        assert m is not None and isinstance(m, list)
        err = max(abs(m[i][j] - ref[i][j]) for i in range(_N) for j in range(_N))
        assert err < 1e-12, (fn, err)


def test_numpy_free_build_dispatches_and_is_correct():
    """Post-#564 the public builders are numpy-free by default; rc129 each
    returns a numpy-free ``Mat`` (``.shape`` + ``m[i, j]``) — native list-marshal
    when HAS_NATIVE, else pure Python — matching the hand-computed matrix."""
    from srmech.amsc.mat import Mat
    assert not hasattr(_lap, "np")     # numpy is gone, not merely monkeypatched
    for fn, pub in _FNS.items():
        out = pub(_N, _EDGES, _WTS)
        assert isinstance(out, Mat) and out.shape == (_N, _N)   # rc129: Mat carrier
        ref = _REFS[fn]
        err = max(abs(out[i, j] - ref[i][j]) for i in range(_N) for j in range(_N))
        assert err < 1e-12, (fn, err)
