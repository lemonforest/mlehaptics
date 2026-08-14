"""v0.9.0rc334 (§102 / F1252 — INCREMENTAL STAGE 1+2, task #887) — the LAST genome
wire-glue parity gap closed: ``plasmid.add_plasmid`` earns its whole-op C peer
``srmech_genome_add_plasmid`` and ``CEIL_WIRE_GLUE_GAPS`` drops **1 → 0**.

``add_plasmid`` is a stateful, disk-backed incremental orchestrator — the hardest of
the §2-G7 family. The Python projection owns the stage-1 APPEND
(``srmech_genome_plasmid_extract``, which seeds a fresh store + refreshes the
``__vocab__`` karyotype index); this peer runs the CONSERVE (merge the section-count
accumulator + ``srmech_genome_conserved_core``) + ORGANIZE (page every section off
disk, decode + harvest the induced core subgraph, sum the per-``(u,v)`` multiplicities
in canonical order, pack it, then MINT the core + FOLD the retained plasmids) half
END-TO-END in C.

Proven here — the NATIVE ``add_plasmid`` is BYTE-IDENTICAL to the FORCED-PURE
``add_plasmid`` (the pure body is the byte-parity oracle), for the whole ``strand``
AND the full ``state`` (the ``section_count`` map, ``vocab``, ``labels``, ``core``,
``k``, and the ``sections`` edge cache), across:
  * a single document (the seed section);
  * a multi-document INCREMENTAL sequence (state threaded call to call);
  * the CORE-CHANGED step (the antimode first promotes a core) AND the CORE-UNCHANGED
    steps after it (the core is byte-untouched);
  * ``cache_edges`` ON and OFF;
  * an EMPTY-tokens document (a zero-node section).
Plus the rc279 EQUIVALENCE contract on the native path (``add_plasmid`` D times ==
one ``genome_integrate_plasmids`` over the same D sections), the state marshalling
(the peer's returned counts/core/k == the pure ``conserved_core``), and the ratchet
closure (the peer is declared in the header AND actually dispatched;
``CEIL_WIRE_GLUE_GAPS == 0`` and ``_KNOWN_GLUE_GAPS`` is EMPTY).

numpy-free (no ``import numpy`` here — the whole file runs in a numpy-absent venv);
integer/exact (Class-N); no ``abs()``.
"""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

import pytest

from srmech import _native
from srmech.biology import plasmid as P
from srmech.math.hdc import klein4_expand

_DIM = 64                                           # >= 52 (the §89 kernel header)
_CORE = ["alpha", "beta", "gamma", "delta"]         # the PLANTED conserved core


def _one(seed=1334):
    return klein4_expand(_DIM, seed)


def _tmp():
    return tempfile.mkdtemp(prefix="srmech_addplasmid_")


def _planted_every_doc(n_docs=8):
    """The core words appear in EVERY document (count == n_docs); every periphery word
    in exactly ONE. Once there are >= 2 docs the histogram is occupied at {1, n_docs}
    with a wide empty valley, so the antimode splits at k == 2 and recovers ``_CORE``.
    Running this incrementally exercises BOTH the core-changed step (doc 2 first
    promotes the core) and the core-unchanged steps after it."""
    return [list(_CORE) + [f"w{i}a", f"w{i}b", f"w{i}c"] for i in range(n_docs)]


def _blocks(strand):
    return [bytes(h) for h in strand]


def _state_view(st):
    """A byte-comparable projection of the running organize state."""
    return {
        "section_count": dict(st["section_count"]),
        "vocab": list(st["vocab"]),
        "labels": list(st["labels"]),
        "core": list(st["core"]),
        "k": st["k"],
        "sections": [[tuple(int(x) for x in e) for e in sec]
                     for sec in st["sections"]],
    }


def _result_view(res):
    """The result dict minus the strand/state (compared separately) — every scalar
    the two paths must agree on."""
    return {kk: res[kk] for kk in ("section", "k", "k_source", "core_changed",
                                   "core", "bimodal", "one_dna_type", "counts",
                                   "n_sections", "n_integrated", "status")}


