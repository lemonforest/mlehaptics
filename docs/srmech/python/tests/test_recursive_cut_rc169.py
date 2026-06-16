"""rc169 — §52 Part 2 out-of-core recursive partition driver (F793).

`recursive_cut` recursively bisects a bounded graph into community tomes, but
never holds the whole structure in RAM: the adjacency, every pending sub-graph,
and every finished tome live on disk; each bisection streams its induced edges
through the rc168 `fiedler_sparse_file`. These tests prove the partition is
correct (cliques split cleanly, full coverage, disjoint), the disk artifacts
exist, the leaf cap is honoured, and the degenerate/n<2 cases terminate.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""

import os
import shutil
import tempfile

import pytest

from srmech.amsc import laplacian as L


def _clique(off, k):
    return [(off + a, off + b) for a in range(k) for b in range(a + 1, k)]


def _cleanup(*results):
    for r in results:
        shutil.rmtree(r["work_dir"], ignore_errors=True)


def test_two_cliques_split_into_two_tomes():
    """Two 8-cliques joined by one weak bridge → exactly two tomes, each one
    clique, covering all nodes disjointly."""
    n = 16
    edges = _clique(0, 8) + _clique(8, 8) + [(0, 8)]
    w = [1.0] * (len(edges) - 1) + [0.01]
    r = L.recursive_cut(n, edges, w, max_tome=8)
    try:
        tomes = sorted(sorted(t) for t in r["tomes"])
        assert r["n_tomes"] == 2
        assert tomes == [list(range(8)), list(range(8, 16))]
        # full, disjoint cover
        flat = sorted(x for t in r["tomes"] for x in t)
        assert flat == list(range(n))
    finally:
        _cleanup(r)


def test_four_cliques_recurse_to_four_tomes():
    """Four 6-cliques in a chain of weak bridges recurse to four ≤6-node tomes
    (the recursion descends, not just one bisection)."""
    n = 24
    edges = []
    for blk in range(4):
        edges += _clique(blk * 6, 6)
    edges += [(0, 6), (6, 12), (12, 18)]  # weak chain
    w = [1.0] * (len(edges) - 3) + [0.01, 0.01, 0.01]
    r = L.recursive_cut(n, edges, w, max_tome=6)
    try:
        assert r["n_tomes"] == 4
        assert all(len(t) <= 6 for t in r["tomes"])
        flat = sorted(x for t in r["tomes"] for x in t)
        assert flat == list(range(n))
        # each tome is exactly one clique block
        blocks = {frozenset(range(b * 6, b * 6 + 6)) for b in range(4)}
        assert {frozenset(t) for t in r["tomes"]} == blocks
    finally:
        _cleanup(r)


def test_disk_artifacts_exist_and_are_bounded():
    """The graph, the tome files, and the work_dir are real on-disk artifacts;
    each tome_path round-trips via _read_node_set to its in-RAM node-set."""
    n = 16
    edges = _clique(0, 8) + _clique(8, 8) + [(0, 8)]
    r = L.recursive_cut(n, edges, max_tome=8)
    try:
        assert os.path.isdir(r["work_dir"])
        assert os.path.exists(os.path.join(r["work_dir"], "graph.bin"))
        assert len(r["tome_paths"]) == r["n_tomes"]
        for path, ids in zip(r["tome_paths"], r["tomes"]):
            assert os.path.exists(path)
            assert L._read_node_set(path) == ids
    finally:
        _cleanup(r)


def test_leaf_cap_no_cut_below_max_tome():
    """A graph already ≤ max_tome is a single tome (no bisection attempted)."""
    n = 5
    edges = _clique(0, 5)
    r = L.recursive_cut(n, edges, max_tome=256)
    try:
        assert r["n_tomes"] == 1
        assert sorted(r["tomes"][0]) == list(range(5))
    finally:
        _cleanup(r)


def test_uncuttable_homogeneous_block_terminates():
    """A single big clique (> max_tome) can't be spectrally split — the Fiedler
    gives a one-sided sign, so it is emitted as one (oversized) tome rather than
    recursing forever."""
    n = 20
    edges = _clique(0, 20)  # one clique, no community structure
    r = L.recursive_cut(n, edges, max_tome=8, max_depth=10)
    try:
        # it cannot be cut into communities → all nodes stay together (or at
        # most a couple of degenerate splits), but it MUST terminate + cover all
        flat = sorted(x for t in r["tomes"] for x in t)
        assert flat == list(range(n))
        assert r["n_tomes"] >= 1
    finally:
        _cleanup(r)


def test_n_less_than_two_single_tome():
    r1 = L.recursive_cut(1, [(0, 0)])
    r0 = L.recursive_cut(0, [])
    try:
        assert r1["n_tomes"] == 1 and r1["tomes"] == [[0]]
        assert r0["n_tomes"] == 1 and r0["tomes"] == [[]]
    finally:
        _cleanup(r1, r0)


def test_explicit_work_dir_is_reused():
    d = tempfile.mkdtemp()
    try:
        n = 16
        edges = _clique(0, 8) + _clique(8, 8) + [(0, 8)]
        r = L.recursive_cut(n, edges, max_tome=8, work_dir=d)
        assert r["work_dir"] == d
        assert os.path.exists(os.path.join(d, "graph.bin"))
        assert r["n_tomes"] == 2
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_recursive_cut_matches_single_bisect_at_top():
    """The top-level split recursive_cut makes equals normalized_cut_bisect on
    the same graph (recursive_cut IS recursive normalized_cut_bisect, out-of-core)."""
    n = 16
    edges = _clique(0, 8) + _clique(8, 8) + [(0, 8)]
    w = [1.0] * (len(edges) - 1) + [0.01]
    # max_tome = 8 → exactly the top bisection, no deeper recursion
    r = L.recursive_cut(n, edges, w, max_tome=8)
    try:
        left, right = L.normalized_cut_bisect(n, edges, w)
        got = {frozenset(t) for t in r["tomes"]}
        assert got == {frozenset(left), frozenset(right)}
    finally:
        _cleanup(r)
