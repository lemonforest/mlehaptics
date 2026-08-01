"""v0.9.0rc278 (§102 / F1252 STAGE 1 — EXTRACT) — the plasmid-native sectional store.

Stage 1 of the two-stage genome encode (design:
``docs/srmech/notes/f1252_two_stage_encode_design.md``). Each ingest DOCUMENT becomes
ONE Tier-1 plasmid chromosome — its LOCAL window co-occurrence graph, encoded to a §89
KERNEL chromosome (GLOBAL node-ids) and APPENDED (§v12 O(1)) to a ``sections/`` genome
store. This RETIRES the loose 916 MB ``simplewiki_directed_sparse_kernel.json`` at the
graph-L layer (route each doc's co-occurrence through ``genome_append`` instead of one
monolithic JSON).

Proven here:
  * per-doc append produces ONE plasmid chromosome; the store round-trips (census sees P
    plasmid sections + the shared VOCAB chromosome);
  * ``section_count`` accumulates correctly (per distinct section a GLOBAL node appears in)
    and is SSoT-derivable (:func:`section_counts`) from the sections' node_ids;
  * C↔Python BYTE-PARITY of the extracted sections — the native ``srmech_genome_plasmid_extract``
    orchestrator's ``turns.bin`` == the pure ``_graph_kernel_encode`` + ``genome_append_kernel``
    ``turns.bin``, byte-for-byte;
  * §101 progress/cancel truncates at a whole-SECTION (chromosome) boundary — a partial
    section is never left;
  * RETIREMENT EQUIVALENCE: each stored section decodes back to the SAME co-occurrence graph
    the old JSON path (``cooccurrence_topk``) produced — genome-native, lossless.

numpy-free (no ``import numpy`` here — the whole file runs in this numpy-absent venv);
integer/exact (Class-N); no ``abs()``.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.biology import genome as G
from srmech.biology import plasmid as P
from srmech.math.hdc import klein4_expand
from srmech.math.text import cooccurrence_topk

_DIM = 64                                           # >= 52 (the §89 kernel header)


def _one(seed=1278):
    return klein4_expand(_DIM, seed)


def _corpus():
    """A tiny fixture corpus — words shared ACROSS documents so section-conservation
    is non-trivial ('the' / 'cat' / 'dog' recur; 'quark' appears once)."""
    return [
        ["the", "cat", "sat", "on", "the", "mat"],
        ["the", "dog", "ran", "after", "the", "cat"],
        ["a", "cat", "and", "a", "dog", "are", "friends"],
        ["the", "quark", "is", "small"],
    ]


def _tmp():
    return tempfile.mkdtemp(prefix="srmech_plasmid_")


# ── (1) per-doc plasmid chromosomes + store round-trip (census) ───────────────

def test_per_doc_plasmid_chromosomes_and_census():
    one = _one()
    corpus = _corpus()
    store = _tmp()
    res = P.plasmid_extract(corpus, store, one, window=2, k=8)
    assert res["status"] == "ok"
    assert res["n_sections"] == len(corpus)
    assert res["sections"] == [f"sec{i}" for i in range(len(corpus))]
    census = G.genome_census(store, coupling=one)
    labels = sorted(c["label"] for c in census["chromosomes"])
    # P plasmid sections + the shared VOCAB chromosome (the karyotype index).
    assert labels == sorted([f"sec{i}" for i in range(len(corpus))] + [P.VOCAB_LABEL])
    assert census["n_chromosomes"] == len(corpus) + 1
    # every section (and the vocab chrom) is a PLASMID (no centromere) — Tier-1.
    assert census["types"]["nuclear"] == 0
    assert census["types"]["plasmid"] == len(corpus) + 1


# ── (2) section_count accumulates + is SSoT-derivable ─────────────────────────

def test_section_count_accumulates_and_is_derivable():
    one = _one()
    corpus = _corpus()
    store = _tmp()
    res = P.plasmid_extract(corpus, store, one, window=2, k=8)
    sc = res["section_count"]
    vocab = res["vocab"]
    idx = {w: i for i, w in enumerate(vocab)}
    # 'the' appears in docs 0, 1, 3 -> 3 sections; 'cat' in 0, 1, 2 -> 3; 'quark' in
    # doc 3 only -> 1. (A node counts ONCE per section it appears in.)
    assert sc[idx["the"]] == 3
    assert sc[idx["cat"]] == 3
    assert sc[idx["dog"]] == 2
    assert sc[idx["quark"]] == 1
    # SSoT: the derived read (scanning the sections' GLOBAL node_ids) == the streamed
    # accumulator, byte-for-byte.
    assert P.section_counts(store, coupling=one) == sc
    # the ~asymmetry: most nodes are accessory (count 1), a few conserved (>1).
    conserved = [v for v in sc.values() if v >= 2]
    assert len(conserved) >= 2 and len(conserved) < len(sc)


# ── (3) C↔Python BYTE-PARITY of the extracted sections ────────────────────────

def _turns_bin(store):
    return (Path(store) / "turns.bin").read_bytes()


def test_native_equals_pure_turns_bin_byte_parity(monkeypatch):
    corpus = _corpus()
    # native: the whole section rides srmech_genome_plasmid_extract.
    store_native = _tmp()
    P.plasmid_extract(corpus, store_native, _one(), window=2, k=8)
    native_bytes = _turns_bin(store_native)
    # pure: FORCE the C orchestrator to decline (as in a no-C / numpy-absent venv) so
    # the pure _graph_kernel_encode + genome_append_kernel path builds the region.
    monkeypatch.setattr(_native, "genome_plasmid_extract_c", lambda *a, **k: None)
    store_pure = _tmp()
    P.plasmid_extract(corpus, store_pure, _one(), window=2, k=8)
    pure_bytes = _turns_bin(store_pure)
    monkeypatch.undo()
    assert native_bytes == pure_bytes, "native section bytes != pure section bytes"
    assert len(native_bytes) > 0


def test_native_peer_present_when_built():
    """When a native lib is loaded it MUST carry the rc278 orchestrator (the parity
    battery above only proves native==pure when the peer is present)."""
    if _native.HAS_NATIVE:
        assert _native.has_native_genome_plasmid_extract(), (
            "HAS_NATIVE but srmech_genome_plasmid_extract absent — stale .so")


# ── (4) §101 progress / cancel truncates at a whole-section boundary ──────────

def test_progress_monotone_and_reaches_total():
    one = _one()
    corpus = _corpus()
    seen = []
    P.plasmid_extract(corpus, _tmp(), one, window=2, k=8,
                      progress=lambda ev: seen.append((ev["phase"], ev["done"],
                                                        ev["total"])) or False)
    assert seen, "progress never fired"
    phases = {p for (p, _d, _t) in seen}
    assert phases == {_native.SRMECH_PHASE_EXTRACTING}
    dones = [d for (_p, d, _t) in seen]
    assert dones == sorted(dones)                   # monotone
    assert all(t == len(corpus) for (_p, _d, t) in seen)
    assert dones[0] == 0


def test_cancel_truncates_at_section_boundary():
    one = _one()
    corpus = _corpus()
    store = _tmp()

    def cancel_after_two(ev):
        return ev["done"] >= 2                       # cancel entering section 2

    res = P.plasmid_extract(corpus, store, one, window=2, k=8,
                            progress=cancel_after_two)
    assert res["status"] == "cancelled"
    assert res["n_sections"] == 2                    # sec0 + sec1 completed
    census = G.genome_census(store, coupling=one)
    section_labels = sorted(c["label"] for c in census["chromosomes"]
                            if c["label"] != P.VOCAB_LABEL)
    assert section_labels == ["sec0", "sec1"]        # NO partial sec2
    # each completed section round-trips (a valid chromosome boundary).
    for lbl in section_labels:
        g = P._read_section_graph(store, lbl, one)
        assert "node_ids" in g and "edges" in g


# ── (5) RETIREMENT EQUIVALENCE: the section IS the co-occurrence graph ─────────

def test_retirement_equivalence_same_graph_as_json_path():
    """Each stored section decodes back to the SAME co-occurrence graph the old JSON
    path (cooccurrence_topk) produced for that document — mapped through the GLOBAL
    node_ids table. The genome-native store is lossless vs the retired monolith."""
    one = _one()
    corpus = _corpus()
    store = _tmp()
    res = P.plasmid_extract(corpus, store, one, window=2, k=8)
    vocab = res["vocab"]
    idx = {w: i for i, w in enumerate(vocab)}
    for i, doc in enumerate(corpus):
        # the old path: the doc's bounded co-occurrence graph (LOCAL edges + weights).
        cooc = cooccurrence_topk([doc], window=2, k=8)
        want_edges = {}
        for (u, v), w in zip(cooc["edges"], cooc["weights"]):
            gu, gv = idx[cooc["vocab"][u]], idx[cooc["vocab"][v]]
            want_edges[(gu, gv)] = w
        # the new path: decode the stored section, map LOCAL edges -> GLOBAL via node_ids.
        graph = P._read_section_graph(store, f"sec{i}", one)
        nid = graph["node_ids"]
        got_edges = {}
        for (u, v), w in zip(graph["edges"], graph["weights"]):
            got_edges[(nid[u], nid[v])] = w
        assert got_edges == want_edges, f"doc {i} co-occurrence graph diverged"
        assert set(nid) == {idx[w] for w in set(doc)}


# ── (6) streaming: add a doc appends one section, prior sections untouched ─────

def test_streaming_append_only_prior_sections_byte_untouched():
    one = _one()
    corpus = _corpus()
    store = _tmp()
    vocab = []
    # ingest the first 2 docs.
    P.plasmid_extract(corpus[:2], store, one, vocab=vocab, window=2, k=8)
    sec0_before = G.genome_window(store, "sec0", coupling=one)
    turns_prefix = _turns_bin(store)
    # ingest 2 more (SAME vocab object -> shared global id space).
    res = P.plasmid_extract(corpus[2:], store, one, vocab=vocab, window=2, k=8)
    assert res["n_sections"] == 2
    census = G.genome_census(store, coupling=one)
    sections = sorted(c["label"] for c in census["chromosomes"]
                      if c["label"] != P.VOCAB_LABEL)
    assert sections == ["sec0", "sec1", "sec2", "sec3"]
    # the first section's coupled leaves are byte-untouched (append-only).
    sec0_after = G.genome_window(store, "sec0", coupling=one)
    assert [b.tobytes() for b in sec0_before] == [b.tobytes() for b in sec0_after]
    # the earlier sections' turns.bin span is a PREFIX of the grown body (the vocab
    # chromosome is re-minted at the tail, so compare only the sec0..sec1 region).
    sec1 = next(c for c in G.genome_catalog(store, coupling=one)["chromosomes"]
                if c["label"] == "sec1")
    keep = int(sec1["byte_offset"]) + int(sec1["byte_len"])
    assert _turns_bin(store)[:keep] == turns_prefix[:keep]


# ── (7) leaf_dim guard (a plasmid section is a §89 kernel chromosome) ──────────

def test_leaf_dim_must_fit_kernel_header():
    with pytest.raises(ValueError):
        P.plasmid_extract([["a", "b"]], _tmp(), klein4_expand(16, 1), window=2)