def _run_sequence(docs, one, *, native, cache_edges, monkeypatch):
    """Run ``add_plasmid`` over ``docs`` threading state, in its own fresh store, with
    the native peer forced ON or OFF. Returns the per-step result list."""
    store = _tmp()
    if not native:
        monkeypatch.setattr(_native, "HAS_NATIVE", False)
    try:
        state, steps = None, []
        for doc in docs:
            res = P.add_plasmid(store, one, doc, state=state, cache_edges=cache_edges)
            state = res["state"]
            steps.append(res)
    finally:
        if not native:
            monkeypatch.setattr(_native, "HAS_NATIVE", True)
    return steps


def _assert_native_equals_pure(docs, one, monkeypatch, *, cache_edges=True):
    """The core assertion: the NATIVE add_plasmid sequence is byte-identical to the
    FORCED-PURE sequence, step for step — strand blocks, full state, result scalars."""
    assert _native.has_native_genome_add_plasmid(), "rc334 C peer not bound"
    native = _run_sequence(docs, one, native=True, cache_edges=cache_edges,
                           monkeypatch=monkeypatch)
    pure = _run_sequence(docs, one, native=False, cache_edges=cache_edges,
                         monkeypatch=monkeypatch)
    assert len(native) == len(pure) == len(docs)
    for i, (n, p) in enumerate(zip(native, pure)):
        assert _blocks(n["strand"]) == _blocks(p["strand"]), (
            f"step {i}: native strand != pure strand")
        assert _state_view(n["state"]) == _state_view(p["state"]), (
            f"step {i}: native state != pure state")
        assert _result_view(n) == _result_view(p), (
            f"step {i}: native result != pure result")
    return native, pure


# ── native == forced-pure, byte-identical, across every case ────────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_single_document_seed(monkeypatch):
    """One document — the seed section. A single-count histogram has no antimode, so
    the organize is ALL-PLASMID (no core promoted)."""
    one = _one()
    native, _ = _assert_native_equals_pure([list(_CORE) + ["x", "y"]], one, monkeypatch)
    assert native[0]["core"] == [] and native[0]["one_dna_type"] is True


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_multi_document_incremental(monkeypatch):
    """A threaded incremental sequence — state fed back call to call."""
    native, _ = _assert_native_equals_pure(_planted_every_doc(8), _one(), monkeypatch)
    assert native[-1]["n_sections"] == 8


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_core_changed_then_core_unchanged(monkeypatch):
    """The antimode PROMOTES a core once its valley opens (``core_changed`` True on the
    step the core first differs), then the core stays byte-untouched on later docs
    (``core_changed`` False) — and native tracks pure through both transitions."""
    native, _ = _assert_native_equals_pure(_planted_every_doc(6), _one(), monkeypatch)
    prev = []
    for s in native:                                # core_changed <=> core moved
        assert s["core_changed"] == (s["core"] != prev)
        prev = s["core"]
    promoted = [i for i, s in enumerate(native) if s["core_changed"] and s["core"]]
    assert promoted, "the planted valley must promote a core at some step"
    # once promoted the core is STABLE (byte-untouched) for the rest of the run
    assert all(s["core_changed"] is False for s in native[promoted[0] + 1:])
    assert native[-1]["core"] and native[-1]["counts"]["nuclear"] == len(_CORE)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_cache_edges_off(monkeypatch):
    """``cache_edges=False`` (the store-re-read path) is byte-identical native vs pure —
    and the resulting state's empty edge cache matches too."""
    native, _ = _assert_native_equals_pure(_planted_every_doc(6), _one(), monkeypatch,
                                           cache_edges=False)
    assert native[-1]["state"]["sections"] == []    # nothing cached


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_empty_tokens_document(monkeypatch):
    """An EMPTY document — a zero-node plasmid section — folds in native == pure."""
    docs = [list(_CORE) + ["p", "q"], [], list(_CORE) + ["r", "s"]]
    _assert_native_equals_pure(docs, _one(), monkeypatch)


