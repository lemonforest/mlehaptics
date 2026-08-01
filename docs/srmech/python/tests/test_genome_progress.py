"""v0.9.0rc275 (§101 / PR#687 / F1252) — ENCODE PROGRESS + GRACEFUL ABORT.

The long srmech encode ops gain an INLINE caller ``progress(ev) -> bool`` heartbeat
with a nonzero-return-to-CANCEL channel (the libcurl XFERINFOFUNCTION / SQLite
progress_handler pattern). These tests prove the §7 shapes of the prototype:

  1. progress is MONOTONE and REACHES 100% (recursive_cut done -> n).
  2. CANCEL at X% aborts + returns the derived CLEAN partial / honest-decline for
     every op (recursive_cut / genome_partition / genome_from_graph / mint /
     mint_strand / fiedler_sparse_file), and genome_from_graph does NOT save on
     cancel.
  3. C<->Python parity: the native (trampoline) and pure paths emit the SAME
     (phase, done, total) event sequence (mint full-sequence + fiedler prefix).
  4. The native-absent / forced-pure path honours the identical contract.
  5. done/total are EXACT ints (Class-N) — never a float, never abs().
  6. The trampoline swallows a Python exception raised inside the callback and
     re-raises it (never crosses the C frames).
  7. The Callable-not-a-wire-param guard: ``progress`` is in NO ToolEntry.parameters.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import os
import tempfile

import pytest

from srmech.biology import genome as G
from srmech.math import laplacian as L
from srmech.amsc import _native
from srmech.math.hdc import klein4_expand

_DIM = 64
_PARTITIONING = _native.SRMECH_PHASE_PARTITIONING
_MINTING = _native.SRMECH_PHASE_MINTING
_STRUCT = _native.PROGRESS_STRUCT_SIZE


def _one(seed=1275):
    return klein4_expand(_DIM, seed)


def _lv(n, base=0):
    return [klein4_expand(_DIM, base + s) for s in range(n)]


class _Recorder:
    """Collect (phase, done, total) events; optionally cancel at a predicate.

    Also proves the events are well-formed ints and that NO event fires after a
    cancel has been issued (a second call after cancel sets ``.after_cancel``)."""

    def __init__(self, cancel=None):
        self.events = []
        self._cancel = cancel
        self.cancelled = False
        self.after_cancel = False

    def __call__(self, ev):
        if self.cancelled:
            self.after_cancel = True
        # every field is an EXACT int (Class-N; no float, no abs)
        assert isinstance(ev["struct_size"], int) and ev["struct_size"] == _STRUCT
        assert isinstance(ev["phase"], int)
        assert isinstance(ev["done"], int) and ev["done"] >= 0
        assert isinstance(ev["total"], int) and ev["total"] >= 0
        assert not isinstance(ev["done"], bool)
        self.events.append((ev["phase"], ev["done"], ev["total"]))
        if self._cancel is not None and self._cancel(ev):
            self.cancelled = True
            return True
        return False


def _two_cliques(k=8):
    """Two k-cliques joined by one weak bridge — forces >= 2 tomes at max_tome=k."""
    def clique(off):
        return [(off + a, off + b) for a in range(k) for b in range(a + 1, k)]
    edges = clique(0) + clique(k) + [(0, k)]
    weights = [1.0] * (len(edges) - 1) + [0.01]
    return 2 * k, edges, weights


def _bimodal_graph():
    """Two 10-cliques + 2 bridge nodes — an asymmetric nuclear/plasmid split
    (mirrors test_genome_partition_rc272), so genome_partition yields >= 2 groups."""
    def clique(nodes):
        e, w, c = [], [], []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                e.append((nodes[i], nodes[j])); w.append(1); c.append(1)
        return e, w, c
    A, B, bridges = list(range(10)), list(range(10, 20)), [20, 21]
    e, w, c = clique(A)
    e2, w2, c2 = clique(B)
    edges, weights, charges = e + e2, w + w2, c + c2
    for b in bridges:
        for t in (A[0], A[1], B[0], B[1]):
            edges.append((b, t)); weights.append(1); charges.append(-1)
    edges.append((20, 21)); weights.append(1); charges.append(1)
    return 22, edges, weights, charges


# ── 1. MONOTONE + REACHES 100% (recursive_cut) ───────────────────────────────

def test_recursive_cut_progress_monotone_and_reaches_100():
    n, edges, w = _two_cliques(8)
    rec = _Recorder()
    r = L.recursive_cut(n, edges, w, max_tome=8,
                        work_dir=tempfile.mkdtemp(), progress=rec)
    assert r["status"] == "ok"
    assert rec.events, "at least one progress event must fire"
    # every event is the PARTITIONING phase over the exact node total
    assert all(ph == _PARTITIONING and tot == n for ph, _d, tot in rec.events)
    dones = [d for _p, d, _t in rec.events]
    assert dones == sorted(dones), "done must be monotone non-decreasing"
    assert dones[-1] == n, "the terminal event reaches done == total (100%)"


# ── 2. CANCEL → CLEAN PARTIAL, per op ─────────────────────────────────────────

def test_recursive_cut_cancel_returns_clean_partition():
    n, edges, w = _two_cliques(8)
    rec = _Recorder(cancel=lambda ev: ev["done"] >= 1)   # after the 1st tome resolves
    r = L.recursive_cut(n, edges, w, max_tome=8,
                        work_dir=tempfile.mkdtemp(), progress=rec)
    assert r["status"] == "cancelled"
    assert not rec.after_cancel, "no event fires after a cancel"
    # the finalized + promoted-pending tomes still partition ALL n nodes
    flat = sorted(x for t in r["tomes"] for x in t)
    assert flat == list(range(n))


def test_genome_partition_cancel_returns_clean_partial():
    n, edges, weights, charges = _bimodal_graph()
    rec = _Recorder(cancel=lambda ev: True)              # cancel on the first event
    p = G.genome_partition(n, edges, weights, charges,
                           work_dir=tempfile.mkdtemp(), max_tome=12, progress=rec)
    assert p["status"] == "cancelled"
    assert p["groups"] == []                             # the pure read was not run
    assert p["counts"] == {"nuclear": 0, "plasmid": 0}
    assert p["node_counts"] == {"nuclear": 0, "plasmid": 0}


def test_genome_from_graph_cancel_in_partition_no_save():
    n, edges, weights, charges = _bimodal_graph()
    one = _one()
    d = tempfile.mkdtemp()
    path = os.path.join(d, "geno")
    rec = _Recorder(cancel=lambda ev: True)              # cancel during partitioning
    res = G.genome_from_graph(n, edges, weights, charges, coupling=one,
                              path=path, leaf_dim=_DIM, max_tome=12, progress=rec)
    assert res["status"] == "cancelled"
    assert res["strand"] == []
    assert "path" not in res and "census" not in res
    assert not os.path.exists(os.path.join(path, "manifest.json")), "no save on cancel"


def test_genome_from_graph_cancel_in_mint_partial_no_save():
    n, edges, weights, charges = _bimodal_graph()
    one = _one()
    d = tempfile.mkdtemp()
    path = os.path.join(d, "geno")
    # let PARTITIONING through; cancel on the 2nd MINTING event (1 chromosome minted)
    rec = _Recorder(cancel=lambda ev: ev["phase"] == _MINTING and ev["done"] >= 1)
    res = G.genome_from_graph(n, edges, weights, charges, coupling=one,
                              path=path, leaf_dim=_DIM, max_tome=12, progress=rec)
    assert res["status"] == "cancelled"
    assert len(res["chromosomes"]) >= 1                  # a valid shorter genome
    assert res["strand"], "the partial strand carries the minted chromosome(s)"
    assert "path" not in res and "census" not in res
    assert not os.path.exists(os.path.join(path, "manifest.json")), "no save on cancel"
    # the MINTING phase fired after the PARTITIONING phase
    phases = [ph for ph, _d, _t in rec.events]
    assert _MINTING in phases and _PARTITIONING in phases


def test_mint_cancel_returns_valid_partial_strand():
    one = _one()
    kernels = {"k0": _lv(3, 0), "k1": _lv(3, 10), "k2": _lv(3, 20), "k3": _lv(3, 30)}
    full = G.mint(kernels, one)
    rec = _Recorder(cancel=lambda ev: ev["done"] >= 2)   # after 2 chromosomes
    partial = G.mint(kernels, one, progress=rec)
    assert 0 < len(partial) < len(full), "a strict, non-empty partial"
    # the partial is a byte-PREFIX of the full strand (chromosomes minted in order)
    assert ([list(x) for x in partial]
            == [list(x) for x in full[:len(partial)]])


def test_mint_strand_cancel_returns_unmodified_strand():
    one = _one()
    strand = G.chromosome(_lv(6, 200), one, label="x")   # an already-packed strand
    before = [list(x) for x in strand]
    rec = _Recorder(cancel=lambda ev: True)              # decline the single pre-op gate
    out = G.mint_strand(strand, one, progress=rec)
    assert [list(x) for x in out] == before, "the strand is UNMODIFIED on decline"
    assert not any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in out)


# ── 3 + 4. C<->Python PARITY + forced-pure honour the same contract ───────────

def test_mint_native_vs_pure_same_event_sequence(monkeypatch):
    one = _one()
    kernels = {"k0": _lv(3, 0), "k1": _lv(6, 10), "k2": _lv(3, 20)}
    rec_a = _Recorder()
    G.mint(kernels, one, progress=rec_a)                 # native if HAS_NATIVE, else pure
    rec_b = _Recorder()
    monkeypatch.setattr(_native, "has_native_genome_mint", lambda: False)   # force pure
    G.mint(kernels, one, progress=rec_b)
    assert rec_a.events == rec_b.events, "native and pure emit the SAME sequence"
    assert rec_b.events == [(_MINTING, i, len(kernels)) for i in range(len(kernels))]


def test_fiedler_native_vs_pure_same_cancel_sequence(monkeypatch):
    n = 4
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]             # a 4-cycle
    d = tempfile.mkdtemp()
    path = os.path.join(d, "graph.bin")
    L.write_packed_graph(path, edges, [1.0] * len(edges))
    cancel3 = lambda ev: ev["done"] >= 3

    rec_a = _Recorder(cancel=cancel3)                    # native path if available
    va = L.fiedler_sparse_file(n, path, progress=rec_a)
    rec_b = _Recorder(cancel=cancel3)
    monkeypatch.setattr(_native, "has_native_fiedler_sparse_file_progress",
                        lambda: False)                   # force the pure power loop
    vb = L.fiedler_sparse_file(n, path, progress=rec_b)

    assert rec_a.events == rec_b.events == [
        (_PARTITIONING, 1, 250), (_PARTITIONING, 2, 250), (_PARTITIONING, 3, 250)]
    # cancel leaves the zeroed "no cut" vector on BOTH paths (byte-parity)
    assert list(va) == [0.0] * n
    assert list(vb) == [0.0] * n


# ── 6. TRAMPOLINE swallows a Python exception cleanly (re-raised) ─────────────

def test_progress_exception_is_reraised_not_swallowed():
    one = _one()
    kernels = {"k0": _lv(3, 0), "k1": _lv(3, 10)}
    boom = RuntimeError("callback exploded")

    def raiser(_ev):
        raise boom

    with pytest.raises(RuntimeError, match="callback exploded"):
        G.mint(kernels, one, progress=raiser)


@pytest.mark.skipif(not _native.has_native_genome_mint_progress(),
                    reason="native mint-progress overload not built")
def test_native_trampoline_exception_does_not_crash_and_reraises():
    """Native-path-specific: the exception is stashed inside the trampoline (never
    crosses the C frames) and re-raised by genome_mint_c after the C call returns."""
    one = _one()
    kernels = {"k0": _lv(3, 0), "k1": _lv(3, 10), "k2": _lv(3, 20)}

    def raiser(_ev):
        raise ValueError("native boundary")

    with pytest.raises(ValueError, match="native boundary"):
        G.mint(kernels, one, progress=raiser)
    # the library is still usable afterward (no corrupted state / no crash)
    assert len(G.mint(kernels, one)) > 0


# ── 7. Callable-not-a-wire-param guard ────────────────────────────────────────

def test_progress_is_never_a_tool_wire_param():
    from srmech.amsc.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    for t in get_tool_schema().tools:
        names = [p.name for p in (t.parameters or ())]
        assert "progress" not in names, f"{t.name} must not expose progress as a wire param"
