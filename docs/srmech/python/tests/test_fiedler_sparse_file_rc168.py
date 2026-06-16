"""rc168 — §52 Part 2 out-of-core streaming Fiedler (F793).

The bounded co-occurrence graph is written to a packed binary edge file
(``write_packed_graph``) and the normalized-cut Fiedler streams it from disk
(``fiedler_sparse_file``) — only the O(n) working vectors are resident, so a
low-RAM target can partition a graph whose edge list exceeds RAM. These tests
prove the round-trip, the streamed-vs-in-RAM equivalence (the streaming path is
the same algorithm), the truncated-file guard, and the n<2 short-circuit.

numpy-free: a numpy-free module's test must itself be numpy-free
([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""

import os
import struct
import tempfile

import pytest

from srmech.amsc import laplacian as L


# A two-community graph: triangles {0,1,2} and {3,4,5} + one weak bridge 2—3.
TWO_BLOCK_EDGES = [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 3)]
TWO_BLOCK_W = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.05]


def _write(edges, weights=None):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "g.bin")
    n = L.write_packed_graph(p, edges, weights)
    return p, n


def test_packed_graph_round_trips_byte_exact():
    """write_packed_graph → _read_packed_graph recovers the edges + weights,
    and the file is exactly 16 bytes per record."""
    p, n = _write(TWO_BLOCK_EDGES, TWO_BLOCK_W)
    assert n == len(TWO_BLOCK_EDGES)
    assert os.path.getsize(p) == 16 * n
    edges, weights = L._read_packed_graph(p)
    assert edges == TWO_BLOCK_EDGES
    assert weights == TWO_BLOCK_W


def test_record_format_is_le_u32_u32_f64():
    """The on-disk record is exactly uint32 u | uint32 v | double w (16 B),
    native order — the layout the standalone-C reader memcpy's."""
    p, _ = _write([(7, 9)], [2.5])
    with open(p, "rb") as fh:
        blob = fh.read()
    assert len(blob) == 16
    u, v, w = struct.unpack("=IId", blob)
    assert (u, v, w) == (7, 9, 2.5)


def test_streamed_fiedler_equals_in_ram_fiedler():
    """The streaming Fiedler is the SAME power iteration as fiedler_sparse, so
    its vector equals fiedler_sparse on the same graph — bit-for-bit (same init,
    same matvec arithmetic, whichever path each takes)."""
    p, _ = _write(TWO_BLOCK_EDGES, TWO_BLOCK_W)
    fv_file = L.fiedler_sparse_file(6, p)
    fv_ram = L.fiedler_sparse(6, TWO_BLOCK_EDGES, TWO_BLOCK_W)
    assert fv_file.shape == (6,)
    assert all(fv_file[i] == fv_ram[i] for i in range(6))


def test_streamed_fiedler_clean_two_block_cut():
    """The sign of the streamed Fiedler separates {0,1,2} from {3,4,5}."""
    p, _ = _write(TWO_BLOCK_EDGES, TWO_BLOCK_W)
    fv = L.fiedler_sparse_file(6, p)
    sa = fv[0] >= 0
    assert (fv[1] >= 0) == sa and (fv[2] >= 0) == sa  # block A uniform
    sb = fv[3] >= 0
    assert (fv[4] >= 0) == sb and (fv[5] >= 0) == sb  # block B uniform
    assert sa != sb                                    # opposite signs


def test_n_less_than_two_is_zero_vector_without_reading():
    """n < 2 short-circuits to the zero vector and NEVER opens the file (so a
    missing/garbage path is irrelevant) — the no-cut degenerate case."""
    fv = L.fiedler_sparse_file(1, "this_path_does_not_exist.bin")
    assert list(fv) == [0.0]
    fv0 = L.fiedler_sparse_file(0, "also_missing.bin")
    assert list(fv0) == []


def test_default_weights_all_one():
    """Omitting weights writes all-1.0 records (drop-in for an unweighted
    co-occurrence graph)."""
    p, n = _write(TWO_BLOCK_EDGES)
    assert n == len(TWO_BLOCK_EDGES)
    _, weights = L._read_packed_graph(p)
    assert weights == [1.0] * n
    fv = L.fiedler_sparse_file(6, p)
    assert fv.shape == (6,)


def test_truncated_file_raises():
    """A file that is not a whole number of 16-byte records is a truncated
    graph — the no-native read path raises (mirrors the C BAD_INPUT guard)."""
    d = tempfile.mkdtemp()
    p = os.path.join(d, "trunc.bin")
    with open(p, "wb") as fh:
        fh.write(b"\x00" * 20)  # 20 bytes != k*16
    with pytest.raises(ValueError):
        L._read_packed_graph(p)


def test_write_packed_graph_rejects_negative_endpoint():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "neg.bin")
    with pytest.raises(ValueError):
        L.write_packed_graph(p, [(0, -1)])


def test_weights_shorter_than_edges_raises():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "short.bin")
    with pytest.raises(ValueError):
        L.write_packed_graph(p, [(0, 1), (1, 2)], [1.0])


def test_bigger_graph_partitions_past_dense_wall():
    """A 300-node two-clique graph (> the n≤256 dense-eig wall, ~22k streamed
    edges) partitions cleanly off the streamed file — the corpus-scale
    out-of-core path. Two dense blocks give a large spectral gap, so the
    inter-block cut is unambiguous (rings would be a pathological slow-
    convergence case: a tiny, near-degenerate gap)."""
    half = 150
    edges = []
    for a in range(half):                             # clique on block A
        for b in range(a + 1, half):
            edges.append((a, b))
    for a in range(half, 2 * half):                   # clique on block B
        for b in range(a + 1, 2 * half):
            edges.append((a, b))
    edges.append((0, half))                           # one weak bridge
    weights = [1.0] * (len(edges) - 1) + [0.01]
    p, _ = _write(edges, weights)
    fv = L.fiedler_sparse_file(2 * half, p)
    left = [i for i in range(2 * half) if fv[i] < 0]
    right = [i for i in range(2 * half) if fv[i] >= 0]
    # the cut is the two blocks (up to a global flip), every node placed right
    sides = ({i for i in left}, {i for i in right})
    block_a = set(range(half))
    block_b = set(range(half, 2 * half))
    assert sides in ((block_a, block_b), (block_b, block_a))