# ── the rc279 equivalence contract, on the NATIVE path ──────────────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_native_incremental_equals_one_batch_integrate(monkeypatch):
    """D native ``add_plasmid`` calls == ONE ``genome_integrate_plasmids`` over the
    same D sections, byte-for-byte (the exact incremental rule, natively)."""
    one = _one()
    docs = _planted_every_doc(8)
    native = _run_sequence(docs, one, native=True, cache_edges=True,
                           monkeypatch=monkeypatch)
    batch_store = _tmp()
    ext = P.plasmid_extract(docs, batch_store, one)
    batch = P.genome_integrate_plasmids(batch_store, one,
                                        section_count=ext["section_count"])
    assert _blocks(native[-1]["strand"]) == _blocks(batch["strand"]), (
        "native incremental organize must equal the from-scratch organize byte for byte")
    assert native[-1]["k"] == batch["k"] and native[-1]["core"] == batch["core"]


# ── state marshalling: the peer's returned {counts, core, k} == pure conserved_core ─

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_peer_state_marshalling_matches_conserved_core(monkeypatch):
    """The counts/core/k the C peer marshals OUT are byte-identical to the pure
    ``conserved_core`` over the pure-bumped accumulator — the state round-trip is a
    real marshalling test, not a Python re-derivation."""
    one = _one()
    docs = _planted_every_doc(6)
    native = _run_sequence(docs, one, native=True, cache_edges=True,
                           monkeypatch=monkeypatch)
    # rebuild the pure accumulator + conserved_core independently and compare.
    pure = _run_sequence(docs, one, native=False, cache_edges=True,
                         monkeypatch=monkeypatch)
    for n, p in zip(native, pure):
        split = P.conserved_core(p["state"]["section_count"])
        assert n["state"]["section_count"] == p["state"]["section_count"]
        assert n["core"] == split["core"] == p["core"]
        assert n["k"] == split["k"] and n["bimodal"] == split["bimodal"]


# ── the ratchet closure: declared-and-dispatched, CEIL 0, empty gap list ────────

def _load_rosetta():
    path = Path(__file__).with_name("test_rosetta_transitive_standalone.py")
    spec = importlib.util.spec_from_file_location("_rosetta_rc334", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ratchet_add_plasmid_declared_and_gap_list_empty():
    """add_plasmid moved ``_KNOWN_GLUE_GAPS -> _WHOLE_OP_C_PEER``; the map names the
    right symbol, the header declares it, and the DOWN-ONLY ceiling is now 0 with an
    EMPTY gap list — the enumerated genome wire-glue surface is fully C-reachable."""
    r = _load_rosetta()
    assert (r._WHOLE_OP_C_PEER["srmech.biology.plasmid.add_plasmid"]
            == "srmech_genome_add_plasmid")
    assert "srmech.biology.plasmid.add_plasmid" not in r._KNOWN_GLUE_GAPS
    assert set(r._KNOWN_GLUE_GAPS) == set()
    assert len(r._KNOWN_GLUE_GAPS) == r.CEIL_WIRE_GLUE_GAPS == 0
    header = (Path(__file__).resolve().parents[2] / "c" / "include" / "srmech.h"
              ).read_text(encoding="utf-8", errors="replace")
    assert "srmech_genome_add_plasmid(" in header, "peer not declared in the header"


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_peer_is_actually_dispatched():
    """A declaration is not a dispatch — the native peer is bound AND add_plasmid's
    source reaches the ``genome_add_plasmid_c`` dispatcher (the flip is only visible
    native-present)."""
    import ast
    import inspect
    import textwrap
    assert _native.has_native_genome_add_plasmid(), "rc334 peer not bound"
    src = textwrap.dedent(inspect.getsource(P.add_plasmid))
    names = {n.attr for n in ast.walk(ast.parse(src))
             if isinstance(n, ast.Attribute)}
    assert "genome_add_plasmid_c" in names, (
        "add_plasmid does not dispatch to _native.genome_add_plasmid_c")
