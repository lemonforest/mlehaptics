"""§100 G1 (rc284) — BYTE-PARITY between the two coherency projections of
``laplacian.recursive_cut``.

ADR-0009: the capability is the invariant; neither implementation is primary. So
the test is not "does C agree with Python" — it is "do the two projections emit
the SAME BYTES". Every tome file is compared byte-for-byte, in order, along with
the returned tome sizes, ordering and status.

The native driver landed in rc284; before it, the Fiedler ENGINE was native
(rc168) but the ``while pending`` RECURSION around it was Python-only, so a
bare-C host could bisect once and no further. These cases pin the whole
recursion — including the degenerate shapes that are where an out-of-core queue
driver actually breaks (disconnected, edgeless, complete/degenerate spectrum,
single-node, empty) — plus the §101 cancel path.
"""
import os

import pytest

from srmech.amsc import _native
from srmech.math import laplacian


pytestmark = pytest.mark.skipif(
    not _native.has_native_recursive_cut(),
    reason="rc284 native recursive_cut not built into this lib",
)


def _pure(monkeypatch):
    """Force the pure-Python driver (the parity ORACLE) for one call."""
    monkeypatch.setattr(_native, "recursive_cut_c", lambda *a, **k: None)


def _tome_bytes(res):
    out = []
    for p in res["tome_paths"]:
        with open(p, "rb") as fh:
            out.append(fh.read())
    return out


def _run(tmp_path, tag, n, edges, weights=None, max_tome=4, max_depth=64,
         progress=None):
    wd = tmp_path / tag
    return laplacian.recursive_cut(
        n, edges, weights, max_tome=max_tome, work_dir=str(wd),
        max_depth=max_depth, progress=progress)


# ---------------------------------------------------------------------------
# the input matrix: shape x size x degeneracy
# ---------------------------------------------------------------------------

def _ring_of_cliques(n_cliques, clique):
    """Real community structure: cliques joined in a ring by ONE weak bridge."""
    edges, weights = [], []
    for c in range(n_cliques):
        base = c * clique
        for i in range(clique):
            for j in range(i + 1, clique):
                edges.append((base + i, base + j))
                weights.append(1.0)
    for c in range(n_cliques):
        a = c * clique + clique - 1
        b = ((c + 1) % n_cliques) * clique
        edges.append((a, b))
        weights.append(0.02)
    return n_cliques * clique, edges, weights


def _path_graph(n):
    return n, [(i, i + 1) for i in range(n - 1)], [1.0] * (n - 1)


def _complete(n):
    e = [(i, j) for i in range(n) for j in range(i + 1, n)]
    return n, e, [1.0] * len(e)


def _disconnected(n_comp, size):
    """No edge between components at all — the driver must not assume connected."""
    edges, weights = [], []
    for c in range(n_comp):
        base = c * size
        for i in range(size):
            for j in range(i + 1, size):
                edges.append((base + i, base + j))
                weights.append(1.0)
    return n_comp * size, edges, weights


CASES = [
    ("ring3x3", *_ring_of_cliques(3, 3)),
    ("ring4x4", *_ring_of_cliques(4, 4)),
    ("ring5x6", *_ring_of_cliques(5, 6)),
    ("path12", *_path_graph(12)),
    ("path31", *_path_graph(31)),          # odd size, no clean split
    ("complete8", *_complete(8)),          # DEGENERATE spectrum
    ("complete16", *_complete(16)),
    ("disconnected3x4", *_disconnected(3, 4)),
    ("disconnected5x2", *_disconnected(5, 2)),
    ("edgeless9", 9, [], []),              # no edges at all
    ("single", 1, [], []),                 # single node
    ("two_isolated", 2, [], []),
    ("pair", 2, [(0, 1)], [1.0]),
    ("empty", 0, [], []),                  # n == 0
]


@pytest.mark.parametrize("tag,n,edges,weights", CASES)
@pytest.mark.parametrize("max_tome", [1, 2, 4, 8])
def test_recursive_cut_is_byte_identical_across_projections(
        tmp_path, monkeypatch, tag, n, edges, weights, max_tome):
    """THE acceptance test: same bytes, same order, same status, both ways."""
    native = _run(tmp_path, f"{tag}_{max_tome}_c", n, edges, weights,
                  max_tome=max_tome)
    with monkeypatch.context() as m:
        _pure(m)
        pure = _run(tmp_path, f"{tag}_{max_tome}_py", n, edges, weights,
                    max_tome=max_tome)

    assert native["n_tomes"] == pure["n_tomes"], f"{tag}: tome COUNT differs"
    assert native["status"] == pure["status"] == "ok"
    assert [len(t) for t in native["tomes"]] == [len(t) for t in pure["tomes"]], (
        f"{tag}: tome SIZES differ")
    assert native["tomes"] == pure["tomes"], f"{tag}: tome CONTENT/ORDER differs"
    assert _tome_bytes(native) == _tome_bytes(pure), f"{tag}: tome BYTES differ"
    # the file NAMES must line up too (tome_0.bin, tome_1.bin, ... in order)
    assert ([os.path.basename(p) for p in native["tome_paths"]]
            == [os.path.basename(p) for p in pure["tome_paths"]]), (
        f"{tag}: tome FILE NAMES differ")


