"""rc230 — resonant_spectrum_sparse: the F172 storage signature at UNBOUNDED n.

The multiset-agreement PROOF (issue #698). ``resonant_spectrum`` reads the
storage signature (eigen-tensions + the Class-N/J resonance lock/libration
verdict) only through the DENSE Class-L eigensolve (native-capped at
MAX_NATIVE_NODES = 256; O(n²) RAM, O(n³) eig). ``resonant_spectrum_sparse`` reads
the SAME signature restricted to the k EXTREME modes via streaming power
iteration + Gram-Schmidt deflation on the packed edge stream (RAM O(k·n), time
O(k·|E|·iters), n unbounded).

The genuine (no-shell) proof:

1. **Multiset agreement (n ≤ 256).** On graphs whose extreme modes are SEPARATED
   from the bulk, the k extreme tensions from ``resonant_spectrum_sparse`` MATCH
   the k extreme tensions of the dense ``resonant_spectrum`` (within eig-tol) AND
   the Class-N/J lock/libration verdicts + exact ``best_rational`` ratios are
   IDENTICAL (they call the SAME ``_resonances_from_tensions`` helper).
2. **native == pure.** The C peer ``srmech_laplacian_k_extreme_modes_file`` and
   the pure-Python streaming read agree within float tolerance (same iteration,
   same arithmetic order).
3. **n > 256 (past the dense native-eig wall).** The op RUNS at n > 256 (where
   the dense native eigensolve caps), native == pure, and the well-separated
   top-k tensions match the dense reference.

Honest envelope (documented on the op): near-degenerate boundary clusters (a
dense low-frequency bulk) converge slowly — the genuine limitation of ANY
iterative extreme-eigenvalue read vs. a full dense eigensolve. These proof
graphs use SEPARATED extreme modes (the regime a k-extreme read is for).

numpy-free (imports only srmech + stdlib), per the numpy-absent CI cell.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from srmech import introspect
from srmech.biology import coupling as C
from srmech.math import laplacian as L
from srmech import _native
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

warmup_all()

_EIG_TOL = 1e-5


def _tensions(d) -> list:
    t = d["tensions"]
    return [float(t[i]) for i in range(t.shape[0])]


def _dense_extreme(n, edges, weights, k):
    """The dense reference: full eigensolve, then the INDEX-based extreme
    selection (first k ∪ last k of the ascending spectrum)."""
    Lm = L.dense_laplacian(n, edges, weights)
    dn = C.resonant_spectrum(Lm)
    full = sorted(float(dn["tensions"][i]) for i in range(dn["tensions"].shape[0]))
    idx = sorted(set(range(min(k, n))) | set(range(max(0, n - k), n)))
    return [full[i] for i in idx]


def _close(a, b, tol=_EIG_TOL):
    return len(a) == len(b) and all(
        (x - y if x >= y else y - x) <= tol * (1.0 + (y if y >= 0 else -y))
        for x, y in zip(a, b))


# ── well-separated proof graphs (n ≤ 256) ──────────────────────────────────


def _from_bodies_graph():
    # F928 Jupiter+Galilean prototype — a small, well-separated coupling graph.
    return C.from_bodies([1000.0, 1.0, 2.0, 1.5, 2.5], [0.0, 4.0, 6.0, 9.0, 13.0])


def _weighted_path(n):
    edges = [(i, i + 1) for i in range(n - 1)]
    weights = [1.0 + 0.3 * i for i in range(n - 1)]
    return n, edges, weights


def _well_separated_random(n, p, seed):
    rng = random.Random(seed)
    edges, weights = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                edges.append((i, j))
                weights.append(round(rng.uniform(0.5, 3.0), 3))
    return n, edges, weights


# The proof graphs — extreme modes SEPARATED from the bulk (the regime a
# k-extreme read is for): gravity coupling (from_bodies; a heavy central body
# gives well-separated tensions) + moderate random graphs. (A path/ring, whose
# low-frequency modes densely CLUSTER near 0, is deliberately NOT used — those
# clustered modes converge slowly, the honest limitation documented on the op.)
_SMALL_GRAPHS = [
    ("bodies5", C.from_bodies([1000., 1., 2., 1.5, 2.5], [0, 4, 6, 9, 13]), 3),
    ("bodies6", C.from_bodies([500., 3., 1., 4., 2., 5.], [0, 3, 7, 11, 16, 22]), 3),
    ("rand40", _well_separated_random(40, 0.2, 3), 4),
    ("rand60", _well_separated_random(60, 0.25, 17), 3),
]


def test_multiset_agreement_small_graphs():
    """The k extreme tensions match dense within eig-tol on n ≤ 256 graphs."""
    for name, (n, e, w), k in _SMALL_GRAPHS:
        sp = C.resonant_spectrum_sparse(e, w, k=k, n=n)
        st = _tensions(sp)
        ref = _dense_extreme(n, e, w, k)
        assert _close(st, ref), (
            f"[{name}] sparse extreme tensions {[round(x, 6) for x in st]} != "
            f"dense {[round(x, 6) for x in ref]}")


def test_lock_libration_verdicts_identical():
    """The Class-N/J lock/libration verdicts + exact best_rational ratios are
    IDENTICAL to the dense read restricted to the same extreme tensions (both
    call _resonances_from_tensions)."""
    for name, (n, e, w), k in _SMALL_GRAPHS:
        sp = C.resonant_spectrum_sparse(e, w, k=k, n=n)
        ref = _dense_extreme(n, e, w, k)
        ref_res = C._resonances_from_tensions(ref, 64)
        s_locks = [r["locked"] for r in sp["resonances"]]
        d_locks = [r["locked"] for r in ref_res]
        s_ratios = [r["ratio"] for r in sp["resonances"]]
        d_ratios = [r["ratio"] for r in ref_res]
        assert s_locks == d_locks, f"[{name}] locks {s_locks} != {d_locks}"
        assert s_ratios == d_ratios, f"[{name}] ratios {s_ratios} != {d_ratios}"


def test_native_equals_pure_small():
    """The native C peer and the pure-Python streaming read agree within float
    tolerance (differential parity)."""
    for name, (n, e, w), k in _SMALL_GRAPHS:
        native = C.resonant_spectrum_sparse(e, w, k=k, n=n)
        pure_pairs = sorted(C._kext_modes_py(n, e, w, k, 1000), key=lambda p: p[0])
        st = _tensions(native)
        pt = [p[0] for p in pure_pairs]
        assert _close(st, pt), (
            f"[{name}] native {[round(x, 6) for x in st]} != pure "
            f"{[round(x, 6) for x in pt]}")


def test_path_input_streams_from_file(tmp_path):
    """A packed-file path input streams (edges never resident) and yields the
    identical signature to the in-RAM edge-list input."""
    n, e, w = _weighted_path(20)
    graph = str(tmp_path / "g.bin")
    L.write_packed_graph(graph, e, w)
    from_edges = _tensions(C.resonant_spectrum_sparse(e, w, k=4, n=n))
    from_path = _tensions(C.resonant_spectrum_sparse(graph, k=4, n=n))
    assert _close(from_edges, from_path)
    # n inferred from the file when omitted.
    from_path_infer = _tensions(C.resonant_spectrum_sparse(graph, k=4))
    assert _close(from_edges, from_path_infer)


def test_full_spectrum_when_2k_ge_n():
    """When 2k ≥ n the extreme union is the FULL spectrum (bottom/top deflate so
    they never collide) — every dense tension is recovered."""
    n, e, w = _from_bodies_graph()  # n = 5
    sp = C.resonant_spectrum_sparse(e, w, k=5, n=n)   # 2k = 10 ≥ 5
    st = _tensions(sp)
    Lm = L.dense_laplacian(n, e, w)
    full = sorted(float(x) for x in
                  (C.resonant_spectrum(Lm)["tensions"][i] for i in range(n)))
    assert sp["n_modes"] == n
    assert _close(st, full)


def test_dict_shape_and_structure():
    """The returned dict has the resonant_spectrum shape restricted to k extreme
    modes (tensions ascending Vec, modes n×m Mat columns, resonances list)."""
    n, e, w = _weighted_path(24)
    k = 4
    sp = C.resonant_spectrum_sparse(e, w, k=k, n=n)
    assert set(sp) >= {"tensions", "modes", "resonances", "k", "n", "n_modes"}
    assert sp["k"] == k and sp["n"] == n
    st = _tensions(sp)
    assert st == sorted(st)                       # ascending
    assert sp["n_modes"] == len(st) == min(2 * k, n)
    assert sp["modes"].shape == (n, sp["n_modes"])  # columns = eigenvectors
    assert "force_orders" not in sp                # not materialisable at large n
    assert isinstance(sp["resonances"], list)
    for r in sp["resonances"]:
        assert set(r) == {"pair", "ratio", "den_coords", "locked"}


# ── n > 256: runs past the dense native-eig wall ────────────────────────────


def _heavy_edge_graph_300():
    """n = 300 with a clear top spectral gap: a base ring (w=1) + 8 well-
    separated heavy edges → the top-8 tensions are dominated by the heavy edges
    (well-separated), the bottom is a near-degenerate ring cluster."""
    n = 300
    e, w = [], []
    for i in range(n):
        e.append((i, (i + 1) % n))
        w.append(1.0)
    for i in range(8):
        e.append((3 * i, 3 * i + 1))
        w.append(40.0 + 7.0 * i)
    return n, e, w


def test_runs_and_matches_past_256():
    """n = 300 (past the n ≤ 256 dense native-eig wall): the op RUNS, native ==
    pure, and the well-separated top-k tensions match the dense reference."""
    n, e, w = _heavy_edge_graph_300()
    k = 8
    sp = C.resonant_spectrum_sparse(e, w, k=k, n=n)
    st = _tensions(sp)
    assert sp["n_modes"] == 2 * k
    assert st == sorted(st)
    assert min(st) < 1.0                           # the trivial bottom mode ~ 0

    # native == pure (differential).
    pure = sorted(p[0] for p in C._kext_modes_py(n, e, w, k, 1000))
    assert _close(st, pure, tol=1e-4)

    # the well-separated TOP-k match the dense reference (the extreme modes a
    # k-extreme read targets); dense still runs at n=300 (its native eig caps at
    # 256 → pure Jacobi O(n³) here, infeasible at truly large n while this op
    # stays O(k·|E|)).
    ref = _dense_extreme(n, e, w, k)
    top_s = sorted(st)[-k:]
    top_d = ref[-k:]
    assert _close(top_s, top_d, tol=1e-6), (
        f"top-k sparse {[round(x, 4) for x in top_s]} != dense "
        f"{[round(x, 4) for x in top_d]}")


# ── registration ───────────────────────────────────────────────────────────


def test_registration():
    assert "resonant_spectrum_sparse" in C.__all__
    assert introspect.describe()["tools"]["total"] == 605
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.biology.coupling.resonant_spectrum_sparse" in names
    entry = next(t for t in get_tool_schema().tools
                 if t.name == "srmech.biology.coupling.resonant_spectrum_sparse")
    assert entry.category == "coupling"
    assert "#698" in entry.summary
    # the Rosetta ledger row (c_dispatched — routes to the C peer).
    ndjson = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(line) for line in
            ndjson.read_text(encoding="utf-8").splitlines() if line.strip()]
    mine = [r for r in rows
            if r["exposed_as"] == "srmech.biology.coupling.resonant_spectrum_sparse"]
    assert len(mine) == 1 and mine[0]["bucket"] == "c_dispatched"


def test_native_peer_bound_when_native():
    """When HAS_NATIVE, the k-extreme C peer is loaded + bound (the standalone-C
    streaming read); else the pure path is the complete alternative."""
    if _native.HAS_NATIVE:
        # rc230+ lib exposes the symbol; a stale lib does not (pure path used).
        assert (_native.has_native_k_extreme_modes()
                or not hasattr(_native.LIB, "srmech_laplacian_k_extreme_modes_file"))
