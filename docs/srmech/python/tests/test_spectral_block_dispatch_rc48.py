"""spectral_block_dispatch — the 1024-node 4-sector spectral one-call (rc48).

RBS-LM UPSTREAM_NOTES Ask-3: wire the four-sector (Klein-4 4-rung, F233) thread
pattern to eigendecompose ≤4 dense symmetric blocks (each n ≤ 256) so that
4 × 256 = 1024 nodes are reachable within the native dense-eig bound. Each
block runs on its own thread (0 cross-thread reads), so the parallel spectrum
equals the serial spectrum bit-for-bit.

These tests pin the per-block correctness, the bit-exact parallel==serial
guarantee, the combined merged-sorted spectrum, the F220 4-cap + per-block 256
bound, and the numpy-free list-input path.
"""

from __future__ import annotations

import itertools

import pytest

from srmech.amsc.laplacian import (
    MAX_NATIVE_NODES,
    jacobi_eigvals,
    spectral_block_dispatch,
)

# Triangle-graph Laplacian: eigenvalues [0, 3, 3].
_TRI = [[2.0, -1.0, -1.0], [-1.0, 2.0, -1.0], [-1.0, -1.0, 2.0]]
# Path-2 Laplacian: eigenvalues [0, 2].
_PATH2 = [[1.0, -1.0], [-1.0, 1.0]]


def _eig_list(m):
    ev = jacobi_eigvals(m)
    return list(ev.tolist()) if hasattr(ev, "tolist") else list(ev)


def test_per_block_spectra_correct():
    r = spectral_block_dispatch([_TRI, _PATH2])
    assert r["ok"] is True
    assert r["n_blocks"] == 2
    assert r["block_sizes"] == [3, 2]
    assert r["n_nodes"] == 5
    assert [round(x, 6) for x in r["blocks"][0]] == [0.0, 3.0, 3.0]
    assert [round(x, 6) for x in r["blocks"][1]] == [0.0, 2.0]


def test_combined_is_merged_sorted():
    r = spectral_block_dispatch([_TRI, _PATH2])
    assert [round(x, 6) for x in r["combined"]] == [0.0, 0.0, 2.0, 3.0, 3.0]


def test_parallel_equals_serial_bit_for_bit():
    blocks = [_TRI, _PATH2, _TRI]
    r = spectral_block_dispatch(blocks)
    serial = sorted(itertools.chain.from_iterable(_eig_list(b) for b in blocks))
    assert r["combined"] == serial


def test_combine_false_leaves_combined_none():
    r = spectral_block_dispatch([_TRI], combine=False)
    assert r["combined"] is None
    assert r["blocks"][0] == _eig_list(_TRI) or \
        [round(x, 6) for x in r["blocks"][0]] == [0.0, 3.0, 3.0]


def test_four_blocks_reach_the_cap():
    r = spectral_block_dispatch([_PATH2, _PATH2, _PATH2, _PATH2])
    assert r["n_blocks"] == 4
    assert r["n_nodes"] == 8
    assert [round(x, 6) for x in r["combined"]] == [0.0, 0.0, 0.0, 0.0,
                                                    2.0, 2.0, 2.0, 2.0]


def test_more_than_four_blocks_rejected():
    with pytest.raises(ValueError):
        spectral_block_dispatch([_PATH2] * 5)  # the F220 Klein-4 4-cap


def test_empty_blocks_rejected():
    with pytest.raises(ValueError):
        spectral_block_dispatch([])


def test_oversize_block_rejected():
    n = MAX_NATIVE_NODES + 1
    big = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    with pytest.raises(ValueError):
        spectral_block_dispatch([big])  # per-block dense-eig bound is 256


def test_non_square_block_rejected():
    with pytest.raises(ValueError):
        spectral_block_dispatch([[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]])


def test_deterministic():
    a = spectral_block_dispatch([_TRI, _PATH2])
    b = spectral_block_dispatch([_TRI, _PATH2])
    assert a["combined"] == b["combined"]
    assert a["blocks"] == b["blocks"]


def test_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.spectral_block_dispatch" in names