@pytest.mark.parametrize("tag,n,edges,weights", CASES)
def test_tomes_are_an_exact_partition(tmp_path, tag, n, edges, weights):
    """Whatever the shape: every node lands in exactly ONE tome, exactly once."""
    res = _run(tmp_path, f"{tag}_part", n, edges, weights, max_tome=3)
    seen = [x for tome in res["tomes"] for x in tome]
    assert sorted(seen) == list(range(n)), f"{tag}: not an exact partition"


@pytest.mark.parametrize("max_depth", [0, 1, 2, 3])
def test_max_depth_guard_parity(tmp_path, monkeypatch, max_depth):
    """The depth guard short-circuits the recursion — both ways identically."""
    n, edges, weights = _ring_of_cliques(4, 4)
    native = _run(tmp_path, f"d{max_depth}_c", n, edges, weights, max_tome=2,
                  max_depth=max_depth)
    with monkeypatch.context() as m:
        _pure(m)
        pure = _run(tmp_path, f"d{max_depth}_py", n, edges, weights, max_tome=2,
                    max_depth=max_depth)
    assert native["tomes"] == pure["tomes"]
    assert _tome_bytes(native) == _tome_bytes(pure)


# ---------------------------------------------------------------------------
# §101 progress / cancel
# ---------------------------------------------------------------------------

def test_progress_ticks_are_monotone_and_total_is_n(tmp_path):
    n, edges, weights = _ring_of_cliques(4, 4)
    seen = []

    def tick(ev):
        seen.append((ev["done"], ev["total"]))
        return 0

    res = _run(tmp_path, "tick", n, edges, weights, max_tome=2, progress=tick)
    assert res["status"] == "ok"
    assert seen, "progress never fired"
    assert all(t == n for _d, t in seen), "total must be n"
    dones = [d for d, _t in seen]
    assert dones == sorted(dones), "done must be monotone non-decreasing"
    assert dones[-1] == n, "the terminal heartbeat must report done == n"


@pytest.mark.parametrize("cancel_at", [1, 2, 3])
def test_cancel_yields_a_valid_coarser_partition(tmp_path, cancel_at):
    """A cancel is a CLEAN partial: coarser, but still every node exactly once."""
    n, edges, weights = _ring_of_cliques(4, 4)
    calls = {"k": 0}

    def tick(ev):
        calls["k"] += 1
        return 1 if calls["k"] >= cancel_at else 0

    res = _run(tmp_path, f"cancel{cancel_at}", n, edges, weights, max_tome=2,
               progress=tick)
    assert res["status"] == "cancelled"
    seen = [x for tome in res["tomes"] for x in tome]
    assert sorted(seen) == list(range(n)), "cancelled partition lost nodes"


@pytest.mark.parametrize("cancel_at", [1, 2, 3])
def test_cancel_is_byte_identical_across_projections(tmp_path, monkeypatch,
                                                     cancel_at):
    n, edges, weights = _ring_of_cliques(4, 4)

    def mk():
        calls = {"k": 0}

        def tick(ev):
            calls["k"] += 1
            return 1 if calls["k"] >= cancel_at else 0
        return tick

    native = _run(tmp_path, f"cx{cancel_at}_c", n, edges, weights, max_tome=2,
                  progress=mk())
    with monkeypatch.context() as m:
        _pure(m)
        pure = _run(tmp_path, f"cx{cancel_at}_py", n, edges, weights,
                    max_tome=2, progress=mk())
    assert native["status"] == pure["status"] == "cancelled"
    assert native["tomes"] == pure["tomes"], "cancelled tomes differ"
    assert _tome_bytes(native) == _tome_bytes(pure), "cancelled tome BYTES differ"


def test_progress_exception_propagates_and_does_not_cross_c_frames(tmp_path):
    n, edges, weights = _ring_of_cliques(3, 3)

    def boom(ev):
        raise RuntimeError("tick blew up")

    with pytest.raises(RuntimeError, match="tick blew up"):
        _run(tmp_path, "boom", n, edges, weights, max_tome=2, progress=boom)


def test_work_dir_is_reusable(tmp_path):
    """An existing work_dir is REUSED, not rejected (mkdir is idempotent)."""
    n, edges, weights = _ring_of_cliques(3, 3)
    wd = tmp_path / "reused"
    first = laplacian.recursive_cut(n, edges, weights, max_tome=3,
                                    work_dir=str(wd))
    second = laplacian.recursive_cut(n, edges, weights, max_tome=3,
                                     work_dir=str(wd))
    assert first["tomes"] == second["tomes"]
